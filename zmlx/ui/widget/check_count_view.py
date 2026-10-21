"""旧模块名（兼容层，**已弃用**）：``check_count_view`` -> :mod:`zmlx.ui.tabs.check_count_view`.

⚠️ **本模块只是一层转发**，真正的实现全在 ``zmlx/ui/tabs/check_count_view.py`` 里 ——
本文件除了下面那几行 import / 别名不该再有任何内容。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本模块时
会发出 :class:`DeprecationWarning`。**新代码请写** ``from zmlx.ui.tabs import CheckCountView``
（或 ``from zmlx.ui.tabs.check_count_view import CheckCountView``）。

为什么留着而不删
----------------

2026-10-16 把「**顶层控件**」（只被装配层打开成一个标签页、**不会被任何控件当组件
（子控件）用**）集中迁到 ``zmlx/ui/tabs/``；本目录只留**底层控件**（会被
``addWidget()`` 进别处的、或被继承的）以及宿主不是标签页的常驻控件（状态栏按钮 /
右侧栏面板 / 标签容器 / 对话框组件集）。

但 ``from zmlx.ui.widgets.check_count_view import CheckCountView`` 这条路径仍被三类来源用着，故留一年过渡：
① 外部脚本与用户在控制台敲的命令；② 历史标签页的 ``gui_restore``（重启时按存下来的
字符串重放）；③ 更早的兼容层（``license_count`` / ``license_feedback``）。

⚠️ 判据与依赖方向见 ``zmlx/ui/tabs/AGENTS.md``。

Created by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn


warn(
    '``zmlx.ui.widgets.check_count_view`` 已弃用（2026-10-16）：控件 ``CheckCountView`` 已迁至 '
    '``zmlx.ui.tabs.check_count_view``；本转发层将于 **2027-10-16** 删除。'
    '请改用 ``from zmlx.ui.tabs import CheckCountView``。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.ui.tabs.check_count_view import *  # noqa: F401,F403
from zmlx.ui.tabs.check_count_view import (  # noqa: F401
    BANNER_QSS,
    BUTTON_HEIGHT,
    CHART_BAR_RATIO,
    CHART_EXPORT_DPI,
    CHART_HINT_HEIGHT,
    CHART_MARGIN,
    CHART_MAX_TICKS,
    CHART_MAX_VALUE_LABELS,
    CHART_MIN_HEIGHT,
    COUNT_TAG,
    CheckCountView,
    DATE_FORMAT,
    DAY_CHOICES,
    DEFAULT_DAYS,
    DETAIL_SEP,
    EMAIL_PLACEHOLDER,
    GAP,
    LIST_MIN_HEIGHT,
    LIST_WIDTH,
    MARGIN,
    RANGE_TAG,
    STATUS_VIEW_HEIGHT,
    days_ago_str,
    is_count_reply,
    parse_count_reply,
    today_str
)

# ⚠️ 这几个名字在更早那次重构里被**下沉**到 ``zmlx.ui.utils.lic_utils``
#    （license_register 与 check_count_view 都要用，横向互借违反分层）。
#    但当时只改了新家的导出、没管旧路径 —— 老 import 因此断掉。
#    经实测（T0 = a7a24b404）这些名字原先是可取到的，属**真回归**，故在此补回。
from zmlx.ui.utils.lic_utils import (  # noqa: F401
    LIST_TAG,
    USER_LIST_TAG,
    looks_like_email,
)
