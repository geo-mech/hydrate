# ** desc = 'matplotlib绘图示例'

import numpy as np

from zmlx import plot


def on_figure(fig, x, y, z):
    """
    回调函数，在给定的fig上绘图。回调函数的第一个参数，必须是figure对象。
    Args:
        fig: 目标figure对象
        x: x坐标矩阵 (二维的矩阵)
        y: y坐标矩阵 (二维的矩阵)
        z: z坐标矩阵 (二维的矩阵)
    Returns:
        None
    """
    ax = fig.add_subplot()
    obj = ax.contourf(x, y, z)
    fig.colorbar(obj)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_aspect('equal')
    fig.tight_layout()


def test():
    """
    测试contourf函数
    Returns:
        None
    """
    x = np.linspace(-5, 5, 30)
    y = np.linspace(-5, 5, 30)
    x, y = np.meshgrid(x, y)
    z = np.sin(np.sqrt(x ** 2 + y ** 2))

    plot(on_figure, x, y, z, gui_mode=True, caption='绘图示例')


if __name__ == '__main__':
    test()
