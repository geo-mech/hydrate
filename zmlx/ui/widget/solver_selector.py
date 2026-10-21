"""旧模块名（兼容层，**已弃用**）：``solver_selector`` -> :mod:`zmlx.ui.plugins.builtin.solver_menu`.

⚠️ **本模块只是一层转发**，真正的实现（``SolverSelector`` / ``SOLVER_META`` /
``PARAM_DEFS``）现在在插件 ``zmlx/ui/plugins/builtin/solver_menu.py`` 里 —— 本文件除了
下面那几行 import / 别名不该再有任何内容。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本模块时
会发出 :class:`DeprecationWarning`。**新代码请写**
``from zmlx.ui.plugins.builtin.solver_menu import SolverSelector``
（⚠️ 那是**插件内部**的路径，正常业务代码不需要直接造 ``SolverSelector`` ——
打开求解器面板请调 ``gui.show_solver_selector()``）。

搬了几次 / 为什么留着
--------------------

2026-10-16 把「**顶层控件**」集中迁到 ``zmlx/ui/tabs/``；2026-10-22 又把
``SolverSelector`` 连同 ``show_solver_selector`` 一起并入插件「求解器」（搬走后它只剩
那个插件在用 —— 「可关掉的功能，它的代码也应当能一起关掉」）。本垫片随之改指新位置，
老路径继续可用。

⚠️ 这条路径仍被三类来源用着，故留一年过渡：① 外部脚本与用户在控制台敲的命令；
② 历史标签页的 ``gui_restore``（重启时按存下来的字符串重放）；③ 更早的兼容层
（``license_count`` / ``license_feedback``）。

⚠️ **本模块现在是** ``ui`` → ``plugins`` 的**逆向 import**（同 ``widget/img.py`` /
``widget/demo_view.py``）：只允许出现在兼容层，正常代码不要效仿。

⚠️ 判据与依赖方向见 ``zmlx/ui/tabs/AGENTS.md``。

Created by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
Modified by DeepSeek, 2026-10-22: 目标改为插件 ``plugins/builtin/solver_menu.py`` ——
    ``SolverSelector`` 随 ``show_solver_selector`` 并入了「求解器」插件
"""
from zmlx.system import warn


warn(
    '``zmlx.ui.widgets.solver_selector`` 已弃用（2026-10-16）：控件 ``SolverSelector`` 已迁至插件 '
    '``zmlx.ui.plugins.builtin.solver_menu``（2026-10-22 起）；本转发层将于 '
    '**2027-10-16** 删除。打开求解器面板请用 ``gui.show_solver_selector()``。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.ui.plugins.builtin.solver_menu import (  # noqa: F401
    PARAM_DEFS,
    SOLVER_META,
    SolverSelector,
)

__all__ = ['PARAM_DEFS', 'SOLVER_META', 'SolverSelector']
