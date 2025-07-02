from typing import Optional, Literal, List
from pydantic import BaseModel


class UpdatedMatch(BaseModel):
    id: int
    first_player_id: int
    first_player_score: int
    first_nickname: str
    first_rating: Optional[int]
    first_rating_new: int
    second_player_id: int
    second_player_score: int
    second_nickname: str
    second_rating: Optional[str]
    second_rating_new: int
    is_approved: bool
    server: str

    class Config:
        from_attributes = True  # Allows mapping from SQLAlchemy objects
