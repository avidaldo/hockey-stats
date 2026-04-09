# Object Model — Class Diagram

```mermaid
classDiagram
    direction LR

    class Player {
        +int id
        +str name
        +str role  %% "skater" | "goalie"
        +bool active
        +datetime created_at
    }

    class Season {
        +int id
        +str label
    }

    class Game {
        +int id
        +str date
        +str opponent
        +str result    %% "win" | "loss"
        +str game_type %% "regular" | "playoff"
        +str notes
    }

    class SkaterGameStat {
        +int id
        +int jersey_number  %% optional
        +int goals
        +int assists
        +int pim
        +int shg
        +int ppg
    }

    class GoalieGameStat {
        +int id
        +int jersey_number   %% optional
        +int saves
        +int goals_against
        +int shots_received  %% computed: saves + goals_against
    }

    class MailRecipient {
        +int id
        +str name
        +str email
    }

    Season "1" --> "0..*" Game : contains
    Game "1" --> "0..*" SkaterGameStat : has
    Game "1" --> "0..*" GoalieGameStat : has
    Player "1" --> "0..*" SkaterGameStat : recorded as skater
    Player "1" --> "0..*" GoalieGameStat : recorded as goalie
```

## Notes

- `shots_received` on `GoalieGameStat` is always derived as `saves + goals_against`. It is stored for query performance but never entered by the user.
- `jersey_number` is per game stat line, not a player profile attribute. The same number may be reused across seasons or by substitute players.
- A `Player` has one primary `role`, but can appear in either `SkaterGameStat` or `GoalieGameStat` per game (exception role override).
- `MailRecipient` has no relationship to `Player`; the mailing list is managed independently.
