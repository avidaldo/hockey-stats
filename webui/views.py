from __future__ import annotations

import datetime as dt
import json
from urllib.parse import urlencode

from django.forms import formset_factory
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from app.domain.models import Player
from app.service_factory import build_service
from webui.forms import (
    GameForm,
    GoalieLineForm,
    MailRecipientForm,
    PlayerForm,
    ResendForm,
    SeasonFilterForm,
    SkaterLineForm,
)

SKATER_FORMSET = formset_factory(SkaterLineForm, extra=4)
GOALIE_FORMSET = formset_factory(GoalieLineForm, extra=2)
SAFE_REDIRECT_ROUTES = {
    "dashboard",
    "roster",
    "correction-picker",
    "mailing",
}


def _service():
    return build_service()


def _player_label(player: Player) -> str:
    detail = f"{player.role.title()} · {player.player_type.title()}"
    if player.default_jersey_number is not None:
        detail = f"{detail} · #{player.default_jersey_number}"
    return f"{player.name} ({detail})"


def _redirect_with_notice(route_name: str, *, notice: str | None = None, error: str | None = None, **params: str) -> HttpResponse:
    if route_name not in SAFE_REDIRECT_ROUTES:
        raise ValueError("Unsupported redirect route")
    query = {k: v for k, v in params.items() if v}
    if notice:
        query["notice"] = notice
    if error:
        query["error"] = error
    url = reverse(route_name)
    if not url.startswith("/"):
        raise ValueError("Expected a local redirect path")
    if query:
        url = f"{url}?{urlencode(query)}"
    return HttpResponseRedirect(url)


def _player_choices(season_label: str) -> tuple[list[Player], list[tuple[int, str]], dict[str, int]]:
    players = _service().list_active_players(season_label)
    choices = [(player.id, _player_label(player)) for player in players]
    defaults = {
        str(player.id): player.default_jersey_number
        for player in players
        if player.default_jersey_number is not None and player.player_type == "permanent"
    }
    return players, choices, defaults


def _build_formsets(
    season_label: str,
    *,
    data: dict | None = None,
    initial_skaters: list[dict] | None = None,
    initial_goalies: list[dict] | None = None,
):
    _, player_choices, _ = _player_choices(season_label)
    skaters = SKATER_FORMSET(
        data=data or None,
        prefix="skaters",
        initial=initial_skaters,
        form_kwargs={"player_choices": player_choices},
    )
    goalies = GOALIE_FORMSET(
        data=data or None,
        prefix="goalies",
        initial=initial_goalies,
        form_kwargs={"player_choices": player_choices},
    )
    return skaters, goalies


def _season_preview(game_form: GameForm) -> str | None:
    raw_date = game_form.data.get(game_form.add_prefix("game_date")) if game_form.is_bound else game_form.initial.get("game_date")
    if isinstance(raw_date, dt.date):
        raw_date = raw_date.isoformat()
    if not raw_date:
        return None
    try:
        return _service().derive_season_label(str(raw_date))
    except ValueError:
        return None


def _extract_stats(formset):
    stats = []
    for form in formset:
        if not form.is_valid():
            continue
        if not form.has_meaningful_data():
            continue
        stats.append(form.to_input())
    return stats


def dashboard(request: HttpRequest) -> HttpResponse:
    service = _service()
    season = request.GET.get("season", service.default_season_label())
    summary = service.get_season_stats(season)
    return render(
        request,
        "webui/dashboard.html",
        {
            "season": season,
            "summary": summary,
            "season_blocks": [
                ("Regular season", summary["regular"]),
                ("Playoffs", summary["playoff"]),
            ],
            "notice": request.GET.get("notice", ""),
            "error": request.GET.get("error", ""),
        },
    )


def roster(request: HttpRequest) -> HttpResponse:
    service = _service()
    season = request.GET.get("season", service.default_season_label())
    notice = request.GET.get("notice", "")
    error = request.GET.get("error", "")

    if request.method == "POST":
        form = PlayerForm(request.POST)
        if form.is_valid():
            try:
                service.add_player(
                    name=form.cleaned_data["name"],
                    role=form.cleaned_data["role"],
                    player_type=form.cleaned_data["player_type"],
                    season_label=form.cleaned_data["season_label"],
                    default_jersey_number=form.cleaned_data.get("default_jersey_number"),
                )
                return _redirect_with_notice("roster", season=form.cleaned_data["season_label"], notice="Player added.")
            except ValueError as exc:
                error = str(exc)
    else:
        form = PlayerForm(initial={"season_label": season, "player_type": "permanent", "role": "skater"})

    players = service.list_active_players(season)
    return render(
        request,
        "webui/roster.html",
        {
            "form": form,
            "players": players,
            "season": season,
            "notice": notice,
            "error": error,
        },
    )


