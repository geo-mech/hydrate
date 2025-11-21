"""
界面模块。

在外部使用的时候，任何情况下，不要从此包的子模块中导入任何内容。所有允许被外部使用的内容
已经在此__init__中给定了。
"""

from zmlx.ui.gui_buffer import (
    gui, information, question, plot, break_point, gui_exec, open_gui,
    open_gui_without_setup)


def get_path(*args):
    """
    返回数据目录
    """
    import os
    from zmlx.base.zml import make_parent
    from zmlx.alg.fsys import join_paths
    return make_parent(join_paths(os.path.dirname(__file__), *args))
