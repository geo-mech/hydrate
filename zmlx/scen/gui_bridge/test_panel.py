"""界面桥 — **测试控件**（`BridgeTestPanel`）：两个界面互连、发请求、看双向日志.

为什么需要它
------------

跨进程通道最容易出现的问题是"看起来通了、其实没通"（回包是本地伪造的、或者请求
根本没进到对方的 GUI 线程）。所以验收不能只看"有没有报错"，要看**四个判据**
（``ReadMe.md`` §10.2）：

1. ``ping`` 拿到对方的 pid；
2. ``tabs`` 返回的是**对方的**标签页；
3. ``screenshot`` 拿到的图里是**对方的界面**（没有本窗口）；
4. ``show`` 之后**对方的界面**切过去了。

本控件同时扮演"本机服务状态面板"和"客户端"，所以不需要任何外部工具，
开两个实例就能把上面四条走一遍。

⚠️ 服务是**进程级**的，不随本面板的开关而存亡：关掉标签页只关掉"控制台"，
不会停服务（否则外部正连着的调用会莫名断掉）。

Created by DeepSeek, 2026-10-30: 第一版（MVP）
"""

import json
import os
import tempfile
import time

from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.utils.thread_runner import run

from zmlx.scen.gui_bridge import client as client_mod
from zmlx.scen.gui_bridge import discovery, server as server_mod

#: 进程级单例：一个进程只该有一个桥服务
_SERVER = None


def get_server():
    """取（必要时创建）本进程的桥服务实例."""
    global _SERVER
    if _SERVER is None:
        _SERVER = server_mod.BridgeServer()
    return _SERVER


