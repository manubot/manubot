from random import Random, shuffle
from jinja2 import evalcontextfilter


@evalcontextfilter
def mb_random(eval_ctx, value, seed=None):
    shuffled = list(value)
    if seed is not None:
        Random(seed).shuffle(shuffled)
    else:
        shuffle(shuffled)
    return shuffled
