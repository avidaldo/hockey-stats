from __future__ import annotations

import datetime as dt
import sqlite3

from app.domain.models import GoalieGameStatInput, SkaterGameStatInput
from app.main import build_service


def _add_player_if_missing(service, name: str, role: str, number: int | None = None) -> None:
    current = {player.name.lower(): player for player in service.list_active_players()}
    if name.lower() in current:
        return
    service.add_player(name=name, role=role, number=number)


def _add_recipient_if_missing(service, name: str, email: str) -> None:
    current = {recipient.email.lower() for recipient in service.list_mail_recipients()}
    if email.lower() in current:
        return
    service.add_mail_recipient(name=name, email=email)


def seed() -> None:
    service = build_service()

    # Add players with jersey numbers
    _add_player_if_missing(service, "Liam", "skater", 10)
    _add_player_if_missing(service, "Noah", "skater", 17)
    _add_player_if_missing(service, "Ethan", "goalie", 1)

    _add_recipient_if_missing(service, "Coach", "coach@example.com")
    _add_recipient_if_missing(service, "Manager", "manager@example.com")

    active_by_name = {player.name: player for player in service.list_active_players()}

    season = f"{dt.date.today().year}-{dt.date.today().year + 1}"
    game_date = dt.date.today().isoformat()

    skaters = [
        SkaterGameStatInput(
            player_id=active_by_name["Liam"].id,
            goals=2,
            assists=1,
            pim=2,
            shg=0,
            ppg=1,
        ),
        SkaterGameStatInput(
            player_id=active_by_name["Noah"].id,
            goals=1,
            assists=2,
            pim=0,
            shg=1,
            ppg=0,
        ),
    ]

    goalies = [
        GoalieGameStatInput(
            player_id=active_by_name["Ethan"].id,
            saves=28,
            goals_against=2,
            shots_received=30,  # This will be recalculated as saves + GA
        )
    ]

    try:
        service.record_game_stats(
            season_label=season,
            season_type="regular",
            game_date=game_date,
            opponent="Demo Opponent",
            result="win",
            notes="Demo seeded game",
            skater_stats=skaters,
            goalie_stats=goalies,
            auto_send_email=False,  # Don't send email during seeding
        )
        print("Seed completed: players, recipients, and one demo game were added.")
    except (sqlite3.IntegrityError, ValueError) as exc:
        print(f"Seed skipped game insert: {exc}")
        print("Players/recipients were still ensured.")


if __name__ == "__main__":
    seed()
