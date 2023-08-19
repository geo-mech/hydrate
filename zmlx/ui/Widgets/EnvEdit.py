from PyQt5 import QtWidgets
from zml import app_data
import sys


class LineEdit(QtWidgets.QLineEdit):

    def __init__(self, parent=None, key=None):
        super().__init__(parent)
        self.key = None
        self.setKey(key)
        self.editingFinished.connect(self.save)

    def setKey(self, key):
        self.key = key
        self.load()

    def load(self):
        if self.key is not None:
            self.setText(app_data.getenv(self.key, encoding='utf-8', default=''))

    def save(self):
        if self.key is not None:
            app_data.setenv(key=self.key, value=self.text(), encoding='utf-8')


class ComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None, key=None):
        super().__init__(parent)
        self.key = key
        self.currentTextChanged.connect(self.save)

    def setKey(self, key):
        self.key = key
        self.load()

    def load(self):
        if self.key is not None:
            self.setCurrentText(app_data.getenv(self.key, encoding='utf-8', default=''))

    def save(self):
        if self.key is not None:
            app_data.setenv(key=self.key, value=self.currentText(), encoding='utf-8')


class MultiLineEdit(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid = QtWidgets.QGridLayout(self)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 2)
        self.items = []

    def add(self, key, label=None, items=None):
        if label is not None:
            self.grid.addWidget(QtWidgets.QLabel(label), len(self.items), 0)
        assert isinstance(key, str)
        if items is None:
            item = LineEdit()
            item.setKey(key)
            self.grid.addWidget(item, len(self.items), 1)
            self.items.append(item)
        else:
            item = ComboBox()
            item.addItems(items)
            item.setKey(key)
            self.grid.addWidget(item, len(self.items), 1)
            self.items.append(item)


def test1():
    app = QtWidgets.QApplication(sys.argv)
    w = MultiLineEdit()
    w.add(key='name', label='name')
    w.add(key='age', label='age')
    w.add(key='性别', label='性别', items=['男', '女', '不确定'])
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    test1()
