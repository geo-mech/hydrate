from zmlx.plt.fig2 import plotxy
from zmlx.plt.fig2 import tricontourf
from zmlx.plt.fig3 import scatter

__all__ = ['scatter', 'tricontourf', 'plotxy']

import zmlx.alg.sys as warnings

warnings.warn('zmlx.ui.Matplot will be deleted after 2026-3-5. '
              'Use zmlx.plt instead', DeprecationWarning, stacklevel=2)


