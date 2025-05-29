from zmlx.base.has_cells import *

__all__ = ['get_pos_range', 'get_cells_in_range', 'get_cell_mask',
           'get_cell_pos', 'get_cell_property', 'plot_tricontourf']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)
