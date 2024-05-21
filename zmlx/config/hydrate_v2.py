import warnings

warnings.warn('use zmlx.config.hydrate instead. '
              'zmlx.config.hydrate_v2 will be removed after 2025-1-28',
              DeprecationWarning)
from zmlx.config.hydrate import *

Config = ConfigV2

if __name__ == '__main__':
    c = Config()
    print(c.kwargs)
