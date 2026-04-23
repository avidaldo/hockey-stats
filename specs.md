# Specifications

| Version | Date | Description |
|---------|------|-------------|
| v1 | 2025 (approx.) | Initial PoC specification |
| v2 | 2026-04-10 | Post-demo client requirements merged |
| v3 | 2026-04-23 | Post-v0.2-demo client requirements merged (current) |

> **Current version: v3**
>
> - Meeting notes that drove this update → [`notes-v3.md`](notes-v3.md)
> - Unresolved decisions → [`open_questions.md`](open_questions.md)
> - Object model (UML) → [`docs/class_diagram.md`](docs/class_diagram.md)
> - Architecture (layers, ports, decisions) → [`docs/architecture.md`](docs/architecture.md)
> - Iteration history → [`docs/iteration_log.md`](docs/iteration_log.md)

---

## 1) Product Overview
- Desktop application for managing and displaying cumulative hockey stats by season.
- Core follows Clean Architecture so the UI can be replaced (desktop now, potentially web/mobile later).
- Initial users are team staff/coaches managing one team.

---

## 2) Goals and Non-Goals

### Goals (MVP)
- Register and manage team roster (add/edit/remove players).
- Register and correct game-by-game stats from score sheet fields.
- Show cumulative season stats (skater, goalie, team) split by regular season and playoffs.
- Send updated stats summary to a team mailing list automatically on each game save.

### Non-Goals
- Full OCR pipeline for score sheet images (keep as extension point).
- Advanced analytics beyond requested metrics.
- Multi-team / multi-league support.
- Cloud deployment.

---

## 3) Actors
- **Team Manager**: enters data, manages roster, and initiates corrections.
- **Coach/Staff**: reviews stats dashboard/reports.
- **System**: calculates aggregates and sends email notifications.
- **External AI Agent** (future): extracts structured data from score sheet images.

> **Note (v3):** Multi-user support with distinct roles (e.g., Manager vs. Coach) is a confirmed requirement. Exact permissions per role are under discussion; see [`open_questions.md`](open_questions.md).

---

## 4) Functional Requirements

### FR-1 Team Configuration
- Add player with initial stats = 0.
- When adding a player, specify their **player type**: `permanent` or `substitute`.
  - **Permanent players** are regular roster members for a season. A default jersey number can be assigned to them per season (stored in the season roster). This number is pre-filled when entering game stats and can be overridden for a specific game.
  - **Substitute players** are occasional fill-ins. Their jersey number varies and is not stored in the roster; it can still be entered on a game-by-game basis.
- **Edit** an existing player's name, primary role, and player type (preserves all historical game stats).
- Remove player from active roster (mark inactive; historical stats are retained).
- Player has a **primary role**: `skater` or `goalie`.
- As an exception, a player may play a **different role in a specific game** (e.g., skater filling in as goalie). The game entry form defaults to the player's primary role; the user can override it per game.
- Aggregation is role-aware per game record; season totals keep skater and goalie metric families separated.
- Internal database IDs must **not** be displayed to users in any part of the UI.

### FR-2 Input Match/Score Sheet Data
- Data is entered via GUI form that maps to score sheet fields.
- Game input must capture:
    - Game metadata: date, opponent, **game type** (`regular` / `playoff`), result (win/loss), optional notes.
      - **Season is derived automatically from the date** and is never entered manually. See season derivation rule in §5.
    - Per skater: **optional jersey number** (pre-filled from season roster for permanent players), goals, assists, PIM, SHG, PPG.
    - Per goalie: **optional jersey number** (pre-filled from season roster for permanent players), saves, goals against. `ShotsReceived` is always computed as `Saves + GoalsAgainst` and displayed read-only — it is not a free-entry field.
- Date field uses a standard calendar/date-picker control and **defaults to today's date**.
- Date validation: only dates in September through April are valid (outside these months are rejected, as they fall outside the hockey season).
- Players are identified by their **unique ID** throughout the system. Duplicate name detection is not a substitute for ID-based lookup; the UI must select players unambiguously (e.g., by showing name alongside their player type or roster number, never relying on name uniqueness).
- Save operation validates required fields and rejects invalid values (negative stats, unknown player, out-of-season date).
- Duplicate game detection: same `season + date + opponent`. Error message clearly states the duplicate, which record already exists, and how to correct it.

### FR-3 Display Season Outputs
- Season stats dashboard is **read-only**. Corrections go through the dedicated correction flow.
- Stats are displayed in **two separate blocks**: regular season and playoffs.
- Per skater: **Jersey number**, Goals, Assists, PIM, SHG, PPG.
- Per goalie: **Jersey number**, Saves, Wins, Goals Against, SV%.
- Team stats: Wins, Losses.

### FR-4 Derived Metrics
- Goalie save percentage:
    - $SV\% = \frac{Saves}{ShotsReceived}$ where $ShotsReceived = Saves + GoalsAgainst$
- If `ShotsReceived = 0`, display `SV% = N/A`.

### FR-5 Send Stats by Email
- **Automatically** send season stats summary email when a game is saved or corrected.
- A secondary "Resend" button remains available on the mailing tab.
- Email includes regular-season and playoff stat blocks.
- Delivery result (success/failure) is logged.

