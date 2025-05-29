from zmlx.alg.sys import install_dep

__all__ = ['install_dep']

import zmlx.alg.sys as warnings

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

if __name__ == '__main__':
    install_dep()
