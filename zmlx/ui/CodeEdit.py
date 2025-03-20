import os
from datetime import datetime

from zml import read_text, write_text, app_data
from zmlx.ui.Config import code_in_editor
from zmlx.ui.Qt import QtWidgets, QtName
from zmlx.ui.alg.create_action import create_action

PythonEditor = None
use_QSci = False

if PythonEditor is None:
    try:
        from zmlx.ui.Widgets.PythonEditor import PythonEditor

        use_QSci = True
    except Exception as e:
        print(f'Error: {e}. Please install QScintilla for {QtName}')

if PythonEditor is None:
    try:
        from zmlx.ui.Widgets.PythonEditOld import PythonEditOld as PythonEditor
    except Exception as e:
        print(f'Error: {e}')

if PythonEditor is None:
    PythonEditor = QtWidgets.QTextEdit

use_text_edit = not use_QSci


class CodeEdit(PythonEditor):
    def __init__(self, parent=None):
        super(CodeEdit, self).__init__(parent)
        self.__fname = None
        self.setText(code_in_editor)
        self.textChanged.connect(self.save)
        self.textChanged.connect(self.show_status)

    def contextMenuEvent(self, event):
        # 创建菜单并添加清除动作
        self.get_context_menu().exec(event.globalPos())

    def get_context_menu(self):
        menu = super().createStandardContextMenu()
        menu.addSeparator()
        menu.addAction(create_action(self, "运行", 'begin', self.console_exec))
        return menu

    def export_data(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(self, '导出代码',
                                                         '', f'Python File(*.py)')
        if len(fpath) > 0:
            write_text(path=fpath,
                       text=self.toPlainText() if use_text_edit else self.text(),
                       encoding='utf-8')

    def save(self):
        """
        尝试保存文件
        """
        if self.__fname is not None:
            try:
                write_text(path=self.__fname,
                           text=self.toPlainText() if use_text_edit else self.text(),
                           encoding='utf-8')
            except Exception as err:
                print(err)

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
            except Exception as err:
                print(err)

    def enterEvent(self, event):
        self.show_status()
        super().enterEvent(event)

    def show_status(self):
        if isinstance(self.__fname, str):
            window = app_data.get('main_window')
            if window is not None:
                window.cmd_status(self.__fname + f' ({self.get_mtime()})', 3000)

    def get_fname(self):
        """
        返回当前的存储路径
        """
        return self.__fname

    def get_mtime(self):
        if not isinstance(self.__fname, str):
            return ''
        if os.path.isfile(self.__fname):
            return datetime.fromtimestamp(os.path.getmtime(self.__fname)).strftime('%Y-%m-%d %H:%M:%S')
        else:
            return ''

    def console_exec(self):
        main_window = app_data.get('main_window')
        if main_window is not None:
            try:
                self.save()
                main_window.exec_file(self.get_fname())
            except Exception as err:
                print(err)

    def get_start_code(self):
        return f"""gui.open_code(r'{self.__fname}')"""


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = CodeEdit()
    window.show()
    sys.exit(app.exec())
