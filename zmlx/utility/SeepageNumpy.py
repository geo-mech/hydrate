import zmlx.alg.sys as warnings

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, please import from zmlx instead.',
              DeprecationWarning, stacklevel=2)

from zmlx.base.seepage import SeepageNumpy, as_numpy

__all__ = ['SeepageNumpy', 'as_numpy']
