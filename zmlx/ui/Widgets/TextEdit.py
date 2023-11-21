from zml import read_text, write_text
from zmlx.ui.GuiBuffer import gui
from zmlx.ui.Qt import QtWidgets


class TextEdit(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super(TextEdit, self).__init__(parent)
        self.__fname = None
        self.textChanged.connect(self.save)

    def save(self):
        if self.__fname is not None:
            try:
                write_text(path=self.__fname, text=self.toPlainText(), encoding='utf-8')
            except:
                pass

    def load(self):
        if self.__fname is not None:
            try:
                self.setText(read_text(self.__fname, encoding='utf-8', default=''))
            except:
                pass
        else:
            self.setText('')

    def set_fname(self, fname=None):
        self.__fname = fname
        self.load()

    def get_fname(self):
        return self.__fname

    def enterEvent(self, event):
        gui.status(f"Text Editor: {self.__fname}", 3000)
