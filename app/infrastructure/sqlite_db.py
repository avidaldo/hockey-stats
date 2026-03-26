from __future__ import annotations

import math
import sqlite3
from pathlib import Path

from app.application.use_cases import GoalieSummaryRow, SeasonSummary, SkaterSummaryRow
from app.domain.models import GoalieGameStatInput, MailRecipient, Player, SkaterGameStatInput


def _last_row_id(cursor: sqlite3.Cursor) -> int:
    if cursor.lastrowid is None:
        raise RuntimeError("SQLite insert did not return lastrowid")
    return int(cursor.lastrowid)


class SqliteDatabase:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('skater', 'goalkeeper')),
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS seasons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    season_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    opponent TEXT NOT NULL,
                    result TEXT NOT NULL CHECK (result IN ('win', 'loss')),
                    notes TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY(season_id) REFERENCES seasons(id),
                    UNIQUE(season_id, date, opponent)
                );

                CREATE TABLE IF NOT EXISTS skater_game_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    player_id INTEGER NOT NULL,
                    goals INTEGER NOT NULL DEFAULT 0,
                    assists INTEGER NOT NULL DEFAULT 0,
                    pim INTEGER NOT NULL DEFAULT 0,
                    shg INTEGER NOT NULL DEFAULT 0,
                    ppg INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
                    FOREIGN KEY(player_id) REFERENCES players(id)
                );

                CREATE TABLE IF NOT EXISTS goalie_game_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    player_id INTEGER NOT NULL,
                    saves INTEGER NOT NULL DEFAULT 0,
                    goals_against INTEGER NOT NULL DEFAULT 0,
                    shots_received INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
                    FOREIGN KEY(player_id) REFERENCES players(id)
                );

                CREATE TABLE IF NOT EXISTS mail_recipients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS email_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    recipients TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    detail TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )


class SqlitePlayerRepository:
    def __init__(self, db: SqliteDatabase) -> None:
        self.db = db

    def add_player(self, name: str, role: str) -> int:
        with self.db.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO players(name, role, active) VALUES (?, ?, 1)",
                (name, role),
            )
            return _last_row_id(cursor)

    def remove_player(self, player_id: int) -> None:
        with self.db.connect() as conn:
            conn.execute("UPDATE players SET active = 0 WHERE id = ?", (player_id,))

    def list_active_players(self) -> list[Player]:
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT id, name, role, active FROM players WHERE active = 1 ORDER BY name"
            ).fetchall()

        return [
            Player(id=row["id"], name=row["name"], role=row["role"], active=bool(row["active"]))
            for row in rows
        ]


