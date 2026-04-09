from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from typing import Protocol, TypedDict

from app.domain.models import GoalieGameStatInput, MailRecipient, Player, SkaterGameStatInput
from app.domain.services import calculate_save_percentage

logger = logging.getLogger(__name__)


class PlayerRepository(Protocol):
    def add_player(self, name: str, role: str) -> int: ...
    def edit_player(self, player_id: int, name: str, role: str) -> None: ...
    def remove_player(self, player_id: int) -> None: ...
    def list_active_players(self) -> list[Player]: ...


class GameInfo(TypedDict):
    id: int
    season_label: str
    date: str
    opponent: str
    result: str
    game_type: str
    notes: str


class GameDetail(TypedDict):
    id: int
    season_label: str
    date: str
    opponent: str
    result: str
    game_type: str
    notes: str
    skater_stats: list[SkaterGameStatInput]
    goalie_stats: list[GoalieGameStatInput]


class GameRepository(Protocol):
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
    ) -> int: ...

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
    ) -> None: ...

    def get_last_game(self) -> GameDetail | None: ...

    def list_games_by_season(self, season_label: str) -> list[GameInfo]: ...

    def get_game_by_id(self, game_id: int) -> GameDetail | None: ...

    def get_season_summary(self, season_label: str) -> SeasonSummary: ...


class TeamSummary(TypedDict):
    wins: int
    losses: int


class SkaterSummaryRow(TypedDict):
    player_name: str
    goals: int
    assists: int
    pim: int
    shg: int
    ppg: int


class GoalieSummaryRow(TypedDict):
    player_name: str
    saves: int
    goals_against: int
    shots_received: int
    wins: int
    sv_pct: float


class SeasonBlock(TypedDict):
    team: TeamSummary
    skaters: list[SkaterSummaryRow]
    goalies: list[GoalieSummaryRow]


class SeasonSummary(TypedDict):
    season: str
    regular: SeasonBlock
    playoff: SeasonBlock


class MailingListRepository(Protocol):
    def add_recipient(self, name: str, email: str) -> int: ...
    def remove_recipient(self, recipient_id: int) -> None: ...
    def list_recipients(self) -> list[MailRecipient]: ...


class EmailSender(Protocol):
    def send(self, subject: str, body: str, recipients: list[str]) -> tuple[bool, str]: ...


class EmailLogRepository(Protocol):
    def log_email(self, subject: str, recipients_csv: str, success: bool, detail: str) -> None: ...


