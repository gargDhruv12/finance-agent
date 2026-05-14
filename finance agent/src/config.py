from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _as_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None
    dry_run: bool
    sender_email: str
    payment_base_url: str
    audit_db_path: Path


def load_settings() -> Settings:
    _load_env_file(PROJECT_ROOT / ".env")
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        dry_run=_as_bool(os.getenv("DRY_RUN"), default=True),
        sender_email=os.getenv("SENDER_EMAIL", "finance@example.com"),
        payment_base_url=os.getenv("PAYMENT_BASE_URL", "https://payments.example.com/pay"),
        audit_db_path=PROJECT_ROOT / os.getenv("AUDIT_DB_PATH", "outputs/audit_log.sqlite"),
    )


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
