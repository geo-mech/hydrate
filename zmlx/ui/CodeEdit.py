import hashlib
import os
from datetime import datetime

from zml import read_text, write_text, app_data
from zmlx.filesys.tag import time_string
from zmlx.ui.Config import code_in_editor
from zmlx.ui.Qt import QtWidgets, QtName, is_PyQt6
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
        menu.addAction(
            create_action(self, "运行", 'begin', self.console_exec))
        if not use_QSci and is_PyQt6:  # 尝试添加安装Qsci的动作

            def install_qsci():
                from zmlx.alg.pip_install import pip_install
                from zmlx.ui.window.start_func import start_func
                start_func(lambda:
                           pip_install(
                               package_name='pyqt6-qscintilla',
                               name='PyQt6.Qsci'))

            menu.addAction(
                create_action(
                    self,
                    "安装PyQt6.Qsci以获得更好的代码编辑功能",
                    'set', install_qsci))

        folder = self._history_folder()
        if os.path.isdir(folder):
            def show_history():
                from zmlx.ui.MainWindow import get_window
                get_window().show_code_history(folder=folder)

            menu.addAction(
                create_action(
                    self,
                    "编辑历史",
                    slot=show_history))

        return menu

    def export_data(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, '导出代码',
            '',
            f'Python File(*.py)')
        if len(fpath) > 0:
            write_text(path=fpath,
                       text=self.toPlainText() if use_text_edit else self.text(),
                       encoding='utf-8')

    def save(self):
        """
        尝试保存文件
        """
        if self.__fname is not None:
            names = [self.__fname]
            try:  # 尝试生成临时保存的路径
                ts = time_string()[:-1] + '0'
                names.append(os.path.join(self._history_folder(), f'{ts}.py'))
            except:
                pass
            try:
                for name in names:
                    write_text(path=name,
                               text=self.toPlainText() if use_text_edit else self.text(),
                               encoding='utf-8')
            except Exception as err:
                print(err)

    def _history_folder(self):
        try:  # 尝试生成临时保存的路径
            hash_obj = hashlib.sha256(
                self.__fname.encode('utf-8')).hexdigest()
            return app_data.root('editing_history', hash_obj[: 20])
        except:
            return ''

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
                self.setText(
                    read_text(fname, encoding='utf-8', default=code_in_editor))
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
            return datetime.fromtimestamp(
                os.path.getmtime(self.__fname)).strftime('%Y-%m-%d %H:%M:%S')
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
