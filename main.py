# uvicorn app.main:app --host localhost --port 8000 --reload
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
import os
from typing import Optional, List
from sqlalchemy.orm import Session, aliased
from sqlalchemy import and_, select
from fastapi.middleware.cors import CORSMiddleware
from app import models, database
from app.config import Config
from app.dto import UpdatedMatch
from app.models import Player, Matches, Base
from dotenv import load_dotenv
from app.database import engine, get_db
from contextlib import asynccontextmanager
from app.logging_config import get_logger
from app.utility import get_new_rating

Base.metadata.create_all(bind=engine)
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")
    yield
    logger.info("Shutting down application")

app = FastAPI(title="osu! AI Agent", lifespan=lifespan)
# app.mount("/frontend", StaticFiles(directory="frontend"),
# name="frontend") TODO
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = get_logger(__name__)


@app.post("add_players_from_forms_csv")
async def add_players_to_db(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        logger.info("Starting bulk player import")
    except Exception as e:
        logger.error(f"Error in add_players_to_db: {e}")
        raise HTTPException(status_code=500, detail=f"Error in add_players_to_db: {str(e)}")


@app.get("/show_matches", response_model=List[UpdatedMatch])
def show_matches(db: Session = Depends(get_db)):
    try:
        playeralias = aliased(Player)
        stmt = (
            select(
                Matches,
                Player.nickname.label("first_nickname"),
                Player.rating.label("first_rating"),
                playeralias.nickname.label("second_nickname"),
                playeralias.rating.label("second_rating"),
            )
            .join(Player, Player.osu_id == Matches.first_player_id)
            .join(playeralias, playeralias.osu_id == Matches.second_player_id)
            .order_by(Matches.is_approved)
            #.offset(skip)
            #.limit(limit)
        )
        result = db.execute(stmt)
        matches = []
        for row in result:
            match = row[0]
            match_dict = {
                "id": match.id,
                "first_player_id": match.first_player_id,
                "first_player_score": match.first_player_score,
                "first_nickname": row.first_nickname,
                "first_rating": row.first_rating,
                "first_rating_new": round(
                    get_new_rating(
                        row.first_rating or 0,
                        row.second_rating or 0,
                        match.first_player_score,
                        match.second_player_score,
                    ),
                    1,
                ),
                "second_player_id": match.second_player_id,
                "second_player_score": match.second_player_score,
                "second_nickname": row.second_nickname,
                "second_rating": row.second_rating,
                "second_rating_new": round(
                    get_new_rating(
                        row.second_rating or 0,
                        row.first_rating or 0,
                        match.second_player_score,
                        match.first_player_score,
                    ),
                    1,
                ),
                "is_approved": match.is_approved,
                "server": match.server,
            }
            matches.append(UpdatedMatch(**match_dict))

        if not matches:
            raise HTTPException(status_code=404, detail="No matches found")
        return matches
    except Exception as e:
        logger.error(f"Error in show matches: {e}")
        raise HTTPException(status_code=500, detail=f"Error in show matches: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
