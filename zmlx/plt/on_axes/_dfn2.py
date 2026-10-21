""" dfn2 绘图工具。

Modified by Claude, 2026-08-12
"""
def add_dfn2(ax, dfn2, **opts):
    """
    将一个二维的离散裂缝网络添加到Axes上.
    注意：
        此函数效率有待优化

    Args:
        ax: 要添加裂缝网络的Axes.
        dfn2: 离散裂缝网络.
        opts: 其他参数, 用于plot函数.
            例如, linewidth=0.5, color='red', etc.
            其中 ``cbar`` 与绘图框架的通用参数 ``caption`` / ``tight_layout``
            是**框架**的参数，不交给 plot；若一起透传，会报
            ``Line2D.set() got an unexpected keyword argument ...``
            （2026-10-21 修复：此前 show_dfn2 / add_dfn2 只要带这些参数就必然报错）。

    Returns:
        None
    """
    # cbar / caption / tight_layout 是 add_* 系列的统一参数，消耗在本函数里，
    # 不能透传给 ax.plot。目前 dfn2 没有逐条裂缝的标量值，故只接受 cbar、不画颜色条。
    for _key in ('cbar', 'caption', 'tight_layout'):
        opts.pop(_key, None)
    for pos in dfn2:
        ax.plot([pos[0], pos[2]], [pos[1], pos[3]], **opts)
