"""
在这里，处理对axes的各种操作。这是定义绘图的底层的操作。
"""
import warnings
from zmlx.plt.contourf import add_contourf as contourf
from zmlx.plt.scatter import add_scatter3 as scatter3
from zmlx.plt.tricontourf import add_tricontourf as tricontourf
from zmlx.plt.trisurf import add_trisurf as trisurf3

_keep = [contourf, trisurf3, tricontourf, scatter3]


def colorbar(ax, obj, **kwargs):
    """
    为Axes添加颜色条.
    Args:
        ax: Axes对象，用于添加颜色条
        obj: 用于创建颜色条的对象，例如散点图、填充等高线图等
        **kwargs: 传递给ax.colorbar函数的关键字参数
    Returns:
        颜色条对象
    """
    return ax.get_figure().colorbar(obj, ax=ax, **kwargs)


def call_ax(ax, name, *args, **kwargs):
    """
    调用Axes的方法，在ax上绘图。
    Args:
        ax: Axes对象，用于绘制图形
        name: 方法的名称，字符串形式
        *args: 传递给方法的参数
        **kwargs: 传递给方法的关键字参数
    Returns:
        调用方法的返回值
    """
    return getattr(ax, name)(*args, **kwargs)


def curve(ax, *args, **kwargs):
    """
    绘制曲线图.
    Args:
        ax: Axes对象，用于绘制曲线图
        *args: 传递给ax.plot函数的参数
        **kwargs: 传递给ax.plot函数的关键字参数
    Returns:
        绘制的曲线对象
    """
    return ax.plot(*args, **kwargs)


def plot_on_axes(on_axes, dim=2, **opts):
    """
    给定on_axes的函数，然后在界面上绘图。
    注意：
        此函数后续废弃。
    """
    from zmlx.plt.on_figure import add_axes2, add_axes3
    from zmlx.ui import plot
    add_axes = add_axes2 if dim == 2 else add_axes3
    return plot(add_axes, on_axes, **opts)


def add_subplot(*args, **kwargs):
    """
    添加子图到当前的Figure中。
    Args:
        *args: 传递给add_subplot函数的参数
        **kwargs: 传递给add_subplot函数的关键字参数
    Returns:
        Axes对象，代表添加的子图
    """
    from zmlx.plt.on_figure import add_subplot as impl
    return impl(*args, **kwargs)


def add_axes2(*args, **kwargs):
    """
    添加2D子图到当前的Figure中。
    Args:
        *args: 传递给add_axes2函数的参数
        **kwargs: 传递给add_axes2函数的关键字参数
    Returns:
        Axes对象，代表添加的2D子图
    """
    from zmlx.plt.on_figure import add_axes2 as impl
    return impl(*args, **kwargs)


def add_axes3(*args, **kwargs):
    """
    添加3D子图到当前的Figure中。
    Args:
        *args: 传递给add_axes3函数的参数
        **kwargs: 传递给add_axes3函数的关键字参数
    Returns:
        Axes对象，代表添加的3D子图
    """
    from zmlx.plt.on_figure import add_axes3 as impl
    return impl(*args, **kwargs)


def get_kernels():
    """
    获取一个“项目名称”到“内核函数”的映射表
    这个表用于将项目名称映射到对应的添加函数，从而在add_items函数中根据项目名称调用相应的添加函数。
    Returns:
        一个字典，键为项目名称，值为对应的添加函数。
    """
    from zmlx.plt.surf import add_surf
    from zmlx.plt.cbar import add_cbar
    from zmlx.plt.contourf import add_contourf
    from zmlx.plt.tricontourf import add_tricontourf
    from zmlx.plt.dfn2 import add_dfn2
    from zmlx.plt.field2 import add_field2

    # 准备“项目名称”到“内核函数”的映射表
    return dict(
        tricontourf=add_tricontourf, tric=add_tricontourf,
        surface=add_surf, surf=add_surf,
        colorbar=add_cbar, cbar=add_cbar,
        contourf=add_contourf, cont=add_contourf,
        curve2='plot', xy='plot',
        dfn2=add_dfn2,
        field2=add_field2,
    )


