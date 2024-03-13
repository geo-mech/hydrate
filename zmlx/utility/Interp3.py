import numpy as np
from scipy.interpolate import NearestNDInterpolator, LinearNDInterpolator
from zmlx.alg.join_cols import join_cols


class Interp3:
    def __init__(self, x, y, z, v, rescale=True):
        """
        根据4列数据来构造
        """
        assert len(v) >= 1
        if len(v) == 1:
            self.value = v[0]
            self.f1 = None
            self.f2 = None
            return

        # 创建插值
        points = join_cols(x, y, z)
        values = v

        # 首选的线性插值
        try:
            self.f1 = LinearNDInterpolator(points, values, rescale=rescale, fill_value=np.nan)
        except:
            self.f1 = None

        # 备选
        self.f2 = NearestNDInterpolator(points, values, rescale=rescale)

        # 默认值
        self.value = None

    def __call__(self, x, y, z):
        """
        返回给定点处的数据
        """
        if self.f1 is not None:
            v = self.f1(x, y, z)
            if v is not None:
                return v

        if self.f2 is not None:
            v = self.f2(x, y, z)
            if v is not None:
                return v

        # 最后，返回默认值
        return self.value

