import json
from flask import Blueprint
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import Player
from app import engine
from app.utility import serialize_player_to_json

player_api = Blueprint(
    'player_api',
    __name__,
    template_folder='templates',
    url_prefix="/api")


@player_api.route("/player/<int:player_id>", methods=['GET'])
def get_player(player_id):
    """
    GET на player + с учетом матчей, чтобы потом можно было +-как-то отобразить это на фронтенде
    :param player_id:
    :return:
    """
    with Session(engine) as session:
        player_select = select(Player).where(Player.osu_id == player_id)
        player = session.execute(player_select).scalars().first()
        if player is None:
            return json.dumps({'message': "The player is not found !"}), 404, {
                'Content-Type': 'application/json'}
        return json.dumps(player, default=serialize_player_to_json), 200, {
            'Content-Type': 'application/json'}