def add_items(ax, *items, kernels=None):
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
        kernels: 项目名称到添加函数的映射表，默认使用get_kernels()获取

    Returns:
        一个列表，包含添加到Axes上的对象。如果项目的名称为空，则添加None到列表中。
    """
    # 首先，准备“项目名称”到“内核函数”的映射表
    if kernels is None:
        kernels = get_kernels()
    else:
        assert isinstance(kernels, dict)
        temp = get_kernels()
        temp.update(kernels)
        kernels = temp

    objects = []  # 添加到Axes上的对象

    for opt in items:  # 依次添加所有的选项
        if len(opt) == 0:  # 没有给定选项
            warnings.warn('没有给定项目的名称', stacklevel=2)
            objects.append(None)
            continue

        name = opt[0]  # 项目的名字，可以是kernels中的函数，或者是Axes对象的方法的名字
        if not isinstance(name, str):
            objects.append(None)
            warnings.warn(f'name 不是字符串：{type(name)}', stacklevel=2)
            continue

        # 识别别名
        for step in range(10):
            assert step <= 5
            value = kernels.get(name, None)
            if isinstance(value, str):
                assert len(value) > 0
                name = value
            else:
                break  # 不是别名

        # 准备参数
        args = [] if 1 >= len(opt) else opt[1]
        kwargs = {} if 2 >= len(opt) else opt[2]

        # 首先，尝试从kernels中获取对应的添加函数
        func = kernels.get(name, None)
        if func is None:
            func = getattr(ax, name, None)  # 尝试从Axes对象中获取对应的方法
            if func is None:  # 没有对应的方法
                warnings.warn(f'没有对应的添加函数或方法：{name}', stacklevel=2)
                objects.append(None)
            else:
                obj = func(*args, **kwargs)
                objects.append(obj)
        else:  # 使用给定的函数绘图
            obj = func(ax, *args, **kwargs)
            objects.append(obj)

    return objects  # 返回添加到Axes上的对象列表


def item(name, *args, **kwargs):
    """
    生成一个item，用于add_items函数。
    Args:
        name: 项目的名称，字符串形式
        *args: 传递给项目的参数
        **kwargs: 传递给项目的关键字参数

    Returns:
        一个元组，包含项目的名称、参数和关键字参数
    """
    return name, args, kwargs


def plot2d(*items, **opts):
    """
    绘制二维图.
    Args:
        *items: 项目的元组，每个元组包含项目的名称、参数和关键字参数
        **opts: 传递给plot函数的关键字参数

    Returns:
        None
    """
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
    from zmlx.ui import plot
    plot(add_axes3, add_items, *items, **opts)


def test_1():
    """
    测试plot3d函数.
    """
    from zmlx.plt.data.surf import get_data
    from zmlx.plt.cmap import get_cm

    cmap = get_cm('jet')
    x, y, z, v = get_data(jx=40, jy=20, xr=(-5, 5), yr=(-3, 3))
    v0 = v.min()
    v1 = v.max() + 1
    items = [
        item('surf', x, y, z, v, clim=(v0, v1), cmap=cmap),
        item('surf', x + 10, y, z + 1, v + 1,
             clim=(v0, v1), alpha=v + 1, cmap=cmap),
        item('cbar', clim=(v0, v1), label='Hehe', shrink=0.5, cmap=cmap)
    ]
    plot3d(*items, tight_layout=True, caption='Test')


def test_2():
    """
    测试plot2d函数.
    """
    from zmlx.plt.cmap import get_cm
    import numpy as np

    x = np.linspace(-5, 5, 30)
    y = np.linspace(-5, 5, 30)
    x, y = np.meshgrid(x, y)
    z = np.sin(np.sqrt(x ** 2 + y ** 2))
    a = np.linspace(-4, 15, 100)
    b = np.sin(a)

    from zmlx.geometry.dfn2 import dfn2
    fractures = dfn2(
        lr=[2, 10], ar=[0, 1], p21=4,
        xr=[-5, 17],
        yr=[5, 17.5], l_min=0.2
    )

    cmap = get_cm('coolwarm')

    items = [
        item('cont', x, y, z, cmap=cmap),
        item('tric', x.flatten() + 12, y.flatten(), z.flatten(),
             cmap=cmap),
        item('cbar', clim=(-1, 1), label='Hehe', shrink=0.8, cmap=cmap),
        item('curve2', a, b),
        item('xy', a, b + 1),
        item('plot', a, b + 2),
        item('dfn2', fractures)
    ]
    plot2d(*items, tight_layout=True, caption='Test',
           xlabel='x', ylabel='y', aspect='equal')


if __name__ == '__main__':
    test_2()
