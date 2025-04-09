def is_running():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is not None:
        return window.is_running()
    else:
        return False


def start_func(code):
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is not None:
        if not window.is_running():
            window.start_func(code)


def status(*args, **kwargs):
    """
    显示状态信息。参数同status_bar.showMessage函数
    Args:
        *args:
        **kwargs:

    Returns:
        None
    """
    try:
        from zmlx.ui.main_window import get_window
        window = get_window()
        if window is not None:
            window.cmd_status(*args, **kwargs)
    except:
        pass


def show_txt(filepath):
    try:
        from zml import read_text
        from zmlx.alg.fsys import get_size_mb, show_fileinfo
        if get_size_mb(filepath) < 0.5:
            from zmlx.ui.main_window import get_window
            window = get_window()
            if window is not None:
                window.open_text(filepath)
            else:
                print(f'{filepath}:\n\n')
                print(read_text(path=filepath, encoding='utf-8'))
                print('\n')
        else:
            show_fileinfo(filepath)
    except:
        pass


def edit_code(fname):
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is not None:
        window.open_code(fname)


def new_code():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is not None:
        from zmlx.ui.pyqt import QtWidgets
        import os
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            window,
            caption='新建.py脚本',
            directory=os.getcwd(),
            filter='Python File (*.py);;')
        edit_code(fname)


def exec_code_in_editing():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is not None:
        window.exec_current()
