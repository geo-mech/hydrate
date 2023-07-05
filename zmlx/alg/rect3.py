from zmlx.geometry.rect_3d import *
import warnings


warnings.warn('please use zmlx.geometry.rect_3d instead. zmlx.alg.rect3 will deleted after 2024-7-2',
              DeprecationWarning)

__all__ = ['from_v3', 'to_v3', 'get_rc3', 'set_rc3', 'get_v3', 'set_v3', 'get_cent', 'get_area', 'v3_area',
           'get_vertexes', 'v3_intersected']

