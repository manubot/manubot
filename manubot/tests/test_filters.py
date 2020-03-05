def test_mb_random_order():
    from manubot.filters import mb_random
    start = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    shuffled = mb_random(start, seed=5)

    assert start != shuffled
    assert start == sorted(shuffled)


def test_mb_random_same_seed():
    from manubot.filters import mb_random
    start = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    shuffled1 = mb_random(start, seed=5)
    shuffled2 = mb_random(start, seed=5)

    assert shuffled1 == shuffled2


def test_mb_random_start_unchanged():
    from manubot.filters import mb_random
    start = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    mb_random(start, seed=5)

    assert start == start


def test_mb_random_diff_seeds():
    from manubot.filters import mb_random
    start = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    shuffled1 = mb_random(start, seed=5)
    shuffled2 = mb_random(start, seed=6)

    assert shuffled1 != shuffled2
