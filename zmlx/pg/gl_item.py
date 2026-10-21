"""pyqtgraph OpenGL 元素。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
import pyqtgraph.opengl as gl


Scatter = gl.GLScatterPlotItem
Line = gl.GLLinePlotItem
Grid = gl.GLGridItem

warn(
    'please do not use <zmlx/pg/GLItem> anymore. will be removed after 2024-6-16',
    DeprecationWarning, stacklevel=2)