class BridgeTestPanel(QtWidgets.QWidget):
    """界面桥的控制台与客户端（顶层控件，由插件打开成标签页）."""

    def __init__(self, parent=None):
        super(BridgeTestPanel, self).__init__(parent)
        self._client = None
        self._busy = False
        self._build_ui()
        self._sync_server_state()
        self._refresh_targets()

    # -- 界面 ---------------------------------------------------------------

    def _build_ui(self):
        self.setWindowTitle('界面桥')
        self.setMinimumWidth(560)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 本机服务
        box = QtWidgets.QGroupBox('本机服务（被外部调用的那一端）', self)
        form = QtWidgets.QVBoxLayout(box)
        row = QtWidgets.QHBoxLayout()
        self.state_label = QtWidgets.QLabel('● 已停止', box)
        row.addWidget(self.state_label)
        row.addStretch(1)
        self.btn_start = QtWidgets.QPushButton('启动服务', box)
        self.btn_start.clicked.connect(self._on_start)
        row.addWidget(self.btn_start)
        self.btn_stop = QtWidgets.QPushButton('停止', box)
        self.btn_stop.clicked.connect(self._on_stop)
        row.addWidget(self.btn_stop)
        form.addLayout(row)

        self.handle_label = QtWidgets.QLabel('句柄：—', box)
        self.handle_label.setStyleSheet('color: #666;')
        self.handle_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addWidget(self.handle_label)
        layout.addWidget(box)

        # 目标
        box2 = QtWidgets.QGroupBox('目标（另一个进程）', self)
        form2 = QtWidgets.QVBoxLayout(box2)
        row2 = QtWidgets.QHBoxLayout()
        self.target_box = QtWidgets.QComboBox(box2)
        self.target_box.setMinimumWidth(300)
        row2.addWidget(self.target_box, 1)
        self.btn_refresh = QtWidgets.QPushButton('刷新发现', box2)
        self.btn_refresh.clicked.connect(self._refresh_targets)
        row2.addWidget(self.btn_refresh)
        form2.addLayout(row2)

        row3 = QtWidgets.QHBoxLayout()
        row3.addWidget(QtWidgets.QLabel('或手动：', box2))
        self.addr_edit = QtWidgets.QLineEdit(box2)
        self.addr_edit.setPlaceholderText('127.0.0.1:端口')
        row3.addWidget(self.addr_edit, 1)
        self.btn_connect = QtWidgets.QPushButton('连接', box2)
        self.btn_connect.clicked.connect(self._on_connect)
        row3.addWidget(self.btn_connect)
        form2.addLayout(row3)

        self.target_state = QtWidgets.QLabel('● 未连接', box2)
        self.target_state.setStyleSheet('color: #666;')
        form2.addWidget(self.target_state)
        layout.addWidget(box2)

        # 请求
        box3 = QtWidgets.QGroupBox('发请求', self)
        row4 = QtWidgets.QHBoxLayout(box3)
        for text, method in [('ping', 'ping'), ('info', 'info'),
                             ('tabs', 'tabs'), ('截图', 'screenshot')]:
            button = QtWidgets.QPushButton(text, box3)
            button.clicked.connect(
                lambda _=False, m=method: self._call_async(m, {}))
            row4.addWidget(button)
        row4.addWidget(QtWidgets.QLabel('show：', box3))
        self.show_edit = QtWidgets.QLineEdit(box3)
        self.show_edit.setPlaceholderText('show_env_edit')
        row4.addWidget(self.show_edit, 1)
        self.btn_show = QtWidgets.QPushButton('打开', box3)
        self.btn_show.clicked.connect(self._on_show)
        row4.addWidget(self.btn_show)
        layout.addWidget(box3)

        # 日志
        box4 = QtWidgets.QGroupBox('日志（双向）', self)
        inner = QtWidgets.QVBoxLayout(box4)
        self.log_view = QtWidgets.QPlainTextEdit(box4)
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(160)
        font = self.log_view.font()
        font.setFamily('Consolas')
        self.log_view.setFont(font)
        inner.addWidget(self.log_view)
        layout.addWidget(box4, 1)

        tip = QtWidgets.QLabel(
            '提示：再开一个本程序（双击 zml_ui.pyw）→ 两份界面各自「启动服务」→ '
            '在这里「刷新发现」→ 选中对方 → 点「截图」，图里应是**对方**的界面。',
            self)
        tip.setWordWrap(True)
        tip.setStyleSheet('color: #666;')
        layout.addWidget(tip)

    # -- 本机服务 -----------------------------------------------------------

    def _sync_server_state(self):
        bridge = get_server()
        if bridge.running:
            self.state_label.setText('● 运行中　端口 {0}　PID {1}'.format(
                bridge.port, os.getpid()))
            self.state_label.setStyleSheet('color: #0a7a3d;')
            self.handle_label.setText('句柄：' + discovery.handle_path())
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
        else:
            self.state_label.setText('● 已停止')
            self.state_label.setStyleSheet('color: #888;')
            self.handle_label.setText('句柄：—（启动后写入）')
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)

    def _on_start(self):
        bridge = get_server()
        try:
            port = bridge.start()
        except Exception as err:  # noqa: BLE001
            self._log('启动失败：{0}'.format(err), ok=False)
            return
        self._log('服务已启动，端口 {0}'.format(port), ok=True)
        self._sync_server_state()
        self._refresh_targets()

    def _on_stop(self):
        get_server().stop()
        self._log('服务已停止', ok=True)
        self._sync_server_state()

    # -- 目标 ---------------------------------------------------------------

    def _refresh_targets(self):
        self.target_box.clear()
        try:
            handles = discovery.list_handles(clean=True, exclude_self=True)
        except Exception as err:  # noqa: BLE001
            handles = []
            self._log('扫描失败：{0}'.format(err), ok=False)
        for item in handles:
            text = 'PID {0} · 端口 {1} · v{2} · {3}'.format(
                item.get('pid'), item.get('port'),
                item.get('version') or '?', item.get('cwd') or '')
            self.target_box.addItem(text, item)
        if not handles:
            self.target_box.addItem('（没有发现其它实例）', None)
        self._log('发现 {0} 个其它实例'.format(len(handles)),
                  ok=bool(handles))

    def _on_connect(self):
        handle = self.target_box.currentData()
        client = None
        if handle:
            client = client_mod.BridgeClient.from_handle(handle, timeout=5.0)
        else:
            text = self.addr_edit.text().strip()
            if not text:
                self._log('没有目标：先「刷新发现」，或手动填 127.0.0.1:端口', ok=False)
                return
            try:
                host, port = text.rsplit(':', 1)
                client = client_mod.BridgeClient(int(port), token='', host=host)
            except ValueError:
                self._log('地址格式应为 127.0.0.1:端口', ok=False)
                return
            self._log('手动地址没有 token，只能探活（/health）；'
                      '要发请求请在「刷新发现」里选实例', ok=False)
        self._client = client
        self.target_state.setText('● 连接中… {0}'.format(client.url))
        self.target_state.setStyleSheet('color: #b06a00;')

        box = {}

        def task():
            try:
                health = client.health()
                if client.token:
                    health = client.ping()
                box['r'] = health
            except Exception as err:  # noqa: BLE001
                box['e'] = err

        def done():
            err = box.get('e')
            if err is not None:
                self.target_state.setText('● 连接失败：{0}'.format(err))
                self.target_state.setStyleSheet('color: #b33;')
                self._log('连接失败：{0}'.format(err), ok=False)
                return
            info = box.get('r') or {}
            self.target_state.setText(
                '● 已连接　{0}　PID {1}　v{2}'.format(
                    client.url, info.get('pid'), info.get('version')))
            self.target_state.setStyleSheet('color: #0a7a3d;')
            self._log('已连接 {0}'.format(client.url), ok=True)

        run(task, done)

    # -- 请求 ---------------------------------------------------------------

    def _on_show(self):
        name = self.show_edit.text().strip()
        if not name:
            self._log('show 需要填一个 gui 命令名，例如 show_env_edit', ok=False)
            return
        self._call_async('show', {'name': name})

    def _call_async(self, method, params):
        client = self._client
        if client is None:
            self._log('还没有连接目标：先「刷新发现」并「连接」', ok=False)
            return
        if self._busy:
            self._log('上一个请求还没返回，稍等', ok=False)
            return
        self._busy = True
        started = time.time()
        self._log('→ {0} {1}'.format(method, _brief(params)), ok=True)

        box = {}

        def task():
            try:
                box['r'] = client.call(method, params)
            except Exception as err:  # noqa: BLE001
                box['e'] = err

        def done():
            self._busy = False
            cost = (time.time() - started) * 1000.0
            err = box.get('e')
            if err is not None:
                self._log('← 失败 {0:.0f}ms　{1}'.format(cost, err), ok=False)
                return
            result = box.get('r') or {}
            if method == 'screenshot' and result.get('png_b64'):
                self._show_screenshot(result, cost)
                return
            self._log('← {0:.0f}ms　{1}'.format(cost, _brief(result)), ok=True)

        run(task, done)

    def _show_screenshot(self, result, cost):
        """把截到的图存成临时文件并开一个新标签页（**这就是"看见对方"的判据**）."""
        import base64

        try:
            data = base64.b64decode(result.get('png_b64') or '')
        except Exception as err:  # noqa: BLE001
            self._log('截图解码失败：{0}'.format(err), ok=False)
            return
        folder = os.path.join(tempfile.gettempdir(), 'zml_gui_bridge')
        try:
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, 'shot_{0}.png'.format(
                time.strftime('%H%M%S')))
            with open(path, 'wb') as fp:
                fp.write(data)
        except OSError as err:
            self._log('截图存盘失败：{0}'.format(err), ok=False)
            return
        self._log('← {0:.0f}ms　PNG {1}×{2}　{3}'.format(
            cost, result.get('width'), result.get('height'), path), ok=True)
        try:
            from zmlx.ui import gui

            gui.open_image(path)
        except Exception as err:  # noqa: BLE001
            self._log('打开截图失败（文件已存盘）：{0}'.format(err), ok=False)

    # -- 日志 ---------------------------------------------------------------

    def _log(self, text, ok=True):
        mark = '  ' if ok else '!!'
        line = '{0} {1} {2}'.format(
            time.strftime('%H:%M:%S'), mark, text)
        self.log_view.appendPlainText(line)
        bar = self.log_view.verticalScrollBar()
        bar.setValue(bar.maximum())


def _brief(value, limit=240):
    """把参数/结果压成一行短文本（去掉大字段，避免日志被 base64 淹掉）."""
    if isinstance(value, dict) and 'png_b64' in value:
        value = {key: item for key, item in value.items() if key != 'png_b64'}
    try:
        text = json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        text = str(value)
    return text if len(text) <= limit else text[:limit] + '…'
