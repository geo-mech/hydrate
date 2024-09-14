"""
用于程序的配置存储。这里所有函数均不抛出异常
"""

import os

from zml import app_data, read_text, write_text
from zmlx.alg.clamp import clamp
from zmlx.io.json_ex import read as read_json
from zmlx.ui.Qt import QtGui, QtWidgets, QtCore, QtMultimedia

try:
    app_data.add_path(os.path.join(os.path.dirname(__file__), 'data'))
except Exception as e:
    print(e)


def temp(name):
    return app_data.temp(name)


def get_paths():
    return app_data.get_paths()


def find(name):
    return app_data.find(name)


def find_all(name):
    return app_data.find_all(name)


def find_icon_file(name):
    try:
        for folder in reversed(find_all('zml_icons')):
            filepath = os.path.join(folder, name)
            if os.path.isfile(filepath):
                return filepath
    except Exception as err_2:
        print(err_2)


def load_pixmap(name):
    filepath = find_icon_file(name)
    if filepath is not None:
        return QtGui.QPixmap(filepath)


def load_icon(name):
    try:
        pixmap = load_pixmap(name)
        if pixmap is not None:
            icon = QtGui.QIcon()
            icon.addPixmap(pixmap, QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
            return icon
        else:
            return QtGui.QIcon()
    except Exception as err_2:
        print(err_2)
        return QtGui.QIcon()


def find_sound(name):
    try:
        for folder in reversed(find_all('zml_sounds')):
            filepath = os.path.join(folder, name)
            if os.path.isfile(filepath):
                return filepath
    except Exception as err_2:
        print(err_2)


def play_sound(name):
    try:
        filepath = find_sound(name)
        if filepath is not None:
            if QtMultimedia is not None:
                QtMultimedia.QSound.play(filepath)
    except Exception as err_2:
        print(err_2)


def play_click():
    play_sound('click.wav')


def play_gallop():
    play_sound('gallop.wav')


def play_ding():
    play_sound('ding.wav')


def play_error():
    play_sound('error.wav')


def save(key, value, encoding=None):
    write_text(path=temp(key), text=f'{value}', encoding=encoding)


def load(key, default='', encoding=None):
    return read_text(path=find(key), default=default, encoding=encoding)


def load_window_style(win, name, extra=''):
    try:
        value = load(name, default='', encoding='utf-8')
        win.setStyleSheet(f'{value};{extra}')
    except Exception as err_2:
        print(err_2)


def load_window_size(win, name):
    try:
        words = app_data.getenv(name, encoding='utf-8', default='').split()
        rect = QtWidgets.QDesktopWidget().availableGeometry()
        if len(words) == 2:
            w = clamp(int(words[0]), rect.width() * 0.2, rect.width() * 0.8)
            h = clamp(int(words[1]), rect.height() * 0.2, rect.height() * 0.8)
            win.resize(int(w), int(h))
        else:
            win.resize(int(rect.width() * 0.7), int(rect.height() * 0.7))
    except Exception as err_2:
        print(err_2)
        rect = QtWidgets.QDesktopWidget().availableGeometry()
        win.resize(int(rect.width() * 0.7), int(rect.height() * 0.7))


def save_window_size(win, name):
    try:
        app_data.setenv(name, f'{win.width()}  {win.height()}')
    except Exception as err_2:
        print(err_2)


def save_cwd():
    try:
        app_data.setenv('current_work_directory', os.getcwd(), encoding='utf-8')
    except Exception as err_2:
        print(err_2)


def load_cwd():
    try:
        os.chdir(app_data.getenv('current_work_directory', default=os.getcwd(), encoding='utf-8'))
    except Exception as err_2:
        print(err_2)
        save_cwd()


Priorities = {'HighestPriority': QtCore.QThread.Priority.HighestPriority,
              'HighPriority': QtCore.QThread.Priority.HighPriority,
              'IdlePriority': QtCore.QThread.Priority.IdlePriority,
              'InheritPriority': QtCore.QThread.Priority.InheritPriority,
              'LowestPriority': QtCore.QThread.Priority.LowestPriority,
              'LowPriority': QtCore.QThread.Priority.LowPriority,
              'NormalPriority': QtCore.QThread.Priority.NormalPriority,
              }


def priority_value(text):
    """
    根据文本来获得优先级
    """
    return Priorities.get(text, QtCore.QThread.Priority.LowPriority)


def load_priority():
    """
    应用内核的优先级。默认使用较低的优先级，以保证整个计算机运行的稳定
    """
    return app_data.getenv('console_priority', default='LowPriority', encoding='utf-8', ignore_empty=True)


def save_priority(value):
    app_data.setenv('console_priority', value, encoding='utf-8')


def load_ui_text():
    ui_text1 = {}
    try:
        for path in reversed(find_all('zml_text.json')):
            try:
                ui_text1.update(read_json(path, default={}))
            except Exception as err_3:
                print(err_3)
    except Exception as err_2:
        print(err_2)
    return ui_text1


ui_text = load_ui_text()


def get_text(key):
    try:
        if isinstance(key, str):
            return ui_text.get(key, key)
        if isinstance(key, list):
            return [get_text(elem) for elem in key]
        if isinstance(key, tuple):
            return tuple(get_text(list(key)))
        if isinstance(key, dict):
            texts = {}
            for x, y in key.items():
                texts[x] = get_text(y)
            return texts
        else:
            return key
    except Exception as err_2:
        print(err_2)


def get_menus():
    """
    返回所有预定义的菜单项目
    """
    menus = {}
    for file_name in find_all('zml_menus.json'):
        data = read_json(path=file_name, default={})
        if isinstance(data, dict):
            menus.update(data)
    return menus


def get_action_files():
    """
    返回所有的Action文件的路径
    """
    files = {}
    for path in reversed(find_all('zml_actions')):
        if path is None:
            continue
        if not os.path.isdir(path):
            continue
        for filename in os.listdir(path):
            name, ext = os.path.splitext(filename)
            if ext == '.txtpy':
                files[filename] = os.path.join(path, filename)
    return files


try:
    code_in_editor = read_text(find('zml_code_in_editor.txtpy'), encoding='utf-8',
                               default='')
except Exception as e:
    print(e)
    code_in_editor = ''


def get_default_code():
    return code_in_editor
