"""
基于matplotlib来显示绘图元素
"""
from zmlx.plt import on_axes, plot_on_figure, add_axes2, add_axes3, add_subplot


def _get_kernels():
    """
    返回添加项目的内核函数
    """
    return dict(
        tricontourf=on_axes.add_tricontourf, tric=on_axes.add_tricontourf,
        surface=on_axes.add_surf, surf=on_axes.add_surf,
        colorbar=on_axes.add_cbar, cbar=on_axes.add_cbar,
        contourf=on_axes.add_contourf, cont=on_axes.add_contourf,
        curve2=on_axes.add_curve, xy=on_axes.add_curve, curve=on_axes.add_curve,
        dfn2=on_axes.add_dfn2,
        field2=on_axes.add_field2,
        rc3=on_axes.add_rc3,  # 三维矩形集合
        trisurf=on_axes.add_trisurf, tris=on_axes.add_trisurf,
        trimesh=on_axes.add_trimesh,
        scatter=on_axes.add_scatter,
        fn2=on_axes.add_fn2,
        seepage_mesh=on_axes.add_seepage_mesh,
    )


def _add_item(ax, ax_item, *, kernels=None, **default_opts):
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
        kernels = _get_kernels()

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
        return add_to_axes(ax, *args, kernels=kernels, **opts)

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


def add_to_axes(ax, *ax_items, kernels=None, **common_opts):
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
        kernels = _get_kernels()
    return [_add_item(ax, a, kernels=kernels, **common_opts) for a in ax_items]


def plot2d(*ax2_items, **opts):
    """
    绘制二维图.
    Args:
        *ax2_items: 项目的元组，每个元组包含项目的名称、参数和关键字参数
        **opts: 传递给plot函数的关键字参数

    Returns:
        None
    """
    plot_on_figure(add_axes2, add_to_axes, *ax2_items, **opts)


def plot3d(*ax3_items, **opts):
    """
    绘制三维图.
    Args:
        *ax3_items: 项目的元组，每个元组包含项目的名称、参数和关键字参数
        **opts: 传递给plot函数的关键字参数

    Returns:
        None
    """
    plot_on_figure(add_axes3, add_to_axes, *ax3_items, **opts)


def add_to_figure(figure, *fig_items, **common_opts):
    for a in fig_items:
        if len(a) == 0:  # 没有给定选项
            import warnings
            warnings.warn('没有给定项目的名称', stacklevel=2)
            continue

        name = a[0]  # 项目的名字，可以是kernels中的函数，或者是Axes对象的方法的名字
        if not isinstance(name, str):
            import warnings
            warnings.warn(f'name 不是字符串：{type(name)}', stacklevel=2)
            continue

        args = [] if 1 >= len(a) else a[1]
        opts = {} if 2 >= len(a) else a[2]

        # 添加 common_opts
        opts = {**common_opts, **opts}

        if name == 'subplot':  # 添加子图
            add_subplot(figure, add_to_axes, *args, **opts)

        elif name == 'comb':  # 处理组合
            add_to_figure(figure, *args, **opts)

        elif name == 'auto_layout':  # 自动划分子区域
            from zmlx.plt import calc_best_layout
            aspect_ratio = opts.get('aspect_ratio', None)
            count = 0
            for arg in args:
                if arg[0] == 'subplot':
                    count += 1
            n_rows, n_cols = calc_best_layout(
                figure, num_plots=count, subplot_aspect_ratio=aspect_ratio
            )
            index = 1
            for arg in args:
                if arg[0] == 'subplot':
                    add_to_figure(figure, arg, ncols=n_cols, nrows=n_rows, index=index)
                    index += 1
                else:
                    add_to_figure(figure, arg)

        else:  # 调用figure的成员函数
            func = getattr(figure, name, None)
            if func is not None:  # 没有对应的方法
                func(*args, **opts)


def show(*fig_items, **opts):
    """
    显示给定的项目(必须是subplot项目)
    Args:
        *fig_items: 项目的元组，每个元组包含项目的名称、参数和关键字参数 (要在figure上，必须是subplot项目)
        **opts: 传递给plot函数的选项
    """

    def f(figure):
        add_to_figure(figure, *fig_items)

    return plot_on_figure(f, **opts)
