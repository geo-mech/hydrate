# -*- coding: utf-8 -*-


import os
import time

from zmlx.ui.CodeAlg import edit_code


def show_info(filepath):
    if not os.path.isfile(filepath):
        return
    try:
        print(f'File   Path: {filepath}')
        print(f'File   Size: {os.path.getsize(filepath) / (1024 * 1024)} Mb')
        print(f'Access Time: {time.ctime(os.path.getatime(filepath))}')
        print(f'Modify Time: {time.ctime(os.path.getmtime(filepath))}')
        print('\n\n')
    except:
        pass


def edit_py(filepath):
    if os.path.isfile(filepath):
        if os.path.splitext(filepath)[-1] == '.py':
            edit_code(filepath)


def show_fn2(filepath):
    from zml import gui
    gui.show_fn2(filepath)


def show_seepage(filepath):
    from zml import Seepage, app_data
    model = Seepage(path=filepath)
    app_data.put('seepage', model)
    print(model)


file_processors = {'.py': edit_py, '.fn2': show_fn2, '.seepage': show_seepage}
file_desc = {'.py': 'Python File To Execute', '.fn2': 'Fracture Network 2D', '.seepage': 'Seepage Model File'}


def get_extensions():
    result = []
    for key in file_processors.keys():
        desc = file_desc.get(key, key)
        result.append((key, desc))
    return result


def open_file(filepath):
    if not os.path.isfile(filepath):
        if os.path.isdir(filepath):
            from zml import gui
            win = gui.window()
            win.console_widget.set_cwd(filepath)
        return

    ext = os.path.splitext(filepath)[-1]
    if ext is None:
        print(f'Error: do not has extension: {filepath}')
        return

    assert isinstance(ext, str)
    ext = ext.lower()

    func = file_processors.get(ext)
    if func is None:
        return show_info(filepath)

    try:
        return func(filepath)
    except Exception as err:
        print(f'Error: filepath = {filepath} \nmessage = {err}')


def open_file_by_dlg(folder=None):
    from zml import gui
    import os

    temp = ''
    for ext, desc in get_extensions():
        temp = f'{temp}{desc} (*{ext});; '

    if folder is None:
        folder = ''

    filepath = gui.get_open_file_name('please choose the file to open', folder, f'{temp}All File(*.*)')
    if os.path.isfile(filepath):
        open_file(filepath)
