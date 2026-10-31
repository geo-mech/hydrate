"""界面桥 — **能力层**（方法名 → 实现，全部在 **GUI 线程**里执行）.

⚠️⚠️ 本模块的每一个函数都只允许在 **GUI 线程**里跑：它们会 ``w.grab()``、
会切标签页、会碰控件。调用链是::

    HTTP 服务线程 → gui.command('bridge_call', method, params) → GUI 线程 → 这里

``GuiApi.command`` 负责跨线程投递（``utils/gui_api.py:122-157``），**不要**在这里
自己起线程，也**不要**把这里的函数登记成 ``mark_direct``（那会取消投递，
在 HTTP 线程里直接碰 Qt —— 轻则不刷新、重则崩，且不可复现）。

本版本（MVP）只实现 6 个方法，够验证「跨进程让界面动一下」这条路线：
``ping`` / ``info`` / ``commands`` / ``tabs`` / ``show`` / ``screenshot``。

Created by DeepSeek, 2026-10-30: 第一版
"""

import base64
import os
import time

from zmlx.scen.gui_bridge import protocol


#: 进程启动时刻（算 uptime 用）
_STARTED = time.time()


def dispatch(method, params):
    """执行一个方法（**必须在 GUI 线程**）.

    Args:
        method: 已由 :mod:`protocol` 校验过的方法名。
        params: 参数字典。

    Returns:
        dict: 方法的 ``result``（一定可 JSON 序列化）。

    Raises:
        protocol.ProtocolError: 未知方法 / 参数错误 / 没有界面。
    """
    handler = _HANDLERS.get(method)
    if handler is None:
        raise protocol.ProtocolError(
            protocol.METHOD_NOT_FOUND,
            '方法 {0!r} 尚未实现'.format(method),
            hint='本版本可用：' + ', '.join(protocol.METHODS))
    return handler(params or {})


def _window():
    """取主窗口；没有界面时抛 ``FAILED``.

    ⚠️ ``gui.get()`` 返回的是 **``GuiApi``（命令表）**，不是主窗口 —— 2026-10-30
    第一次联调时踩过：直接 ``gui.get().windowTitle()`` 报
    ``'GuiApi' object has no attribute 'windowTitle'``。

    正确写法就是 ``gui.window()``（**一行**）：``MainWindow`` 在
    ``__init_gui_api`` 末尾对 ``window`` 调过 ``mark_direct``（``main.py:451-454``），
    于是 ``command('window')`` 跳过"派发到 GUI 线程"这一步、直接执行注册的
    ``lambda: self``；而在 GUI 线程内即便不 direct 也是就地执行（AutoConnection
    直连）。headless 时 ``GuiBuffer.command`` 直接返回 ``None``，不会抛异常。
    """
    from zmlx.ui import gui

    window = gui.window()
    if window is None:
        raise protocol.ProtocolError(
            protocol.FAILED,
            '当前进程没有界面（headless 模式），无法执行界面操作')
    return window


def _api():
    """取命令表（``GuiApi``）。它就是 ``gui.get()``，不是主窗口."""
    from zmlx.ui import gui

    api = gui.get()
    if api is None:
        raise protocol.ProtocolError(
            protocol.FAILED, '当前进程没有界面（headless 模式），取不到命令表')
    return api


# ---------------------------------------------------------------------------
# 只读方法
# ---------------------------------------------------------------------------

def _ping(params):
    """连通性：只回身份，不碰界面（除了解析版本号）."""
    from zmlx import __version__

    return {
        'ok': True,
        'app': 'IGG-Hydrate',
        'version': str(__version__),
        'pid': os.getpid(),
        'uptime': round(time.time() - _STARTED, 1),
        'cwd': os.getcwd(),
    }


def _info(params):
    """窗口状态快照（agent 判断"现在是什么状况"用）."""
    from zmlx.ui import gui

    window = _window()
    dark = None
    try:
        dark = bool(gui.in_dark_mode())
    except Exception:
        pass
    return {
        'ok': True,
        'window': {
            'title': window.windowTitle(),
            'size': [window.width(), window.height()],
            'maximized': bool(window.isMaximized()),
            'dark': dark,
        },
        'tab_count': int(window.count_tabs()),
        'cwd': os.getcwd(),
        'pid': os.getpid(),
    }


