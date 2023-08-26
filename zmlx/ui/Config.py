"""
用于程序的配置存储。这里所有函数均不抛出异常
"""

import os
from PyQt5 import QtGui, QtWidgets, QtCore

try:
    from PyQt5 import QtMultimedia
except:
    QtMultimedia = None
    pass

from zmlx.ui.alg.write_text import write_text
from zmlx.ui.alg.read_text import read_text
from zmlx.ui.alg.read_json import read_json
from zmlx.ui.alg.clamp import clamp
from zml import app_data

try:
    app_data.add_path(os.path.join(os.path.dirname(__file__), 'data'))
except:
    pass


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
    except:
        pass


def load_icon(name):
    try:
        pixmap = load_pixmap(name)
        if pixmap is not None:
            icon = QtGui.QIcon()
            icon.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
            return icon
        else:
            return QtGui.QIcon()
    except:
        return QtGui.QIcon()


def find_sound(name):
    try:
        for folder in reversed(find_all('zml_sounds')):
            filepath = os.path.join(folder, name)
            if os.path.isfile(filepath):
                return filepath
    except:
        pass


def play_sound(name):
    try:
        filepath = find_sound(name)
        if filepath is not None:
            if QtMultimedia is not None:
                QtMultimedia.QSound.play(filepath)
    except:
        pass


def play_click():
    play_sound('click.wav')


def play_gallop():
    play_sound('gallop.wav')


def play_ding():
    play_sound('ding.wav')


def play_error():
    play_sound('Windows Error.wav')


def save(key, value, encoding=None):
    write_text(path=temp(key), text=f'{value}', encoding=encoding)


def load(key, default='', encoding=None):
    return read_text(path=find(key), default=default, encoding=encoding)


def load_window_style(win, name, extra=''):
    try:
        value = load(name, default='', encoding='UTF-8')
        win.setStyleSheet(f'{value};{extra}')
    except:
        pass


def load_window_size(win, name):
    try:
        words = app_data.getenv(name, encoding='utf-8', default='').split()
        rect = QtWidgets.QDesktopWidget().availableGeometry()
        if len(words) == 2:
            w = clamp(int(words[0]), rect.width() * 0.4, rect.width() * 0.8)
            h = clamp(int(words[1]), rect.height() * 0.4, rect.height() * 0.8)
            win.resize(int(w), int(h))
        else:
            win.resize(int(rect.width() * 0.8), int(rect.height() * 0.8))
    except:
        rect = QtWidgets.QDesktopWidget().availableGeometry()
        win.resize(int(rect.width() * 0.8), int(rect.height() * 0.8))


def save_window_size(win, name):
    try:
        app_data.setenv(name, f'{win.width()}  {win.height()}')
    except:
        pass


def save_cwd():
    try:
        app_data.setenv('current_work_directory', os.getcwd(), encoding='utf-8')
    except:
        pass


def load_cwd():
    try:
        os.chdir(app_data.getenv('current_work_directory', default=os.getcwd(), encoding='utf-8'))
    except:
        save_cwd()


Priorities = {'HighestPriority': QtCore.QThread.HighestPriority,
              'HighPriority': QtCore.QThread.HighPriority,
              'IdlePriority': QtCore.QThread.IdlePriority,
              'InheritPriority': QtCore.QThread.InheritPriority,
              'LowestPriority': QtCore.QThread.LowestPriority,
              'LowPriority': QtCore.QThread.LowPriority,
              'NormalPriority': QtCore.QThread.NormalPriority,
              }


def priority_value(text):
    """
    根据文本来获得优先级
    """
    return Priorities.get(text, QtCore.QThread.LowPriority)


def load_priority():
    """
    应用内核的优先级。默认使用较低的优先级，以保证整个计算机运行的稳定
    """
    return app_data.getenv('console_priority', default='LowPriority', encoding='utf-8')


def save_priority(value):
    app_data.setenv('console_priority', value, encoding='utf-8')


def load_ui_text():
    ui_text1 = {}
    try:
        for path in reversed(find_all('zml_text.json')):
            try:
                ui_text1.update(read_json(path, default={}))
            except:
                pass
    except:
        pass
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
    except:
        pass


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
            if filename == '__init__.py':
                continue
            name, ext = os.path.splitext(filename)
            if ext == '.py' or ext == '.pyw':
                files[filename] = os.path.join(path, filename)
    return files


try:
    code_in_editor = read_text(find('zml_code_in_editor.py'), encoding='utf-8',
                               default='')
except:
    code_in_editor = ''


def get_default_code():
    return code_in_editor
