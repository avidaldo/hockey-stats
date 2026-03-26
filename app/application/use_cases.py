from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Protocol, TypedDict

from app.domain.models import GoalieGameStatInput, MailRecipient, Player, SkaterGameStatInput
from app.domain.services import calculate_save_percentage


class PlayerRepository(Protocol):
    def add_player(self, name: str, role: str) -> int:
        ...

    def remove_player(self, player_id: int) -> None:
        ...

    def list_active_players(self) -> list[Player]:
        ...


class GameRepository(Protocol):
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
        ...

    def get_season_summary(self, season_label: str) -> "SeasonSummary":
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
    team: TeamSummary
    skaters: list[SkaterSummaryRow]
    goalkeepers: list[GoalieSummaryRow]


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

    def add_player(self, name: str, role: str) -> int:
        normalized_name = name.strip()
        normalized_role = role.strip().lower()
        if not normalized_name:
            raise ValueError("Player name is required")
        if normalized_role not in {"skater", "goalkeeper"}:
            raise ValueError("Role must be 'skater' or 'goalkeeper'")
        return self.players.add_player(normalized_name, normalized_role)

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
        notes: str,
        skater_stats: list[SkaterGameStatInput],
        goalie_stats: list[GoalieGameStatInput],
    ) -> int:
        if not season_label.strip():
            raise ValueError("Season label is required")
        if not opponent.strip():
            raise ValueError("Opponent is required")
        if result not in {"win", "loss"}:
            raise ValueError("Result must be 'win' or 'loss'")
        dt.date.fromisoformat(game_date)

        if not skater_stats and not goalie_stats:
            raise ValueError("At least one stat line is required")

        self._validate_stat_lines(skater_stats, goalie_stats)

        return self.games.record_game(
            season_label=season_label.strip(),
            game_date=game_date,
            opponent=opponent.strip(),
            result=result,
            notes=notes.strip(),
            skater_stats=skater_stats,
            goalie_stats=goalie_stats,
        )

    def get_season_stats(self, season_label: str) -> SeasonSummary:
        raw = self.games.get_season_summary(season_label.strip())

        for goalie in raw["goalkeepers"]:
            goalie["sv_pct"] = calculate_save_percentage(goalie["saves"], goalie["shots_received"])

        return raw

    def send_season_stats_email(self, season_label: str) -> tuple[bool, str]:
        summary = self.get_season_stats(season_label)
        recipients = [recipient.email for recipient in self.list_mail_recipients()]
        if not recipients:
            raise ValueError("No mail recipients configured")

        subject = f"Hockey stats update - {season_label}"
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
            if min(stat.saves, stat.goals_against, stat.shots_received) < 0:
                raise ValueError("Goalkeeper stats cannot be negative")

    @staticmethod
    def _format_summary_email(summary: SeasonSummary) -> str:
        lines = [
            f"Season: {summary['season']}",
            f"Team record: {summary['team']['wins']}W-{summary['team']['losses']}L",
            "",
            "Skaters:",
        ]
        for row in summary["skaters"]:
            lines.append(
                f"- {row['player_name']}: G={row['goals']} A={row['assists']} PIM={row['pim']} SHG={row['shg']} PPG={row['ppg']}"
            )

        lines.append("")
        lines.append("Goalkeepers:")
        for row in summary["goalkeepers"]:
            sv_display = "NaN" if row["sv_pct"] != row["sv_pct"] else f"{row['sv_pct']:.3f}"
            lines.append(
                f"- {row['player_name']}: Saves={row['saves']} GA={row['goals_against']} Wins={row['wins']} SV%={sv_display}"
            )

        return "\n".join(lines)
