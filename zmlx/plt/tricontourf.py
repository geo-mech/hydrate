"""tricontourf 绘图工具。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn

warn(f'{__name__} will be removed after 2027-6-1', DeprecationWarning, stacklevel=2)

from zmlx.plt.on_ui import show_tricontourf as tricontourf
from zmlx.plt.on_axes import add_tricontourf

on_axes = add_tricontourf
_keep = [add_tricontourf, tricontourf, on_axes]
