"""
提供界面系统最核心的控件系统。
"""
import glob
import hashlib
import os
import subprocess
import sys
import time
import timeit
from datetime import datetime

from zml import (
    core, lic, get_dir, make_parent, reg, timer, app_data,
    write_text, read_text)
from zmlx.alg.base import fsize2str, time2str, clamp
from zmlx.alg.fsys import samefile, time_string
from zmlx.alg.search_paths import choose_path
from zmlx.ui.gui_buffer import gui
from zmlx.ui.alg import (
    add_code_history, create_action, add_exec_history,
    get_last_exec_history)
from zmlx.ui.pyqt import (
    QWebEngineView, is_pyqt6, QtCore, QtGui, QtWidgets, qt_name)
from zmlx.ui.settings import (
    get_default_code, load_icon, get_text, play_error,
    load_priority, priority_value, get_setup_files, set_setup_files)
from zmlx.ui.utils import CodeFile, SharedValue, BreakPoint

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
                self, "运行", 'begin', self.console_exec))
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
                    'set', install_qsci))

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


class SetupFileEdit(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.listWidget = QtWidgets.QListWidget()

        self.listWidget.setDragDropMode(
            QtWidgets.QAbstractItemView.DragDropMode.InternalMove)

        self.listWidget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.listWidget.itemDoubleClicked.connect(self.on_item_double_clicked)

        # 创建按钮
        self.addButton = QtWidgets.QPushButton("添加文件")
        self.removeButton = QtWidgets.QPushButton("忽略选中")
        self.resetButton = QtWidgets.QPushButton("重新搜索")

        # 按钮布局
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.addButton)
        button_layout.addWidget(self.removeButton)
        button_layout.addWidget(self.resetButton)

        # 主布局
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.listWidget)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # 连接信号
        self.addButton.clicked.connect(self.add_file)
        self.removeButton.clicked.connect(self.remove_selected)
        self.resetButton.clicked.connect(self.reset_files)
        # 连接拖拽完成信号
        self.listWidget.model().rowsMoved.connect(self.on_rows_moved)

        for file_path in get_setup_files():
            self.add_file_to_list(file_path)

    def on_rows_moved(self, parent, start, end, destination, row):
        """
        当拖拽操作完成后触发的槽函数
        """
        print(f"项目从位置 {start} 移动到 {row}")
        self.save_files()  # 自动保存新的顺序

    def reset_files(self):
        while self.listWidget.count() > 0:
            self.listWidget.takeItem(0)
        for file_path in get_setup_files(rank_max=1.0e200):
            self.add_file_to_list(file_path)
        print('启动文件列表已经重置')
        self.save_files()  # 自动保存

    def save_files(self):
        """保存当前列表到环境变量"""
        file_paths = []
        for i in range(self.listWidget.count()):
            file_paths.append(self.listWidget.item(i).text())
        set_setup_files(file_paths)
        print('启动文件列表已经保存')

    def add_file(self):
        """添加新的启动文件"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择Python启动文件",
            "",
            "Python文件 (*.py);;所有文件 (*)"
        )

        if file_path and os.path.isfile(file_path):
            existing_files = [self.listWidget.item(i).text() for i in
                              range(self.listWidget.count())]
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
        self.listWidget.addItem(item)

    def remove_selected(self):
        """移除选中的文件"""
        selected = self.listWidget.selectedItems()
        if not selected:
            return

        for item in selected:
            self.listWidget.takeItem(self.listWidget.row(item))
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

    def contextMenuEvent(self, event):
        # 创建菜单并添加清除动作
        self.get_context_menu().exec(event.globalPos())

    def get_context_menu(self):
        menu = super().createStandardContextMenu()
        menu.addSeparator()
        menu.addAction(create_action(
            self, "清除内容", 'clean', self.clear))
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
        path = os.path.join(get_dir(), 'README.md')
        if os.path.isfile(path):
            self.setOpenLinks(True)
            self.setOpenExternalLinks(True)
            self.setMarkdown(read_text(path=path, encoding='utf-8'))
            self.set_status(path)


class TabDetailView(QtWidgets.QTableWidget):
    class TabWrapper:
        def __init__(self, data):
            self.data = data

        def count(self):
            return self.data.count()

        def get(self, index):
            return self.data.tabText(index), type(
                self.data.widget(index)).__name__

        def remove(self, index):
            self.data.close_tab(index)

        def show(self, index):
            self.data.setCurrentIndex(index)

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
            btn = QtWidgets.QPushButton('移除', self)
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__current_folder = None

        layout = QtWidgets.QHBoxLayout(self)

        # 左侧文件列表（保持与之前相同）
        self.__list = QtWidgets.QListWidget()
        self.__list.itemClicked.connect(self.__show_content)
        layout.addWidget(self.__list, stretch=2)

        # 右侧代码编辑器
        self.__edit = CodeEdit()
        layout.addWidget(self.__edit, stretch=5)

        self.__list.clear()
        self.__edit.clear()

    def set_folder(self, folder):
        """设置目标文件夹，自动过滤.py文件"""
        self.__current_folder = os.path.abspath(folder)
        self.__refresh_list()

        if self.__list.count() > 0:
            self.__list.setCurrentRow(0)
            self.__show_content(self.__list.currentItem())

    def console_exec(self):
        self.__edit.console_exec()

    def __refresh_list(self):
        """刷新.py文件列表"""
        self.__list.clear()

        if not self.__current_folder or not os.path.isdir(
                self.__current_folder):
            return

        pattern = os.path.join(self.__current_folder, "*.py")
        files = [(f, QtCore.QFileInfo(f).lastModified()) for f in
                 glob.glob(pattern)]
        sorted_files = sorted(files, key=lambda x: x[1], reverse=True)

        for idx, (file_path, mtime) in enumerate(sorted_files, 1):
            time_str = QtCore.QDateTime.toString(
                mtime, "yyyy-MM-dd hh:mm")
            text = read_text(file_path, encoding='utf-8')
            text = text[:300]
            item = QtWidgets.QListWidgetItem(
                f"\n{idx:02d}.\t{time_str}\n\n{text}\n--------------\n\n")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, file_path)
            self.__list.addItem(item)

    def __show_content(self, item):
        """使用CodeEdit打开文件"""
        file_path = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self.__edit.open(file_path)  # 依赖CodeEdit自身的错误处理


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
        self.text_view = ConsoleOutput(self)
        self.main_layout.addWidget(self.text_view, stretch=5)

        self.clear_display()
        self.set_folder()

    def clear_display(self):
        self.file_list.clear()
        self.text_view.load_text('')

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
            self.text_view.load_text(file_path)
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
        self.__data = [['关于', folder,
                        f'注意，请单击以下项目以打开，之后点击任务栏上的<运行>按钮来运行. 可以在文件夹<{folder}>找到这些示例'], ]
        for path, desc in list_demo_files():
            self.__data.append([os.path.relpath(path, folder), path, desc])

        if len(self.__data) == 0:
            self.clear()
            return

        self.setRowCount(len(self.__data))
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['项目', '说明'])
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
                        gui.open_code(path)

            if os.path.isdir(path):
                os.startfile(path)
        except Exception as err:
            print(err)


class MemView(QtWidgets.QTableWidget):
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

    def __refresh(self):
        names_ignored = app_data.get('names_ignored', None)
        if names_ignored is None:
            space = {}
            exec('from zmlx import *', space)
            names_ignored = set(space.keys())
            app_data.put('names_ignored', names_ignored)
        data = []
        for key, value in app_data.space.items():
            if len(key) > 2:
                if key[0:2] == '__':
                    continue
            if key in names_ignored:
                continue
            data.append([key, f'{value}', f'{type(value)}'])

        self.setRowCount(len(data))
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['名称', '值', '类型'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for i_row in range(len(data)):
            for i_col in range(3):
                self.setItem(
                    i_row, i_col,
                    QtWidgets.QTableWidgetItem(data[i_row][i_col]))

    def refresh(self):
        """
        更新
        """
        if not self.isVisible():
            return
        cpu_t = timeit.default_timer()
        try:
            self.__refresh()
        except Exception as err:
            print(err)
            self.clear()
        cpu_t = timeit.default_timer() - cpu_t
        msec = clamp(int(cpu_t * 200 / 0.001), 200, 8000)
        self.timer.setInterval(msec)


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


class PackageTool(QtWidgets.QTableWidget):
    class InstallThread(QtCore.QThread):
        finished = QtCore.pyqtSignal(int)

        def __init__(self, package_name, row):
            super().__init__()
            self.package_name = package_name
            self.row = row

        def run(self):
            try:
                # 创建子进程并捕获输出
                proc = subprocess.Popen(
                    [sys.executable, "-m", "pip", "install", self.package_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )

                # 实时读取输出
                while True:
                    line = proc.stdout.readline()
                    if not line:
                        break
                    print(f"[{self.package_name}]", line.strip())

                # 等待进程结束并检查返回码
                proc.wait()
                if proc.returncode != 0:
                    raise subprocess.CalledProcessError(proc.returncode,
                                                        proc.args)

            except subprocess.CalledProcessError as err:
                print(f"安装失败: {err}")
            finally:
                self.finished.emit(self.row)

    def __init__(self, parent=None, packages=None):
        super().__init__(parent)
        self.setup_ui()
        self.threads = []
        if packages is not None:
            self.set_packages(*packages)

    def setup_ui(self):
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["包名", "状态", "操作"])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

    def set_packages(self, *packages):
        self.clearContents()
        self.setRowCount(len(packages))

        for row, pkg in enumerate(packages):
            # 包名称列
            name_item = QtWidgets.QTableWidgetItem(pkg["package_name"])
            name_item.setData(QtCore.Qt.ItemDataRole.UserRole, pkg)
            self.setItem(row, 0, name_item)

            # 状态列
            status_item = QtWidgets.QTableWidgetItem()
            self.setItem(row, 1, status_item)

            # 操作列
            button = QtWidgets.QPushButton("安装")
            button.setCursor(
                QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            self.setCellWidget(row, 2, button)

            self.update_row_status(row)

    def update_row_status(self, row):
        pkg_data = self.item(row, 0).data(
            QtCore.Qt.ItemDataRole.UserRole)
        import_name = pkg_data["import_name"]
        button = self.cellWidget(row, 2)

        if self.check_installation(import_name):
            self.item(row, 1).setText("已安装")
            button.setEnabled(False)
            button.setText("已安装")
            button.setStyleSheet("color: #666; background-color: #eee")
        else:
            self.item(row, 1).setText("尚未安装")
            button.setEnabled(True)
            button.setText("安装")
            button.setStyleSheet("")
            button.clicked.connect(lambda: self.start_installation(row))

    @staticmethod
    def check_installation(import_name):
        try:
            __import__(import_name)
            return True
        except ImportError:
            return False

    def start_installation(self, row):
        pkg_data = self.item(row, 0).data(
            QtCore.Qt.ItemDataRole.UserRole)
        package_name = pkg_data["package_name"]

        # 更新界面状态
        self.item(row, 1).setText("安装中...")
        button = self.cellWidget(row, 2)
        button.setEnabled(False)

        # 创建并启动安装线程
        thread = PackageTool.InstallThread(package_name, row)
        thread.finished.connect(self.handle_install_result)
        self.threads.append(thread)
        thread.start()

    def handle_install_result(self, row):
        self.update_row_status(row)
        # 移除已完成线程
        self.threads = [t for t in self.threads if t.isRunning()]


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
            except:
                pass
        else:
            QtWidgets.QMessageBox.information(
                self,
                '提示', '请输入激活码后再试')


class Label(QtWidgets.QLabel):

    def __init__(self, parent=None):
        super(Label, self).__init__(parent)
        self._style_backup = None
        self._status = None

    def set_status(self, text):
        self._status = text

    def enterEvent(self, event):
        if self._status is not None:
            gui.status(self._status, 3000)
        if self._style_backup is None:
            self._style_backup = self.styleSheet()
        self.setStyleSheet('border: 1px solid red;')
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._style_backup is not None:
            self.setStyleSheet(self._style_backup)
        super().leaveEvent(event)


class VersionLabel(Label):
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            text = core.time_compile.split(',')[0]
            self.setText(f'Version: {text}')
        except Exception as err:
            print(err)
            self.setText('Version: ERROR')
        self.set_status('程序内核版本，双击显示详细内容')

    def mouseDoubleClickEvent(self, event):
        """
        在鼠标双击的时候，清除所有的内容
        """
        try:
            gui.show_about()
        except Exception as err:
            print(err)
        super().mouseDoubleClickEvent(event)  # 调用父类的事件处理


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(TabWidget, self).__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.setMovable(True)
        self.set_position()
        self.set_shape()

    def set_position(self):
        try:
            text = app_data.getenv('TabPosition', default='North',
                                   ignore_empty=True)
            if text == 'North':
                self.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)
            if text == 'South':
                self.setTabPosition(QtWidgets.QTabWidget.TabPosition.South)
            if text == 'East':
                self.setTabPosition(QtWidgets.QTabWidget.TabPosition.East)
            if text == 'West':
                self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        except Exception as err:
            print(err)

    def set_shape(self):
        try:
            text = app_data.getenv('TabShape', default='Rounded',
                                   ignore_empty=True)
            if text == 'Triangular':
                self.setTabShape(QtWidgets.QTabWidget.TabShape.Triangular)
            if text == 'Rounded':
                self.setTabShape(QtWidgets.QTabWidget.TabShape.Rounded)
        except Exception as err:
            print(err)

    def contextMenuEvent(self, event):
        # 点击的标签的索引
        tab_index = None
        for i in range(self.count()):
            if self.tabBar().tabRect(i).contains(event.pos()):
                tab_index = i

        menu = QtWidgets.QMenu(self)
        if self.count() >= 1:
            menu.addAction(gui.get_action('console_show'))
            menu.addAction(gui.get_action('console_hide'))
            menu.addSeparator()
            menu.addAction(gui.get_action('close_all_tabs'))
            menu.addAction(gui.get_action('tab_details'))
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
            menu.addSeparator()
        menu.addAction(gui.get_action('readme'))
        menu.addAction(gui.get_action('about'))
        menu.addSeparator()
        menu.addAction(gui.get_action('open'))
        menu.addAction(gui.get_action('set_cwd'))
        menu.addAction(gui.get_action('demo'))
        menu.exec(event.globalPos())

    def close_tab(self, index):
        widget = self.widget(index)
        widget.deleteLater()
        self.removeTab(index)

    def find_widget(self, the_type=None, text=None):
        assert the_type is not None or text is not None
        for i in range(self.count()):
            widget = self.widget(i)
            if the_type is not None:
                if not isinstance(widget, the_type):
                    continue
            if text is not None:
                if text != self.tabText(i):
                    continue
            return widget
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
        while self.count() > 0:
            self.close_tab(0)

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
            menu.addSeparator()
            menu.addAction(gui.get_action('console_hide'))
            if self.console.is_running():
                menu.addAction(gui.get_action('console_pause'))
                menu.addAction(gui.get_action('console_resume'))
                menu.addAction(gui.get_action('console_stop'))
            else:
                menu.addAction(gui.get_action('console_start_last'))
                menu.addAction(gui.get_action('show_code_history'))
                menu.addAction(gui.get_action('show_output_history'))
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


class ConsoleThread(QtCore.QThread):
    sig_done = QtCore.pyqtSignal()
    sig_err = QtCore.pyqtSignal(str)

    def __init__(self, code):
        super(ConsoleThread, self).__init__()
        self.code = code
        self.result = None
        self.post_task = None
        self.text_end = None
        self.time_beg = None

    def run(self):
        if self.code is not None:
            try:
                self.result = self.code()
            except KeyboardInterrupt:
                print('KeyboardInterrupt')
            except Exception as err:
                self.sig_err.emit(f'{err}')
        self.sig_done.emit()


class Console(QtWidgets.QWidget):
    sig_kernel_started = QtCore.pyqtSignal()
    sig_kernel_done = QtCore.pyqtSignal()
    sig_kernel_err = QtCore.pyqtSignal(str)
    sig_refresh = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(Console, self).__init__(parent)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QtWidgets.QSplitter(self)
        self.splitter.setOrientation(QtCore.Qt.Orientation.Vertical)
        main_layout.addWidget(self.splitter)

        self.output_widget = ConsoleOutput(self.splitter, console=self)
        self.input_editor = CodeEdit(self.splitter)

        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addItem(QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum))

        def add_button(text, icon, slot):
            button = QtWidgets.QPushButton(self)
            button.setText(get_text(text))
            button.setIcon(load_icon(icon))
            button.clicked.connect(slot)
            h_layout.addWidget(button)
            return button

        # 开始运行
        self.button_exec = add_button(
            '运行', 'begin',
            lambda: self.exec_file(fname=None))
        self.button_exec.setToolTip(
            '运行此按钮上方输入框内的脚本. 如需要运行标签页的脚本，请点击工具栏的运行按钮')
        self.button_exec.setShortcut('Ctrl+Return')
        # 暂停/继续：两者只显示一个
        self.button_pause = add_button(
            '暂停', 'pause', lambda: self.set_pause(True))
        self.button_continue = add_button(
            '继续', 'begin', lambda: self.set_pause(False))
        self.button_continue.setVisible(False)
        # 终止
        self.button_exit = add_button('终止', 'stop', self.stop)
        self.button_exit.setToolTip(
            '安全地终止内核的执行 (需要提前在脚本内设置break_point)')

        h_layout.addItem(QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum))
        main_layout.addLayout(h_layout)

        self.kernel_err = None
        self.thread = None
        self.result = None
        if app_data.get('gui') is None:
            app_data.put('gui', gui)
        self.restore_code()

        self.break_point = BreakPoint(self)
        self.flag_exit = SharedValue(False)

        def set_visible():
            if not self.isVisible():
                self.setVisible(True)
                self.sig_refresh.emit()

        # 只要有线程启动，就显示控制台窗口
        self.sig_kernel_started.connect(set_visible)

    def refresh_view(self):
        running = self.is_running()
        pause = self.get_pause()
        self.button_exec.setEnabled(not running)
        self.button_exec.setStyleSheet(
            'background-color: #e15631; ' if running else '')
        self.button_pause.setVisible(not pause)
        self.button_pause.setEnabled(running)
        self.button_continue.setVisible(pause)
        self.button_continue.setEnabled(running)
        self.button_exit.setEnabled(running)
        self.button_exit.setStyleSheet(
            'background-color: #e15631; ' if self.get_stop() else '')
        self.input_editor.setVisible(
            True if not running else samefile(
                app_data.get('__file__', ''),
                self.input_editor.get_fname()))
        self.output_widget.setStyleSheet(
            'border: 1px dashed red' if running else '')

    def get_pause(self):
        return self.break_point.locked()

    def set_pause(self, value):
        if value != self.get_pause():
            if self.break_point.locked():
                self.break_point.unlock()
            else:
                self.break_point.lock()
            self.sig_refresh.emit()

    def get_stop(self):
        return self.flag_exit.get()

    def set_stop(self, value):
        self.flag_exit.set(value)
        if value:
            self.set_pause(False)
        self.sig_refresh.emit()

    def stop(self):
        app_data.log(f'execute <stop_clicked> of {self}')
        self.set_stop(not self.get_stop())

    def exec_file(self, fname=None):
        if fname is None:
            fname = self.input_editor.get_fname()
            self.input_editor.save()
            if fname is None:
                return
        if os.path.isfile(fname):
            self.start_func(CodeFile(fname), name='__main__')

    def start_func(self, code, text_beg=None, text_end=None,
                   post_task=None, file=None, name=None):
        """
        启动方程，注意，这个函数的调用不支持多线程（务必再主线程中调用）
        """
        if code is None:  # 清除最后一次调用的信息
            add_exec_history(None)
            return

        if self.is_running():
            play_error()
            return

        add_exec_history(dict(
            code=code, text_beg=text_beg, text_end=text_end,
            post_task=post_task, file=file, name=name))

        if isinstance(code, CodeFile):  # 此时，执行脚本文件
            if not code.exists():
                add_exec_history(None)
                return
            file = code.abs_path()
            code = code.get_text()
            text_beg = f"Start: {file}"
            text_end = 'Done'
            add_code_history(file)  # 记录代码历史
            app_data.log(f'execute file: {file}')  # since 230923

        self.result = None
        self.kernel_err = None

        app_data.space['__file__'] = file if isinstance(file, str) else ''
        app_data.space['__name__'] = name if isinstance(name, str) else ''

        if isinstance(code, str):
            self.thread = ConsoleThread(lambda: exec(code, app_data.space))
        else:
            self.thread = ConsoleThread(code)

        self.thread.post_task = post_task
        self.thread.text_end = text_end
        self.thread.sig_done.connect(self.__kernel_exited)
        self.thread.sig_err.connect(self.__kernel_err)
        priority = load_priority()
        if text_beg is not None:
            print(f'{text_beg} ({priority})')
        self.thread.time_beg = timeit.default_timer()
        self.set_stop(False)
        self.set_pause(False)
        self.thread.start(priority_value(priority))
        self.sig_kernel_started.emit()
        self.sig_refresh.emit()

    def start_last(self):
        last_history = get_last_exec_history()
        if last_history is not None:
            self.start_func(**last_history)

    def __kernel_exited(self):
        if self.thread is not None:
            self.result = self.thread.result  # 首先，要获得结果

            self.set_stop(False)
            self.set_pause(False)

            if self.thread.text_end is not None:
                print(self.thread.text_end)

            time_end = timeit.default_timer()
            if self.thread.time_beg is not None and time_end is not None:
                t = time2str(time_end - self.thread.time_beg)
                print(f'Time used = {t}\n')

            post_task = self.thread.post_task
            self.thread = None  # 到此未知，线程结束

            self.sig_kernel_done.emit()
            self.sig_refresh.emit()

            try:  # 完成了所有的工作，再执行善后
                if callable(post_task):
                    post_task()
            except Exception as err:
                print(err)

    def __kernel_err(self, err):
        self.kernel_err = err
        print(f'Error: {err}')
        self.sig_kernel_err.emit(err)
        try:
            app_data.log(f'meet exception: {err}')
        except Exception as err:
            print(err)

    def kill_thread(self):
        """
        杀死线程；一种非常不安全的一种终止方法
        """
        if self.thread is not None:
            reply = QtWidgets.QMessageBox.question(
                self, '杀死进程',
                "强制结束当前进程，可能会产生不可预期的影响，是否继续?",
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                if self.thread is not None:
                    thread = self.thread
                    thread.sig_done.emit()
                    thread.terminate()

    def writeline(self, text):
        self.output_widget.write(f'{text}\n')

    def restore_code(self):
        try:
            self.input_editor.open(
                os.path.join(os.getcwd(), 'code_in_editor.py'))
        except Exception as err:
            print(err)

    def get_fname(self):
        return self.input_editor.get_fname()

    def is_running(self):
        return self.thread is not None

    def get_break_point(self):
        return self.break_point

    def get_flag_exit(self):
        return self.flag_exit


try:
    from pyqtgraph.console import ConsoleWidget


    class PgConsole(ConsoleWidget):
        def __init__(self, parent=None):
            text = app_data.getenv(
                key='PgConsoleText',
                encoding='utf-8',
                default="""
这是一个交互的Python控制台。请在输入框输入Python命令并开始！

---\n\n""")
            code = app_data.getenv(
                key='PgConsoleInit',
                encoding='utf-8',
                default="from zmlx import *"
            )
            super().__init__(parent, namespace=app_data.space, text=text)
            try:
                exec(code, app_data.space)
            except Exception as err:
                print(err)

except ImportError:
    PgConsole = None
