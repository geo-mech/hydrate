from zmlx.plt.plot_on_axes import plot_on_axes


def plotxy(x=None, y=None, ipath=None, ix=None, iy=None,
           **opts):
    """
    绘制二维曲线图，支持数组输入和文件数据加载

    Parameters
    ----------
    x, y : array-like, optional
        一维数据数组，长度需相同。当与ipath同时存在时优先使用
    ipath : str, optional
        数据文件路径，要求为可被numpy.loadtxt读取的格式
    ix, iy : int, optional
        文件数据列的索引，用于指定x/y数据所在列
    **opts : dict
        传递给底层plot的附加参数
    """
    # 文件数据加载处理
    if ipath is not None:
        import numpy as np
        try:
            data = np.loadtxt(ipath, dtype=float)
            # 自动处理列索引（当未指定时默认0/1列）
            x = data[:, ix] if ix is not None else data[:, 0]
            y = data[:, iy] if iy is not None else data[:, 1]
        except Exception as e:
            raise ValueError(f"文件加载失败: {str(e)}") from e

    # 校验数据存在性
    if x is None or y is None:
        raise ValueError("必须提供x/y数据或有效文件路径")

    plot_on_axes(on_axes=lambda ax: ax.plot(x, y), **opts)


def test_1():
    import numpy as np
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    plotxy(x, y, title='sin(x)', xlabel='x', ylabel='y',
           caption='sin(x)', gui_mode=True)


if __name__ == '__main__':
    test_1()

