import numpy as np


def get_data(jx=30, jy=20, xr=None, yr=None):
    """
    创建用于测试的表面数据
    Returns:
        x: 网格坐标X
        y: 网格坐标Y
        z: 网格坐标Z
        v: 颜色数据
    """
    if xr is None:
        xr = (-5, 5)
    if yr is None:
        yr = (-5, 5)
    # 创建示例数据（20 x 30网格）
    x = np.linspace(xr[0], xr[1], jx)
    y = np.linspace(yr[0], yr[1], jy)
    x, y = np.meshgrid(x, y)  # 生成网格坐标

    # 计算Z坐标（示例函数）
    z = np.sin(np.sqrt(x ** 2 + y ** 2))

    # 创建颜色数据V（独立于Z的另一个函数）
    v = np.cos(0.5 * x) * np.sin(0.5 * y)

    return x, y, z, v
