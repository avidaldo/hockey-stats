# Specifications

> **Current version: v2** (initial PoC spec merged with post-demo client requirements).
> See `open_questions.md` for unresolved decisions.
> See `docs/class_diagram.md` for the object model (UML class diagram).

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
- Authentication/authorization.
- Cloud deployment.

---

## 3) Actors
- **Team Manager**: enters data, manages roster, and initiates corrections.
- **Coach/Staff**: reviews stats dashboard/reports.
- **System**: calculates aggregates and sends email notifications.
- **External AI Agent** (future): extracts structured data from score sheet images.

---

## 4) Functional Requirements

### FR-1 Team Configuration
- Add player with initial stats = 0.
- **Edit** an existing player's name and primary role (preserves all historical game stats).
- Remove player from active roster (mark inactive; historical stats are retained).
- Player has a **primary role**: `skater` or `goalie`.
- As an exception, a player may play a **different role in a specific game** (e.g., skater filling in as goalie). The game entry form defaults to the player's primary role; the user can override it per game.
- Aggregation is role-aware per game record; season totals keep skater and goalie metric families separated.

### FR-2 Input Match/Score Sheet Data
- Data is entered via GUI form that maps to score sheet fields.
- Game input must capture:
    - Game metadata: date, opponent, season, **game type** (`regular` / `playoff`), result (win/loss), optional notes.
    - Per skater: **optional jersey number**, goals, assists, PIM, SHG, PPG.
    - Per goalie: **optional jersey number**, saves, goals against. `ShotsReceived` is always computed as `Saves + GoalsAgainst` and displayed read-only — it is not a free-entry field.
- Save operation validates required fields and rejects invalid values (negative stats, unknown player).
- Duplicate game detection: same `season + date + opponent`. Error message clearly states the duplicate, which record already exists, and how to correct it.

### FR-3 Display Season Outputs
- Season stats dashboard is **read-only**. Corrections go through the dedicated correction flow.
- Stats are displayed in **two separate blocks**: regular season and playoffs.
- Per skater: Goals, Assists, PIM, SHG, PPG.
- Per goalie: Saves, Wins, Goals Against, SV%.
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
- On save, corrected stats replace the previous ones atomically (transactional delete + reinsert).
- Automatic email is triggered after a successful correction.

### FR-8 AI Ingestion Extension (Future)
- Provide interface/port to accept structured score-sheet payload from external AI.
- Core validation and persistence reused from the manual input flow.

---

## 5) Business Rules
- Stats are cumulative from recorded games, not manually editable totals.
- Each game belongs to exactly one season and has one game type (`regular` or `playoff`).
- Jersey number is recorded per game stat line (not as a fixed player attribute). The same number may be used by different players across seasons and by temporary players within a season.
- A player's primary role is a profile attribute; a per-game role override is allowed.
- Duplicate game registration (same `season + date + opponent`) is prevented; correction is the only way to change a recorded game.

---

## 6) Quality Attributes (Non-Functional)
- **Architecture**: strict separation of domain / application / infrastructure / UI.
- **Testability**: core use cases and calculations covered by unit tests.
- **Reliability**: input validation and transactional writes for game + player stats.
- **Usability**: minimal workflow for manual entry; clear feedback for all user actions.
- **Portability**: core independent of GUI framework.

---

## 7) Clean Architecture

### Domain Layer
- Entities: `Player`, `Season`, `Game`, `SkaterGameStat`, `GoalieGameStat`, `MailRecipient`.
- Value objects: `PlayerId`, `SeasonId`, `EmailAddress`, `GameResult`, `GameType`.
- Domain services: `SeasonStatAggregator`, `GoalieSavePercentageCalculator`.

### Application Layer (Use Cases / Service)
- `add_player`, `edit_player`, `remove_player`, `list_active_players`
- `record_game_stats`, `correct_game_stats`, `get_last_game`, `list_games_by_season`
- `get_season_stats`
- `send_season_stats_email`
- `add_mail_recipient`, `remove_mail_recipient`, `list_mail_recipients`

### Ports (Interfaces)
- `PlayerRepository`
- `GameRepository`
- `MailingListRepository`
- `EmailSender`
- `EmailLogRepository`
- `AIIngestionGateway` (future)

### Infrastructure Layer
- SQLite repositories.
- SMTP adapter for email (mock fallback when unconfigured).

### Presentation Layer
- Tkinter desktop GUI calling use cases only.

---

## 8) Data Model

```
players         (id, name, role CHECK('skater','goalie'), active, created_at)
seasons         (id, label UNIQUE)
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
- Can register one game with mixed skater + goalie stats; optional jersey numbers accepted.
- Game type (regular/playoff) is recorded and displayed in separate dashboard blocks.
- Season dashboard is read-only.
- SV% is computed correctly (`saves / (saves + goals_against)`); shows `N/A` when shots = 0.
- Team wins/losses update after each game, split by game type.
- Stats summary email is sent automatically after game save/correction.
- Correct Last Game and Correct Any Game flows work; stats replace atomically.
- Duplicate detection shows a clear, descriptive error message.

---

## 10) Stack
- Python 3.12+
- SQLite (via `sqlite3` stdlib)
- Tkinter (desktop UI)
- `pytest` (testing)

---

## 11) Input Artifact
- Example score sheet reference: `score_sheet.pdf` (maps GUI fields; also used as future AI ingestion payload reference).

