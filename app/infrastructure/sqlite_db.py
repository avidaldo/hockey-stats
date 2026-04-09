from __future__ import annotations

import math
import sqlite3
from pathlib import Path

from app.application.use_cases import (
    GameDetail,
    GameInfo,
    GoalieSummaryRow,
    SeasonBlock,
    SeasonSummary,
    SkaterSummaryRow,
)
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
                    game_type TEXT NOT NULL DEFAULT 'regular' CHECK (game_type IN ('regular', 'playoff')),
                    notes TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY(season_id) REFERENCES seasons(id),
                    UNIQUE(season_id, date, opponent)
                );

                CREATE TABLE IF NOT EXISTS skater_game_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    player_id INTEGER NOT NULL,
                    jersey_number INTEGER,
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
                    jersey_number INTEGER,
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
            self._migrate(conn)

    def _migrate(self, conn: sqlite3.Connection) -> None:
        """Apply incremental schema migrations for existing databases."""
        existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(games)")}
        if "game_type" not in existing_cols:
            conn.execute(
                "ALTER TABLE games ADD COLUMN game_type TEXT NOT NULL DEFAULT 'regular'"
            )

        for table in ("skater_game_stats", "goalie_game_stats"):
            cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            if "jersey_number" not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN jersey_number INTEGER")

        # Migrate role values: 'goalkeeper' → 'goalie' for legacy records
        conn.execute("UPDATE players SET role = 'goalie' WHERE role = 'goalkeeper'")


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

    def edit_player(self, player_id: int, name: str, role: str) -> None:
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE players SET name = ?, role = ? WHERE id = ?",
                (name, role, player_id),
            )

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

    def _season_label_for_id(self, conn: sqlite3.Connection, season_id: int) -> str:
        row = conn.execute("SELECT label FROM seasons WHERE id = ?", (season_id,)).fetchone()
        return str(row["label"]) if row else ""

    def record_game(
        self,
        season_label: str,
        game_date: str,
        opponent: str,
        result: str,
        game_type: str,
        notes: str,
        skater_stats: list[SkaterGameStatInput],
        goalie_stats: list[GoalieGameStatInput],
    ) -> int:
        with self.db.connect() as conn:
            season_id = self._get_or_create_season_id(conn, season_label)
            try:
                cursor = conn.execute(
                    "INSERT INTO games(season_id, date, opponent, result, game_type, notes) VALUES (?, ?, ?, ?, ?, ?)",
                    (season_id, game_date, opponent, result, game_type, notes),
                )
            except sqlite3.IntegrityError:
                raise ValueError(
                    f"Duplicate game detected: a game vs '{opponent}' on {game_date} in season '{season_label}' "
                    f"already exists. Use the 'Correct Game' flow to edit the existing record."
                )
            game_id = _last_row_id(cursor)
            self._insert_stat_lines(conn, game_id, skater_stats, goalie_stats)
            return game_id

    def correct_game(
        self,
        game_id: int,
        season_label: str,
        game_date: str,
        opponent: str,
        result: str,
        game_type: str,
        notes: str,
        skater_stats: list[SkaterGameStatInput],
        goalie_stats: list[GoalieGameStatInput],
    ) -> None:
        with self.db.connect() as conn:
            season_id = self._get_or_create_season_id(conn, season_label)
            conn.execute(
                "UPDATE games SET season_id=?, date=?, opponent=?, result=?, game_type=?, notes=? WHERE id=?",
                (season_id, game_date, opponent, result, game_type, notes, game_id),
            )
            conn.execute("DELETE FROM skater_game_stats WHERE game_id = ?", (game_id,))
            conn.execute("DELETE FROM goalie_game_stats WHERE game_id = ?", (game_id,))
            self._insert_stat_lines(conn, game_id, skater_stats, goalie_stats)

    def get_last_game(self) -> GameDetail | None:
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT g.id, g.season_id, g.date, g.opponent, g.result, g.game_type, g.notes "
                "FROM games g ORDER BY g.id DESC LIMIT 1"
            ).fetchone()
            if not row:
                return None
            return self._build_game_detail(conn, row)

    def list_games_by_season(self, season_label: str) -> list[GameInfo]:
        with self.db.connect() as conn:
            season_row = conn.execute("SELECT id FROM seasons WHERE label = ?", (season_label,)).fetchone()
            if not season_row:
                return []
            rows = conn.execute(
                "SELECT g.id, g.date, g.opponent, g.result, g.game_type, g.notes "
                "FROM games g WHERE g.season_id = ? ORDER BY g.date DESC, g.id DESC",
                (int(season_row["id"]),),
            ).fetchall()
            return [
                GameInfo(
                    id=int(r["id"]),
                    season_label=season_label,
                    date=str(r["date"]),
                    opponent=str(r["opponent"]),
                    result=str(r["result"]),
                    game_type=str(r["game_type"]),
                    notes=str(r["notes"]),
                )
                for r in rows
            ]

    def get_game_by_id(self, game_id: int) -> GameDetail | None:
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT g.id, g.season_id, g.date, g.opponent, g.result, g.game_type, g.notes "
                "FROM games g WHERE g.id = ?",
                (game_id,),
            ).fetchone()
            if not row:
                return None
            return self._build_game_detail(conn, row)

    def _build_game_detail(self, conn: sqlite3.Connection, row: sqlite3.Row) -> GameDetail:
        season_label = self._season_label_for_id(conn, int(row["season_id"]))
        skater_rows = conn.execute(
            "SELECT player_id, jersey_number, goals, assists, pim, shg, ppg FROM skater_game_stats WHERE game_id = ?",
            (int(row["id"]),),
        ).fetchall()
        goalie_rows = conn.execute(
            "SELECT player_id, jersey_number, saves, goals_against FROM goalie_game_stats WHERE game_id = ?",
            (int(row["id"]),),
        ).fetchall()
        return GameDetail(
            id=int(row["id"]),
            season_label=season_label,
            date=str(row["date"]),
            opponent=str(row["opponent"]),
            result=str(row["result"]),
            game_type=str(row["game_type"]),
            notes=str(row["notes"]),
            skater_stats=[
                SkaterGameStatInput(
                    player_id=int(r["player_id"]),
                    goals=int(r["goals"]),
                    assists=int(r["assists"]),
                    pim=int(r["pim"]),
                    shg=int(r["shg"]),
                    ppg=int(r["ppg"]),
                    jersey_number=r["jersey_number"],
                )
                for r in skater_rows
            ],
            goalie_stats=[
                GoalieGameStatInput(
                    player_id=int(r["player_id"]),
                    saves=int(r["saves"]),
                    goals_against=int(r["goals_against"]),
                    jersey_number=r["jersey_number"],
                )
                for r in goalie_rows
            ],
        )

    @staticmethod
    def _insert_stat_lines(
        conn: sqlite3.Connection,
        game_id: int,
        skater_stats: list[SkaterGameStatInput],
        goalie_stats: list[GoalieGameStatInput],
    ) -> None:
        for stat in skater_stats:
            conn.execute(
                "INSERT INTO skater_game_stats(game_id, player_id, jersey_number, goals, assists, pim, shg, ppg) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (game_id, stat.player_id, stat.jersey_number, stat.goals, stat.assists, stat.pim, stat.shg, stat.ppg),
            )
        for stat in goalie_stats:
            shots_received = stat.saves + stat.goals_against
            conn.execute(
                "INSERT INTO goalie_game_stats(game_id, player_id, jersey_number, saves, goals_against, shots_received) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (game_id, stat.player_id, stat.jersey_number, stat.saves, stat.goals_against, shots_received),
            )

    def get_season_summary(self, season_label: str) -> SeasonSummary:
        with self.db.connect() as conn:
            season_row = conn.execute("SELECT id FROM seasons WHERE label = ?", (season_label,)).fetchone()
            if not season_row:
                empty_block: SeasonBlock = {"team": {"wins": 0, "losses": 0}, "skaters": [], "goalies": []}
                return SeasonSummary(season=season_label, regular=empty_block, playoff=dict(empty_block))  # type: ignore[arg-type]

            season_id = int(season_row["id"])
            result: SeasonSummary = SeasonSummary(
                season=season_label,
                regular=self._query_block(conn, season_id, "regular"),
                playoff=self._query_block(conn, season_id, "playoff"),
            )
            return result

    @staticmethod
    def _query_block(conn: sqlite3.Connection, season_id: int, game_type: str) -> SeasonBlock:
        team_row = conn.execute(
            """
            SELECT
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) AS losses
            FROM games
            WHERE season_id = ? AND game_type = ?
            """,
            (season_id, game_type),
        ).fetchone()

        skaters = conn.execute(
            """
            SELECT p.name AS player_name,
                   SUM(s.goals) AS goals, SUM(s.assists) AS assists,
                   SUM(s.pim) AS pim, SUM(s.shg) AS shg, SUM(s.ppg) AS ppg
            FROM skater_game_stats s
            JOIN games g ON g.id = s.game_id
            JOIN players p ON p.id = s.player_id
            WHERE g.season_id = ? AND g.game_type = ?
            GROUP BY s.player_id, p.name ORDER BY p.name
            """,
            (season_id, game_type),
        ).fetchall()

        goalies = conn.execute(
            """
            SELECT p.name AS player_name,
                   SUM(gs.saves) AS saves, SUM(gs.goals_against) AS goals_against,
                   SUM(gs.shots_received) AS shots_received,
                   SUM(CASE WHEN g.result = 'win' THEN 1 ELSE 0 END) AS wins
            FROM goalie_game_stats gs
            JOIN games g ON g.id = gs.game_id
            JOIN players p ON p.id = gs.player_id
            WHERE g.season_id = ? AND g.game_type = ?
            GROUP BY gs.player_id, p.name ORDER BY p.name
            """,
            (season_id, game_type),
        ).fetchall()

        skater_rows: list[SkaterSummaryRow] = [
            SkaterSummaryRow(
                player_name=row["player_name"],
                goals=int(row["goals"] or 0),
                assists=int(row["assists"] or 0),
                pim=int(row["pim"] or 0),
                shg=int(row["shg"] or 0),
                ppg=int(row["ppg"] or 0),
            )
            for row in skaters
        ]
        goalie_rows: list[GoalieSummaryRow] = [
            GoalieSummaryRow(
                player_name=row["player_name"],
                saves=int(row["saves"] or 0),
                goals_against=int(row["goals_against"] or 0),
                shots_received=int(row["shots_received"] or 0),
                wins=int(row["wins"] or 0),
                sv_pct=math.nan,
            )
            for row in goalies
        ]
        return SeasonBlock(
            team={"wins": int(team_row["wins"] or 0), "losses": int(team_row["losses"] or 0)},
            skaters=skater_rows,
            goalies=goalie_rows,
        )


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
                "INSERT INTO email_logs(subject, recipients, success, detail) VALUES (?, ?, ?, ?)",
                (subject, recipients_csv, 1 if success else 0, detail),
            )
