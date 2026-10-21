"""  init   绘图工具。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn

warn(
    f'The package zmlx.plt.data is deprecated and '
    f'will be removed after 2027-1-27',
    DeprecationWarning, stacklevel=2)