def edit_player(request: HttpRequest, player_id: int) -> HttpResponse:
    service = _service()
    season = request.GET.get("season", service.default_season_label())
    player = next((item for item in service.list_active_players(season) if item.id == player_id), None)
    if player is None:
        return _redirect_with_notice("roster", season=season, error="Player not found.")

    if request.method == "POST":
        form = PlayerForm(request.POST)
        if form.is_valid():
            try:
                service.edit_player(
                    player_id=player_id,
                    name=form.cleaned_data["name"],
                    role=form.cleaned_data["role"],
                    player_type=form.cleaned_data["player_type"],
                    season_label=form.cleaned_data["season_label"],
                    default_jersey_number=form.cleaned_data.get("default_jersey_number"),
                )
                return _redirect_with_notice("roster", season=form.cleaned_data["season_label"], notice="Player updated.")
            except ValueError as exc:
                return render(
                    request,
                    "webui/player_edit.html",
                    {"form": form, "player": player, "season": season, "error": str(exc)},
                )
    else:
        form = PlayerForm(
            initial={
                "season_label": season,
                "name": player.name,
                "role": player.role,
                "player_type": player.player_type,
                "default_jersey_number": player.default_jersey_number,
            }
        )

    return render(request, "webui/player_edit.html", {"form": form, "player": player, "season": season, "error": ""})


def remove_player(request: HttpRequest, player_id: int) -> HttpResponse:
    if request.method == "POST":
        season = request.POST.get("season") or _service().default_season_label()
        _service().remove_player(player_id)
        return _redirect_with_notice("roster", season=season, notice="Player removed from the active roster.")
    return _redirect_with_notice("roster")


def new_game(request: HttpRequest) -> HttpResponse:
    service = _service()
    date_initial = dt.date.today()
    season_guess = service.default_season_label(date_initial)

    if request.method == "POST":
        game_form = GameForm(request.POST)
        raw_game_date = request.POST.get("game_date", "")
        try:
            season_guess = service.derive_season_label(raw_game_date)
        except ValueError:
            season_guess = service.default_season_label()
        skater_formset, goalie_formset = _build_formsets(season_guess, data=request.POST)
        if game_form.is_valid() and skater_formset.is_valid() and goalie_formset.is_valid():
            try:
                service.record_game_stats(
                    season_label=None,  # None tells the service to derive the season from game_date.
                    game_date=game_form.cleaned_data["game_date"].isoformat(),
                    opponent=game_form.cleaned_data["opponent"],
                    result=game_form.cleaned_data["result"],
                    game_type=game_form.cleaned_data["game_type"],
                    notes=game_form.cleaned_data["notes"],
                    skater_stats=_extract_stats(skater_formset),
                    goalie_stats=_extract_stats(goalie_formset),
                )
                season_label = service.derive_season_label(game_form.cleaned_data["game_date"].isoformat())
                return _redirect_with_notice("dashboard", season=season_label, notice="Game saved and summary email triggered.")
            except ValueError as exc:
                error = str(exc)
            else:
                error = ""
        else:
            error = "Please correct the highlighted form errors."
    else:
        game_form = GameForm(initial={"game_date": date_initial, "result": "win", "game_type": "regular"})
        skater_formset, goalie_formset = _build_formsets(season_guess)
        error = request.GET.get("error", "")

    _, _, player_defaults = _player_choices(season_guess)
    return render(
        request,
        "webui/game_form.html",
        {
            "title": "Record game",
            "submit_label": "Save game",
            "game_form": game_form,
            "skater_formset": skater_formset,
            "goalie_formset": goalie_formset,
            "season_preview": _season_preview(game_form),
            "player_defaults_json": json.dumps(player_defaults),
            "error": error,
            "editing": False,
        },
    )


def correction_picker(request: HttpRequest) -> HttpResponse:
    service = _service()
    season = request.GET.get("season", service.default_season_label())
    form = SeasonFilterForm(initial={"season_label": season})
    games = service.list_games_by_season(season)
    return render(request, "webui/correction_picker.html", {"form": form, "games": games, "season": season})


