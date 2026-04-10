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
**Status:** Completed — ready for next client demo  
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

### What to validate at next client demo

1. Correction flow: is the two-step load-then-save intuitive?
2. Playoff split: does the dashboard format match what coaches actually use?
3. Email format: does the text summary contain the right information in a readable format?
4. Jersey number behavior: is per-game-line tracking sufficient, or do coaches want per-season tracking?

---

## Iteration 0.3 — Next (planned)

**Type:** TBD (scope to be defined after client demo of v0.2)  
**Status:** Not started — awaiting client feedback

### Input

- Feedback from the v0.2 demo (to be captured in `open_questions.md` during the meeting).
- Any items promoted from the current open questions.

### Candidate features (unconfirmed)

These are hypotheses, not confirmed requirements. They will only be added to `specs.md` after the client validates them:

- Jersey number uniqueness rule within a season (resolve current open question).
- HTML email format for the stats summary.
- Filter/search in the "Correct Any Game" picker.
- Export to CSV or PDF.
- AI score sheet ingestion (FR-8 extension point, if client prioritizes it).

### Planned technical improvements (independent of client feedback)

These are quality/tooling items already identified as deferred from v0.2. They do not require client validation but should be included in the next iteration.

- **Unit and integration test suite** — `specs.md §6` requires core use cases and calculations to be covered by unit tests; this was deferred from the MVP. Planned scope: domain tests (pure unit), use case tests (mocked repositories), SQLite integration tests (in-memory DB). Tool: `pytest` + `pytest-cov` added as dev dependencies in `pyproject.toml`. See the conversation in the session documentation for the full test plan.
- **Copilot instruction files** — Add `.github/copilot-instructions.md` (workspace-level Copilot context) to make every AI session automatically aware of the project's SDD workflow, architecture rules, and spec references. Described in [`docs/sdd_workflow.md §7`](sdd_workflow.md).
