"""通知消息中心（``MessageEdit``）+「显示 → 通知」菜单入口.

**本文件自含**：控件 :class:`MessageEdit`、消息的**落盘 API**（``add_message`` /
``get_messages`` / ``del_message`` …）与菜单入口 ``gui.show_messages`` 都在这里。

⚠️ **2026-10-31 由 ``zmlx/ui/tabs/message.py`` 搬到 ``setups/``**（原模块删除、
**不留垫片**：``tabs/__init__.py`` 的静态转发与 ``widget/message.py`` 的兼容垫片
一并删除）。控件本体与公开函数一字未改。

为什么在 ``setups/`` 而不是 ``tabs/`` 或插件
---------------------------------------------------

判据是 ``setups/AGENTS.md`` §1 那条：**关掉它，软件还能不能正常用？**

- **不能** —— 它是**基础设施**，不是「可关闭的扩展」：``gui.add_message(...)`` 是
  ``main.py``（警告 / 异常通道）、``plugins/_alg.py``（插件加载失败）等处的**通用出口**；
  把它做成插件，就等于允许用户关掉「告警去哪看」。
- 也**不该**待在 ``tabs/`` —— 它带来的是「落盘 API + 菜单入口」这整块装配，
  而不只是一个标签页控件；``tabs/`` 收的是「只被装配层打开成页面的顶层控件」。

于是它和 ``license_query.py`` / ``plugin_placeholders.py`` 一样，是**必加载**的装配，
住 ``setups/``。⚠️ 由 ``setups/__init__.py`` 的 ``setup_ui()`` 统一调用
（那里是**唯一**的登记点）。

⚠️ 命令名与菜单项**一字未改**：``gui.show_messages`` / ``gui.add_message`` /
``gui.message``，菜单 action ``name='show_messages'``（「显示 → 通知」）。
历史标签页（``gui_restore`` 存的就是 ``gui.show_messages()``）照常恢复。

Created by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-31: 由 ``zmlx/ui/tabs/message.py`` 搬到
    ``zmlx/ui/setups/message.py``（原模块删除、**不留垫片**）；
    ``setup_ui`` 补 ``@execute_once``，命令名 / action name 均未变。
Modified by DeepSeek, 2026-11-02: 界面重排 + 复制 / 清空 / 刷新变成可见按钮。
    控件由「裸露的 ``QTableWidget``」改为组合控件：顶部工具条（计数 + 复制全部 /
    刷新 / 清空）+ 消息表格（没有消息时显示「暂无通知」）；每行加「复制」按钮，
    右键菜单保留「复制选中消息」。顺带修掉多行消息只显示一行的问题。
    ⚠️ 类名 ``MessageEdit``、命令名 ``gui.show_messages``、标签页标题「通知」
    一律未变（``gui_restore`` 靠它们恢复历史标签页）。
"""

import os
import time

from zmlx.system import app_data, execute_once, get_hash, log as zml_log
from zmlx.io.json_ex import read, write
from zmlx.ui import gui
from zmlx.ui.alg import create_action
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets
from zmlx.ui.widgets.label import Label


def add_message(text, *, code=None, color=None):
    fname = app_data.root('message', get_hash(text) + '.json')
    data = dict(text=text, code=code, color=color)
    write(fname, data)

    while get_message_count() > 50:
        data = get_messages()
        keys = list(data)
        keys.sort(key=lambda x: data[x]['time'])
        del_message(keys[0])


def test_1():
    for idx in range(6):
        add_message(f'M{idx}', code=f'{idx}', color='green')
        time.sleep(0.1)


def get_message_count():
    folder = app_data.root('message')
    if not os.path.isdir(folder):
        return 0
    return len(os.listdir(folder))


def get_messages():
    folder = app_data.root('message')
    if not os.path.isdir(folder):
        return {}
    result = {}
    for name in os.listdir(folder):
        if name.endswith('.json'):
            try:
                path = os.path.join(folder, name)
                data = read(path)
                data['time'] = os.path.getmtime(path)
                result[name] = data
            except Exception as err:
                print(err)
    return result


def test_2():
    data = get_messages()
    print(data)
    print(list(data))


def del_message(name):
    path = app_data.root('message', name)
    if os.path.isfile(path):
        os.remove(path)


def del_all_messages():
    keys = list(get_messages())
    for key in keys:
        del_message(key)


