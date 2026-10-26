"""surf 绘图工具。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.plt.on_axes import add_surf

warn(
    'The module zmlx.plt.surf 已弃用（remove after 2027-5-23）：'
    '请改用 `from zmlx import add_surf`',
    DeprecationWarning, stacklevel=2)
_keep = [add_surf]
