from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class TraceLogger:
    def __init__(
        self,
        output_dir: str | Path,
        enable_local: bool = True,
        langsmith_enabled: bool = False,
        langsmith_api_key: str | None = None,
        langsmith_project: str = "finance-credit-follow-up-agent",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.enable_local = enable_local
        self.langsmith_enabled = langsmith_enabled and bool(langsmith_api_key)
        self.langsmith_project = langsmith_project
        self._events: list[dict[str, Any]] = []
        self._langsmith_client = self._build_langsmith_client(langsmith_api_key)

    def event(self, name: str, payload: dict[str, Any]) -> None:
        event = {
            "timestamp": datetime.now().isoformat(),
            "event": name,
            "payload": payload,
        }
        self._events.append(event)
        self._send_langsmith_event(event)

    def flush(self) -> None:
        if not self.enable_local:
            return
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "trace_events.json").write_text(
            json.dumps(self._events, indent=2, default=str),
            encoding="utf-8",
        )

    def _build_langsmith_client(self, api_key: str | None):
        if not self.langsmith_enabled:
            return None
        try:
            from langsmith import Client
        except Exception:
            return None
        return Client(api_key=api_key)

    def _send_langsmith_event(self, event: dict[str, Any]) -> None:
        if self._langsmith_client is None:
            return
        try:
            self._langsmith_client.create_run(
                name=event["event"],
                run_type="tool",
                project_name=self.langsmith_project,
                inputs=event["payload"],
                outputs={"logged": True},
            )
        except Exception:
            return
