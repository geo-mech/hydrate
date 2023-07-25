import sys

from zml import app_data
from zmlx.alg.search_paths import choose_path
from zmlx.ui.Qt import QtWidgets


class FileFind(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel(self)
        label.setText('请在此输入文件名: ')
        layout.addWidget(label)

        self.fname_edit = QtWidgets.QLineEdit(self)
        self.fname_edit.textChanged.connect(self.updateFiles)
        layout.addWidget(self.fname_edit)

        label = QtWidgets.QLabel(self)
        label.setText('完整路径如下: ')
        layout.addWidget(label)

        self.output = QtWidgets.QTextBrowser(self)
        layout.addWidget(self.output)

        button = QtWidgets.QPushButton(self)
        button.setText('添加搜索路径')
        button.clicked.connect(self.addPath)
        layout.addWidget(button)

        self.updateFiles()

    def updateFiles(self):
        filename = self.fname_edit.text()
        if len(filename) == 0:
            text = ''
            for path in app_data.get_paths():
                text = text + path + '\n'
            self.output.setPlainText(text)
            return
        results = app_data.find_all(filename)
        if len(results) == 0:
            self.output.setPlainText('未找到')
            return
        else:
            self.output.setPlainText('\n'.join(results))

    def addPath(self):
        choose_path()


def test1():
    app = QtWidgets.QApplication(sys.argv)
    w = FileFind()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    test1()
