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


def subplot(*items, **opts):
    """
    在fig上执行的操作
    """
    return item('subplot', *items, **opts)


def axes2(*items, **opts):
    """
    在fig上执行的操作
    """
    opts['projection'] = None
    return item('subplot', *items, **opts)


def axes3(*items, **opts):
    """
    在fig上执行的操作
    """
    opts['projection'] = '3d'
    return item('subplot', *items, **opts)


def tight_layout(*args, **kwargs):
    """
    在fig上执行的操作
    """
    return item('tight_layout', *args, **kwargs)


def suptitle(text):
    """
    在fig上执行的操作
    """
    return item('suptitle', text)


def auto_layout(*axes_items, aspect_ratio=1.0, **opts):
    return item('auto_layout', *axes_items, aspect_ratio=aspect_ratio, **opts)


def add_items(figure, *items, **common_opts):
    from zmlx.plt.on_figure.subplot import add_subplot
    from zmlx.plt.on_axes.data import add_items as add_to_axes

    for a in items:
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
            add_items(figure, *args, **opts)

        elif name == 'auto_layout':  # 自动划分子区域
            from zmlx.plt.subplot_layout import calculate_subplot_layout
            aspect_ratio = opts.get('aspect_ratio', None)
            count = 0
            for arg in args:
                if arg[0] == 'subplot':
                    count += 1
            n_rows, n_cols = calculate_subplot_layout(
                count, subplot_aspect_ratio=aspect_ratio, fig=figure
            )
            index = 1
            for arg in args:
                if arg[0] == 'subplot':
                    add_items(figure, arg, ncols=n_cols, nrows=n_rows, index=index)
                    index += 1
                else:
                    add_items(figure, arg)

        else:  # 调用figure的成员函数
            func = getattr(figure, name, None)
            if func is not None:  # 没有对应的方法
                func(*args, **opts)


add_to_figure = add_items


def show(*items, **opts):
    """
    显示给定的项目(必须是subplot项目)
    Args:
        *items: 项目的元组，每个元组包含项目的名称、参数和关键字参数 (要在figure上，必须是subplot项目)
        **opts: 传递给plot函数的选项
    """
    from zmlx.ui import plot
    def f(figure):
        add_items(figure, *items)

    return plot(f, **opts)
