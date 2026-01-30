"""
提供界面系统最核心的控件系统。
"""
import glob
import hashlib
import os
import sys
import time
import timeit
from datetime import datetime

from zml import (
    core, lic, get_dir, make_parent, reg, timer, app_data,
    write_text, read_text)
from zmlx.alg.base import fsize2str, time2str, clamp
from zmlx.alg.fsys import time_string
from zmlx.alg.search_paths import choose_path
from zmlx.ui import settings
from zmlx.ui import setup_files
from zmlx.ui.alg import (
    create_action)
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import (
    QWebEngineView, is_pyqt6, QtCore, QtGui, QtWidgets, qt_name, QAction)
from zmlx.ui.settings import (
    get_default_code)
from zmlx.ui.utils import TaskProc

try:  # 尝试基于QsciScintilla实现Python编辑器
    if is_pyqt6:
        from PyQt6.Qsci import QsciScintilla, QsciLexerPython
    else:
        from PyQt5.Qsci import QsciScintilla, QsciLexerPython


    class _PythonEdit(QsciScintilla):
        def __init__(self, parent=None):
            super().__init__(parent)

            # 基础编辑器设置
            self.setUtf8(True)
            self.setAutoIndent(True)
            self.setIndentationWidth(4)
            self.setTabWidth(4)
            self.setIndentationsUseTabs(False)
            self.setEdgeColumn(80)
            self.setEdgeMode(QsciScintilla.EdgeMode.EdgeLine)
            self.setWrapMode(QsciScintilla.WrapMode.WrapNone)
            self.setCaretLineVisible(True)

            # 设置语法高亮
            self.lexer = QsciLexerPython()
            self.setLexer(self.lexer)

            # 自动补全设置
            self.setAutoCompletionSource(
                QsciScintilla.AutoCompletionSource.AcsAll)
            self.setAutoCompletionThreshold(2)
            self.setAutoCompletionCaseSensitivity(False)
            self.setAutoCompletionReplaceWord(True)

            # 行号设置
            self.setMarginType(
                0, QsciScintilla.MarginType.NumberMargin)
            self.setMarginWidth(0, "0000")
            # self.setMarginsForegroundColor(QColor("#888888"))

            # 括号匹配
            self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)

            # 初始化颜色主题
            self._update_theme()

            # 自动检测主题变化
            self.app_palette = QtWidgets.QApplication.palette()
            QtWidgets.QApplication.instance().paletteChanged.connect(
                self._on_palette_changed)

        def _is_dark_theme(self):
            # 通过背景色亮度判断是否为暗色主题
            bg_color = self.palette().color(QtGui.QPalette.ColorRole.Window)
            return bg_color.lightness() < 128

        def _update_theme(self):
            if self._is_dark_theme():
                self._setup_dark_theme()
            else:
                self._setup_light_theme()

        def _on_palette_changed(self):
            self._update_theme()

        def _setup_light_theme(self):
            # 亮色主题行号设置
            margin_bg = QtGui.QColor("#F0F0F0")  # 稍亮的背景
            margin_fg = QtGui.QColor("#606060")  # 深灰色文字

            self.setMarginsBackgroundColor(margin_bg)
            self.setMarginsForegroundColor(margin_fg)

            # 亮色主题颜色配置
            paper = QtGui.QColor("#FFFFFF")
            text = QtGui.QColor("#000000")
            caret = QtGui.QColor("#000000")
            selection = QtGui.QColor("#C0C0C0")

            # 设置基础颜色
            self.setCaretForegroundColor(caret)
            self.setSelectionBackgroundColor(selection)
            self.setPaper(paper)
            self.setColor(text)

            # 设置语法高亮颜色
            self.lexer.setDefaultPaper(paper)
            self.lexer.setDefaultColor(text)
            self.lexer.setColor(QtGui.QColor("#008000"),
                                QsciLexerPython.Comment)
            self.lexer.setColor(QtGui.QColor("#FF0000"),
                                QsciLexerPython.SingleQuotedString)
            self.lexer.setColor(QtGui.QColor("#FF0000"),
                                QsciLexerPython.DoubleQuotedString)
            self.lexer.setColor(QtGui.QColor("#0000FF"),
                                QsciLexerPython.Keyword)
            self.lexer.setColor(QtGui.QColor("#FF00FF"),
                                QsciLexerPython.ClassName)
            self.lexer.setColor(QtGui.QColor("#FF8000"),
                                QsciLexerPython.FunctionMethodName)

            # 设置边线颜色
            self.setEdgeColor(QtGui.QColor("#E0E0E0"))

            # 当前行高亮
            self.setCaretLineBackgroundColor(QtGui.QColor("#F0F0F0"))

        def _setup_dark_theme(self):
            # 暗色主题行号设置
            margin_bg = QtGui.QColor("#202020")  # 比编辑器背景更深的颜色
            margin_fg = QtGui.QColor("#A0A0A0")  # 浅灰色文字

            self.setMarginsBackgroundColor(margin_bg)
            self.setMarginsForegroundColor(margin_fg)

            # 暗色主题颜色配置
            paper = QtGui.QColor("#2D2D2D")
            text = QtGui.QColor("#E0E0E0")
            caret = QtGui.QColor("#E0E0E0")
            selection = QtGui.QColor("#404040")

            # 设置基础颜色
            self.setCaretForegroundColor(caret)
            self.setSelectionBackgroundColor(selection)
            self.setPaper(paper)
            self.setColor(text)

            # 设置语法高亮颜色
            self.lexer.setDefaultPaper(paper)
            self.lexer.setDefaultColor(text)
            self.lexer.setColor(QtGui.QColor("#608060"),
                                QsciLexerPython.Comment)
            self.lexer.setColor(QtGui.QColor("#FF8080"),
                                QsciLexerPython.SingleQuotedString)
            self.lexer.setColor(QtGui.QColor("#FF8080"),
                                QsciLexerPython.DoubleQuotedString)
            self.lexer.setColor(QtGui.QColor("#CC99FF"),
                                QsciLexerPython.Keyword)
            self.lexer.setColor(QtGui.QColor("#99CCFF"),
                                QsciLexerPython.ClassName)
            self.lexer.setColor(QtGui.QColor("#FFCC66"),
                                QsciLexerPython.FunctionMethodName)

            # 设置边线颜色
            self.setEdgeColor(QtGui.QColor("#505050"))

            # 当前行高亮
            self.setCaretLineBackgroundColor(QtGui.QColor("#3D3D3D"))

