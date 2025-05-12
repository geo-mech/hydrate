from zmlx.geometry.utils import triangle_area

__all__ = ['triangle_area', ]

import warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

if __name__ == '__main__':
    print(triangle_area(3, 4, 5))
