from zmlx.system import warn
# Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）

warn(f"{__file__} is deprecated", DeprecationWarning, stacklevel=2)
from zmlx.fem.set_mass import set_mass

set_mas = set_mass
