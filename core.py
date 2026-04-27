"""
agents/core.py
Base shared library for agents: AgentBase, configuration, messaging helpers.

Requisitos: fastapi, uvicorn, httpx, redis, pydantic, python-dotenv

Uso: extender AgentBase y proveer implementacion de handle_task
"""
from __future__ import annotations
import asyncio
import json
import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from pydantic import BaseModel, BaseSettings
import httpx
import redis.asyncio as redis

logger = logging.getLogger("agents")
logging.basicConfig(level=logging.INFO)


class AgentConfig(BaseSettings):
    AGENT_NAME: str = "agent"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    REDIS_URL: str = "redis://localhost:6379/0"
    API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"


class TaskPayload(BaseModel):
    project_id: str
    phase: Optional[str]
    task: Dict[str, Any]
    origin: Optional[str]
    intent: Optional[str] = "request"
    trace_id: Optional[str]


class AgentBase:
    """Clase base para agentes.

    Provee:
    - servidor FastAPI con endpoints /task y /status
    - cliente redis asincrono para contexto y pub/sub
    - helpers para publicar eventos y enviar tareas a otros agentes
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.app = FastAPI(title=f"Agent - {self.config.AGENT_NAME}")
        self.redis = redis.from_url(self.config.REDIS_URL)
        self.http = httpx.AsyncClient(timeout=30.0)
        self._register_routes()

    def _register_routes(self):
        @self.app.post("/task")
        async def receive_task(payload: TaskPayload, background_tasks: BackgroundTasks, request: Request):
            # simple api-key header check (optional)
            if self.config.API_KEY:
                key = request.headers.get("x-api-key")
                if key != self.config.API_KEY:
                    raise HTTPException(status_code=401, detail="Invalid API key")

            trace_id = payload.trace_id or str(uuid.uuid4())
            logger.info(f"[{self.config.AGENT_NAME}] Received task {trace_id}: {payload.dict()}" )
            # delegate processing to background to keep HTTP fast
            background_tasks.add_task(self._process_and_respond, payload.dict(), trace_id)
            return {"status": "accepted", "trace_id": trace_id}

        @self.app.get("/status")
        async def status():
            return {"agent": self.config.AGENT_NAME, "status": "ok"}

        @self.app.get("/health")
        async def health():
            try:
                await self.redis.ping()
                return {"redis": "ok"}
            except Exception as e:
                return {"redis": f"error: {e}"}

    async def _process_and_respond(self, payload: Dict[str, Any], trace_id: str):
        try:
            result = await self.handle_task(payload)
            # publish result event
            await self.publish_event({
                "project_id": payload.get("project_id"),
                "origin": self.config.AGENT_NAME,
                "trace_id": trace_id,
                "intent": "response",
                "result": result,
            })
        except Exception as exc:
            logger.exception("Error processing task")
            await self.publish_event({
                "project_id": payload.get("project_id"),
                "origin": self.config.AGENT_NAME,
                "trace_id": trace_id,
                "intent": "error",
                "error": str(exc),
            })

    async def handle_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Override en subclases para implementar la logica del agente.

        Debe devolver un dict con al menos `status` y opcionalmente `data`.
        """
        raise NotImplementedError()

    # Context helpers
    async def get_context(self, project_id: str) -> Dict[str, Any]:
        key = f"project:{project_id}:context"
        raw = await self.redis.get(key)
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except Exception:
            return {}

    async def update_context(self, project_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        key = f"project:{project_id}:context"
        # naive merge with retries
        for _ in range(3):
            try:
                async with self.redis.pipeline() as pipe:
                    await pipe.watch(key)
                    raw = await pipe.get(key)
                    base = json.loads(raw) if raw else {}
                    # shallow merge
                    base.update(patch)
                    await pipe.multi()
                    await pipe.set(key, json.dumps(base))
                    await pipe.execute()
                    return base
            except redis.exceptions.WatchError:
                continue
        # fallback: set directly
        await self.redis.set(key, json.dumps(patch))
        return patch

    async def publish_event(self, event: Dict[str, Any]):
        channel = "agent:events"
        payload = json.dumps(event)
        await self.redis.publish(channel, payload)
        logger.info(f"[{self.config.AGENT_NAME}] Published event on {channel}: {payload}")

    async def send_task_to_agent(self, url: str, payload: Dict[str, Any]) -> httpx.Response:
        headers = {}
        if self.config.API_KEY:
            headers["x-api-key"] = self.config.API_KEY
        resp = await self.http.post(url, json=payload, headers=headers)
        return resp


# helper for standalone running
if __name__ == "__main__":
    import uvicorn
    cfg = AgentConfig()
    agent = AgentBase(cfg)
    uvicorn.run(agent.app, host=cfg.HOST, port=cfg.PORT)
