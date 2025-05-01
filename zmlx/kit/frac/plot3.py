from zmlx.plt.fig3 import show_rc3
from zmlx.kit.frac.rc3 import get_rc3
from zml import Seepage
from zmlx.base.seepage import get_time
from zmlx.utility.seepage_numpy import as_numpy


def show_pressure(flow: Seepage, **opts):
    """
    二维绘图。其中颜色代表流体压力的值.
    这里，opts是传递给绘图内核show_fn2函数的参数
    """
    rc3 = get_rc3(flow)
    c = as_numpy(flow).cells.pre / 1e6
    tmp = dict(clabel='The Pressure [MPa]',
               caption='The Pressure 3d',
               title=f'Time = {get_time(flow, as_str=True)}',
               edge_width=0)
    tmp.update(opts)
    show_rc3(rc3, face_color=c, **tmp)
