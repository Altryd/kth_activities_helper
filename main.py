# uvicorn app.main:app --host localhost --port 8000 --reload
import redis
from fastapi import FastAPI, HTTPException, Depends
import os
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi.middleware.cors import CORSMiddleware
from app import models, database
from app.config import Config
from app.dto import UpdatedMatch
from app.models import UserGet
from app.database import User
from dotenv import load_dotenv
from app.database import engine, get_db
from contextlib import asynccontextmanager
from app.logging_config import get_logger

database.Base.metadata.create_all(bind=engine)

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

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

@matches_routes.route("/show_matches", methods=['GET'])
def show_matches():
    with Session(engine) as session:
        playeralias = aliased(Player)
        stmt = select(Matches, Player.nickname, Player.rating, playeralias.nickname, playeralias.rating)\
            .join(Player, Player.osu_id == Matches.first_player_id)\
            .join(playeralias, playeralias.osu_id == Matches.second_player_id).order_by(Matches.is_approved)

        result = session.execute(stmt)
        matches = []
        for row in result:
            # print(row)
            match_dict = row[0].__dict__
            match_dict["first_nickname"] = row[1]
            match_dict["first_rating"] = row[2]
            match_dict["first_rating_new"] = get_new_rating(row[2], row[4], row[0].first_player_score,
                                                            row[0].second_player_score)
            match_dict["first_rating_new"] = round(match_dict["first_rating_new"], 1)
            match_dict["second_nickname"] = row[3]
            match_dict["second_rating"] = row[4]
            match_dict["second_rating_new"] = get_new_rating(row[4], row[2], row[0].second_player_score,
                                                            row[0].first_player_score)
            match_dict["second_rating_new"] = round(match_dict["second_rating_new"], 1)
            matches.append(match_dict)

        return render_template("matches.html", matches=matches)


@app.get("/show_matches")
def show_matches(db: Session = Depends(get_db), response_model=List[UpdatedMatch]):
    playeralias = aliased(Player)
    stmt = select(Matches, Player.nickname, Player.rating, playeralias.nickname, playeralias.rating) \
        .join(Player, Player.osu_id == Matches.first_player_id) \
        .join(playeralias, playeralias.osu_id == Matches.second_player_id).order_by(Matches.is_approved)  # ???
    matches = []
    for row in result:
        match_dict = row[0].__dict__
        # ...
        matches.append(match_dict)
    return matches


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)