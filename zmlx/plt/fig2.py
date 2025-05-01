try:
    import numpy as np
except Exception as e:
    print(e)
    np = None

from zml import is_array
from zmlx.plt.cmap import get_cm, get_color
from zmlx.plt.on_axes import plot_on_axes
from zmlx.plt.on_figure import plot_on_figure


def contourf(x=None, y=None, z=None,
             levels=20,
             cmap='coolwarm',
             clabel=None,
             **opts):
    """
    绘制二维填充等高线图（云图），支持灵活的参数配置

    Parameters
    ----------
    x, y : array-like, optional
        坐标数组，形状需与z的维度匹配。若未提供，将自动生成基于z的索引坐标
    z : array-like,2D
        二维标量数据数组，形状为 (ny, nx)
    levels : int or array-like, default 20
        等高线层级配置：
        - 整数：自动生成该数量的等间距层级
        - 数组：使用指定值作为层级边界
    cmap : str or Colormap, default 'coolwarm'
        颜色映射名称或Colormap对象
    clabel : str, optional
        是否显示等高线标签，默认由绘图后端决定
    **opts : dict
        传递给底层plot函数的附加参数
    """

    def on_axes(ax):
        item = ax.contourf(
            x, y, z,
            levels=levels, cmap=cmap, antialiased=True
        )
        cbar = ax.get_figure().colorbar(item, ax=ax)
        if clabel is not None:
            cbar.set_label(clabel)

    plot_on_axes(on_axes, **opts)


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


def show_dfn2(dfn2, **opts):
    """
    利用画线的方式显示一个二维的离散裂缝网络. 主要用于测试.
    """

    def on_axes(ax):
        for pos in dfn2:
            ax.plot([pos[0], pos[2]], [pos[1], pos[3]])

    opts.setdefault('aspect', 'equal')
    plot_on_axes(on_axes, **opts)


def show_field2(f, xr, yr, clabel=None, **opts):
    """
    显示一个二维的场，用于测试
    """

    def on_axes(ax):
        x = []
        y = []
        z = []
        va = [xr[0] + (xr[1] - xr[0]) * i * 0.01 for i in range(101)]
        vb = [yr[0] + (yr[1] - yr[0]) * i * 0.01 for i in range(101)]
        for a in va:
            for b in vb:
                x.append(a)
                y.append(b)
                z.append(f(a, b))
        item = ax.tricontourf(
            x, y, z,
            levels=30,
            cmap='coolwarm',
            antialiased=True
        )
        cbar = ax.get_figure().colorbar(item, ax=ax)
        if isinstance(clabel, str):
            cbar.set_label(clabel)

    plot_on_axes(on_axes, **opts)


def tricontourf(x=None, y=None, z=None,
                ipath=None, ix=None, iy=None, iz=None,
                triangulation=None,
                levels=20,
                cmap='coolwarm',
                clabel=None,
                **opts):
    """
    利用给定的x，y，z来画一个二维的云图.
    """

    def _load(ipath=None, ix=None, iy=None, iz=None):
        import numpy as np
        data = np.loadtxt(ipath, float)
        return data[:, ix], data[:, iy], data[:, iz]

    def on_axes(ax):
        args = (x, y, z) if ipath is None else _load(ipath, ix, iy, iz)
        if triangulation is None:
            item = ax.tricontourf(*args, levels=levels, cmap=cmap,
                                  antialiased=True)
        else:
            item = ax.tricontourf(triangulation, args[2], levels=levels,
                                  cmap=cmap, antialiased=True)

        cbar = ax.get_figure().colorbar(item, ax=ax)
        if clabel is not None:
            cbar.set_label(clabel)

    opts.setdefault('aspect', 'equal')
    plot_on_axes(on_axes, **opts)


