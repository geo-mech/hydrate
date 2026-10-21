"""旧模块名（兼容层）：``license_count`` -> :mod:`zmlx.ui.tabs.check_count_view`.

⚠️ **本模块只是一层转发**，真正的实现全在 ``check_count_view.py`` 里 ——
本文件除了下面那几行 import / 别名不该再有任何内容。

为什么留着而不删
----------------

**为兼容旧代码。** 2026-10-10 这次改名（控件 ``LicenseCount`` → ``CheckCountView``）
动了好几层名字，凡是外面还按旧名字引用它的地方，都应该继续能用：

1. ``from zmlx.ui.widgets.license_count import LicenseCount`` —— **旧类名照常可用**
   （本模块末尾把它指到新类上）；
2. ``from zmlx.ui.widgets.license_count import CheckCountView`` —— 旧模块名 + 新类名也行；
3. ``zmlx/exts/_lic.py`` 的模块文档里写着「判定与显示的实现见
   ``zmlx.ui.widgets.license_count``」，别的 ReadMe 也可能这么引 —— 留着这层，
   那些引用至少指得到、而且一眼能看出新名字是哪个。

⚠️ 新代码请用 ``from zmlx.ui.tabs import CheckCountView``（推荐）或
``from zmlx.ui.tabs.check_count_view import CheckCountView``。

⚠️ 名字的由来：旧名把**数据来源**（``check_count`` 那个接口）当成了控件本身，而
``check_count`` 查的是**被数出来的那些 check 的次数**、不是"授权检查"。新名是
「接口名去掉动词 + ``View``」，与兄弟控件 ``FeedbacksView``（← ``list_feedbacks``）
配成一对。

Created by DeepSeek, 2026-10-10

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn

warn(
    'zmlx.ui.widgets.license_count 已弃用（2026-10-16）：请改用 zmlx.ui.tabs.check_count_view；'
    '本兼容层将于 **2027-10-16** 删除。',
    DeprecationWarning,
    stacklevel=2,
)


from zmlx.ui.tabs.check_count_view import CheckCountView, parse_user_list  # noqa: F401
from zmlx.ui.tabs.check_count_view import *  # noqa: F401,F403

#: 旧类名 —— 留着只为兼容，新代码用 ``CheckCountView``
LicenseCount = CheckCountView