"""Tiny client for sending telemetry from an agent to AgentLens."""
import requests

class AgentLogger:
    def __init__(self, base_url="http://127.0.0.1:8000", agent_name="My Agent", timeout=5):
        self.base_url = base_url.rstrip("/")
        self.agent_name = agent_name
        self.timeout = timeout

    def start_run(self, user_input, prompt_version="v1"):
        response = requests.post(
            f"{self.base_url}/runs",
            json={"agent_name": self.agent_name, "user_input": user_input,
                  "prompt_version": prompt_version, "status": "running"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["id"]

    def log_tool_call(self, run_id, tool_name, input_summary="", output_summary="",
                      status="success", duration_ms=0, error_message=""):
        response = requests.post(
            f"{self.base_url}/runs/{run_id}/tool-calls",
            json={"tool_name": tool_name, "input_summary": input_summary,
                  "output_summary": output_summary, "status": status,
                  "duration_ms": duration_ms, "error_message": error_message},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def finish_run(self, run_id, status="success", duration_ms=0,
                   response_summary="", error_message=""):
        response = requests.patch(
            f"{self.base_url}/runs/{run_id}",
            json={"status": status, "duration_ms": duration_ms,
                  "response_summary": response_summary, "error_message": error_message},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
