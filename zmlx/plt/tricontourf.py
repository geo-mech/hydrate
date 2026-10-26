"""tricontourf 绘图工具（**旧路径垫片**）。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
Modified by DeepSeek, 2026-10-21: 补齐替代路径（期限未动）
"""
from zmlx.system import warn

warn(
    'The module zmlx.plt.tricontourf 已弃用（remove after 2027-6-1）：'
    '请改用 `from zmlx import tricontourf`（即 show_tricontourf）'
    '或 `from zmlx import add_tricontourf`',
    DeprecationWarning, stacklevel=2)

from zmlx.plt.on_ui import show_tricontourf as tricontourf
from zmlx.plt.on_axes import add_tricontourf

on_axes = add_tricontourf
_keep = [add_tricontourf, tricontourf, on_axes]
