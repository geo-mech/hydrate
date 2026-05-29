from zmlx.exts import Seepage
from zmlx.plt import add_axes2, add_items, item
from zmlx.tfc import get_cell_mask, get_x, get_z, get_t, get_p, get_v, get_time
from zmlx.ui import plot


def show_xz(model: Seepage, caption=None, *, yr=None, zr=None, xr=None):
    """
    显示xz平面的温度、压力、流体饱和度
    """

    def on_figure(fig):
        from zmlx.plt import calculate_subplot_layout
        n_rows, n_cols = calculate_subplot_layout(8, subplot_aspect_ratio=0.5, fig=fig)
        opts = dict(ncols=n_cols, nrows=n_rows, xlabel='x', ylabel='z', aspect='equal')
        mask = get_cell_mask(model=model, xr=xr, yr=yr, zr=zr)
        x = get_x(model, mask=mask)
        z = get_z(model, mask=mask)
        args = ['tricontourf', x, z, ]
        t = get_t(model, mask=mask)
        add_axes2(fig, add_items, item(*args, t, cbar=dict(label='温度', shrink=0.6), cmap='coolwarm'),
                  title='温度', index=1, **opts)
        p = get_p(model, mask=mask)
        add_axes2(fig, add_items, item(*args, p, cbar=dict(label='压力', shrink=0.6), cmap='jet'),
                  title='压力', index=2, **opts)
        v = get_v(model, mask=mask)
        index = 3
        for fid in ['kg', 'ho', 'lo', 'ch4', 'h2o', 'steam', ]:
            s = get_v(model, mask=mask, fid=fid) / v
            add_axes2(fig, add_items, item(*args, s, cbar=dict(label=f'{fid}饱和度', shrink=0.6)),
                      title=f'{fid}饱和度', index=index, **opts)
            index += 1

    plot(on_figure, caption=caption, clear=True, tight_layout=True,
         suptitle=f'time = {get_time(model, as_str=True)}'
         )
