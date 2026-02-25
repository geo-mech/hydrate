import hashlib
import os
import sys
from datetime import datetime

from zml import app_data, write_text, read_text
from zmlx.alg.fsys import time_string
from zmlx.ui.alg import create_action
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import is_pyqt6, QtCore, QtGui, QtWidgets
from zmlx.ui.settings import get_default_code

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
