from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String, Integer, Boolean, BigInteger, Table, Column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import registry

mapper_registry = registry()


class Base(DeclarativeBase):
    pass


class MyMixin(Base):
    __abstract__ = True

    def to_dict(self):
        return dict((col, getattr(self, col)) for col in self.__table__.columns)


class Matches(Base):
    __tablename__ = "matches"
    id = mapped_column(BigInteger, unique=True, primary_key=True, autoincrement=False)
    first_player_id = mapped_column(BigInteger, ForeignKey("player.osu_id"), nullable=False)
    first_player_score = mapped_column(Integer, nullable=False)
    first_player = relationship("Player", primaryjoin="(Player.osu_id == Matches.first_player_id)")
    second_player_id = mapped_column(BigInteger, ForeignKey("player.osu_id"), nullable=False)
    second_player_score = mapped_column(Integer, nullable=False)
    second_player = relationship("Player", primaryjoin="(Player.osu_id == Matches.second_player_id)")
    is_approved = mapped_column(Boolean, nullable=False, default=False)
    server: Mapped[str] = mapped_column(String(32))

    def __init__(self, match_id, first_player_id, first_player_score, second_player_id, second_player_score,
                 is_approved=False, server="bancho"):
        super().__init__()
        self.id = match_id
        self.first_player_id = first_player_id
        self.first_player_score = first_player_score
        self.second_player_id = second_player_id
        self.second_player_score = second_player_score
        self.is_approved = is_approved
        self.server = server



class Player(Base):
    __tablename__ = "player"
    osu_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    nickname: Mapped[str] = mapped_column(String(32))
    rating: Mapped[int] = mapped_column(Integer, nullable=True)
    discord_id: Mapped[str] = mapped_column(String(32), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


    left_nodes = relationship("Matches", primaryjoin=osu_id == Matches.first_player_id)
    right_nodes = relationship("Matches", primaryjoin=osu_id == Matches.second_player_id)
    """
    right_nodes = relationship(
        "Player",
        secondary="matches",
        primaryjoin=osu_id == Matches.first_player_id,
        secondaryjoin=osu_id == Matches.second_player_id,
        backref="left_nodes",
    )
    """

    @property
    def matches(self):
        return self.left_nodes + self.right_nodes

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
