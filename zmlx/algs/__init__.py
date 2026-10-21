"""
定义常用的一些算法。这些算法大部分和zml无关。目前，这个包中的内容有些混乱，会逐渐在后续的版本中
去进行整理。另外，后续会逐步避免模块/包的名字与函数/类重名。

确保：from zmlx.algs import * 可以在zmlx中的其他包内正确执行，不会循环应用.

Modified by Claude, 2026-08-12

⚠️ **本目录 2026-10-16 由 ``zmlx.alg`` 改名为 ``zmlx.algs``**
（与 ``utils`` / ``fluids`` / ``reactions`` / ``geometries`` / ``demos`` / ``meshes`` / ``seepage_meshes`` / ``scripts`` / ``krs`` 等一批包统一用**复数**目录名 ——
``通用算法（与 zml 无关的那些）``，复数才是它实际的形态）。

⚠️ **旧名 ``zmlx.alg`` 保留为兼容垫片**（导入即发 :class:`DeprecationWarning`，
**2027-10-16 删除**）—— 那只是过渡，**将来一定会删**，所以来历记在这里（新家）。

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.alg`` 改为 ``zmlx.algs``.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.algs._code_config import code_config
from zmlx.algs._slowdown import get_velocity_after_slowdown_by_viscosity
from zmlx.algs._startfile import startfile  # 替代os.startfile, 实现跨平台的文件打开
from zmlx.algs._update_by_git import update_by_git  # 基于 git 的安全更新
from zmlx.algs.base import (
    clamp,
    divide_list,
    fsize2str,
    is_sorted,
    join_cols,
    join_rows,
    less,
    linspace,
    make_index,
    mass2str,
    mean,
    rand_dir3,
    time2str,
    year_to_seconds,
)
from zmlx.algs.fsys import (
    count_lines,
    first_only,
    get_last_file,
    has_tag,
    is_time_string,
    join_paths,
    list_files,
    make_fname,
    make_fpath,
    prepare_dir,
    print_tag,
    time_string,
)
from zmlx.algs.interp import create_interp1d, interp1
from zmlx.algs.multi_proc import apply_async, create_async
from zmlx.algs.sys import install_dep, pip_install, sbatch, timing_show
from zmlx.exts import SelfPath
from zmlx.system import warn


def get_cell_mask(*args, **kwargs):
    """已弃用，请改用 ``zmlx.exts.get_cell_mask``（2027-5-23 后移除）."""
    from zmlx.exts import get_cell_mask as impl

    warn(
        "get_cell_mask is deprecated (will be removed after 2027-5-23). Please use zmlx.exts.get_cell_mask instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return impl(*args, **kwargs)


def get_pos_range(*args, **kwargs):
    """已弃用，请改用 ``zmlx.exts.get_pos_range``（2027-5-23 后移除）."""
    from zmlx.exts import get_pos_range as impl

    warn(
        "get_pos_range is deprecated (will be removed after 2027-5-23). Please use zmlx.exts.get_pos_range instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return impl(*args, **kwargs)


get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
