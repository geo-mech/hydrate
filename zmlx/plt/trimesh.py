from zmlx.plt.on_figure import add_axes2
from zmlx.ui import plot


def trimesh(triangles, points, line_width=1.0, **opts):
    """
    调用plot，使用Matplotlib绘制二维三角形网格.

    Args:
        line_width: 绘制三角形的时候，线条的宽度 (默认为1.0)
        triangles: 三角形的索引，形状为(N, 3). 或者是一个list，且list的每一个元素的长度都是3
        points: 顶点坐标，形状为(N, 2). 或者是一个list，且list的每一个元素的长度都是2
        **opts: 传递给plot的参数，主要包括:
            caption(str): 在界面绘图的时候的标签 （默认为untitled）
            clear(bool): 是否清除界面上之前的axes （默认清除）
            on_top (bool): 是否将标签页当到最前面显示 (默认为否)

    Note:
        此函数主要用于测试显示二维三角形网格的结构，类似与Matlab的trimesh函数，主要画出
        三角形的边，并且为了显示得更加清晰，边的颜色是随机的。
    """

    def on_axes(ax):
        import numpy as np

        edges = set()
        for tri in triangles:
            assert len(tri) == 3, f'The size of tri must be 3, but got: ({tri})'
            for i in range(3):
                a, b = tri[i], tri[(i + 1) % 3]
                if a > b:
                    a, b = b, a
                edges.add((a, b))
        # 绘制每条边
        for a, b in edges:
            x = [points[a][0], points[b][0]]
            y = [points[a][1], points[b][1]]
            color = np.random.rand(3)  # 生成随机RGB颜色
            ax.plot(x, y, color=color, linewidth=line_width)

    # 设置默认的坐标轴比例为等比例，用户可通过opts覆盖
    opts.setdefault('aspect', 'equal')
    plot(add_axes2, on_axes=on_axes, **opts)


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
    import numpy as np

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
