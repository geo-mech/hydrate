from zml import Interp1
import numpy as np


def create_krf():
    """
    裂缝导流系数随着厚度的变化的趋势.
    """
    x = np.linspace(0.0, 100.0, 1000)
    y = x ** 2
    return Interp1(x=x, y=y)
