# Liam Hockey v2

Desktop Python app to manage amateur hockey stats with a clean-architecture style split.

## Features (v2)
- **Roster management**: Add/edit/remove active players with jersey numbers
- **Game stat input**: Skater + goalie lines per game with season type (regular/playoff)
- **Game editing**: Load and modify any existing game stats
- **Season dashboard**: Read-only cumulative stats filtered by season type
- **Auto-calculated fields**: Shots = Saves + Goals Against (read-only)
- **Independent mailing list management**
- **Auto-email notifications**: Email sent automatically when a game is saved
- **Manual email sending**: Send season summary by email (SMTP or mock sender)

## Run
1. Create and activate your Python environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Start app:
   - `python3 -m app.main`

## Seed demo data
- Run:
  - `python3 scripts/seed_demo.py`
- It creates sample players, recipients, and one sample game (idempotent for players/recipients).

## SMTP (optional)
If these environment variables are present, SMTP sending is used:
- `HOCKEY_SMTP_HOST`
- `HOCKEY_SMTP_PORT` (default `587`)
- `HOCKEY_SMTP_USER`
- `HOCKEY_SMTP_PASSWORD`
- `HOCKEY_SMTP_FROM`
- `HOCKEY_SMTP_TLS` (`true`/`false`, default `true`)

If missing, app uses mock sender and still logs email attempts.

## Notes
- Save percentage uses `NaN` when shots received is 0.
- Duplicate game registration is prevented by `season + season_type + date + opponent`.
- The v1 database is backed up to `data/hockey_v1_backup.sqlite3` (if exists).

## v2 Changes
See [v2.md](v2.md) for full list of implemented changes.
