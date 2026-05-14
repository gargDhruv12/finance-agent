from __future__ import annotations

from datetime import date
from pathlib import Path

from .config import PROJECT_ROOT, load_settings
from .main import process_invoices


def start_scheduler(input_path: Path | None = None, today: date | None = None) -> None:
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
    except Exception as exc:
        raise RuntimeError("APScheduler is not installed. Run pip install -r requirements.txt.") from exc

    settings = load_settings()
    scheduler = BlockingScheduler()
    source = input_path or PROJECT_ROOT / "data" / "sample_invoices.csv"

    scheduler.add_job(
        lambda: process_invoices(source, today=today),
        "interval",
        hours=settings.scheduler_interval_hours,
        id="finance_follow_up_agent",
        replace_existing=True,
    )
    print(f"Scheduler started. Running every {settings.scheduler_interval_hours} hours for {source}.")
    scheduler.start()