except ImportError as import_error:
    print(f'Error: {import_error}')
    QsciScintilla = None
    QsciLexerPython = None


    class _PythonHighlighter(QtGui.QSyntaxHighlighter):
        """
        原文链接：
        https://blog.csdn.net/xiaoyangyang20/article/details/68923133
        """
        Rules = []
        Formats = {}

        def __init__(self, parent=None):
            super(_PythonHighlighter, self).__init__(parent)

            self.initialize_formats()

            def zml_names():
                try:
                    space = {}
                    exec('from zmlx import *', space)
                    return list(set(space.keys()))
                except Exception as err:
                    print(err)
                    return []

            keywords = [
                "and", "as", "assert", "break", "class",
                "continue", "def", "del", "elif", "else", "except",
                "exec", "finally", "for", "from", "global", "if",
                "import", "in", "is", "lambda", "not", "or", "pass",
                "print", "raise", "return", "try", "while", "with",
                "yield"]
            builtins = [
                "abs", "all", "any", "basestring", "bool",
                "callable", "chr", "classmethod", "cmp", "compile",
                "complex", "delattr", "dict", "dir", "divmod",
                "enumerate", "eval", "execfile", "exit", "file",
                "filter", "float", "frozenset", "getattr",
                "globals",
                "hasattr", "hex", "id", "int", "isinstance",
                "issubclass", "iter", "len", "list", "locals",
                "map",
                "max", "min", "object", "oct", "open", "ord", "pow",
                "property", "range", "reduce", "repr", "reversed",
                "round", "set", "setattr", "slice", "sorted",
                "staticmethod", "str", "sum", "super", "tuple",
                "type",
                "vars", "zip", "zml", "zmlx"
            ]
            builtins += zml_names()
            constants = [
                "False", "True", "None", "NotImplemented",
                "Ellipsis"]

            _PythonHighlighter.Rules.append((QtCore.QRegularExpression(
                "|".join([r"\b%s\b" % keyword for keyword in keywords])),
                                             "keyword"))
            _PythonHighlighter.Rules.append((QtCore.QRegularExpression(
                "|".join([r"\b%s\b" % builtin for builtin in builtins])),
                                             "builtin"))
            _PythonHighlighter.Rules.append((QtCore.QRegularExpression(
                "|".join([r"\b%s\b" % constant
                          for constant in constants])), "constant"))
            _PythonHighlighter.Rules.append((QtCore.QRegularExpression(
                r"\b[+-]?[0-9]+[lL]?\b"
                r"|\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b"
                r"|\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b"),
                                             "number"))
            _PythonHighlighter.Rules.append((QtCore.QRegularExpression(
                r"\bPyQt4\b|\bQt?[A-Z][a-z]\w+\b"), "pyqt"))
            _PythonHighlighter.Rules.append(
                (QtCore.QRegularExpression(r"\b@\w+\b"),
                 "decorator"))
            string_re = QtCore.QRegularExpression(
                r"""(?:'[^']*?'|"[^"]*?")""")
            _PythonHighlighter.Rules.append((string_re, "string"))
            self.stringRe = QtCore.QRegularExpression(
                r"""(:?"["].*?"|'''.*?'')""")
            _PythonHighlighter.Rules.append((self.stringRe, "string"))
            self.tripleSingleRe = QtCore.QRegularExpression(r"""'''(?!")""")
            self.tripleDoubleRe = QtCore.QRegularExpression(r'''"""(?!')''')

        @staticmethod
        def initialize_formats():
            base_format = QtGui.QTextCharFormat()
            # base_format.setFontFamily("courier")
            # base_format.setFontPointSize(10)
            for name, color in (
                    ("normal", QtCore.Qt.GlobalColor.black),
                    ("keyword", QtCore.Qt.GlobalColor.darkBlue),
                    ("builtin", QtCore.Qt.GlobalColor.darkRed),
                    ("constant",
                     QtCore.Qt.GlobalColor.darkGreen),
                    ("decorator",
                     QtCore.Qt.GlobalColor.darkBlue),
                    ("comment",
                     QtCore.Qt.GlobalColor.darkGreen),
                    ("string",
                     QtCore.Qt.GlobalColor.darkYellow),
                    ("number",
                     QtCore.Qt.GlobalColor.darkMagenta),
                    ("error", QtCore.Qt.GlobalColor.darkRed),
                    ("pyqt", QtCore.Qt.GlobalColor.darkCyan)
            ):
                fmt = QtGui.QTextCharFormat(base_format)
                fmt.setForeground(QtGui.QColor(color))
                if name in ("keyword", "decorator"):
                    fmt.setFontWeight(QtGui.QFont.Weight.Bold)
                if name == "comment":
                    fmt.setFontItalic(True)
                _PythonHighlighter.Formats[name] = fmt

        def highlightBlock(self, text):
            try:
                self.__highlight_block(text)
            except Exception as err:
                print(err)

        def __highlight_block(self, text):
            normal, triple_single, triple_double, error = range(4)

            text_length = len(text)
            prev_state = self.previousBlockState()

            self.setFormat(
                0, text_length,
                _PythonHighlighter.Formats["normal"])

            if text.startswith("Traceback") or text.startswith("Error: "):
                self.setCurrentBlockState(error)
                self.setFormat(
                    0, text_length,
                    _PythonHighlighter.Formats["error"])
                return
            if (prev_state == error and
                    not (text.startswith(sys.ps1) or text.startswith("#"))):
                self.setCurrentBlockState(error)
                self.setFormat(
                    0, text_length,
                    _PythonHighlighter.Formats["error"])
                return

            for regex, fmt in _PythonHighlighter.Rules:
                matches = regex.globalMatch(text)
                # 处理匹配项并设置格式
                while matches.hasNext():
                    match = matches.next()  # 获取下一个匹配
                    start = match.capturedStart(0)  # 获取匹配的起始索引
                    length = match.capturedLength(0)  # 获取匹配的长度
                    self.setFormat(
                        start, length,
                        _PythonHighlighter.Formats[fmt])

            # Slow but good quality highlighting for comments. For more
            # speed, comment this out and add the following to __init__:
            # PythonHighlighter.Rules.append((QtCore.QRegExp(r"#.*"), "comment"))
            if not text:
                pass
            elif text[0] == "#":
                self.setFormat(
                    0, len(text),
                    _PythonHighlighter.Formats["comment"])
            else:
                stack = []
                for i, c in enumerate(text):
                    if c in ('"', "'"):
                        if stack and stack[-1] == c:
                            stack.pop()
                        else:
                            stack.append(c)
                    elif c == "#" and len(stack) == 0:
                        self.setFormat(
                            i, len(text),
                            _PythonHighlighter.Formats["comment"])
                        break

            self.setCurrentBlockState(normal)

            match = self.stringRe.match(text)
            if match.hasMatch():  # 检查是否有匹配
                return

            # This is fooled by triple quotes inside single quoted strings
            for regex, state in (
                    (self.tripleSingleRe, triple_single),
                    (self.tripleDoubleRe, triple_double)
            ):
                match = regex.match(text)  # 使用 match() 方法获取匹配结果
                i = match.capturedStart(
                    0) if match.hasMatch() else -1  # 获取匹配的起始位置

                if self.previousBlockState() == state:
                    if i == -1:  # 如果没有匹配，设置 i 为文本长度
                        i = len(text)
                        self.setCurrentBlockState(state)
                    self.setFormat(
                        0, i + 3,
                        _PythonHighlighter.Formats["string"])  # 设置格式
                elif i > -1:  # 如果找到匹配
                    self.setCurrentBlockState(state)
                    self.setFormat(
                        i, len(text),
                        _PythonHighlighter.Formats["string"])  # 设置格式


    class _PythonEdit(QtWidgets.QTextEdit):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.__highlighter = _PythonHighlighter(self.document())

        def event(self, event):
            if (event.type() == QtCore.QEvent.Type.KeyPress
                    and event.key() == QtCore.Qt.Key.Key_Tab):
                cursor = self.textCursor()
                cursor.insertText("    ")
                return True
            return QtWidgets.QTextEdit.event(self, event)


