"""模块可用性检测（已弃用的过渡文件）.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn


warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import has_module

# 是否存在numpy
has_numpy = has_module('numpy')

# 是否存在scipy
has_scipy = has_module('scipy')

# 是否存在PyQt5
# has_PyQt5 = has_module('PyQt5')   # removed since 2025-4-16

# 是否存在 matplotlib
has_matplotlib = has_module('matplotlib')
