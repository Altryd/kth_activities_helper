import json
from flask import request, Blueprint
from osuParseMpLinks.osu_api_usage import parse_scrim
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session
from app import Matches, Player
from app import engine
from app.config import Config
from app.utility import get_new_rating

match_api = Blueprint(
    'match_api',
    __name__,
    template_folder='templates',
    url_prefix="/api")


@match_api.route("/create_pairs", methods=['GET', 'POST'])
def create_pairs(pairs_correction_list=None):
    """
    Создание 1вс1 пар с учетом предложенного списка, полученного от администратора, а также с учетом временно
    не использующихся игроков. При этом также проверяется, играли ли оппоненты друг против друга ранее.
    :param pairs_correction_list: list of tuples where [0] is first_player_username, [1] is second_player_username
    :return:
    """
    temporary_used_players = []
    if "temporary_used_players" in request.json:
        temporary_used_players = request.json['temporary_used_players']
        temporary_used_players = temporary_used_players.split(',')
    used_players = set(temporary_used_players)
    pairs = []
    with (Session(engine) as session):
        players_query = select(Player).where(
            Player.active.is_(True)).order_by(
            desc(
                Player.rating))
        players = session.execute(players_query).scalars().all()
        pairs_correction_list = []
        if 'pairs_correction' in request.json:
            # print(request.json['pairs_correction'])
            some_list = request.json['pairs_correction'].split('\n')
            corrected_pairs = [pair.split(',') for pair in some_list]
            for pair in corrected_pairs:
                if len(pair) < 2:
                    continue
                first_player = next(
                    (player for player in players if player.nickname.lower() == pair[0].lower()),
                    None)
                if first_player is None:
                    return (json.dumps({"message": f"the player with nickname {pair[0]} is not found"}), 404,
                            {'Content-Type': 'application/json'})
                second_player = next(
                    (player for player in players if player.nickname.lower() == pair[1].lower()),
                    None)
                if second_player is None:
                    return (json.dumps({"message": f"the player with nickname {pair[1]} is not found"}), 404,
                            {'Content-Type': 'application/json'})
                used_players.add(first_player.nickname)
                used_players.add(second_player.nickname)
                pairs.append((first_player, second_player))
        overpowered_players = set()
        SET_OF_ALL_PLAYERS = [player.nickname for player in players]
        SET_OF_ALL_PLAYERS = set(SET_OF_ALL_PLAYERS)
        unused = []
        for player in players:
            if player.nickname in used_players:
                continue
            for player_second in players:
                if player_second.nickname in used_players or player_second.osu_id == player.osu_id:
                    continue
                player_matches = player.matches
                skip = False  # skipping if the two players already played against each other
                for match in player_matches:
                    if player_second.osu_id == match.first_player_id or player_second.osu_id == match.second_player_id:
                        # TODO: add one year gap
                        skip = True
                if skip:
                    continue
                if player.rating - player_second.rating >= 300:
                    overpowered_players.add((player.nickname, player.rating))
                    used_players.add(player.nickname)
                    """
                    print("Cannot find a decent opponent because of rating for: {0},
                    rating {1}".format(player.nickname, player["rating"]))
                    print(
                        f"Невозможно найти подходящего соперника из-за SKILL ISSUE рейтинга для: {player.nickname}, "
                        f"rating {player.rating}")
                    """
                    unused.append(f"Невозможно найти подходящего соперника из-за SKILL ISSUE рейтинга "
                                  f"для: {player.nickname}, rating {player.rating}")

                    break
                pairs.append((player, player_second))
                used_players.add(player.nickname)
                used_players.add(player_second.nickname)
                break
    unused_list = list(SET_OF_ALL_PLAYERS.difference(used_players))
    for unused_player in unused_list:
        players_query = (
            select(Player) .where(
                func.lower(
                    Player.nickname) == unused_player.lower()))

        player = session.execute(players_query).scalars().first()
        """
        print(f"Неиспользованные игроки "
              f"(по другим причинам, скорее всего из-за нехватки еще одного игрока для формирования пары): "
              f"{unused_player}, rating {player.rating}")
        """
        unused.append(
            f"Неиспользованные игроки "
            f"(по другим причинам, скорее всего из-за нехватки еще одного игрока для формирования пары): "
            f"{unused_player}, rating {player.rating}")
    # print("\n")
    # overpowered_players = sorted(overpowered_players, key=lambda player: player[1], reverse=True)
    # print("overpowered players: ", overpowered_players)
    pairs_nickname = []
    paris_raw = []
    for pair in pairs:
        pairs_nickname.append(
            f"{pair[0].nickname} ({pair[0].rating}) vs {pair[1].nickname} ({pair[1].rating})")
        paris_raw.append(f"{pair[0].nickname},{pair[1].nickname}")
        """
        print(
            "{0} ({1}) vs {2} ({3})".format(pair[0].nickname, pair[0].rating, pair[1].nickname,
                                            pair[1].rating))
        """

    # print("\nfor discord:")
    data = []
    pairs_discord = []
    for pair in pairs:
        pairs_discord.append(
            f"<@{pair[0].discord_id}>\tvs\t<@{pair[1].discord_id}>")
        # print("<@{0}>\tvs\t<@{1}>".format(pair[0].discord_id, pair[1].discord_id))
        data.append([pair[0].nickname, pair[1].nickname])

    """
    print("\n\n[DEBUG]")
    print(f"all_players_count: {len(SET_OF_ALL_PLAYERS)}")
    print(f"used_players_count (incl.rating issues): {len(used_players)}")
    print(f"unused players: {SET_OF_ALL_PLAYERS.difference(used_players)}")
    """
    return (json.dumps({"pairs_nickname": pairs_nickname,
                        "pairs_discord": pairs_discord,
                        'unused': unused,
                        'pairs_row': paris_raw}),
            200,
            {'Content-Type': 'application/json'})


