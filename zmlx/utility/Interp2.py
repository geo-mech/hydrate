import numpy as np
from scipy.interpolate import NearestNDInterpolator, LinearNDInterpolator

from zmlx.alg.join_cols import join_cols


class Interp2:
    """
    二维的插值. 将首先尝试线性插值，当线性插值失败的时候，则转而寻找最为接近的点.
        注意：
            不支持向量化操作；
    """

    def __init__(self, x, y, v, rescale=True):
        """
        根据3列数据来构造一个2维插值。当不同维度的范围差异比较大的时候，务必将rescale设置为True
        """
        assert len(v) >= 1
        if len(v) == 1:
            # 此时是一个常数
            self.value = v[0]
            self.f1 = None
            self.f2 = None
            return

        # 创建插值
        points = join_cols(x, y)
        values = v

        # 首选的线性插值
        try:
            self.f1 = LinearNDInterpolator(points, values, rescale=rescale, fill_value=np.nan)
        except:
            self.f1 = None

        # 备选，当线性插值失败的时候，使用这个
        self.f2 = NearestNDInterpolator(points, values, rescale=rescale)

        # 默认值 (此时不具备默认值)
        self.value = None

    def __call__(self, x, y):
        """
        返回给定点处的数据。
            注意：此函数不支持向量;
        """
        if self.f1 is not None:
            # 首先，尝试线性插值
            v = self.f1(x, y)
            if not np.isnan(v):  # 当插值失败，会返回np.nan
                return v

        if self.f2 is not None:
            v = self.f2(x, y)
            if not np.isnan(v):  # 当插值失败，会返回np.nan
                return v
            else:
                assert False, 'The function f2 (NearestNDInterpolator) should never get nan'

        # 最后，返回默认值.
        assert self.f2 is None
        return self.value


def test():
    import random
    x = [0, 0]
    y = [-1, 1]
    v = [-1, 1]
    f = Interp2(x, y, v)
    for idx in range(20):
        x = random.uniform(-2, 2)
        y = random.uniform(-2, 2)
        v = f(x, y)
        print(f'pos: {x}  {y}, v: {v}')


if __name__ == '__main__':
    test()