### FR-6 Manage Mailing List
- Add email recipient.
- Remove recipient.
- List all recipients.
- Mailing list is independent from players.

### FR-7 Correct Game Stats
- **Correct Last Game** shortcut: loads the most recently saved game into an editable form.
- **Correct Any Game**: select a past game from a list (filterable by season) to load it for editing.
- On save, corrected stats replace the previous ones atomically (transactional delete + reinsert of stat lines; the game record itself is updated in place).
- **Date change during correction**: if the date is changed, the existing game record is updated to the new date and the season is re-derived accordingly. A date change that would move a game to a different season is rejected with a clear error message; the user must delete and re-enter such a game manually.
- Automatic email is triggered after a successful correction.

### FR-8 AI Ingestion Extension (Future)
- Provide interface/port to accept structured score-sheet payload from external AI.
- Core validation and persistence reused from the manual input flow.

### FR-9 Multi-user with Roles (planned)
- The application must support multiple named users.
- Users have distinct roles that control what they can do.
- Exact role definitions and permission matrix are captured in [`open_questions.md`](open_questions.md) and will be confirmed before implementation.

---

## 5) Business Rules
- Stats are cumulative from recorded games, not manually editable totals.
- Each game belongs to exactly one season and has one game type (`regular` or `playoff`).
- **Season derivation rule**: A game's season is determined solely by its date.
  - Dates in September–December of year Y → season label `Y-(Y+1)` (abbreviated, e.g., `2025-26`).
  - Dates in January–April of year Y → season label `(Y-1)-Y` (e.g., `2025-26`).
  - Dates in May–August are outside the hockey season and are rejected.
- Jersey number for **permanent players** is fixed per season and stored in `season_roster`; it is used as the default for game stat entry and may be overridden per game line.
- Jersey number for **substitute players** is not stored in the roster; it may be optionally recorded on a game stat line.
- A player's primary role is a profile attribute; a per-game role override is allowed.
- Duplicate game registration (same `season + date + opponent`) is prevented; correction is the only way to change a recorded game.
- Internal database IDs are implementation details and must not be exposed in any user-facing screen.

---

## 6) Quality Attributes (Non-Functional)
- **Architecture**: strict separation of domain / application / infrastructure / UI.
- **Testability**: core use cases and calculations covered by unit tests.
- **Reliability**: input validation and transactional writes for game + player stats.
- **Usability**: minimal workflow for manual entry; clear feedback for all user actions.
- **Portability**: core independent of GUI framework.

---

## 7) Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full architecture description: layer breakdown, port interfaces, composition root, key architectural decisions, and extension points.

Summary:
- **Domain** (`app/domain/`): entities and domain services; no external dependencies.
- **Application** (`app/application/use_cases.py`): use cases and port Protocols.
- **Infrastructure** (`app/infrastructure/`): SQLite repositories, SMTP email adapter.
- **Presentation** (`app/ui/`): Tkinter GUI; calls use cases only.

---

## 8) Data Model

```
players         (id, name, role CHECK('skater','goalie'),
                 player_type CHECK('permanent','substitute'), active, created_at)
seasons         (id, label UNIQUE)
                -- label format: "YYYY-YY", e.g. "2025-26"; derived from game date, never user-entered
season_roster   (id, player_id, season_id, jersey_number,
                 UNIQUE(player_id, season_id))
                -- permanent players only; stores default jersey for the season
games           (id, season_id, date, opponent, result CHECK('win','loss'),
                 game_type CHECK('regular','playoff') DEFAULT 'regular', notes)
skater_game_stats (id, game_id, player_id, jersey_number, goals, assists, pim, shg, ppg)
goalie_game_stats (id, game_id, player_id, jersey_number, saves, goals_against,
                   shots_received [computed: saves+goals_against, stored for query perf])
mail_recipients (id, email UNIQUE, name)
email_logs      (id, subject, recipients, success, detail, created_at)
```

Unique constraint on `games(season_id, date, opponent)`.

---

## 9) Acceptance Criteria
- Can add, edit, and remove players; list active roster.
- Player type (permanent / substitute) is captured and stored.
- Default jersey number for permanent players is stored in `season_roster` and pre-filled in game entry.
- Can register one game with mixed skater + goalie stats; optional jersey numbers accepted; jersey number shown in dashboard.
- Game type (regular/playoff) is recorded and displayed in separate dashboard blocks.
- Season dashboard is read-only and shows jersey numbers.
- Season is derived from the game date automatically; no manual season input.
- Date picker defaults to today; dates outside September–April are rejected.
- Correction flow: changing a game date updates the existing record (does not create a duplicate); cross-season date changes are rejected with a clear error.
- SV% is computed correctly (`saves / (saves + goals_against)`); shows `N/A` when shots = 0.
- Team wins/losses update after each game, split by game type.
- Stats summary email is sent automatically after game save/correction.
- Correct Last Game and Correct Any Game flows work; stats replace atomically.
- Duplicate detection shows a clear, descriptive error message.
- No internal database IDs are shown in any part of the UI.

---

## 10) Stack
- Python 3.12+
- SQLite (via `sqlite3` stdlib)
- Tkinter (desktop UI)
- `pytest` (testing)

---

## 11) Input Artifact
- Example score sheet reference: `score_sheet.pdf` (maps GUI fields; also used as future AI ingestion payload reference).

