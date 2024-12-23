import os

from zmlx.ui.Qt import QtCore, QtGui
from zmlx.ui.TextBrowser import TextBrowser


class ConsoleOutput(TextBrowser):
    sig_add_text = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(ConsoleOutput, self).__init__(parent)
        self.__length = 0
        self.__length_max = 1000000
        self.sig_add_text.connect(self.__add_text)

    def write(self, text):
        self.sig_add_text.emit(text)

    def flush(self):
        pass

    def __add_text(self, text):
        while self.__length > self.__length_max:
            fulltext = self.toPlainText()
            fulltext = fulltext[-int(len(fulltext) / 2): -1]
            self.clear()
            self.setPlainText(fulltext)
            self.__length = len(fulltext)
        self.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.insertPlainText(text)
        self.__length += len(text)

    def load_text(self, filename):
        try:
            if os.path.isfile(filename):
                with open(filename, 'r') as file:
                    text = file.read()
                    self.setPlainText(text)
                    self.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        except Exception as err2:
            print(err2)

    def save_text(self, filename):
        try:
            with open(filename, 'w') as file:
                file.write(self.toPlainText())
        except Exception as err2:
            print(err2)
