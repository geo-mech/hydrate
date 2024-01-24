# ** desc = '创建一个三维的DFN(竖直的裂缝)并且基于pg来显示'

from zmlx.geometry.dfn_v3 import to_rc3, create_demo
from zmlx.pg.show_rc3 import show_rc3
from zmlx.ui.GuiBuffer import gui


def test():
    import random
    rc3 = to_rc3(create_demo())
    color = []
    alpha = []
    for _ in rc3:
        color.append(random.uniform(0, 1))
        alpha.append(random.uniform(0, 1) ** 3)
    show_rc3(rc3, color=color, alpha=alpha, caption='dfn_v3')


if __name__ == '__main__':
    gui.execute(test, close_after_done=False)
