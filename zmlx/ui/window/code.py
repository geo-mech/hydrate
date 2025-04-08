import os

from zmlx.ui.Qt import QtWidgets


def edit_code(fname):
    from zmlx.ui.MainWindow import get_window
    window = get_window()
    if window is not None:
        window.open_code(fname)


def new_code():
    from zmlx.ui.MainWindow import get_window
    window = get_window()
    if window is not None:
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(window,
                                                         caption='新建.py脚本',
                                                         directory=os.getcwd(),
                                                         filter='Python File (*.py);;')
        edit_code(fname)


def exec_code_in_editing():
    from zmlx.ui.MainWindow import get_window
    window = get_window()
    if window is not None:
        window.exec_current()
