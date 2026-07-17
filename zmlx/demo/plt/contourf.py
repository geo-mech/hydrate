# ** desc = 'matplotlib绘图示例'
#
# 本案例演示使用matplotlib的contourf函数绘制填充等值线图。
# 在二维平面中生成一个正弦波数据（sin(sqrt(x^2+y^2))），通过plot函数
# 封装实现快速绘图。主要展示contourf的基本用法：数据生成、坐标网格
# 创建、填充等值线绘制、颜色条添加和坐标轴设置。

import numpy as np

from zmlx import plot


def on_figure(fig, x, y, z):
    """
    回调函数，在给定的fig上绘图。回调函数的第一个参数，必须是figure对象。

    Args:
        fig: 目标figure对象，matplotlib.figure.Figure
        x: x坐标矩阵（二维网格坐标）
        y: y坐标矩阵（二维网格坐标）
        z: z值矩阵（二维，表示标量场数值）

    Returns:
        None
    """
    # 添加子图并绘制填充等值线
    ax = fig.add_subplot()
    obj = ax.contourf(x, y, z)
    # 添加颜色条
    fig.colorbar(obj)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_aspect('equal')      # 保持纵横比一致
    fig.tight_layout()


def test():
    """
    测试contourf函数

    在[-5,5]x[-5,5]范围内生成30x30的网格，计算函数
    z = sin(sqrt(x^2 + y^2))的值，然后绘制填充等值线图。

    Returns:
        None
    """
    # 生成网格坐标
    x = np.linspace(-5, 5, 30)
    y = np.linspace(-5, 5, 30)
    x, y = np.meshgrid(x, y)
    # 计算标量场：中心向外传播的正弦波
    z = np.sin(np.sqrt(x ** 2 + y ** 2))

    plot(on_figure, x, y, z, gui_mode=True, caption='绘图示例')


if __name__ == '__main__':
    test()
