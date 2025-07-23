import os
import time

from zml import app_data, get_hash, log as zml_log
from zmlx.io.json_ex import read, write
from zmlx.ui import gui
from zmlx.ui.alg import create_action
from zmlx.ui.pyqt import QtWidgets
from zmlx.ui.widget import Label


def add_message(text, code=None, color=None):
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


def setup_ui():
    def show_messages():
        def oper(w):
            w.gui_restore = 'gui.show_messages()'
            w.refresh()

        gui.get_widget(MessageEdit, caption='通知', oper=oper,
                       on_top=True, caption_color='red', icon='info')

    gui.add_func('show_messages', show_messages)

    def get_text():
        return f'通知({get_message_count()})'

    gui.add_action(
        menu='显示', text=get_text, slot=show_messages,
        name='show_messages',
        is_visible=lambda: get_message_count() > 0,
        on_toolbar=True, icon='info',
    )

    def add_and_show(text, code=None, color=None):
        add_message(text, code, color)
        show_messages()
        zml_log(text)
        gui.refresh_action('show_messages')

    gui.add_func('add_message', add_and_show)


def main():
    from zmlx.alg.sys import first_execute
    if first_execute(__file__):
        gui.execute(func=setup_ui, keep_cwd=False, close_after_done=False)


if __name__ == '__main__':
    main()