def show_fn2(pos=None, w=None, c=None, w_min=1, w_max=4, ipath=None, iw=4, ic=6,
             clabel=None, ctitle=None,
             title=None,
             xlabel=None, ylabel=None,
             xlim=None, ylim=None,
             **opt):
    """显示二维裂缝网络数据。

    该函数支持两种数据输入方式：
    1. 直接通过参数传递数据
    2. 从文本文件读取数据（当ipath参数被指定时）

    Args:
        pos (list[tuple], optional): 裂缝位置数据，每个元素为包含4个浮点数的元组，
            表示线段端点坐标(x0, y0, x1, y1)。默认为None。
        w (list[float], optional): 裂缝宽度数据，长度需与pos一致。默认为None。
        c (list[float], optional): 裂缝颜色数据，长度需与pos一致。默认为None。
        w_min: (float, optional): 线条最小显示宽度（像素单位）。默认为0.1。
        w_max (float, optional): 线条最大显示宽度（像素单位）。默认为4。
        ipath (str, optional): 数据文件路径，优先级高于pos/w/c参数。默认为None。
        iw (int, optional): 文件中宽度数据列索引（0-based）。默认为4。
        ic (int, optional): 文件中颜色数据列索引（0-based）。默认为6。
        clabel (str, optional): 颜色条轴标签（如'Pressure [Pa]'）。默认为None。
        ctitle (str, optional): 颜色条标题。默认为None。
        title (str, optional): 图表主标题。默认为None。
        xlabel (str, optional): x轴标签，默认显示'x / m'。
        ylabel (str, optional): y轴标签，默认显示'y / m'。
        xlim (tuple[float], optional): x轴显示范围(min, max)。默认为None。
        ylim (tuple[float], optional): y轴显示范围(min, max)。默认为None。
        **opt: 传递给 plot_on_figure 的额外参数

    Returns:
        None: 直接显示matplotlib图形，无返回值

    Note:
        文件数据格式要求：
        1. 当使用ipath参数时，文件应为空格/制表符分隔的文本文件
        2. 自动处理颜色映射：
            - 颜色数据会自动归一化到[cl, cr]范围
            - cl/cr通过数据集的min/max值自动计算
            - 可通过opt参数中的cmap指定颜色映射
    """
    if pos is None or w is None or c is None:
        if ipath is not None:
            import numpy as np
            d = np.loadtxt(ipath)
            pos = d[:, 0: 4]
            w = d[:, iw]
            c = d[:, ic]

    count = len(pos)
    if count == 0:
        return

    assert not is_array(w) or len(w) == count, f'w = {w}, count = {count}'
    assert not is_array(c) or len(c) == count, f'c = {c}, count = {count}'

    def get(t, i):
        if is_array(t):
            return t[i]
        else:
            return t if t is not None else 1

    def get_w(i):
        return get(w, i)

    def get_c(i):
        return get(c, i)

    def get_r(f):
        """
        返回给定函数的取值范围
        """
        lr = f(0)
        rr = lr
        for i in range(1, count):
            v = f(i)
            lr = min(lr, v)
            rr = max(rr, v)
        return lr, rr

    # 宽度和颜色对应的原始数据的范围
    wl, wr = get_r(get_w)
    cl, cr = get_r(get_c)
    xl, xr = get_r(lambda i: (pos[i][0] + pos[i][2]) / 2)
    yl, yr = get_r(lambda i: (pos[i][1] + pos[i][3]) / 2)

    # 获取颜色表
    cmap = opt.pop('cmap', None)  # 这个default不可以省略
    if isinstance(cmap, str) or cmap is None:
        cmap = get_cm(cmap)

    if w_max < w_min:  # 确保w_max > w_min
        w_max, w_min = w_min, w_max

    def on_figure(fig):
        from matplotlib.cm import ScalarMappable
        from matplotlib.colors import Normalize

        ax = fig.subplots()
        ax.set_xlabel(xlabel if xlabel is not None else 'x / m')
        ax.set_ylabel(ylabel if ylabel is not None else 'y / m')
        if title is not None:
            ax.set_title(title)

        assert w_min <= w_max, \
            f'The w_min({w_min}) must be less than w_max({w_max}).'
        for idx in range(count):
            x0, y0, x1, y1 = pos[idx]
            lw = w_min + get_w(idx) * (w_max - w_min) / max(wr, 1.0e-10)
            ax.plot(
                [x0, x1],
                [y0, y1],
                c=get_color(cmap, cl, cr, get_c(idx)),
                linewidth=lw)

        # 创建ScalarMappable对象用于colorbar
        mappable = ScalarMappable(
            norm=Normalize(vmin=cl, vmax=cr), cmap=cmap)
        mappable.set_array([])  # 必须设置空数组才能显示colorbar
        # 添加colorbar
        cbar = fig.colorbar(mappable, ax=ax)
        if clabel is not None:
            cbar.set_label(clabel)
        if ctitle is not None:
            cbar.ax.set_title(ctitle)

        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)

        ratio = max(xr - xl, 1.0e-10) / max(yr - yl, 1.0e-10)
        if 0.0333 <= ratio <= 33.33:
            ax.set_aspect('equal')

    # 执行绘图
    plot_on_figure(on_figure, **opt)


