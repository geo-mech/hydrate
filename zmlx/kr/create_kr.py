from zmlx.kr.pre_defines import create_kr

__all__ = ['create_kr']

import warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)


def _test1():
    # create_kr(srg=0.01, srw=0.4, ag=3.5, aw=4.5)
    vs, kg, kw = create_kr(srg=0.01, srw=0.4, ag=3.5, aw=4.5, count=1000)
    for i in range(len(vs)):
        print(vs[i], kg[i], kw[len(vs) - 1 - i])

    import numpy as np
    from zmlx.ui import plot

    def f(fig):
        ax = fig.subplots()
        ax.plot(vs, kg)
        ax.plot(1 - np.asarray(vs), kw)

    plot(f)


if __name__ == '__main__':
    _test1()
