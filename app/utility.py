import csv

debug = False


def serialize_player_to_json(player):
    matches = player.matches
    matches_dict = [serialize_match_to_json(match) for match in matches]
    final_dict = {
        'osu_id': player.osu_id,
        'nickname': player.nickname,
        'rating': player.rating,
        'discord_id': player.discord_id,
        'active': player.active,
        "matches": matches_dict}
    # TODO: matches
    return final_dict


def serialize_match_to_json(match):
    return {
        'id': match.id,
        "first_player_nickname": match.first_player.nickname,
        "first_player_id": match.first_player.osu_id,
        "first_player_score": match.first_player_score,
        "second_player_nickname": match.second_player.nickname,
        "second_player_id": match.second_player.osu_id,
        "second_player_score": match.second_player_score,
        "is_approved": match.is_approved}


def get_new_rating(initial_rating, opponent_rating, player_wins, opponent_wins, k=35):
    """

    :param initial_rating: старый рейтинг
    :param opponent_rating: рейтинг оппонента
    :param player_wins: кол-во побед первого игрока
    :param opponent_wins: кол-во побед оппонента
    :param k: коэф.значимости матча, по умолчанию = 35
    :return: Новый рейтинг игрока после матча
    """
    match_weight = get_g(player_wins, opponent_wins)
    result = 0.5
    if player_wins > opponent_wins:
        result = 1
    elif player_wins < opponent_wins:
        result = 0
    expected_result = get_we(initial_rating, opponent_rating)
    return initial_rating + k * match_weight * (result - expected_result)


def get_g(player_wins, opponent_wins):
    if player_wins < 0 or opponent_wins < 0:
        raise ValueError("Number of wins cannot be negative")
    difference = player_wins - opponent_wins
    if abs(difference) <= 1:
        return 1
    elif abs(difference) == 2:
        return 3 / 2
    else:
        return (11 + abs(difference)) / 8


def get_we(player_rating, opponent_rating):
    dr = player_rating - opponent_rating
    denominator = 10**(-dr / 400) + 1
    return 1 / denominator


def dump_to_csv(path_to_csv, data):
    with open(f'{path_to_csv}', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        # write the data
        writer.writerows(data)
    return True
