"""
用于程序的配置存储。这里所有函数均不抛出异常
"""

import os

from zml import app_data, read_text, write_text, get_hash
from zmlx.alg.base import clamp
from zmlx.io.json_ex import read as read_json
from zmlx.ui.alg import get_current_screen_geometry
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtGui, QtCore, QtWidgets, is_pyqt6


def __add_path():
    try:
        app_data.add_path(os.path.join(os.path.dirname(__file__), 'data'))
    except Exception as err:
        print(err)


__add_path()


def find_icon_file(name):
    try:
        if os.path.isfile(name):  # 本身已经是了
            return name
        image_exts = app_data.get('icon_exts', None)  # 默认搜索的图片扩展名
        if image_exts is None:
            image_exts = ['.jpg', '.png']
        for folder in reversed(app_data.find_all('zml_icons')):
            filepath = os.path.join(folder, name)
            if os.path.isfile(filepath):
                return filepath
            for ext in image_exts:
                filepath = os.path.join(folder, name + ext)
                if os.path.isfile(filepath):
                    return filepath
        return None
    except Exception as err:
        print(err)
        return None


def load_pixmap(name):
    if isinstance(name, QtGui.QPixmap):
        return name
    filepath = find_icon_file(name)
    if filepath is not None:
        return QtGui.QPixmap(filepath)
    return None


def load_icon(name):
    if isinstance(name, QtGui.QIcon):
        return name
    try:
        pixmap = load_pixmap(name)
        if pixmap is not None:
            icon = QtGui.QIcon()
            icon.addPixmap(
                pixmap, QtGui.QIcon.Mode.Normal,
                QtGui.QIcon.State.Off)
            return icon
        else:
            return QtGui.QIcon()
    except Exception as err:
        print(err)
        return QtGui.QIcon()


def find_sound(name):
    try:
        if os.path.isfile(name):  # 本身已经是了
            return name
        sound_exts = app_data.get('sound_exts', None)
        if sound_exts is None:
            sound_exts = ['.wav']
        for folder in reversed(app_data.find_all('zml_sounds')):
            filepath = os.path.join(folder, name)
            if os.path.isfile(filepath):
                return filepath
            for ext in sound_exts:
                filepath = os.path.join(folder, name + ext)
                if os.path.isfile(filepath):
                    return filepath
        return None
    except Exception as err:
        print(err)
        return None


def play_sound(name):
    try:
        filepath = find_sound(name)
        if filepath is not None:
            gui.play_sound(filepath)
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
    write_text(path=app_data.temp(key), text=f'{value}', encoding=encoding)


def load(key, default='', encoding=None, ignore_empty=False):
    for file in app_data.find_all(key):
        text = read_text(path=file, default=None, encoding=encoding)
        if isinstance(text, str):
            if len(text) > 0 or not ignore_empty:
                return text
    return default


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
    if is_pyqt6:
        return [screen.availableGeometry() for screen in
                QtWidgets.QApplication.screens()]
    else:  # PyQt5
        desktop = QtWidgets.QDesktopWidget()
        return [desktop.availableGeometry(i) for i in
                range(desktop.screenCount())]


