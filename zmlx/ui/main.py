def init():
    try:
        from zmlx.ui.main_window import get_window
        from zml import app_data
        if app_data.getenv('show_readme', default='Yes',
                           ignore_empty=True) == 'Yes':
            window = get_window()
            if window.count_tabs() == 0:
                window.trigger('readme')
    except Exception as e:
        print(f'Error: {e}')


def open_gui(argv=None):
    """
    打开gui
    """
    from zmlx.ui.gui_buffer import gui
    gui.execute(init, keep_cwd=False, close_after_done=False)


def open_gui_without_setup(argv=None):
    """
    打开gui
    """
    from zmlx.ui.gui_buffer import gui
    gui.execute(init, keep_cwd=False, close_after_done=False, run_setup=False)


if __name__ == "__main__":
    import sys

    open_gui(sys.argv)
