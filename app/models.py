from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Boolean, BigInteger, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from app.config import Config


Base = declarative_base()


class Role(enum.Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"


class Matches(Base):
    __tablename__ = "matches"
    __table_args__ = (
        Index("idx_first_player_id", "first_player_id"),
        Index("idx_second_player_id", "second_player_id"),
    )
    id = Column(BigInteger, unique=True, primary_key=True, autoincrement=False)
    first_player_id = Column(BigInteger, ForeignKey("players.osu_id"), nullable=False)
    first_player_score = Column(Integer, nullable=False)
    first_player = relationship("Player", foreign_keys=[first_player_id])
    # first_player = relationship("Player", primaryjoin="(Player.osu_id == Matches.first_player_id)")
    second_player_id = Column(
        BigInteger,
        ForeignKey("players.osu_id"),
        nullable=False)
    second_player_score = Column(Integer, nullable=False)
    # second_player = relationship("Player", primaryjoin="(Player.osu_id == Matches.second_player_id)")
    second_player = relationship("Player", foreign_keys=[second_player_id])
    is_approved = Column(Boolean, nullable=False, default=False)
    server = Column(String(32), default="bancho", nullable=False)

    def __init__(
            self,
            match_id,
            first_player_id,
            first_player_score,
            second_player_id,
            second_player_score,
            is_approved=False,
            server="bancho"):
        if first_player_id == second_player_id:
            raise ValueError("First and second player IDs must be different")
        super().__init__()
        self.id = match_id
        self.first_player_id = first_player_id
        self.first_player_score = first_player_score
        self.second_player_id = second_player_id
        self.second_player_score = second_player_score
        self.is_approved = is_approved
        self.server = server


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (Index("idx_nickname", "nickname"),)
    osu_id = Column(BigInteger, primary_key=True, autoincrement=False)
    nickname = Column(String(64), nullable=False, unique=True)
    rating = Column(Integer, default=0, nullable=True)
    discord_id = Column(String(32), unique=True, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    role = Column(Enum(Role), default=Role.user, nullable=False)

    #left_nodes = relationship("Matches", primaryjoin=osu_id == Matches.first_player_id)
    left_nodes = relationship("Matches", foreign_keys=[Matches.first_player_id])
    #right_nodes = relationship("Matches", primaryjoin=osu_id == Matches.second_player_id)
    right_nodes = relationship("Matches", foreign_keys=[Matches.second_player_id])

    @property
    def matches(self):
        return self.left_nodes + self.right_nodes

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
