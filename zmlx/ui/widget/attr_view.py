import sys

from zmlx.ui.pyqt import QtWidgets, QtCore


class AttrView(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        header = self.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

    def get_count(self):
        return len(self._data)

    def get_data(self):
        return self._data

    def show_attrs(self, clear: bool = False, **opts):
        if clear:
            self._data.clear()
        self._data.update(opts)
        data = []
        for key, value in self._data.items():
            if isinstance(value, dict):
                n = value.get('name')
                v = value.get('value')
                if isinstance(n, str) and v is not None:
                    data.append([n, f'{v}'])
                    continue
            data.append([key, f'{value}'])

        self.setRowCount(len(data))
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['名称', '值'])

        for i in range(len(data)):
            for j in range(2):
                item = QtWidgets.QTableWidgetItem(data[i][j])
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.setItem(i, j, item)


def test():
    app = QtWidgets.QApplication(sys.argv)
    w = AttrView()
    w.show_attrs(a=1, b=2, c=3)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test()
