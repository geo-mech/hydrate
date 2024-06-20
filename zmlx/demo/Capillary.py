# ** desc = '流体在毛管力驱动下的流动'

import numpy as np

from zml import Seepage
from zmlx.config import capillary
from zmlx.config import seepage
from zmlx.geometry.point_distance import point_distance
from zmlx.plt.tricontourf import tricontourf
from zmlx.seepage_mesh.cube import create_cube
from zmlx.ui import gui
from zmlx.utility.SeepageNumpy import as_numpy

mud = """0.007698294	1930020.672
0.0441305	4270730.329
0.087590542	14003815.37
0.131146363	23172141.89
0.186770428	38537645.32
0.236863215	65745613.48
0.4	97799554.5"""

sand_J = """0	757.5757576
0.011	1167.929293
0.0339	1849.747475
0.0806	2891.414141
0.2015	4595.959596
0.2934	7304.292929
0.3564	11691.91919
0.4365	18636.36364
0.5081	29008.83838
0.5789	46193.18182
0.6408	73257.57576
0.6923	117146.4646
0.7346	186887.6263
0.7477	290119.9495
0.7514	460871.2121
0.7541	732171.7172
0.7576	1154223.485
0.7634	1846483.586
0.7724	2888648.99
0.7867	4626369.949
0.8086	7346635.101
0.8561	12562297.98"""

sand_K = """0	1167.929293
0.0088	1849.747475
0.0533	2891.414141
0.2083	4595.959596
0.4296	7304.292929
0.5022	11616.16162
0.5762	18503.78788
0.6374	28857.32323
0.7001	46407.82828
0.7584	73522.72727
0.8099	116420.4545
0.8134	186628.7879
0.814	292859.8485
0.8143	459627.5253
0.8165	732253.7879
0.8183	1155707.071
0.8217	1846590.909
0.8273	2887904.04
0.8364	4623099.747
0.8504	7345050.505
0.8774	12570795.45"""

sand_P = """0	130170.4545
0.3064	315587.1212
0.4867	508428.0303
0.5329	638825.7576
0.5637	744002.5253
0.5945	929103.5354
0.6363	1241477.273
0.6913	1880555.556"""

sand_T = """0	10580.80808
0.0001	12689.39394
0.0003	18945.70707
0.0043	32752.52525
0.0063	65959.59596
0.0173	93686.86869
0.0586	127279.0404
0.2346	329785.3535
0.3088	504513.8889
0.3418	626376.2626
0.3721	758901.5152
0.4051	953219.697
0.4463	1248484.848
0.5068	1895265.152"""


def get_idx(x, y, z):
    """
    定义在不同的区域所使用的毛管压力曲线的ID (从0开始编号)
    """
    if point_distance((x, y, z), (50, 50, 0)) < 20:
        return 0
    if x < 50:
        if y < 50:
            return 1
        else:
            return 2
    else:
        if y < 50:
            return 3
        else:
            return 4


def get_s(x, y, z):
    return (0, 1) if point_distance((x, y, z), (60, 50, 0)) < 20 else (1, 0)


def create():
    fludefs = [Seepage.FluDef(den=50, vis=1.0e-4, name='gas'),
               Seepage.FluDef(den=1000, vis=1.0e-3, name='water')
               ]
    model = seepage.create(
        mesh=create_cube(np.linspace(0, 100, 101),
                         np.linspace(0, 100, 101),
                         (-0.5, 0.5)),
        porosity=0.2, pore_modulus=100e6, p=1e6, temperature=280, perm=1e-14,
        s=get_s, fludefs=fludefs
    )
    model.set_kr(saturation=[0, 1],
                 kr=[0, 1])
    capillary.add(model, fid0='water', fid1='gas', get_idx=get_idx,
                  data=[mud, sand_J, sand_K, sand_P, sand_T])
    return model


def show(x, y, z, caption=None):
    tricontourf(x, y, z, caption=caption, gui_only=True)


def solve(model: Seepage):
    md = as_numpy(model)
    x = md.cells.get(-1)
    y = md.cells.get(-2)

    show(x, y, [get_idx(x[i], y[i], 0) for i in range(len(x))], caption='岩石ID')
    show(x, y, [get_s(x[i], y[i], 0)[1] for i in range(len(x))], caption='初始饱和度')

    for step in range(2000):
        gui.break_point()
        capillary.iterate(model, 1e5)
        if step % 30 == 0:
            print(f'step = {step}')
            show(x, y, md.fluids(1).vol, caption='饱和度')


def execute(gui_mode=True, close_after_done=False):
    gui.execute(solve, args=(create(),), close_after_done=close_after_done,
                disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()
