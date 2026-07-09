from zmlx.exts import Seepage
from zmlx.plt import add_axes2, calculate_subplot_layout
from zmlx.fig import add_to_axes as add_items, item
from zmlx.tfc import get_p, get_t, get_time
from zmlx.ui import plot
from matplotlib.tri import Triangulation

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
    cells = _plot_cells(model)
    x = [cell.pos[0] for cell in cells]
    z = [cell.pos[2] for cell in cells]
    triangulation = Triangulation(x, z)
    names = [name for name in fields if name in keys]

    def cell_attr(name):
        key = keys[name]
        return [cell.get_attr(key, default_val=0.0) for cell in cells]

    def on_figure(fig):
        total = 2 + len(names)
        n_rows, n_cols = calculate_subplot_layout(
            max(total, 1),
            subplot_aspect_ratio=0.65,
            fig=fig)
        opts = dict(ncols=n_cols, nrows=n_rows, xlabel='x/m', ylabel='z/m', aspect='equal')
        cbar = dict(shrink=0.65)
        args = ['tricontourf', triangulation]

        add_axes2(
            fig, add_items,
            item(*args, _select_values(get_t(model), model, cells), cbar=cbar, cmap='coolwarm'),
            title='temperature_K',
            index=1,
            **opts)
        add_axes2(
            fig, add_items,
            item(*args, [p / 1.0e6 for p in _select_values(get_p(model), model, cells)], cbar=cbar, cmap='jet'),
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


def _plot_cells(model):
    cells = list(model.cells)
    max_water = _max_plot_water_kg(model)
    if max_water is None:
        return cells
    h2o = model.find_fludef('h2o')
    if h2o is None:
        return cells
    selected = []
    for cell in cells:
        try:
            water = float(cell.get_fluid(*h2o).mass)
        except Exception:
            water = 0.0
        if 0.0 < water <= max_water:
            selected.append(cell)
    return selected if len(selected) >= 3 else cells


def _max_plot_water_kg(model):
    try:
        return max(float(model.get_text('MineralizationMaxWaterKg')), 0.0)
    except Exception:
        return None


def _select_values(values, model, cells):
    if len(cells) == len(model.cells):
        return values
    return [values[cell.index] for cell in cells]
