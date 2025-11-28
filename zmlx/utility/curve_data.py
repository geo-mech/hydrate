import os

from scipy.interpolate import interp1d

from zmlx.alg.base import clamp
from zmlx.base.zml import is_array, np


class CurveData:
    """
    定义曲线数据. 当自变量超过这个曲线的范围时，采用最为接近的数值.
    """

    def __init__(self, *args, **kwargs):
        """
        初始化
        """
        self.x_min = None
        self.x_max = None
        self.data = None
        self.set_xy(*args, **kwargs)

    def set_xy(self, x=None, y=None, *, dat=None, ix=None, iy=None, fname=None):
        """
        设置x到y的映射数据.
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
        """
        给定x，返回对应的y (一个浮点数或者一个list)
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
