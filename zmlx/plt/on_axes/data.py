"""
定义数据驱动的绘图模式
"""


def item(name, *args, **kwargs):
    """
    生成一个绘图的item.
    Args:
        name: 项目的名称，字符串形式
        *args: 传递给项目的参数
        **kwargs: 传递给项目的关键字参数

    Returns:
        一个元组，包含项目的名称、参数和关键字参数
    """
    return name, args, kwargs


def tricontourf(*args, **kwargs):
    return item('tricontourf', *args, **kwargs)


def tric(*args, **kwargs):
    return tricontourf(*args, **kwargs)


def trisurf(*args, **kwargs):
    return item('trisurf', *args, **kwargs)


def tris(*args, **kwargs):
    return trisurf(*args, **kwargs)


def surface(*args, **kwargs):
    return item('surface', *args, **kwargs)


def surf(*args, **kwargs):
    return surface(*args, **kwargs)


def trimesh(*args, **kwargs):
    return item('trimesh', *args, **kwargs)


def scatter(*args, **kwargs):
    return item('scatter', *args, **kwargs)


def colorbar(*args, **kwargs):
    return item('colorbar', *args, **kwargs)


def cbar(*args, **kwargs):
    return colorbar(*args, **kwargs)


def contourf(*args, **kwargs):
    return item('contourf', *args, **kwargs)


def cont(*args, **kwargs):
    return contourf(*args, **kwargs)


def curve(*args, **kwargs):
    return item('plot', *args, **kwargs)


def curve2(*args, **kwargs):
    return curve(*args, **kwargs)


def xy(*args, **kwargs):
    return curve(*args, **kwargs)


def text(*args, **kwargs):
    """
    显示文本.

    Example:
        text(0.5, 0.5, 'Hello World')
    """
    return item('text', *args, **kwargs)


def field2(*args, **kwargs):
    return item('field2', *args, **kwargs)


def rc3(*args, **kwargs):
    return item('rc3', *args, **kwargs)


def dfn2(*args, **kwargs):
    return item('dfn2', *args, **kwargs)


def fn2(*args, **kwargs):
    return item('fn2', *args, **kwargs)


def seepage_mesh(*args, **kwargs):
    return item('seepage_mesh', *args, **kwargs)


def xlabel(text):
    return item('set_xlabel', text)


def ylabel(text):
    return item('set_ylabel', text)


def zlabel(text):
    return item('set_zlabel', text)


def title(text):
    return item('set_title', text)


def view_opts(**opts):
    return item('view_init', **opts)


def aspect(*args, **kwargs):
    return item('set_aspect', *args, **kwargs)


def xlim(*args, **kwargs):
    return item('set_xlim', *args, **kwargs)


def ylim(*args, **kwargs):
    return item('set_ylim', *args, **kwargs)


def zlim(*args, **kwargs):
    return item('set_zlim', *args, **kwargs)


def legend(*args, **kwargs):
    return item('legend', *args, **kwargs)


def grid(*args, **kwargs):
    return item('grid', *args, **kwargs)


def axis(*args, **kwargs):
    return item('axis', *args, **kwargs)


def comb(*args, **opts):
    """
    项目的组合comb.
    Args:
        *args: 项目的列表
        **opts: 传递给comb项目的关键字参数

    Returns:
        一个元组，包含项目的名称、参数和关键字参数
    """
    return item('comb', *args, **opts)


def dfn2_comb(data, **opts):
    """
    生成二维的DFN。创建一系列线段的组合
    Args:
        data:
        **opts:
    """
    curves = [curve([pos[0], pos[2]], [pos[1], pos[3]], **opts) for pos in data]
    return comb(*curves)


