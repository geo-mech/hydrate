"""plot trisurf 绘图工具（**旧路径垫片**）。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
Modified by DeepSeek, 2026-10-21: 文案纠错（modulus→module；并给出真实存在的替代路径）
"""

from zmlx.system import warn
from zmlx.plt.on_ui import show_trisurf as plot_trisurf

_keep = [plot_trisurf]

warn(
    'The module zmlx.plt.plot_trisurf 已弃用（remove after 2026-4-16）：'
    '请改用 `from zmlx import plot_trisurf`（即 show_trisurf）',
    DeprecationWarning, stacklevel=2
)
