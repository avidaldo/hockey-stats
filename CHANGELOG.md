# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Why a CHANGELOG alongside git history?**
> Git history records every commit for developers. A CHANGELOG is a curated, human-readable narrative of *significant changes* for stakeholders (clients, instructors, new contributors) who need to understand what changed between versions without reading individual commits. Both serve different audiences.

---

## [Unreleased]

- Next client demo feedback and iteration 0.3 planning.

---

## [0.2.0] — 2026-04-10

**Iteration 0.2 — Minimum Viable Product.**
Full implementation of all requirements from the post-PoC client meeting (specs.md v2).

### Added

- **Game type (regular/playoff)**: `game_type` field on games; season dashboard split into two blocks.
- **Game corrections**: "Correct Last Game" shortcut and "Correct Any Game" picker; stats replaced atomically.
- **Per-game role override**: a player with a primary skater role can be entered as a goalie in a specific game, and vice versa.
- **Optional jersey numbers**: recorded per game stat line, not as a fixed player attribute.
- **Shots received (computed)**: always derived as `saves + goals_against`; displayed read-only in UI; stored denormalized in DB for query performance.
- **Player editing**: update a player's name and primary role without losing historical stats.
- **Email notifications**: automatic stats summary email after every game save or correction; manual resend button.
- **Mailing list management**: add, remove, and list email recipients (independent from roster).
- **Email logging**: all send attempts logged to `email_logs` table.
- **SMTP adapter**: real STARTTLS email when `HOCKEY_SMTP_*` env vars are set; mock sender otherwise.
- **Duplicate game detection**: clear error message when `season + date + opponent` already exists.
- **Soft delete for players**: removed players are marked inactive; all historical stats retained.
- **Seed script**: `scripts/seed_demo.py` for populating demo data (idempotent).
- **Clean Architecture**: domain / application / infrastructure / UI layers with Port interfaces (Protocols).
- **Documentation**: `specs.md` v2, `docs/architecture.md`, `docs/class_diagram.md`, `docs/iteration_log.md`, `docs/sdd_workflow.md`, `open_questions.md`.

### Changed

- Dashboard is now read-only; corrections go through the dedicated correction flow (FR-7).
- Season stats aggregation is role-aware per game record.

### Migration notes

- `game_type` defaults to `'regular'` for records created before this field was added.
- `jersey_number` defaults to `NULL` for records created before this field was added.

---

## [0.1.0] — 2025-02

**Iteration 0.1 — Proof of Concept.**
Initial working prototype to validate the core concept with the client.

### Added

- Basic player roster: add and remove players.
- Manual game stat entry for skaters and goalies.
- Season cumulative stats view.
- SQLite persistence (single file, `data/hockey.sqlite3`).
- Tkinter desktop UI.

---

[Unreleased]: https://github.com/avidaldo/hockey-stats/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/avidaldo/hockey-stats/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/avidaldo/hockey-stats/releases/tag/v0.1.0
