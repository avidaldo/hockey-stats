# Open Questions

This file tracks unresolved design decisions. In the Spec-Driven Development workflow this project follows, open questions serve a specific purpose:

- **During a development iteration**: they capture decisions that cannot be made yet — either because technical information is missing, or because the client needs to weigh in.
- **After a client demo**: each question is reviewed with the client and either promoted to a confirmed requirement in `specs.md`, marked as explicitly out of scope (Non-Goal), or left for a future iteration.

Open questions should not be resolved by guessing. They are honest acknowledgment of uncertainty, not failures. See [`docs/sdd_workflow.md`](docs/sdd_workflow.md) for context.

Resolved items have been incorporated into [`specs.md`](specs.md).

---

## Jersey Numbers

- **Within a season**: can two *regular* (non-temporary) players share the same jersey number in the same season?
    - Current assumption: no — only temporary/substitute players may share a number.
    - No uniqueness constraint is currently enforced in the DB; this is left as a validation decision.

## Game Corrections

- Should corrections be restricted to a time window after the game (e.g., 24 hours), or always allowed?
    - Current implementation: corrections allowed at any time.

## Season / Playoff Labels

- Are playoffs part of the same season label (e.g., `2024-25`) or a separate label?
    - Current implementation: same label, differentiated by `game_type = 'playoff'`.

## Backward Compatibility

- How should records created before the `game_type` and `jersey_number` fields were added behave?
    - Current migration: `game_type` defaults to `'regular'`; `jersey_number` defaults to `NULL`.

## Role Decisions

- Can the same player hold both skater and goalie primary roles simultaneously? (No — one primary role, override per game.)
- Should stats from games where a player played an exception role be shown in both stat families, or only in the overridden family?
    - Current implementation: only in the overridden family (the actual game role determines the stat family).
