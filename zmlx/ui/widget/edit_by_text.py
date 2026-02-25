from typing import Any

from zmlx.ui.alg import create_action
from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.widget import CodeEdit


class CodeEditEx(CodeEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.context_actions = []

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        for action in self.context_actions:
            menu.addAction(action)
        menu.exec(event.globalPos())


class ObjEditByText(QtWidgets.QWidget):
    """
    将所有的数据都转化为字符串来进行编辑
    """
    sig_changed = QtCore.pyqtSignal()  # 右键-应用的时候触发

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.code_edit = CodeEditEx(self)
        main_layout.addWidget(self.code_edit)
        self.code_edit.context_actions = [
            create_action(self, '重置', slot=lambda: self.set_data(self._data)),
            create_action(self, '应用', slot=self.sig_changed.emit),
        ]

    def set_data(self, data: Any):
        self._data = data
        self.code_edit.setText("value = " + repr(self._data))

    def get_data(self):
        try:
            space = {}
            try:
                exec(self.code_edit.get_text(), space)
            except Exception as err:
                print(err)
            data = space.get('value', None)
            if type(data) == type(self._data):
                return data
            else:
                print(f"类型错误: 期望{type(self._data)}，但得到{type(data)}")
                return self._data
        except Exception as err:
            print(err)
            return self._data


def test():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = ObjEditByText()
    w.sig_changed.connect(lambda: print(w.get_data()))
    w.set_data(3)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test()
