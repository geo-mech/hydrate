from zmlx.ui.pyqt import is_pyqt6, QtCore, QtWidgets

if is_pyqt6:
    from PyQt6.QtWidgets import (QApplication, QTableWidget, QTableWidgetItem,
                                 QHeaderView, QPushButton)
else:
    from PyQt5.QtWidgets import (QApplication, QTableWidget, QTableWidgetItem,
                                 QHeaderView, QPushButton)


class TabDetails(QTableWidget):

    def __init__(self, parent=None, obj=None, header_labels=None):
        super().__init__(parent)
        self.header_labels = header_labels
        self.obj = obj
        self._init_ui()
        self._connect_signals()
        self.refresh()

    def _init_ui(self):
        self.setColumnCount(3)
        if self.header_labels is not None:
            assert len(self.header_labels) == 3
            self.setHorizontalHeaderLabels(
                self.header_labels)
        else:
            self.setHorizontalHeaderLabels(['标题', '类型', '操作'])
        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(True)
        self.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu)  # 启用右键菜单

    def _connect_signals(self):
        self.cellClicked.connect(self._on_cell_clicked)
        self.customContextMenuRequested.connect(
            self._show_context_menu)  # 右键菜单信号

    def refresh(self):
        if (not hasattr(self.obj, 'count')
                or not hasattr(self.obj, 'get')
                or not hasattr(self.obj, 'remove')
                or not hasattr(self.obj, 'show')):
            return
        row_count = self.obj.count()
        self.setRowCount(row_count)

        for row in range(row_count):
            value, name = self.obj.get(row)
            # 数值列（直接显示值）
            self.setItem(row, 0, QTableWidgetItem(str(value)))
            # 类型列（使用type获取类型）
            self.setItem(row, 1, QTableWidgetItem(name))
            # 删除按钮
            btn = QPushButton('移除', self)
            btn.clicked.connect(lambda _, r=row: self._handle_delete(r))
            self.setCellWidget(row, 2, btn)

    def _handle_delete(self, row):
        self.obj.remove(row)
        self.refresh()

    def _on_cell_clicked(self, row, column):
        if column in (0, 1):
            self.obj.show(row)

    def _show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        refresh_action = menu.addAction("刷新表格")
        refresh_action.triggered.connect(self.refresh)
        menu.exec(self.viewport().mapToGlobal(pos))


class ListWp:
    def __init__(self, data):
        self.data = data.copy()  # 防止原始数据被修改

    def count(self):
        return len(self.data)

    def get(self, index):
        return self.data[index], type(self.data[index]).__name__

    def remove(self, index):
        del self.data[index]

    def show(self, index):
        print(self.data[index])


class TabWp:
    def __init__(self, data):
        self.data = data

    def count(self):
        return self.data.count()

    def get(self, index):
        return self.data.tabText(index), type(self.data.widget(index)).__name__

    def remove(self, index):
        self.data.close_tab(index)

    def show(self, index):
        self.data.setCurrentIndex(index)


def test():
    # 测试数据（包含不同类型）
    test_data = [
        42,
        "Hello",
        3.14,
        True,
        [1, 2, 3],
        {"key": "value"},
        None,
        (4, 5, 6)
    ]
    obj = ListWp(test_data)

    app = QApplication([])
    table = TabDetails(obj=obj)
    table.setGeometry(0, 0, 800, 500)
    table.show()
    app.exec()


if __name__ == '__main__':
    test()
