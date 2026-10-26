"""legend 绘图工具。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.plt.on_axes import add_legend

_keep = [add_legend]


warn(
    'The module zmlx.plt.legend 已弃用（remove after 2027-5-23）：'
    '请改用 `from zmlx import add_legend`',
    DeprecationWarning, stacklevel=2)
