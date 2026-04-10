# Architecture

> This document describes the structural design of the hockey-stats application.
> For *what to build* (requirements, acceptance criteria), see [`specs.md`](../specs.md).
> For the object model, see [`docs/class_diagram.md`](class_diagram.md).

---

## Overview

The application follows **Clean Architecture** (also known as Ports & Adapters or Hexagonal Architecture). The core principle is the **Dependency Rule**: source code dependencies point only inward — inner layers know nothing about outer layers.

```
┌──────────────────────────────────────────────────────────┐
│                    Presentation (UI)                     │
│               app/ui/tk_app.py  (Tkinter)                │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Application (Use Cases)               │  │
│  │         app/application/use_cases.py               │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │                 Domain                       │  │  │
│  │  │   app/domain/models.py  services.py          │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
│               Infrastructure                             │
│   app/infrastructure/sqlite_db.py  email_sender.py       │
└──────────────────────────────────────────────────────────┘
```

Dependencies flow inward:

- UI → Application → Domain (no dependency goes the other way)
- Infrastructure → Application (via Protocol interfaces defined in the application layer)

---

## Layers

### Domain Layer (`app/domain/`)

The innermost layer. Contains pure business logic with **no external dependencies** — no database, no HTTP, no framework.

**Entities**

| Class | Description |
|-------|-------------|
| `Player` | Team member with a primary role (skater or goalie) |
| `SkaterGameStatInput` | Stats line for a skater in one game |
| `GoalieGameStatInput` | Stats line for a goalie in one game |
| `MailRecipient` | Email address on the mailing list |

> Note: `Season`, `Game`, `SkaterGameStat`, and `GoalieGameStat` are represented as typed dictionaries in the application layer (`GameInfo`, `GameDetail`, `SeasonSummary`) rather than domain entities, because they are primarily read-model projections returned from the database. The domain layer owns the input shapes; the repository returns aggregated read models.

**Domain Services**

| Function | Description |
|----------|-------------|
| `calculate_save_percentage(saves, shots_received)` | Returns `saves / shots_received`, or `NaN` if shots = 0 |

---

### Application Layer (`app/application/use_cases.py`)

The orchestration layer. Defines **use cases** (business operations) and **port interfaces** (Protocols) that the infrastructure layer must implement.

**Port Interfaces (Protocols)**

| Interface | Implemented by |
|-----------|---------------|
| `PlayerRepository` | `SqlitePlayerRepository` |
| `GameRepository` | `SqliteGameRepository` |
| `MailingListRepository` | `SqliteMailingListRepository` |
| `EmailSender` | `SmtpEmailSender` / `MockEmailSender` (via `AutoEmailSender`) |
| `EmailLogRepository` | `SqliteEmailLogRepository` |

**`HockeyService` use cases**

*Player management*

- `add_player(name, role)` → validates and delegates to `PlayerRepository`
- `edit_player(player_id, name, role)` → updates name and primary role; historical stats are preserved
- `remove_player(player_id)` → marks inactive; historical stats are retained
- `list_active_players()` → returns active roster

*Game recording*

- `record_game_stats(...)` → validates, persists, triggers auto-email
- `correct_game_stats(game_id, ...)` → transactionally replaces old game data, triggers auto-email
- `get_last_game()` → returns the most recently saved game for "Correct Last Game" flow
- `list_games_by_season(season_label)` → used by the correction picker UI
- `get_game_by_id(game_id)` → loads a specific game for editing

*Stats*

- `get_season_stats(season_label)` → aggregated season summary split by regular/playoff, with SV% computed

*Email*

- `send_season_stats_email(season_label)` → manual resend
- `_auto_send_email(season_label)` → silent send after game save/correction; logs result, never raises

*Mailing list*

- `add_mail_recipient(name, email)`, `remove_mail_recipient(id)`, `list_mail_recipients()`

**Validation** lives in the application layer, not the domain or UI:

- Required fields (season, opponent)
- Enum constraints (result: win/loss; game_type: regular/playoff; role: skater/goalie)
- Non-negative stats
- ISO 8601 date format

---

### Infrastructure Layer (`app/infrastructure/`)

Adapters that implement the port interfaces using concrete external systems.

#### `sqlite_db.py`

Contains the SQLite schema and all repository implementations.

**Schema** (see also `specs.md` §8):

```sql
players           (id, name, role, active, created_at)
seasons           (id, label UNIQUE)
games             (id, season_id, date, opponent, result, game_type, notes)
                  UNIQUE(season_id, date, opponent)  -- duplicate detection
skater_game_stats (id, game_id, player_id, jersey_number, goals, assists, pim, shg, ppg)
goalie_game_stats (id, game_id, player_id, jersey_number, saves, goals_against, shots_received)
mail_recipients   (id, email UNIQUE, name)
email_logs        (id, subject, recipients, success, detail, created_at)
```

`shots_received` is stored (derived as `saves + goals_against`) for query performance. It is never entered directly by the user.

The `correct_game` operation deletes and reinserts all stat lines atomically within a transaction.

#### `email_sender.py`

`AutoEmailSender` selects the implementation at runtime:

- If all SMTP environment variables are present → `SmtpEmailSender` (real STARTTLS email)
- Otherwise → `MockEmailSender` (logs to console, returns success)

Both implementations satisfy the `EmailSender` protocol. All sends are logged to `email_logs`.

---

### Presentation Layer (`app/ui/tk_app.py`)

A Tkinter desktop GUI. The UI:

- Calls `HockeyService` use cases exclusively — no direct DB or domain access.
- Provides four tabs: Roster, Game Entry, Dashboard, Mailing.
- Handles all user feedback (error dialogs, info messages).
- Maintains ephemeral UI state (pending stat lines, correction mode) independently of the service.

The UI is deliberately thin: it translates user gestures into use case calls and renders results. Business logic does not live here.

---

## Composition Root

`app/main.py` is the **composition root** — the single place where all layers are wired together:

```python
db = SqliteDatabase("data/hockey.sqlite3")
service = HockeyService(
    players=SqlitePlayerRepository(db),
    games=SqliteGameRepository(db),
    mailing=SqliteMailingListRepository(db),
    sender=AutoEmailSender(),
    email_logs=SqliteEmailLogRepository(db),
)
app = HockeyApp(service)
```

This is the only place that knows about all layers simultaneously. Changing infrastructure (e.g., swapping SQLite for Postgres) requires changing only `main.py` and the new adapter — the domain and application layers are untouched.

---

## Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| Python `Protocol` for ports | Structural typing (duck typing) — no inheritance required, libraries not needed |
| SQLite / stdlib only | Minimizes dependencies; suitable for a single-user desktop app |
| `shots_received` stored in DB | Denormalization justified by read performance; spec explicitly documents and justifies it |
| Auto-email never raises | A delivery failure must not block a game save; logged instead |
| `game_type` default `'regular'` | Backward compatibility for records created before the field was added |
| Jersey number per game line | Business rule: same number can be used by different players across seasons |

---

## Extension Points

| Extension | How to add |
|-----------|-----------|
| Web / mobile UI | Implement a new presentation layer calling the same `HockeyService` |
| Different database | Implement the repository protocols; swap in `main.py` |
| AI ingestion (FR-8) | Add `AIIngestionGateway` protocol; call `record_game_stats` from the adapter |
| Multi-team support | New entity `Team`; add `team_id` FK to relevant tables; update repository queries |
