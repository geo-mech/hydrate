"""
界面模块。

在外部使用的时候，任何情况下，不要从此包的子模块中导入任何内容。所有允许被外部使用的内容
已经在此__init__中给定了。
"""

from zmlx.exts import SelfPath
from zmlx.ui.gui_buffer import (
    gui, information, question, plot, break_point, gui_exec, open_gui,
    open_gui_without_setup, progress, show_attrs)

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
