import warnings

from zmlx.alg.utils import rand_dir3

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

if __name__ == '__main__':
    for i in range(30):
        print(rand_dir3())