def test_3():
    data = get_messages()
    for key, val in data.items():
        del_message(key)
        break
    print(get_messages())


class MessageEdit(QtWidgets.QWidget):
    """通知消息中心（「显示 → 通知」打开的那一页）.

    布局：**顶部工具条**（计数 + 复制全部 / 刷新 / 清空）→ **消息表格**（没有消息时
    换成一句「暂无通知」）。以前就是一个裸露的 ``QTableWidget``：清空 / 刷新都藏在
    右键菜单里，连「有几条消息」都得数行才知道。

    - 计数与操作按钮常驻在表格**外围**，不用右键也能点到；
    - 每行仍保留「复制」「删除」两个行内按钮 —— 行内动作就地解决，不必先选中；
    - 多行消息按内容撑高行（原先行高锁死在一行，长消息被截断）。

    ⚠️ **类名没变**：``gui.show_messages()`` 的标签页状态里存的是命令原文
    （``gui_restore`` 重启重放），而 ``get_widget`` 按「类型 + 标题」复用页面 ——
    类名 / 标题一改，历史标签页就恢复不了。改界面结构不影响那条约定。
    """

    class RemoveButton(QtWidgets.QToolButton):
        def __init__(self, parent, key, refresh):
            super().__init__(parent)
            self.setText('x')
            self.setToolTip('删除这条通知')
            self.key = key
            self.refresh = refresh
            self.clicked.connect(self.on_clicked)

        def on_clicked(self):
            del_message(self.key)
            self.refresh()
            gui.refresh_action('show_messages')  # 刷新Action

    class CopyButton(QtWidgets.QToolButton):
        """复制消息正文到剪贴板.

        连的是**绑定方法** :meth:`on_clicked`（不是 lambda）：控件销毁时 Qt 会自动
        断连，不会在迟到的事件里碰已删除的对象。
        """

        def __init__(self, parent, text):
            super().__init__(parent)
            self.setText('复制')
            self.setToolTip('复制这条消息的内容到剪贴板')
            self._text = text
            self.clicked.connect(self.on_clicked)

        def on_clicked(self):
            MessageEdit.copy_to_clipboard(self._text)

    class MessageLabel(Label):
        """通知正文（多行、自动换行、可框选、双击执行代码）.

        高度**由表格逐行设置**（见 :meth:`_fit_row_heights`），这里只负责按给定宽度
        算出「这一行需要多高」。
        """

        def row_height(self, width):
            """在给定宽度下，这段正文需要多高（按字体度量量出换行结果）.

            ``QLabel`` 没有 ``document()``（那是 ``QTextEdit`` 的），而它的
            ``heightForWidth`` / ``sizeHint`` 在「还没拿到宽度」时给出的数不可信，
            所以自己用 :class:`QtGui.QFontMetrics` 量：``boundingRect`` 带上换行标志，
            就是 Qt 实际会画出来的高度。
            """
            flags = int(QtCore.Qt.TextFlag.TextWordWrap)
            metrics = QtGui.QFontMetrics(self.font())
            rect = metrics.boundingRect(
                QtCore.QRect(0, 0, max(width, 1), 100000), flags, self.text())
            return rect.height() + 4  # 上下各留 2 px，免得掐字

    class CodeExecute:
        def __init__(self, code):
            self.code = code

        def __call__(self):
            if isinstance(self.code, str):
                if gui.exists():
                    gui.start(self.code)
                else:
                    print(self.code)

    #: 表格列号（列顺序变了只改这里）
    COL_INDEX, COL_TIME, COL_TEXT, COL_COPY, COL_CLOSE = range(5)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._texts = []  # 行号 -> 消息正文（「复制全部」「复制选中」用）
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        """搭出「顶部工具条 + 表格 / 空状态」两段式界面."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # ---- 顶部工具条 ----
        bar = QtWidgets.QHBoxLayout()
        bar.setSpacing(6)
        self.summary = QtWidgets.QLabel()
        bar.addWidget(self.summary)
        bar.addStretch(1)

        # ⚠️ 按钮**不按「有没有消息」置灰**：置灰在用户眼里就是「控件坏了」
        #   （见 widgets/AGENTS.md「'置灰'等于'这里不能改'」）。没有消息时点
        #   「复制全部」只在状态栏说一句，界面上另有「暂无通知」把情况说清楚。
        self.btn_copy_all = QtWidgets.QToolButton()
        self.btn_copy_all.setText('复制全部')
        self.btn_copy_all.setToolTip('把所有通知的内容复制到剪贴板（每条之间空一行）')
        self.btn_copy_all.clicked.connect(self.copy_all)
        bar.addWidget(self.btn_copy_all)

        self.btn_refresh = QtWidgets.QToolButton()
        self.btn_refresh.setText('刷新')
        self.btn_refresh.setToolTip('重新读取通知列表')
        self.btn_refresh.clicked.connect(self.refresh)
        bar.addWidget(self.btn_refresh)

        self.btn_clear = QtWidgets.QToolButton()
        self.btn_clear.setText('清空')
        self.btn_clear.setToolTip('删除全部通知')
        self.btn_clear.clicked.connect(self.clear_all)
        bar.addWidget(self.btn_clear)

        layout.addLayout(bar)

        # ---- 表格 ----
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['#', '时间', '消息', '', ''])
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(True)
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        mode = QtWidgets.QHeaderView.ResizeMode
        # ⚠️ 序号 / 时间列**不能**用 ResizeToContents：它按「表头文字 + 最宽单元格」
        #   算宽度，而表头 ``#`` 在 C++ 侧是宽字符、``时间`` 是中文 —— 实测被撑到
        #   200 px 以上（时间只有 19 个 ASCII 字符，宽出三四倍）。这两列内容长度固定，
        #   直接给固定宽度；消息列吃掉剩下的空间。
        header.setSectionResizeMode(self.COL_INDEX, mode.Fixed)
        header.setSectionResizeMode(self.COL_TIME, mode.Fixed)
        header.setSectionResizeMode(self.COL_TEXT, mode.Stretch)
        header.setSectionResizeMode(self.COL_COPY, mode.ResizeToContents)
        header.setSectionResizeMode(self.COL_CLOSE, mode.ResizeToContents)
        metrics = QtGui.QFontMetrics(self.table.font())
        self.table.setColumnWidth(self.COL_INDEX, 40)
        self.table.setColumnWidth(self.COL_TIME, metrics.horizontalAdvance('0000-00-00 00:00:00') + 16)
        self.table.verticalHeader().setVisible(False)
        # ⚠️ **行高必须自己管**（Fixed），不能用 ResizeToContents：后者按单元格
        #    控件的 ``sizeHint().height()`` 定高，而自动换行的 QLabel 的 sizeHint
        #    按自己的首选用法算 —— 实测把 126 px 的内容撑成 196 px，于是正文只顶上
        #    半截、其余全空（2026-11-02 实测）。换行后的高度只有表格知道（它知道列宽），
        #    所以由 :meth:`_fit_row_heights` 逐行 setRowHeight。
        self.table.verticalHeader().setSectionResizeMode(mode.Fixed)
        self.table.cellDoubleClicked.connect(self._on_double_clicked)
        # 表格自己的右键菜单（本控件是容器，事件不会冒泡到它的 contextMenuEvent）
        self.table.contextMenuEvent = self._on_table_context_menu
        layout.addWidget(self.table, stretch=1)

        # ---- 空状态 ----
        self.empty_label = QtWidgets.QLabel('暂无通知')
        self.empty_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Preferred)
        layout.addWidget(self.empty_label, stretch=1)

    def sizeHint(self):
        # 打开成标签页时给一个能一眼看完几条通知的初始尺寸（表格/空状态自带拉伸）
        hint = super().sizeHint()
        return QtCore.QSize(max(hint.width(), 640), max(hint.height(), 320))

    def showEvent(self, event):
        """显示时按**真实列宽**重算行高（``refresh()`` 跑的时候列宽还不可信）."""
        super().showEvent(event)
        self._fit_row_heights()

    def resizeEvent(self, event):
        """窗口变宽 / 变窄后间隔一拍重算行高.

        ⚠️ 必须用 ``QTimer.singleShot(0, ...)`` 而不能在这里直接算：``ResizeEvent``
        到达时拉伸列（Stretch）的新宽度还没落到视图上，当场量的还是旧宽度。
        ⚠️ 计时器**不传 self 作 parent**，且连的是绑定方法 —— 控件销毁后回调因
        ``QTimer.singleShot`` 已排队而不保证被拦下，所以回调里先判一次是否已销毁。
        """
        super().resizeEvent(event)
        QtCore.QTimer.singleShot(0, self._fit_row_heights)

    # ------------------------------------------------------------ 剪贴板

    @staticmethod
    def copy_to_clipboard(text):
        """把文本放进系统剪贴板，并在状态栏提示一句.

        拿不到剪贴板（极端环境）时退回 ``print`` —— 至少内容还能被看到、被控制台的
        「输出历史」留住，而不是点了按钮却毫无反应。
        """
        clipboard = QtWidgets.QApplication.clipboard()
        if clipboard is None:
            print(text)
            return
        clipboard.setText(text)
        gui.status('已复制通知内容', 3000)

    def _join(self, rows, empty_hint):
        """按给定行号拼出文本；没有内容时在状态栏说明为什么没复制."""
        texts = [self._texts[row] for row in rows if 0 <= row < len(self._texts)]
        if not texts:
            gui.status(empty_hint, 3000)
            return
        MessageEdit.copy_to_clipboard('\n\n'.join(texts))

    def copy_all(self):
        """复制全部通知正文（按表格顺序，每条之间空一行）."""
        self._join(range(len(self._texts)), '当前没有通知可复制')

    def copy_selected(self):
        """复制所有（整行）选中的通知正文，每条之间空一行."""
        rows = sorted({index.row() for index in self.table.selectedIndexes()})
        self._join(rows, '请先选中要复制的通知')

    def clear_all(self):
        """清空全部通知（清完本页没有内容，:meth:`refresh` 会试着收起标签）."""
        del_all_messages()
        self.refresh()

    def _on_double_clicked(self, row, column):
        """双击消息列 = 执行它附带的那段代码（原来连在 ``Label`` 的双击上）."""
        if column != self.COL_TEXT:
            return
        label = self.table.cellWidget(row, self.COL_TEXT)
        if label is not None:
            label.sig_double_clicked.emit()

    # ------------------------------------------------------------ 布局

    def _fit_row_heights(self):
        """让每行的高度容得下「消息列当前宽度」下的换行结果.

        ⚠️ 第一次判断 ``self.table`` **在 try 里**：``resizeEvent`` 用
        ``QTimer.singleShot(0, self._fit_row_heights)`` 排了一次调用，控件在那之前
        被销毁（关标签页或清空后自动收页）时，访问已删除的 C++ 对象会抛
        ``RuntimeError``。这类「迟到调用」开头必须带兜底，不能靠运气。
        """
        try:
            table = self.table
            hidden = table is None or table.isHidden()
        except RuntimeError:
            return
        if hidden or table.rowCount() == 0:
            return
        width = table.columnWidth(self.COL_TEXT) - 8
        if width <= 0:  # 还没布局完：等 showEvent / 下次 refresh
            return
        minimum = table.verticalHeader().defaultSectionSize()
        for row in range(table.rowCount()):
            label = table.cellWidget(row, self.COL_TEXT)
            if isinstance(label, MessageEdit.MessageLabel):
                height = max(label.row_height(width), minimum)
                if table.rowHeight(row) != height:
                    table.setRowHeight(row, height)

    # ------------------------------------------------------------ 刷新

    def refresh(self):
        """重新读取消息目录并重建表格."""
        messages = get_messages()
        keys = list(messages)
        keys.sort(key=lambda x: messages[x]['time'])

        table = self.table
        self._texts = []
        table.setRowCount(len(keys))
        for row, key in enumerate(keys):
            data = messages[key]
            text = data.get('text', '')
            self._texts.append(text)
            table.setItem(row, self.COL_INDEX,
                          QtWidgets.QTableWidgetItem(str(row + 1)))
            local_time = time.localtime(data['time'])
            formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
            item = QtWidgets.QTableWidgetItem(formatted_time)
            # 单行文本在（可能很高的）行里垂直居中，与靠上的正文错开 —— 时间读起来
            # 像「这条消息的旁注」，而不是正文的一部分。
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, self.COL_TIME, item)
            # 消息
            label = MessageEdit.MessageLabel(
                parent=table, text=text,
                double_clicked=MessageEdit.CodeExecute(
                    data.get('code', None)))
            label.setWordWrap(True)
            # 单元格控件里的文本默认「可选中、但不可聚焦」—— 不给焦点，
            # Ctrl+C 就到不了它。显式给上，用户也能在正文里框选一部分再复制。
            label.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
                | QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard)
            color = data.get('color', None)
            if color:
                label.setStyleSheet(f"color: {color};")
            # 多行消息时行可以很高，正文与行内按钮都**靠上**对齐 —— 居中会让几条
            # 消息的正文各从不同高度起笔，看着像没对齐。
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft
                               | QtCore.Qt.AlignmentFlag.AlignTop)
            table.setCellWidget(row, self.COL_TEXT, label)
            # 复制 / 关闭
            table.setCellWidget(row, self.COL_COPY,
                                MessageEdit.CopyButton(table, text))
            table.setCellWidget(row, self.COL_CLOSE,
                                MessageEdit.RemoveButton(table, key, self.refresh))

        count = len(keys)
        self.summary.setText(f'共 {count} 条通知')
        table.setVisible(count > 0)
        self.empty_label.setVisible(count == 0)
        self._fit_row_heights()

        if count == 0:  # 尝试关闭标签
            gui.close_tab_object(self)

    # ------------------------------------------------------------ 右键

    def contextMenuEvent(self, event):
        self.get_context_menu().exec(event.globalPos())

    def _on_table_context_menu(self, event):
        self.get_context_menu().exec(event.globalPos())

    def get_context_menu(self):
        menu = QtWidgets.QMenu(self)
        copy_action = create_action(self, '复制选中消息',
                                    slot=self.copy_selected)
        copy_action.setEnabled(bool(self.table.selectedIndexes()))
        menu.addAction(copy_action)
        menu.addAction(create_action(self, "刷新", icon='refresh',
                                     slot=self.refresh))
        menu.addAction(create_action(self, '清空', icon='clean',
                                     slot=self.clear_all))
        return menu


def test_4():
    import sys

    app = QtWidgets.QApplication(sys.argv)
    # 演示用示例数据。⚠️ 它写的是**真实的**消息目录（与正常使用同一个位置），
    # 所以只加这三句、不碰已有条目；看完点「清空」即可。
    add_message('这是一条短通知。')
    add_message('这是一条很长的通知，用来验证自动换行是否生效：' * 8)
    add_message('带代码的通知（双击正文执行）', code='print("hello")',
                color='green')
    w = MessageEdit()
    w.show()
    sys.exit(app.exec())


@execute_once(file=__file__)
def setup_ui():
    """注册 ``gui.show_messages`` / ``gui.add_message`` / ``gui.message`` 与「显示 → 通知」.

    由 ``setups/__init__.py`` 的 ``setup_ui()`` 调用（唯一登记点）；
    ``@execute_once`` 保证重复调用也不会挂出第二条菜单。
    """

    def show_messages(on_top=True):
        """
        显示消息标签，默认在前端显示
        """

        def oper(w):
            w.gui_restore = 'gui.show_messages()'
            w.refresh()

        gui.get_widget(MessageEdit, caption='通知', oper=oper,
                       on_top=on_top, caption_color='red', icon='info')

    gui.add_func('show_messages', show_messages)

    def get_text():
        return f'通知({get_message_count()})'

    gui.add_action(
        menu='显示', text=get_text, slot=show_messages,
        name='show_messages',
        is_visible=lambda: get_message_count() > 0,
        on_toolbar=True, icon='info',
    )

    def add_and_show(text, *, code=None, color=None):
        add_message(text, code=code, color=color)
        # 为了避免某些频繁的消息，对于添加消息的时候，默认不再强制在前端显示
        # 2026-1-14
        # 如果某个标签在显示的时候，会添加消息，那么，on_top=True会使得这个标签无法正常显示
        show_messages(on_top=False)
        # tag 用消息本身（加 ``message:`` 前缀，与菜单/异常等其它通道的 tag 隔开），
        # 于是**同一条通知每天只落一次盘**。此前不带 tag 是「每次都记」，像
        # ``MainWindow.toolbar_warning`` 这种每次启动都会触发的消息，会把当天的
        # 日志刷成一片重复文本，也淹掉了真正有用的记录。
        zml_log(text, tag=f'message: {text}')
        gui.refresh_action('show_messages')

    gui.add_func('add_message', add_and_show)
    gui.add_func('message', add_and_show)
