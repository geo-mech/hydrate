import os
import sys

from PyQt5 import QtWidgets, QtCore


class FileWidget(QtWidgets.QListWidget):
    sig_file_clicked = QtCore.pyqtSignal(str)
    sig_file_double_clicked = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(FileWidget, self).__init__(parent)

        def click(item, sig):
            text = item.text()
            if text == '..':
                fpath = os.path.dirname(self.folder)
            else:
                fpath = os.path.join(self.folder, text)
            if os.path.exists(fpath):
                sig.emit(fpath)

        self.itemClicked.connect(
            lambda item: click(item, self.sig_file_clicked))
        self.itemDoubleClicked.connect(
            lambda item: click(item, self.sig_file_double_clicked))
        self.folder = None
        self.set_dir()

    def set_dir(self, folder=None):
        if folder is None:
            folder = os.getcwd()
        self.clear()
        self.folder = folder
        if os.path.isdir(self.folder):
            self.addItem('..')
            for name in os.listdir(self.folder):
                self.addItem(name)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = FileWidget()
    w.sig_file_clicked.connect(lambda path: print(f'clicked: {path}'))
    w.sig_file_double_clicked.connect(lambda path: print(f'double_clicked: {path}'))
    w.show()
    sys.exit(app.exec_())
