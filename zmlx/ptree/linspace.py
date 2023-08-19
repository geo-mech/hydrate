import numpy as np
from zmlx.ptree.ptree import PTree


def linspace(pt, start=0.0, stop=0.0, num=50, endpoint=True):
    """
    Return evenly spaced numbers over a specified interval.
    """
    assert isinstance(pt, PTree)

    num = pt(key='num', default=num,
             doc='Number of samples to generate')

    if num <= 0:
        return np.array([])

    start = pt(key='start', default=start,
               doc='The starting value of the sequence')

    stop = pt(key='stop', default=stop,
              doc='The end value of the sequence')

    endpoint = pt(key='endpoint', default=endpoint,
                  doc='If True, `stop` is the last sample. Otherwise, it is not included')

    return np.linspace(start=start, stop=stop, num=num, endpoint=endpoint)

