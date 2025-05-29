import zmlx.alg.sys as warnings

from zmlx.base.around_seg import get_faces_around_seg, get_face_ids_around_seg

__all__ = ['get_faces_around_seg', 'get_face_ids_around_seg']

warnings.warn('The modulus get_faces_around_seg is deprecated '
              'will be removed after 2026-4-9), '
              'please use zmlx.base.around_seg instead.',
              DeprecationWarning, stacklevel=2)