def _commands(params):
    """可调用的 gui 命令名（**运行时取自 ``list_all()``**，不维护静态副本）."""
    api = _api()
    names = api.list_all()
    allowed = sorted(name for name in names if protocol.is_command_allowed(name))
    return {'ok': True, 'count': len(allowed), 'names': allowed}


def _tabs(params):
    """标签页列表 + 当前页（用 ``count_tabs`` / ``get_tab_caption``，不改 ``main.py``）."""
    window = _window()
    count = int(window.count_tabs())
    items = []
    for index in range(count):
        try:
            caption = window.get_tab_caption(index)
        except Exception:
            caption = ''
        items.append({'index': index, 'caption': str(caption)})
    current = -1
    try:
        current = int(window.get_tab_widget().currentIndex())
    except Exception:
        pass
    return {'ok': True, 'current': current, 'count': count, 'items': items}


# ---------------------------------------------------------------------------
# 写方法（本版本只有一个）
# ---------------------------------------------------------------------------

def _show(params):
    """打开 / 切到某个页面（本版本唯一会让界面**变化**的方法）.

    ``name`` 是**真实的 gui 命令名**（如 ``show_env_edit``），由
    :func:`protocol.check_command_name` 按前缀白名单校验。
    """
    name = protocol.check_command_name(params.get('name'))
    _window()  # 先确认有界面：headless 时这里就抛 FAILED
    api = _api()
    func = api.get_func(name)
    if not callable(func):
        return {
            'ok': False,
            'name': name,
            'message': '命令 {0} 当前不存在 —— 提供它的插件可能没有加载'.format(name),
        }
    try:
        func()  # 已在 GUI 线程，直接调（返回值丢弃：可能是控件对象，不可序列化）
    except Exception as err:  # noqa: BLE001 - 单个页面打不开不该炸掉通道
        return {'ok': False, 'name': name,
                'message': '{0}: {1}'.format(type(err).__name__, err)}
    return {'ok': True, 'name': name}


# ---------------------------------------------------------------------------
# 截图
# ---------------------------------------------------------------------------

def _screenshot(params):
    """截一张图，返回 PNG 的 base64.

    ⚠️ 本机 ``devicePixelRatio`` 是 1.75，``grab()`` 给的是**物理像素**
    （1440 逻辑宽 → 2520 物理宽）。所以默认按 ``max_width=1440`` 缩回去，
    否则 base64 体积会平白翻一倍多。
    """
    from zmlx.ui.pyqt import QtCore

    window = _window()
    target = str(params.get('target') or 'window').strip().lower()
    if target not in ('window', 'tab'):
        raise protocol.ProtocolError(
            protocol.INVALID_PARAMS,
            "target 只能是 'window' 或 'tab'，当前是 {0!r}".format(target))

    max_width = protocol.check_int(params.get('max_width'), 'max_width',
                                  64, protocol.MAX_SCREENSHOT_WIDTH, default=1440)

    widget = window
    if target == 'tab':
        try:
            current = window.get_tab_widget().currentWidget()
        except Exception:
            current = None
        if current is not None:
            widget = current

    pixmap = widget.grab()
    image = pixmap.toImage()
    if image.isNull():
        raise protocol.ProtocolError(protocol.FAILED, '截图失败：grab() 返回了空图像')
    if image.width() > max_width:
        image = image.scaledToWidth(
            max_width, QtCore.Qt.TransformationMode.SmoothTransformation)

    buffer = QtCore.QBuffer()
    buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, 'PNG')
    data = bytes(buffer.data())
    buffer.close()

    return {
        'ok': True,
        'target': target,
        'width': int(image.width()),
        'height': int(image.height()),
        'bytes': len(data),
        'png_b64': base64.b64encode(data).decode('ascii'),
    }


#: 方法名 → 实现。**这张表就是白名单**，不在表里的一律拒绝。
_HANDLERS = {
    'ping': _ping,
    'info': _info,
    'commands': _commands,
    'tabs': _tabs,
    'show': _show,
    'screenshot': _screenshot,
}
