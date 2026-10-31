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
"""

import os
import time

from zmlx.system import app_data, execute_once, get_hash, log as zml_log
from zmlx.io.json_ex import read, write
from zmlx.ui import gui
from zmlx.ui.alg import create_action
from zmlx.ui.pyqt import QtWidgets
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


class MessageEdit(QtWidgets.QTableWidget):
    class RemoveButton(QtWidgets.QToolButton):
        def __init__(self, parent, key, refresh):
            super().__init__(parent)
            self.setText('x')
            self.key = key
            self.refresh = refresh
            self.clicked.connect(self.on_clicked)

        def on_clicked(self):
            del_message(self.key)
            self.refresh()
            gui.refresh_action('show_messages')  # 刷新Action

    class CodeExecute:
        def __init__(self, code):
            self.code = code

        def __call__(self):
            if isinstance(self.code, str):
                if gui.exists():
                    gui.start(self.code)
                else:
                    print(self.code)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(4)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        headers = ["#", "时间", "消息", ""]
        self.setHorizontalHeaderLabels(headers)
        header = self.horizontalHeader()
        mode = QtWidgets.QHeaderView.ResizeMode
        header.setSectionResizeMode(0, mode.ResizeToContents)
        header.setSectionResizeMode(1, mode.ResizeToContents)
        header.setSectionResizeMode(2, mode.Stretch)
        header.setSectionResizeMode(3, mode.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.refresh()

    def refresh(self):
        messages = get_messages()
        keys = list(messages)
        keys.sort(key=lambda x: messages[x]['time'])

        self.setRowCount(len(keys))
        for row, key in enumerate(keys):
            self.setItem(row, 0, QtWidgets.QTableWidgetItem(str(row + 1)))
            data = messages[key]
            # 时间
            local_time = time.localtime(data['time'])
            formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
            self.setItem(row, 1, QtWidgets.QTableWidgetItem(
                formatted_time))
            # 消息
            label = Label(parent=self, text=data.get('text', ''),
                          double_clicked=MessageEdit.CodeExecute(
                              data.get('code', None)))
            label.setWordWrap(True)
            color = data.get('color', None)
            if color:
                label.setStyleSheet(f"color: {color};")
            self.setCellWidget(row, 2, label)
            # 关闭
            self.setCellWidget(
                row, 3,
                MessageEdit.RemoveButton(self, key, self.refresh))

        if self.rowCount() == 0:  # 尝试关闭标签
            gui.close_tab_object(self)

    def contextMenuEvent(self, event):
        # 创建菜单并添加清除动作
        self.get_context_menu().exec(event.globalPos())

    def get_context_menu(self):
        menu = QtWidgets.QMenu(self)
        menu.addAction(create_action(self, "刷新", icon='refresh',
                                     slot=self.refresh))

        def clear():
            del_all_messages()
            self.refresh()

        menu.addAction(create_action(self, '清空', icon='clean',
                                     slot=clear))

        return menu


def test_4():
    import sys
    from zmlx.ui.pyqt import QtWidgets
    app = QtWidgets.QApplication(sys.argv)
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
