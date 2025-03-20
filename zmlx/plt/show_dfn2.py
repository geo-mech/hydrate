from zml import Dfn2
from zmlx.ui.GuiBuffer import plot


def show_dfn2(dfn2, *,
              aspect='equal',
              title='The Discrete Fracture Network',
              xlabel='x / m',
              ylabel='y / m',
              **opts):
    """
    利用画线的方式显示一个二维的离散裂缝网络. 主要用于测试.
    """

    def on_figure(fig):
        """
        用以在fig上绘图的内核函数
        """
        ax = fig.subplots()  # 创建二维的坐标轴
        if isinstance(xlabel, str):
            ax.set_xlabel(xlabel)
        if isinstance(ylabel, str):
            ax.set_ylabel(ylabel)
        if isinstance(title, str):
            ax.set_title(title)
        for pos in dfn2:
            ax.plot([pos[0], pos[2]], [pos[1], pos[3]])
        if aspect is not None:
            ax.set_aspect(aspect)

    # 执行绘图
    plot(on_figure, **opts)


def __test(angle=None, length=None,
           pos_range=None, p21=None, lmin=None):
    """
    创建二维的DFN模型，并将它保存到给定的文件.
    返回二维DFN对象
    """
    if length is None:
        length = [float(i) + 10.0 for i in range(51)]
    if angle is None:
        angle = [0, 1.5]
    dfn = Dfn2()
    if pos_range is None:
        dfn.range = [-100, -100, 100, 100]
    else:
        dfn.range = pos_range
    if p21 is None:
        p21 = 0.2
    if lmin is None:
        lmin = 2
    dfn.add_frac(angles=angle, lengths=length, p21=p21, l_min=lmin)
    show_dfn2(dfn.get_fractures())


if __name__ == '__main__':
    __test()
