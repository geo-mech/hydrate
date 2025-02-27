from zml import Dfn2
from zmlx.ui.GuiBuffer import gui, plot


def show_dfn2(dfn2, **opts):
    """
    利用画线的方式显示一个二维的离散裂缝网络
    """
    def on_figure(fig):
        ax = fig.subplots()
        ax.set_aspect('equal')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        for row in dfn2:
            ax.plot([row[0], row[2]], [row[1], row[3]])
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
        dfn.range = [-75, -250, 75, 250]
    else:
        dfn.range = pos_range
    if p21 is None:
        p21 = 0
    if lmin is None:
        lmin = -1
    dfn.add_frac(angles=angle, lengths=length, p21=p21, l_min=lmin)

    show_dfn2([dfn.get_fracture(i) for i in range(dfn.fracture_n)], caption='Dfn2')


if __name__ == '__main__':
    gui.execute(lambda: __test(p21=0.2, lmin=2, pos_range=[-100, -100, 100, 100]),
                close_after_done=False)
