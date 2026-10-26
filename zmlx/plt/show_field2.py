"""show field2 绘图工具（**旧路径垫片**）。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
Modified by DeepSeek, 2026-10-21: 文案纠错（modulus→module；并给出真实存在的替代路径）
"""

from zmlx.system import warn
from zmlx.plt.on_ui import show_field2

_keep = [show_field2]

warn(
    'The module zmlx.plt.show_field2 已弃用（remove after 2026-4-16）：'
    '请改用 `from zmlx import show_field2`',
    DeprecationWarning, stacklevel=2
)
