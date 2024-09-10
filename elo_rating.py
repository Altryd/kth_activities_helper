# For testing purposes only. Use utility.py package instead!
def get_new_rating(r0, opponents_rating, wins_first, wins_opponent, k=35):
    """

    :param r0: - старый рейтинг
    :param k:
    :return:
    """
    G = get_g(wins_first, wins_opponent)
    W = 0.5
    if wins_first > wins_opponent:
        W = 1
    elif wins_first < wins_opponent:
        W = 0
    We = get_we(r0, opponents_rating)
    return r0 + k * G * (W - We)


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


if __name__ == "__main__":
    rating_A = 630
    rating_B = 500
    rating_C = 480
    A_wins = 3
    B_wins = 1
    print("team A vs team B")
    print("Situation first: A:3 - B:1")
    rating_A_new = get_new_rating(rating_A, rating_B, A_wins, B_wins)
    print(f"difference for A: {rating_A_new - rating_A}")
    rating_B_new = get_new_rating(rating_B, rating_A, B_wins, A_wins)
    print(f"difference for B: {rating_B_new - rating_B}")

    print("\nSituation second: A:1 - B:3")
    A_wins = 1
    B_wins = 3
    rating_A_new = get_new_rating(rating_A, rating_B, A_wins, B_wins)
    print(f"difference for A: {rating_A_new - rating_A}")
    rating_B_new = get_new_rating(rating_B, rating_A, B_wins, A_wins)
    print(f"difference for B: {rating_B_new - rating_B}")

    print("\nSituation third: A:2 - B:2")
    A_wins = 2
    B_wins = 2
    rating_A_new = get_new_rating(rating_A, rating_B, A_wins, B_wins)
    print(f"difference for A: {rating_A_new - rating_A}")
    rating_B_new = get_new_rating(rating_B, rating_A, B_wins, A_wins)
    print(f"difference for B: {rating_B_new - rating_B}")

    print("\n\nteam B vs team C")
    print("Situation first: B:3 - C:1")
    B_wins = 3
    C_wins = 1
    rating_B_new = get_new_rating(rating_B, rating_C, B_wins, C_wins)
    print(f"difference for B: {rating_B_new - rating_B}")
    rating_C_new = get_new_rating(rating_C, rating_B, C_wins, B_wins)
    print(f"difference for C: {rating_C_new - rating_C}")

    print("\nSituation second: B:1 - C:3")
    B_wins = 1
    C_wins = 3
    rating_B_new = get_new_rating(rating_B, rating_C, B_wins, C_wins)
    print(f"difference for B: {rating_B_new - rating_B}")
    rating_C_new = get_new_rating(rating_C, rating_B, C_wins, B_wins)
    print(f"difference for C: {rating_C_new - rating_C}")

    print("\nSituation third: B:2 - C:2")
    B_wins = 2
    C_wins = 2
    rating_B_new = get_new_rating(rating_B, rating_C, B_wins, C_wins)
    print(f"difference for B: {rating_B_new - rating_B}")
    rating_C_new = get_new_rating(rating_C, rating_B, C_wins, B_wins)
    print(f"difference for C: {rating_C_new - rating_C}")
