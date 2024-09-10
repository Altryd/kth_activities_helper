import flask
from flask import render_template, request, redirect, url_for, Blueprint
from flask_login import current_user, login_required

matches_routes = Blueprint('matches', __name__, template_folder='templates', url_prefix="/matches")
from app import engine, app
from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func
from app import Matches, Player
from app.utility import get_new_rating
from osuParseMpLinks.osu_api_usage import get_user_data_by_username_or_id
import csv
from app.config import Config


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


@matches_routes.route("/parse_scrims", methods=['GET'])
def parse_scrims():
    return render_template("parse_scrims.html")


@matches_routes.route("/parse_pair_correction", methods=['GET'])
def parse_pair_correction():
    return render_template("parse_pair_correction.html")


@matches_routes.route("/read_csv", methods=['GET'])
def read_csv():
    with Session(engine) as session:
        matches = []
        missing_players = set()
        with open(r"routes/matches_to_add.csv", encoding='utf-8-sig') as fp:
            reader = csv.reader(fp, delimiter=",", quotechar='"')
            # next(reader, None)  # skip the headers
            matches = [row for row in reader]
        for match in matches:
            match_id = int(match[0])
            match_check = select(Matches).where(Matches.id == match_id)
            match_check = session.execute(match_check).scalars().first()
            if match_check is not None:
                print(f"[SKIP] Match with id {match_id} already exists, skipping")
                continue

            first_player_id = get_user_data_by_username_or_id(secrets=Config.secrets, username=match[1])
            first_player = select(Player).where(Player.osu_id == first_player_id)
            first_player = session.execute(first_player).scalars().first()
            if not first_player:
                missing_players.add(match[1])
                print(match[1])
            first_player_score = int(match[2])

            second_player_id = get_user_data_by_username_or_id(secrets=Config.secrets, username=match[3])
            if match[3] == "SweetDream":
                second_player_id = 9003579
            second_player = select(Player).where(Player.osu_id == second_player_id)
            second_player = session.execute(second_player).scalars().first()
            if not second_player:
                missing_players.add(match[3])
                print(match[3])
            second_player_score = int(match[4])
            server = "bancho"
            if len(match) > 5:
                server = str(match[5])
            new_match = Matches(id=match_id,
                                first_player_id=first_player.osu_id, first_player_score=first_player_score,
                                second_player_id=second_player.osu_id, second_player_score=second_player_score,
                                is_approved=True, server=server)
            session.add(new_match)
        try:
            session.commit()
        except BaseException as ex:
            session.rollback()

    print(f"missing_players: {missing_players}")
    return str(missing_players)

"""
@matches_routes.route("/read_csv", methods=['GET'])
def read_csv():
    with Session(engine) as session:
        matches = []
        missing_players = set()
        with open(r"pairs_to_add_1_jan.csv", encoding='utf-8-sig') as fp:
            reader = csv.reader(fp, delimiter=",", quotechar='"')
            # next(reader, None)  # skip the headers
            matches = [row for row in reader]
        for match in matches:
            first_player = select(Player).where(func.lower(Player.nickname) == match[0].lower())
            first_player = session.execute(first_player).scalars().first()
            if not first_player:
                missing_players.add(match[0])

            second_player = select(Player).where(func.lower(Player.nickname) == match[1].lower())
            second_player = session.execute(second_player).scalars().first()
            if not second_player:
                missing_players.add(match[1])
    print(missing_players)
    return str(missing_players)
"""