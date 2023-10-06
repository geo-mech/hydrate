from zmlx.ui.Qt import QtCore, QtWidgets, QtGui
from zml import gui, get_dir, version
import sys


class ConsoleOutput(QtWidgets.QTextBrowser):
    __sig_add_text = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(ConsoleOutput, self).__init__(parent)
        self.__length = 0
        self.__length_max = 1000000
        self.__sig_add_text.connect(self.__add_text)

    def write(self, text):
        self.__sig_add_text.emit(text)

    def flush(self):
        pass

    def __add_text(self, text):
        while self.__length > self.__length_max:
            fulltext = self.toPlainText()
            fulltext = fulltext[-int(len(fulltext) / 2): -1]
            self.clear()
            self.setPlainText(fulltext)
            self.__length = len(fulltext)
        self.moveCursor(QtGui.QTextCursor.End)
        self.insertPlainText(text)
        self.__length += len(text)

    def enterEvent(self, event):
        gui.status(f'System: zml ({version}) at <{get_dir()}> with Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')
