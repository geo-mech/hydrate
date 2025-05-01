from zml import read_text, write_text, app_data
from zmlx.ui.pyqt import QtWidgets


class TextEdit(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super(TextEdit, self).__init__(parent)
        self.__fname = None
        self.textChanged.connect(self.save)

    def save(self):
        if self.__fname is not None:
            try:
                write_text(path=self.__fname, text=self.toPlainText(),
                           encoding='utf-8')
            except:
                pass

    def load(self):
        if self.__fname is not None:
            try:
                self.setText(
                    read_text(self.__fname, encoding='utf-8', default=''))
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
        window = app_data.get('main_window')
        if window is not None:
            window.cmd_status(f"{self.__fname}", 3000)

    def get_start_code(self):
        return f"""gui.open_text(r'{self.__fname}')"""
