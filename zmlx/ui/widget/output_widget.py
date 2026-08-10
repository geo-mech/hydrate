import os
from typing import Optional, Tuple, List, Union

from zmlx.system import app_data
from zmlx.ui.alg import create_action, get_last_exec_history, clear_exec_history
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets
from zmlx.ui.widget._parallel import CoreParallelEdit
from zmlx.ui.widget.attr_view import AttrView
from zmlx.ui.widget.text_browser import TextBrowser


class OutputWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.text_browser = TextBrowser(self)
        layout.addWidget(self.text_browser)

        self.parallel_edit = CoreParallelEdit(self)
        layout.addWidget(self.parallel_edit)

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
                print(f'{type(ex).__name__}: {ex}')

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


def test_1():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = OutputWidget()
    w.resize(800, 600)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test_1()
