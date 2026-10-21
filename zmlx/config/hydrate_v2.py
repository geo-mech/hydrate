"""已弃用的模块，请改用 zmlx.scen.hydrate._config.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.scen.hydrate._config import ConfigV2

warn('use zmlx.config.hydrate instead. '
              'zmlx.config.hydrate_v2 will be removed after 2025-1-28',
              DeprecationWarning, stacklevel=2)

Config = ConfigV2

if __name__ == '__main__':
    c = Config()
    print(c.kwargs)
