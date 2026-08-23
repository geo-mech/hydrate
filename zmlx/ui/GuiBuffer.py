"""已弃用的模块，请改用 zmlx.ui.gui_buffer（或直接从 zmlx 导入）."""

import zmlx.alg.sys as warnings

from zmlx.ui.gui_buffer import *

__all__ = ['information', 'question', 'plot', 'break_point', 'gui_exec',
           'GuiBuffer', 'gui']

warnings.warn(f'The module {__name__} is deprecated (remove after 2026-4-15), '
              f'please import from zmlx instead.',
              DeprecationWarning, stacklevel=2)
