# ** desc = 'matplotlib绘图示例'
#
# 本案例演示matplotlib三角网格填充等值线图（tricontourf）的多种用法。
# 包括：
#   1. 基于Delaunay三角剖分的填充等值线
#   2. 带填充图案（hatching）的等值线
#   3. 无颜色仅含填充图案的等值线（带图例）
#   4. 用户自定义三角剖分的填充等值线（经纬度数据）
# 三角网格适用于非规则网格数据的可视化，在地质建模和地球物理中
# 有广泛应用（如井点数据插值、地形图绘制等）。

import matplotlib.tri as tri

from zmlx import *


def main():
    """
    主函数：演示tricontourf的4种不同用法

    分别展示：
      figure1: Delaunay三角剖分的填充等值线+等值线叠加
      figure2: 带填充图案的等值线（cividis颜色映射）
      figure3: 仅含填充图案（无颜色）的等值线，带图例
      figure4: 用户自定义三角剖分的等值线（经纬度坐标数据）
    """
    # %%
    # Creating a Triangulation without specifying the triangles results in the
    # Delaunay triangulation of the points.
    # 不指定三角形时，默认使用Delaunay三角剖分

    # First create the x and y coordinates of the points.
    # 首先生成点的x、y坐标
    n_angles = 48         # 角度方向分段数
    n_radii = 8           # 半径方向分段数
    min_radius = 0.25     # 最小半径（中心空洞区域）
    radii = np.linspace(min_radius, 0.95, n_radii)

    angles = np.linspace(0, 2 * np.pi, n_angles, endpoint=False)
    angles = np.repeat(angles[..., np.newaxis], n_radii, axis=1)
    angles[:, 1::2] += np.pi / n_angles   # 交错偏移以改善网格质量

    # 将极坐标转为直角坐标
    x = (radii * np.cos(angles)).flatten()
    y = (radii * np.sin(angles)).flatten()
    # 计算标量值：径向和角向的余弦乘积
    z = (np.cos(radii) * np.cos(3 * angles)).flatten()

    # 创建三角剖分对象（未指定三角形，将自动进行Delaunay三角剖分）
    triang = tri.Triangulation(x, y)

    # 遮罩掉中心区域（半径小于min_radius）的三角形
    triang.set_mask(np.hypot(x[triang.triangles].mean(axis=1),
                             y[triang.triangles].mean(axis=1))
                    < min_radius)

    # %%
    # pcolor plot.
    # figure1: 基础填充等值线 + 等值线叠加
    def on_figure1(fig1):
        """绘制Delaunay三角剖分的填充等值线和等值线"""
        ax1 = fig1.add_subplot()
        ax1.set_aspect('equal')
        tcf = ax1.tricontourf(triang, z)          # 填充等值线
        fig1.colorbar(tcf)
        ax1.tricontour(triang, z, colors='k')      # 叠加黑色等值线
        ax1.set_title('Contour plot of Delaunay triangulation')

    plot(on_figure1, caption='figure1')

    # %%
    # You could also specify hatching patterns along with different cmaps.
    # figure2: 带填充图案（hatching）的等值线
    def on_figure2(fig2):
        """绘制带填充图案和cividis颜色映射的等值线"""
        ax2 = fig2.add_subplot()
        ax2.set_aspect("equal")
        tcf = ax2.tricontourf(
            triang,
            z,
            hatches=["*", "-", "/", "//", "\\", None],  # 设置填充图案样式
            cmap="cividis"
        )
        fig2.colorbar(tcf)
        # 叠加黑色实线等值线，宽度2.0
        ax2.tricontour(triang, z, linestyles="solid", colors="k", linewidths=2.0)
        ax2.set_title("Hatched Contour plot of Delaunay triangulation")

    plot(on_figure2, caption='figure2')

    # %%
    # You could also generate hatching patterns labeled with no color.
    # figure3: 仅含填充图案（无颜色）的等值线
    def on_figure3(fig3):
        """绘制仅含填充图案、不带颜色的等值线，并添加图例"""
        ax3 = fig3.add_subplot()
        ax3.set_aspect("equal")
        n_levels = 7
        tcf = ax3.tricontourf(
            triang,
            z,
            n_levels,
            colors="none",         # 不使用颜色
            hatches=[".", "/", "\\", None, "\\\\", "*"],  # 仅使用填充图案
        )
        ax3.tricontour(triang, z, n_levels, colors="black", linestyles="-")

        # 为等值线集创建图例
        artists, labels = tcf.legend_elements(str_format="{:2.1f}".format)
        ax3.legend(artists, labels, handleheight=2, framealpha=1)

    plot(on_figure3, caption='figure3')

    # %%
    # You can specify your own triangulation rather than perform a Delaunay
    # triangulation of the points, where each triangle is given by the indices of
    # the three points that make up the triangle, ordered in either a clockwise or
    # anticlockwise manner.
    # 用户自定义三角剖分：指定每个三角形的三个顶点索引（顺时针或逆时针顺序）

    # 定义不规则分布的经纬度数据点
    xy = np.asarray([
        [-0.101, 0.872], [-0.080, 0.883], [-0.069, 0.888], [-0.054, 0.890],
        [-0.045, 0.897], [-0.057, 0.895], [-0.073, 0.900], [-0.087, 0.898],
        [-0.090, 0.904], [-0.069, 0.907], [-0.069, 0.921], [-0.080, 0.919],
        [-0.073, 0.928], [-0.052, 0.930], [-0.048, 0.942], [-0.062, 0.949],
        [-0.054, 0.958], [-0.069, 0.954], [-0.087, 0.952], [-0.087, 0.959],
        [-0.080, 0.966], [-0.085, 0.973], [-0.087, 0.965], [-0.097, 0.965],
        [-0.097, 0.975], [-0.092, 0.984], [-0.101, 0.980], [-0.108, 0.980],
        [-0.104, 0.987], [-0.102, 0.993], [-0.115, 1.001], [-0.099, 0.996],
        [-0.101, 1.007], [-0.090, 1.010], [-0.087, 1.021], [-0.069, 1.021],
        [-0.052, 1.022], [-0.052, 1.017], [-0.069, 1.010], [-0.064, 1.005],
        [-0.048, 1.005], [-0.031, 1.005], [-0.031, 0.996], [-0.040, 0.987],
        [-0.045, 0.980], [-0.052, 0.975], [-0.040, 0.973], [-0.026, 0.968],
        [-0.020, 0.954], [-0.006, 0.947], [0.003, 0.935], [0.006, 0.926],
        [0.005, 0.921], [0.022, 0.923], [0.033, 0.912], [0.029, 0.905],
        [0.017, 0.900], [0.012, 0.895], [0.027, 0.893], [0.019, 0.886],
        [0.001, 0.883], [-0.012, 0.884], [-0.029, 0.883], [-0.038, 0.879],
        [-0.057, 0.881], [-0.062, 0.876], [-0.078, 0.876], [-0.087, 0.872],
        [-0.030, 0.907], [-0.007, 0.905], [-0.057, 0.916], [-0.025, 0.933],
        [-0.077, 0.990], [-0.059, 0.993]])
    # 转换为角度制
    x = np.degrees(xy[:, 0])
    y = np.degrees(xy[:, 1])
    x0 = -5         # 高斯函数中心经度
    y0 = 52         # 高斯函数中心纬度
    # 计算高斯型标量场（模拟地球物理中的局部异常）
    z = np.exp(-0.01 * ((x - x0) ** 2 + (y - y0) ** 2))

    # 用户自定义三角形连接关系（顶点索引数组）
    triangles = np.asarray([
        [67, 66, 1], [65, 2, 66], [1, 66, 2], [64, 2, 65], [63, 3, 64],
        [60, 59, 57], [2, 64, 3], [3, 63, 4], [0, 67, 1], [62, 4, 63],
        [57, 59, 56], [59, 58, 56], [61, 60, 69], [57, 69, 60], [4, 62, 68],
        [6, 5, 9], [61, 68, 62], [69, 68, 61], [9, 5, 70], [6, 8, 7],
        [4, 70, 5], [8, 6, 9], [56, 69, 57], [69, 56, 52], [70, 10, 9],
        [54, 53, 55], [56, 55, 53], [68, 70, 4], [52, 56, 53], [11, 10, 12],
        [69, 71, 68], [68, 13, 70], [10, 70, 13], [51, 50, 52], [13, 68, 71],
        [52, 71, 69], [12, 10, 13], [71, 52, 50], [71, 14, 13], [50, 49, 71],
        [49, 48, 71], [14, 16, 15], [14, 71, 48], [17, 19, 18], [17, 20, 19],
        [48, 16, 14], [48, 47, 16], [47, 46, 16], [16, 46, 45], [23, 22, 24],
        [21, 24, 22], [17, 16, 45], [20, 17, 45], [21, 25, 24], [27, 26, 28],
        [20, 72, 21], [25, 21, 72], [45, 72, 20], [25, 28, 26], [44, 73, 45],
        [72, 45, 73], [28, 25, 29], [29, 25, 31], [43, 73, 44], [73, 43, 40],
        [72, 73, 39], [72, 31, 25], [42, 40, 43], [31, 30, 29], [39, 73, 40],
        [42, 41, 40], [72, 33, 31], [32, 31, 33], [39, 38, 72], [33, 72, 38],
        [33, 38, 34], [37, 35, 38], [34, 38, 35], [35, 37, 36]])

    # %%
    # Rather than create a Triangulation object, can simply pass x, y and triangles
    # arrays to tripcolor directly.  It would be better to use a Triangulation
    # object if the same triangulation was to be used more than once to save
    # duplicated calculations.
    # figure4: 直接使用x、y、triangles数组绘制等值线
    def on_figure4(fig4):
        """使用用户自定义三角剖分绘制填充等值线"""
        ax4 = fig4.add_subplot()
        ax4.set_aspect('equal')
        tcf = ax4.tricontourf(x, y, triangles, z)   # 直接传入三角形数组
        fig4.colorbar(tcf)
        ax4.set_title('Contour plot of user-specified triangulation')
        ax4.set_xlabel('Longitude (degrees)')
        ax4.set_ylabel('Latitude (degrees)')

    plot(on_figure4, caption='figure4')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
