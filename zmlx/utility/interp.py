"""多维散点数据插值。

2D：依序尝试 CloughTocher → 线性 → 最近点，均失败时返回常数或 NaN。
3D：依序尝试线性 → 最近点，均失败时返回常数或 NaN。

Modified by Claude, 2026-08-12
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
    """二维插值。

    依序尝试 CloughTocher2DInterpolator → LinearNDInterpolator →
    NearestNDInterpolator。当三种方法都失败时，若有常量值则返回常量，
    否则返回 NaN。
    """

    def __init__(self, x, y, v, rescale=True):
        """根据散点数据构造二维插值。

        ``len(v) == 1`` 时直接作为常量，不创建插值器。

        Args:
            x: x 坐标数组。
            y: y 坐标数组。
            v: 数值数组。
            rescale: 是否按各维度范围缩放（维度范围差异大时建议 True）。
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
        except Exception:
            self.f0 = None

        # 首选的线性插值
        try:
            self.f1 = LinearNDInterpolator(
                points, values, rescale=rescale,
                fill_value=np.nan)
        except Exception:
            self.f1 = None

        # 备选，当线性插值失败的时候，使用这个
        try:
            self.f2 = NearestNDInterpolator(
                points, values, rescale=rescale)
        except Exception:
            self.f2 = None

        # 默认值 (此时不具备默认值)
        self.value = None

    def __call__(self, x, y):
        """返回给定点处的插值结果。

        依序尝试 f0 → f1 → f2，成功则立即返回；
        均失败时若有常量值则返回常量数组，否则返回 NaN 数组。

        Args:
            x: x 坐标（标量或数组）。
            y: y 坐标（标量或数组）。

        Returns:
            ndarray: 插值结果。
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
    """三维插值。

    依序尝试 LinearNDInterpolator → NearestNDInterpolator。
    当两种方法都失败时，若有常量值则返回常量，否则返回 NaN。
    """

    def __init__(self, x, y, z, v, rescale=True):
        """根据散点数据构造三维插值。

        输入为标量或长度为 1 的数组时直接作为常量，不创建插值器。

        Args:
            x: x 坐标数组。
            y: y 坐标数组。
            z: z 坐标数组。
            v: 数值数组（形状与 x, y, z 相同）。
            rescale: 是否按各维度范围缩放（维度范围差异大时建议 True）。
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
        except Exception:
            self.f1 = None

        # 备选，当线性插值失败的时候，使用这个
        self.f2 = NearestNDInterpolator(
            points, values, rescale=rescale)

        # 默认值 (此时不具备默认值)
        self.value = None

    def __call__(self, x, y, z):
        """返回给定点处的插值结果。

        依序尝试 f1 → f2，成功则立即返回；
        均失败时若有常量值则返回常量数组，否则返回 NaN 数组。

        Args:
            x: x 坐标（标量或数组）。
            y: y 坐标（标量或数组）。
            z: z 坐标（标量或数组）。

        Returns:
            ndarray: 插值结果。
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
