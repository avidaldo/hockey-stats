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
                    role TEXT NOT NULL CHECK (role IN ('skater', 'goalie')),
                    number INTEGER,
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
                    season_type TEXT NOT NULL DEFAULT 'regular' CHECK (season_type IN ('regular', 'playoff')),
                    date TEXT NOT NULL,
                    opponent TEXT NOT NULL,
                    result TEXT NOT NULL CHECK (result IN ('win', 'loss')),
                    notes TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY(season_id) REFERENCES seasons(id),
                    UNIQUE(season_id, season_type, date, opponent)
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

    def add_player(self, name: str, role: str, number: int | None = None) -> int:
        with self.db.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO players(name, role, number, active) VALUES (?, ?, ?, 1)",
                (name, role, number),
            )
            return _last_row_id(cursor)

    def update_player(self, player_id: int, name: str, role: str, number: int | None) -> None:
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE players SET name = ?, role = ?, number = ? WHERE id = ?",
                (name, role, number, player_id),
            )

    def get_player(self, player_id: int) -> Player | None:
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT id, name, role, number, active FROM players WHERE id = ?",
                (player_id,),
            ).fetchone()
        if row:
            return Player(
                id=row["id"],
                name=row["name"],
                role=row["role"],
                number=row["number"],
                active=bool(row["active"]),
            )
        return None

    def remove_player(self, player_id: int) -> None:
        with self.db.connect() as conn:
            conn.execute("UPDATE players SET active = 0 WHERE id = ?", (player_id,))

    def list_active_players(self) -> list[Player]:
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT id, name, role, number, active FROM players WHERE active = 1 ORDER BY name"
            ).fetchall()

        return [
            Player(id=row["id"], name=row["name"], role=row["role"], number=row["number"], active=bool(row["active"]))
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

    def check_game_exists(self, season_label: str, season_type: str, game_date: str, opponent: str) -> dict | None:
        """Check if a game already exists and return its details if so."""
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT id FROM seasons WHERE label = ?", (season_label,)
            ).fetchone()
            if not row:
                return None
            season_id = row["id"]
            game_row = conn.execute(
                """
                SELECT id, date, opponent, result FROM games
                WHERE season_id = ? AND season_type = ? AND date = ? AND opponent = ?
                """,
                (season_id, season_type, game_date, opponent),
            ).fetchone()
            if game_row:
                return {
                    "id": game_row["id"],
                    "date": game_row["date"],
                    "opponent": game_row["opponent"],
                    "result": game_row["result"],
                }
        return None

    def list_games(self, season_label: str, season_type: str | None = None) -> list[dict]:
        """List games for a season, optionally filtered by season_type."""
        with self.db.connect() as conn:
            season_row = conn.execute("SELECT id FROM seasons WHERE label = ?", (season_label,)).fetchone()
            if not season_row:
                return []
            season_id = season_row["id"]
            if season_type:
                rows = conn.execute(
                    "SELECT id, season_type, date, opponent, result, notes FROM games WHERE season_id = ? AND season_type = ? ORDER BY date DESC",
                    (season_id, season_type),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, season_type, date, opponent, result, notes FROM games WHERE season_id = ? ORDER BY date DESC",
                    (season_id,),
                ).fetchall()
            return [
                {
                    "id": row["id"],
                    "season_type": row["season_type"],
                    "date": row["date"],
                    "opponent": row["opponent"],
                    "result": row["result"],
                    "notes": row["notes"],
                }
                for row in rows
            ]

    def get_game_stats(self, game_id: int) -> dict:
        """Get all stats for a specific game."""
        with self.db.connect() as conn:
            game_row = conn.execute(
                """
                SELECT g.id, g.season_type, g.date, g.opponent, g.result, g.notes, s.label as season_label
                FROM games g
                JOIN seasons s ON s.id = g.season_id
                WHERE g.id = ?
                """,
                (game_id,),
            ).fetchone()
            if not game_row:
                return {}
            skater_rows = conn.execute(
                """
                SELECT ss.player_id, p.name as player_name, ss.goals, ss.assists, ss.pim, ss.shg, ss.ppg
                FROM skater_game_stats ss
                JOIN players p ON p.id = ss.player_id
                WHERE ss.game_id = ?
                """,
                (game_id,),
            ).fetchall()
            goalie_rows = conn.execute(
                """
                SELECT gs.player_id, p.name as player_name, gs.saves, gs.goals_against, gs.shots_received
                FROM goalie_game_stats gs
                JOIN players p ON p.id = gs.player_id
                WHERE gs.game_id = ?
                """,
                (game_id,),
            ).fetchall()
            return {
                "id": game_row["id"],
                "season_label": game_row["season_label"],
                "season_type": game_row["season_type"],
                "date": game_row["date"],
                "opponent": game_row["opponent"],
                "result": game_row["result"],
                "notes": game_row["notes"],
                "skaters": [
                    {
                        "player_id": row["player_id"],
                        "player_name": row["player_name"],
                        "goals": row["goals"],
                        "assists": row["assists"],
                        "pim": row["pim"],
                        "shg": row["shg"],
                        "ppg": row["ppg"],
                    }
                    for row in skater_rows
                ],
                "goalies": [
                    {
                        "player_id": row["player_id"],
                        "player_name": row["player_name"],
                        "saves": row["saves"],
                        "goals_against": row["goals_against"],
                        "shots_received": row["shots_received"],
                    }
                    for row in goalie_rows
                ],
            }

    def update_game(
        self,
        game_id: int,
        result: str,
        notes: str,
        skater_stats: list[SkaterGameStatInput],
        goalie_stats: list[GoalieGameStatInput],
    ) -> None:
        """Update an existing game's stats."""
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE games SET result = ?, notes = ? WHERE id = ?",
                (result, notes, game_id),
            )
            # Delete existing stats and re-insert
            conn.execute("DELETE FROM skater_game_stats WHERE game_id = ?", (game_id,))
            conn.execute("DELETE FROM goalie_game_stats WHERE game_id = ?", (game_id,))
            for stat in skater_stats:
                conn.execute(
                    """
                    INSERT INTO skater_game_stats(game_id, player_id, goals, assists, pim, shg, ppg)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (game_id, stat.player_id, stat.goals, stat.assists, stat.pim, stat.shg, stat.ppg),
                )
            for stat in goalie_stats:
                shots_received = stat.saves + stat.goals_against
                conn.execute(
                    """
                    INSERT INTO goalie_game_stats(game_id, player_id, saves, goals_against, shots_received)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (game_id, stat.player_id, stat.saves, stat.goals_against, shots_received),
                )

    def record_game(
        self,
        season_label: str,
        season_type: str,
        game_date: str,
        opponent: str,
        result: str,
        notes: str,
        skater_stats: list[SkaterGameStatInput],
        goalie_stats: list[GoalieGameStatInput],
    ) -> int:
        with self.db.connect() as conn:
            season_id = self._get_or_create_season_id(conn, season_label)
            
            # Check for existing game first
            existing = conn.execute(
                """
                SELECT id FROM games
                WHERE season_id = ? AND season_type = ? AND date = ? AND opponent = ?
                """,
                (season_id, season_type, game_date, opponent),
            ).fetchone()
            if existing:
                raise ValueError(
                    f"A game against '{opponent}' on {game_date} ({season_type}) already exists.\n\n"
                    f"To update this game, please use the 'Edit Game' feature instead."
                )
            
            cursor = conn.execute(
                """
                INSERT INTO games(season_id, season_type, date, opponent, result, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (season_id, season_type, game_date, opponent, result, notes),
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
                shots_received = stat.saves + stat.goals_against
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

    def get_season_summary(self, season_label: str, season_type: str | None = None) -> SeasonSummary:
        with self.db.connect() as conn:
            season_row = conn.execute("SELECT id FROM seasons WHERE label = ?", (season_label,)).fetchone()
            if not season_row:
                return {
                    "season": season_label,
                    "season_type": season_type or "all",
                    "team": {"wins": 0, "losses": 0},
                    "skaters": [],
                    "goalies": [],
                }

            season_id = int(season_row["id"])
            
            # Build WHERE clause for season_type filtering
            type_filter = "" if not season_type else f" AND g.season_type = '{season_type}'"
            games_type_filter = "" if not season_type else f" AND season_type = '{season_type}'"

            team_row = conn.execute(
                f"""
                SELECT
                    SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
                    SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) AS losses
                FROM games
                WHERE season_id = ?{games_type_filter}
                """,
                (season_id,),
            ).fetchone()

            skaters = conn.execute(
                f"""
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
                WHERE g.season_id = ?{type_filter}
                GROUP BY s.player_id, p.name
                ORDER BY p.name
                """,
                (season_id,),
            ).fetchall()

            goalies = conn.execute(
                f"""
                SELECT
                    p.name AS player_name,
                    SUM(gs.saves) AS saves,
                    SUM(gs.goals_against) AS goals_against,
                    SUM(gs.shots_received) AS shots_received,
                    SUM(CASE WHEN g.result = 'win' THEN 1 ELSE 0 END) AS wins
                FROM goalie_game_stats gs
                JOIN games g ON g.id = gs.game_id
                JOIN players p ON p.id = gs.player_id
                WHERE g.season_id = ?{type_filter}
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
                for row in goalies
            ]

            return {
                "season": season_label,
                "season_type": season_type or "all",
                "team": {
                    "wins": int(team_row["wins"] or 0),
                    "losses": int(team_row["losses"] or 0),
                },
                "skaters": skater_rows,
                "goalies": goalie_rows,
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