@dataclass(slots=True)
class HockeyService:
    players: PlayerRepository
    games: GameRepository
    mailing: MailingListRepository
    sender: EmailSender
    email_logs: EmailLogRepository

    def add_player(self, name: str, role: str) -> int:
        normalized_name = name.strip()
        normalized_role = role.strip().lower()
        if not normalized_name:
            raise ValueError("Player name is required")
        if normalized_role not in {"skater", "goalie"}:
            raise ValueError("Role must be 'skater' or 'goalie'")
        return self.players.add_player(normalized_name, normalized_role)

    def edit_player(self, player_id: int, name: str, role: str) -> None:
        normalized_name = name.strip()
        normalized_role = role.strip().lower()
        if not normalized_name:
            raise ValueError("Player name is required")
        if normalized_role not in {"skater", "goalie"}:
            raise ValueError("Role must be 'skater' or 'goalie'")
        self.players.edit_player(player_id, normalized_name, normalized_role)

    def remove_player(self, player_id: int) -> None:
        self.players.remove_player(player_id)

    def list_active_players(self) -> list[Player]:
        return self.players.list_active_players()

    def add_mail_recipient(self, name: str, email: str) -> int:
        normalized_name = name.strip()
        normalized_email = email.strip()
        if not normalized_email or "@" not in normalized_email:
            raise ValueError("Valid email is required")
        if not normalized_name:
            normalized_name = normalized_email
        return self.mailing.add_recipient(normalized_name, normalized_email)

    def remove_mail_recipient(self, recipient_id: int) -> None:
        self.mailing.remove_recipient(recipient_id)

    def list_mail_recipients(self) -> list[MailRecipient]:
        return self.mailing.list_recipients()

    def record_game_stats(
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
        self._validate_game_inputs(season_label, game_date, opponent, result, game_type, skater_stats, goalie_stats)
        game_id = self.games.record_game(
            season_label=season_label.strip(),
            game_date=game_date,
            opponent=opponent.strip(),
            result=result,
            game_type=game_type,
            notes=notes.strip(),
            skater_stats=skater_stats,
            goalie_stats=goalie_stats,
        )
        self._auto_send_email(season_label.strip())
        return game_id

    def correct_game_stats(
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
        self._validate_game_inputs(season_label, game_date, opponent, result, game_type, skater_stats, goalie_stats)
        self.games.correct_game(
            game_id=game_id,
            season_label=season_label.strip(),
            game_date=game_date,
            opponent=opponent.strip(),
            result=result,
            game_type=game_type,
            notes=notes.strip(),
            skater_stats=skater_stats,
            goalie_stats=goalie_stats,
        )
        self._auto_send_email(season_label.strip())

    def get_last_game(self) -> GameDetail | None:
        return self.games.get_last_game()

    def list_games_by_season(self, season_label: str) -> list[GameInfo]:
        return self.games.list_games_by_season(season_label.strip())

    def get_game_by_id(self, game_id: int) -> GameDetail | None:
        return self.games.get_game_by_id(game_id)

    def get_season_stats(self, season_label: str) -> SeasonSummary:
        raw = self.games.get_season_summary(season_label.strip())
        for block in (raw["regular"], raw["playoff"]):
            for goalie in block["goalies"]:
                goalie["sv_pct"] = calculate_save_percentage(goalie["saves"], goalie["shots_received"])
        return raw

    def send_season_stats_email(self, season_label: str) -> tuple[bool, str]:
        summary = self.get_season_stats(season_label)
        recipients = [r.email for r in self.list_mail_recipients()]
        if not recipients:
            raise ValueError("No mail recipients configured")

        subject = f"Hockey stats update - {season_label}"
        body = self._format_summary_email(summary)
        success, detail = self.sender.send(subject=subject, body=body, recipients=recipients)
        self.email_logs.log_email(subject, ",".join(recipients), success, detail)
        return success, detail

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _auto_send_email(self, season_label: str) -> None:
        """Send email silently after a game save/correction; log but never raise."""
        try:
            recipients = [r.email for r in self.list_mail_recipients()]
            if not recipients:
                return
            summary = self.get_season_stats(season_label)
            subject = f"Hockey stats update - {season_label}"
            body = self._format_summary_email(summary)
            success, detail = self.sender.send(subject=subject, body=body, recipients=recipients)
            self.email_logs.log_email(subject, ",".join(recipients), success, detail)
        except Exception:
            logger.exception("Auto-email after game save failed")

    @staticmethod
    def _validate_game_inputs(
        season_label: str,
        game_date: str,
        opponent: str,
        result: str,
        game_type: str,
        skater_stats: list[SkaterGameStatInput],
        goalie_stats: list[GoalieGameStatInput],
    ) -> None:
        if not season_label.strip():
            raise ValueError("Season label is required")
        if not opponent.strip():
            raise ValueError("Opponent is required")
        if result not in {"win", "loss"}:
            raise ValueError("Result must be 'win' or 'loss'")
        if game_type not in {"regular", "playoff"}:
            raise ValueError("Game type must be 'regular' or 'playoff'")
        dt.date.fromisoformat(game_date)
        if not skater_stats and not goalie_stats:
            raise ValueError("At least one stat line is required")
        for stat in skater_stats:
            if min(stat.goals, stat.assists, stat.pim, stat.shg, stat.ppg) < 0:
                raise ValueError("Skater stats cannot be negative")
        for stat in goalie_stats:
            if min(stat.saves, stat.goals_against) < 0:
                raise ValueError("Goalie stats cannot be negative")

    @staticmethod
    def _format_summary_email(summary: SeasonSummary) -> str:
        lines = [f"Season: {summary['season']}"]

        for block_name, block in (("Regular Season", summary["regular"]), ("Playoffs", summary["playoff"])):
            team = block["team"]
            if team["wins"] == 0 and team["losses"] == 0 and not block["skaters"] and not block["goalies"]:
                continue
            lines += [
                "",
                f"── {block_name} ──",
                f"Team record: {team['wins']}W-{team['losses']}L",
                "",
                "Skaters:",
            ]
            for row in block["skaters"]:
                lines.append(
                    f"  {row['player_name']}: G={row['goals']} A={row['assists']} PIM={row['pim']} SHG={row['shg']} PPG={row['ppg']}"
                )
            lines.append("Goalies:")
            for row in block["goalies"]:
                sv_display = "N/A" if row["sv_pct"] != row["sv_pct"] else f"{row['sv_pct']:.3f}"
                lines.append(
                    f"  {row['player_name']}: Saves={row['saves']} GA={row['goals_against']} Wins={row['wins']} SV%={sv_display}"
                )

        return "\n".join(lines)
