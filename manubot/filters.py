from random import Random, shuffle


def mb_random(value, seed=None):
    shuffled = list(value)
    if seed is not None:
        Random(seed).shuffle(shuffled)
    else:
        shuffle(shuffled)
    return shuffled


MB_FILTERS = {
    'mb_random': mb_random
}
