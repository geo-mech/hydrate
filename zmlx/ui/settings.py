"""
用于程序的配置存储。这里所有函数均不抛出异常.

Modified by Claude, 2026-08-12
"""

import os

from zmlx.algs.base import clamp
from zmlx.system import app_data, read_text, write_text
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
    except Exception as err:
        print(f'Error: \nfunction _set_default_geometry in {__file__}. Message: {err}')


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
    except Exception as err:
        print(f"Error: \nfunction _set_saved_geometry in {__file__}. Message: {err}")
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
    except Exception as err:
        print(f"Error: \nfunction load_window_size in {__file__}. Message: {err}")
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


#: 右侧栏（控制台那一栏）的宽度——存盘键（2026-10-26 加）。
#: ⚠️ 键名带 ``_px`` 后缀：``app_data.getenv`` 会**先查 ``os.environ``**，用
#: ``console_width`` 这种通用词会被外部环境变量静默掩盖（见 ``widgets/AGENTS.md``）。
KEY_CONSOLE_WIDTH = 'main_window_console_width_px'

#: 「上次可见时」的右侧栏宽度——:func:`save_console_width` 的兜底键。
LAST_VISIBLE_WIDTH_KEY = 'main_window_console_width_last_visible_px'

#: 右侧栏宽度的**下限**（像素）。低于它，控制台里的命令行输入框就窄到没法输入了。
#: ⚠️ 上限由**窗口本身**决定（见 :func:`load_console_width`），不在这里写死 ——
#: 否则换个屏幕、换个窗口尺寸，恢复出来的宽度就可能把左边挤没。
#: ⚠️ 2026-10-26 由 160 降到 120：右侧栏默认宽度改成约 22% 之后，窗口一窄就会先撞上这个
#: 下限（表现是「比例调小了、右边却一点没变窄」）。120 px 仍放得下控制台底部那行输入框。
MIN_CONSOLE_WIDTH = 120

#: 右侧栏的**默认宽度占窗口宽度的比例**（2026-10-26 加）。用户没有存过宽度时用它。
#: ⚠️ 历史值是 ``0.30``；默认布局偏宽（控制台那一栏挤占了左边工作区），改成 ``0.22``。
#: 用户拖过之后就一直是用户的宽度（存盘），这个比例只在没有记录时生效。
DEFAULT_CONSOLE_RATIO = 0.22

#: 右侧栏宽度的上限比例（相对 ``splitter`` 宽度）。窗口很窄时把比例夹到它以内，
#: 免得把左边挤没。
MAX_CONSOLE_RATIO = 0.60


def save_console_width(win):
    """记下右侧栏（控制台那一栏）的宽度，供下次启动恢复.

    ⚠️ **隐藏时不覆盖已存的宽度**：右侧栏隐藏后 ``splitter.sizes()`` 里那一项是 **0**，
    直接存 0 就等于「用户把控制台拖没了」—— 下次恢复时只能退回默认值。
    所以只记 ``> 0`` 的那个，另外把「隐藏前最后一次可见时的宽度」也存一份兜底。

    Args:
        win: 主窗口（``MainWindow``）。需要有 ``splitter`` / ``right_tabs``；
            缺了（或还没建好）就什么都不做。
    """
    try:
        splitter = getattr(win, 'splitter', None)
        right_tabs = getattr(win, 'right_tabs', None)
        if splitter is None or right_tabs is None:
            return
        sizes = splitter.sizes()
        if len(sizes) < 2:
            return
        width = int(sizes[1])
        if width <= 0:
            return  # 隐藏中：保留上次的宽度，别用 0 覆盖
        app_data.setenv(KEY_CONSOLE_WIDTH, str(width), encoding='utf-8')
        last = getattr(win, '_last_console_width', None)
        if isinstance(last, int) and last > 0:
            app_data.setenv(
                LAST_VISIBLE_WIDTH_KEY, str(last), encoding='utf-8')
    except Exception as err:
        print(err)


def load_console_width(win, default_width):
    """恢复右侧栏宽度；没有记录 / 记录不可用时返回 ``None``.

    取 :data:`KEY_CONSOLE_WIDTH`（没有就退到 :data:`LAST_VISIBLE_WIDTH_KEY`），
    夹到「:data:`MIN_CONSOLE_WIDTH` ~ 窗口宽度的 :data:`MAX_CONSOLE_RATIO`」之间；
    窗口太窄、夹完也放不下时返回 ``None``，由调用方用 ``default_width`` 这个默认值。

    Args:
        win: 主窗口（取当前宽度作上限参考）。
        default_width: 默认宽度（窗口宽度的一个比例），拿不到记录时用它。

    Returns:
        int | None: 可用的宽度；没有记录时 ``None``。
    """
    try:
        text = app_data.getenv(
            KEY_CONSOLE_WIDTH, encoding='utf-8', default='', ignore_empty=True)
        if not text:
            text = app_data.getenv(
                LAST_VISIBLE_WIDTH_KEY, encoding='utf-8', default='',
                ignore_empty=True)
        if not text:
            return None
        width = int(float(text))
        upper = max(MIN_CONSOLE_WIDTH + 1, int(win.width() * MAX_CONSOLE_RATIO))
        return clamp(width, MIN_CONSOLE_WIDTH, upper)
    except Exception as err:
        print(err)
        return None


