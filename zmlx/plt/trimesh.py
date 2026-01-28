from zmlx.data.trimesh_test import generate_test_mesh


def trimesh(triangles, points, linewidth=1.0, gui_mode=None, **opts):
    """
    调用plot，使用Matplotlib绘制二维三角形网格.

    Args:
        triangles: 三角形的索引，形状为(N, 3). 或者是一个list，且list的每一个元素的长度都是3
        points: 顶点坐标，形状为(N, 2). 或者是一个list，且list的每一个元素的长度都是2
        linewidth(float): 三角形的线宽 (默认1.0)
        gui_mode(bool): 是否在gui模式下显示 (默认None)
        **opts: 传递给plot的参数，主要包括:
            caption(str): 在界面绘图的时候的标签 （默认为untitled）
            clear(bool): 是否清除界面上之前的axes （默认清除）
            on_top (bool): 是否将标签页当到最前面显示 (默认为否)

    Note:
        此函数主要用于测试显示二维三角形网格的结构，类似与Matlab的trimesh函数，主要画出
        三角形的边，并且为了显示得更加清晰，边的颜色是随机的。
    """
    from zmlx.plt.on_axes.data import trimesh
    from zmlx.plt.on_axes import plot2d

    default_opts = dict(
        aspect='equal',
        xlabel='x / m', ylabel='y / m', title='Triangle Mesh')
    opts = {**default_opts, **opts}

    plot2d(
        trimesh(triangles, points, linewidth=linewidth), gui_mode=gui_mode,
        **opts
    )


def test():
    # 生成测试网格
    triangles, points = generate_test_mesh()
    # 绘制三角形网格
    trimesh(triangles=triangles, points=points, gui_mode=True)


if __name__ == '__main__':
    test()
