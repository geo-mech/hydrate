from zmlx.plt.on_axes import add_contourf
from zmlx.plt.on_ui import show_contourf as plot_contourf

on_axes = add_contourf
contourf = plot_contourf

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2027-5-23',
              DeprecationWarning, stacklevel=2)
