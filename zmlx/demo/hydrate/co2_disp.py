"""旧模块名（兼容层，**已弃用**）：``hydrate.co2_disp`` -> :mod:`zmlx.demos.hydrate.co2_disp`.

⚠️ **本模块只是一层转发**，真正的实现在 ``zmlx/demos/hydrate/co2_disp.py``。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。

⚠️ **为什么 demo 只恢复了这 2 个模块**：``zmlx/demos/`` 下绝大多数是**顶层的可运行案例**，
不是给人 import 的库代码（实测 154 个模块里只有 4 个被 import 过）。所以这里**不**为
那 150 个案例建转发 —— 只有**确实被外部项目用到**的才补：

    from zmlx.demo.hydrate.co2_disp import execute   # methane-hydrate
    from zmlx.demo.opath import opath                # productivity

⚠️ 完整的兼容策略见 ``zmlx/demo/__init__.py``。

Modified by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn

warn(
    '``zmlx.demo.hydrate.co2_disp`` 已弃用（2026-10-16）：请改用 ``zmlx.demos.hydrate.co2_disp``；'
    '本转发层将于 **2027-10-16** 删除。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.demos.hydrate.co2_disp import *  # noqa: F401,F403

from zmlx.demos.hydrate.co2_disp import (  # noqa: F401
    GuiIterator,
    Seepage,
    Tensor3,
    add_cell_face,
    create,
    create_xz_half,
    execute,
    get_gui_iter,
    opath,
    solve,
    tfc,
    timer,
)
