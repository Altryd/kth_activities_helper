import pytest
from app.utility import get_new_rating


@pytest.mark.parametrize("test_input", [
    {"rating_A": 630, "rating_B": 500, "A_wins": 3, "B_wins": 1, "diff": 16.8, "k": 35},
    {"rating_A": 630, "rating_B": 500, "A_wins": 1, "B_wins": 3, "diff": -35.6, "k": 35},
    {"rating_A": 630, "rating_B": 500, "A_wins": 2, "B_wins": 2, "diff": -6, "k": 35},
    {"rating_A": 500, "rating_B": 480, "A_wins": 3, "B_wins": 1, "diff": 24.7, "k": 35},
    {"rating_A": 500, "rating_B": 480, "A_wins": 1, "B_wins": 3, "diff": -27.75, "k": 35},
    {"rating_A": 500, "rating_B": 480, "A_wins": 2, "B_wins": 2, "diff": -1, "k": 35},
    # wikipedia
    {"rating_A": 630, "rating_B": 500, "A_wins": 3, "B_wins": 1, "diff": 9.6, "k": 20},
    {"rating_A": 630, "rating_B": 500, "A_wins": 1, "B_wins": 3, "diff": -20.3, "k": 20},
    {"rating_A": 630, "rating_B": 500, "A_wins": 2, "B_wins": 2, "diff": -3.5, "k": 20},
    {"rating_A": 500, "rating_B": 480, "A_wins": 3, "B_wins": 1, "diff": 14.13, "k": 20},
    {"rating_A": 500, "rating_B": 480, "A_wins": 1, "B_wins": 3, "diff": -15.8, "k": 20},
    {"rating_A": 500, "rating_B": 480, "A_wins": 2, "B_wins": 2, "diff": -0.58, "k": 20},
    # edge cases
    {"rating_A": 1000, "rating_B": 100, "A_wins": 10, "B_wins": 0, "diff": 0.5, "k": 35},
    {"rating_A": 500, "rating_B": 500, "A_wins": 0, "B_wins": 0, "diff": 0, "k": 35},
])
def test_elo_rating(test_input):
    rating_A = test_input["rating_A"]
    rating_B = test_input["rating_B"]
    A_wins = test_input["A_wins"]
    B_wins = test_input["B_wins"]
    k = test_input["k"]
    print(f"\nteam A ({rating_A}) vs team B ({rating_B})")
    print(f"Situation first: A:{A_wins} - B:{B_wins}")
    rating_A_new = get_new_rating(rating_A, rating_B, A_wins, B_wins, k=k)
    diff_A = rating_A_new - rating_A
    print(f"difference for A: {diff_A}")
    rating_B_new = get_new_rating(rating_B, rating_A, B_wins, A_wins, k=k)
    diff_B = rating_B_new - rating_B
    print(f"difference for B: {rating_B_new - rating_B}")

    assert abs(diff_A) == pytest.approx(abs(diff_B), abs=0.3)
    assert diff_A == pytest.approx(test_input["diff"], abs=0.3)
    if test_input["diff"] > 0:
        assert diff_A > 0
    elif test_input["diff"] < 0:
        assert diff_A < 0
    else:
        assert diff_A == pytest.approx(0, abs=0.3)


@pytest.mark.parametrize("test_input", [
    {"rating_A": 630, "rating_B": 500, "A_wins": -2, "B_wins": -5},
    {"rating_A": 630, "rating_B": 500, "A_wins": 1, "B_wins": -5},
    {"rating_A": 630, "rating_B": 500, "A_wins": -500, "B_wins": 0},
])
def test_elo_rises(test_input):
    with pytest.raises(ValueError):
        get_new_rating(test_input["rating_A"], test_input["rating_B"], test_input["A_wins"], test_input["B_wins"])