#: 「重置布局」涉及的全部存盘键（2026-10-26 加）。
#: ⚠️ 与 :func:`reset_layout` 一一对应：**以后新增任何「布局类」存盘键都要加进来**，
#: 否则「重置布局」会"重置不干净"，用户点了还以为没生效。
#:
#: ⚠️⚠️ **这里只放「右侧栏」那几项**（2026-10-26 按用户要求收窄）。**不**包含：
#:   - ``main_window_size*`` —— 用户拖出来的窗口大小/位置是"他知道自己在干什么"，
#:     「重置布局」不该把窗口拽回屏幕居中 75%；
#:   - 样式表（``zml_window_style.qss``）—— 外观不是布局。
LAYOUT_KEYS = (
    KEY_CONSOLE_WIDTH,            # 右侧栏宽度
    LAST_VISIBLE_WIDTH_KEY,       # 右侧栏上次可见宽度
    'console_visible',            # 右侧栏是否显示
)


def reset_layout(style_sheet=None):
    """「显示 → 重置布局」：清掉存盘的**布局类**设置，下次启动回到默认.

    清哪些（见 :data:`LAYOUT_KEYS`）：右侧栏宽度、上次可见宽度、是否显示。
    **窗口大小 / 位置不在其中**，样式表**默认也不清**（见下）。

    ⚠️ **只清「布局」这一类的键**：不碰插件名单、不碰历史标签页、不碰工作路径 ——
    那些不是布局，清掉会让用户丢东西。要清更多得自己往 :data:`LAYOUT_KEYS` 里加。

    Args:
        style_sheet: 要一并清掉的样式表键（tuple）。**默认 ``None`` = 不动样式表**
            （2026-10-26 按用户要求：外观不是布局）。传了才清 —— 样式表存的是**文件**
            （``settings.save`` 写到 ``app_data.temp(key)``），只写空串不算真清，
            所以要**删除文件**、再写一次空串兜底。

    Returns:
        list[str]: 真正清掉的键名（供界面提示用）。
    """
    keys = list(LAYOUT_KEYS)
    style_keys = [k for k in (style_sheet or ())
                  if isinstance(k, str) and len(k) > 0]
    keys.extend(style_keys)
    cleared = []
    for key in keys:
        try:
            app_data.setenv(key, '', encoding='utf-8')
            cleared.append(key)
        except Exception as err:
            print(err)
    for key in style_keys:
        try:
            path = app_data.temp(key)
            if isinstance(path, str) and os.path.isfile(path):
                os.remove(path)
        except Exception as err:
            print(err)
        try:
            save(key, '', encoding='utf-8')  # 兜底：删不掉时至少把内容清空
        except Exception as err:
            print(err)
    return cleared


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


def add_env_item(label=None, key=None, items=None, note=None, kind=None,
                 default=None, **extra):
    """登记一条环境变量配置项（供「设置 → 系统」表单使用）。

    Args:
        label: 显示用的名称。
        key: 环境变量键名（必须给出，否则忽略）。
        items: 枚举型的可选项列表。
        note: 说明文字。
        kind: 控件类型 —— ``'bool'`` / ``'enum'`` / ``'int'`` / ``'str'``。
            缺省时由界面按「有 items → enum，否则 str」推断。
        default: **代码里真正采用的默认值**。界面按它初始化控件，所以它必须与
            读取该键的那段代码逐字一致（见 ``zmlx/ui/data/zml_env_items.py``）。
        **extra: 其它字段（如 ``int`` 型的 ``min`` / ``max``），原样透传给界面。

    Note:
        ⚠️ 这里**必须**用 ``**extra`` 兜住未知字段：早先的实现只接受固定的四个
        关键字，于是在 JSON 里新加 ``kind`` / ``default`` 时会被静默丢弃
        （实测：15 项全部报 ``unexpected keyword argument 'kind'``，界面退化成
        全部显示「未设置」）—— 那正是本界面撒谎的根源。
    """
    if key is None:
        return
    item = dict(label=label, key=key, items=items, note=note)
    if kind is not None:
        item['kind'] = kind
    if default is not None:
        item['default'] = default
    item.update(extra)
    env_items = get_env_items()
    for elem in env_items:
        if elem['key'] == key:
            elem.update(item)
            app_data.put('env_items', env_items)
            return
    env_items.append(item)
    app_data.put('env_items', env_items)



def __env_items_init():
    for filename in app_data.find_all('zml_env_items.json'):
        try:
            from zmlx.io.json_ex import read
            data = read(filename, encoding='utf-8')
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
