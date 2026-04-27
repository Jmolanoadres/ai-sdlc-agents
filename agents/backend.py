"""
agents/backend.py
Agente de Desarrollo Backend
"""
from __future__ import annotations
import logging
from typing import Dict, Any

from .core import AgentBase, AgentConfig

logger = logging.getLogger("agents.backend")


class BackendAgent(AgentBase):
    async def handle_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        project_id = payload.get("project_id")
        task = payload.get("task", {})
        action = task.get("action")

        if action == "scaffold_api":
            entity = task.get("entity", "Item")
            openapi = self._generate_openapi_spec(entity)
            artifact = {"entity": entity, "openapi": openapi}
            await self.update_context(project_id, {"backend": artifact})
            return {"status": "ok", "data": artifact}

        else:
            return {"status": "error", "message": f"unknown action {action}"}

    def _generate_openapi_spec(self, entity: str) -> Dict[str, Any]:
        spec = {
            "openapi": "3.0.0",
            "info": {"title": f"{entity} API", "version": "1.0.0"},
            "paths": {
                f"/api/{entity.lower()}": {
                    "get": {"summary": f"List {entity}", "responses": {"200": {"description": "ok"}}},
                    "post": {"summary": f"Create {entity}", "responses": {"201": {"description": "created"}}},
                },
                f"/api/{entity.lower()}/{{id}}": {
                    "get": {"summary": f"Get {entity}", "responses": {"200": {"description": "ok"}}}
                }
            }
        }
        return spec


if __name__ == "__main__":
    import uvicorn
    cfg = AgentConfig(AGENT_NAME="backend", PORT=8004)
    agent = BackendAgent(cfg)
    uvicorn.run(agent.app, host=cfg.HOST, port=cfg.PORT)
