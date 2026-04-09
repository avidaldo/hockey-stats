# Liam Hockey Stats

Desktop Python app to manage amateur hockey stats with a clean-architecture style split.

## Documentation
- `specs.md` — full product specifications (v2, current).
- `open_questions.md` — unresolved design decisions.
- `docs/class_diagram.md` — UML class diagram (Mermaid).
- `score_sheet.pdf` — score sheet reference for GUI field mapping.

## Features
- Roster management: add, edit, and remove active players.
- Game stat input (skater + goalie lines per game) with optional jersey numbers.
- Game type tagging: regular season or playoffs.
- Season cumulative dashboard — **read-only**, split by regular and playoff blocks.
- Correct last game or any past game (stats replaced atomically).
- Automatic stats email after every game save/correction.
- Independent mailing list management.
- SMTP email (mock sender if SMTP is unconfigured); all sends are logged.

## Run
1. Create and activate your Python environment.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Start app:
   ```
   python -m app.main
   ```

## Seed demo data
```
python scripts/seed_demo.py
```
Creates sample players, recipients, and one demo game (idempotent).

## SMTP (optional)
If these environment variables are present, real SMTP sending is used:
- `HOCKEY_SMTP_HOST`
- `HOCKEY_SMTP_PORT` (default `587`)
- `HOCKEY_SMTP_USER`
- `HOCKEY_SMTP_PASSWORD`
- `HOCKEY_SMTP_FROM`
- `HOCKEY_SMTP_TLS` (`true`/`false`, default `true`)

If missing, the mock sender is used and email attempts are still logged.

## Notes
- `SV%` shows `N/A` when shots received is 0.
- Shots received is always computed as `saves + goals against`; it is not a free-entry field.
- Duplicate game detection is by `season + date + opponent`; use the correction flow to fix recorded games.
