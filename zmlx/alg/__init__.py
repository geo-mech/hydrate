"""
定义常用的一些算法。这些算法大部分和zml无关。目前，这个包中的内容有些混乱，会逐渐在后续的版本中
去进行整理。另外，后续会逐步避免模块/包的名字与函数/类重名。

确保：from zmlx.alg import * 可以在zmlx中的其他包内正确执行，不会循环应用.
"""
import warnings

from zmlx.alg._code_config import code_config
from zmlx.alg._slowdown import get_velocity_after_slowdown_by_viscosity
from zmlx.alg.base import (
    year_to_seconds, rand_dir3, make_index, clamp, linspace, mean, divide_list, less, is_sorted,
    join_cols, join_rows, mass2str, time2str, fsize2str
)
from zmlx.alg.fsys import first_only, print_tag, join_paths, make_fname, count_lines
from zmlx.alg.interp import create_interp1d
from zmlx.alg.multi_proc import create_async, apply_async
from zmlx.alg.sys import sbatch
from zmlx.exts import SelfPath


def get_cell_mask(*args, **kwargs):
    from zmlx.exts import get_cell_mask as impl
    warnings.warn(
        "get_cell_mask is deprecated (will be removed after 2027-5-23). Please use zmlx.exts.get_cell_mask instead.",
        DeprecationWarning, stacklevel=2)
    return impl(*args, **kwargs)


def get_pos_range(*args, **kwargs):
    from zmlx.exts import get_pos_range as impl
    warnings.warn(
        "get_pos_range is deprecated (will be removed after 2027-5-23). Please use zmlx.exts.get_pos_range instead.",
        DeprecationWarning, stacklevel=2)
    return impl(*args, **kwargs)


get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
