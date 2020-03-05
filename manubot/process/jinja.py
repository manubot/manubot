from random import Random


def mb_random(value, seed=None):
    shuffled = list(value)
    Random(seed).shuffle(shuffled)
    return shuffled


MB_FILTERS = {"mb_random": mb_random}
