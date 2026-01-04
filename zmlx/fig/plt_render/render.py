class AxesRender:
    """
    使用Matplotlib来渲染绘图项目
    """

    def __init__(self):
        try:
            from zmlx.fig.plt_render.cbar import add_cbar
        except ImportError:
            add_cbar = None

        try:
            from zmlx.fig.plt_render.tricontourf import add_tricontourf
        except ImportError:
            add_tricontourf = None

        try:
            from zmlx.fig.plt_render.surf import add_surf
        except ImportError:
            add_surf = None

        try:
            from zmlx.fig.plt_render.contourf import add_contourf
        except ImportError:
            add_contourf = None

        def add_curve(ax, *args, **opts):
            return ax.plot(*args, **opts)

        try:
            from zmlx.fig.plt_render.dfn2 import add_dfn2
        except ImportError:
            add_dfn2 = None

        try:
            from zmlx.fig.plt_render.field2 import add_field2
        except ImportError:
            add_field2 = None

        try:
            from zmlx.fig.plt_render.rc3 import add_rc3
        except ImportError:
            add_rc3 = None

        def comb(ax, *args, **opts):
            return self.add_items(ax, args, **opts)

        try:
            from zmlx.fig.plt_render.trisurf import add_trisurf
        except ImportError:
            add_trisurf = None

        try:
            from zmlx.fig.plt_render.trimesh import add_trimesh
        except ImportError:
            add_trimesh = None

        try:
            from zmlx.fig.plt_render.scatter import add_scatter
        except ImportError:
            add_scatter = None

        self.kernels = dict(
            tricontourf=add_tricontourf, tric=add_tricontourf,
            surface=add_surf, surf=add_surf,
            colorbar=add_cbar, cbar=add_cbar,
            contourf=add_contourf, cont=add_contourf,
            curve2=add_curve, xy=add_curve, curve=add_curve,
            dfn2=add_dfn2,
            field2=add_field2,
            rc3=add_rc3,  # 三维矩形集合
            comb=comb,  # 项目组合
            trisurf=add_trisurf, tris=add_trisurf,
            trimesh=add_trimesh,
            scatter=add_scatter,
        )

    def update_kernels(self, kernels):
        """
        添加自定义的内核函数。
        Args:
            kernels: 一个字典，键为项目名称，值为添加函数
        """
        if kernels is not None:
            self.kernels.update(kernels)

    def add(self, ax, item, **default_opts):
        if len(item) == 0:  # 没有给定选项
            import warnings
            warnings.warn('没有给定项目的名称', stacklevel=2)
            return None

        name = item[0]  # 项目的名字，可以是kernels中的函数，或者是Axes对象的方法的名字
        if not isinstance(name, str):
            import warnings
            warnings.warn(f'name 不是字符串：{type(name)}', stacklevel=2)
            return None

        # 识别别名
        for step in range(10):
            assert step <= 5
            value = self.kernels.get(name, None)
            if isinstance(value, str):
                assert len(value) > 0
                name = value
            else:
                break  # 不是别名

        # 准备参数
        args = [] if 1 >= len(item) else item[1]
        opts = {} if 2 >= len(item) else item[2]

        # 合并默认选项和给定选项
        opts = {**default_opts, **opts}

        # 首先，尝试从kernels中获取对应的添加函数
        func = self.kernels.get(name, None)
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

    def add_items(self, ax, items, **common_opts):
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
            ax: Axes对象，用于添加项目
            *items: 项目的元组，每个元组包含项目的名称、参数和关键字参数

        Returns:
            一个列表，包含添加到Axes上的对象。如果项目的名称为空，则添加None到列表中。
        """
        return [self.add(ax, item, **common_opts) for item in items]


def add_to_axes(ax, *items, kernels=None):
    """
    将给定name的项目添加到Axes上。后续，会逐渐将更多的类型添加到这个函数中，从而
    使得此函数成为plt模块的一个基本的入口.

    Args:
        ax: Axes对象，用于添加项目
        *items: 项目的元组，每个元组包含项目的名称、参数和关键字参数
        kernels: 项目名称到添加函数的映射表，默认使用get_kernels()获取

    Returns:
        一个列表，包含添加到Axes上的对象。如果项目的名称为空，则添加None到列表中。
    """
    render = AxesRender()
    render.update_kernels(kernels)
    return render.add_items(ax, items)


def add_to_figure(figure, *items, **common_opts):
    from zmlx.fig.plt_render.subplot import add_subplot

    for item in items:
        if len(item) == 0:  # 没有给定选项
            import warnings
            warnings.warn('没有给定项目的名称', stacklevel=2)
            continue

        name = item[0]  # 项目的名字，可以是kernels中的函数，或者是Axes对象的方法的名字
        if not isinstance(name, str):
            import warnings
            warnings.warn(f'name 不是字符串：{type(name)}', stacklevel=2)
            continue

        args = [] if 1 >= len(item) else item[1]
        opts = {} if 2 >= len(item) else item[2]

        # 添加 common_opts
        opts = {**common_opts, **opts}

        if name == 'subplot':   # 添加子图
            add_subplot(figure, *args, **opts)

        elif name == 'comb':   # 处理组合
            add_to_figure(figure, *args, **opts)

        elif name == 'auto_layout':   # 自动划分子区域
            from zmlx.fig.plt_render.layout import calculate_subplot_layout
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
                    add_to_figure(figure, arg, ncols=n_cols, nrows=n_rows, index=index)
                    index += 1
                else:
                    add_to_figure(figure, arg)

        else:  # 调用figure的成员函数
            func = getattr(figure, name, None)
            if func is not None:  # 没有对应的方法
                func(*args, **opts)


def show(*items, **opts):
    """
    显示给定的项目(必须是subplot项目)
    Args:
        *items: 项目的元组，每个元组包含项目的名称、参数和关键字参数 (要在figure上，必须是subplot项目)
        **opts: 传递给plot函数的选项
    """
    from zmlx.ui import plot
    def f(figure):
        add_to_figure(figure, *items)

    return plot(f, **opts)
