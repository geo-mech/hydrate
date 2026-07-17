# ** desc = 'matplotlib绘图示例'
#
# 本案例演示在三维坐标系中绘制等值线填充图（contourf）的方法。
# 在三维盒体的三个正交面上分别投影填充等值线：
#   - XY底面（z=0）
#   - XZ左侧面（y=0）
#   - YZ右侧面（x=max）
# 同时绘制盒体边线、设置坐标轴标签、视角和颜色条。
# 这是三维地质建模中常用的数据展示方式。

from zmlx import *


def on_figure(fig):
    """
    在figure对象上绘制三维等值线填充图

    生成一个100x300x500的模拟数据体，在三个正交面上绘制填充等值线，
    并添加盒体边缘线和颜色条，展示三维数据体的空间分布特征。

    Args:
        fig: matplotlib.figure.Figure对象，绘图的目标画布
    """
    # 定义三维数据维度
    Nx, Ny, Nz = 100, 300, 500
    X, Y, Z = np.meshgrid(np.arange(Nx), np.arange(Ny), -np.arange(Nz))

    # 生成模拟数据：二次函数形式，模拟某种物理场在空间中的分布
    data = (((X + 100) ** 2 + (Y - 20) ** 2 + 2 * Z) / 1000 + 1)

    # 设置等值线参数：颜色映射范围及等值线层级
    kw = {
        'vmin': data.min(),
        'vmax': data.max(),
        'levels': np.linspace(data.min(), data.max(), 10),
    }

    # 创建三维坐标轴
    ax = fig.add_subplot(111, projection='3d')

    # 在XY底面（z=0）绘制填充等值线
    _ = ax.contourf(
        X[:, :, 0], Y[:, :, 0], data[:, :, 0],
        zdir='z', offset=0, **kw
    )
    # 在XZ左侧面（y=0）绘制填充等值线
    _ = ax.contourf(
        X[0, :, :], data[0, :, :], Z[0, :, :],
        zdir='y', offset=0, **kw
    )
    # 在YZ右侧面（x=max）绘制填充等值线（保留返回值用于颜色条）
    C = ax.contourf(
        data[:, -1, :], Y[:, -1, :], Z[:, -1, :],
        zdir='x', offset=X.max(), **kw
    )

    # 设置坐标轴范围
    xmin, xmax = X.min(), X.max()
    ymin, ymax = Y.min(), Y.max()
    zmin, zmax = Z.min(), Z.max()
    ax.set(xlim=[xmin, xmax], ylim=[ymin, ymax], zlim=[zmin, zmax])

    # 绘制盒体边缘线，增强三维视觉效果
    edges_kw = dict(color='0.4', linewidth=1, zorder=1e3)
    ax.plot([xmax, xmax], [ymin, ymax], 0, **edges_kw)
    ax.plot([xmin, xmax], [ymin, ymin], 0, **edges_kw)
    ax.plot([xmax, xmax], [ymin, ymin], [zmin, zmax], **edges_kw)

    # 设置坐标轴标签和z轴刻度
    ax.set(
        xlabel='X [km]',
        ylabel='Y [km]',
        zlabel='Z [m]',
        zticks=[0, -150, -300, -450],
    )

    # 设置视角和缩放
    ax.view_init(40, -30, 0)     # 仰角40度，方位角-30度
    ax.set_box_aspect(None, zoom=0.9)  # 缩小至原来的0.9倍

    # 添加颜色条
    fig.colorbar(C, ax=ax, fraction=0.02, pad=0.1, label='Name [units]')


if __name__ == '__main__':
    plot(on_figure, gui_mode=True)
