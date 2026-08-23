""" legend 绘图工具。

Modified by Claude, 2026-08-12
"""
def add_legend(ax, **opts):
    """
    在ax上添加一个图例
    Args:
        ax: 目标Axes对象
        **opts: 其他参数
    """
    ax.legend(**opts)