def edit_game(request: HttpRequest, game_id: int) -> HttpResponse:
    service = _service()
    game = service.get_game_by_id(game_id)
    if game is None:
        return _redirect_with_notice("correction-picker", error="Game not found.")
    season_label = game["season_label"]

    if request.method == "POST":
        game_form = GameForm(request.POST)
        try:
            season_label = service.derive_season_label(request.POST.get("game_date", ""))
        except ValueError:
            season_label = game["season_label"]
        skater_formset, goalie_formset = _build_formsets(season_label, data=request.POST)
        if game_form.is_valid() and skater_formset.is_valid() and goalie_formset.is_valid():
            try:
                service.correct_game_stats(
                    game_id=game_id,
                    season_label=None,  # None tells the service to derive the season from game_date.
                    game_date=game_form.cleaned_data["game_date"].isoformat(),
                    opponent=game_form.cleaned_data["opponent"],
                    result=game_form.cleaned_data["result"],
                    game_type=game_form.cleaned_data["game_type"],
                    notes=game_form.cleaned_data["notes"],
                    skater_stats=_extract_stats(skater_formset),
                    goalie_stats=_extract_stats(goalie_formset),
                )
                return _redirect_with_notice(
                    "dashboard",
                    season=game["season_label"],
                    notice="Game corrected and summary email triggered.",
                )
            except ValueError as exc:
                error = str(exc)
            else:
                error = ""
        else:
            error = "Please correct the highlighted form errors."
    else:
        game_form = GameForm(
            initial={
                "game_date": dt.date.fromisoformat(game["date"]),
                "opponent": game["opponent"],
                "result": game["result"],
                "game_type": game["game_type"],
                "notes": game["notes"],
            }
        )
        skater_formset, goalie_formset = _build_formsets(
            season_label,
            initial_skaters=[
                {
                    "player_id": stat.player_id,
                    "jersey_number": stat.jersey_number,
                    "goals": stat.goals,
                    "assists": stat.assists,
                    "pim": stat.pim,
                    "shg": stat.shg,
                    "ppg": stat.ppg,
                }
                for stat in game["skater_stats"]
            ],
            initial_goalies=[
                {
                    "player_id": stat.player_id,
                    "jersey_number": stat.jersey_number,
                    "saves": stat.saves,
                    "goals_against": stat.goals_against,
                }
                for stat in game["goalie_stats"]
            ],
        )
        error = request.GET.get("error", "")

    _, _, player_defaults = _player_choices(season_label)
    return render(
        request,
        "webui/game_form.html",
        {
            "title": f"Correct game vs {game['opponent']}",
            "submit_label": "Save correction",
            "game_form": game_form,
            "skater_formset": skater_formset,
            "goalie_formset": goalie_formset,
            "season_preview": _season_preview(game_form),
            "player_defaults_json": json.dumps(player_defaults),
            "error": error,
            "editing": True,
            "game": game,
        },
    )


def mailing(request: HttpRequest) -> HttpResponse:
    service = _service()
    season = request.GET.get("season", service.default_season_label())
    notice = request.GET.get("notice", "")
    error = request.GET.get("error", "")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add":
            add_form = MailRecipientForm(request.POST)
            resend_form = ResendForm(initial={"season_label": season})
            if add_form.is_valid():
                try:
                    service.add_mail_recipient(add_form.cleaned_data.get("name", ""), add_form.cleaned_data["email"])
                    return _redirect_with_notice("mailing", season=season, notice="Recipient added.")
                except ValueError as exc:
                    error = str(exc)
        elif action == "resend":
            resend_form = ResendForm(request.POST)
            add_form = MailRecipientForm()
            if resend_form.is_valid():
                try:
                    success, detail = service.send_season_stats_email(resend_form.cleaned_data["season_label"])
                    if success:
                        return _redirect_with_notice("mailing", season=resend_form.cleaned_data["season_label"], notice=detail)
                    return _redirect_with_notice("mailing", season=resend_form.cleaned_data["season_label"], error=detail)
                except ValueError as exc:
                    error = str(exc)
        else:
            add_form = MailRecipientForm(initial={"season_label": season})
            resend_form = ResendForm(initial={"season_label": season})
    else:
        add_form = MailRecipientForm()
        resend_form = ResendForm(initial={"season_label": season})

    recipients = service.list_mail_recipients()
    return render(
        request,
        "webui/mailing.html",
        {
            "add_form": add_form,
            "resend_form": resend_form,
            "recipients": recipients,
            "season": season,
            "notice": notice,
            "error": error,
        },
    )


def remove_recipient(request: HttpRequest, recipient_id: int) -> HttpResponse:
    if request.method == "POST":
        season = request.POST.get("season") or _service().default_season_label()
        _service().remove_mail_recipient(recipient_id)
        return _redirect_with_notice("mailing", season=season, notice="Recipient removed.")
    return _redirect_with_notice("mailing")
