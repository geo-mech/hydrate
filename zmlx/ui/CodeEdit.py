from zml import read_text, write_text, app_data
from zmlx.ui.Config import code_in_editor
from zmlx.ui.PythonHighlighter import PythonHighlighter
from zmlx.ui.Qt import QtCore, QtWidgets


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

    def export_data(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(self, '导出代码',
                                                         '', f'Python File(*.py)')
        if len(fpath) > 0:
            write_text(path=fpath, text=self.toPlainText(), encoding='utf-8')

    def save(self):
        """
        尝试保存文件
        """
        if self.__fname is not None:
            try:
                write_text(path=self.__fname, text=self.toPlainText(), encoding='utf-8')
            except Exception as e:
                print(e)

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
            except Exception as e:
                print(e)

    def enterEvent(self, event):
        window = app_data.get('main_window')
        if window is not None:
            window.cmd_status(self.__fname, 3000)
        super().enterEvent(event)

    def get_fname(self):
        """
        返回当前的存储路径
        """
        return self.__fname

    def console_exec(self):
        main_window = app_data.get('main_window')
        if main_window is not None:
            try:
                self.save()
                main_window.exec_file(self.get_fname())
            except Exception as e:
                print(e)

    def get_start_code(self):
        return f"""gui.open_code(r'{self.__fname}')"""
