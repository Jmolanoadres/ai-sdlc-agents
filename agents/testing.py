"""
agents/testing.py
Agente de Testing y QA
"""
from __future__ import annotations
import logging
from typing import Dict, Any

from .core import AgentBase, AgentConfig

logger = logging.getLogger("agents.testing")


class TestingAgent(AgentBase):
    async def handle_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        project_id = payload.get("project_id")
        task = payload.get("task", {})
        action = task.get("action")

        if action == "generate_tests":
            target = task.get("target", {})
            tests = self._generate_pytest_for_target(target)
            artifact = {"tests": tests}
            await self.update_context(project_id, {"tests": artifact})
            return {"status": "ok", "data": artifact}

        elif action == "run_smoke":
            # placeholder: run smoke - in real scenario invoke CI or test runner
            result = {"status": "pass"}
            await self.update_context(project_id, {"last_smoke": result})
            return {"status": "ok", "data": result}

        else:
            return {"status": "error", "message": f"unknown action {action}"}

    def _generate_pytest_for_target(self, target: Dict[str, Any]) -> str:
        # naive generator
        endpoint = target.get("endpoint", "/health")
        return f"""
import requests

def test_smoke():
    r = requests.get('http://localhost:8004{endpoint}')
    assert r.status_code == 200
"""


if __name__ == "__main__":
    import uvicorn
    cfg = AgentConfig(AGENT_NAME="testing", PORT=8005)
    agent = TestingAgent(cfg)
    uvicorn.run(agent.app, host=cfg.HOST, port=cfg.PORT)
