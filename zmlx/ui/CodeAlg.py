import os
from zml import app_data
from zml import gui


def edit_code(fname):
    if gui.exists():
        gui.open_code(fname)


def new_code():
    if gui.exists():
        fname = gui.get_save_file_name(caption='新建.py脚本', directory=os.getcwd(),
                                       filter='Python File (*.py);;')
        edit_code(fname)


def exec_code_in_editing():
    main_window = app_data.space.get('main_window', None)
    if main_window is not None:
        main_window.exec_current()
