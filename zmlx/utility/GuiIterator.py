import zmlx.alg.sys as warnings

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16. please import from zmlx instead. ',
              DeprecationWarning, stacklevel=2)



from zmlx.utility.gui_iterator import *

__all__ = ['GuiIterator']
