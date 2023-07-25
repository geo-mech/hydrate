# -*- coding: utf-8 -*-
"""
用于程序的配置存储。这里所有函数均不抛出异常
"""

import os
import warnings
from PyQt5 import QtGui, QtWidgets, QtCore

try:
    from PyQt5 import QtMultimedia
except Exception as err:
    QtMultimedia = None
    warnings.warn(f'error import QtMultimedia. error = {err}, may not play sound')

from zml import app_data, read_text
from zmlx.alg.json_ex import read as read_json

try:
    app_data.add_path(os.path.join(os.path.dirname(__file__), 'data'))
except Exception as err:
    warnings.warn(f'error when add <zmlx.ui.data> to search path. error = {err}')


def temp(name):
    return app_data.temp(name)


def get_paths():
    return app_data.get_paths()


def find(name):
    return app_data.find(name)


def find_all(name):
    return app_data.find_all(name)


def load_pixmap(name):
    try:
        for folder in reversed(find_all('zml_icons')):
            filepath = os.path.join(folder, name)
            if os.path.isfile(filepath):
                return QtGui.QPixmap(filepath)
    except Exception as e:
        warnings.warn(f'error load pixmap. name = {name}. error = {e}')


def load_icon(name):
    try:
        pixmap = load_pixmap(name)
        if pixmap is not None:
            icon = QtGui.QIcon()
            icon.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
            return icon
        else:
            return QtGui.QIcon()
    except Exception as e:
        warnings.warn(f'error load icon. name = {name}. error = {e}')
        return QtGui.QIcon()


def find_sound(name):
    try:
        for folder in reversed(find_all('zml_sounds')):
            filepath = os.path.join(folder, name)
            if os.path.isfile(filepath):
                return filepath
    except Exception as e:
        warnings.warn(f'error find sound. name = {name}. error = {e}')


def play_sound(name):
    try:
        filepath = find_sound(name)
        if filepath is not None:
            if QtMultimedia is not None:
                QtMultimedia.QSound.play(filepath)
    except Exception as e:
        warnings.warn(f'error play sound. name = {name}. error = {e}')


def play_click():
    play_sound('click.wav')


def play_gallop():
    play_sound('gallop.wav')


def play_ding():
    play_sound('ding.wav')


def play_error():
    play_sound('Windows Error.wav')


def save(key, value, encoding=None):
    try:
        with open(temp(key), 'w', encoding=encoding) as file:
            file.write(f'{value}')
    except Exception as e:
        warnings.warn(f'error save. key = {key}. value = {value}. encoding = {encoding}, error = {e}')


def load(key, value='', encoding=None):
    try:
        with open(find(key), 'r', encoding=encoding) as file:
            return file.read()
    except Exception as e:
        warnings.warn(f'error load. key = {key}. value = {value}. encoding = {encoding}, error = {e}')


def load_window_style(win, name, extra=''):
    try:
        value = load(name, '', encoding='UTF-8')
        win.setStyleSheet(f'{value};{extra}')
    except Exception as e:
        warnings.warn(f'error load window style. name = {name}. error = {e}')


def load_window_size(win, name):
    try:
        words = app_data.getenv(name, encoding='UTF-8').split()
        if len(words) == 2:
            rect = QtWidgets.QDesktopWidget().availableGeometry()
            w = int(words[0])
            h = int(words[1])
            w = max(rect.width() * 0.4, min(w, rect.width() * 0.8))
            h = max(rect.height() * 0.4, min(h, rect.height() * 0.8))
            win.resize(int(w), int(h))
            return
    except Exception as e:
        rect = QtWidgets.QDesktopWidget().availableGeometry()
        win.resize(rect.width() * 0.7, rect.height() * 0.7)
        warnings.warn(f'error load window size. error = {e}')


def save_window_size(win, name):
    try:
        app_data.setenv(name, f'{win.width()}  {win.height()}')
    except Exception as e:
        warnings.warn(f'error save window size. name = {name}. error = {e}')


def save_cwd():
    try:
        app_data.setenv('current_work_directory', os.getcwd(), encoding='utf-8')
    except Exception as e:
        warnings.warn(f'error save cwd. error = {e}')


def load_cwd():
    try:
        os.chdir(app_data.getenv('current_work_directory', default=os.getcwd(), encoding='utf-8'))
    except Exception as e:
        save_cwd()
        warnings.warn(f'error load cwd. error = {e}')


def load_console_priority():
    """
    应用内核的优先级。默认使用较低的优先级，以保证整个计算机运行的稳定
    """
    try:
        return int(app_data.getenv('console_priority', default=f'{QtCore.QThread.LowPriority}'))
    except Exception as e:
        warnings.warn(f'error load console priority. error = {e}')
        return QtCore.QThread.LowPriority


def save_console_priority(value):
    try:
        app_data.setenv('console_priority', f'{value}')
    except Exception as e:
        warnings.warn(f'error save console priority. error = {e}')


def get_priority_text(value):
    try:
        if value == QtCore.QThread.HighestPriority:
            return 'HighestPriority'

        if value == QtCore.QThread.HighPriority:
            return 'HighPriority'

        if value == QtCore.QThread.IdlePriority:
            return 'IdlePriority'

        if value == QtCore.QThread.InheritPriority:
            return 'InheritPriority'

        if value == QtCore.QThread.LowestPriority:
            return 'LowestPriority'

        if value == QtCore.QThread.LowPriority:
            return 'LowPriority'

        if value == QtCore.QThread.NormalPriority:
            return 'NormalPriority'

        if value == QtCore.QThread.TimeCriticalPriority:
            return 'TimeCriticalPriority'
    except Exception as e:
        warnings.warn(f'error get priority text. text = {value}. error = {e}')


def load_ui_text():
    ui_text1 = {}
    try:
        for path in reversed(find_all('zml_text.json')):
            try:
                ui_text1.update(read_json(path, default={}))
            except Exception as e:
                warnings.warn(f'error load ui text. path = {path}. error = {e}')
    except Exception as e2:
        warnings.warn(f'error load ui text. error = {e2}')
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
    except Exception as e:
        warnings.warn(f'error get text. key = {key}. error = {e}')


def get_menus():
    """
    返回所有预定义的菜单项目
    """
    menus = []
    for file_name in find_all('zml_menus.json'):
        data = read_json(path=file_name, default=[])
        for m in data:
            menus.append(m)
    return menus


def get_action_files():
    """
    返回所有的Action文件的路径
    """
    files = {}
    for path in reversed(find_all('zml_actions')):
        if path is not None and os.path.isdir(path):
            for filename in os.listdir(path):
                name, ext = os.path.splitext(filename)
                if ext == '.py' or ext == '.pyw':
                    files[filename] = os.path.join(path, filename)
    return files


try:
    code_in_editor = read_text(find('zml_code_in_editor.py'), encoding='utf-8',
                               default='')
except Exception as err:
    code_in_editor = ''
    warnings.warn(f'error read zml_code_in_editor.py. error = {err}')


def get_default_code():
    return code_in_editor
