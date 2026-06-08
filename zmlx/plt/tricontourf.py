import zmlx.alg.sys as warnings

warnings.warn(f'{__name__} will be removed after 2027-6-1', DeprecationWarning, stacklevel=2)

from zmlx.plt.on_ui import show_tricontourf as tricontourf
from zmlx.plt.on_axes import add_tricontourf

on_axes = add_tricontourf
_keep = [add_tricontourf, tricontourf, on_axes]
