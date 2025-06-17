
def open_gui(argv=None):
    """
    打开gui
    """
    from zmlx.ui.gui_buffer import gui
    gui.execute(keep_cwd=False, close_after_done=False)


def open_gui_without_setup(argv=None):
    """
    打开gui
    """
    from zmlx.ui.gui_buffer import gui
    gui.execute(keep_cwd=False, close_after_done=False, run_setup=False)


if __name__ == "__main__":
    import sys

    open_gui(sys.argv)
