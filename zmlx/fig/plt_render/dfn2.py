def add_dfn2(ax, dfn2, **opts):
    """
    将一个二维的离散裂缝网络添加到Axes上.
    注意：
        此函数效率有待优化
    """
    for pos in dfn2:
        ax.plot([pos[0], pos[2]], [pos[1], pos[3]], **opts)
