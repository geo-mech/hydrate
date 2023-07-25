import pyqtgraph.opengl as gl
import warnings

Scatter = gl.GLScatterPlotItem
Line = gl.GLLinePlotItem
Grid = gl.GLGridItem

warnings.warn('please do not use <zmlx/pg/GLItem> anymore. will be removed after 2024-6-16', DeprecationWarning)
