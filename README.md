# Liam Hockey PoC

Desktop Python app to manage amateur hockey stats with a clean-architecture style split.

## Features (PoC)
- Roster management (add/remove active players)
- Game stat input (skater + goalkeeper lines per game)
- Season cumulative dashboard
- Independent mailing list
- Send season summary by email (SMTP if configured, fallback mock sender)

## Run
1. Create and activate your Python environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Start app:
   - `python -m app.main`

## Seed demo data
- Run:
  - `python scripts/seed_demo.py`
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
- Duplicate game registration is prevented by `season + date + opponent`.
