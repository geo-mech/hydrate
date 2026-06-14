from zmlx.exts import Seepage
from zmlx.plt import add_axes2, calculate_subplot_layout
from zmlx.fig import add_to_axes as add_items, item
from zmlx.tfc import get_p, get_t, get_time
from zmlx.ui import plot

from zmlx.scen.mineralization_reactor._seepage import key_fields


def show_xz(model: Seepage, caption=None, fields=None):
    """
    Show mineralization fields on the x-z section with the IGG-Hydrate GUI.
    """
    if fields is None:
        fields = [
            'pH',
            'co2_aq_kg',
            'ca_kg',
            'mg_kg',
            'hco3_kg',
            'calcite_kg',
        ]

    keys = key_fields(model)
    x = [cell.pos[0] for cell in model.cells]
    z = [cell.pos[2] for cell in model.cells]
    names = [name for name in fields if name in keys]

    def cell_attr(name):
        key = keys[name]
        return [cell.get_attr(key, default_val=0.0) for cell in model.cells]

    def on_figure(fig):
        total = 2 + len(names)
        n_rows, n_cols = calculate_subplot_layout(
            max(total, 1),
            subplot_aspect_ratio=0.65,
            fig=fig)
        opts = dict(ncols=n_cols, nrows=n_rows, xlabel='x/m', ylabel='z/m', aspect='equal')
        cbar = dict(shrink=0.65)
        args = ['tricontourf', x, z]

        add_axes2(
            fig, add_items,
            item(*args, get_t(model), cbar=cbar, cmap='coolwarm'),
            title='temperature_K',
            index=1,
            **opts)
        add_axes2(
            fig, add_items,
            item(*args, [p / 1.0e6 for p in get_p(model)], cbar=cbar, cmap='jet'),
            title='pressure_MPa',
            index=2,
            **opts)
        for index, name in enumerate(names, start=3):
            add_axes2(
                fig, add_items,
                item(*args, cell_attr(name), cbar=cbar),
                title=name,
                index=index,
                **opts)

    return plot(
        on_figure,
        caption=caption,
        clear=True,
        tight_layout=True,
        suptitle=f'time = {get_time(model, as_str=True)}',
        gui_mode=True)
