from __future__ import annotations

import datetime as dt
import math
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from app.application.use_cases import HockeyService
from app.domain.models import GoalieGameStatInput, SkaterGameStatInput


class HockeyApp(tk.Tk):
    def __init__(self, service: HockeyService) -> None:
        super().__init__()
        self.service = service
        self.title("Liam Hockey v2")
        self.geometry("1100x750")

        self.pending_skaters: list[SkaterGameStatInput] = []
        self.pending_goalies: list[GoalieGameStatInput] = []
        self.editing_game_id: int | None = None

        self._build_ui()
        self.refresh_players()
        self.refresh_recipients()

    def _build_ui(self) -> None:
        tabs = ttk.Notebook(self)
        tabs.pack(fill=tk.BOTH, expand=True)

        self.roster_tab = ttk.Frame(tabs)
        self.game_tab = ttk.Frame(tabs)
        self.edit_game_tab = ttk.Frame(tabs)
        self.dashboard_tab = ttk.Frame(tabs)
        self.mail_tab = ttk.Frame(tabs)

        tabs.add(self.roster_tab, text="Roster")
        tabs.add(self.game_tab, text="New Game")
        tabs.add(self.edit_game_tab, text="Edit Game")
        tabs.add(self.dashboard_tab, text="Dashboard")
        tabs.add(self.mail_tab, text="Mailing")

        self._build_roster_tab()
        self._build_game_tab()
        self._build_edit_game_tab()
        self._build_dashboard_tab()
        self._build_mail_tab()

    # ===================== ROSTER TAB =====================
    def _build_roster_tab(self) -> None:
        form = ttk.LabelFrame(self.roster_tab, text="Add Player")
        form.pack(fill=tk.X, padx=12, pady=12)

        ttk.Label(form, text="Name").grid(row=0, column=0, padx=8, pady=8, sticky=tk.W)
        self.player_name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.player_name_var, width=25).grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(form, text="Role").grid(row=0, column=2, padx=8, pady=8, sticky=tk.W)
        self.player_role_var = tk.StringVar(value="skater")
        ttk.Combobox(form, textvariable=self.player_role_var, values=["skater", "goalie"], width=12, state="readonly").grid(
            row=0, column=3, padx=8, pady=8,
        )

        ttk.Label(form, text="Number").grid(row=0, column=4, padx=8, pady=8, sticky=tk.W)
        self.player_number_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.player_number_var, width=6).grid(row=0, column=5, padx=8, pady=8)

        ttk.Button(form, text="Add Player", command=self.add_player).grid(row=0, column=6, padx=8, pady=8)

        # Edit player section
        edit_frame = ttk.LabelFrame(self.roster_tab, text="Edit Selected Player")
        edit_frame.pack(fill=tk.X, padx=12, pady=8)

        ttk.Label(edit_frame, text="Name").grid(row=0, column=0, padx=8, pady=8, sticky=tk.W)
        self.edit_player_name_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.edit_player_name_var, width=25).grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(edit_frame, text="Role").grid(row=0, column=2, padx=8, pady=8, sticky=tk.W)
        self.edit_player_role_var = tk.StringVar(value="skater")
        ttk.Combobox(edit_frame, textvariable=self.edit_player_role_var, values=["skater", "goalie"], width=12, state="readonly").grid(
            row=0, column=3, padx=8, pady=8,
        )

        ttk.Label(edit_frame, text="Number").grid(row=0, column=4, padx=8, pady=8, sticky=tk.W)
        self.edit_player_number_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.edit_player_number_var, width=6).grid(row=0, column=5, padx=8, pady=8)

        ttk.Button(edit_frame, text="Save Changes", command=self.save_player_edit).grid(row=0, column=6, padx=8, pady=8)

        list_frame = ttk.LabelFrame(self.roster_tab, text="Active Players")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        columns = ("id", "name", "role", "number")
        self.players_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=14)
        self.players_tree.heading("id", text="ID")
        self.players_tree.heading("name", text="Name")
        self.players_tree.heading("role", text="Role")
        self.players_tree.heading("number", text="#")
        self.players_tree.column("id", width=50)
        self.players_tree.column("name", width=200)
        self.players_tree.column("role", width=100)
        self.players_tree.column("number", width=60)
        self.players_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.players_tree.bind("<<TreeviewSelect>>", self.on_player_select)

        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_player).pack(side=tk.RIGHT, padx=4)

    def on_player_select(self, event: Any) -> None:
        selection = self.players_tree.selection()
        if selection:
            item = self.players_tree.item(selection[0])
            values = item["values"]
            self.edit_player_name_var.set(str(values[1]))
            self.edit_player_role_var.set(str(values[2]))
            self.edit_player_number_var.set(str(values[3]) if values[3] else "")

    def save_player_edit(self) -> None:
        selection = self.players_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a player to edit.")
            return
        item = self.players_tree.item(selection[0])
        player_id = int(item["values"][0])
        try:
            number_str = self.edit_player_number_var.get().strip()
            number = int(number_str) if number_str else None
            self.service.update_player(
                player_id,
                self.edit_player_name_var.get(),
                self.edit_player_role_var.get(),
                number,
            )
            self.refresh_players()
            messagebox.showinfo("Success", "Player updated successfully.")
        except Exception as exc:
            messagebox.showerror("Update failed", str(exc))

    # ===================== GAME ENTRY TAB =====================
    def _build_game_tab(self) -> None:
        game_meta = ttk.LabelFrame(self.game_tab, text="Game Information")
        game_meta.pack(fill=tk.X, padx=12, pady=12)

        self.season_var = tk.StringVar(value=f"{dt.date.today().year}-{dt.date.today().year + 1}")
        self.season_type_var = tk.StringVar(value="regular")
        self.date_var = tk.StringVar(value=dt.date.today().isoformat())
        self.opponent_var = tk.StringVar()
        self.result_var = tk.StringVar(value="win")
        self.notes_var = tk.StringVar()

        ttk.Label(game_meta, text="Season").grid(row=0, column=0, padx=8, pady=6, sticky=tk.W)
        ttk.Entry(game_meta, textvariable=self.season_var, width=16).grid(row=0, column=1, padx=8, pady=6)
        ttk.Label(game_meta, text="Type").grid(row=0, column=2, padx=8, pady=6, sticky=tk.W)
        ttk.Combobox(game_meta, textvariable=self.season_type_var, values=["regular", "playoff"], state="readonly", width=10).grid(
            row=0, column=3, padx=8, pady=6,
        )
        ttk.Label(game_meta, text="Date (YYYY-MM-DD)").grid(row=0, column=4, padx=8, pady=6, sticky=tk.W)
        ttk.Entry(game_meta, textvariable=self.date_var, width=14).grid(row=0, column=5, padx=8, pady=6)

        ttk.Label(game_meta, text="Opponent").grid(row=1, column=0, padx=8, pady=6, sticky=tk.W)
        ttk.Entry(game_meta, textvariable=self.opponent_var, width=20).grid(row=1, column=1, padx=8, pady=6)
        ttk.Label(game_meta, text="Result").grid(row=1, column=2, padx=8, pady=6, sticky=tk.W)
        ttk.Combobox(game_meta, textvariable=self.result_var, values=["win", "loss"], state="readonly", width=10).grid(
            row=1, column=3, padx=8, pady=6,
        )
        ttk.Label(game_meta, text="Notes").grid(row=1, column=4, padx=8, pady=6, sticky=tk.W)
        ttk.Entry(game_meta, textvariable=self.notes_var, width=30).grid(row=1, column=5, padx=8, pady=6, sticky=tk.W)

        lines = ttk.Frame(self.game_tab)
        lines.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Skater entry
        skater_box = ttk.LabelFrame(lines, text="Add Skater Stats")
        skater_box.pack(fill=tk.X, pady=6)
        self.skater_player_var = tk.StringVar()
        self.s_goals = tk.StringVar(value="0")
        self.s_assists = tk.StringVar(value="0")
        self.s_pim = tk.StringVar(value="0")
        self.s_shg = tk.StringVar(value="0")
        self.s_ppg = tk.StringVar(value="0")

        self.skater_player_combo = ttk.Combobox(skater_box, textvariable=self.skater_player_var, state="readonly", width=22)
        self.skater_player_combo.grid(row=0, column=0, padx=6, pady=6)
        ttk.Entry(skater_box, textvariable=self.s_goals, width=6).grid(row=0, column=1, padx=4)
        ttk.Entry(skater_box, textvariable=self.s_assists, width=6).grid(row=0, column=2, padx=4)
        ttk.Entry(skater_box, textvariable=self.s_pim, width=6).grid(row=0, column=3, padx=4)
        ttk.Entry(skater_box, textvariable=self.s_shg, width=6).grid(row=0, column=4, padx=4)
        ttk.Entry(skater_box, textvariable=self.s_ppg, width=6).grid(row=0, column=5, padx=4)
        ttk.Button(skater_box, text="Add", command=self.add_skater_line).grid(row=0, column=6, padx=6)

        ttk.Label(skater_box, text="Player").grid(row=1, column=0, sticky=tk.W, padx=6)
        ttk.Label(skater_box, text="G").grid(row=1, column=1)
        ttk.Label(skater_box, text="A").grid(row=1, column=2)
        ttk.Label(skater_box, text="PIM").grid(row=1, column=3)
        ttk.Label(skater_box, text="SHG").grid(row=1, column=4)
        ttk.Label(skater_box, text="PPG").grid(row=1, column=5)

        # Goalie entry - shots is calculated
        goalie_box = ttk.LabelFrame(lines, text="Add Goalie Stats")
        goalie_box.pack(fill=tk.X, pady=6)

        self.goalie_player_var = tk.StringVar()
        self.g_saves = tk.StringVar(value="0")
        self.g_ga = tk.StringVar(value="0")
        self.g_shots_display = tk.StringVar(value="0")

        self.goalie_player_combo = ttk.Combobox(goalie_box, textvariable=self.goalie_player_var, state="readonly", width=22)
        self.goalie_player_combo.grid(row=0, column=0, padx=6, pady=6)
        
        saves_entry = ttk.Entry(goalie_box, textvariable=self.g_saves, width=8)
        saves_entry.grid(row=0, column=1, padx=4)
        saves_entry.bind("<KeyRelease>", self._update_shots_display)
        
        ga_entry = ttk.Entry(goalie_box, textvariable=self.g_ga, width=8)
        ga_entry.grid(row=0, column=2, padx=4)
        ga_entry.bind("<KeyRelease>", self._update_shots_display)
        
        # Shots is read-only, calculated field
        shots_entry = ttk.Entry(goalie_box, textvariable=self.g_shots_display, width=8, state="readonly")
        shots_entry.grid(row=0, column=3, padx=4)
        
        ttk.Button(goalie_box, text="Add", command=self.add_goalie_line).grid(row=0, column=4, padx=6)

        ttk.Label(goalie_box, text="Player").grid(row=1, column=0, sticky=tk.W, padx=6)
        ttk.Label(goalie_box, text="Saves").grid(row=1, column=1)
        ttk.Label(goalie_box, text="GA").grid(row=1, column=2)
        ttk.Label(goalie_box, text="Shots (auto)").grid(row=1, column=3)

        pending_box = ttk.LabelFrame(lines, text="Stats to be Saved")
        pending_box.pack(fill=tk.BOTH, expand=True, pady=6)
        self.pending_lines_list = tk.Listbox(pending_box, height=8)
        self.pending_lines_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        action_row = ttk.Frame(lines)
        action_row.pack(fill=tk.X, pady=4)
        ttk.Button(action_row, text="Save Game", command=self.save_game).pack(side=tk.RIGHT, padx=6)
        ttk.Button(action_row, text="Clear All", command=self.clear_pending).pack(side=tk.RIGHT, padx=6)

    def _update_shots_display(self, event: Any = None) -> None:
        try:
            saves = int(self.g_saves.get() or 0)
            ga = int(self.g_ga.get() or 0)
            self.g_shots_display.set(str(saves + ga))
        except ValueError:
            self.g_shots_display.set("?")

    # ===================== EDIT GAME TAB =====================
    def _build_edit_game_tab(self) -> None:
        # Season/game selection
        select_frame = ttk.LabelFrame(self.edit_game_tab, text="Select Game to Edit")
        select_frame.pack(fill=tk.X, padx=12, pady=12)

        ttk.Label(select_frame, text="Season").grid(row=0, column=0, padx=8, pady=8)
        self.edit_season_var = tk.StringVar(value=f"{dt.date.today().year}-{dt.date.today().year + 1}")
        ttk.Entry(select_frame, textvariable=self.edit_season_var, width=16).grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(select_frame, text="Type").grid(row=0, column=2, padx=8, pady=8)
        self.edit_season_type_var = tk.StringVar(value="regular")
        ttk.Combobox(select_frame, textvariable=self.edit_season_type_var, values=["regular", "playoff", ""], state="readonly", width=10).grid(
            row=0, column=3, padx=8, pady=8,
        )

        ttk.Button(select_frame, text="Load Games", command=self.load_games_for_edit).grid(row=0, column=4, padx=8, pady=8)

        # Games list
        games_frame = ttk.LabelFrame(self.edit_game_tab, text="Games")
        games_frame.pack(fill=tk.X, padx=12, pady=8)

        columns = ("id", "date", "opponent", "type", "result")
        self.games_tree = ttk.Treeview(games_frame, columns=columns, show="headings", height=6)
        self.games_tree.heading("id", text="ID")
        self.games_tree.heading("date", text="Date")
        self.games_tree.heading("opponent", text="Opponent")
        self.games_tree.heading("type", text="Type")
        self.games_tree.heading("result", text="Result")
        self.games_tree.column("id", width=50)
        self.games_tree.column("date", width=100)
        self.games_tree.column("opponent", width=150)
        self.games_tree.column("type", width=80)
        self.games_tree.column("result", width=60)
        self.games_tree.pack(fill=tk.X, padx=8, pady=8)

        ttk.Button(games_frame, text="Load Selected Game", command=self.load_game_for_edit).pack(pady=8)

        # Edit form
        edit_form = ttk.LabelFrame(self.edit_game_tab, text="Edit Game Stats")
        edit_form.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        meta_row = ttk.Frame(edit_form)
        meta_row.pack(fill=tk.X, padx=8, pady=8)

        self.edit_game_info_var = tk.StringVar(value="No game loaded")
        ttk.Label(meta_row, textvariable=self.edit_game_info_var, font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)

        ttk.Label(meta_row, text="Result:").pack(side=tk.LEFT, padx=(20, 4))
        self.edit_result_var = tk.StringVar(value="win")
        ttk.Combobox(meta_row, textvariable=self.edit_result_var, values=["win", "loss"], state="readonly", width=8).pack(side=tk.LEFT)

        ttk.Label(meta_row, text="Notes:").pack(side=tk.LEFT, padx=(20, 4))
        self.edit_notes_var = tk.StringVar()
        ttk.Entry(meta_row, textvariable=self.edit_notes_var, width=30).pack(side=tk.LEFT)

        # Pending edits
        self.edit_pending_skaters: list[SkaterGameStatInput] = []
        self.edit_pending_goalies: list[GoalieGameStatInput] = []

        stats_frame = ttk.Frame(edit_form)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Skater add row
        skater_row = ttk.Frame(stats_frame)
        skater_row.pack(fill=tk.X, pady=4)

        ttk.Label(skater_row, text="Skater:").pack(side=tk.LEFT, padx=4)
        self.edit_skater_player_var = tk.StringVar()
        self.edit_skater_player_combo = ttk.Combobox(skater_row, textvariable=self.edit_skater_player_var, state="readonly", width=20)
        self.edit_skater_player_combo.pack(side=tk.LEFT, padx=4)

        self.edit_s_goals = tk.StringVar(value="0")
        self.edit_s_assists = tk.StringVar(value="0")
        self.edit_s_pim = tk.StringVar(value="0")
        self.edit_s_shg = tk.StringVar(value="0")
        self.edit_s_ppg = tk.StringVar(value="0")

        for lbl, var in [("G", self.edit_s_goals), ("A", self.edit_s_assists), ("PIM", self.edit_s_pim), ("SHG", self.edit_s_shg), ("PPG", self.edit_s_ppg)]:
            ttk.Label(skater_row, text=lbl).pack(side=tk.LEFT, padx=2)
            ttk.Entry(skater_row, textvariable=var, width=4).pack(side=tk.LEFT, padx=2)

        ttk.Button(skater_row, text="Add", command=self.add_edit_skater_line).pack(side=tk.LEFT, padx=8)

        # Goalie add row
        goalie_row = ttk.Frame(stats_frame)
        goalie_row.pack(fill=tk.X, pady=4)

        ttk.Label(goalie_row, text="Goalie:").pack(side=tk.LEFT, padx=4)
        self.edit_goalie_player_var = tk.StringVar()
        self.edit_goalie_player_combo = ttk.Combobox(goalie_row, textvariable=self.edit_goalie_player_var, state="readonly", width=20)
        self.edit_goalie_player_combo.pack(side=tk.LEFT, padx=4)

        self.edit_g_saves = tk.StringVar(value="0")
        self.edit_g_ga = tk.StringVar(value="0")
        self.edit_g_shots_display = tk.StringVar(value="0")

        ttk.Label(goalie_row, text="Saves").pack(side=tk.LEFT, padx=2)
        edit_saves = ttk.Entry(goalie_row, textvariable=self.edit_g_saves, width=6)
        edit_saves.pack(side=tk.LEFT, padx=2)
        edit_saves.bind("<KeyRelease>", self._update_edit_shots_display)

        ttk.Label(goalie_row, text="GA").pack(side=tk.LEFT, padx=2)
        edit_ga = ttk.Entry(goalie_row, textvariable=self.edit_g_ga, width=6)
        edit_ga.pack(side=tk.LEFT, padx=2)
        edit_ga.bind("<KeyRelease>", self._update_edit_shots_display)

        ttk.Label(goalie_row, text="Shots").pack(side=tk.LEFT, padx=2)
        ttk.Entry(goalie_row, textvariable=self.edit_g_shots_display, width=6, state="readonly").pack(side=tk.LEFT, padx=2)

        ttk.Button(goalie_row, text="Add", command=self.add_edit_goalie_line).pack(side=tk.LEFT, padx=8)

        # Pending stats list
        self.edit_pending_list = tk.Listbox(stats_frame, height=6)
        self.edit_pending_list.pack(fill=tk.BOTH, expand=True, pady=8)

        # Action buttons
        btn_row = ttk.Frame(edit_form)
        btn_row.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(btn_row, text="Save Changes", command=self.save_game_edit).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_row, text="Clear Stats", command=self.clear_edit_pending).pack(side=tk.RIGHT, padx=4)

    def _update_edit_shots_display(self, event: Any = None) -> None:
        try:
            saves = int(self.edit_g_saves.get() or 0)
            ga = int(self.edit_g_ga.get() or 0)
            self.edit_g_shots_display.set(str(saves + ga))
        except ValueError:
            self.edit_g_shots_display.set("?")

    def load_games_for_edit(self) -> None:
        season = self.edit_season_var.get().strip()
        season_type = self.edit_season_type_var.get() or None
        try:
            games = self.service.list_games(season, season_type)
            for item in self.games_tree.get_children():
                self.games_tree.delete(item)
            for game in games:
                self.games_tree.insert("", "end", values=(
                    game["id"], game["date"], game["opponent"], game["season_type"], game["result"]
                ))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def load_game_for_edit(self) -> None:
        selection = self.games_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a game to edit.")
            return
        item = self.games_tree.item(selection[0])
        game_id = int(item["values"][0])
        try:
            game = self.service.get_game_stats(game_id)
            if not game:
                messagebox.showerror("Error", "Game not found.")
                return

            self.editing_game_id = game_id
            self.edit_game_info_var.set(f"Editing: {game['date']} vs {game['opponent']} ({game['season_type']})")
            self.edit_result_var.set(game["result"])
            self.edit_notes_var.set(game["notes"])

            # Load existing stats
            self.edit_pending_skaters.clear()
            self.edit_pending_goalies.clear()
            self.edit_pending_list.delete(0, tk.END)

            for s in game["skaters"]:
                stat = SkaterGameStatInput(
                    player_id=s["player_id"],
                    goals=s["goals"],
                    assists=s["assists"],
                    pim=s["pim"],
                    shg=s["shg"],
                    ppg=s["ppg"],
                )
                self.edit_pending_skaters.append(stat)
                self.edit_pending_list.insert(
                    tk.END,
                    f"SKATER {s['player_name']}: G={s['goals']} A={s['assists']} PIM={s['pim']} SHG={s['shg']} PPG={s['ppg']}",
                )

            for g in game["goalies"]:
                stat = GoalieGameStatInput(
                    player_id=g["player_id"],
                    saves=g["saves"],
                    goals_against=g["goals_against"],
                    shots_received=g["shots_received"],
                )
                self.edit_pending_goalies.append(stat)
                shots = g["saves"] + g["goals_against"]
                self.edit_pending_list.insert(
                    tk.END,
                    f"GOALIE {g['player_name']}: Saves={g['saves']} GA={g['goals_against']} Shots={shots}",
                )

        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def add_edit_skater_line(self) -> None:
        try:
            player_label = self.edit_skater_player_var.get()
            player_id = self.player_lookup.get(player_label)
            if player_id is None:
                messagebox.showwarning("No Player", "Please select a player.")
                return
            stat = SkaterGameStatInput(
                player_id=player_id,
                goals=int(self.edit_s_goals.get()),
                assists=int(self.edit_s_assists.get()),
                pim=int(self.edit_s_pim.get()),
                shg=int(self.edit_s_shg.get()),
                ppg=int(self.edit_s_ppg.get()),
            )
            self.edit_pending_skaters.append(stat)
            self.edit_pending_list.insert(
                tk.END,
                f"SKATER {player_label}: G={stat.goals} A={stat.assists} PIM={stat.pim} SHG={stat.shg} PPG={stat.ppg}",
            )
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def add_edit_goalie_line(self) -> None:
        try:
            player_label = self.edit_goalie_player_var.get()
            player_id = self.player_lookup.get(player_label)
            if player_id is None:
                messagebox.showwarning("No Player", "Please select a player.")
                return
            saves = int(self.edit_g_saves.get())
            ga = int(self.edit_g_ga.get())
            stat = GoalieGameStatInput(
                player_id=player_id,
                saves=saves,
                goals_against=ga,
                shots_received=saves + ga,
            )
            self.edit_pending_goalies.append(stat)
            self.edit_pending_list.insert(
                tk.END,
                f"GOALIE {player_label}: Saves={saves} GA={ga} Shots={saves + ga}",
            )
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def clear_edit_pending(self) -> None:
        self.edit_pending_skaters.clear()
        self.edit_pending_goalies.clear()
        self.edit_pending_list.delete(0, tk.END)

    def save_game_edit(self) -> None:
        if self.editing_game_id is None:
            messagebox.showwarning("No Game", "Please load a game to edit first.")
            return
        try:
            self.service.update_game_stats(
                game_id=self.editing_game_id,
                result=self.edit_result_var.get(),
                notes=self.edit_notes_var.get(),
                skater_stats=self.edit_pending_skaters,
                goalie_stats=self.edit_pending_goalies,
            )
            messagebox.showinfo("Success", "Game stats updated successfully.")
            self.refresh_dashboard()
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))

    # ===================== DASHBOARD TAB =====================
    def _build_dashboard_tab(self) -> None:
        controls = ttk.Frame(self.dashboard_tab)
        controls.pack(fill=tk.X, padx=12, pady=12)

        self.dashboard_season_var = tk.StringVar(value=f"{dt.date.today().year}-{dt.date.today().year + 1}")
        self.dashboard_type_var = tk.StringVar(value="")

        ttk.Label(controls, text="Season").pack(side=tk.LEFT, padx=6)
        ttk.Entry(controls, textvariable=self.dashboard_season_var, width=16).pack(side=tk.LEFT, padx=6)
        ttk.Label(controls, text="Type").pack(side=tk.LEFT, padx=6)
        ttk.Combobox(controls, textvariable=self.dashboard_type_var, values=["", "regular", "playoff"], state="readonly", width=10).pack(side=tk.LEFT, padx=6)
        ttk.Button(controls, text="Refresh", command=self.refresh_dashboard).pack(side=tk.LEFT, padx=6)

        # Dashboard is READ-ONLY
        self.dashboard_text = tk.Text(self.dashboard_tab, height=28, state=tk.DISABLED)
        self.dashboard_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

    # ===================== MAIL TAB =====================
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
        ttk.Button(list_box, text="Remove Selected", command=self.remove_recipient).pack(anchor=tk.E, padx=8, pady=8)

        send_box = ttk.LabelFrame(self.mail_tab, text="Send Stats Manually")
        send_box.pack(fill=tk.X, padx=12, pady=12)
        self.send_season_var = tk.StringVar(value=f"{dt.date.today().year}-{dt.date.today().year + 1}")
        self.send_type_var = tk.StringVar(value="")
        ttk.Label(send_box, text="Season").grid(row=0, column=0, padx=8, pady=8)
        ttk.Entry(send_box, textvariable=self.send_season_var, width=16).grid(row=0, column=1, padx=8, pady=8)
        ttk.Label(send_box, text="Type").grid(row=0, column=2, padx=8, pady=8)
        ttk.Combobox(send_box, textvariable=self.send_type_var, values=["", "regular", "playoff"], state="readonly", width=10).grid(row=0, column=3, padx=8, pady=8)
        ttk.Button(send_box, text="Send", command=self.send_summary).grid(row=0, column=4, padx=8, pady=8)

    # ===================== ACTIONS =====================
    def refresh_players(self) -> None:
        players = self.service.list_active_players()
        
        # Clear tree
        for item in self.players_tree.get_children():
            self.players_tree.delete(item)

        display_values: list[str] = []
        self.player_lookup: dict[str, int] = {}
        for player in players:
            number_str = str(player.number) if player.number else ""
            self.players_tree.insert("", "end", values=(player.id, player.name, player.role, number_str))
            label = f"#{player.number} {player.name}" if player.number else player.name
            display_values.append(label)
            self.player_lookup[label] = player.id

        # Update all player combos
        self.skater_player_combo["values"] = display_values
        self.goalie_player_combo["values"] = display_values
        self.edit_skater_player_combo["values"] = display_values
        self.edit_goalie_player_combo["values"] = display_values

        if display_values:
            self.skater_player_var.set(display_values[0])
            self.goalie_player_var.set(display_values[0])
            self.edit_skater_player_var.set(display_values[0])
            self.edit_goalie_player_var.set(display_values[0])

    def add_player(self) -> None:
        try:
            number_str = self.player_number_var.get().strip()
            number = int(number_str) if number_str else None
            self.service.add_player(self.player_name_var.get(), self.player_role_var.get(), number)
            self.player_name_var.set("")
            self.player_number_var.set("")
            self.refresh_players()
        except Exception as exc:
            messagebox.showerror("Add player failed", str(exc))

    def remove_player(self) -> None:
        selection = self.players_tree.selection()
        if not selection:
            return
        item = self.players_tree.item(selection[0])
        player_id = int(item["values"][0])
        self.service.remove_player(player_id)
        self.refresh_players()

    def add_skater_line(self) -> None:
        try:
            player_label = self.skater_player_var.get()
            player_id = self.player_lookup.get(player_label)
            if player_id is None:
                messagebox.showwarning("No Player", "Please select a player.")
                return
            stat = SkaterGameStatInput(
                player_id=player_id,
                goals=int(self.s_goals.get()),
                assists=int(self.s_assists.get()),
                pim=int(self.s_pim.get()),
                shg=int(self.s_shg.get()),
                ppg=int(self.s_ppg.get()),
            )
            self.pending_skaters.append(stat)
            self.pending_lines_list.insert(
                tk.END,
                f"SKATER {player_label}: G={stat.goals} A={stat.assists} PIM={stat.pim} SHG={stat.shg} PPG={stat.ppg}",
            )
        except Exception as exc:
            messagebox.showerror("Invalid skater line", str(exc))

    def add_goalie_line(self) -> None:
        try:
            player_label = self.goalie_player_var.get()
            player_id = self.player_lookup.get(player_label)
            if player_id is None:
                messagebox.showwarning("No Player", "Please select a player.")
                return
            saves = int(self.g_saves.get())
            ga = int(self.g_ga.get())
            stat = GoalieGameStatInput(
                player_id=player_id,
                saves=saves,
                goals_against=ga,
                shots_received=saves + ga,
            )
            self.pending_goalies.append(stat)
            self.pending_lines_list.insert(
                tk.END,
                f"GOALIE {player_label}: Saves={saves} GA={ga} Shots={saves + ga}",
            )
        except Exception as exc:
            messagebox.showerror("Invalid goalie line", str(exc))

    def clear_pending(self) -> None:
        self.pending_skaters.clear()
        self.pending_goalies.clear()
        self.pending_lines_list.delete(0, tk.END)

    def save_game(self) -> None:
        try:
            self.service.record_game_stats(
                season_label=self.season_var.get(),
                season_type=self.season_type_var.get(),
                game_date=self.date_var.get(),
                opponent=self.opponent_var.get(),
                result=self.result_var.get(),
                notes=self.notes_var.get(),
                skater_stats=self.pending_skaters,
                goalie_stats=self.pending_goalies,
                auto_send_email=True,
            )
            self.clear_pending()
            self.refresh_dashboard()
            messagebox.showinfo("Success", "Game saved! Email notification sent (if recipients configured).")
        except Exception as exc:
            messagebox.showerror("Save game failed", str(exc))

    def refresh_dashboard(self) -> None:
        try:
            season_type = self.dashboard_type_var.get() or None
            summary = self.service.get_season_stats(self.dashboard_season_var.get(), season_type)
            
            # Enable to update, then disable again (read-only)
            self.dashboard_text.config(state=tk.NORMAL)
            self.dashboard_text.delete("1.0", tk.END)
            
            type_str = f" ({summary['season_type']})" if summary.get('season_type') and summary['season_type'] != 'all' else ""
            self.dashboard_text.insert(
                tk.END,
                f"Season: {summary['season']}{type_str}\n"
                f"Team Record: {summary['team']['wins']}W - {summary['team']['losses']}L\n\n"
                "═══════════════════════════════════════\n"
                "SKATERS\n"
                "═══════════════════════════════════════\n",
            )
            if not summary["skaters"]:
                self.dashboard_text.insert(tk.END, "  No skater stats recorded.\n")
            for row in summary["skaters"]:
                self.dashboard_text.insert(
                    tk.END,
                    f"  {row['player_name']:<20} G={row['goals']:>3}  A={row['assists']:>3}  PIM={row['pim']:>3}  SHG={row['shg']:>2}  PPG={row['ppg']:>2}\n",
                )

            self.dashboard_text.insert(
                tk.END,
                "\n═══════════════════════════════════════\n"
                "GOALIES\n"
                "═══════════════════════════════════════\n",
            )
            if not summary["goalies"]:
                self.dashboard_text.insert(tk.END, "  No goalie stats recorded.\n")
            for row in summary["goalies"]:
                sv = row["sv_pct"]
                sv_display = "NaN" if math.isnan(sv) else f"{sv:.3f}"
                shots = row["shots_received"]
                self.dashboard_text.insert(
                    tk.END,
                    f"  {row['player_name']:<20} Saves={row['saves']:>3}  GA={row['goals_against']:>3}  Shots={shots:>3}  Wins={row['wins']:>2}  SV%={sv_display}\n",
                )
            
            self.dashboard_text.config(state=tk.DISABLED)
        except Exception as exc:
            messagebox.showerror("Dashboard error", str(exc))

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
        except Exception as exc:
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
            season_type = self.send_type_var.get() or None
            success, detail = self.service.send_season_stats_email(self.send_season_var.get(), season_type)
            if success:
                messagebox.showinfo("Email", detail)
            else:
                messagebox.showerror("Email", detail)
        except Exception as exc:
            messagebox.showerror("Email error", str(exc))
