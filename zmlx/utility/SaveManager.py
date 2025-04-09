import zmlx.alg.sys as warnings

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16',
              DeprecationWarning, stacklevel=2)



from zmlx.utility.save_manager import *

__all__ = ['SaveManager']
