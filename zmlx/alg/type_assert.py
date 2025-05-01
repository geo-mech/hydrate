import warnings

from zmlx.alg.sys import type_assert

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)



if __name__ == '__main__':
    type_assert('x', int)
