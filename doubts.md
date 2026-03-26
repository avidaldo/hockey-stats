# Open Questions / Decisions

## Roster and player lifecycle
- When removing a player, should the system:
	- A) mark as inactive (recommended), or
	- B) hard delete from roster/history?
- Can the same player return in a later season with the same identity?

## Positions and role changes
- Decision (PoC): players can switch between `skater` and `goalkeeper` at any time (amateur team reality).
- Implication for stats calculation:
	- Aggregation must be role-aware per game entry, not per fixed player profile.
	- A player may contribute skater stats in one game and goalkeeper stats in another.
	- Season totals should be split by stat family (skater totals vs goalkeeper totals) to avoid mixing incompatible metrics.

## Mailing list model
- Decision (PoC): mailing list is independent from players.
- Contacts are managed as recipients only; no player linkage is required.

## Game identity and duplicates
- What uniquely identifies a game for duplicate prevention?
	- Proposed default: `season + date + opponent`.

## Validation and display details
- Decision (PoC): for `SV%` when shots received is zero, display `NaN`.
- Should negative corrections be allowed via edit flow, or only by deleting/re-entering game data?

## Email behavior
- Should stats be sent automatically after each update, or manually via "Send" action (recommended for PoC)?
- Preferred email transport for PoC: SMTP account, local mail relay, or mock sender only?

## UI and platform
- Preferred desktop stack for PoC: Tkinter (lightweight) or PySide6 (richer UI)?
- Target OS only Windows, or cross-platform from start?