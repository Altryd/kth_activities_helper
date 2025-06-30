from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Boolean, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from app.config import Config


Base = declarative_base()


class Role(enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class Matches(Base):
    __tablename__ = "matches"
    id = Column(BigInteger, unique=True, primary_key=True, autoincrement=False)
    first_player_id = Column(BigInteger, ForeignKey("player.osu_id"), nullable=False)
    first_player_score = Column(Integer, nullable=False)
    first_player = relationship(
        "Player", primaryjoin="(Player.osu_id == Matches.first_player_id)")
    second_player_id = Column(
        BigInteger,
        ForeignKey("player.osu_id"),
        nullable=False)
    second_player_score = Column(Integer, nullable=False)
    second_player = relationship(
        "Player", primaryjoin="(Player.osu_id == Matches.second_player_id)")
    is_approved = Column(Boolean, nullable=False, default=False)
    server = Column(String(32), default="banco", nullable=True)

    def __init__(
            self,
            match_id,
            first_player_id,
            first_player_score,
            second_player_id,
            second_player_score,
            is_approved=False,
            server="bancho"):
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
    osu_id = Column(BigInteger, primary_key=True, autoincrement=True)
    nickname = Column(String(64), nullable=False, unique=True)
    rating = Column(Integer, default=0, nullable=True)
    discord_id = Column(String(32), unique=True, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    # TODO: roles ?

    left_nodes = relationship(
        "Matches", primaryjoin=osu_id == Matches.first_player_id)
    right_nodes = relationship(
        "Matches", primaryjoin=osu_id == Matches.second_player_id)

    @property
    def matches(self):
        return self.left_nodes + self.right_nodes

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
