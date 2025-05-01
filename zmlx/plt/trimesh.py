import warnings

import numpy as np

from zmlx.plt.fig2 import trimesh

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)


def generate_test_mesh(rows=15, cols=15, noise=0.01):
    """
    生成带有随机扰动的二维三角形测试网格

    Args:
        rows: 纵向网格单元数量 (控制生成三角形行数)
        cols: 横向网格单元数量 (控制生成三角形列数)
        noise: 坐标扰动幅度 (0表示完全规则网格)

    Returns:
        triangles: 三角形顶点索引数组，形状(N,3)
        points: 顶点坐标数组，形状(M,2)
    """
    # 生成基础网格坐标 (包含rows+1行和cols+1列)
    x = np.linspace(0, 1, cols + 1)
    y = np.linspace(0, 1, rows + 1)
    xx, yy = np.meshgrid(x, y)

    # 添加随机扰动 (-noise到noise之间的均匀分布)
    xx += np.random.uniform(-noise, noise, xx.shape)
    yy += np.random.uniform(-noise, noise, yy.shape)

    # 展平坐标并合并为点集 [N*(cols+1) + M] -> (M*N, 2)
    points = np.column_stack((xx.ravel(), yy.ravel()))

    # 生成三角形索引 (每个矩形分成两个三角形)
    triangles = []
    for j in range(rows):
        for i in range(cols):
            # 计算当前网格单元四个顶点的线性索引
            lt = j * (cols + 1) + i  # 左上
            rt = lt + 1  # 右上
            lb = (j + 1) * (cols + 1) + i  # 左下
            rb = lb + 1  # 右下

            # 添加两个三角形 (对角线分割方式：lt -> rb)
            triangles.append([lt, rt, lb])
            triangles.append([rt, rb, lb])

    return np.array(triangles), points


def test_1():
    # 生成测试网格
    triangles, points = generate_test_mesh(rows=15, cols=15, noise=0.01)
    # 绘制三角形网格
    trimesh(triangles=triangles, points=points, line_width=1.0,
            title='2D Triangle Mesh', xlabel='X', ylabel='Y', gui_mode=True)


if __name__ == '__main__':
    test_1()
