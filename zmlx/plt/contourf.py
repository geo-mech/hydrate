"""contourf 绘图工具。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.plt.on_axes import add_contourf
from zmlx.plt.on_ui import show_contourf as plot_contourf

on_axes = add_contourf
contourf = plot_contourf


warn(
    'The module zmlx.plt.contourf 已弃用（remove after 2027-5-23）：'
    '请改用 `from zmlx import contourf`（即 show_contourf）'
    '或 `from zmlx import add_contourf`',
    DeprecationWarning, stacklevel=2)
