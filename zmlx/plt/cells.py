"""cells 绘图工具。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.tfc import show_cells

_keep = [show_cells]


warn(
    'The module zmlx.plt.cells 已弃用（remove after 2027-5-23）：'
    '请改用 `from zmlx import show_cells`（或 `from zmlx.tfc import show_cells`）',
    DeprecationWarning, stacklevel=2)
