# Specifications

## 1) Product Overview
- Desktop application for managing and displaying cumulative hockey stats by season.
- Core must follow Clean Architecture so UI can be replaced (desktop now, potentially web/mobile later).
- Initial users are team staff/coaches managing one team.

## 2) Goals and Non-Goals

### Goals (MVP)
- Register and manage team roster (add/remove players).
- Register game-by-game stats from score sheet fields.
- Show cumulative season stats (player, goalkeeper, team).
- Send updated stats summary to a team mailing list.

### Non-Goals (for PoC)
- Full OCR pipeline for score sheet images (keep as extension point).
- Advanced analytics beyond requested metrics.
- Multi-team / multi-league support.

## 3) Actors
- Team Manager: enters data and manages roster.
- Coach/Staff: reviews stats dashboard/reports.
- System: calculates aggregates and sends email notifications.
- External AI Agent (future): extracts structured data from score sheet images.

## 4) Functional Requirements

### FR-1 Team Configuration
- Add player with initial stats = 0.
- Remove player from active roster.
- Keep player historical stats for past games/seasons even if removed from active roster.
- Player has role/position: `skater` or `goalkeeper`.
- For PoC, role can change over time; game stats determine role-specific aggregation.

### FR-2 Input Match/Score Sheet Data
- Data is entered via GUI form that maps to score sheet fields.
- At minimum, game input must capture:
    - Game metadata: date, opponent, season, result (win/loss), optional notes.
    - Per skater: goals, assists, PIM, SHG, PPG.
    - Per goalkeeper: saves, goals against, shots received (if not entered, derive from saves + goals against).
- Save operation validates required fields and rejects invalid values (negative stats, unknown player).

### FR-3 Display Season Outputs
- Show cumulative stats per season.
- Per skater:
    - Goals
    - Assists
    - PIM
    - SHG
    - PPG
- Per goalkeeper:
    - Saves
    - Wins
    - Goals Against
    - SV% (save percentage)
- Team stats:
    - Wins
    - Losses

### FR-4 Derived Metrics
- Goalkeeper save percentage is calculated dynamically:
    - $SV\% = \frac{Saves}{ShotsReceived}$
- If `ShotsReceived = 0`, display `SV% = NaN`.

### FR-5 Send Stats by Email
- After stats update, system can send summary email to mailing list.
- Email includes season summary (team + top-level player and goalkeeper totals).
- Delivery result (success/failure) is logged.

### FR-6 Manage Mailing List
- Add email recipient.
- Remove recipient.
- List all recipients.
- Mailing list is independent from players (no linkage required in PoC).

### FR-7 AI Ingestion Extension (Future)
- Provide interface/port to accept structured score-sheet payload from external AI.
- Core validation and persistence are reused from manual input flow.

## 5) Business Rules
- Stats are cumulative from recorded games, not manually editable totals.
- A player can switch between skater and goalkeeper across games.
- Aggregation is role-aware per game record; season totals keep skater and goalkeeper metric families separated.
- Each game belongs to exactly one season.
- Duplicate game registration (same date + opponent + season) is prevented unless explicitly overridden.

## 6) Quality Attributes (Non-Functional)
- Architecture: strict separation of domain/application/infrastructure/UI.
- Testability: core use cases and calculations covered by unit tests.
- Reliability: input validation and transactional writes for game + player stats.
- Usability: minimal workflow for manual entry in desktop UI.
- Portability: core independent of GUI framework.

## 7) Proposed Clean Architecture

### Domain Layer
- Entities: `Player`, `Season`, `Game`, `PlayerGameStat`, `GoalieGameStat`, `MailRecipient`.
- Value objects: `PlayerId`, `SeasonId`, `EmailAddress`, `GameResult`.
- Domain services: `SeasonStatAggregator`, `GoalieSavePercentageCalculator`.

### Application Layer (Use Cases)
- `AddPlayer`
- `RemovePlayer`
- `RecordGameStats`
- `GetSeasonStats`
- `SendSeasonStatsEmail`
- `AddMailRecipient` / `RemoveMailRecipient` / `ListMailRecipients`

### Ports (Interfaces)
- `PlayerRepository`
- `GameRepository`
- `SeasonStatsRepository` (or query service)
- `MailingListRepository`
- `EmailSender`
- `AIIngestionGateway` (future)

### Infrastructure Layer
- SQLite repositories.
- Pandas-based aggregation adapter (if needed for reporting/export).
- SMTP adapter for email.

### Presentation Layer
- Desktop GUI adapter (framework TBD) calling use cases only.

## 8) Data Model (Initial)
- `players(id, name, role, active, created_at)`
- `seasons(id, label, start_date, end_date)`
- `games(id, season_id, date, opponent, result, notes)`
- `skater_game_stats(id, game_id, player_id, goals, assists, pim, shg, ppg)`
- `goalie_game_stats(id, game_id, player_id, saves, goals_against, shots_received)`
- `mail_recipients(id, email, name)`

## 9) PoC Scope (Implementation Phase 1)
- In scope:
    - SQLite persistence.
    - Core domain + use cases.
    - Basic desktop UI for roster management, game entry, and season dashboard.
    - Email sending with plain-text summary.
- Out of scope:
    - AI image ingestion implementation.
    - Authentication/authorization.
    - Cloud deployment.

## 10) Acceptance Criteria for PoC
- Can add/remove players and list active roster.
- Can register one game with mixed skater + goalkeeper stats.
- Season dashboard totals match manual calculation for test data.
- SV% is computed correctly and shown for goalkeeper(s).
- Team wins/losses update after each game.
- Stats summary email can be sent to all mailing recipients.

## 11) Suggested Stack
- Python 3.12+
- SQLite
- Pandas (for aggregation/reporting tasks)
- Desktop UI framework: Tkinter (PoC decision)
- Testing: `pytest`

## 12) Input Artifact
- Example score sheet reference: `score_sheet.pdf` (to map GUI fields and future AI ingestion payload).



