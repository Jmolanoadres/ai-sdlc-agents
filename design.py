"""
agents/design.py
Agente de Diseño y Arquitectura
"""
from __future__ import annotations
import logging
from typing import Dict, Any

from .core import AgentBase, AgentConfig

logger = logging.getLogger("agents.design")


class DesignAgent(AgentBase):
    async def handle_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        project_id = payload.get("project_id")
        task = payload.get("task", {})
        action = task.get("action")

        if action == "create_architecture":
            requirements = (await self.get_context(project_id)).get("requirements", {})
            diagram = self._generate_mermaid_diagram(requirements)
            doc = {
                "architecture": {
                    "diagram_mermaid": diagram,
                    "decisions": ["Use microservices for scalability", "Expose RESTful APIs"],
                }
            }
            await self.update_context(project_id, doc)
            return {"status": "ok", "data": doc}

        else:
            return {"status": "error", "message": f"unknown action {action}"}

    def _generate_mermaid_diagram(self, requirements: Dict[str, Any]) -> str:
        # simple mermaid stub
        return """
        graph LR
            A[User] --> B[Frontend]
            B --> C[Backend]
            C --> D[(Database)]
        """


if __name__ == "__main__":
    import uvicorn
    cfg = AgentConfig(AGENT_NAME="design", PORT=8002)
    agent = DesignAgent(cfg)
    uvicorn.run(agent.app, host=cfg.HOST, port=cfg.PORT)
