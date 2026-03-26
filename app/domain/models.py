from dataclasses import dataclass


@dataclass(slots=True)
class Player:
    id: int
    name: str
    role: str
    number: int | None
    active: bool


@dataclass(slots=True)
class MailRecipient:
    id: int
    name: str
    email: str


@dataclass(slots=True)
class SkaterGameStatInput:
    player_id: int
    goals: int = 0
    assists: int = 0
    pim: int = 0
    shg: int = 0
    ppg: int = 0


@dataclass(slots=True)
class GoalieGameStatInput:
    player_id: int
    saves: int = 0
    goals_against: int = 0
    shots_received: int = 0
