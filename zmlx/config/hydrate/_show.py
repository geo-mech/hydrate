from zmlx.alg.base import time2str
from zmlx.alg.fsys import join_paths
from zmlx.alg.fsys import make_fname
from zmlx.base.seepage import as_numpy
from zmlx.base.zml import Seepage
from zmlx.config import seepage
from zmlx.plt.fig2 import tricontourf
from zmlx.plt.on_axes import add_items, item
from zmlx.plt.on_figure import add_axes2
from zmlx.plt.subplot_layout import calculate_subplot_layout
from zmlx.ui import gui, plot

try:
    import numpy as np
except ImportError:
    np = None


def get_label(idim):
    if idim == 0:
        return 'x/m'
    if idim == 1:
        return 'y/m'
    if idim == 2:
        return 'z/m'
    else:
        return None


def show_2d_v2(
        model: Seepage, caption=None, dim0=None, dim1=None, subplot_aspect_ratio=None,
        mask=None, xr=None, yr=None, zr=None, shape=None, other_items=None,
        fids=None, tight_layout=None
):
    text = model.get_text('show_2d_v2_opts')
    if len(text) > 0:
        inner_opts = eval(text)
        assert isinstance(inner_opts, dict)
    else:
        inner_opts = {}

    if xr is None:
        xr = inner_opts.get('xr')
    if yr is None:
        yr = inner_opts.get('yr')
    if zr is None:
        zr = inner_opts.get('zr')
    if dim0 is None:
        dim0 = inner_opts.get('dim0', 0)
    if dim1 is None:
        dim1 = inner_opts.get('dim1', 0)

    if mask is None:
        if xr is not None or yr is not None or zr is not None:
            mask = seepage.get_cell_mask(model, xr=xr, yr=yr, zr=zr)

    if fids is None:
        fids = inner_opts.get('fids', ['ch4', 'ch4_hydrate'])

    if shape is None:
        shape = inner_opts.get('shape')

    x = seepage.get_cell_pos(model, dim=dim0, mask=mask, shape=shape)
    y = seepage.get_cell_pos(model, dim=dim1, mask=mask, shape=shape)

    if subplot_aspect_ratio is None:
        x0, x1 = np.min(x), np.max(x)
        y0, y1 = np.min(y), np.max(y)
        subplot_aspect_ratio = max(abs(x1 - x0), 1.0e-10) / max(abs(y1 - y0), 1.0e-10)

    if other_items is None:
        other_items = []

    def on_figure(fig):
        n_rows, n_cols = calculate_subplot_layout(
            num_plots=len(fids) + 2, subplot_aspect_ratio=subplot_aspect_ratio, fig=fig)

        opts = dict(ncols=n_cols, nrows=n_rows, xlabel=get_label(dim0),
                    ylabel=get_label(dim1), aspect='equal'
                    )
        args = ['tricontourf' if shape is None else 'contourf', x, y]

        t = seepage.get_t(model, mask=mask, shape=shape)
        add_axes2(
            fig, add_items,
            item(*args, t, cbar=dict(shrink=0.6), cmap='coolwarm'), *other_items,
            title='温度', index=1, **opts)
        p = seepage.get_p(model, mask=mask, shape=shape)
        add_axes2(
            fig, add_items,
            item(*args, p, cbar=dict(shrink=0.6), cmap='coolwarm'), *other_items,
            title='压力', index=2, **opts)

        v = seepage.get_v(model, mask=mask, shape=shape)
        index = 3
        for fid in fids:
            s = seepage.get_v(model, fid=fid, mask=mask, shape=shape) / v
            add_axes2(
                fig, add_items,
                item(*args, s, cbar=dict(shrink=0.6)), *other_items,
                title=f'{fid}饱和度', index=index, **opts)
            index += 1

    if caption is None:
        caption = f"Seepage({model.handle})"

    plot(on_figure, caption=caption, clear=True, tight_layout=tight_layout,
         suptitle=f'time = {seepage.get_time_str(model)}'
         )


def show_2d(model: Seepage, folder=None, xdim=0, ydim=1):
    """
    二维绘图，且当folder给定的时候，将绘图结果保存到给定的文件夹
    """
    if not gui:
        return

    time = seepage.get_time(model)
    options = {'title': f'plot when time={time2str(time)}'}
    x = as_numpy(model).cells.get(-(xdim + 1))
    y = as_numpy(model).cells.get(-(ydim + 1))

    def fname(key):
        return make_fname(
            time / (3600 * 24 * 365),
            folder=join_paths(folder, key),
            ext='.jpg', unit='y')

    cell_keys = seepage.cell_keys(model)

    def show_key(key):
        tricontourf(
            x, y, as_numpy(model).cells.get(cell_keys[key]),
            caption=key,
            fname=fname(key), **options)

    show_key('pre')
    show_key('temperature')

    fv_all = as_numpy(model).cells.fluid_vol

    def show_s(flu_name):
        s = as_numpy(model).fluids(*model.find_fludef(flu_name)).vol / fv_all
        tricontourf(
            x, y, s, caption=flu_name,
            fname=fname(flu_name), **options)

    for item in ['ch4', 'liq', 'ch4_hydrate']:
        show_s(item)
