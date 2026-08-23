"""空间标量场，包含常数场、线性场和均匀分布场，用于辅助建模.

Modified by Claude, 2026-08-12
"""

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
    """线性温度场或压力场。

    场值公式：``v(x,y,z) = v0 + (x-x0)*dx + (y-y0)*dy + (z-z0)*dz``。
    """

    def __init__(self, x0=0, y0=0, z0=0, v0=0, dx=0, dy=0, dz=0):
        """构造线性场。

        Args:
            x0: 基准点 x 坐标 [m]。
            y0: 基准点 y 坐标 [m]。
            z0: 基准点 z 坐标 [m]。
            v0: 基准点场值。
            dx: x 方向梯度。
            dy: y 方向梯度。
            dz: z 方向梯度。
        """
        self.x0 = x0
        self.y0 = y0
        self.z0 = z0
        self.v0 = v0
        self.dx = dx
        self.dy = dy
        self.dz = dz

    def __call__(self, x, y, z):
        """返回给定坐标处的场值。

        Args:
            x: x 坐标 [m]。
            y: y 坐标 [m]。
            z: z 坐标 [m]。

        Returns:
            float: 场值。
        """
        return self.v0 + (x - self.x0) * self.dx + (y - self.y0) * self.dy + (
                z - self.z0) * self.dz


class Field:
    """三维标量场封装。

    将任意位置映射到场值：``value = f(pos)``。
    当传入值不可调用时（如常数），自动包装为 ``Field.Constant``。
    """

    class Constant:
        """常数场（所有位置返回相同值）。"""

        def __init__(self, value):
            """构造常数场。

            Args:
                value: 常数值。
            """
            self.__value = value

        def __call__(self, *args, **kwargs):
            """返回常数值（忽略位置参数）。

            Returns:
                任意: 常数场值。
            """
            return self.__value

    def __init__(self, value):
        """构造场对象。

        Args:
            value: 可调用对象（接收坐标参数）或常数值；
                   不可调用时自动包装为 ``Field.Constant``。
        """
        if callable(value):
            self.__field = value
        else:
            self.__field = Field.Constant(value)

    def __call__(self, *args, **kwargs):
        """返回给定位置处的场值。

        Args:
            *args: 坐标参数。
            **kwargs: 坐标关键词参数。

        Returns:
            任意: 场值。
        """
        return self.__field(*args, **kwargs)


class UniformProfile:
    """均匀分布曲线，利用文件缓存生成的随机数据。

    若缓存文件存在则直接加载，否则随机生成并保存。
    """

    def __init__(self, fname, *, xlim=None, ylim=None, count=100):
        """构造均匀分布曲线。

        若 ``fname`` 文件已存在，从文件加载 (x, y) 数据；
        否则在 ``xlim`` × ``ylim`` 范围内随机生成 ``count`` 个点并保存。

        Args:
            fname: 缓存文件路径。
            xlim: x 范围 (x_min, x_max)，默认 (0, 1)。
            ylim: y 范围 (y_min, y_max)，默认 (0, 1)。
            count: 生成的点数（仅文件不存在时使用）。
        """
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
        """返回给定 x 处的插值结果。

        Args:
            x: 横坐标（标量或数组）。

        Returns:
            ndarray: 插值结果。
        """
        return self.data(x)


def _test():
    from zmlx.exts import app_data
    f = UniformProfile(
        xlim=[0, 10], ylim=[2, 3],
        fname=app_data.temp('uniform_profile.txt'))
    x = np.linspace(1, 3, 5)
    y = f(x)
    print(f'x = {x}')
    print(f'y = {y}')


if __name__ == '__main__':
    _test()
