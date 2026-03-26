from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.application.use_cases import HockeyService
from app.infrastructure.email_sender import AutoEmailSender
from app.infrastructure.sqlite_db import (
    SqliteDatabase,
    SqliteEmailLogRepository,
    SqliteGameRepository,
    SqliteMailingListRepository,
    SqlitePlayerRepository,
)
from app.ui.tk_app import HockeyApp


def build_service() -> HockeyService:
    db = SqliteDatabase(Path("data/hockey.sqlite3"))
    db.initialize()

    return HockeyService(
        players=SqlitePlayerRepository(db),
        games=SqliteGameRepository(db),
        mailing=SqliteMailingListRepository(db),
        sender=AutoEmailSender(),
        email_logs=SqliteEmailLogRepository(db),
    )


def main() -> None:
    service = build_service()
    app = HockeyApp(service)
    app.mainloop()


if __name__ == "__main__":
    main()
