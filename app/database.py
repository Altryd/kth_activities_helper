from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import Config

engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI, echo=Config.DEBUG,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