class CodeEdit(_PythonEdit):
    def __init__(self, parent=None):
        super(CodeEdit, self).__init__(parent)
        self.__fname = None
        self.setText(get_default_code())
        self.textChanged.connect(self.save)
        self.textChanged.connect(self.show_status)

    def contextMenuEvent(self, event):
        # 创建菜单并添加清除动作
        self.get_context_menu().exec(event.globalPos())

    def get_context_menu(self):
        menu = super().createStandardContextMenu()
        menu.addSeparator()
        menu.addAction(
            create_action(
                self, "运行", icon='begin', slot=self.console_exec))
        if QsciScintilla is None and is_pyqt6:  # 尝试添加安装Qsci的动作

            def install_qsci():
                if not gui.is_running():
                    from zmlx.alg.sys import pip_install
                    gui.start_func(
                        lambda: pip_install(
                            package_name='pyqt6-qscintilla',
                            name='PyQt6.Qsci'))

            menu.addAction(
                create_action(
                    self,
                    "安装PyQt6.Qsci以获得更好的代码编辑功能",
                    icon='set', slot=install_qsci))

        folder = self._history_folder()
        if os.path.isdir(folder):
            def show_history():
                gui.show_code_history(folder=folder)

            menu.addAction(
                create_action(
                    self, "编辑历史", slot=show_history))

        menu.addSeparator()
        menu.addAction(
            create_action(
                self, "在主线程执行", slot=self.direct_exec))

        return menu

    def get_text(self):
        if isinstance(self, QtWidgets.QTextEdit):
            return self.toPlainText()
        else:
            return self.text()

    def export_data(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, '导出代码',
            '',
            f'Python File(*.py)')
        if len(fpath) > 0:
            write_text(path=fpath, text=self.get_text(), encoding='utf-8')

    def save(self):
        """
        尝试保存文件
        """
        if self.__fname is not None:
            names = [self.__fname]
            try:  # 尝试生成临时保存的路径
                ts = time_string()[:-1] + '0'
                names.append(os.path.join(self._history_folder(), f'{ts}.py'))
            except Exception as err:
                print(err)
            try:
                text = self.get_text()
                for name in names:
                    write_text(path=name, text=text, encoding='utf-8')
            except Exception as err:
                print(err)

    def _history_folder(self):
        try:  # 尝试生成临时保存的路径
            hash_obj = hashlib.sha256(
                self.__fname.encode('utf-8')).hexdigest()
            return app_data.root('editing_history', hash_obj[: 20])
        except Exception as err:
            print(err)
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
                    read_text(fname, encoding='utf-8',
                              default=get_default_code()))
                self.__fname = fname
            except Exception as err:
                print(err)

    def enterEvent(self, event):
        self.show_status()
        super().enterEvent(event)

    def show_status(self):
        if isinstance(self.__fname, str):
            gui.status(
                self.__fname + f' ({self.get_mtime()})', 3000)

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
        try:
            self.save()
            gui.exec_file(self.get_fname())
        except Exception as err:
            print(err)

    def direct_exec(self):
        if not app_data.has_tag_today('code_direct_exec_warning_show'):
            if gui.question('在当前线程内直接运行脚本，可能会阻塞界面，导致界面卡顿。\n'
                            '是否继续？'):
                app_data.add_tag_today('code_direct_exec_warning_show')
            else:
                return
        try:
            text = self.get_text()
            space = {'__name__': '__main__', '__file__': self.__fname,
                     'gui': gui}
            exec(text, space)
        except Exception as err:
            print(err)


