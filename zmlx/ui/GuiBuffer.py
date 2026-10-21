"""已弃用的模块，请改用 zmlx.ui.gui_buffer（或直接从 zmlx 导入）.

⚠️ **本模块是兼容垫片，将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。

为什么留着而不删
----------------

2026-10-16 做过一次「检查是否还有人引用」并删除了本模块 —— 但那次只在
**zmlx 本仓**内搜索，没查到**外部项目**。事后核对 `igg-hydrate-works` 发现
**2 个项目共 12 处**仍在用：

    from zmlx.ui.GuiBuffer import gui

（methane-hydrate、other-works 等）

⚠️ 教训：**「本仓没人引用」不等于「没人引用」** —— 删任何「已弃用」模块之前，
   必须连外部工作区一起搜。

⚠️ 注意本文件名是 **大写 G**（`GuiBuffer.py`），而真实现是小写
   （`gui_buffer.py`）。两者在 Windows 上**无法共存**（文件名大小写不敏感），
   所以在大小写敏感的系统上会同时存在两份 —— 这正是它当初能作为垫片存在的原因，
   也是它在 Windows 工作区里「看不见」的原因。

Modified by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn

warn(f'The module {__name__} is deprecated (remove after 2027-10-16), '
              f'please import from zmlx instead.',
              DeprecationWarning, stacklevel=2)

from zmlx.ui.gui_buffer import *  # noqa: F401,F403
from zmlx.ui.gui_buffer import (  # noqa: F401
    GuiBuffer,
    break_point,
    gui,
    gui_exec,
    information,
    plot,
    question,
)

__all__ = ['information', 'question', 'plot', 'break_point', 'gui_exec',
           'GuiBuffer', 'gui']
