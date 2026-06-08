"""
定义数据驱动的绘图模式
"""

from zmlx.fig._item import item


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
