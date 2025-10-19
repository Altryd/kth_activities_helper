from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, BigInteger, Enum, CheckConstraint, \
    JSON
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship, mapped_column, Mapped
from datetime import datetime
import enum
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.config import settings


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Role(enum.Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    osu_id = Column(BigInteger, primary_key=True, autoincrement=False)
    discord_id = Column(String(32), unique=True, nullable=True)
    username = Column(String(255), nullable=False)
    pp = Column(Float, default=0.0)
    elo_rating = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    role = Column(Enum(Role), default=Role.user, nullable=False)

    roulette_rolls = Column(Integer, default=0)
    roulette_wins = Column(Integer, default=0)
    roulette_streak_current = Column(Integer, default=0)
    roulette_achievements: Mapped[list[str]] = mapped_column(JSON, default=list)  # ['выбил_63', 'overkill_3_times', ...]

    # Связь с таблицей matches
    matches_as_player1 = relationship("Match", foreign_keys="[Match.player1_id]", back_populates="player1")
    matches_as_player2 = relationship("Match", foreign_keys="[Match.player2_id]", back_populates="player2")
    matches_as_winner = relationship("Match", foreign_keys="[Match.winner_id]", back_populates="winner")

    @property
    def matches(self):
        return sorted(
            self.matches_as_player1 + self.matches_as_player2,
            key=lambda m: m.match_date,
            reverse=True
        )


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        CheckConstraint("player1_id != player2_id", name="check_different_players"),
    )

    match_id = Column(Integer, primary_key=True, autoincrement=True)
    player1_id = Column(BigInteger, ForeignKey("users.osu_id"), nullable=False)
    player2_id = Column(BigInteger, ForeignKey("users.osu_id"), nullable=False)
    player1_score = Column(Integer, default=0)
    player2_score = Column(Integer, default=0)
    winner_id = Column(BigInteger, ForeignKey("users.osu_id"), nullable=True)

    match_date = Column(DateTime, default=datetime.utcnow)

    # Обратные связи с таблицей users
    player1 = relationship("User", foreign_keys=[player1_id], back_populates="matches_as_player1")
    player2 = relationship("User", foreign_keys=[player2_id], back_populates="matches_as_player2")
    winner = relationship("User", foreign_keys=[winner_id], back_populates="matches_as_winner")


async_engine = create_async_engine(settings.async_database_url, echo=True)  # echo=True для отладки SQL-запросов
async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def reset_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with async_session() as session:
        yield session