@match_api.route('/parse_scrims', methods=['POST'])
def parse_scrims_api():
    """
    Парсинг скрима с учетом "разминочных карт" (warmup) и карт, которые были сыграны после окончания матча (skip last)
    :return:
    """
    data = request.json
    mplinks_splitted_by_n = data['text'].split('\n')
    final_results = []
    to_return = dict()
    for mplink in mplinks_splitted_by_n:
        mplink_split_by_comma = mplink.split(",")
        link_to_mp = mplink_split_by_comma[0]
        warmups = 0
        skip_last = 0
        if len(mplink_split_by_comma) > 1:
            warmups = int(mplink_split_by_comma[1])
        if len(mplink_split_by_comma) > 2:
            skip_last = int(mplink_split_by_comma[2])
        result = json.loads(
            parse_scrim(
                Config.secrets,
                link_to_mp,
                warmups,
                skip_last))
        match_id = link_to_mp.split('/')[-1]  # id of match
        result.append(match_id)
        final_results.append(result)
        to_return["results"] = final_results
    return json.dumps(to_return), 200, {'Content-Type': 'application/json'}


@match_api.route('/match', methods=['POST'])
def add_match():
    """
    Добавляет матч в БД
    :return:
    """
    match_data = request.json
    with Session(engine) as session:
        match_select = select(Matches).where(Matches.id == match_data['id'])
        match = session.execute(match_select).scalars().first()
        if match:
            return json.dumps({'message': "Can not add match: the match with that ID already exists"}), 422, {
                'Content-Type': 'application/json'}
        server = "bancho"
        if 'server' in match_data:
            server = match_data['server']
        try:
            new_match = Matches(
                match_id=match_data['id'],
                first_player_id=match_data['first_player_id'],
                first_player_score=match_data['first_player_score'],
                second_player_id=match_data['second_player_id'],
                second_player_score=match_data['second_player_score'],
                is_approved=match_data['is_approved'],
                server=server)
            session.add(new_match)
            session.commit()
        except BaseException as ex:
            session.rollback()
            return json.dumps({"message": ex}), 500, {
                'Content-Type': 'application/json'}

    return json.dumps([]), 200, {'Content-Type': 'application/json'}


@match_api.route("/approve_match", methods=['POST'])
def approve_match():
    """
    Позволяет администраторам одобрять матчи. При этом происходит перерасчет эло рейтинга !
    :return:
    """
    data = request.json
    if 'id' not in data:
        return json.dumps({'message': "Can not approve match: id is missing from query"}), 422, {
            'Content-Type': 'application/json'}
    needed_id = data['id']
    with Session(engine) as session:
        match_select = select(Matches).where(Matches.id == needed_id)
        match = session.execute(match_select).scalars().first()
        if not match:
            return json.dumps({'message': "Can not approve match: match with id is not found"}), 404, {
                'Content-Type': 'application/json'}
        first_player = match.first_player
        second_player = match.second_player
        first_player_new_rating = get_new_rating(
            first_player.rating,
            second_player.rating,
            match.first_player_score,
            match.second_player_score)
        second_player_new_rating = get_new_rating(
            second_player.rating,
            first_player.rating,
            match.second_player_score,
            match.first_player_score)
        first_player.rating = first_player_new_rating
        second_player.rating = second_player_new_rating
        match.is_approved = True
        session.commit()
    return json.dumps([]), 200, {'Content-Type': 'application/json'}
