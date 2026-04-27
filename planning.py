"""
agents/planning.py
Agente de Planificacion y Requerimientos
"""
from __future__ import annotations
import logging
from typing import Dict, Any
from pydantic import ValidationError

from .core import AgentBase, AgentConfig, TaskPayload

logger = logging.getLogger("agents.planning")


class PlanningAgent(AgentBase):
    async def handle_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        project_id = payload.get("project_id")
        task = payload.get("task", {})
        action = task.get("action")

        if action == "init_project":
            brief = task.get("brief", "")
            # Naive extraction: create initial backlog of user stories
            stories = self._generate_user_stories(brief)
            context = {
                "requirements": {
                    "brief": brief,
                    "stories": stories,
                    "approved": False,
                }
            }
            await self.update_context(project_id, context)
            return {"status": "ok", "data": context}

        elif action == "approve_requirements":
            await self.update_context(project_id, {"requirements": {"approved": True}})
            return {"status": "ok", "message": "requirements approved"}

        else:
            return {"status": "error", "message": f"unknown action {action}"}

    def _generate_user_stories(self, brief: str):
        # placeholder simple generator - replace by LLM integration if desired
        if not brief:
            return []
        stories = [
            {"id": f"US-{i+1}", "title": f"{brief} - feature {i+1}", "acceptance": ["Should work"]}
            for i in range(5)
        ]
        return stories


if __name__ == "__main__":
    import uvicorn
    cfg = AgentConfig(AGENT_NAME="planning", PORT=8001)
    agent = PlanningAgent(cfg)
    uvicorn.run(agent.app, host=cfg.HOST, port=cfg.PORT)
