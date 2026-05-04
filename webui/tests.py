from __future__ import annotations

import os
import tempfile
from pathlib import Path

from django.test import Client, SimpleTestCase

from app.domain.models import SkaterGameStatInput
from app.service_factory import build_service


class ServiceSpecTests(SimpleTestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "service.sqlite3"
        self.service = build_service(self.db_path)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_rejects_dates_outside_hockey_season(self) -> None:
        player_id = self.service.add_player(
            "Alex Example",
            "skater",
            "permanent",
            season_label="2025-26",
            default_jersey_number=12,
        )

        with self.assertRaisesMessage(ValueError, "September through April"):
            self.service.record_game_stats(
                season_label="",
                game_date="2026-05-01",
                opponent="Tigers",
                result="win",
                game_type="regular",
                notes="",
                skater_stats=[SkaterGameStatInput(player_id=player_id, goals=1)],
                goalie_stats=[],
            )

    def test_correction_rejects_cross_season_date_change(self) -> None:
        player_id = self.service.add_player(
            "Alex Example",
            "skater",
            "permanent",
            season_label="2025-26",
            default_jersey_number=12,
        )
        game_id = self.service.record_game_stats(
            season_label="",
            game_date="2026-04-02",
            opponent="Tigers",
            result="win",
            game_type="regular",
            notes="",
            skater_stats=[SkaterGameStatInput(player_id=player_id, goals=1)],
            goalie_stats=[],
        )

        with self.assertRaisesMessage(ValueError, "different season"):
            self.service.correct_game_stats(
                game_id=game_id,
                season_label="",
                game_date="2026-09-15",
                opponent="Tigers",
                result="win",
                game_type="regular",
                notes="",
                skater_stats=[SkaterGameStatInput(player_id=player_id, goals=2)],
                goalie_stats=[],
            )

    def test_season_summary_includes_default_jersey_number(self) -> None:
        player_id = self.service.add_player(
            "Alex Example",
            "skater",
            "permanent",
            season_label="2025-26",
            default_jersey_number=12,
        )
        self.service.record_game_stats(
            season_label="",
            game_date="2026-04-02",
            opponent="Tigers",
            result="win",
            game_type="regular",
            notes="",
            skater_stats=[SkaterGameStatInput(player_id=player_id, goals=1)],
            goalie_stats=[],
        )

        summary = self.service.get_season_stats("2025-26")

        self.assertEqual(summary["regular"]["skaters"][0]["jersey_number"], 12)


class WebUiTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tempdir.name) / "web.sqlite3"
        os.environ["HOCKEY_STATS_DB_PATH"] = str(cls.db_path)
        service = build_service(cls.db_path)
        player_id = service.add_player(
            "Alex Example",
            "skater",
            "permanent",
            season_label="2025-26",
            default_jersey_number=12,
        )
        service.record_game_stats(
            season_label="",
            game_date="2026-04-02",
            opponent="Tigers",
            result="win",
            game_type="regular",
            notes="",
            skater_stats=[SkaterGameStatInput(player_id=player_id, goals=1, assists=2)],
            goalie_stats=[],
        )

    @classmethod
    def tearDownClass(cls) -> None:
        os.environ.pop("HOCKEY_STATS_DB_PATH", None)
        cls.tempdir.cleanup()
        super().tearDownClass()

    def setUp(self) -> None:
        self.client = Client()

    def test_new_game_page_uses_browser_date_picker_without_season_field(self) -> None:
        response = self.client.get("/games/new/")
        self.assertContains(response, 'type="date"')
        self.assertNotContains(response, 'name="season_label"')
        self.assertContains(response, "Derived season")

    def test_dashboard_displays_jersey_column(self) -> None:
        response = self.client.get("/", {"season": "2025-26"})
        self.assertContains(response, "Jersey")
        self.assertContains(response, "Alex Example")
        self.assertContains(response, ">12<")
