"""
用于程序的配置存储。这里所有函数均不抛出异常
"""

import os

from zml import app_data, read_text, write_text
from zmlx.alg.clamp import clamp
from zmlx.io.json_ex import read as read_json
from zmlx.ui.Qt import QtGui, QtCore, QtWidgets, is_PyQt6
from zmlx.ui.alg.screen import get_current_screen_geometry

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


# 默认搜索的图片扩展名
image_exts = ['.jpg', '.png']


def find_icon_file(name):
    try:
        for folder in reversed(find_all('zml_icons')):
            filepath = os.path.join(folder, name)
            if os.path.isfile(filepath):
                return filepath
            for ext in image_exts:
                filepath = os.path.join(folder, name + ext)
                if os.path.isfile(filepath):
                    return filepath
    except Exception as err:
        print(err)


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
    except Exception as err:
        print(err)
        return QtGui.QIcon()


sound_exts = ['.wav']


def find_sound(name):
    try:
        for folder in reversed(find_all('zml_sounds')):
            filepath = os.path.join(folder, name)
            if os.path.isfile(filepath):
                return filepath
            for ext in sound_exts:
                filepath = os.path.join(folder, name + ext)
                if os.path.isfile(filepath):
                    return filepath
    except Exception as err:
        print(err)


def play_sound(name):
    try:
        filepath = find_sound(name)
        if filepath is not None:
            from zmlx.ui.MainWindow import get_window
            window = get_window()
            if window is not None:
                window.play_sound(filepath)
    except Exception as err:
        print(err)


def play_click():
    play_sound('click')


def play_gallop():
    play_sound('gallop')


def play_ding():
    play_sound('ding')


def play_error():
    play_sound('error')


def save(key, value, encoding=None):
    write_text(path=temp(key), text=f'{value}', encoding=encoding)


def load(key, default='', encoding=None):
    return read_text(path=find(key), default=default, encoding=encoding)


def load_window_style(win, name, extra=''):
    try:
        value = load(name, default='', encoding='utf-8')
        win.setStyleSheet(f'{value};{extra}')
    except Exception as err:
        print(err)


def set_default_geometry(win: QtWidgets.QMainWindow):
    try:
        rect = get_current_screen_geometry(win)
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        x += int(w / 8)
        y += int(h / 8)
        w = int(w * 3 / 4)
        h = int(h * 3 / 4)
        win.setGeometry(QtCore.QRect(x, y, w, h))
    except:
        pass


def set_saved_geometry(win: QtWidgets.QMainWindow, words):
    try:
        if len(words) >= 4:
            rect = get_current_screen_geometry(win)
            w_max = rect.width()
            h_max = rect.height()
            w = clamp(int(words[2]), w_max * 0.3, w_max * 0.8)
            h = clamp(int(words[3]), h_max * 0.3, h_max * 0.8)
            x = clamp(int(words[0]), w_max * 0.02, w_max * 0.98 - w)
            y = clamp(int(words[1]), h_max * 0.02, h_max * 0.98 - h)
            win.setGeometry(QtCore.QRect(int(x), int(y), int(w), int(h)))
    except:
        pass


def load_window_size(win: QtWidgets.QMainWindow):
    try:
        restore = app_data.getenv(key='restore_window_geometry',
                                  default='Yes',
                                  encoding='utf-8',
                                  ignore_empty=True) != 'No'
        if not restore:
            set_default_geometry(win)
            return
        name = 'main_window_size_PyQt6' if is_PyQt6 else 'main_window_size'
        words = app_data.getenv(name, encoding='utf-8', default='').split()
        if len(words) < 5:  # 文件错误
            set_default_geometry(win)
            return
        if words[4] == 'True':  # 需要最大化显示
            set_default_geometry(win)
            win.showMaximized()
            return
        else:  # 恢复窗口
            set_saved_geometry(win, words)
            return
    except:
        set_default_geometry(win)


def save_window_size(win):
    try:
        assert isinstance(win, QtWidgets.QMainWindow)
        name = 'main_window_size_PyQt6' if is_PyQt6 else 'main_window_size'
        rc = win.geometry()
        app_data.setenv(name,
                        f'{rc.x()}  {rc.y()}  {rc.width()}  {rc.height()}  {win.isMaximized()}',
                        encoding='utf-8')
    except Exception as err:
        print(err)


def save_cwd():
    try:
        app_data.setenv('current_work_directory', os.getcwd(), encoding='utf-8')
    except Exception as err:
        print(err)


def load_cwd():
    try:
        os.chdir(app_data.getenv('current_work_directory', default=os.getcwd(), encoding='utf-8'))
    except Exception as err:
        print(err)
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
    except Exception as err:
        print(err)
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
    except Exception as err:
        print(err)


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
            if ext == '.py':
                files[filename] = os.path.join(path, filename)
    return files


try:
    code_in_editor = read_text(find('zml_code_in_editor.py'), encoding='utf-8',
                               default='')
except:
    code_in_editor = ''


def get_default_code():
    return code_in_editor
