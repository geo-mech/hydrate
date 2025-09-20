"""
进行自动的多维插值的库
"""
try:
    import numpy as np
except ImportError:
    np = None

try:
    from scipy.interpolate import NearestNDInterpolator, LinearNDInterpolator, CloughTocher2DInterpolator
except ImportError:
    NearestNDInterpolator = None
    LinearNDInterpolator = None
    CloughTocher2DInterpolator = None

from zmlx.alg.base import join_cols


class Interp2:
    """
    二维的插值.
        将首先尝试CloughTocher2DInterpolator，之后是线性插值，最后寻找最为接近的点.
    """

    def __init__(self, x, y, v, rescale=True):
        """
        根据3列数据来构造一个2维插值。当不同维度的范围差异比较大的时候，务必将rescale设置为True
        """
        assert len(v) >= 1
        if len(v) == 1:
            # 此时是一个常数，无论如何插值，都是这个数字本身，因此不用插值
            self.value = v[0]
            self.f0 = None
            self.f1 = None
            self.f2 = None
            return

        # 创建插值
        points = join_cols(x, y)
        values = v

        # 这是一个比线性插值更加平滑的方法
        try:
            self.f0 = CloughTocher2DInterpolator(
                points, values, rescale=rescale,
                fill_value=np.nan)
        except:
            self.f0 = None

        # 首选的线性插值
        try:
            self.f1 = LinearNDInterpolator(
                points, values, rescale=rescale,
                fill_value=np.nan)
        except:
            self.f1 = None

        # 备选，当线性插值失败的时候，使用这个
        try:
            self.f2 = NearestNDInterpolator(
                points, values, rescale=rescale)
        except:
            self.f2 = None

        # 默认值 (此时不具备默认值)
        self.value = None

    def __call__(self, x, y):
        """
        返回给定点处的数据。
        """
        if self.f0 is not None:  # 首先，尝试CloughTocher插值
            v = self.f0(x, y)
            if not np.any(np.isnan(v)):  # 当插值失败，会返回np.nan
                return v

        if self.f1 is not None:  # 尝试线性插值
            v = self.f1(x, y)
            if not np.any(np.isnan(v)):  # 当插值失败，会返回np.nan
                return v

        if self.f2 is not None:
            v = self.f2(x, y)
            if not np.any(np.isnan(v)):  # 当插值失败，会返回np.nan
                return v
            else:
                assert False, 'The function f2 (NearestNDInterpolator) should never get nan'

        # 最后，返回默认值.
        assert self.f2 is None

        if self.value is not None:
            return self.value * np.ones_like(x)
        else:
            return np.nan * np.ones_like(x)  # 2025-8-4修改，尚未测试


class Interp3:
    """
    三维的插值.
    将首先尝试线性插值，当线性插值失败的时候，则转而寻找最为接近的点.
    """

    def __init__(self, x, y, z, v, rescale=True):
        """
        根据4列数据来构造一个三维插值。当不同维度的范围差异比较大的时候，务必将rescale设置为True
        """
        x = np.asarray(x)
        y = np.asarray(y)
        z = np.asarray(z)
        v = np.asarray(v)

        assert x.shape == y.shape == z.shape == v.shape, "x, y, z, v must have the same shape"
        ndim = x.ndim
        assert 0 <= ndim <= 1, "x, y, z must be scalar or 1D arrays"

        if v.size == 1 or ndim == 0:
            if ndim == 0:
                self.value = float(v)
            else:  # 1d
                self.value = float(v[0])
            self.f1 = None
            self.f2 = None
            return

        # 创建插值
        points = join_cols(x, y, z)
        values = v

        # 首选的线性插值
        try:
            self.f1 = LinearNDInterpolator(
                points, values, rescale=rescale,
                fill_value=np.nan)
        except:
            self.f1 = None

        # 备选，当线性插值失败的时候，使用这个
        self.f2 = NearestNDInterpolator(
            points, values, rescale=rescale)

        # 默认值 (此时不具备默认值)
        self.value = None

    def __call__(self, x, y, z):
        """
        返回给定点处的数据。
        """
        if self.f1 is not None:  # 首先，尝试线性插值
            v = self.f1(x, y, z)
            if not np.any(np.isnan(v)):  # 当插值失败，会返回np.nan
                return v

        if self.f2 is not None:  # 尝试最接近的点
            v = self.f2(x, y, z)
            if not np.any(np.isnan(v)):  # 当插值失败，会返回np.nan
                return v
            else:
                assert False, 'The function f2 (NearestNDInterpolator) should never get nan'

        # 最后，返回默认值.
        assert self.f2 is None
        if self.value is not None:
            return self.value * np.ones_like(x)
        else:
            return np.nan * np.ones_like(x)  # 2025-8-4修改，尚未测试


def load_field3(filename):
    """
    从文件中加载数据.
    Args:
        filename: 文件名，文件中每一行包含4个数字，分别表示x, y, z, v

    Returns:
        Interp3: 插值对象
    """
    data = np.loadtxt(filename)
    if len(data.shape) == 1:
        # 对于一维数组，直接取前4个元素
        x, y, z, v = data[:4]  # 简洁的解包方式
        return Interp3(x, y, z, v)
    else:
        # 对于二维数组，取前4列
        assert data.shape[1] >= 4, "数据列数不足4列"
        x = data[:, 0]
        y = data[:, 1]
        z = data[:, 2]
        v = data[:, 3]
        return Interp3(x, y, z, v)


def test():
    import random
    x = [0, 0]
    y = [0, 0]
    z = [-1, 1]
    v = [-1, 1]
    f = Interp3(x, y, z, v)
    for idx in range(20):
        x = random.uniform(-2, 2)
        y = random.uniform(-2, 2)
        z = random.uniform(-2, 2)
        v = f(x, y, z)
        print(f'pos: {x}  {y}  {z}, v: {v}')


if __name__ == '__main__':
    test()
