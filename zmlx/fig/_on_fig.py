"""
定义数据驱动的绘图模式
"""
from zmlx.fig._item import item


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
