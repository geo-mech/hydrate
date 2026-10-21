"""曲线数据封装（scipy ``interp1d`` 包装，自变量超出范围时钳制到边界值）.

Modified by Claude, 2026-08-12
"""

import os

from scipy.interpolate import interp1d

from zmlx.algs.base import clamp
from zmlx.exts import is_array, np


class CurveData:
    """曲线数据封装。

    基于 scipy ``interp1d`` 的一维曲线，当自变量超出取值范围时，
    自动钳制到边界值（最近点外推）。
    """

    def __init__(self, *args, **kwargs):
        """初始化曲线数据，参数透传给 ``set_xy``."""
        self.x_min = None
        self.x_max = None
        self.data = None
        self.set_xy(*args, **kwargs)

    def set_xy(self, x=None, y=None, *, dat=None, ix=None, iy=None, fname=None):
        """设置 x 到 y 的映射数据。

        数据来源优先级：直接给定 x/y > 从数据矩阵 dat 中提取列 > 从文件读取。
        若 x 和 y 均未给定且 dat/fname 也为 None，则不做任何操作。

        Args:
            x: 横坐标数组。
            y: 纵坐标数组。
            dat: 数据矩阵（将通过 ``np.loadtxt`` 加载或由调用者传入）。
            ix: ``dat`` 中横坐标的列索引，默认 0。
            iy: ``dat`` 中纵坐标的列索引，默认 1。
            fname: 数据文件路径（经 ``np.loadtxt`` 读取）。
        """
        if x is None or y is None:
            # x和y没有完全给定，因此导入数据.
            if dat is None:
                # 读取文件
                if fname is None:
                    return
                assert os.path.isfile(fname)
                dat = np.loadtxt(fname=fname)
            assert dat is not None
            if ix is None or iy is None:
                ix, iy = 0, 1
            # 读取列
            x = dat[:, ix]
            y = dat[:, iy]
        assert len(x) == len(y)
        self.x_min = np.min(x)
        self.x_max = np.max(x)
        self.data = interp1d(x, y)

    def __call__(self, x):
        """给定 x，返回对应的 y（超出范围时钳制到边界值）。

        Args:
            x: 横坐标（单个值或数组）。

        Returns:
            float | ndarray: 插值结果（标量或数组）。
        """
        if is_array(x):
            return self.data(
                [clamp(item, self.x_min, self.x_max) for item in x])
        else:
            return self.data(clamp(x, self.x_min, self.x_max))


def _test():
    data = CurveData(x=[0, 1, 2], y=[1, 0, 1])
    print(data(0))
    print(data(0.4))
    print(data(np.linspace(0, 6, 9)))
    print(data(-2))


if __name__ == '__main__':
    _test()
