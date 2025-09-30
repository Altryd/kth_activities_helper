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

def dump_to_csv(path_to_csv, data):
    with open(f'{path_to_csv}', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        # write the data
        writer.writerows(data)
    return True