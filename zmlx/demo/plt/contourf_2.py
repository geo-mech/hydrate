# ** desc = 'matplotlib绘图示例'
#
# 本案例演示contourf的动态绘图效果。与contourf.py相比，本案例让数据
# 中心点沿x轴移动（从-5到5），形成动画效果。每次绘制前更新数据并短暂
# 休眠（0.05s），实现连续刷新。展示了plot函数在动态可视化中的应用。

from time import sleep

from zmlx import *


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
    fig.colorbar(obj)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_aspect('equal')    # 保持x和y轴比例一致
    fig.tight_layout()


def test():
    """
    测试contourf函数（动态版本）

    将数据中心cx从-5到5循环移动（共30步），每一步重新生成数据并绘图，
    模拟动画效果。z值始终为sin(sqrt(x^2+y^2))，但x坐标范围跟随cx移动。

    Returns:
        None
    """
    # 循环移动数据中心，产生动态效果
    for cx in np.linspace(-5, 5, 30):
        print(f'cx={cx}')
        # 以cx为中心生成x坐标，y坐标固定在[-5,5]
        x = np.linspace(cx - 5, cx + 5, 30)
        y = np.linspace(-5, 5, 30)
        x, y = np.meshgrid(x, y)
        # 计算标量场：中心向外传播的正弦波
        z = np.sin(np.sqrt(x ** 2 + y ** 2))
        plot(on_figure, x, y, z, caption='绘图示例')
        sleep(0.05)   # 短暂休眠以控制动画速度


if __name__ == '__main__':
    gui.execute(test, close_after_done=False)
