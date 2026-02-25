import os

from zml import app_data
from zmlx.ui.alg import create_action
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtGui, QtWidgets
from zmlx.ui.widget.text_browser import TextBrowser


class OutputWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.text_browser = TextBrowser(self)
        layout.addWidget(self.text_browser)
        # 添加进度条（这也是作为标准输出）
        self.progress_label = QtWidgets.QLabel(self)
        self.progress_bar = QtWidgets.QProgressBar(self)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        self.progress(visible=False)
        # 覆盖text_browser的右键菜单
        get_context_menu = self.text_browser.get_context_menu

        def f2():
            menu = get_context_menu()
            menu.addSeparator()
            for ac in self.get_context_actions():
                menu.addAction(ac)
            return menu

        self.text_browser.get_context_menu = f2  # 替换

    def progress(
            self, label=None, val_range=None, value=None, visible=None):
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

    def get_context_actions(self):
        result = [create_action(
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
            result.append(create_action(
                self, '重新执行', slot=lambda: gui.start_last())
            )
            result.append(create_action(
                self, '运行历史',
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

    def add_text(self, text):
        self.text_browser.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.text_browser.insertPlainText(text)
        while self.text_browser.document().characterCount() > 10000:
            fulltext = self.text_browser.toPlainText()
            fulltext = fulltext[-int(len(fulltext) / 2): -1]
            self.text_browser.setPlainText(fulltext)

    def set_text(self, text):
        self.text_browser.setPlainText(text)
        self.text_browser.moveCursor(QtGui.QTextCursor.MoveOperation.End)

    def load_text(self, filename):
        try:
            if os.path.isfile(filename):
                with open(filename, 'r') as file:
                    self.set_text(file.read())
        except Exception as err2:
            print(err2)
            self.text_browser.setPlainText('')

    def save_text(self, filename):
        try:
            with open(filename, 'w') as file:
                file.write(self.text_browser.toPlainText())
        except Exception as err2:
            print(err2)
