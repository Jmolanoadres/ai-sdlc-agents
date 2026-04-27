"""
agents/docs.py
Agente de Documentación y Mantenimiento
"""
from __future__ import annotations
import logging
from typing import Dict, Any

from .core import AgentBase, AgentConfig

logger = logging.getLogger("agents.docs")


class DocsAgent(AgentBase):
    async def handle_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        project_id = payload.get("project_id")
        task = payload.get("task", {})
        action = task.get("action")

        if action == "generate_docs":
            context = await self.get_context(project_id)
            docs = self._render_docs(context)
            await self.update_context(project_id, {"docs": docs})
            return {"status": "ok", "data": docs}

        else:
            return {"status": "error", "message": f"unknown action {action}"}

    def _render_docs(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # simple assembler of docs
        return {
            "readme": f"Project README for {context.get('requirements', {}).get('brief', 'Unnamed')}",
            "architecture": context.get("architecture", {}),
            "api": context.get("backend", {}),
        }


if __name__ == "__main__":
    import uvicorn
    cfg = AgentConfig(AGENT_NAME="docs", PORT=8007)
    agent = DocsAgent(cfg)
    uvicorn.run(agent.app, host=cfg.HOST, port=cfg.PORT)
