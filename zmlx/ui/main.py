import sys


def init():
    try:
        from zmlx.io.python import read_py
        from zml import app_data
        from zmlx.ui import gui
        if app_data.getenv('restore_tabs', default='Yes', ignore_empty=True) == 'Yes':
            filename = app_data.temp('tab_start_code.json')
            data = read_py(filename)
            for text in data:
                try:
                    exec(text, {'gui': gui})
                except Exception as err:
                    print(err)
    except:
        pass

    try:
        from zmlx.ui.MainWindow import get_window
        setattr(get_window(), 'tabs_should_be_saved', 1)
    except:
        pass

    try:
        from zmlx.ui.MainWindow import get_window
        from zml import app_data
        if app_data.getenv('show_readme', default='Yes', ignore_empty=True) == 'Yes':
            window = get_window()
            if window.count_tabs() == 0:
                window.trigger('readme.txtpy')
    except Exception as e:
        print(f'Error: {e}')

    try:
        from zml import get_dir
        from zmlx.alg.is_chinese import is_chinese
        if is_chinese(get_dir()):
            from zmlx.ui import gui
            gui.toolbar_warning('提醒：请务必将程序安装在纯英文路径下')
    except Exception as e:
        print(f'Error: {e}')


def open_gui(argv=None):
    """
    打开gui; 将首先尝试安装依赖项.
    """
    from zmlx.ui.GuiBuffer import gui
    gui.execute(init, keep_cwd=False, close_after_done=False)


if __name__ == "__main__":
    open_gui(sys.argv)
