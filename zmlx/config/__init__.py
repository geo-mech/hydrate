"""
弃用的包. 此包中的所有内容，将于 2027-5-17之后彻底删除.

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn

warn("The module zmlx.config is deprecated (will be removed after 2027-5-17)",
     DeprecationWarning, stacklevel=2
     )
