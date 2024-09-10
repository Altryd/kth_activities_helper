import flask
from flask import render_template, request, redirect, url_for, Blueprint
from flask_login import current_user, login_required

api_routes = Blueprint('api', __name__, template_folder='templates', url_prefix="/api")
from app import engine, app
from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func
from app import Matches, Player
from app.config import Config
from app.utility import get_new_rating, dump_to_csv
from osuParseMpLinks.osu_api_usage import get_user_data_by_username_or_id, parse_scrim
import csv
import json
import requests


@api_routes.route('/check_missing', methods=['GET'])
def get_missing_players():

    with open(r"json_work/players_to_check.csv", encoding='utf-8-sig') as fp:
        reader = csv.reader(fp, delimiter=",", quotechar='"')
        # next(reader, None)  # skip the headers
        results = [row for row in reader]

    # print(results)
    with open("secrets.json", "r") as file:
        secrets = json.loads(file.read())
    with Session(engine) as session:
        missing_counter = 0
        missing_players = []
        for row in results:
            player_id = int(row[0])
            statement = select(Player).filter_by(osu_id=player_id)
            player_obj = session.scalars(statement).all()
            if player_obj is None or len(player_obj) == 0:
                token = requests.post("https://osu.ppy.sh/oauth/token",
                                      data="client_id={}&client_secret={}&grant_type=client_credentials&scope=public"
                                      .format(secrets["client_id"], secrets["client_secret"]),
                                      headers={"Accept": "application/json",
                                               "Content-Type": "application/x-www-form-urlencoded"})  #
                if token.status_code != 200:
                    print(
                        "Программа не смогла обратиться к API osu, проверьте интернет соединение или настройки json файла")
                    exit(-1)
                access_token = token.json()["access_token"]

                user_info_raw = requests.get("https://osu.ppy.sh/api/v2/users/{}/osu".format(player_id),
                                             headers={"Authorization": "Bearer {}".format(access_token)})
                if user_info_raw.status_code != 200:
                    print("Неверный username :( ")
                    exit(-1)

                user_info = user_info_raw.json()
                missing_players.append(f"{player_id},{user_info['username']}")
                missing_counter += 1
        # print(f"Count of missing players: {missing_counter}")
    result = {"missing": missing_players, "count_of_missing": missing_counter}
    return json.dumps(result), 200, {'Content-Type': 'application/json'}


@api_routes.route('/dump_players_to_csv', methods=['GET'])
def dump_players_to_csv():
    string = ""
    with Session(engine) as session:
        players = session.scalars(select(Player)).all()
        players = [player.to_dict().values() for player in players]
        dump_to_csv("dump.csv", players)
    return json.dumps({}), 200, {'Content-Type': 'application/json'}


@api_routes.route('/add_players_to_db', methods=['GET'])
def add_players_to_db():
    with Session(engine) as session:
        results = []
        with open(r"json_work/players_to_add.csv", encoding='utf-8-sig') as fp:
            reader = csv.reader(fp, delimiter=",", quotechar='"')
            # next(reader, None)  # skip the headers
            results = [row for row in reader]
        elements_to_add = []
        for player in results:
            player_id = int(player[0])
            rating = 0
            if len(player) > 3:
                rating = int(player[3])
            active = True
            if len(player) > 4:
                active = int(player[4])
            statement = select(Player).filter_by(osu_id=player_id)
            player_obj = session.scalars(statement).all()
            if player_obj is None or len(player_obj) == 0:
                print(f"ADDING: {player[1]}")
                elem_to_add = Player(osu_id=int(player[0]),
                                     nickname=player[1],
                                     rating=rating,
                                     discord_id=player[2],
                                     active=active)
                elements_to_add.append(elem_to_add)

        session.add_all(elements_to_add)
        # session.add_all(matches_to_add)
        session.commit()
    return json.dumps("<Good!>"), 200, {'Content-Type': 'application/json'}


@api_routes.route('/add_players_from_forms_csv', methods=['GET'])
def add_players_to_db_from_forms_csv():
    with Session(engine) as session:
        results = []
        with open(r"json_work/players_from_form.csv", encoding='utf-8-sig') as fp:  #  id,discordID
            reader = csv.reader(fp, delimiter=",", quotechar='"')
            # next(reader, None)  # skip the headers
            results = [row for row in reader]
        elements_to_add = []
        for player in results:
            player_id = int(player[0])
            rating = 0
            # if len(player) > 2:
            #     rating = int(player[2])
            # active = True
            # if len(player) > 4:
            #     active = int(player[4])
            statement = select(Player).filter_by(osu_id=player_id)
            player_obj = session.scalars(statement).first()
            username = get_user_data_by_username_or_id(Config.secrets, player_id)['username']
            if player_obj is None:
                print(f"ADDING: {username}")
                elem_to_add = Player(osu_id=int(player[0]),
                                     nickname=username,
                                     rating=player[2],
                                     discord_id=player[1],
                                     active=True)
                elements_to_add.append(elem_to_add)
            else:
                print(f"the player with nickname {username} is already in database! refreshing discordId, "
                      f"rating and active")
                player_obj.discord_id = player[1]
                player_obj.rating = player[2]  # TODO: comment later !!
                player_obj.active = True
                # update discordId, set active=1

        session.add_all(elements_to_add)
        # session.add_all(matches_to_add)
        session.commit()
    return json.dumps("<Good!>"), 200, {'Content-Type': 'application/json'}

"""
@api_routes.route('/dump_players_to_csv', methods=['GET'])
def dump_players_to_csv():
    string = ""
    with Session(engine) as session:
        players = session.scalars(select(Player)).all()
        players = [player for player in players]
        for player in players:
            string = string + f",{player.nickname}"
        print(string)
        # dump_to_csv("dump.csv", players)
    return json.dumps({}), 200, {'Content-Type': 'application/json'}




with Session(engine) as session:
    results = []
    with open(r"json_work/players_to_add.csv", encoding='utf-8-sig') as fp:
        reader = csv.reader(fp, delimiter=",", quotechar='"')
        # next(reader, None)  # skip the headers
        results = [row for row in reader]
    elements_to_add = []
    for player in results:
        player_id = int(player[0])
        statement = select(Player).filter_by(osu_id=player_id)
        player_obj = session.scalars(statement).all()
        if player_obj is None or len(player_obj) == 0:
            print(f"ADDING: {player[1]}")
            elem_to_add = Player(osu_id=int(player[0]),
                                 nickname=player[1],
                                 rating=0,
                                 discord_id=player[2],
                                 active=True)
            elements_to_add.append(elem_to_add)

    session.add_all(elements_to_add)
    # session.add_all(matches_to_add)
    session.commit()

ADD PLAYERS
"""