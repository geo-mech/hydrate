import os

from zml import gui


def edit_code(fname, warning=True):
    if gui.exists():
        gui.open_code(fname, warning=warning)


def new_code():
    if gui.exists():
        fname = gui.get_save_file_name(caption='新建.py脚本', directory=os.getcwd(),
                                       filter='Python File (*.py);;')
        edit_code(fname)


def exec_code_in_editing():
    if gui.exists():
        gui.exec_current()
