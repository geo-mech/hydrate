"""已弃用的模块，请改用 zmlx.algs.around_seg.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.algs.around_seg import *

_keep = [get_cells_around_seg, get_cell_ids_around_seg]


warn(f'{__name__} will be removed after 2027-5-17', DeprecationWarning, stacklevel=2)
