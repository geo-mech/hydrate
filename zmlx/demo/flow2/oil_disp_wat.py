# ** desc = '两相流，油驱替水模拟'

from zmlx import *
from wat_disp_oil import create, show


def oil_disp_wat():
    """
    执行建模并且求解的主函数
    """
    model = create(30, 30, s=(0, 1), fid_inj=0)
    seepage.solve(model, close_after_done=False, extra_plot=lambda: show(model, 30, 30),
                  hide_console_when_done=True)


if __name__ == '__main__':
    oil_disp_wat()
