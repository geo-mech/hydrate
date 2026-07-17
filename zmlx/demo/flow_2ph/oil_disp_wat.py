# ** desc = '两相流，油驱替水模拟'
#
# 物理问题描述：
#   本模型模拟油驱替水的两相流动过程（即注油采水）。
#   模型采用二维平面网格（30x30），区域范围0~30m x 0~30m。
#   初始时模型内部充满水（Water饱和度=1），
#   在右下角以恒定流量注入油（流体ID=0），油逐渐驱替孔隙中的水，
#   最终在右上角（x最大，y最大）流出。
#   这是水驱油（二次采油）的逆向过程。
#
# 建模技术要点：
#   1. 复用 wat_disp_oil.py 中的 create 和 show 函数
#   2. 仅改变初始饱和度 s=(0,1)（即Water饱和，Oil=0）和注入流体ID fid_inj=0
#   3. 通过一个文件验证了同一套代码可以模拟驱替和被驱替的双向过程
#   4. 总模拟时长100天

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from wat_disp_oil import create, show
from zmlx import *


def oil_disp_wat():
    """
    主函数：创建30x30网格的油驱水模型（初始纯水），模拟100天的驱替过程。
    通过设置 fid_inj=0 实现注油驱水，s=(0,1) 使模型初始充满水。
    """
    jx, jy = 30, 30
    model = create(jx, jy, s=(0, 1), fid_inj=0)
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy), time_forward=100 * 24 * 3600)


if __name__ == '__main__':
    gui.execute(oil_disp_wat, close_after_done=False)
