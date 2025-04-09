from zmlx.plt.on_figure import plot_on_figure

__all__ = ['plot_on_figure']

import zmlx.alg.sys as warnings

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, import functions directly from <zmlx> instead',
              DeprecationWarning, stacklevel=2
              )
