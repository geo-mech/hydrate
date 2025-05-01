import warnings

from zmlx.ui.gui_buffer import *

__all__ = ['information', 'question', 'plot', 'break_point', 'gui_exec',
           'GuiBuffer', 'gui']

warnings.warn(f'The module {__name__} is deprecated (remove after 2026-4-15), '
              f'please use zmlx.ui.gui_buffer instead.',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)




