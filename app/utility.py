import requests
import json
import csv

debug = False
from app.models import Player, Matches


def serialize_player_to_json(player):
    matches = player.matches
    matches_dict = [serialize_match_to_json(match) for match in matches]
    final_dict = {'osu_id': player.osu_id, 'nickname': player.nickname, 'rating': player.rating,
                  'discord_id': player.discord_id, 'active': player.active, "matches": matches_dict}
    # TODO: matches
    return final_dict


def serialize_match_to_json(match):
    return {'id': match.id, "first_player_nickname": match.first_player.nickname,
            "first_player_id": match.first_player.osu_id, "first_player_score": match.first_player_score,
            "second_player_nickname": match.second_player.nickname, "second_player_id": match.second_player.osu_id,
            "second_player_score": match.second_player_score, "is_approved": match.is_approved
            }


def get_new_rating(r0, opponents_rating, wins_first, wins_opponent, k=35):
    """

    :param r0: старый рейтинг
    :param opponents_rating: рейтинг оппонента
    :param wins_first: кол-во побед первого игрока
    :param wins_opponent: кол-во побед оппонента
    :param k: коэф.значимости матча, по умолчанию = 20
    :return:
    """
    G = get_g(wins_first, wins_opponent)
    W = 0.5
    if wins_first > wins_opponent:
        W = 1
    elif wins_first < wins_opponent:
        W = 0
    We = get_we(r0, opponents_rating)
    return r0 + k*G*(W-We)


def get_g(wins_first, wins_second):
    difference = wins_first - wins_second
    if abs(difference) <= 1:
        return 1
    elif abs(difference) == 2:
        return 3 / 2
    else:
        return (11 + abs(difference)) / 8


def get_we(rating_first, rating_second):
    dr = rating_first - rating_second
    denominator = 10**(-dr / 400) + 1
    return 1 / denominator


def dump_to_csv(path_to_csv, data):
    with open(f'{path_to_csv}', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        # write the data
        writer.writerows(data)
    return True
