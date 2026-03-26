from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Protocol, TypedDict

from app.domain.models import GoalieGameStatInput, MailRecipient, Player, SkaterGameStatInput
from app.domain.services import calculate_save_percentage


class PlayerRepository(Protocol):
    def add_player(self, name: str, role: str, number: int | None = None) -> int:
        ...

    def update_player(self, player_id: int, name: str, role: str, number: int | None) -> None:
        ...

    def get_player(self, player_id: int) -> Player | None:
        ...

    def remove_player(self, player_id: int) -> None:
        ...

    def list_active_players(self) -> list[Player]:
        ...


class GameRepository(Protocol):
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
        ...

    def update_game(
        self,
        game_id: int,
        result: str,
        notes: str,
        skater_stats: list[SkaterGameStatInput],
        goalie_stats: list[GoalieGameStatInput],
    ) -> None:
        ...

    def list_games(self, season_label: str, season_type: str | None = None) -> list[dict]:
        ...

    def get_game_stats(self, game_id: int) -> dict:
        ...

    def get_season_summary(self, season_label: str, season_type: str | None = None) -> "SeasonSummary":
        ...


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


class SeasonSummary(TypedDict):
    season: str
    season_type: str
    team: TeamSummary
    skaters: list[SkaterSummaryRow]
    goalies: list[GoalieSummaryRow]


class MailingListRepository(Protocol):
    def add_recipient(self, name: str, email: str) -> int:
        ...

    def remove_recipient(self, recipient_id: int) -> None:
        ...

    def list_recipients(self) -> list[MailRecipient]:
        ...


class EmailSender(Protocol):
    def send(self, subject: str, body: str, recipients: list[str]) -> tuple[bool, str]:
        ...


class EmailLogRepository(Protocol):
    def log_email(self, subject: str, recipients_csv: str, success: bool, detail: str) -> None:
        ...


@dataclass(slots=True)
class HockeyService:
    players: PlayerRepository
    games: GameRepository
    mailing: MailingListRepository
    sender: EmailSender
    email_logs: EmailLogRepository

    def add_player(self, name: str, role: str, number: int | None = None) -> int:
        normalized_name = name.strip()
        normalized_role = role.strip().lower()
        if not normalized_name:
            raise ValueError("Player name is required")
        if normalized_role not in {"skater", "goalie"}:
            raise ValueError("Role must be 'skater' or 'goalie'")
        return self.players.add_player(normalized_name, normalized_role, number)

    def update_player(self, player_id: int, name: str, role: str, number: int | None) -> None:
        normalized_name = name.strip()
        normalized_role = role.strip().lower()
        if not normalized_name:
            raise ValueError("Player name is required")
        if normalized_role not in {"skater", "goalie"}:
            raise ValueError("Role must be 'skater' or 'goalie'")
        self.players.update_player(player_id, normalized_name, normalized_role, number)

    def get_player(self, player_id: int) -> Player | None:
        return self.players.get_player(player_id)

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
        season_type: str,
        game_date: str,
        opponent: str,
        result: str,
        notes: str,
        skater_stats: list[SkaterGameStatInput],
        goalie_stats: list[GoalieGameStatInput],
        auto_send_email: bool = True,
    ) -> int:
        if not season_label.strip():
            raise ValueError("Season label is required")
        if not opponent.strip():
            raise ValueError("Opponent is required")
        if result not in {"win", "loss"}:
            raise ValueError("Result must be 'win' or 'loss'")
        if season_type not in {"regular", "playoff"}:
            raise ValueError("Season type must be 'regular' or 'playoff'")
        dt.date.fromisoformat(game_date)

        if not skater_stats and not goalie_stats:
            raise ValueError("At least one stat line is required")

        self._validate_stat_lines(skater_stats, goalie_stats)

        game_id = self.games.record_game(
            season_label=season_label.strip(),
            season_type=season_type,
            game_date=game_date,
            opponent=opponent.strip(),
            result=result,
            notes=notes.strip(),
            skater_stats=skater_stats,
            goalie_stats=goalie_stats,
        )

        # Auto-send email after saving game
        if auto_send_email:
            try:
                self.send_season_stats_email(season_label, season_type)
            except ValueError:
                # No recipients configured, skip email
                pass

        return game_id

    def update_game_stats(
        self,
        game_id: int,
        result: str,
        notes: str,
        skater_stats: list[SkaterGameStatInput],
        goalie_stats: list[GoalieGameStatInput],
    ) -> None:
        if result not in {"win", "loss"}:
            raise ValueError("Result must be 'win' or 'loss'")

        if not skater_stats and not goalie_stats:
            raise ValueError("At least one stat line is required")

        self._validate_stat_lines(skater_stats, goalie_stats)

        self.games.update_game(
            game_id=game_id,
            result=result,
            notes=notes.strip(),
            skater_stats=skater_stats,
            goalie_stats=goalie_stats,
        )

    def list_games(self, season_label: str, season_type: str | None = None) -> list[dict]:
        return self.games.list_games(season_label.strip(), season_type)

    def get_game_stats(self, game_id: int) -> dict:
        return self.games.get_game_stats(game_id)

    def get_season_stats(self, season_label: str, season_type: str | None = None) -> SeasonSummary:
        raw = self.games.get_season_summary(season_label.strip(), season_type)

        for goalie in raw["goalies"]:
            goalie["sv_pct"] = calculate_save_percentage(goalie["saves"], goalie["shots_received"])

        return raw

    def send_season_stats_email(self, season_label: str, season_type: str | None = None) -> tuple[bool, str]:
        summary = self.get_season_stats(season_label, season_type)
        recipients = [recipient.email for recipient in self.list_mail_recipients()]
        if not recipients:
            raise ValueError("No mail recipients configured")

        type_str = f" ({season_type})" if season_type else ""
        subject = f"Hockey stats update - {season_label}{type_str}"
        body = self._format_summary_email(summary)

        success, detail = self.sender.send(subject=subject, body=body, recipients=recipients)
        self.email_logs.log_email(subject, ",".join(recipients), success, detail)
        return success, detail

    @staticmethod
    def _validate_stat_lines(
        skater_stats: list[SkaterGameStatInput],
        goalie_stats: list[GoalieGameStatInput],
    ) -> None:
        for stat in skater_stats:
            if min(stat.goals, stat.assists, stat.pim, stat.shg, stat.ppg) < 0:
                raise ValueError("Skater stats cannot be negative")
        for stat in goalie_stats:
            if min(stat.saves, stat.goals_against) < 0:
                raise ValueError("Goalie stats cannot be negative")

    @staticmethod
    def _format_summary_email(summary: SeasonSummary) -> str:
        type_str = f" ({summary['season_type']})" if summary.get('season_type') and summary['season_type'] != 'all' else ""
        lines = [
            f"Season: {summary['season']}{type_str}",
            f"Team record: {summary['team']['wins']}W-{summary['team']['losses']}L",
            "",
            "Skaters:",
        ]
        for row in summary["skaters"]:
            lines.append(
                f"- {row['player_name']}: G={row['goals']} A={row['assists']} PIM={row['pim']} SHG={row['shg']} PPG={row['ppg']}"
            )

        lines.append("")
        lines.append("Goalies:")
        for row in summary["goalies"]:
            sv_display = "NaN" if row["sv_pct"] != row["sv_pct"] else f"{row['sv_pct']:.3f}"
            lines.append(
                f"- {row['player_name']}: Saves={row['saves']} GA={row['goals_against']} Shots={row['shots_received']} Wins={row['wins']} SV%={sv_display}"
            )

        return "\n".join(lines)
