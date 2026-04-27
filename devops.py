"""
agents/devops.py
Agente de DevOps y Despliegue
"""
from __future__ import annotations
import logging
from typing import Dict, Any

from .core import AgentBase, AgentConfig

logger = logging.getLogger("agents.devops")


class DevOpsAgent(AgentBase):
    async def handle_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        project_id = payload.get("project_id")
        task = payload.get("task", {})
        action = task.get("action")

        if action == "generate_ci":
            platform = task.get("platform", "github_actions")
            pipeline = self._generate_ci_pipeline(platform)
            await self.update_context(project_id, {"ci_pipeline": pipeline})
            return {"status": "ok", "data": pipeline}

        elif action == "build_image":
            # placeholder build logic
            image = f"{project_id}:latest"
            await self.update_context(project_id, {"last_image": image})
            return {"status": "ok", "image": image}

        else:
            return {"status": "error", "message": f"unknown action {action}"}

    def _generate_ci_pipeline(self, platform: str) -> Dict[str, Any]:
        return {"platform": platform, "steps": ["lint", "test", "build", "deploy:staging"]}


if __name__ == "__main__":
    import uvicorn
    cfg = AgentConfig(AGENT_NAME="devops", PORT=8006)
    agent = DevOpsAgent(cfg)
    uvicorn.run(agent.app, host=cfg.HOST, port=cfg.PORT)