def _set_saved_geometry(win: QtWidgets.QMainWindow, words, scale=None):
    try:
        if len(words) < 4:
            _set_default_geometry(win)
        else:
            target_rect = QtCore.QRect(
                int(words[0]), int(words[1]),
                int(words[2]), int(words[3])
            )
            if scale is not None:
                target_rect = _scale_rect_around_center(target_rect, scale)
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
                _set_default_geometry(
                    win, w=target_rect.width(), h=target_rect.height())
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
        restore = app_data.getenv(
            key='restore_window_geometry',
            default='Yes',
            encoding='utf-8',
            ignore_empty=True) != 'No'
        if not restore:
            _set_default_geometry(win)
            return
        name = 'main_window_size_PyQt6' if is_pyqt6 else 'main_window_size'
        words = app_data.getenv(name, encoding='utf-8', default='').split()
        if len(words) < 5:  # 文件错误
            _set_default_geometry(win)
            return
        if words[4] == 'True':  # 需要最大化显示
            _set_saved_geometry(win, words, scale=0.75)
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
        name = 'main_window_size_PyQt6' if is_pyqt6 else 'main_window_size'
        rc = win.geometry()
        app_data.setenv(
            name,
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
        os.chdir(app_data.getenv(
            'current_work_directory', default=os.getcwd(), encoding='utf-8'))
    except Exception as err:
        print(err)
        save_cwd()


def priority_value(text):
    """
    根据文本来获得优先级
    """
    priorities = {
        'HighestPriority': QtCore.QThread.Priority.HighestPriority,
        'HighPriority': QtCore.QThread.Priority.HighPriority,
        'IdlePriority': QtCore.QThread.Priority.IdlePriority,
        'InheritPriority': QtCore.QThread.Priority.InheritPriority,
        'LowestPriority': QtCore.QThread.Priority.LowestPriority,
        'LowPriority': QtCore.QThread.Priority.LowPriority,
        'NormalPriority': QtCore.QThread.Priority.NormalPriority,
    }
    return priorities.get(text, QtCore.QThread.Priority.LowPriority)


def load_priority():
    """
    应用内核的优先级。默认使用较低的优先级，以保证整个计算机运行的稳定
    """
    return app_data.getenv(
        'console_priority', default='LowPriority',
        encoding='utf-8', ignore_empty=True)


def save_priority(value):
    app_data.setenv('console_priority', value, encoding='utf-8')


def load_ui_text():
    ui_text1 = {}
    try:
        for path in reversed(app_data.find_all('zml_text.json')):
            try:
                ui_text1.update(read_json(path, default={}))
            except Exception as err_3:
                print(err_3)
    except Exception as err:
        print(err)
    return ui_text1


app_data.put(key='ui_text', value=load_ui_text())


def get_text(key):
    try:
        __ui_text = app_data.get('ui_text', None)
        if not isinstance(__ui_text, dict):
            return key
        if isinstance(key, str):
            return __ui_text.get(key, key)
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
        return None


def get_default_code():
    try:
        return read_text(
            app_data.find('zml_code_in_editor.py'),
            encoding='utf-8',
            default='')
    except Exception as err:
        print(err)
        return ''


def get_env_items():
    data = app_data.get('env_items', None)
    if isinstance(data, list):
        return data
    else:
        return []


def add_env_item(label=None, key=None, items=None, note=None):
    if key is None:
        return
    env_items = get_env_items()
    for item in env_items:
        if item['key'] == key:
            item.update(dict(label=label, items=items, note=note))
            app_data.put('env_items', env_items)
            return
    env_items.append(dict(
        label=label,
        key=key,
        items=items,
        note=note))
    app_data.put('env_items', env_items)


def __env_items_init():
    for fname in app_data.find_all('zml_env_items.json'):
        try:
            from zmlx.io.json_ex import read
            data = read(fname, encoding='utf-8')
            for item in data:
                try:
                    add_env_item(**item)
                except Exception as err:
                    print(f'Error: {err}')
                    pass
        except Exception as err:
            print(f'Error: {err}')
            pass


# 环境变量配置的初始化
__env_items_init()


def get_setup_file_rank(path):
    """
    返回配置文件的优先级
    """
    if not isinstance(path, str):
        return 1.0e20
    try:
        text = app_data.getenv(key=get_hash('rank: ' + path))
        rank = float(text)
        return clamp(rank, 0.0, 1.0e20)
    except TypeError:  # 默认的rank
        return 1.0e10


def set_setup_file_rank(path, rank=None):
    """
    修改配置文件的优先级
    """
    if not isinstance(rank, (int, float)):
        rank = 1.0e10  # 重置为默认的rank
    else:
        rank = clamp(rank, 0.0, 1.0e20)
    app_data.setenv(
        key=get_hash('rank: ' + path), value=f'{rank}')


def get_setup_files(rank_max=2.0e10):
    """
    返回所有的，经过排序的，存在的，去除重复的，zml_gui_setup.py文件的路径。
    如果给定rank_max，则只返回rank小于等于rank_max的文件。
    """
    from zmlx.alg.sys import listdir

    all_files = []

    # 用户额外存储的文件
    files_data = app_data.getenv(
        key='zml_gui_setup_files', encoding='utf-8', default=''
    )
    for f in files_data.split(';'):
        try:
            path = os.path.abspath(f.strip())
            if os.path.isfile(path) and path not in all_files:
                all_files.append(path)
        except Exception as err:
            print(err)

    # 在程序包内搜索到的文件
    folders = app_data.get_paths()
    folders.extend(listdir(path=folders, with_file=False, with_dir=True))
    for folder in folders:
        path = os.path.abspath(os.path.join(folder, 'zml_gui_setup.py'))
        if os.path.isfile(path) and path not in all_files:
            all_files.append(path)

    # 附加优先级
    file_ranks = []
    for path in all_files:
        rank = get_setup_file_rank(path)
        if rank <= rank_max:
            file_ranks.append([path, rank])

    # 根据rank来排序
    file_ranks.sort(key=lambda x: x[1])

    # 返回所有的文件名
    return [file_rank[0] for file_rank in file_ranks]


def set_setup_files(files):
    """
    保存当前列表到环境变量
    """
    files = [os.path.abspath(file) for file in files]

    # 存储列表
    app_data.setenv(
        key='zml_gui_setup_files',
        encoding='utf-8',
        value=";".join(files)
    )

    # 确保不在列表中的文件会被排除
    for file in get_setup_files(rank_max=1.0e200):
        if file not in files:
            set_setup_file_rank(file, 1.0e20)

    # 存储列表的rank
    for idx in range(len(files)):
        set_setup_file_rank(files[idx], idx + 1)
