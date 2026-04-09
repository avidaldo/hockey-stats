from __future__ import annotations

import datetime as dt
import math
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Any

from app.application.use_cases import HockeyService
from app.domain.models import GoalieGameStatInput, SkaterGameStatInput


class HockeyApp(tk.Tk):
    def __init__(self, service: HockeyService) -> None:
        super().__init__()
        self.service = service
        self.title("Liam Hockey Stats")
        self.geometry("1100x740")

        self.pending_skaters: list[SkaterGameStatInput] = []
        self.pending_goalies: list[GoalieGameStatInput] = []
        self._correction_game_id: int | None = None

        self._build_ui()
        self.refresh_players()
        self.refresh_recipients()

    def _build_ui(self) -> None:
        tabs = ttk.Notebook(self)
        tabs.pack(fill=tk.BOTH, expand=True)

        self.roster_tab = ttk.Frame(tabs)
        self.game_tab = ttk.Frame(tabs)
        self.dashboard_tab = ttk.Frame(tabs)
        self.mail_tab = ttk.Frame(tabs)

        tabs.add(self.roster_tab, text="Roster")
        tabs.add(self.game_tab, text="Game Entry")
        tabs.add(self.dashboard_tab, text="Dashboard")
        tabs.add(self.mail_tab, text="Mailing")

        self._build_roster_tab()
        self._build_game_tab()
        self._build_dashboard_tab()
        self._build_mail_tab()

    # ------------------------------------------------------------------
    # Roster tab
    # ------------------------------------------------------------------

    def _build_roster_tab(self) -> None:
        form = ttk.LabelFrame(self.roster_tab, text="Add Player")
        form.pack(fill=tk.X, padx=12, pady=12)

        ttk.Label(form, text="Name").grid(row=0, column=0, padx=8, pady=8, sticky=tk.W)
        self.player_name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.player_name_var, width=30).grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(form, text="Role").grid(row=0, column=2, padx=8, pady=8, sticky=tk.W)
        self.player_role_var = tk.StringVar(value="skater")
        ttk.Combobox(
            form, textvariable=self.player_role_var, values=["skater", "goalie"], width=14, state="readonly"
        ).grid(row=0, column=3, padx=8, pady=8)
        ttk.Button(form, text="Add", command=self.add_player).grid(row=0, column=4, padx=8, pady=8)

        list_frame = ttk.LabelFrame(self.roster_tab, text="Active Players")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        self.players_list = tk.Listbox(list_frame, height=18)
        self.players_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        btn_row = ttk.Frame(list_frame)
        btn_row.pack(anchor=tk.E, padx=8, pady=8)
        ttk.Button(btn_row, text="Edit Selected", command=self.edit_player).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Remove Selected", command=self.remove_player).pack(side=tk.LEFT, padx=4)

    # ------------------------------------------------------------------
    # Game entry tab
    # ------------------------------------------------------------------

    def _build_game_tab(self) -> None:
        self._correction_banner_var = tk.StringVar(value="")
        banner = ttk.Label(self.game_tab, textvariable=self._correction_banner_var, foreground="blue")
        banner.pack(fill=tk.X, padx=12, pady=(8, 0))

        game_meta = ttk.LabelFrame(self.game_tab, text="Game")
        game_meta.pack(fill=tk.X, padx=12, pady=6)

        self.season_var = tk.StringVar(value=f"{dt.date.today().year}-{dt.date.today().year + 1}")
        self.date_var = tk.StringVar(value=dt.date.today().isoformat())
        self.opponent_var = tk.StringVar()
        self.result_var = tk.StringVar(value="win")
        self.game_type_var = tk.StringVar(value="regular")
        self.notes_var = tk.StringVar()

        ttk.Label(game_meta, text="Season").grid(row=0, column=0, padx=8, pady=6, sticky=tk.W)
        ttk.Entry(game_meta, textvariable=self.season_var, width=16).grid(row=0, column=1, padx=8, pady=6)
        ttk.Label(game_meta, text="Date (YYYY-MM-DD)").grid(row=0, column=2, padx=8, pady=6, sticky=tk.W)
        ttk.Entry(game_meta, textvariable=self.date_var, width=14).grid(row=0, column=3, padx=8, pady=6)

        ttk.Label(game_meta, text="Opponent").grid(row=1, column=0, padx=8, pady=6, sticky=tk.W)
        ttk.Entry(game_meta, textvariable=self.opponent_var, width=20).grid(row=1, column=1, padx=8, pady=6)
        ttk.Label(game_meta, text="Result").grid(row=1, column=2, padx=8, pady=6, sticky=tk.W)
        ttk.Combobox(
            game_meta, textvariable=self.result_var, values=["win", "loss"], state="readonly", width=12
        ).grid(row=1, column=3, padx=8, pady=6)

        ttk.Label(game_meta, text="Game Type").grid(row=2, column=0, padx=8, pady=6, sticky=tk.W)
        ttk.Combobox(
            game_meta, textvariable=self.game_type_var, values=["regular", "playoff"], state="readonly", width=12
        ).grid(row=2, column=1, padx=8, pady=6)
        ttk.Label(game_meta, text="Notes").grid(row=2, column=2, padx=8, pady=6, sticky=tk.W)
        ttk.Entry(game_meta, textvariable=self.notes_var, width=42).grid(
            row=2, column=3, padx=8, pady=6, sticky=tk.W
        )

        lines = ttk.Frame(self.game_tab)
        lines.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        # Skater line
        skater_box = ttk.LabelFrame(lines, text="Add Skater Line")
        skater_box.pack(fill=tk.X, pady=4)

        self.skater_player_var = tk.StringVar()
        self.s_jersey = tk.StringVar(value="")
        self.s_goals = tk.StringVar(value="0")
        self.s_assists = tk.StringVar(value="0")
        self.s_pim = tk.StringVar(value="0")
        self.s_shg = tk.StringVar(value="0")
        self.s_ppg = tk.StringVar(value="0")

        self.skater_player_combo = ttk.Combobox(
            skater_box, textvariable=self.skater_player_var, state="readonly", width=22
        )
        self.skater_player_combo.grid(row=0, column=0, padx=6, pady=6)
        ttk.Entry(skater_box, textvariable=self.s_jersey, width=5).grid(row=0, column=1, padx=4)
        ttk.Entry(skater_box, textvariable=self.s_goals, width=5).grid(row=0, column=2, padx=4)
        ttk.Entry(skater_box, textvariable=self.s_assists, width=5).grid(row=0, column=3, padx=4)
        ttk.Entry(skater_box, textvariable=self.s_pim, width=5).grid(row=0, column=4, padx=4)
        ttk.Entry(skater_box, textvariable=self.s_shg, width=5).grid(row=0, column=5, padx=4)
        ttk.Entry(skater_box, textvariable=self.s_ppg, width=5).grid(row=0, column=6, padx=4)
        ttk.Button(skater_box, text="Add Skater", command=self.add_skater_line).grid(row=0, column=7, padx=6)

        for col, label in enumerate(["Player", "#", "G", "A", "PIM", "SHG", "PPG"]):
            ttk.Label(skater_box, text=label).grid(row=1, column=col, padx=(6 if col == 0 else 4), sticky=tk.W)

        # Goalie line
        goalie_box = ttk.LabelFrame(lines, text="Add Goalie Line")
        goalie_box.pack(fill=tk.X, pady=4)

        self.goalie_player_var = tk.StringVar()
        self.g_jersey = tk.StringVar(value="")
        self.g_saves = tk.StringVar(value="0")
        self.g_ga = tk.StringVar(value="0")
        self._g_shots_var = tk.StringVar(value="0")  # read-only computed display

        self.goalie_player_combo = ttk.Combobox(
            goalie_box, textvariable=self.goalie_player_var, state="readonly", width=22
        )
        self.goalie_player_combo.grid(row=0, column=0, padx=6, pady=6)
        ttk.Entry(goalie_box, textvariable=self.g_jersey, width=5).grid(row=0, column=1, padx=4)
        ttk.Entry(goalie_box, textvariable=self.g_saves, width=7).grid(row=0, column=2, padx=4)
        ttk.Entry(goalie_box, textvariable=self.g_ga, width=7).grid(row=0, column=3, padx=4)
        ttk.Label(goalie_box, textvariable=self._g_shots_var, width=7, relief="sunken", anchor=tk.CENTER).grid(
            row=0, column=4, padx=4
        )
        ttk.Button(goalie_box, text="Add Goalie", command=self.add_goalie_line).grid(row=0, column=5, padx=6)

        for col, label in enumerate(["Player", "#", "Saves", "GA", "Shots (auto)"]):
            ttk.Label(goalie_box, text=label).grid(row=1, column=col, padx=(6 if col == 0 else 4), sticky=tk.W)

        # Keep shots-received display up to date as user types
        self.g_saves.trace_add("write", self._update_shots_display)
        self.g_ga.trace_add("write", self._update_shots_display)

        pending_box = ttk.LabelFrame(lines, text="Pending Stat Lines")
        pending_box.pack(fill=tk.BOTH, expand=True, pady=4)
        self.pending_lines_list = tk.Listbox(pending_box, height=8)
        self.pending_lines_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        action_row = ttk.Frame(lines)
        action_row.pack(fill=tk.X, pady=4)
        ttk.Button(action_row, text="Save Game", command=self.save_game).pack(side=tk.RIGHT, padx=6)
        ttk.Button(action_row, text="Clear Pending", command=self.clear_pending).pack(side=tk.RIGHT, padx=6)
        ttk.Button(action_row, text="Cancel Correction", command=self.cancel_correction).pack(side=tk.RIGHT, padx=6)

    # ------------------------------------------------------------------
    # Dashboard tab
    # ------------------------------------------------------------------

    def _build_dashboard_tab(self) -> None:
        controls = ttk.Frame(self.dashboard_tab)
        controls.pack(fill=tk.X, padx=12, pady=12)

        self.dashboard_season_var = tk.StringVar(value=f"{dt.date.today().year}-{dt.date.today().year + 1}")
        ttk.Label(controls, text="Season").pack(side=tk.LEFT, padx=6)
        ttk.Entry(controls, textvariable=self.dashboard_season_var, width=16).pack(side=tk.LEFT, padx=6)
        ttk.Button(controls, text="Refresh", command=self.refresh_dashboard).pack(side=tk.LEFT, padx=6)
        ttk.Button(controls, text="Correct Last Game", command=self.load_last_game_for_correction).pack(
            side=tk.RIGHT, padx=6
        )
        ttk.Button(controls, text="Correct Game…", command=self.open_correction_picker).pack(side=tk.RIGHT, padx=6)

        self.dashboard_text = tk.Text(self.dashboard_tab, height=28, state=tk.DISABLED)
        self.dashboard_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

    # ------------------------------------------------------------------
    # Mailing tab
    # ------------------------------------------------------------------

    def _build_mail_tab(self) -> None:
        add_box = ttk.LabelFrame(self.mail_tab, text="Add Recipient")
        add_box.pack(fill=tk.X, padx=12, pady=12)

        self.mail_name_var = tk.StringVar()
        self.mail_email_var = tk.StringVar()
        ttk.Label(add_box, text="Name").grid(row=0, column=0, padx=8, pady=8)
        ttk.Entry(add_box, textvariable=self.mail_name_var, width=30).grid(row=0, column=1, padx=8, pady=8)
        ttk.Label(add_box, text="Email").grid(row=0, column=2, padx=8, pady=8)
        ttk.Entry(add_box, textvariable=self.mail_email_var, width=30).grid(row=0, column=3, padx=8, pady=8)
        ttk.Button(add_box, text="Add", command=self.add_recipient).grid(row=0, column=4, padx=8, pady=8)

        list_box = ttk.LabelFrame(self.mail_tab, text="Recipients")
        list_box.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        self.mail_list = tk.Listbox(list_box, height=14)
        self.mail_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        ttk.Button(list_box, text="Remove Selected", command=self.remove_recipient).pack(
            anchor=tk.E, padx=8, pady=8
        )

        send_box = ttk.LabelFrame(self.mail_tab, text="Resend Stats")
        send_box.pack(fill=tk.X, padx=12, pady=12)
        self.send_season_var = tk.StringVar(value=f"{dt.date.today().year}-{dt.date.today().year + 1}")
        ttk.Label(send_box, text="Season").grid(row=0, column=0, padx=8, pady=8)
        ttk.Entry(send_box, textvariable=self.send_season_var, width=16).grid(row=0, column=1, padx=8, pady=8)
        ttk.Button(send_box, text="Resend", command=self.send_summary).grid(row=0, column=2, padx=8, pady=8)

    # ------------------------------------------------------------------
    # Roster actions
    # ------------------------------------------------------------------

    def refresh_players(self) -> None:
        players = self.service.list_active_players()
        self.players_list.delete(0, tk.END)

        display_values: list[str] = []
        self.player_lookup: dict[str, int] = {}
        for player in players:
            label = f"{player.id} | {player.name} ({player.role})"
            display_values.append(label)
            self.player_lookup[label] = player.id
            self.players_list.insert(tk.END, label)

        self.skater_player_combo["values"] = display_values
        self.goalie_player_combo["values"] = display_values

        if display_values:
            self.skater_player_var.set(display_values[0])
            self.goalie_player_var.set(display_values[0])

    def add_player(self) -> None:
        try:
            self.service.add_player(self.player_name_var.get(), self.player_role_var.get())
            self.player_name_var.set("")
            self.refresh_players()
            messagebox.showinfo("Player added", "Player added successfully.")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Add player failed", str(exc))

    def edit_player(self) -> None:
        players_list_any: Any = self.players_list
        selection = tuple(players_list_any.curselection())
        if not selection:
            messagebox.showwarning("Edit player", "Select a player to edit.")
            return
        selected = str(players_list_any.get(selection[0]))
        player_id = self.player_lookup[selected]

        # Simple inline dialog using simpledialog
        new_name = simpledialog.askstring(
            "Edit Player", "New name:", initialvalue=selected.split(" | ", 1)[1].split(" (")[0]
        )
        if new_name is None:
            return
        new_role = simpledialog.askstring(
            "Edit Player", "New role (skater / goalie):", initialvalue=selected.rsplit("(", 1)[-1].rstrip(")")
        )
        if new_role is None:
            return
        try:
            self.service.edit_player(player_id, new_name, new_role)
            self.refresh_players()
            messagebox.showinfo("Player updated", "Player details saved.")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Edit player failed", str(exc))

    def remove_player(self) -> None:
        players_list_any: Any = self.players_list
        selection = tuple(players_list_any.curselection())
        if not selection:
            return
        selected = str(players_list_any.get(selection[0]))
        player_id = self.player_lookup[selected]
        self.service.remove_player(player_id)
        self.refresh_players()

    # ------------------------------------------------------------------
    # Game entry actions
    # ------------------------------------------------------------------

    def _update_shots_display(self, *_: Any) -> None:
        try:
            shots = int(self.g_saves.get() or 0) + int(self.g_ga.get() or 0)
            self._g_shots_var.set(str(shots))
        except ValueError:
            self._g_shots_var.set("?")

    def add_skater_line(self) -> None:
        try:
            player_label = self.skater_player_var.get()
            player_id = self.player_lookup[player_label]
            jersey_raw = self.s_jersey.get().strip()
            stat = SkaterGameStatInput(
                player_id=player_id,
                goals=int(self.s_goals.get()),
                assists=int(self.s_assists.get()),
                pim=int(self.s_pim.get()),
                shg=int(self.s_shg.get()),
                ppg=int(self.s_ppg.get()),
                jersey_number=int(jersey_raw) if jersey_raw else None,
            )
            self.pending_skaters.append(stat)
            jersey_display = f"#{stat.jersey_number} " if stat.jersey_number is not None else ""
            self.pending_lines_list.insert(
                tk.END,
                f"SKATER {jersey_display}{player_label.split(' | ')[1]} "
                f"G={stat.goals} A={stat.assists} PIM={stat.pim} SHG={stat.shg} PPG={stat.ppg}",
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Invalid skater line", str(exc))

    def add_goalie_line(self) -> None:
        try:
            player_label = self.goalie_player_var.get()
            player_id = self.player_lookup[player_label]
            jersey_raw = self.g_jersey.get().strip()
            stat = GoalieGameStatInput(
                player_id=player_id,
                saves=int(self.g_saves.get()),
                goals_against=int(self.g_ga.get()),
                jersey_number=int(jersey_raw) if jersey_raw else None,
            )
            self.pending_goalies.append(stat)
            shots = stat.saves + stat.goals_against
            jersey_display = f"#{stat.jersey_number} " if stat.jersey_number is not None else ""
            self.pending_lines_list.insert(
                tk.END,
                f"GOALIE {jersey_display}{player_label.split(' | ')[1]} "
                f"Saves={stat.saves} GA={stat.goals_against} Shots={shots}",
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Invalid goalie line", str(exc))

    def clear_pending(self) -> None:
        self.pending_skaters.clear()
        self.pending_goalies.clear()
        self.pending_lines_list.delete(0, tk.END)

    def cancel_correction(self) -> None:
        self._correction_game_id = None
        self._correction_banner_var.set("")
        self.clear_pending()

    def save_game(self) -> None:
        try:
            if self._correction_game_id is not None:
                self.service.correct_game_stats(
                    game_id=self._correction_game_id,
                    season_label=self.season_var.get(),
                    game_date=self.date_var.get(),
                    opponent=self.opponent_var.get(),
                    result=self.result_var.get(),
                    game_type=self.game_type_var.get(),
                    notes=self.notes_var.get(),
                    skater_stats=list(self.pending_skaters),
                    goalie_stats=list(self.pending_goalies),
                )
                self._correction_game_id = None
                self._correction_banner_var.set("")
                messagebox.showinfo("Success", "Game corrected and stats email sent.")
            else:
                self.service.record_game_stats(
                    season_label=self.season_var.get(),
                    game_date=self.date_var.get(),
                    opponent=self.opponent_var.get(),
                    result=self.result_var.get(),
                    game_type=self.game_type_var.get(),
                    notes=self.notes_var.get(),
                    skater_stats=list(self.pending_skaters),
                    goalie_stats=list(self.pending_goalies),
                )
                messagebox.showinfo("Success", "Game saved and stats email sent.")
            self.clear_pending()
            self.refresh_dashboard()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Save game failed", str(exc))

    # ------------------------------------------------------------------
    # Correction helpers
    # ------------------------------------------------------------------

    def load_last_game_for_correction(self) -> None:
        game = self.service.get_last_game()
        if not game:
            messagebox.showinfo("Correct game", "No games recorded yet.")
            return
        self._load_game_into_form(game)

    def open_correction_picker(self) -> None:
        season = self.dashboard_season_var.get().strip()
        games = self.service.list_games_by_season(season)
        if not games:
            messagebox.showinfo("Correct game", f"No games found for season '{season}'.")
            return

        win = tk.Toplevel(self)
        win.title("Select Game to Correct")
        win.geometry("520x300")

        ttk.Label(win, text="Select a game to load for correction:").pack(padx=12, pady=8)
        listbox = tk.Listbox(win, height=12)
        listbox.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        game_ids = [g["id"] for g in games]
        for g in games:
            listbox.insert(
                tk.END,
                f"{g['date']}  vs {g['opponent']}  [{g['game_type']}]  {g['result'].upper()}",
            )

        def on_select() -> None:
            sel = listbox.curselection()
            if not sel:
                return
            game_id = game_ids[sel[0]]
            game = self.service.get_game_by_id(game_id)
            win.destroy()
            if game:
                self._load_game_into_form(game)

        ttk.Button(win, text="Load for Correction", command=on_select).pack(pady=8)

    def _load_game_into_form(self, game: dict) -> None:  # type: ignore[type-arg]
        self._correction_game_id = game["id"]
        self._correction_banner_var.set(
            f"⚠ Correcting game #{game['id']}: {game['date']} vs {game['opponent']} — edit and Save to apply."
        )

        self.season_var.set(game["season_label"])
        self.date_var.set(game["date"])
        self.opponent_var.set(game["opponent"])
        self.result_var.set(game["result"])
        self.game_type_var.set(game["game_type"])
        self.notes_var.set(game["notes"])

        self.clear_pending()
        # Restore stat lines from the game
        for stat in game.get("skater_stats", []):
            self.pending_skaters.append(stat)
            jersey_display = f"#{stat.jersey_number} " if stat.jersey_number is not None else ""
            player_label = next((lbl for lbl, pid in self.player_lookup.items() if pid == stat.player_id), f"p#{stat.player_id}")
            self.pending_lines_list.insert(
                tk.END,
                f"SKATER {jersey_display}{player_label.split(' | ')[-1] if ' | ' in player_label else player_label} "
                f"G={stat.goals} A={stat.assists} PIM={stat.pim}",
            )
        for stat in game.get("goalie_stats", []):
            self.pending_goalies.append(stat)
            shots = stat.saves + stat.goals_against
            jersey_display = f"#{stat.jersey_number} " if stat.jersey_number is not None else ""
            player_label = next((lbl for lbl, pid in self.player_lookup.items() if pid == stat.player_id), f"p#{stat.player_id}")
            self.pending_lines_list.insert(
                tk.END,
                f"GOALIE {jersey_display}{player_label.split(' | ')[-1] if ' | ' in player_label else player_label} "
                f"Saves={stat.saves} GA={stat.goals_against} Shots={shots}",
            )

    # ------------------------------------------------------------------
    # Dashboard actions
    # ------------------------------------------------------------------

    def refresh_dashboard(self) -> None:
        try:
            summary = self.service.get_season_stats(self.dashboard_season_var.get())
            self.dashboard_text.configure(state=tk.NORMAL)
            self.dashboard_text.delete("1.0", tk.END)
            self.dashboard_text.insert(tk.END, f"Season: {summary['season']}\n\n")

            for block_name, block in (("Regular Season", summary["regular"]), ("Playoffs", summary["playoff"])):
                team = block["team"]
                self.dashboard_text.insert(
                    tk.END, f"── {block_name} ──\nTeam: {team['wins']}W - {team['losses']}L\n\nSkaters:\n"
                )
                for row in block["skaters"]:
                    self.dashboard_text.insert(
                        tk.END,
                        f"  {row['player_name']}: G={row['goals']} A={row['assists']} "
                        f"PIM={row['pim']} SHG={row['shg']} PPG={row['ppg']}\n",
                    )
                self.dashboard_text.insert(tk.END, "\nGoalies:\n")
                for row in block["goalies"]:
                    sv = row["sv_pct"]
                    sv_display = "N/A" if math.isnan(sv) else f"{sv:.3f}"
                    self.dashboard_text.insert(
                        tk.END,
                        f"  {row['player_name']}: Saves={row['saves']} GA={row['goals_against']} "
                        f"Shots={row['shots_received']} Wins={row['wins']} SV%={sv_display}\n",
                    )
                self.dashboard_text.insert(tk.END, "\n")

            self.dashboard_text.configure(state=tk.DISABLED)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Dashboard error", str(exc))

    # ------------------------------------------------------------------
    # Mailing actions
    # ------------------------------------------------------------------

    def refresh_recipients(self) -> None:
        recipients = self.service.list_mail_recipients()
        self.mail_list.delete(0, tk.END)
        self.mail_lookup: dict[str, int] = {}
        for recipient in recipients:
            label = f"{recipient.id} | {recipient.name} <{recipient.email}>"
            self.mail_lookup[label] = recipient.id
            self.mail_list.insert(tk.END, label)

    def add_recipient(self) -> None:
        try:
            self.service.add_mail_recipient(self.mail_name_var.get(), self.mail_email_var.get())
            self.mail_name_var.set("")
            self.mail_email_var.set("")
            self.refresh_recipients()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Recipient error", str(exc))

    def remove_recipient(self) -> None:
        mail_list_any: Any = self.mail_list
        selection = tuple(mail_list_any.curselection())
        if not selection:
            return
        selected = str(mail_list_any.get(selection[0]))
        recipient_id = self.mail_lookup[selected]
        self.service.remove_mail_recipient(recipient_id)
        self.refresh_recipients()

    def send_summary(self) -> None:
        try:
            success, detail = self.service.send_season_stats_email(self.send_season_var.get())
            if success:
                messagebox.showinfo("Email", detail)
            else:
                messagebox.showerror("Email", detail)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Email error", str(exc))
