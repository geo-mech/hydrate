"""获取颜色值工具。

Modified by Claude, 2026-08-12
"""
from zmlx.alg.base import clamp


def get_color(cmap, lr, rr, val):
    """
    对于给定的colormap，数值的范围和给定的数值，返回给定的数值所对应的颜色
    """
    return cmap.mapToFloat(clamp((val - lr) / (rr - lr), 0, 1))
