from zmlx.ui.gui_buffer import gui
from zml import app_data


def open_gui(argv=None):
    """
    打开gui
    """
    app_data.put('restore_tabs', True)
    gui.execute(keep_cwd=False, close_after_done=False)


def open_gui_without_setup(argv=None):
    """
    打开gui
    """
    app_data.put('restore_tabs', True)
    app_data.put('run_setup', False)
    gui.execute(keep_cwd=False, close_after_done=False)


if __name__ == "__main__":
    import sys

    open_gui(sys.argv)