class TextFileEdit(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super(TextFileEdit, self).__init__(parent)
        self.__fname = None
        self.textChanged.connect(self.save)

    def save(self):
        if self.__fname is not None:
            try:
                write_text(
                    path=self.__fname, text=self.toPlainText(),
                    encoding='utf-8')
            except Exception as err:
                print(err)

    def load(self):
        if self.__fname is not None:
            try:
                self.setText(
                    read_text(
                        self.__fname, encoding='utf-8', default=''))
            except Exception as err:
                print(err)
        else:
            self.setText('')

    def set_fname(self, fname=None):
        self.__fname = fname
        self.load()

    def get_fname(self):
        return self.__fname

    def enterEvent(self, event):
        gui.status(f"{self.__fname}", 3000)


class SetupFileEdit(QtWidgets.QListWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(
            QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
        # 连接拖拽完成信号
        self.model().rowsMoved.connect(self.on_rows_moved)
        for file_path in setup_files.get_files():
            self.add_file_to_list(file_path)

    def contextMenuEvent(self, event):  # 右键菜单
        menu = QtWidgets.QMenu(self)
        menu.addAction(create_action(self, '添加', slot=self.add_file))
        menu.addAction(create_action(self, '忽略', slot=self.remove_selected))
        menu.addAction(create_action(self, '重置', slot=self.reset_files))
        menu.exec(event.globalPos())

    def on_rows_moved(self, parent, start, end, destination, row):
        """
        当拖拽操作完成后触发的槽函数
        """
        print(f"项目从位置 {start} 移动到 {row}")
        self.save_files()  # 自动保存新的顺序

    def reset_files(self):
        while self.count() > 0:
            self.takeItem(0)
        setup_files.set_files([])  # 把额外保存的删除掉
        for file_path in setup_files.get_files(rank_max=1.0e200):
            self.add_file_to_list(file_path)
        self.save_files()  # 自动保存

    def save_files(self):
        """保存当前列表到环境变量"""
        file_paths = []
        for i in range(self.count()):
            file_paths.append(self.item(i).text())
        setup_files.set_files(file_paths)

    def add_file(self):
        """添加新的启动文件"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择Python启动文件",
            "",
            "Python文件 (*.py);;所有文件 (*)"
        )
        if file_path and os.path.isfile(file_path):
            existing_files = [self.item(i).text() for i in
                              range(self.count())]
            if file_path not in existing_files:
                self.add_file_to_list(file_path)
                self.save_files()  # 自动保存

    def add_file_to_list(self, file_path):
        """将文件路径添加到列表控件"""
        item = QtWidgets.QListWidgetItem(file_path)
        item.setToolTip(file_path)
        item.setFlags(
            item.flags() | QtCore.Qt.ItemFlag.ItemIsEnabled |
            QtCore.Qt.ItemFlag.ItemIsSelectable |
            QtCore.Qt.ItemFlag.ItemIsDragEnabled)
        self.addItem(item)

    def remove_selected(self):
        """移除选中的文件"""
        selected = self.selectedItems()
        if not selected:
            return

        for item in selected:
            self.takeItem(self.row(item))
        self.save_files()  # 自动保存
        print(f"已移除 {len(selected)} 个文件")

    @staticmethod
    def on_item_double_clicked(item):
        """双击打开文件编辑"""
        file_path = item.text()
        if os.path.isfile(file_path):
            try:
                gui.open_code(file_path)
            except Exception as err:
                print(f"打开文件失败: {str(err)}")
        else:
            print(f"文件不存在: {file_path}")


class AppPathEdit(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel(self)
        label.setText('请在此输入文件名: ')
        layout.addWidget(label)

        self.fname_edit = QtWidgets.QLineEdit(self)
        self.fname_edit.textChanged.connect(self.update_files)
        layout.addWidget(self.fname_edit)

        label = QtWidgets.QLabel(self)
        label.setText('完整路径如下: ')
        layout.addWidget(label)

        self.output = QtWidgets.QTextBrowser(self)
        layout.addWidget(self.output)

        button = QtWidgets.QPushButton(self)
        button.setText('添加搜索路径')
        button.clicked.connect(self.add_path)
        layout.addWidget(button)

        self.update_files()

    def update_files(self):
        filename = self.fname_edit.text()
        if len(filename) == 0:
            text = ''
            for path in app_data.get_paths():
                text = text + path + '\n'
            self.output.setPlainText(text)
            return
        results = app_data.find_all(filename)
        if len(results) == 0:
            self.output.setPlainText('未找到')
            return
        else:
            self.output.setPlainText('\n'.join(results))

    @staticmethod
    def add_path():
        choose_path()


class EnvEdit(QtWidgets.QTableWidget):
    class EnvLineEdit(QtWidgets.QLineEdit):

        def __init__(self, parent=None, key=None):
            super().__init__(parent)
            self.key = None
            self.set_key(key)
            self.editingFinished.connect(self.save)

        def set_key(self, key):
            self.key = key
            self.load()

        def load(self):
            if self.key is not None:
                self.setText(
                    app_data.getenv(self.key, encoding='utf-8', default=''))

        def save(self):
            if self.key is not None:
                app_data.setenv(key=self.key, value=self.text(),
                                encoding='utf-8')
                gui.status(f'保存成功. key = {self.key}, value = {self.text()}')

    class EnvComboBox(QtWidgets.QComboBox):
        def __init__(self, parent=None, key=None):
            super().__init__(parent)
            self.key = key
            self.currentTextChanged.connect(self.save)

        def set_key(self, key):
            self.key = key
            self.load()

        def load(self):
            if self.key is not None:
                self.setCurrentText(
                    app_data.getenv(self.key, encoding='utf-8', default=''))

        def save(self):
            if self.key is not None:
                app_data.setenv(key=self.key, value=self.currentText(),
                                encoding='utf-8')
                gui.status(
                    f'保存成功. key = {self.key}, value = {self.currentText()}')

    sigRefresh = QtCore.pyqtSignal()

    def __init__(self, parent=None, items=None):
        super().__init__(parent)
        self.env_items = items
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sigRefresh.connect(self.refresh)
        self.sigRefresh.emit()

    def refresh(self):
        data = self.env_items
        if data is None:
            return
        self.setRowCount(len(data))
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['项目', '值', '备注'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for i in range(len(data)):
            label = data[i].get('label')
            key = data[i].get('key')
            items = data[i].get('items')
            note = data[i].get('note')
            if label is not None:
                self.setItem(i, 0, QtWidgets.QTableWidgetItem(label))
            assert isinstance(key, str)
            if items is None:
                item = EnvEdit.EnvLineEdit()
                item.set_key(key)
            else:
                item = EnvEdit.EnvComboBox()
                item.addItems(items)
                item.set_key(key)
            self.setCellWidget(i, 1, item)
            if isinstance(note, str):
                self.setItem(i, 2, QtWidgets.QTableWidgetItem(note))
            self.resizeRowToContents(i)

    def resizeEvent(self, event):
        for row in range(self.rowCount()):
            self.resizeRowToContents(row)
        super().resizeEvent(event)


class TextBrowser(QtWidgets.QTextBrowser):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status = None
        self.context_actions = [create_action(self, "清除内容", icon='clean', slot=self.clear)]

    def contextMenuEvent(self, event):
        # 创建菜单并添加清除动作
        self.get_context_menu().exec(event.globalPos())

    def get_context_menu(self):
        menu = super().createStandardContextMenu()
        menu.addSeparator()
        for action in self.context_actions:
            if isinstance(action, QAction):
                menu.addAction(action)
            else:
                menu.addSeparator()
        return menu

    def set_status(self, text):
        self._status = text

    def enterEvent(self, event):
        if self._status is not None:
            gui.status(self._status, 3000)
        super().enterEvent(event)

    def export_data(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, '导出文本',
            '',
            f'文本文件 (*.txt)')
        if len(fpath) > 0:
            write_text(
                path=fpath, text=self.toPlainText(),
                encoding='utf-8')


class ReadMeBrowser(TextBrowser):
    def __init__(self, parent=None):
        super(ReadMeBrowser, self).__init__(parent)
        self._load()
        self.context_actions.append(create_action(self, "重新导入并显示ReadMe", slot=self._load))
        self.context_actions.append(create_action(self, "关于", slot=gui.show_about))
        self.context_actions.append(create_action(self, "注册", slot=gui.show_reg_tool))

    def _load(self):
        from zmlx import get_path
        path = get_path('..', 'README.md')
        if os.path.isfile(path):
            self.setOpenLinks(True)
            self.setOpenExternalLinks(True)
            self.setMarkdown(read_text(path=path, encoding='utf-8'))
            self.set_status(path)


class TabDetailView(QtWidgets.QTableWidget):
    class TabWrapper:
        def __init__(self, *tab_widgets):
            self.tab_widgets = tab_widgets

        def count(self):
            return sum([w.count() for w in self.tab_widgets])

        def get(self, index):
            for widget_idx in range(len(self.tab_widgets)):
                widget = self.tab_widgets[widget_idx]
                if index < widget.count():
                    return widget.tabText(index), type(widget.widget(index)).__name__
                else:
                    index -= widget.count()
            return "", ""

        def remove(self, index):
            for widget_idx in range(len(self.tab_widgets)):
                widget = self.tab_widgets[widget_idx]
                if index < widget.count():
                    widget.close_tab(index)
                    break
                else:
                    index -= widget.count()

        def show(self, index):
            for widget_idx in range(len(self.tab_widgets)):
                widget = self.tab_widgets[widget_idx]
                if index < widget.count():
                    if not widget.isVisible():
                        widget.setVisible(True)
                    widget.setCurrentIndex(index)
                    break
                else:
                    index -= widget.count()

    def __init__(self, parent=None, obj=None, header_labels=None):
        super().__init__(parent)
        self.header_labels = header_labels
        self.obj = obj
        self._init_ui()
        self._connect_signals()
        self.refresh()

    def _init_ui(self):
        self.setColumnCount(3)
        if self.header_labels is not None:
            assert len(self.header_labels) == 3
            self.setHorizontalHeaderLabels(
                self.header_labels)
        else:
            self.setHorizontalHeaderLabels(['标题', '类型', '操作'])
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(True)
        self.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu)  # 启用右键菜单

    def _connect_signals(self):
        self.cellClicked.connect(self._on_cell_clicked)
        self.customContextMenuRequested.connect(
            self._show_context_menu)  # 右键菜单信号

    def refresh(self):
        if (not hasattr(self.obj, 'count')
                or not hasattr(self.obj, 'get')
                or not hasattr(self.obj, 'remove')
                or not hasattr(self.obj, 'show')):
            return
        row_count = self.obj.count()
        self.setRowCount(row_count)

        for row in range(row_count):
            value, name = self.obj.get(row)
            # 数值列（直接显示值）
            self.setItem(row, 0, QtWidgets.QTableWidgetItem(str(value)))
            # 类型列（使用type获取类型）
            self.setItem(row, 1, QtWidgets.QTableWidgetItem(name))
            # 删除按钮
            btn = QtWidgets.QToolButton(self)
            btn.setText('x')
            btn.clicked.connect(lambda _, r=row: self._handle_delete(r))
            self.setCellWidget(row, 2, btn)

    def _handle_delete(self, row):
        self.obj.remove(row)
        self.refresh()

    def _on_cell_clicked(self, row, column):
        if column in (0, 1):
            self.obj.show(row)

    def _show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        refresh_action = menu.addAction("刷新表格")
        refresh_action.triggered.connect(self.refresh)
        menu.exec(self.viewport().mapToGlobal(pos))


class CodeHistoryView(QtWidgets.QWidget):
    def __init__(self, parent=None, count_max=100):
        super().__init__(parent)
        self.__current_folder = None
        self.count_max = count_max

        layout = QtWidgets.QHBoxLayout(self)

        # 左侧文件列表（保持与之前相同）
        self._list = QtWidgets.QListWidget()
        self._list.itemClicked.connect(self.__show_content)
        layout.addWidget(self._list, stretch=2)

        # 右侧代码编辑器
        self._edit = CodeEdit()
        layout.addWidget(self._edit, stretch=5)

        self._list.clear()
        self._edit.clear()

    def set_folder(self, folder, count_max=None):
        """
        设置目标文件夹，自动过滤.py文件
        """
        if count_max is not None:
            self.count_max = count_max

        self.__current_folder = os.path.abspath(folder)
        self.__refresh_list()

        if self._list.count() > 0:
            self._list.setCurrentRow(0)
            self.__show_content(self._list.currentItem())

    def console_exec(self):
        self._edit.console_exec()

    def __refresh_list(self):
        """
        刷新.py文件列表
        """
        self._list.clear()

        if not self.__current_folder or not os.path.isdir(
                self.__current_folder):
            return

        pattern = os.path.join(self.__current_folder, "*.py")
        files = [(f, QtCore.QFileInfo(f).lastModified()) for f in
                 glob.glob(pattern)]
        sorted_files = sorted(files, key=lambda x: x[1], reverse=True)

        for idx, (file_path, mtime) in enumerate(sorted_files, 1):
            if idx > self.count_max:
                break
            time_str = QtCore.QDateTime.toString(
                mtime, "yyyy-MM-dd hh:mm")
            text = read_text(file_path, encoding='utf-8')
            text = text[:300]
            item = QtWidgets.QListWidgetItem(
                f"\n{idx:02d}.\t{time_str}\n\n{text}\n--------------\n\n")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, file_path)
            self._list.addItem(item)

    def __show_content(self, item):
        """
        使用CodeEdit打开文件
        """
        file_path = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self._edit.open(file_path)  # 依赖CodeEdit自身的错误处理


class OutputHistoryView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_folder = None
        self.current_ext = None
        self.main_layout = QtWidgets.QHBoxLayout(self)

        # 左侧文件列表
        self.file_list = QtWidgets.QListWidget()
        self.file_list.itemClicked.connect(self.show_file_content)
        self.main_layout.addWidget(self.file_list, stretch=2)

        # 右侧文本显示
        self.text_view = TextBrowser(self)
        self.main_layout.addWidget(self.text_view, stretch=5)

        self.clear_display()
        self.set_folder()

    def clear_display(self):
        self.file_list.clear()
        self.text_view.clear()

    def set_folder(self, folder=None):
        if folder is None:
            folder = app_data.root('output_history')

        if folder is not None:
            self.current_folder = folder
            self.current_ext = 'txt'
            self.refresh_file_list()

            if self.file_list.count() > 0:
                self.file_list.setCurrentRow(0)
                self.show_file_content(self.file_list.currentItem())

    def refresh_file_list(self):
        self.file_list.clear()

        if not self.current_folder or not os.path.isdir(self.current_folder):
            return

        pattern = os.path.join(self.current_folder, f"*.{self.current_ext}")
        files = [(f, QtCore.QFileInfo(f).lastModified()) for f in
                 glob.glob(pattern)]
        sorted_files = sorted(files, key=lambda x: x[1], reverse=True)

        for idx, (file_path, mtime) in enumerate(sorted_files, 1):
            filename = os.path.basename(file_path)
            time_str = QtCore.QDateTime.toString(
                mtime,
                "yyyy-MM-dd hh:mm")  # 时间格式保持兼容

            item = QtWidgets.QListWidgetItem(
                f"{idx:02d}. {time_str}: \n\t{filename}\n")
            item.setData(QtCore.Qt.ItemDataRole.UserRole,
                         file_path)  # 使用兼容的角色类型
            self.file_list.addItem(item)

    def show_file_content(self, item):
        file_path = item.data(QtCore.Qt.ItemDataRole.UserRole)
        try:
            with open(file_path, "r") as f:
                text = f.read()
                self.text_view.setText(text)
        except Exception as err:
            self.text_view.setText(
                f"读取文件错误：{str(err)}. file_path={file_path}")


class DemoView(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super(DemoView, self).__init__(parent)
        self.__data = []
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.clicked.connect(self.item_clicked)
        self.refresh()

    def refresh(self):
        from zmlx.demo.list_demo_files import list_demo_files
        from zmlx.demo.path import get_path
        folder = get_path()
        self.__data = [['demo根目录', folder, folder], ]
        for path, desc in list_demo_files():
            self.__data.append([os.path.relpath(path, folder), path, desc])

        if len(self.__data) == 0:
            self.clear()
            return

        self.setRowCount(len(self.__data))
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['项目 (点击打开)', '说明 (点击运行)'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for row_id in range(len(self.__data)):
            try:
                name, path, desc = self.__data[row_id]
                self.setItem(
                    row_id, 0, QtWidgets.QTableWidgetItem(name))
                self.setItem(
                    row_id, 1, QtWidgets.QTableWidgetItem(desc))
            except Exception as err:
                print(err)
                for col_id in range(2):
                    self.setItem(
                        row_id, col_id, QtWidgets.QTableWidgetItem(''))

    def item_clicked(self, index):
        row_id = index.row()
        if row_id >= len(self.__data):
            return

        try:
            name, path, desc = self.__data[row_id]
            if os.path.isfile(path):
                ext = os.path.splitext(path)[-1]
                if ext is not None:
                    if ext.lower() == '.py' or ext.lower() == '.pyw':
                        if index.column() == 0:
                            gui.open_code(path)
                        else:
                            gui.exec_file(path)
            if os.path.isdir(path):
                os.startfile(path)
        except Exception as err:
            print(err)


class CwdView(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super(CwdView, self).__init__(parent)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        self.clicked.connect(self.item_clicked)
        self.doubleClicked.connect(self.item_double_clicked)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(500)
        self.refresh()

    def __refresh(self):
        folder = os.getcwd()
        data = [['..', '文件夹', '', ''], ]
        try:
            names = os.listdir(folder)
        except Exception as err:
            print(err)
            names = []
        for name in names:
            path = os.path.join(folder, name)
            try:
                if os.path.isfile(path):
                    data.append([name, '文件', fsize2str(os.path.getsize(path)),
                                 f'{time.ctime(os.path.getmtime(path))}'])
                    continue

                if os.path.isdir(path):
                    data.append([name, '文件夹', '', ''])
                    continue
            except Exception as err:
                print(err)
        self.setRowCount(len(data))
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(['名称', '类型', '大小', '修改时间'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        for i_row in range(len(data)):
            for i_col in range(4):
                self.setItem(i_row, i_col,
                             QtWidgets.QTableWidgetItem(data[i_row][i_col]))

    def refresh(self):
        cpu_t = timeit.default_timer()
        #
        try:
            self.__refresh()
        except Exception as err:
            print(err)
            self.clear()
        #
        cpu_t = timeit.default_timer() - cpu_t
        msec = clamp(int(cpu_t * 200 / 0.001), 200, 8000)
        self.timer.setInterval(msec)

    def item_clicked(self, index):
        if index.column() != 0:
            return
        item = self.item(index.row(), index.column())
        text = item.text()
        if text == '..':
            fpath = os.path.dirname(os.getcwd())
        else:
            fpath = os.path.join(os.getcwd(), text)

        if os.path.isfile(fpath):
            ext = os.path.splitext(fpath)[-1]
            if ext is not None:
                if ext.lower() == '.py' or ext.lower() == '.pyw':
                    gui.open_code(fpath)

    def item_double_clicked(self, index):
        if index.column() != 0:
            return
        item = self.item(index.row(), index.column())
        text = item.text()
        if text == '..':
            fpath = os.path.dirname(os.getcwd())
        else:
            fpath = os.path.join(os.getcwd(), text)
        gui.open_file(fpath)


class TimerView(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(500)
        self.refresh()

    def export_data(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, '导出Timer',
            '',
            f'Text File(*.txt)')
        with open(make_parent(fpath), 'w', encoding='utf-8') as file:
            for key, val in timer.key2nt.items():
                n, t = val
                file.write(f'{key}\t{n}\t{t}\n')

    def refresh(self):
        """
        更新
        """
        if not self.isVisible():
            return

        cpu_t = timeit.default_timer()

        data = []
        for key, nt in timer.key2nt.items():
            n, t = nt
            data.append([f'{key}', f'{n}', time2str(t), time2str(t / n)])

        self.setRowCount(len(data))
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(
            ['名称', '调用次数', '总耗时', '单次耗时'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for i_row in range(len(data)):
            for i_col in range(4):
                self.setItem(
                    i_row, i_col,
                    QtWidgets.QTableWidgetItem(data[i_row][i_col]))

        cpu_t = timeit.default_timer() - cpu_t
        msec = clamp(int(cpu_t * 200 / 0.001), 200, 8000)
        self.timer.setInterval(msec)


class About(QtWidgets.QTableWidget):

    def __init__(self, parent=None, lic_desc=None):
        super(About, self).__init__(parent)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.context_actions = [
            create_action(self, "ReadMe", slot=gui.show_readme),
            create_action(self, "注册", slot=gui.show_reg_tool)
        ]
        self.setup(lic_desc)

    def get_context_menu(self):
        menu = QtWidgets.QMenu(self)
        for action in self.context_actions:
            menu.addAction(action)
        return menu

    def contextMenuEvent(self, event):
        self.get_context_menu().exec(event.globalPos())

    def setup(self, lic_desc):
        data = [
            ['安装路径', f'{get_dir()}'],
            ['当前版本', f'{core.time_compile}; {core.compiler}'],
            ['授权情况', f'{lic_desc}'],
            ['Python解释器', sys.executable],
            ['Python版本', sys.version],
            ['Qt版本', qt_name],
            ['QWebEngineView已安装',
             'Yes' if QWebEngineView is not None else 'No'],
            ['网址', 'https://gitee.com/geomech/hydrate'],
            ['通讯作者', '张召彬'],
            ['单位', '中国科学院地质与地球物理研究所'],
            ['联系邮箱', 'zhangzhaobin@mail.iggcas.ac.cn'],
            ['管理员权限', 'Yes' if lic.is_admin else 'No'],
            ['硬件码', f'{lic.usb_serial}'],
        ]
        self.setRowCount(len(data))
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['项目', '值'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for i_row in range(len(data)):
            for i_col in range(2):
                self.setItem(
                    i_row, i_col,
                    QtWidgets.QTableWidgetItem(data[i_row][i_col]))


class FeedbackTool(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.temp_file = os.path.join(app_data.temp(),
                                      "the_feedback_widget.tmp")
        main_layout = QtWidgets.QVBoxLayout(self)
        self.setWindowTitle("问题反馈")

        # 设置窗口策略（兼容不同版本）
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,  # 水平策略
            QtWidgets.QSizePolicy.Policy.Expanding  # 垂直策略
        )

        # 固定高度区域
        fixed_layout = QtWidgets.QVBoxLayout()
        fixed_layout.setContentsMargins(0, 0, 0, 0)
        fixed_layout.setSpacing(10)

        # 姓名输入
        lbl_name = QtWidgets.QLabel("姓名（最多10个字符）:")
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setMaxLength(10)
        self.name_edit.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,  # 水平策略
            QtWidgets.QSizePolicy.Policy.Fixed  # 垂直策略
        )
        fixed_layout.addWidget(lbl_name)
        fixed_layout.addWidget(self.name_edit)

        # 联系方式输入
        lbl_contact = QtWidgets.QLabel("联系方式（电话/邮箱，最多100字符）:")
        self.contact_edit = QtWidgets.QLineEdit()
        self.contact_edit.setMaxLength(100)
        self.contact_edit.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,  # 水平策略
            QtWidgets.QSizePolicy.Policy.Fixed  # 垂直策略
        )
        fixed_layout.addWidget(lbl_contact)
        fixed_layout.addWidget(self.contact_edit)

        main_layout.addLayout(fixed_layout)

        # 反馈内容区域（自适应高度）
        lbl_feedback = QtWidgets.QLabel("反馈内容（最多2000字符）:")
        self.feedback_edit = QtWidgets.QTextEdit()
        self.feedback_edit.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,  # 水平策略
            QtWidgets.QSizePolicy.Policy.Expanding  # 垂直策略
        )
        self.feedback_edit.setPlaceholderText("请详细描述您遇到的问题或建议")

        # 自适应区域布局
        scroll_layout = QtWidgets.QVBoxLayout()
        scroll_layout.setContentsMargins(0, 5, 0, 0)
        scroll_layout.addWidget(lbl_feedback)
        scroll_layout.addWidget(self.feedback_edit, stretch=1)
        main_layout.addLayout(scroll_layout, stretch=1)

        # 提交按钮
        self.submit_btn = QtWidgets.QPushButton("提交反馈")
        self.submit_btn.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed,  # 水平策略
            QtWidgets.QSizePolicy.Policy.Fixed  # 垂直策略
        )
        self.submit_btn.clicked.connect(self.submit_feedback)
        main_layout.addWidget(
            self.submit_btn,
            alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        # 设置布局拉伸比例
        main_layout.setStretch(0, 0)  # 固定区域
        main_layout.setStretch(1, 1)  # 自适应区域
        main_layout.setStretch(2, 0)  # 按钮区域

        self.setup_autosave()
        self.load_autosave()

    # 以下方法保持不变
    def setup_autosave(self):
        self.name_edit.textChanged.connect(self.save_autosave)
        self.contact_edit.textChanged.connect(self.save_autosave)
        self.feedback_edit.textChanged.connect(self.save_autosave)

    def save_autosave(self):
        data = {
            "name": self.name_edit.text(),
            "contact": self.contact_edit.text(),
            "feedback": self.feedback_edit.toPlainText()
        }
        try:
            with open(self.temp_file, 'w', encoding='utf-8') as f:
                f.write(
                    f"{data['name']}\n{data['contact']}\n{data['feedback']}")
        except Exception as err:
            print(f"自动保存失败: {str(err)}")

    def load_autosave(self):
        if os.path.exists(self.temp_file):
            try:
                with open(self.temp_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) >= 3:
                        self.name_edit.setText(lines[0].strip())
                        self.contact_edit.setText(lines[1].strip())
                        self.feedback_edit.setPlainText(
                            ''.join(lines[2:]).strip())
            except Exception as err:
                print(f"加载自动保存失败: {str(err)}")

    def validate_input(self):
        if not self.name_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "输入错误", "姓名不能为空")
            return False
        if not self.contact_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "输入错误", "联系方式不能为空")
            return False
        if len(self.feedback_edit.toPlainText().strip()) < 10:
            QtWidgets.QMessageBox.warning(self, "输入错误",
                                          "反馈内容至少需要10个字符")
            return False
        return True

    def submit_feedback(self):
        if not self.validate_input():
            return

        subject = f"用户反馈 - {self.name_edit.text()}"
        text = f"""姓名: {self.name_edit.text()}
联系方式: {self.contact_edit.text()}
反馈内容:
{self.feedback_edit.toPlainText()}"""

        try:
            from zml import sendmail
            success = sendmail(
                address="zhangzhaobin@mail.iggcas.ac.cn",
                subject=subject,
                text=text,
                name_from="用户反馈系统"
            )

            if success:
                QtWidgets.QMessageBox.information(self, "发送成功",
                                                  "反馈已成功提交，感谢您的支持！")
                self.name_edit.clear()
                self.contact_edit.clear()
                self.feedback_edit.clear()
                if os.path.exists(self.temp_file):
                    os.remove(self.temp_file)
            else:
                QtWidgets.QMessageBox.critical(self, "发送失败",
                                               "邮件发送失败，请检查网络连接")
        except Exception as err:
            QtWidgets.QMessageBox.critical(self, "错误", f"发生未知错误: {err}")


class RegTool(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel(self)
        label.setText('第1步，请将以下硬件码发给作者: ')
        layout.addWidget(label)

        output = QtWidgets.QTextBrowser(self)
        output.setPlainText(reg())
        layout.addWidget(output)

        label = QtWidgets.QLabel(self)
        label.setText('第2步，请将作者返回的注册码粘贴到下面: ')
        layout.addWidget(label)

        self.code = QtWidgets.QTextEdit(self)
        layout.addWidget(self.code)

        button = QtWidgets.QPushButton(self)
        button.setText('第3步，点击此按钮完成注册')
        button.clicked.connect(self.apply_reg)
        layout.addWidget(button)

    def apply_reg(self):
        text = self.code.toPlainText()
        if len(text) > 0:
            try:
                code = reg(text)
                print(code)
            except Exception as err:
                print(f"Error (RegTool.apply_reg): {err}")
        else:
            QtWidgets.QMessageBox.information(
                self,
                '提示', '请输入激活码后再试')


class Label(QtWidgets.QLabel):
    sig_double_clicked = QtCore.pyqtSignal()

    def __init__(self, parent=None, text=None, status=None,
                 double_clicked=None):
        super(Label, self).__init__(parent)
        self._status = status
        if text is not None:
            self.setText(text)
        if callable(double_clicked):
            self.sig_double_clicked.connect(lambda: double_clicked())

    def set_status(self, text):
        self._status = text

    def enterEvent(self, event):
        if self._status is not None:
            gui.status(self._status, 3000)
        super().enterEvent(event)

    def leaveEvent(self, event):
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.sig_double_clicked.emit()
        super().mouseDoubleClickEvent(event)  # 调用父类的事件处理


class ConsoleStateLabel(Label):
    def __init__(self, parent=None):
        super().__init__(parent)

        try:
            text = core.time_compile.split(',')[0]
            self.default_text = f'Version: {text}'
        except:
            self.default_text = 'Version: ERROR'

        self.setText('')
        self.set_status('双击显示程序内核的详细内容')
        self.sig_double_clicked.connect(lambda: gui.show_about())

    def setText(self, a0):
        if len(a0) == 0:
            a0 = self.default_text
        super().setText(a0)


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(TabWidget, self).__init__(parent)
        self.task_proc = TaskProc(self)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.setMovable(True)
        self.context_actions = []  # 附加的命令

    def contextMenuEvent(self, event):
        tab_index = None
        for i in range(self.count()):
            if self.tabBar().tabRect(i).contains(event.pos()):
                tab_index = i

        menu = QtWidgets.QMenu(self)
        if self.count() >= 1:
            menu.addAction(
                create_action(self, '关闭所有', slot=self.close_all_tabs))
            menu.addAction(
                create_action(self, '列出标签', slot=gui.show_tab_details))
            if tab_index is not None:
                menu.addSeparator()
                menu.addAction(create_action(
                    self, text='重命名',
                    slot=lambda: self._rename_tab(tab_index))
                )
                menu.addAction(create_action(
                    self, text='关闭',
                    slot=lambda: self.close_tab(tab_index))
                )
                menu.addAction(create_action(
                    self, text='关闭其它',
                    slot=lambda: self._close_all_except(tab_index))
                )

        if len(self.context_actions) > 0:
            menu.addSeparator()
            for action in self.context_actions:
                menu.addAction(action)

        menu.exec(event.globalPos())

    def close_tab(self, index):
        if index < self.count():
            widget = self.widget(index)
            closeable = getattr(widget, 'tab_closeable', None)
            if closeable or closeable is None:
                f = getattr(widget, 'save_file', None)  # 尝试调用save_file
                if callable(f):
                    try:
                        f()
                    except Exception as e:
                        print(e)
                widget.deleteLater()
                self.removeTab(index)
                return True
            else:
                return False
        else:
            return False

    def close_tab_object(self, widget):
        index = self.get_tab_index(widget)
        if index is not None:
            return self.close_tab(index)
        else:
            return False

    def add_task(self, task):
        self.task_proc.add(task)

    def find_widgets(self, the_type=None, text=None, is_ok=None):
        """
        返回给定条件的所有Widget对象。给定的所有条件需要同时满足
        Args:
            the_type: 控件的类型
            text: 标题
            is_ok: 一个函数，用于检查控件对象

        Returns:
            符合条件的所有Widget对象
            符合条件的所有Widget对象，否则返回None
        """
        assert the_type is not None or text is not None or is_ok is not None
        widgets = []
        for i in range(self.count()):
            widget = self.widget(i)
            if the_type is not None:
                if not isinstance(widget, the_type):
                    continue
            if text is not None:
                if text != self.tabText(i):
                    continue
            if callable(is_ok):
                if not is_ok(widget):
                    continue
            widgets.append(widget)
        return widgets

    def find_widget(self, the_type=None, text=None, is_ok=None):
        """
        返回给定条件的Widget。给定的所有条件需要同时满足
        Args:
            the_type: 控件的类型
            text: 标题
            is_ok: 一个函数，用于检查控件对象

        Returns:
            符合条件的Widget对象，否则返回None
        """
        assert the_type is not None or text is not None or is_ok is not None
        for i in range(self.count()):
            widget = self.widget(i)
            if the_type is not None:
                if not isinstance(widget, the_type):
                    continue
            if text is not None:
                if text != self.tabText(i):
                    continue
            if callable(is_ok):
                if not is_ok(widget):
                    continue
            return widget
        return None

    def get_widget(
            self, the_type, caption=None, on_top=None, init=None,
            type_kw=None, oper=None, icon=None, caption_color=None,
            set_parent=False, tooltip=None, is_ok=None, closeable=None):
        """
        返回一个控件，其中type为类型，caption为标题，现有的控件，只有类型和标题都满足，才会返回，否则就
        创建新控件。
        Args:
            the_type: 控件的类型
            caption: 标题
            on_top: 是否将控件设置为当前的控件
            init: 首次生成控件，在显示之前所做的操作
            type_kw: 用于创建控件的关键字参数
            oper: 每次调用都会执行，且在控件显示之后执行
            icon: 图标
            caption_color: 标题的颜色
            set_parent: 是否将控件的父对象设置为当前的窗口
            tooltip: 工具提示
            is_ok: 一个函数，用于检查控件对象
            closeable: 是否允许关闭

        Returns:
            符合条件的Widget对象，否则返回None
        """
        if caption is None:
            caption = 'untitled'
        widget = self.find_widget(the_type=the_type, text=caption, is_ok=is_ok)
        if widget is None:
            if self.count() >= 200:
                print(f'The current number of tabs has reached '
                      f'the maximum allowed')
                return None  # 为了稳定性，不允许标签页太多
            if type_kw is None:
                type_kw = {}
            if set_parent:
                type_kw['parent'] = self
            try:
                widget = the_type(**type_kw)
                assert isinstance(widget, the_type)
                if closeable is not None:
                    widget.tab_closeable = closeable
            except Exception as err:
                print(f'Error: {err}')
                return None
            if init is not None:
                try:
                    init(widget)
                except Exception as err:
                    print(f'Error: {err}')
            index = self.addTab(widget, caption)
            if icon is not None:
                self.setTabIcon(index, settings.load_icon(icon))
            self.setCurrentWidget(widget)
            if tooltip is not None:
                self.setTabToolTip(index, tooltip)
            if caption_color is not None:
                self.tabBar().setTabTextColor(
                    index, QtGui.QColor(caption_color)
                )
            if oper is not None:
                self.add_task(lambda: oper(widget))
            return widget
        else:
            if on_top:
                self.setCurrentWidget(widget)
            if oper is not None:
                self.add_task(lambda: oper(widget))
            return widget

    def get_tab_index(self, widget):
        for idx in range(self.count()):
            if id(self.widget(idx)) == id(widget):
                return idx
        return None

    def show_next(self):
        if self.count() > 1:
            index = self.currentIndex()
            if index + 1 < self.count():
                self.setCurrentIndex(index + 1)

    def show_prev(self):
        if self.count() > 1:
            index = self.currentIndex()
            if index > 0:
                self.setCurrentIndex(index - 1)

    def close_all_tabs(self):
        """
        关闭所有可以被关闭的标签页
        """
        idx = self.count() - 1
        while idx >= 0:
            succeed = self.close_tab(idx)
            if not succeed:
                print(f'failed to close tab {idx}')
            idx -= 1

    def _close_all_except(self, index):
        if 0 <= index < self.count():
            while self.count() > 1:
                if index > 0:
                    self.close_tab(0)
                    index -= 1
                else:
                    self.close_tab(1)
        else:
            self.close_all_tabs()

    def _rename_tab(self, index):
        if index < self.count():
            text, ok = QtWidgets.QInputDialog.getText(
                self, '重命名',
                '请输入新的名称:',
                text=self.tabText(index))
            if ok:
                self.setTabText(index, text)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.MiddleButton:  # 中间按钮关闭选项卡
            for i in range(self.count()):
                if self.tabBar().tabRect(i).contains(event.pos()):
                    self.close_tab(i)
        super().mousePressEvent(event)

    def get_figure_widget(self, init=None, folder_save=None, **kwargs):
        """
        返回一个用以 matplotlib 绘图的控件
        """
        from zmlx.ui.widget.plt import MatplotWidget
        kwargs.setdefault('icon', 'matplotlib')

        def init_x(widget):
            if callable(init):
                init(widget)
            if folder_save is not None:
                widget.set_save_folder(folder_save)

        return self.get_widget(the_type=MatplotWidget, init=init_x, **kwargs)

    def plot(
            self, kernel, *args, fname=None, dpi=None,
            caption=None, on_top=None, icon=None,
            clear=None,
            tight_layout=None,
            suptitle=None, folder_save=None,
            **kwargs
    ):
        """
        调用matplotlib执行绘图操作 注意，此函数会创建或者返回一个标签，并默认清除标签的绘图，返回使用回调函数
        在figure上绘图。
        Args:
            kernel: 绘图的回调函数，函数的原型为：
                def kernel(figure, *args, **kwargs):
                    ...
            fname: 输出的文件名
            dpi: 输出的分辨率
            *args: 传递给kernel函数的参数
            **kwargs: 传递给kernel函数的关键字参数
            caption: 窗口的标题
            on_top: 是否置顶
            icon: 窗口的图标
            clear: 是否清除之前的内容 (特别注意，默认是要清除之前的内容的，因此，如果要多个视图的时候，就不要使用clear)
            tight_layout: 是否自动调整子图参数，以防止重叠
            suptitle: 图表的标题
            folder_save: 自动保存图的文件夹

        Returns:
            None
        """
        if clear is None:  # 默认清除
            clear = True
        try:
            widget = self.get_figure_widget(
                caption=caption, on_top=on_top, icon=icon, folder_save=folder_save
            )

            def on_figure(figure):
                if clear:  # 清除
                    figure.clear()
                if callable(kernel):
                    try:
                        kernel(figure, *args, **kwargs)  # 这里，并不会传入clear参数
                    except Exception as kernel_err:
                        print(kernel_err)
                if isinstance(suptitle, str):
                    figure.suptitle(suptitle)
                if tight_layout:
                    figure.tight_layout()

            widget.plot_on_figure(on_figure=on_figure)
            if fname is not None:
                if dpi is None:
                    from zmlx.io.env import plt_export_dpi
                    dpi = plt_export_dpi.get_value()
                widget.savefig(fname=fname, dpi=dpi)

            return widget.figure  # 返回Figure对象，后续进一步处理
        except Exception as err:
            import zmlx.alg.sys as warnings
            warnings.warn(f'meet exception <{err}> when run <{kernel}>')
            return None


class OutputWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.text_browser = TextBrowser(self)
        layout.addWidget(self.text_browser)
        # 添加进度条（这也是作为标准输出）
        self.progress_label = QtWidgets.QLabel(self)
        self.progress_bar = QtWidgets.QProgressBar(self)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        self.progress(visible=False)
        # 覆盖text_browser的右键菜单
        get_context_menu = self.text_browser.get_context_menu

        def f2():
            menu = get_context_menu()
            menu.addSeparator()
            for ac in self.get_context_actions():
                menu.addAction(ac)
            return menu

        self.text_browser.get_context_menu = f2  # 替换

    def progress(
            self, label=None, val_range=None, value=None, visible=None):
        """
        显示进度
        """
        if label is not None:
            visible = True
            self.progress_label.setText(label)
        if val_range is not None:
            visible = True
            assert len(val_range) == 2
            self.progress_bar.setRange(*val_range)
        if value is not None:
            visible = True
            self.progress_bar.setValue(value)
        if visible is not None:
            self.progress_bar.setVisible(visible)
            self.progress_label.setVisible(visible)

    def get_context_actions(self):
        result = [create_action(
            self, '隐藏', icon='console',
            slot=lambda: gui.hide_console())]
        if gui.is_running():
            if gui.is_paused():
                result.append(create_action(
                    self, '继续', icon='begin',
                    slot=lambda: gui.set_paused(False))
                )
            else:
                result.append(create_action(
                    self, '暂停', icon='pause',
                    slot=lambda: gui.set_paused(True))
                )
            result.append(create_action(
                self, '停止', icon='stop',
                slot=lambda: gui.stop_console())
            )
        else:
            result.append(create_action(
                self, '重新执行', slot=lambda: gui.start_last())
            )
            result.append(create_action(
                self, '运行历史',
                slot=lambda: gui.show_code_history(
                    folder=app_data.root('console_history'),
                    caption='运行历史'))
            )
            result.append(create_action(
                self, '输出历史',
                slot=gui.show_output_history)
            )

        if app_data.get('DISABLE_PAUSE', False):
            result.append(create_action(
                self, '启用pause', slot=lambda: app_data.put('DISABLE_PAUSE', False))
            )
        else:
            result.append(create_action(
                self, '禁用pause', slot=lambda: app_data.put('DISABLE_PAUSE', True))
            )

        return result

    def add_text(self, text):
        self.text_browser.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.text_browser.insertPlainText(text)
        while self.text_browser.document().characterCount() > 10000:
            fulltext = self.text_browser.toPlainText()
            fulltext = fulltext[-int(len(fulltext) / 2): -1]
            self.text_browser.setPlainText(fulltext)

    def set_text(self, text):
        self.text_browser.setPlainText(text)
        self.text_browser.moveCursor(QtGui.QTextCursor.MoveOperation.End)

    def load_text(self, filename):
        try:
            if os.path.isfile(filename):
                with open(filename, 'r') as file:
                    self.set_text(file.read())
        except Exception as err2:
            print(err2)
            self.text_browser.setPlainText('')

    def save_text(self, filename):
        try:
            with open(filename, 'w') as file:
                file.write(self.text_browser.toPlainText())
        except Exception as err2:
            print(err2)
