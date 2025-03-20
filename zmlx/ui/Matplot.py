from zmlx.plt.plotxy import plotxy
from zmlx.plt.scatter import scatter
from zmlx.plt.tricontourf import tricontourf

__all__ = ['scatter', 'tricontourf', 'plotxy']

import warnings

warnings.warn('zmlx.ui.Matplot will be deleted after 2026-3-5. '
              'Use zmlx.plt instead', DeprecationWarning)
