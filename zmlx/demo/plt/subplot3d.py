# ** desc = 'matplotlib绘图示例'
#
# 本案例演示三维子图绘制。在figure中创建两个并排的三维子图：
#   左图：3D曲面图（plot_surface），展示sin(sqrt(x^2+y^2))函数的曲面
#   右图：3D线框（plot_wireframe），使用matplotlib提供的测试数据
# 展示两种常见三维可视化方式：曲面图和线框图，并添加颜色条。

from zmlx import *


def on_figure(fig):
    """
    在figure上绘制两个3D子图

    左侧子图显示三维曲面（彩色映射），右侧子图显示三维线框。
    用于展示同一数据的不同三维可视化风格。

    Args:
        fig: matplotlib.figure.Figure对象
    """
    from matplotlib import cm
    from mpl_toolkits.mplot3d.axes3d import get_test_data

    # =============
    # First subplot: 3D曲面图
    # =============
    # 创建第一个三维坐标轴
    ax = fig.add_subplot(1, 2, 1, projection='3d')

    # 生成网格数据：[-5,5]区间，步长0.25，计算Z = sin(R)
    X = np.arange(-5, 5, 0.25)
    Y = np.arange(-5, 5, 0.25)
    X, Y = np.meshgrid(X, Y)
    R = np.sqrt(X ** 2 + Y ** 2)
    Z = np.sin(R)
    # 绘制三维曲面，使用coolwarm颜色映射
    surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.coolwarm,
                           linewidth=0, antialiased=False)
    ax.set_zlim(-1.01, 1.01)     # 设置z轴范围
    fig.colorbar(surf, shrink=0.5, aspect=10)  # 添加颜色条

    # ==============
    # Second subplot: 3D线框图
    # ==============
    # 创建第二个三维坐标轴
    ax = fig.add_subplot(1, 2, 2, projection='3d')

    # 使用matplotlib内置测试数据绘制线框图
    X, Y, Z = get_test_data(0.05)
    ax.plot_wireframe(X, Y, Z, rstride=10, cstride=10)


if __name__ == '__main__':
    plot(on_figure, gui_mode=True)
