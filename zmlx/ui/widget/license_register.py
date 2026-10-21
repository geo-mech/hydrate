"""旧模块名（兼容层，**已弃用**）：``license_register`` -> :mod:`zmlx.ui.tabs.license_register`.

⚠️ **本模块只是一层转发**，真正的实现全在 ``zmlx/ui/tabs/license_register.py`` 里 ——
本文件除了下面那几行 import / 别名不该再有任何内容。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本模块时
会发出 :class:`DeprecationWarning`。**新代码请写** ``from zmlx.ui.tabs import LicenseRegister``
（或 ``from zmlx.ui.tabs.license_register import LicenseRegister``）。

为什么留着而不删
----------------

2026-10-16 把「**顶层控件**」（只被装配层打开成一个标签页、**不会被任何控件当组件
（子控件）用**）集中迁到 ``zmlx/ui/tabs/``；本目录只留**底层控件**（会被
``addWidget()`` 进别处的、或被继承的）以及宿主不是标签页的常驻控件（状态栏按钮 /
右侧栏面板 / 标签容器 / 对话框组件集）。

但 ``from zmlx.ui.widgets.license_register import LicenseRegister`` 这条路径仍被三类来源用着，故留一年过渡：
① 外部脚本与用户在控制台敲的命令；② 历史标签页的 ``gui_restore``（重启时按存下来的
字符串重放）；③ 更早的兼容层（``license_count`` / ``license_feedback``）。

⚠️ 判据与依赖方向见 ``zmlx/ui/tabs/AGENTS.md``。

Created by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn


warn(
    '``zmlx.ui.widgets.license_register`` 已弃用（2026-10-16）：控件 ``LicenseRegister`` 已迁至 '
    '``zmlx.ui.tabs.license_register``；本转发层将于 **2027-10-16** 删除。'
    '请改用 ``from zmlx.ui.tabs import LicenseRegister``。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.ui.tabs.license_register import *  # noqa: F401,F403
from zmlx.ui.tabs.license_register import (  # noqa: F401
    BANNER_QSS,
    BUTTON_HEIGHT,
    GAP,
    LicenseRegister,
    MARGIN,
    STATUS_VIEW_HEIGHT,
    explain_failure,
)

# ⚠️ 这几个名字在更早那次重构里被**下沉**到 ``zmlx.ui.utils.lic_utils``
#    （license_register 与 check_count_view 都要用，横向互借违反分层）。
#    但当时只改了新家的导出、没管旧路径 —— 老 import 因此断掉。
#    经实测（T0 = a7a24b404）这些名字原先是可取到的，属**真回归**，故在此补回。
from zmlx.ui.utils.lic_utils import (  # noqa: F401
    DETAIL_SEP,
    ELAPSED_SEP,
    PURPOSE_REGISTER,
    SOURCE_TAG,
    SUCCESS_BOUND,
    SUCCESS_SENT,
    is_bound_to_email,
    source_of,
)

# ⚠️ 基准里这几个是**标准库直接 import**（`import time` / `import warnings`），
#    于是 `zmlx.ui.widget.license_register.time` 这类老路径原本取得到。
#    审计实测确认过，故按原样补 —— 注意是 import 标准库，不是从目标模块取。
import time  # noqa: F401
