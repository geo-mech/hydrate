import os

try:
    import numpy as np
except ImportError:
    np = None

try:
    from scipy.interpolate import interp1d
except ImportError as e:
    interp1d = None

from zmlx.alg.base import join_cols


class LinearField:
    """
    线性的温度场或者压力场。用于辅助建模;
    """

    def __init__(self, x0=0, y0=0, z0=0, v0=0, dx=0, dy=0, dz=0):
        self.x0 = x0
        self.y0 = y0
        self.z0 = z0
        self.v0 = v0
        self.dx = dx
        self.dy = dy
        self.dz = dz

    def __call__(self, x, y, z):
        return self.v0 + (x - self.x0) * self.dx + (y - self.y0) * self.dy + (
                z - self.z0) * self.dz


class Field:
    """
    Define a three-dimensional field. Make value = f(pos) return data at any position.
    where pos is the coordinate and f is an instance of Field
    """

    class Constant:
        """
        A constant field
        """

        def __init__(self, value):
            """
            construct with the constant value
            """
            self.__value = value

        def __call__(self, *args, **kwargs):
            """
            return the value when call
            """
            return self.__value

    def __init__(self, value):
        """
        create the field. treat it as a constant field when it is not a function(__call__ not defined)
        """
        if callable(value):
            self.__field = value
        else:
            self.__field = Field.Constant(value)

    def __call__(self, *args, **kwargs):
        return self.__field(*args, **kwargs)


class UniformProfile:
    """
    生成一个均匀的分布，并且利用文件来缓存数据
    """

    def __init__(self, fname, *, xlim=None, ylim=None, count=100):
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
    from zml import app_data
    f = UniformProfile(xlim=[0, 10], ylim=[2, 3],
                       fname=app_data.temp('uniform_profile.txt'))
    x = np.linspace(1, 3, 5)
    y = f(x)
    print(f'x = {x}')
    print(f'y = {y}')


if __name__ == '__main__':
    _test()
