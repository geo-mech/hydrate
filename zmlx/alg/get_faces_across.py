import zmlx.alg.sys as warnings

from zmlx.base.faces_across import get_faces_across

__all__ = ['get_faces_across']
warnings.warn('The modulus get_faces_across is deprecated '
              '(will be removed after 2026-4-9). '
              'please use zmlx.base.faces_across instead.',
              DeprecationWarning, stacklevel=2)
