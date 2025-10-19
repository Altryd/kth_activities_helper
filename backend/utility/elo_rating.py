def get_new_rating(initial_rating, opponent_rating,
                   player_wins, opponent_wins, k=35):
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
