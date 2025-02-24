from zml import Seepage
from zmlx.alg.time2str import time2str
from zmlx.config import seepage
from zmlx.filesys import path
from zmlx.filesys.make_fname import make_fname
from zmlx.plt.tricontourf import tricontourf
from zmlx.ui import gui
from zmlx.utility.SeepageNumpy import as_numpy


def show_media(space: dict, yr, folder=None):
    """
    尝试绘图(尝试绘制基质或者裂缝系统)
    """
    if not gui.exists():
        return

    model = space.get('model')
    assert isinstance(model, Seepage)
    time = seepage.get_time(model)
    year = time / (3600 * 24 * 365)
    kwargs = {'title': f'plot when model.time={time2str(time)}'}

    x = as_numpy(model).cells.get(-1)
    z = as_numpy(model).cells.get(-3)

    y = as_numpy(model).cells.get(-2)
    mask = [yr[0] <= item <= yr[1] for item in y]

    if sum(mask) == 0:
        return

    x = x[mask]
    z = z[mask]

    cell_keys = seepage.cell_keys(model)

    def show_key(key):
        caption = key
        tricontourf(x, z,
                    as_numpy(model).cells.get(cell_keys[key])[mask],
                    caption=caption,
                    fname=make_fname(year,
                                     path.join(folder, caption),
                                     ext='.jpg', unit='y'),
                    **kwargs)

    show_key('pre')
    show_key('temperature')

    fv_all = as_numpy(model).cells.fluid_vol[mask]

    def show_s(flu_name):
        caption = flu_name
        s = as_numpy(model).fluids(*model.find_fludef(flu_name)
                                   ).vol[mask] / fv_all
        tricontourf(x, z, s, caption=caption,
                    fname=make_fname(year,
                                     path.join(folder, caption),
                                     '.jpg', 'y'),
                    **kwargs)

    for item in ['ch4', 'steam', 'h2o', 'lo', 'ho', 'char', 'kg']:
        show_s(item)


def show(space: dict, folder=None):
    """
    尝试绘图
    """
    show_media(space, yr=[-1, 0], folder=folder)
