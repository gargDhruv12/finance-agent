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
    gemini_model: str
    dry_run: bool
    require_approval: bool
    sender_email: str
    payment_base_url: str
    audit_db_path: Path
    cache_db_path: Path
    approvals_path: Path
    enable_local_tracing: bool
    langsmith_tracing: bool
    langsmith_api_key: str | None
    langsmith_project: str
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    smtp_use_tls: bool
    scheduler_interval_hours: int


def load_settings() -> Settings:
    _load_env_file(PROJECT_ROOT / ".env")
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        dry_run=_as_bool(os.getenv("DRY_RUN"), default=True),
        require_approval=_as_bool(os.getenv("REQUIRE_APPROVAL"), default=True),
        sender_email=os.getenv("SENDER_EMAIL", "finance@example.com"),
        payment_base_url=os.getenv("PAYMENT_BASE_URL", "https://payments.example.com/pay"),
        audit_db_path=PROJECT_ROOT / os.getenv("AUDIT_DB_PATH", "outputs/audit_log.sqlite"),
        cache_db_path=PROJECT_ROOT / os.getenv("CACHE_DB_PATH", "outputs/llm_cache.sqlite"),
        approvals_path=PROJECT_ROOT / os.getenv("APPROVALS_PATH", "outputs/approvals.json"),
        enable_local_tracing=_as_bool(os.getenv("ENABLE_LOCAL_TRACING"), default=True),
        langsmith_tracing=_as_bool(os.getenv("LANGSMITH_TRACING"), default=False),
        langsmith_api_key=os.getenv("LANGSMITH_API_KEY") or None,
        langsmith_project=os.getenv("LANGSMITH_PROJECT", "finance-credit-follow-up-agent"),
        smtp_host=os.getenv("SMTP_HOST") or None,
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME") or None,
        smtp_password=os.getenv("SMTP_PASSWORD") or None,
        smtp_use_tls=_as_bool(os.getenv("SMTP_USE_TLS"), default=True),
        scheduler_interval_hours=int(os.getenv("SCHEDULER_INTERVAL_HOURS", "24")),
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
