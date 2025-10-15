# ** desc = 'matplotlib绘图示例'

from time import sleep

from zmlx import *


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
    for cx in np.linspace(-5, 5, 30):
        print(f'cx={cx}')
        x = np.linspace(cx - 5, cx + 5, 30)
        y = np.linspace(-5, 5, 30)
        x, y = np.meshgrid(x, y)
        z = np.sin(np.sqrt(x ** 2 + y ** 2))
        plot(on_figure, x, y, z, caption='绘图示例')
        sleep(0.05)


if __name__ == '__main__':
    gui.execute(test, close_after_done=False)
