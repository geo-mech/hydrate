"""旧模块名（兼容层，**已改名为** :mod:`zmlx.algs.sys`）.

⚠️ **本模块只是一层转发**，真正的实现全在 ``zmlx/algs/sys.py`` 里。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本模块时会发出
:class:`DeprecationWarning`。**新代码请写** ``from zmlx.algs.sys import ...``。

Modified by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn


warn(
    '``zmlx.alg.sys`` 已弃用（2026-10-16）：算法包已改名为 ``zmlx.algs``；'
    '本转发层将于 **2027-10-16** 删除。请改用 ``from zmlx.algs.sys import ...``。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.algs.sys import *  # noqa: F401,F403
from zmlx.algs.sys import (  # noqa: F401
    add_pth_file,
    conda_install,
    create_deprecated,
    create_shortcut,
    create_ui_lnk_on_desktop,
    get_city,
    get_deprecated,
    get_desktop_path,
    get_ipinfo,
    get_latest_version,
    get_pythonw_path,
    has_module,
    import_module,
    install_dep,
    is_conda_env,
    listdir,
    log_deprecated,
    pip_install,
    py2pyc,
    sbatch,
    srand,
    timing_show,
    type_assert,
    unique
)