class SqliteGameRepository:
    def __init__(self, db: SqliteDatabase) -> None:
        self.db = db

    def _get_or_create_season_id(self, conn: sqlite3.Connection, season_label: str) -> int:
        row = conn.execute("SELECT id FROM seasons WHERE label = ?", (season_label,)).fetchone()
        if row:
            return int(row["id"])

        cursor = conn.execute("INSERT INTO seasons(label) VALUES (?)", (season_label,))
        return _last_row_id(cursor)

    def record_game(
        self,
        season_label: str,
        game_date: str,
        opponent: str,
        result: str,
        notes: str,
        skater_stats: list[SkaterGameStatInput],
        goalie_stats: list[GoalieGameStatInput],
    ) -> int:
        with self.db.connect() as conn:
            season_id = self._get_or_create_season_id(conn, season_label)
            cursor = conn.execute(
                """
                INSERT INTO games(season_id, date, opponent, result, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (season_id, game_date, opponent, result, notes),
            )
            game_id = _last_row_id(cursor)

            for stat in skater_stats:
                conn.execute(
                    """
                    INSERT INTO skater_game_stats(game_id, player_id, goals, assists, pim, shg, ppg)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        game_id,
                        stat.player_id,
                        stat.goals,
                        stat.assists,
                        stat.pim,
                        stat.shg,
                        stat.ppg,
                    ),
                )

            for stat in goalie_stats:
                shots_received = stat.shots_received if stat.shots_received else stat.saves + stat.goals_against
                conn.execute(
                    """
                    INSERT INTO goalie_game_stats(game_id, player_id, saves, goals_against, shots_received)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        game_id,
                        stat.player_id,
                        stat.saves,
                        stat.goals_against,
                        shots_received,
                    ),
                )

            return game_id

    def get_season_summary(self, season_label: str) -> SeasonSummary:
        with self.db.connect() as conn:
            season_row = conn.execute("SELECT id FROM seasons WHERE label = ?", (season_label,)).fetchone()
            if not season_row:
                return {
                    "season": season_label,
                    "team": {"wins": 0, "losses": 0},
                    "skaters": [],
                    "goalkeepers": [],
                }

            season_id = int(season_row["id"])

            team_row = conn.execute(
                """
                SELECT
                    SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
                    SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) AS losses
                FROM games
                WHERE season_id = ?
                """,
                (season_id,),
            ).fetchone()

            skaters = conn.execute(
                """
                SELECT
                    p.name AS player_name,
                    SUM(s.goals) AS goals,
                    SUM(s.assists) AS assists,
                    SUM(s.pim) AS pim,
                    SUM(s.shg) AS shg,
                    SUM(s.ppg) AS ppg
                FROM skater_game_stats s
                JOIN games g ON g.id = s.game_id
                JOIN players p ON p.id = s.player_id
                WHERE g.season_id = ?
                GROUP BY s.player_id, p.name
                ORDER BY p.name
                """,
                (season_id,),
            ).fetchall()

            goalkeepers = conn.execute(
                """
                SELECT
                    p.name AS player_name,
                    SUM(gs.saves) AS saves,
                    SUM(gs.goals_against) AS goals_against,
                    SUM(gs.shots_received) AS shots_received,
                    SUM(CASE WHEN g.result = 'win' THEN 1 ELSE 0 END) AS wins
                FROM goalie_game_stats gs
                JOIN games g ON g.id = gs.game_id
                JOIN players p ON p.id = gs.player_id
                WHERE g.season_id = ?
                GROUP BY gs.player_id, p.name
                ORDER BY p.name
                """,
                (season_id,),
            ).fetchall()

            skater_rows: list[SkaterSummaryRow] = [
                {
                    "player_name": row["player_name"],
                    "goals": int(row["goals"] or 0),
                    "assists": int(row["assists"] or 0),
                    "pim": int(row["pim"] or 0),
                    "shg": int(row["shg"] or 0),
                    "ppg": int(row["ppg"] or 0),
                }
                for row in skaters
            ]

            goalie_rows: list[GoalieSummaryRow] = [
                {
                    "player_name": row["player_name"],
                    "saves": int(row["saves"] or 0),
                    "goals_against": int(row["goals_against"] or 0),
                    "shots_received": int(row["shots_received"] or 0),
                    "wins": int(row["wins"] or 0),
                    "sv_pct": math.nan,
                }
                for row in goalkeepers
            ]

            return {
                "season": season_label,
                "team": {
                    "wins": int(team_row["wins"] or 0),
                    "losses": int(team_row["losses"] or 0),
                },
                "skaters": skater_rows,
                "goalkeepers": goalie_rows,
            }


class SqliteMailingListRepository:
    def __init__(self, db: SqliteDatabase) -> None:
        self.db = db

    def add_recipient(self, name: str, email: str) -> int:
        with self.db.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO mail_recipients(name, email) VALUES (?, ?)",
                (name, email),
            )
            return _last_row_id(cursor)

    def remove_recipient(self, recipient_id: int) -> None:
        with self.db.connect() as conn:
            conn.execute("DELETE FROM mail_recipients WHERE id = ?", (recipient_id,))

    def list_recipients(self) -> list[MailRecipient]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT id, name, email FROM mail_recipients ORDER BY email").fetchall()
        return [MailRecipient(id=row["id"], name=row["name"], email=row["email"]) for row in rows]


class SqliteEmailLogRepository:
    def __init__(self, db: SqliteDatabase) -> None:
        self.db = db

    def log_email(self, subject: str, recipients_csv: str, success: bool, detail: str) -> None:
        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT INTO email_logs(subject, recipients, success, detail)
                VALUES (?, ?, ?, ?)
                """,
                (subject, recipients_csv, 1 if success else 0, detail),
            )
