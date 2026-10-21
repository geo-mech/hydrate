"""get color 绘图工具（**旧路径垫片**）。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
Modified by DeepSeek, 2026-10-21: 文案纠错（modulus→module；并给出真实存在的替代路径）
"""

from zmlx.system import warn

# 真实实现所在：zmlx.plt.cmap（zmlx 顶层**没有**导出 get_color）
from zmlx.plt.cmap import get_color

_keep = [get_color]

warn(
    'The module zmlx.plt.get_color 已弃用（remove after 2026-4-16）：'
    '请改用 `from zmlx.plt import get_color` 或 `from zmlx.plt.cmap import get_color`',
    DeprecationWarning, stacklevel=2
)
