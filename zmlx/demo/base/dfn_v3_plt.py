# ** desc = '创建三维的DFN(竖直的裂缝)并且基于plt来显示，测试绘图的效率'

from zmlx.geometry.dfn_v3 import to_rc3, create_demo
from zmlx.plt.show_rc3 import show_rc3
from zmlx.ui.GuiBuffer import gui


def test():
    import random
    for i in range(100):
        print(f'i = {i}')
        rc3 = to_rc3(create_demo())
        color = []
        alpha = []
        for _ in rc3:
            color.append(random.uniform(0, 1))
            alpha.append(random.uniform(0.3, 1))
        show_rc3(rc3, face_color=color, face_alpha=alpha, caption='dfn_v3')


if __name__ == '__main__':
    gui.execute(test, close_after_done=False)
