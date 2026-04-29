# Client Meeting Notes — v0.2 Demo Feedback

**Date:** 2026-04-23  
**Purpose:** Review v0.2 demo with client; capture feedback to drive iteration 0.3.

---

## Feedback Raised

### Date Handling

- Season must be **consecutive years** (e.g., `2025-26`), not an open-text field.
- Season should be **derived automatically from the game date** — the user should never select the season manually.
  - Hockey season runs **September through April**.
  - A date in September–December of year Y belongs to season `Y-(Y+1)` (e.g., November 2025 → `2025-26`).
  - A date in January–April of year Y belongs to season `(Y-1)-Y` (e.g., March 2026 → `2025-26`).
- Game date must be validated: only dates in September–April are accepted.
- Date picker should use standard calendar controls (not a plain text box).
- Date should **default to today**.
- **Bug:** In the current correction flow, changing the date on an existing game creates a *new* game record instead of updating the existing one. The old record is left behind.

### Player Identification

- Currently it is possible to enter stats for two players with the same name — the player must be identified by their internal ID, not by name lookup.
- The internal database numeric ID (row number) is being displayed in the UI; the user does not care about it and does not want to see it.

### Jersey Numbers

- Jersey number should be assignable as a **default when adding a player** (per season), and that default should be pre-filled when entering game stats. The user can still override it for a specific game.
- The **Dashboard should display the jersey number** alongside player stats.

### Roster Model (Permanent vs. Substitute Players)

- There are two categories of players (new terminology agreed with client):
  - **Permanent players**: members of the regular roster for the season. Each permanent player has a fixed jersey number for that season.
  - **Substitute players**: occasional fill-ins. Their jersey number varies and is not tracked in the roster.
- Substitute players' jersey numbers will not be stored in the roster, but may still be recorded on the game stat line if known.

### Multi-user / Roles

- The application needs to support multiple users with different roles (e.g., a manager who enters data vs. a coach who only views stats).
- Exact role definitions and permissions are **still under discussion** ("debate constante") — to be clarified before implementation.

---

## Raw Notes (Original)

> Preserved below as reference; structured version above supersedes.

- Dealing with dates there are several issues:
  - Selector of seasons
  - Season have to be consecutive years
  - Selector of dates with usual controls.
  - Restrictions: the Date have to be in the years of the season
  - September to april
  - The season should be calculated from the date, not openly selected
  - Date automatically today by default
  - Current flow of correcting a game, if you change the date, it just adds a new game with that date, but keeps old one
- multiuser so roles.
- now we are adding a number that's an id and showing it. The user don't care.
- number jersey can be assigned as default when adding a player, but still can be changed when adding a stat
- in Dashboard the number of the jersey
- currently adding the stats for two players with same name. A player should be established by the id, not the name.
- Roster per season, so permanent players have a permanent jersey in that season, and only substitute players (new terminology) change jersey, but we won't keep track of those numbers
- debate constante
