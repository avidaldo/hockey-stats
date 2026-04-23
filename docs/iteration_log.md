# Iteration Log

> This document tracks the major development iterations of the hockey-stats project. It records what was built, what was validated with the client, and what feedback drove the next iteration.
>
> See [`docs/sdd_workflow.md`](sdd_workflow.md) for an explanation of how this log fits into the Spec-Driven Development process.

---

## Iteration 0.1 — Proof of Concept

**Type:** PoC  
**Status:** Completed, presented to client

### Goal

Validate the core concept: can a Python desktop application (Tkinter + SQLite) serve as a practical hockey stats manager for a team's coaching staff?

### What was built

- Basic player roster (add/remove).
- Manual game stat entry for skaters and goalies.
- Season cumulative stats view.
- Single season, no game type differentiation.

### What was validated

- The desktop approach is viable for the target users (team staff, non-technical).
- Score sheet fields map cleanly to the input form.
- SQLite is sufficient for the data volume and access patterns.

### Client feedback that drove v0.2

The client demo surfaced the following new requirements and clarifications (captured initially in `open_questions.md`, then promoted to `specs.md` v2):

| Feedback | Result in v0.2 |
|----------|---------------|
| "We need to fix mistakes after saving a game" | FR-7: Correct Last Game and Correct Any Game flows |
| "Playoffs are part of the same season but different stats" | `game_type` field (regular/playoff); split dashboard blocks |
| "Players sometimes fill in for the goalie — rare, but it happens" | Per-game role override; stats aggregated by actual game role |
| "Send the stats to the whole coaching staff by email after each game" | FR-5: automatic email on save/correction; FR-6: mailing list |
| "Jersey numbers change — don't lock them to players" | Jersey number per game stat line, not a player profile attribute |
| "Can we edit a player's name?" | FR-1: edit player name and role |

---

## Iteration 0.2 — Minimum Viable Product (current)

**Type:** MVP  
**Status:** Completed — demo presented to client (2026-04-23)  
**Spec version:** v2 ([`specs.md`](../specs.md))

### Goal

Implement all requirements identified from the v0.1 demo. The result should be a system the coaching staff can use through a full regular season and playoffs.

### What was built

- **FR-1**: Full roster management — add, edit (name + role), remove (soft delete, history preserved).
- **FR-2**: Complete game entry form — all score sheet fields, game type selection, optional jersey numbers, shots-received computed read-only.
- **FR-3**: Season dashboard split into regular season and playoffs blocks; read-only.
- **FR-4**: SV% computed correctly; `N/A` when shots = 0.
- **FR-5**: Automatic email sent after every game save or correction; logged.
- **FR-6**: Mailing list management — add, remove, list; independent from roster.
- **FR-7**: "Correct Last Game" shortcut and "Correct Any Game" picker; atomic stat replacement.
- **Duplicate detection**: Clear error message when `season + date + opponent` already exists.
- **Architecture**: Full Clean Architecture layering — domain, application, infrastructure, UI.
- **Data migrations**: Backward-compatible defaults for `game_type` and `jersey_number`.

### Deferred to future iterations

Items captured in [`open_questions.md`](../open_questions.md) that were explicitly not implemented in v0.2:

- Jersey number uniqueness constraint within a season (business rule not finalized with client).
- Correction time window restriction.
- Score sheet image OCR / AI ingestion pipeline (FR-8, explicitly a Non-Goal for this iteration).

### What was validated at the v0.2 demo (2026-04-23)

| Question | Client Answer |
|----------|--------------|
| Correction flow intuitive? | Yes, but revealed a bug: date change creates new game instead of updating existing |
| Playoff split format OK? | Yes |
| Email format OK? | Yes |
| Jersey number per-game-line sufficient? | No — permanent players need a fixed jersey per season as a default |

### Client feedback that drives v0.3

Full structured notes in [`notes-v3.md`](../notes-v3.md). Summary:

| Feedback | Action for v0.3 |
|----------|----------------|
| Season should be derived from the date, not selectable | Remove season field from game entry; auto-derive from date (Sep–Apr rule) |
| Date should default to today; constrained to Sep–Apr | Add date picker with today default; validate against season months |
| Bug: date change in correction creates a new game | Fix correction flow to update existing record in-place |
| Internal row ID shown in UI — user doesn't want it | Remove all internal ID display from UI |
| Jersey as default per player per season | Add `player_type` + `season_roster` table; pre-fill jersey in game entry form |
| Dashboard should show jersey numbers | Add jersey number column to dashboard stat tables |
| Players identified by name — can cause confusion | Use player ID for lookup; display must be unambiguous |
| Permanent vs. substitute player categories | New `player_type` attribute on players; roster stores permanent jerseys only |
| Multi-user with roles needed | Confirmed requirement; exact permissions still under discussion |

---

## Iteration 0.3 — Next (planned)

**Type:** Feature iteration  
**Status:** Not started — spec v3 confirmed; awaiting implementation  
**Spec version:** v3 ([`specs.md`](../specs.md))  
**Meeting notes:** [`notes-v3.md`](../notes-v3.md)

### Confirmed requirements (from v0.2 demo)

- **Season auto-derivation**: remove the season selector; compute season label from game date using the Sep–Apr rule. Date picker defaults to today; dates outside Sep–Apr are rejected.
- **Correction flow bug fix**: when a game date is changed during correction, update the existing record rather than creating a new one. Reject cross-season date changes.
- **Player type**: add `permanent` / `substitute` distinction to players.
- **Season roster**: `season_roster` table; store default jersey per permanent player per season.
- **Jersey in game entry**: pre-fill jersey from season roster for permanent players; override allowed.
- **Jersey in dashboard**: display jersey number alongside player stats.
- **No internal IDs in UI**: remove all database ID display from every screen.
- **Multi-user with roles**: users and roles feature (permissions TBD; see [`open_questions.md`](../open_questions.md)).

### Deferred / still open

- Jersey number uniqueness constraint within a season (see open questions).
- Exact multi-user permission matrix (under discussion with client).
- HTML email format.
- Filter/search in the "Correct Any Game" picker.
- Export to CSV or PDF.
- AI score sheet ingestion (FR-8).

### Planned technical improvements (independent of client feedback)

These are quality/tooling items already identified as deferred from v0.2. They do not require client validation but should be included in the next iteration.

- **Unit and integration test suite** — `specs.md §6` requires core use cases and calculations to be covered by unit tests; this was deferred from the MVP. Planned scope: domain tests (pure unit), use case tests (mocked repositories), SQLite integration tests (in-memory DB). Tool: `pytest` + `pytest-cov` added as dev dependencies in `pyproject.toml`. See the conversation in the session documentation for the full test plan.
- **Copilot instruction files** — Add `.github/copilot-instructions.md` (workspace-level Copilot context) to make every AI session automatically aware of the project's SDD workflow, architecture rules, and spec references. Described in [`docs/sdd_workflow.md §7`](sdd_workflow.md).
