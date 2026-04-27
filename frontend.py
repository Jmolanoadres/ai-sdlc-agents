"""
agents/frontend.py
Agente de Desarrollo Frontend
"""
from __future__ import annotations
import logging
from typing import Dict, Any

from .core import AgentBase, AgentConfig

logger = logging.getLogger("agents.frontend")


class FrontendAgent(AgentBase):
    async def handle_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        project_id = payload.get("project_id")
        task = payload.get("task", {})
        action = task.get("action")

        if action == "scaffold_component":
            details = task.get("details", {})
            component_name = details.get("name", "MyComponent")
            code = self._generate_react_component(component_name)
            artifact = {"component": component_name, "code": code}
            await self.update_context(project_id, {"frontend": artifact})
            return {"status": "ok", "data": artifact}

        else:
            return {"status": "error", "message": f"unknown action {action}"}

    def _generate_react_component(self, name: str) -> str:
        return f"""
import React from 'react';

export function {name}(props) {{
    return (
        <div className=\"{name}\">{name} works</div>
    );
}}
"""


if __name__ == "__main__":
    import uvicorn
    cfg = AgentConfig(AGENT_NAME="frontend", PORT=8003)
    agent = FrontendAgent(cfg)
    uvicorn.run(agent.app, host=cfg.HOST, port=cfg.PORT)
