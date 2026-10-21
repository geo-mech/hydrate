"""旧模块名（兼容层，**已改名为** :mod:`zmlx.algs.fsys`）.

⚠️ **本模块只是一层转发**，真正的实现全在 ``zmlx/algs/fsys.py`` 里。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本模块时会发出
:class:`DeprecationWarning`。**新代码请写** ``from zmlx.algs.fsys import ...``。

Modified by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn


warn(
    '``zmlx.alg.fsys`` 已弃用（2026-10-16）：算法包已改名为 ``zmlx.algs``；'
    '本转发层将于 **2027-10-16** 删除。请改用 ``from zmlx.algs.fsys import ...``。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.algs.fsys import *  # noqa: F401,F403
from zmlx.algs.fsys import (  # noqa: F401
    abspath,
    basename,
    change_fmt,
    count_lines,
    dirname,
    exists,
    first_only,
    get_last_file,
    get_latest_file,
    get_lines,
    get_protected,
    get_size_mb,
    getatime,
    getctime,
    getmtime,
    getsize,
    getsize_str,
    has_permission,
    has_tag,
    in_directory,
    is_time_string,
    isdir,
    isfile,
    join,
    join_paths,
    list_code_files,
    list_files,
    make_fname,
    make_fpath,
    now,
    prepare_dir,
    print_tag,
    samefile,
    show_fileinfo,
    time_string
)
