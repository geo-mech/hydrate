"""控制台输出控件（OutputWidget — 标准输出捕获、进度条、命令输入行）.

``print`` 中的 ANSI 转义码会被解释成颜色（``\033[31m`` 等，见 :class:`_Ansi`）；
控件**不支持**的序列（擦行 / 清屏 / 光标定位 / OSC 标题……）会被**删除**，
不会在界面上显示成乱码。

保存 / 恢复（:meth:`OutputWidget.save_text` / :meth:`OutputWidget.load_text`）用 **HTML**
（:attr:`OutputWidget.SUFFIX`）而不是纯文本：颜色、粗体等都是存在文本片段的
``QTextCharFormat`` 里的，``toPlainText()`` 会把它们**全部丢掉** —— 早先正是这样存的，
于是「重启后加载的历史没有颜色」（2026-10-26 修复）。旧版本留下的 ``.txt`` 仍按纯文本打开。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-07: add_text 支持 ANSI 颜色，并过滤不支持的转义序列
Modified by DeepSeek, 2026-10-08: 「内核并行」开关移到主窗口状态栏（原 parallel_edit 属性移除）
Modified by DeepSeek, 2026-10-26: 输出历史改存 HTML，重启后颜色不再丢失
"""

import os
import re
import sys
from typing import Optional, Tuple, List, Union

from zmlx.system import app_data
from zmlx.ui.alg import create_action, get_last_exec_history, clear_exec_history
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets
from zmlx.ui.widgets.attr_view import AttrView
from zmlx.ui.widgets.text_browser import TextBrowser


