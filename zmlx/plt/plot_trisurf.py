"""plot trisurf 绘图工具。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.plt.on_ui import show_trisurf as plot_trisurf

_keep = [plot_trisurf]

warn(
    f'The modulus {__name__} is deprecated and '
    f'will be removed after 2026-4-16, import functions directly from <zmlx> instead',
    DeprecationWarning, stacklevel=2
)