def trimesh(triangles, points, line_width=1.0, **opts):
    """
    调用plot_on_axes，使用Matplotlib绘制二维三角形网格.

    Args:
        line_width: 绘制三角形的时候，线条的宽度 (默认为1.0)
        triangles: 三角形的索引，形状为(N, 3). 或者是一个list，且list的每一个元素的长度都是3
        points: 顶点坐标，形状为(N, 2). 或者是一个list，且list的每一个元素的长度都是2
        **opts: 传递给plot_on_axes的参数，主要包括:
            caption(str): 在界面绘图的时候的标签 （默认为untitled）
            clear(bool): 是否清除界面上之前的axes （默认清除）
            on_top (bool): 是否将标签页当到最前面显示 (默认为否)

    Note:
        此函数主要用于测试显示二维三角形网格的结构，类似与Matlab的trimesh函数，主要画出
        三角形的边，并且为了显示得更加清晰，边的颜色是随机的。
    """

    def on_axes(ax):
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
    plot_on_axes(on_axes=on_axes, dim=2, **opts)


def tricontourf_(ax, x=None, y=None, z=None, ipath=None, ix=None, iy=None,
                 iz=None,
                 triangulation=None, levels=20, cmap='coolwarm'):
    """
    利用给定的x，y，z来画一个二维的云图
    """
    if ipath is not None:
        import numpy as np
        data = np.loadtxt(ipath, float)
        if ix is not None:
            x = data[:, ix]
        if iy is not None:
            y = data[:, iy]
        if iz is not None:
            z = data[:, iz]

    if triangulation is None:
        return ax.tricontourf(x, y, z, levels=levels, cmap=cmap,
                              antialiased=True)
    else:
        return ax.tricontourf(triangulation, z, levels=levels,
                              cmap=cmap, antialiased=True)


kernels = {'tricontourf': tricontourf_}


def plot2(data=None, **opts):
    """
    调用内核函数来做一个二维的绘图. 可以多个数据叠加绘图;
    其中plots为绘图的数据，其中的每一个item都是一个dict，
        在每一个dict中，必须包含三个元素：name, args和kwargs
    """

    def on_axes(ax):
        """
        执行绘图
        """
        if data is None:
            return
        for d in data:
            name = d.get('name')
            if name is None:
                continue
            args, kwargs, kwds = d.get('args', []), d.get(
                'kwargs', {}), d.get('kwds', {})
            kwargs.update(kwds)  # 优先使用kwds
            succeed = False
            obj = None
            if not succeed:
                try:  # 优先去使用标准的版本
                    obj = getattr(ax, name, None)(*args, **kwargs)
                    succeed = True
                except:
                    pass
            if not succeed:
                try:  # 尝试使用自定义的内核函数
                    obj = kernels.get(name)(ax, *args, **kwargs)
                    succeed = True
                except:
                    pass
            if succeed:  # 绘图成功，尝试添加colorbar
                clabel = d.get('clabel')
                if d.get('has_colorbar') or clabel is not None:
                    cbar = ax.get_figure().colorbar(obj, ax=ax)
                    if clabel is not None:
                        cbar.set_label(clabel)
            else:
                print(f'plot failed: name={name}, '
                      f'args={args}, kwargs={kwargs}')

    plot_on_axes(on_axes, dim=2, **opts)
