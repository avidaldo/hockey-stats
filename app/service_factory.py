from __future__ import annotations

import os
from pathlib import Path

from app.application.use_cases import HockeyService
from app.infrastructure.email_sender import AutoEmailSender
from app.infrastructure.sqlite_db import (
    SqliteDatabase,
    SqliteEmailLogRepository,
    SqliteGameRepository,
    SqliteMailingListRepository,
    SqlitePlayerRepository,
)


DEFAULT_DB_PATH = Path("data/hockey.sqlite3")


def build_service(db_path: Path | None = None) -> HockeyService:
    configured_path = db_path or Path(os.getenv("HOCKEY_STATS_DB_PATH", DEFAULT_DB_PATH))
    db = SqliteDatabase(configured_path)
    db.initialize()

    return HockeyService(
        players=SqlitePlayerRepository(db),
        games=SqliteGameRepository(db),
        mailing=SqliteMailingListRepository(db),
        sender=AutoEmailSender(),
        email_logs=SqliteEmailLogRepository(db),
    )
