import zmlx.alg.sys as warnings

from zmlx.base.around_seg import get_cells_around_seg, get_cell_ids_around_seg

__all__ = ['get_cells_around_seg', 'get_cell_ids_around_seg']
warnings.warn('The module zmlx.alg.get_cells_around_seg is deprecated '
              '(will be removed after 2026-4-9). '
              'Please use zmlx.base.around_seg instead.',
              DeprecationWarning, stacklevel=2)
