import warnings

import pyqtgraph.opengl as gl

Scatter = gl.GLScatterPlotItem
Line = gl.GLLinePlotItem
Grid = gl.GLGridItem

warnings.warn(
    'please do not use <zmlx/pg/GLItem> anymore. will be removed after 2024-6-16',
    DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)
