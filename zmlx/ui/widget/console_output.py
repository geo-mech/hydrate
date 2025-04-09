import os

from zmlx.ui.pyqt import QtCore, QtGui
from zmlx.ui.widget.text_browser import TextBrowser


class ConsoleOutput(TextBrowser):
    sig_add_text = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, console=None):
        super(ConsoleOutput, self).__init__(parent)
        self.__length = 0
        self.__length_max = 100000
        self.sig_add_text.connect(self.__add_text)
        self.console = console

    def get_context_menu(self):
        menu = super().get_context_menu()
        if self.console is not None:
            from zmlx.ui.main_window import get_window
            window = get_window()
            menu.addSeparator()
            menu.addAction(window.get_action('console_hide'))
            if self.console.is_running():
                menu.addAction(window.get_action('console_pause'))
                menu.addAction(window.get_action('console_resume'))
                menu.addAction(window.get_action('console_stop'))
            else:
                menu.addAction(window.get_action('show_code_history'))
        return menu

    def write(self, text):
        self.sig_add_text.emit(text)

    def flush(self):
        pass

    def __check_length(self):
        while self.__length > self.__length_max:
            fulltext = self.toPlainText()
            fulltext = fulltext[-int(len(fulltext) / 2): -1]
            self.clear()
            self.setPlainText(fulltext)
            self.__length = len(fulltext)

    def __add_text(self, text):
        self.__check_length()
        self.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.insertPlainText(text)
        self.__length += len(text)

    def load_text(self, filename):
        try:
            if os.path.isfile(filename):
                with open(filename, 'r') as file:
                    text = file.read()
                    self.setPlainText(text)
                    self.__length = len(text)
                    self.__check_length()
                    self.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        except Exception as err2:
            print(err2)
            self.setPlainText('')

    def save_text(self, filename):
        try:
            with open(filename, 'w') as file:
                file.write(self.toPlainText())
        except Exception as err2:
            print(err2)
