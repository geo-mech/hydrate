"""
绘图相关的函数
"""
from typing import List, Optional, Any, Union, Dict

from zmlx.exts import Seepage, np, FractureNetwork
from zmlx.plt.fn2 import show_fn2
from zmlx.plt.on_axes.dfn2 import add_dfn2
from zmlx.scen.frac._base import get_fn2, get_fp_range, get_dn_range, get_ds_range
from zmlx.tfc import seepage
from zmlx.ui import show_attrs


def _show_attr(models: List[Seepage], jx, jy, get_attr, name, dfn2_data=None):
    """
    显示各个层的饱和度
    """
    from zmlx.plt.on_figure import calc_best_layout, add_axes2
    from zmlx.plt.on_axes import contourf
    from zmlx.ui import plot, gui
    if not gui.exists():
        return

    def on_figure(fig):
        fig.clear()
        count = min(len(models), 8)  # 最多显示8层

        n_rows, n_cols = calc_best_layout(fig, num_plots=count, subplot_aspect_ratio=0.8)
        opts = dict(aspect='equal', xlabel='x/m', ylabel='y/m', nrows=n_rows, ncols=n_cols)

        for idx in range(count):
            model = models[idx]
            x = seepage.get_x(model, shape=(jx, jy))
            y = seepage.get_y(model, shape=(jx, jy))
            assert np is not None
            v = np.reshape(get_attr(model), (jx, jy))
            ax = add_axes2(
                fig, contourf, x, y, v, index=idx + 1, cbar=dict(label=name, shrink=0.7),
                title=f'Layer {idx + 1} when {seepage.get_time_str(model)}',
                cmap='coolwarm', **opts
            )
            if dfn2_data is not None:
                add_dfn2(ax, dfn2_data, linewidth=0.5)
        fig.tight_layout()

    plot(on_figure, caption=name, clear=True)


def _show_s(models: List[Seepage], jx, jy, dfn2_data=None):
    """
    显示各个层的饱和度
    """

    def get(model):
        return seepage.get_v(model, 1) / seepage.get_v(model, None)

    _show_attr(models, jx, jy, get, name='饱和度', dfn2_data=dfn2_data)


def _show_p(models: List[Seepage], jx, jy, dfn2_data=None):
    """
    显示各个层的压力
    """

    def get(model):
        return seepage.get_p(model)

    _show_attr(models, jx, jy, get, name='压力', dfn2_data=dfn2_data)


def show_network(network: FractureNetwork, w_min: float = 0.5, w_max: float = 4.0,
                 cbar: Optional[Dict[str, Any]] = None,
                 xlabel: str = 'x/m', ylabel: str = 'y/m', aspect: Union[str, float] = 'equal',
                 caption: str = '裂缝网络',
                 **opts):
    """
    显示裂缝网络
    """

    if cbar is None:
        cbar = dict(label='Pressure')

    pos, w, c = get_fn2(network, key='p')
    show_fn2(pos, w, c, w_min=w_min, w_max=w_max, cbar=cbar, xlabel=xlabel, ylabel=ylabel, aspect=aspect,
             caption=caption, **opts)


def show_p_range(network: FractureNetwork):
    """
    在界面上，显示压力属性的范围
    """
    p_min, p_max = get_fp_range(network)
    assert p_min is not None and p_max is not None
    show_attrs(p_min=dict(
        name='最小压力',
        value=f'{p_min / 1e6: .2f}MPa'
    ), p_max=dict(
        name='最大压力',
        value=f'{p_max / 1e6: .2f}MPa'
    ))


def show_w_range(network: FractureNetwork):
    """
    在界面上，显示宽度属性的范围
    """
    dn_min, dn_max = get_dn_range(network)
    assert dn_min is not None and dn_max is not None
    show_attrs(w_max=dict(
        name='最大宽度',
        value=f'{-dn_min / 1.0e-3: .2f}mm'
    ))


def show_ds_range(network: FractureNetwork):
    """
    在界面上，显示压力属性的范围
    """
    ds_min, ds_max = get_ds_range(network)
    assert ds_min is not None and ds_max is not None
    show_attrs(ds_min=dict(
        name='最小剪切',
        value=f'{ds_min / 1.0e-3: .2f}mm'
    ), ds_max=dict(
        name='最大剪切',
        value=f'{ds_max / 1.0e-3: .2f}mm'
    ))
