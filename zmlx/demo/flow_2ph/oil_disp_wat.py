# ** desc = '两相流，油驱替水模拟'
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from wat_disp_oil import create, show
from zmlx import *


def oil_disp_wat():
    """
    执行建模并且求解的主函数
    """
    jx, jy = 30, 30
    model = create(jx, jy, s=(0, 1), fid_inj=0)
    seepage.solve(model, extra_plot=lambda: show(model, jx, jy), time_forward=100 * 24 * 3600)


if __name__ == '__main__':
    gui.execute(oil_disp_wat, close_after_done=False)
