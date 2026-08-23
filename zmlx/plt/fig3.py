"""fig3 绘图工具。

Modified by Claude, 2026-08-12
"""
from zmlx.plt.on_axes import trisurf3, scatter3
from zmlx.plt.on_ui import show_rc3, show_trisurf as plot_trisurf

_keep = [trisurf3, scatter3, plot_trisurf, show_rc3]
