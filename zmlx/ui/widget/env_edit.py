from zml import app_data
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtWidgets


class EnvEdit(QtWidgets.QTableWidget):
    class EnvLineEdit(QtWidgets.QLineEdit):

        def __init__(self, parent=None, key=None):
            super().__init__(parent)
            self.key = None
            self.set_key(key)
            self.editingFinished.connect(self.save)

        def set_key(self, key):
            self.key = key
            self.load()

        def load(self):
            if self.key is not None:
                self.setText(
                    app_data.getenv(self.key, encoding='utf-8', default=''))

        def save(self):
            if self.key is not None:
                app_data.setenv(key=self.key, value=self.text(),
                                encoding='utf-8')
                gui.status(f'保存成功. key = {self.key}, value = {self.text()}')

    class EnvComboBox(QtWidgets.QComboBox):
        def __init__(self, parent=None, key=None):
            super().__init__(parent)
            self.key = key
            self.currentTextChanged.connect(self.save)

        def set_key(self, key):
            self.key = key
            self.load()

        def load(self):
            if self.key is not None:
                self.setCurrentText(
                    app_data.getenv(self.key, encoding='utf-8', default=''))

        def save(self):
            if self.key is not None:
                app_data.setenv(key=self.key, value=self.currentText(),
                                encoding='utf-8')
                gui.status(
                    f'保存成功. key = {self.key}, value = {self.currentText()}')

    sigRefresh = QtCore.pyqtSignal()

    def __init__(self, parent=None, items=None):
        super().__init__(parent)
        self.env_items = items
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sigRefresh.connect(self.refresh)
        self.sigRefresh.emit()

    def refresh(self):
        data = self.env_items
        if data is None:
            return
        self.setRowCount(len(data))
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['项目', '值', '备注'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for i in range(len(data)):
            label = data[i].get('label')
            key = data[i].get('key')
            items = data[i].get('items')
            note = data[i].get('note')
            if label is not None:
                self.setItem(i, 0, QtWidgets.QTableWidgetItem(label))
            assert isinstance(key, str)
            if items is None:
                item = EnvEdit.EnvLineEdit()
                item.set_key(key)
            else:
                item = EnvEdit.EnvComboBox()
                item.addItems(items)
                item.set_key(key)
            self.setCellWidget(i, 1, item)
            if isinstance(note, str):
                self.setItem(i, 2, QtWidgets.QTableWidgetItem(note))
            self.resizeRowToContents(i)

    def resizeEvent(self, event):
        for row in range(self.rowCount()):
            self.resizeRowToContents(row)
        super().resizeEvent(event)
