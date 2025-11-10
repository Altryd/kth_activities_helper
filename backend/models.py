from typing import List, Optional

from pydantic import BaseModel
from backend.database import Role  # , MatchStatus


class MatchResult(BaseModel):
    player1_id: int
    player2_id: int
    player1_score: int
    player2_score: int


class UserDTOPublic(BaseModel):
    osu_id: int
    username: str
    pp: float
    elo_rating: float | None
    matches: List[MatchResult] | None
    active: bool
    roulette_wins: None | int
    roulette_rolls: None | int
    roulette_winrate: Optional[float]
    roulette_streak_current: None | int
    roulette_achievements: None | list

    class Config:
        from_attributes = True


class UserDTO(UserDTOPublic):
    discord_id: str | None
    role: Role

    class Config:
        from_attributes = True
