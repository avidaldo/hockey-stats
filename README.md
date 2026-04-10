# Liam Hockey Stats

Desktop Python app to manage amateur hockey stats with a clean-architecture style split.

## Documentation

| Document | Description |
|----------|-------------|
| [`specs.md`](specs.md) | Full product specification (v2, current) — requirements, data model, acceptance criteria |
| [`open_questions.md`](open_questions.md) | Unresolved design decisions; input for the next iteration |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history and notable changes |
| [`docs/architecture.md`](docs/architecture.md) | Architecture overview — layers, ports, key decisions |
| [`docs/class_diagram.md`](docs/class_diagram.md) | UML class diagram (Mermaid) |
| [`docs/iteration_log.md`](docs/iteration_log.md) | Iteration history — PoC → MVP → next |
| [`docs/sdd_workflow.md`](docs/sdd_workflow.md) | Didactic guide to Spec-Driven Development and AI-assisted workflows |
| `score_sheet.pdf` | Score sheet reference for GUI field mapping |

## Development Workflow

This project follows **Spec-Driven Development (SDD)**: the specification document (`specs.md`) is the single source of truth. Each iteration starts with an updated spec and ends with a client demo and feedback session.

Current iteration: **v0.2 (MVP)** — ready for client demo. See [`docs/iteration_log.md`](docs/iteration_log.md) for the full history and next planned iteration.

See [`docs/sdd_workflow.md`](docs/sdd_workflow.md) for a full explanation of the workflow, including how AI coding agents (GitHub Copilot) fit into the SDD process.

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
