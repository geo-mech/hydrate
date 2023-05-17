# -*- coding: utf-8 -*-


from PyQt5 import QtCore, QtWidgets

from zml import read_text, write_text, gui
from zmlx.ui.Config import code_in_editor
from zmlx.ui.PythonHighlighter import PythonHighlighter


class CodeEdit(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super(CodeEdit, self).__init__(parent)
        self.__highlighter = PythonHighlighter(self.document())
        self.__fname = None
        self.setText(code_in_editor)
        self.textChanged.connect(self.save)

    def event(self, event):
        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Tab:
            cursor = self.textCursor()
            cursor.insertText("    ")
            return True
        return QtWidgets.QTextEdit.event(self, event)

    def enterEvent(self, event):
        gui.status(f"Editor: {self.__fname}", 3000)

    def save(self):
        """
        尝试保存文件
        """
        if self.__fname is not None:
            try:
                write_text(path=self.__fname, text=self.toPlainText(), encoding='utf-8')
            except:
                pass

    def open(self, fname=None):
        """
        尝试载入文件
        """
        if fname is None and self.__fname is not None:
            self.open(self.__fname)
            return
        if fname is not None:
            try:
                self.__fname = None
                self.setText(read_text(fname, encoding='utf-8', default=code_in_editor))
                self.__fname = fname
            except:
                pass

    def get_fname(self):
        """
        返回当前的存储路径
        """
        return self.__fname
