import os
import numpy as np
from zmlx.alg.join_cols import join_cols
from scipy.interpolate import interp1d


class UniformProfile:
    """
    生成一个均匀的分布，并且利用文件来缓存数据
    """
    def __init__(self, fname='uniform_profile.txt', xlim=None, ylim=None, count=100):
        if os.path.isfile(fname):
            dat = np.loadtxt(fname)
            x, y = dat[:, 0], dat[:, 1]
        else:
            if xlim is None:
                x0, x1 = 0, 1
            else:
                x0, x1 = xlim
            if ylim is None:
                y0, y1 = 0, 1
            else:
                y0, y1 = ylim
            x = np.linspace(x0, x1, count)
            y = np.random.uniform(low=y0, high=y1, size=x.size)
            np.savetxt(fname, join_cols(x, y))
        self.x0 = np.min(x)
        self.x1 = np.max(x)
        self.data = interp1d(x, y)

    def __call__(self, x):
        return self.data(x)


def _test():
    f = UniformProfile(xlim=[0, 10], ylim=[2, 3])
    x = np.linspace(1, 3, 5)
    y = f(x)
    print(f'x = {x}')
    print(f'y = {y}')


if __name__ == '__main__':
    _test()