def get_kernels():
    """
    返回添加项目的内核函数
    """
    try:
        from zmlx.plt.on_axes.cbar import add_cbar
    except ImportError:
        add_cbar = None

    try:
        from zmlx.plt.on_axes.tricontourf import add_tricontourf
    except ImportError:
        add_tricontourf = None

    try:
        from zmlx.plt.on_axes.surf import add_surf
    except ImportError:
        add_surf = None

    try:
        from zmlx.plt.on_axes.contourf import add_contourf
    except ImportError:
        add_contourf = None

    def add_curve(ax, *args, **opts):
        return ax.plot(*args, **opts)

    try:
        from zmlx.plt.on_axes.dfn2 import add_dfn2
    except ImportError:
        add_dfn2 = None

    try:
        from zmlx.plt.on_axes.field2 import add_field2
    except ImportError:
        add_field2 = None

    try:
        from zmlx.plt.on_axes.rc3 import add_rc3
    except ImportError:
        add_rc3 = None

    try:
        from zmlx.plt.on_axes.trisurf import add_trisurf
    except ImportError:
        add_trisurf = None

    try:
        from zmlx.plt.on_axes.trimesh import add_trimesh
    except ImportError:
        add_trimesh = None

    try:
        from zmlx.plt.on_axes.scatter import add_scatter
    except ImportError:
        add_scatter = None

    try:
        from zmlx.plt.on_axes.fn2 import add_fn2
    except ImportError:
        add_fn2 = None

    try:
        from zmlx.plt.on_axes.seepage_mesh import add_seepage_mesh
    except ImportError:
        add_seepage_mesh = None

    return dict(
        tricontourf=add_tricontourf, tric=add_tricontourf,
        surface=add_surf, surf=add_surf,
        colorbar=add_cbar, cbar=add_cbar,
        contourf=add_contourf, cont=add_contourf,
        curve2=add_curve, xy=add_curve, curve=add_curve,
        dfn2=add_dfn2,
        field2=add_field2,
        rc3=add_rc3,  # 三维矩形集合
        trisurf=add_trisurf, tris=add_trisurf,
        trimesh=add_trimesh,
        scatter=add_scatter,
        fn2=add_fn2,
        seepage_mesh=add_seepage_mesh,
    )


def add_item(ax, ax_item, *, kernels=None, **default_opts):
    if len(ax_item) == 0:  # 没有给定选项
        import warnings
        warnings.warn('没有给定项目的名称', stacklevel=2)
        return None

    name = ax_item[0]  # 项目的名字，可以是kernels中的函数，或者是Axes对象的方法的名字
    if not isinstance(name, str):
        import warnings
        warnings.warn(f'name 不是字符串：{type(name)}', stacklevel=2)
        return None

    if kernels is None:
        kernels = get_kernels()

    # 识别别名
    for step in range(10):
        assert step <= 8
        value = kernels.get(name, None)
        if isinstance(value, str):
            assert len(value) > 0
            name = value
        else:
            break  # 不是别名

    # 准备参数
    args = [] if 1 >= len(ax_item) else ax_item[1]
    opts = {} if 2 >= len(ax_item) else ax_item[2]

    # 合并默认选项和给定选项
    opts = {**default_opts, **opts}

    # 对comb进行特殊的处理
    if name == 'comb':
        return add_items(ax, *args, kernels=kernels, **opts)

    # 尝试从kernels中获取对应的添加函数
    func = kernels.get(name, None)
    if func is None:
        func = getattr(ax, name, None)  # 尝试从Axes对象中获取对应的方法
        if func is None:  # 没有对应的方法
            import warnings
            warnings.warn(f'没有对应的添加函数或方法：{name}', stacklevel=2)
            return None
        else:
            obj = func(*args, **opts)
            return obj
    else:  # 使用给定的函数绘图
        obj = func(ax, *args, **opts)
        return obj


def add_items(ax, *ax_items, kernels=None, **common_opts):
    """
    将给定name的项目添加到Axes上。后续，会逐渐将更多的类型添加到这个函数中，从而
    使得此函数成为plt模块的一个基本的入口.
    name支持：
        'surf' or 'surface': 绘制三维表面图
        'cbar' or 'colorbar': 添加颜色条
        'contourf' or 'cont': 绘制填充等高线图
        'tricontourf' or 'tric': 绘制三角形填充等高线图
        'curve2' or 'xy': 绘制二维曲线

    Args:
        kernels: 一个字典，包含添加项目的内核函数
        ax: Axes对象，用于添加项目
        *ax_items: 项目的元组，每个元组包含项目的名称、参数和关键字参数

    Returns:
        一个列表，包含添加到Axes上的对象。如果项目的名称为空，则添加None到列表中。
    """
    if kernels is None:
        kernels = get_kernels()
    return [add_item(ax, a, kernels=kernels, **common_opts) for a in ax_items]


add_to_axes = add_items


def plot2d(*items, **opts):
    """
    绘制二维图.
    Args:
        *items: 项目的元组，每个元组包含项目的名称、参数和关键字参数
        **opts: 传递给plot函数的关键字参数

    Returns:
        None
    """
    from zmlx.plt.on_figure import add_axes2
    from zmlx.ui import plot
    plot(add_axes2, add_items, *items, **opts)


def plot3d(*items, **opts):
    """
    绘制三维图.
    Args:
        *items: 项目的元组，每个元组包含项目的名称、参数和关键字参数
        **opts: 传递给plot函数的关键字参数

    Returns:
        None
    """
    from zmlx.plt.on_figure import add_axes3
    from zmlx.ui import plot
    plot(add_axes3, add_items, *items, **opts)
