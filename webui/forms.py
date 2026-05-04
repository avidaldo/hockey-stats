from __future__ import annotations

import datetime as dt

from django import forms

from app.domain.models import GoalieGameStatInput, SkaterGameStatInput

ROLE_CHOICES = [("skater", "Skater"), ("goalie", "Goalie")]
PLAYER_TYPE_CHOICES = [("permanent", "Permanent"), ("substitute", "Substitute")]
RESULT_CHOICES = [("win", "Win"), ("loss", "Loss")]
GAME_TYPE_CHOICES = [("regular", "Regular season"), ("playoff", "Playoff")]


class PlayerForm(forms.Form):
    season_label = forms.CharField(label="Roster season", max_length=16)
    name = forms.CharField(max_length=100)
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    player_type = forms.ChoiceField(choices=PLAYER_TYPE_CHOICES)
    default_jersey_number = forms.IntegerField(min_value=0, required=False)


class MailRecipientForm(forms.Form):
    name = forms.CharField(max_length=100, required=False)
    email = forms.EmailField(max_length=254)


class ResendForm(forms.Form):
    season_label = forms.CharField(label="Season", max_length=16)


class SeasonFilterForm(forms.Form):
    season_label = forms.CharField(label="Season", max_length=16)


class GameForm(forms.Form):
    game_date = forms.DateField(
        label="Date",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}),
        initial=dt.date.today,
    )
    opponent = forms.CharField(max_length=100)
    result = forms.ChoiceField(choices=RESULT_CHOICES, initial="win")
    game_type = forms.ChoiceField(choices=GAME_TYPE_CHOICES, initial="regular")
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class _BaseStatLineForm(forms.Form):
    player_id = forms.TypedChoiceField(coerce=int, required=False, choices=[])
    jersey_number = forms.IntegerField(min_value=0, required=False)

    stat_fields: tuple[str, ...] = ()

    def __init__(self, *args, player_choices: list[tuple[int, str]] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "---------")]
        if player_choices:
            choices.extend((str(player_id), label) for player_id, label in player_choices)
        self.fields["player_id"].choices = choices

    def has_meaningful_data(self) -> bool:
        if self.cleaned_data.get("player_id"):
            return True
        if self.cleaned_data.get("jersey_number") is not None:
            return True
        return any((self.cleaned_data.get(name) or 0) > 0 for name in self.stat_fields)


class SkaterLineForm(_BaseStatLineForm):
    goals = forms.IntegerField(min_value=0, required=False, initial=0)
    assists = forms.IntegerField(min_value=0, required=False, initial=0)
    pim = forms.IntegerField(min_value=0, required=False, initial=0)
    shg = forms.IntegerField(min_value=0, required=False, initial=0)
    ppg = forms.IntegerField(min_value=0, required=False, initial=0)

    stat_fields = ("goals", "assists", "pim", "shg", "ppg")

    def to_input(self) -> SkaterGameStatInput:
        if not self.cleaned_data.get("player_id"):
            raise forms.ValidationError("Select a skater for each filled stat line.")
        return SkaterGameStatInput(
            player_id=self.cleaned_data["player_id"],
            jersey_number=self.cleaned_data.get("jersey_number"),
            goals=self.cleaned_data.get("goals") or 0,
            assists=self.cleaned_data.get("assists") or 0,
            pim=self.cleaned_data.get("pim") or 0,
            shg=self.cleaned_data.get("shg") or 0,
            ppg=self.cleaned_data.get("ppg") or 0,
        )


class GoalieLineForm(_BaseStatLineForm):
    saves = forms.IntegerField(min_value=0, required=False, initial=0)
    goals_against = forms.IntegerField(min_value=0, required=False, initial=0)

    stat_fields = ("saves", "goals_against")

    def to_input(self) -> GoalieGameStatInput:
        if not self.cleaned_data.get("player_id"):
            raise forms.ValidationError("Select a goalie for each filled stat line.")
        return GoalieGameStatInput(
            player_id=self.cleaned_data["player_id"],
            jersey_number=self.cleaned_data.get("jersey_number"),
            saves=self.cleaned_data.get("saves") or 0,
            goals_against=self.cleaned_data.get("goals_against") or 0,
        )
