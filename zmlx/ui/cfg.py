"""
用于程序的配置存储。这里所有函数均不抛出异常
"""

import os

from zml import app_data, read_text, write_text
from zmlx import clamp
from zmlx.io.json_ex import read as read_json
from zmlx.ui.alg import get_current_screen_geometry
from zmlx.ui.pyqt import QtGui, QtCore, QtWidgets, is_PyQt6

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
            icon.addPixmap(pixmap, QtGui.QIcon.Mode.Normal,
                           QtGui.QIcon.State.Off)
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
            from zmlx.ui.main_window import get_window
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


def _intersection_area(rect1, rect2):
    # 计算x轴的交叠范围
    left = max(rect1.x(), rect2.x())
    right = min(rect1.x() + rect1.width(), rect2.x() + rect2.width())
    overlap_width = right - left

    # 计算y轴的交叠范围
    top = max(rect1.y(), rect2.y())
    bottom = min(rect1.y() + rect1.height(), rect2.y() + rect2.height())
    overlap_height = bottom - top

    # 判断是否有交叠并计算面积
    if overlap_width > 0 and overlap_height > 0:
        return overlap_width * overlap_height
    else:
        return 0


def _adjust_window(rect1, rect2):
    # 初始位置调整（保持原尺寸）
    new_x = clamp(rect2.x(), rect1.x(), rect1.right() - rect2.width() + 1)
    new_y = clamp(rect2.y(), rect1.y(), rect1.bottom() - rect2.height() + 1)
    adjusted_rect = QtCore.QRect(new_x, new_y, rect2.width(), rect2.height())

    # 若调整后完全在内部，直接返回
    if rect1.contains(adjusted_rect):
        return adjusted_rect

    # 需要缩小尺寸并调整位置
    new_width, new_height = rect2.width(), rect2.height()
    final_x, final_y = new_x, new_y

    # 调整宽度（若超过屏幕宽度）
    if rect2.width() > rect1.width():
        new_width = rect1.width()
        original_center_x = rect2.x() + rect2.width() // 2
        final_x = original_center_x - new_width // 2
        final_x = clamp(final_x, rect1.x(), rect1.right() - new_width + 1)

    # 调整高度（若超过屏幕高度）
    if rect2.height() > rect1.height():
        new_height = rect1.height()
        original_center_y = rect2.y() + rect2.height() // 2
        final_y = original_center_y - new_height // 2
        final_y = clamp(final_y, rect1.y(), rect1.bottom() - new_height + 1)

    # 最终位置修正（确保在边界内）
    final_x = clamp(final_x, rect1.x(), rect1.right() - new_width + 1)
    final_y = clamp(final_y, rect1.y(), rect1.bottom() - new_height + 1)

    return QtCore.QRect(final_x, final_y, new_width, new_height)


def _scale_rect_around_center(rect, scale: float):
    """返回一个中心与原矩形相同，大小缩放 scale 倍的新矩形。

    参数:
        rect: 原始矩形（PyQt6.QtCore.QRect）
        scale: 缩放比例（例如 0.5 表示缩小一半，2.0 表示放大一倍）

    返回:
        QRect: 缩放后的新矩形
    """
    # 获取原矩形的中心坐标
    center = rect.center()

    # 计算新尺寸（四舍五入到最近的整数）
    new_width = round(rect.width() * scale)
    new_height = round(rect.height() * scale)

    # 计算新矩形左上角坐标（保持中心不变）
    new_x = round(center.x() - new_width / 2)
    new_y = round(center.y() - new_height / 2)

    # 创建并返回新矩形
    return QtCore.QRect(new_x, new_y, new_width, new_height)


def _set_default_geometry(win: QtWidgets.QMainWindow, w=None, h=None):
    try:
        rect = get_current_screen_geometry(win)
        # 首先，确定宽度和高度
        if w is None:
            w = int(rect.width() * 0.75)
        else:
            w = clamp(int(w), int(rect.width() * 0.3), int(rect.width() * 0.9))
        if h is None:
            h = int(rect.height() * 0.75)
        else:
            h = clamp(int(h), int(rect.height() * 0.3),
                      int(rect.height() * 0.9))
        # 再根据此确定位置.
        x = rect.x() + int((rect.width() - w) / 2)
        y = rect.y() + int((rect.height() - h) / 2)
        win.setGeometry(QtCore.QRect(x, y, w, h))
    except:
        pass


def _screen_geometries():
    if is_PyQt6:
        return [screen.availableGeometry() for screen in
                QtWidgets.QApplication.screens()]
    else:  # PyQt5
        desktop = QtWidgets.QDesktopWidget()
        return [desktop.availableGeometry(i) for i in
                range(desktop.screenCount())]


def _set_saved_geometry(win: QtWidgets.QMainWindow, words):
    try:
        if len(words) < 4:
            _set_default_geometry(win)
        else:
            target_rect = QtCore.QRect(int(words[0]), int(words[1]),
                                       int(words[2]), int(words[3]))
            target_sc = None
            for rect in _screen_geometries():
                if target_sc is None:
                    target_sc = rect
                    continue
                if _intersection_area(rect, target_rect) > _intersection_area(
                        target_sc, target_rect):
                    target_sc = rect
                    continue
            if target_sc is None:
                _set_default_geometry(win, w=target_rect.width(),
                                      h=target_rect.height())
                return
            else:
                target_sc = _scale_rect_around_center(target_sc, 0.96)
                target_rect = _adjust_window(target_sc, target_rect)
                win.setGeometry(target_rect)
                return
    except:
        # 遇到错误，使用默认的
        _set_default_geometry(win)


def load_window_size(win: QtWidgets.QMainWindow):
    try:
        restore = app_data.getenv(key='restore_window_geometry',
                                  default='Yes',
                                  encoding='utf-8',
                                  ignore_empty=True) != 'No'
        if not restore:
            _set_default_geometry(win)
            return
        name = 'main_window_size_PyQt6' if is_PyQt6 else 'main_window_size'
        words = app_data.getenv(name, encoding='utf-8', default='').split()
        if len(words) < 5:  # 文件错误
            _set_default_geometry(win)
            return
        if words[4] == 'True':  # 需要最大化显示
            _set_default_geometry(win)
            win.showMaximized()
            return
        else:  # 恢复窗口
            _set_saved_geometry(win, words)
            return
    except:
        _set_default_geometry(win)


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
        os.chdir(app_data.getenv('current_work_directory', default=os.getcwd(),
                                 encoding='utf-8'))
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
    return app_data.getenv('console_priority', default='LowPriority',
                           encoding='utf-8', ignore_empty=True)


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
