from typing import List

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
    elo_rating: float
    matches: List[MatchResult] | None
    active: bool

    class Config:
        from_attributes = True


class UserDTO(UserDTOPublic):
    discord_id: str | None
    role: Role

    class Config:
        from_attributes = True
