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
        self.title("Liam Hockey PoC")
        self.geometry("1024x700")

        self.pending_skaters: list[SkaterGameStatInput] = []
        self.pending_goalies: list[GoalieGameStatInput] = []

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

    def _build_roster_tab(self) -> None:
        form = ttk.LabelFrame(self.roster_tab, text="Add Player")
        form.pack(fill=tk.X, padx=12, pady=12)

        ttk.Label(form, text="Name").grid(row=0, column=0, padx=8, pady=8, sticky=tk.W)
        self.player_name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.player_name_var, width=30).grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(form, text="Role").grid(row=0, column=2, padx=8, pady=8, sticky=tk.W)
        self.player_role_var = tk.StringVar(value="skater")
        ttk.Combobox(form, textvariable=self.player_role_var, values=["skater", "goalkeeper"], width=14, state="readonly").grid(
            row=0,
            column=3,
            padx=8,
            pady=8,
        )

        ttk.Button(form, text="Add", command=self.add_player).grid(row=0, column=4, padx=8, pady=8)

        list_frame = ttk.LabelFrame(self.roster_tab, text="Active Players")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        self.players_list = tk.Listbox(list_frame, height=18)
        self.players_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        ttk.Button(list_frame, text="Remove Selected", command=self.remove_player).pack(padx=8, pady=8, anchor=tk.E)

    def _build_game_tab(self) -> None:
        game_meta = ttk.LabelFrame(self.game_tab, text="Game")
        game_meta.pack(fill=tk.X, padx=12, pady=12)

        self.season_var = tk.StringVar(value=f"{dt.date.today().year}-{dt.date.today().year + 1}")
        self.date_var = tk.StringVar(value=dt.date.today().isoformat())
        self.opponent_var = tk.StringVar()
        self.result_var = tk.StringVar(value="win")
        self.notes_var = tk.StringVar()

        ttk.Label(game_meta, text="Season").grid(row=0, column=0, padx=8, pady=6, sticky=tk.W)
        ttk.Entry(game_meta, textvariable=self.season_var, width=16).grid(row=0, column=1, padx=8, pady=6)
        ttk.Label(game_meta, text="Date (YYYY-MM-DD)").grid(row=0, column=2, padx=8, pady=6, sticky=tk.W)
        ttk.Entry(game_meta, textvariable=self.date_var, width=14).grid(row=0, column=3, padx=8, pady=6)
        ttk.Label(game_meta, text="Opponent").grid(row=1, column=0, padx=8, pady=6, sticky=tk.W)
        ttk.Entry(game_meta, textvariable=self.opponent_var, width=20).grid(row=1, column=1, padx=8, pady=6)
        ttk.Label(game_meta, text="Result").grid(row=1, column=2, padx=8, pady=6, sticky=tk.W)
        ttk.Combobox(game_meta, textvariable=self.result_var, values=["win", "loss"], state="readonly", width=12).grid(
            row=1,
            column=3,
            padx=8,
            pady=6,
        )
        ttk.Label(game_meta, text="Notes").grid(row=2, column=0, padx=8, pady=6, sticky=tk.W)
        ttk.Entry(game_meta, textvariable=self.notes_var, width=60).grid(row=2, column=1, columnspan=3, padx=8, pady=6, sticky=tk.W)

        lines = ttk.Frame(self.game_tab)
        lines.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        skater_box = ttk.LabelFrame(lines, text="Add Skater Line")
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
        ttk.Button(skater_box, text="Add Skater Stat", command=self.add_skater_line).grid(row=0, column=6, padx=6)

        ttk.Label(skater_box, text="Player").grid(row=1, column=0, sticky=tk.W, padx=6)
        ttk.Label(skater_box, text="G").grid(row=1, column=1)
        ttk.Label(skater_box, text="A").grid(row=1, column=2)
        ttk.Label(skater_box, text="PIM").grid(row=1, column=3)
        ttk.Label(skater_box, text="SHG").grid(row=1, column=4)
        ttk.Label(skater_box, text="PPG").grid(row=1, column=5)

        goalie_box = ttk.LabelFrame(lines, text="Add Goalkeeper Line")
        goalie_box.pack(fill=tk.X, pady=6)

        self.goalie_player_var = tk.StringVar()
        self.g_saves = tk.StringVar(value="0")
        self.g_ga = tk.StringVar(value="0")
        self.g_shots = tk.StringVar(value="0")

        self.goalie_player_combo = ttk.Combobox(goalie_box, textvariable=self.goalie_player_var, state="readonly", width=22)
        self.goalie_player_combo.grid(row=0, column=0, padx=6, pady=6)
        ttk.Entry(goalie_box, textvariable=self.g_saves, width=8).grid(row=0, column=1, padx=4)
        ttk.Entry(goalie_box, textvariable=self.g_ga, width=8).grid(row=0, column=2, padx=4)
        ttk.Entry(goalie_box, textvariable=self.g_shots, width=8).grid(row=0, column=3, padx=4)
        ttk.Button(goalie_box, text="Add Goalie Stat", command=self.add_goalie_line).grid(row=0, column=4, padx=6)

        ttk.Label(goalie_box, text="Player").grid(row=1, column=0, sticky=tk.W, padx=6)
        ttk.Label(goalie_box, text="Saves").grid(row=1, column=1)
        ttk.Label(goalie_box, text="GA").grid(row=1, column=2)
        ttk.Label(goalie_box, text="Shots").grid(row=1, column=3)

        pending_box = ttk.LabelFrame(lines, text="Pending Stat Lines")
        pending_box.pack(fill=tk.BOTH, expand=True, pady=6)
        self.pending_lines_list = tk.Listbox(pending_box, height=10)
        self.pending_lines_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        action_row = ttk.Frame(lines)
        action_row.pack(fill=tk.X, pady=4)
        ttk.Button(action_row, text="Save Game", command=self.save_game).pack(side=tk.RIGHT, padx=6)
        ttk.Button(action_row, text="Clear Pending", command=self.clear_pending).pack(side=tk.RIGHT, padx=6)

    def _build_dashboard_tab(self) -> None:
        controls = ttk.Frame(self.dashboard_tab)
        controls.pack(fill=tk.X, padx=12, pady=12)

        self.dashboard_season_var = tk.StringVar(value=f"{dt.date.today().year}-{dt.date.today().year + 1}")
        ttk.Label(controls, text="Season").pack(side=tk.LEFT, padx=6)
        ttk.Entry(controls, textvariable=self.dashboard_season_var, width=16).pack(side=tk.LEFT, padx=6)
        ttk.Button(controls, text="Refresh", command=self.refresh_dashboard).pack(side=tk.LEFT, padx=6)

        self.dashboard_text = tk.Text(self.dashboard_tab, height=28)
        self.dashboard_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

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

        send_box = ttk.LabelFrame(self.mail_tab, text="Send Stats")
        send_box.pack(fill=tk.X, padx=12, pady=12)
        self.send_season_var = tk.StringVar(value=f"{dt.date.today().year}-{dt.date.today().year + 1}")
        ttk.Label(send_box, text="Season").grid(row=0, column=0, padx=8, pady=8)
        ttk.Entry(send_box, textvariable=self.send_season_var, width=16).grid(row=0, column=1, padx=8, pady=8)
        ttk.Button(send_box, text="Send", command=self.send_summary).grid(row=0, column=2, padx=8, pady=8)

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
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Add player failed", str(exc))

    def remove_player(self) -> None:
        players_list_any: Any = self.players_list
        selection = tuple(players_list_any.curselection())
        if not selection:
            return
        selected = str(players_list_any.get(selection[0]))
        player_id = self.player_lookup[selected]
        self.service.remove_player(player_id)
        self.refresh_players()

    def add_skater_line(self) -> None:
        try:
            player_label = self.skater_player_var.get()
            player_id = self.player_lookup[player_label]
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
                f"SKATER p#{player_id} G={stat.goals} A={stat.assists} PIM={stat.pim} SHG={stat.shg} PPG={stat.ppg}",
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Invalid skater line", str(exc))

    def add_goalie_line(self) -> None:
        try:
            player_label = self.goalie_player_var.get()
            player_id = self.player_lookup[player_label]
            stat = GoalieGameStatInput(
                player_id=player_id,
                saves=int(self.g_saves.get()),
                goals_against=int(self.g_ga.get()),
                shots_received=int(self.g_shots.get()),
            )
            self.pending_goalies.append(stat)
            self.pending_lines_list.insert(
                tk.END,
                f"GOALIE p#{player_id} Saves={stat.saves} GA={stat.goals_against} Shots={stat.shots_received}",
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Invalid goalie line", str(exc))

    def clear_pending(self) -> None:
        self.pending_skaters.clear()
        self.pending_goalies.clear()
        self.pending_lines_list.delete(0, tk.END)

    def save_game(self) -> None:
        try:
            self.service.record_game_stats(
                season_label=self.season_var.get(),
                game_date=self.date_var.get(),
                opponent=self.opponent_var.get(),
                result=self.result_var.get(),
                notes=self.notes_var.get(),
                skater_stats=self.pending_skaters,
                goalie_stats=self.pending_goalies,
            )
            self.clear_pending()
            self.refresh_dashboard()
            messagebox.showinfo("Success", "Game saved")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Save game failed", str(exc))

    def refresh_dashboard(self) -> None:
        try:
            summary = self.service.get_season_stats(self.dashboard_season_var.get())
            self.dashboard_text.delete("1.0", tk.END)
            self.dashboard_text.insert(
                tk.END,
                f"Season: {summary['season']}\n"
                f"Team: {summary['team']['wins']}W-{summary['team']['losses']}L\n\n"
                "Skaters:\n",
            )
            for row in summary["skaters"]:
                self.dashboard_text.insert(
                    tk.END,
                    f"- {row['player_name']}: G={row['goals']} A={row['assists']} PIM={row['pim']} SHG={row['shg']} PPG={row['ppg']}\n",
                )

            self.dashboard_text.insert(tk.END, "\nGoalkeepers:\n")
            for row in summary["goalkeepers"]:
                sv = row["sv_pct"]
                sv_display = "NaN" if math.isnan(sv) else f"{sv:.3f}"
                self.dashboard_text.insert(
                    tk.END,
                    f"- {row['player_name']}: Saves={row['saves']} GA={row['goals_against']} Wins={row['wins']} SV%={sv_display}\n",
                )
        except Exception as exc:  # noqa: BLE001
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