class _Ansi:
    """ANSI 转义序列的最小实现（供 :meth:`OutputWidget.add_text` 上色用）。

    **只解释 SGR**（``\\033[<参数>m``：颜色 / 粗体 / 斜体 / 下划线 / 删除线）；其余序列
    （``\\033[K`` 擦行、``\\033[2J`` 清屏、``\\033[1;1H`` 定位、OSC 标题……）在
    QTextBrowser 上无法实现，一律**删除**——留着只会在界面上显示成乱码。
    被 ``write`` 从中间切断的序列（如 ``'\\033[3'`` + ``'1m红'``）会暂存到下一次调用。

    ⚠️ 四条实测得到的约束（改这个类之前先读）：

    1. PyQt 的 :class:`QtGui.QTextCharFormat` 是**可变引用**：同一个对象若被放进多个
       文本段，后面的 ``\\033[3xm`` 会**追溯**改掉前面段落的颜色。故每次改属性前都要
       ``QTextCharFormat(fmt)`` 拷贝一份。
    2. 「不设置颜色」必须用**空** format（``foreground().style()`` 为 ``NoBrush``）表示，
       这样文字跟随样式表 / 主题；写成 ``setForeground(palette 里的色)`` 在暗色模式下
       就会看不见。
    3. ``\\033[38;5;n`` / ``\\033[38;2;r;g;b``（256 色 / 真彩）必须连**参数**一起吃掉，
       否则剩下的数字会当作普通文本显示出来。
    4. 基础 8 色（30-37 / 90-97 / 40-47 / 100-107）按终端惯例是给**浅色背景**设计的，
       暗色主题下要用另一套取色，见 :attr:`DARK`。
    """

    #: CSI：ESC [ 参数 中间字节 终止字节（``m`` 才是 SGR，其余丢弃）
    CSI = re.compile(r'\x1b\[([0-9;?]*)[ -/]*([@-~])')
    #: 其它完整的转义序列：OSC（BEL 或 ST 结束）、字符集选择、Fe / nF 转义
    OTHER = re.compile(
        r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)'
        r'|\x1b[()#][0-9A-Za-z]'
        r'|\x1b[@-Z\\^_]'
        r'|\x1b[0-9<=>?]')
    #: 可能是「被切断的序列开头」——只对文本**末尾**有意义，故用 ``\Z``（不能用 ``$``，
    #: 它会匹配到换行符之前，把换行也一起吞进暂存区）
    PARTIAL = re.compile(r'\x1b(?:\][^\x07\x1b]{0,120}|\[[0-9;?]{0,32})?\Z')

    #: 浅色背景下的基础 8 色 + 亮色（背景色用同一张表）
    LIGHT = {
        30: '#000000', 31: '#c0392b', 32: '#1a7f37', 33: '#b9770e',
        34: '#1f5fa9', 35: '#8e44ad', 36: '#148f77', 37: '#606060',
        90: '#4d4d4d', 91: '#e74c3c', 92: '#2e9e4f', 93: '#c9a227',
        94: '#3b82f6', 95: '#a855f7', 96: '#0d9488', 97: '#111111',
    }
    #: 暗色背景下的同一组颜色（纯黑 / 纯白都要挪开，否则看不见）
    DARK = {
        30: '#5c6370', 31: '#e06c75', 32: '#98c379', 33: '#e5c07b',
        34: '#61afef', 35: '#c678dd', 36: '#56b6c2', 37: '#abb2bf',
        90: '#7f8c8d', 91: '#ff7b72', 92: '#a5e075', 93: '#f0d27a',
        94: '#79b8ff', 95: '#d2a8ff', 96: '#76e3d6', 97: '#ffffff',
    }

    @classmethod
    def palette(cls, dark):
        """返回当前主题下使用的基础色表。"""
        return cls.DARK if dark else cls.LIGHT

    @classmethod
    def color256(cls, index, dark):
        """xterm 256 色索引 → ``'#rrggbb'``（越界返回 None）。"""
        if index < 0 or index > 255:
            return None
        if index < 8:
            return cls.palette(dark)[30 + index]
        if index < 16:
            return cls.palette(dark)[90 + index - 8]
        if index < 232:
            n = index - 16
            return '#%02x%02x%02x' % tuple(
                0 if v == 0 else 55 + v * 40 for v in (n // 36, (n // 6) % 6, n % 6))
        gray = (index - 232) * 10 + 8  # 232-255：24 级灰阶
        return '#%02x%02x%02x' % (gray, gray, gray)

    @classmethod
    def sgr(cls, fmt, params, dark):
        """按 SGR 参数更新并返回 format（无法识别的参数忽略）。

        Args:
            fmt: 当前生效的 QTextCharFormat（**不会被修改**）
            params: SGR 参数字符串，如 ``'1;38;5;208'``
            dark: 是否暗色主题（决定基础 8 色的取色）

        Returns:
            新的 QTextCharFormat
        """
        if '?' in params:  # 私有模式（\033[?25m 之类）不是 SGR
            return fmt
        codes = [int(x) for x in params.split(';') if x != ''] or [0]
        fmt = QtGui.QTextCharFormat(fmt)  # ⚠️ 必须拷贝，见类文档第 1 条
        table = cls.palette(dark)

        def set_color(color, background=False):
            if color is None:
                return
            if background:
                fmt.setBackground(QtGui.QColor(color))
            else:
                fmt.setForeground(QtGui.QColor(color))

        i = 0
        while i < len(codes):
            code = codes[i]
            i += 1
            if code == 0:  # 全部复位
                fmt = QtGui.QTextCharFormat()
            elif code == 1:
                fmt.setFontWeight(QtGui.QFont.Weight.Bold)
            elif code == 2:
                fmt.setFontWeight(QtGui.QFont.Weight.Light)
            elif code == 3:
                fmt.setFontItalic(True)
            elif code in (4, 21):
                fmt.setFontUnderline(True)
            elif code == 9:
                fmt.setFontStrikeOut(True)
            elif code == 22:
                fmt.setFontWeight(QtGui.QFont.Weight.Normal)
            elif code == 23:
                fmt.setFontItalic(False)
            elif code == 24:
                fmt.setFontUnderline(False)
            elif code == 29:
                fmt.setFontStrikeOut(False)
            elif code == 39:  # 默认前景（跟随主题）
                fmt.clearForeground()
            elif code == 49:  # 默认背景
                fmt.clearBackground()
            elif code in table:  # 30-37 / 90-97：前景
                set_color(table[code])
            elif 40 <= code <= 47:  # 背景
                set_color(table[code - 10], background=True)
            elif 100 <= code <= 107:  # 亮色背景
                set_color(table[code - 10], background=True)
            elif code in (38, 48):  # 256 色 / 真彩
                background = code == 48
                if i < len(codes) and codes[i] == 5 and i + 1 < len(codes):
                    set_color(cls.color256(codes[i + 1], dark), background)
                    i += 2
                elif i < len(codes) and codes[i] == 2 and i + 3 < len(codes):
                    rgb = [min(255, max(0, v)) for v in codes[i + 1:i + 4]]
                    set_color('#%02x%02x%02x' % tuple(rgb), background)
                    i += 4
                else:  # 语法不对：丢掉剩余参数，避免把数字当文本显示
                    i = len(codes)
        return fmt

    @classmethod
    def split(cls, text, fmt, dark=False):
        """把文本拆成「纯文本 + 该段生效的 format」，同时过滤掉不支持的序列。

        Args:
            text: 待处理的文本
            fmt: 上一次调用后仍然生效的 format（跨 write 延续）
            dark: 是否暗色主题

        Returns:
            ``(segments, fmt, pending)``——``segments`` 为 ``[(文本, format)]``；
            ``fmt`` 为末尾仍生效的 format；``pending`` 为**被切断、留待下次处理**的尾部
            （如 ``'\\033[3'``，没有就是空串）。
        """
        segments = []
        pos = i = 0
        n = len(text)
        while i < n:
            if text[i] != '\x1b':
                i += 1
                continue
            found = cls.CSI.match(text, i)
            if found is not None:  # 完整的 CSI
                segments.append((text[pos:i], fmt))
                if found.group(2) == 'm':
                    fmt = cls.sgr(fmt, found.group(1), dark)
                pos = i = found.end()
                continue
            found = cls.OTHER.match(text, i)
            if found is not None:  # 其它完整的转义序列：删掉
                segments.append((text[pos:i], fmt))
                pos = i = found.end()
                continue
            if cls.PARTIAL.match(text, i):  # 尾巴被切断：留给下一次调用
                segments.append((text[pos:i], fmt))
                return segments, fmt, text[i:]
            i += 1  # 零散的 ESC：删掉这个字符
            segments.append((text[pos:i - 1], fmt))
            pos = i
        if pos < n:
            segments.append((text[pos:], fmt))
        return segments, fmt, ''

    @classmethod
    def strip(cls, text):
        """删除文本中的**全部** ANSI 转义序列（含被切断的尾部），返回纯文本。"""
        text = cls.CSI.sub('', text)
        text = cls.OTHER.sub('', text)
        text = cls.PARTIAL.sub('', text)
        return text.replace('\x1b', '')


class OutputWidget(QtWidgets.QWidget):
    #: 控制台保留的最大字符数（超出后从头丢掉一半，见 :meth:`_trim`）
    MAX_CHARS = 10000

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.text_browser = TextBrowser(self)
        layout.addWidget(self.text_browser)

        # ⚠️ 「并行」复选框（CoreParallelEdit，2026-10-26 前叫「内核并行」）**已经搬到主窗口的状态栏**里了
        #    （见 MainWindow.__init__）：它是**全局**开关，而本面板可以不开 / 被收起，
        #    开关就跟着看不见了。不要在这里再放一个 —— 两个 QCheckBox 不会自动同步
        #    （各自只在构造时 setChecked 一次），会显示同一个状态却各说各话。
        #    本类原先的 ``parallel_edit`` 公开属性随之移除（仓内没有外部读取）。

        self.attr_view = AttrView(self)
        self.attr_view.setVisible(False)
        layout.addWidget(self.attr_view)

        # 添加进度条（这也是作为标准输出）
        self.progress_label = QtWidgets.QLabel(self)
        self.progress_bar = QtWidgets.QProgressBar(self)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        self.progress(visible=False)

        # ── 命令输入行 ──
        self._cmd_history = self._load_history()
        self._cmd_history_idx = len(self._cmd_history)
        self._first_cmd = True

        # ── ANSI 状态（跨 write 延续；见 _Ansi）──
        self._ansi_fmt = QtGui.QTextCharFormat()  # 当前仍生效的颜色 / 字体
        self._ansi_pending = ''  # 被 write 切断、留到下一次的转义序列
        self._ansi = self._load_ansi()  # 是否解释 ANSI 转义码

        self.cmd_input = QtWidgets.QLineEdit(self)
        self.cmd_input.setPlaceholderText('输入 Python 命令，按 Enter 执行...')
        self.cmd_input.returnPressed.connect(self._exec_cmd)
        self.cmd_input.installEventFilter(self)
        layout.addWidget(self.cmd_input)

        # 覆盖text_browser的右键菜单
        get_context_menu = self.text_browser.get_context_menu

        def f2():
            menu = get_context_menu()
            menu.addSeparator()
            for ac in self.get_context_actions():
                menu.addAction(ac)
            return menu

        self.text_browser.get_context_menu = f2  # 替换

    def show_attrs(self, **attrs):
        self.attr_view.show_attrs(**attrs)
        self.attr_view.setVisible(self.attr_view.get_count() > 0)

    def progress(
            self, label: Optional[str] = None, val_range: Optional[Union[List[int], Tuple[int, int]]] = None,
            value: Optional[int] = None, visible: Optional[bool] = None):
        """
        显示进度
        """
        if label is not None:
            visible = True
            self.progress_label.setText(label)
        if val_range is not None:
            visible = True
            assert len(val_range) == 2
            self.progress_bar.setRange(*val_range)
        if value is not None:
            visible = True
            self.progress_bar.setValue(value)
        if visible is not None:
            self.progress_bar.setVisible(visible)
            self.progress_label.setVisible(visible)

    def _exec_cmd(self):
        """执行输入的命令."""
        code = self.cmd_input.text().strip()
        self.cmd_input.clear()
        if not code:
            return

        self._cmd_history.append(code)
        self._cmd_history_idx = len(self._cmd_history)
        if len(self._cmd_history) > 500:
            self._cmd_history = self._cmd_history[-500:]
        self._save_history()

        if self._first_cmd:
            self._first_cmd = False
            gui.show_memory()
        self.add_text(f'>>> {code}\n')

        def task():
            try:
                try:
                    c = compile(code, '<console>', 'eval')
                    r = eval(c, app_data.space)
                    if r is not None:
                        print(repr(r))
                except SyntaxError:
                    exec(code, app_data.space)
            except Exception as ex:
                print(f'{type(ex).__name__}: {ex}', file=sys.stderr)

        if gui.exists():
            gui.start_func(task, add_history=False)
        else:
            task()

    @property
    def _history_file(self):
        from zmlx.system import app_data
        return app_data.temp('console_cmd_history.txt')

    def _load_history(self):
        try:
            if os.path.isfile(self._history_file):
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    return [line.rstrip('\n') for line in f if line.strip()]
        except Exception:
            pass
        return []

    def _save_history(self):
        try:
            from zmlx.system import make_parent
            with open(make_parent(self._history_file), 'w', encoding='utf-8') as f:
                for line in self._cmd_history[-500:]:
                    f.write(line + '\n')
        except Exception:
            pass

    def eventFilter(self, obj, event):
        """拦截输入框的上下箭头，浏览命令历史."""
        if obj == self.cmd_input and event.type() == QtCore.QEvent.Type.KeyPress:
            key = event.key()
            if key == QtCore.Qt.Key.Key_Up:
                if self._cmd_history:
                    self._cmd_history_idx = max(0, self._cmd_history_idx - 1)
                    self.cmd_input.setText(self._cmd_history[self._cmd_history_idx])
                return True
            elif key == QtCore.Qt.Key.Key_Down:
                if self._cmd_history:
                    idx = min(len(self._cmd_history) - 1, self._cmd_history_idx + 1)
                    if idx < len(self._cmd_history):
                        self._cmd_history_idx = idx
                        self.cmd_input.setText(self._cmd_history[idx])
                return True
        return super().eventFilter(obj, event)

    def get_context_actions(self):
        act_ansi = create_action(
            self, 'ANSI 颜色', slot=self._toggle_ansi)
        act_ansi.setCheckable(True)
        act_ansi.setChecked(self._ansi)
        result = [act_ansi, create_action(
            self, '隐藏', icon='console',
            slot=lambda: gui.hide_console())]
        if gui.is_running():
            if gui.is_paused():
                result.append(create_action(
                    self, '继续', icon='begin',
                    slot=lambda: gui.set_paused(False))
                )
            else:
                result.append(create_action(
                    self, '暂停', icon='pause',
                    slot=lambda: gui.set_paused(True))
                )
            result.append(create_action(
                self, '停止', icon='stop',
                slot=lambda: gui.stop_console())
            )
        else:
            if get_last_exec_history() is not None:
                result.append(create_action(
                    self, '再次运行', slot=lambda: gui.start_last())
                )
                result.append(create_action(
                    self, '清除历史', slot=clear_exec_history)
                )
            result.append(create_action(
                self, '脚本运行历史',
                slot=lambda: gui.show_code_history(
                    folder=app_data.root('console_history'),
                    caption='运行历史'))
            )
            result.append(create_action(
                self, '输出历史',
                slot=gui.show_output_history)
            )

        if app_data.get('DISABLE_PAUSE', False):
            result.append(create_action(
                self, '启用pause', slot=lambda: app_data.put('DISABLE_PAUSE', False))
            )
        else:
            result.append(create_action(
                self, '禁用pause', slot=lambda: app_data.put('DISABLE_PAUSE', True))
            )

        return result

    @staticmethod
    def _load_ansi():
        """是否解释 ANSI 转义码（持久化在 ``console_ansi``，右键菜单可切换）。"""
        return app_data.getenv(
            key='console_ansi', default='Yes', ignore_empty=True) != 'No'

    @staticmethod
    def plain_text(text):
        """返回去掉全部 ANSI 转义序列的纯文本（状态栏等只放一行的地方用）。"""
        return _Ansi.strip(str(text))

    def _dark(self):
        """当前是否暗色主题（决定 ANSI 基础 8 色用哪一套取色）。

        ⚠️ 这里**不**调 ``gui.in_dark_mode()``：那要经过 GuiApi 的通道往返，而本方法在
        ``print`` 的热路径上（每写一次都要判），直接读控件自己的调色板就够了。
        """
        base = self.text_browser.palette().color(QtGui.QPalette.ColorRole.Base)
        return base.lightness() < 128

    def _toggle_ansi(self):
        """右键菜单：切换是否解释 ANSI 转义码（状态落盘，下次启动仍然生效）。"""
        self._ansi = not self._ansi
        app_data.setenv(key='console_ansi', value='Yes' if self._ansi else 'No')

    def add_text(self, text, ansi=None):
        """
        在控制台末尾追加文本。

        Args:
            text: 要追加的文本。其中的 ANSI 转义码会被解释成颜色，控件不支持的序列
                （擦行 / 清屏 / 光标定位 / OSC……）会被**删除**，不会显示成乱码
            ansi: 是否解释 ANSI 转义码。None（默认）表示按用户设置 ``console_ansi``
                （右键菜单可切换）；False 表示只过滤转义码、不着色
        """
        if not isinstance(text, str):
            text = str(text)
        if ansi is None:
            ansi = self._ansi
        if ansi:
            segments, self._ansi_fmt, self._ansi_pending = _Ansi.split(
                self._ansi_pending + text, self._ansi_fmt, dark=self._dark())
        else:
            segments = [(_Ansi.strip(self._ansi_pending + text), None)]
            self._ansi_pending = ''
        self._insert(segments)

    def _insert(self, segments):
        """把 ``[(文本, format)]`` 追加到末尾（format 为 None 表示跟随主题）。

        ⚠️ 必须走**控件自己的光标**（``moveCursor`` + ``setCurrentCharFormat`` +
        ``insertPlainText``），不能另建 ``QTextCursor`` 直接插：那样控件不会跟着滚动 ——
        实测追加 300 行后滚动条仍停在顶部（另建的 cursor 与控件光标无关）。
        ⚠️ 每段都要显式 ``setCurrentCharFormat``：当前格式会一直生效，不设置的话下一段
        会继承上一段的颜色。
        """
        self.text_browser.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        for text, fmt in segments:
            if len(text) > 0:
                self.text_browser.setCurrentCharFormat(
                    QtGui.QTextCharFormat() if fmt is None else fmt)
                self.text_browser.insertPlainText(text)
        self._trim()

    def _trim(self):
        """字符数超过 :attr:`MAX_CHARS` 时，从头丢掉一半。

        ⚠️ 必须用光标删除。早先是 ``toPlainText()`` / ``setPlainText()`` 整篇重写，那会把
        所有段落的格式**统一成当前格式**（实测整篇变成同一个颜色），而且每次追加都要复制
        近万个字符；光标删除保留其余文本的格式，也更快。
        """
        doc = self.text_browser.document()
        while doc.characterCount() > self.MAX_CHARS:
            cursor = QtGui.QTextCursor(doc)
            cursor.setPosition(0)
            cursor.setPosition(
                doc.characterCount() // 2,
                QtGui.QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()

    def set_text(self, text):
        self.text_browser.clear()
        self._ansi_fmt = QtGui.QTextCharFormat()
        self._ansi_pending = ''
        self.add_text(text)

    #: 历史文件扩展名。用 HTML 而不是 txt：颜色 / 粗体等是存在文本片段的
    #: ``QTextCharFormat`` 里的，``toPlainText()`` 会把它们**全部丢掉**，于是重启后
    #: 只剩无色文本（2026-10-26 修的就是这个）；``toHtml()`` 才能把它们写进文件。
    SUFFIX = '.html'
    #: 非 HTML 的老历史文件（旧版本存的是纯文本）
    SUFFIX_LEGACY = '.txt'

    def load_text(self, filename):
        """从历史文件恢复输出内容（``.html`` 保留颜色，``.txt`` 按纯文本解析）。

        Args:
            filename: 历史文件路径。按**扩展名**决定走富文本还是纯文本 —— 旧版本存的
                是 ``.txt``（纯文本，颜色本就已丢失），仍要能打开。
        """
        try:
            if os.path.isfile(filename):
                # ⚠️ 必须显式 encoding='utf-8'：默认会用系统编码（中文 Windows 上是 GBK），
                #    而文件是 UTF-8 写的，含中文时抛 UnicodeDecodeError（被下面的 except
                #    吞成空内容，现场表现为「历史加载不出来」）。
                if str(filename).lower().endswith(self.SUFFIX):
                    self.set_html(filename)
                else:
                    with open(filename, 'r', encoding='utf-8') as file:
                        self.set_text(file.read())
        except Exception as err2:
            print(err2)
            self.text_browser.setPlainText('')

    def save_text(self, filename):
        """把当前输出保存为历史文件（``.html`` 保留颜色，其余按纯文本保存）。"""
        try:
            text = (self.text_browser.toHtml()
                    if str(filename).lower().endswith(self.SUFFIX)
                    else self.text_browser.toPlainText())
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(text)
        except Exception as err2:
            print(err2)

    def get_html(self):
        """返回当前输出的 HTML（保留颜色 / 粗体等全部字符格式）。"""
        return self.text_browser.toHtml()

    def set_html(self, filename):
        """用历史 HTML 文件的内容替换当前输出（保留颜色 / 粗体等字符格式）。

        ⚠️ 与 :meth:`set_text` 一样要复位 :attr:`_ansi_fmt` / :attr:`_ansi_pending`：
        否则重启后第一条 ``print`` 会**继承**上一份输出残留的 ANSI 状态，把新内容
        染成旧颜色。
        """
        if not os.path.isfile(filename):
            return
        with open(filename, 'r', encoding='utf-8') as file:
            html = file.read()
        self.text_browser.setHtml(html)
        self._ansi_fmt = QtGui.QTextCharFormat()
        self._ansi_pending = ''

    def get_plain_text(self):
        return self.text_browser.toPlainText()


def test_1():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = OutputWidget()
    w.resize(800, 600)
    w.show()

    # 示例数据：能看出控件的主要能力（ANSI 上色 + 过滤不支持的序列）
    w.add_text('普通文本  \033[31m红\033[32m绿\033[33m黄\033[34m蓝\033[0m 普通文本\n')
    w.add_text('\033[1;31m粗体红\033[0m \033[4m下划线\033[24m \033[3m斜体\033[23m\n')
    w.add_text('\033[38;5;208m256 色\033[0m \033[38;2;255;0;255m真彩\033[39m\n')
    w.add_text('不支持的序列会被删除: [\033[2J\033[1;1H\033[K]\033]0;标题\007<\n')
    w.add_text('被切断的序列也能续上: \033[3' + '5m紫色\033[0m\n')

    sys.exit(app.exec())


if __name__ == "__main__":
    test_1()
