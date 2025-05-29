import time

import zmlx.alg.sys as warnings
from zmlx.alg.sys import timing_show

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)


def test():
    timing_show('test1', time.sleep, 1)
    timing_show('test2', time.sleep, 2)


if __name__ == '__main__':
    test()
