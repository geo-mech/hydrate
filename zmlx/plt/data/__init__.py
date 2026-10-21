"""  init   绘图工具（**旧包垫片**）。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
Modified by DeepSeek, 2026-10-21: 补齐替代路径（原先只说"要删"，没说去哪）
"""
from zmlx.system import warn

warn(
    'The package zmlx.plt.data 已弃用（remove after 2027-1-27）：'
    '请改用 `from zmlx.data.example_fn2 import pos, w, c` / '
    '`from zmlx.data.surf import get_data`（或 `from zmlx.data.trimesh_test import ...`）',
    DeprecationWarning, stacklevel=2)
