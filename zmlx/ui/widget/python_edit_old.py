import sys

from zmlx.ui.qt import QtCore, QtWidgets
from zmlx.ui.qt import QtGui


def zml_names():
    try:
        space = {}
        exec('from zmlx import *', space)
        return list(set(space.keys()))
    except:
        return []


class PythonHighlighter(QtGui.QSyntaxHighlighter):
    """
    原文链接：https://blog.csdn.net/xiaoyangyang20/article/details/68923133
    """
    Rules = []
    Formats = {}

    def __init__(self, parent=None):
        super(PythonHighlighter, self).__init__(parent)

        self.initialize_formats()

        keywords = ["and", "as", "assert", "break", "class",
                    "continue", "def", "del", "elif", "else", "except",
                    "exec", "finally", "for", "from", "global", "if",
                    "import", "in", "is", "lambda", "not", "or", "pass",
                    "print", "raise", "return", "try", "while", "with",
                    "yield"]
        builtins = ["abs", "all", "any", "basestring", "bool",
                    "callable", "chr", "classmethod", "cmp", "compile",
                    "complex", "delattr", "dict", "dir", "divmod",
                    "enumerate", "eval", "execfile", "exit", "file",
                    "filter", "float", "frozenset", "getattr", "globals",
                    "hasattr", "hex", "id", "int", "isinstance",
                    "issubclass", "iter", "len", "list", "locals", "map",
                    "max", "min", "object", "oct", "open", "ord", "pow",
                    "property", "range", "reduce", "repr", "reversed",
                    "round", "set", "setattr", "slice", "sorted",
                    "staticmethod", "str", "sum", "super", "tuple", "type",
                    "vars", "zip", "zml", "zmlx"] + zml_names()
        constants = ["False", "True", "None", "NotImplemented",
                     "Ellipsis"]

        PythonHighlighter.Rules.append((QtCore.QRegularExpression(
            "|".join([r"\b%s\b" % keyword for keyword in keywords])),
                                        "keyword"))
        PythonHighlighter.Rules.append((QtCore.QRegularExpression(
            "|".join([r"\b%s\b" % builtin for builtin in builtins])),
                                        "builtin"))
        PythonHighlighter.Rules.append((QtCore.QRegularExpression(
            "|".join([r"\b%s\b" % constant
                      for constant in constants])), "constant"))
        PythonHighlighter.Rules.append((QtCore.QRegularExpression(
            r"\b[+-]?[0-9]+[lL]?\b"
            r"|\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b"
            r"|\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b"),
                                        "number"))
        PythonHighlighter.Rules.append((QtCore.QRegularExpression(
            r"\bPyQt4\b|\bQt?[A-Z][a-z]\w+\b"), "pyqt"))
        PythonHighlighter.Rules.append((QtCore.QRegularExpression(r"\b@\w+\b"),
                                        "decorator"))
        string_re = QtCore.QRegularExpression(r"""(?:'[^']*?'|"[^"]*?")""")
        PythonHighlighter.Rules.append((string_re, "string"))
        self.stringRe = QtCore.QRegularExpression(r"""(:?"["].*?"|'''.*?'')""")
        PythonHighlighter.Rules.append((self.stringRe, "string"))
        self.tripleSingleRe = QtCore.QRegularExpression(r"""'''(?!")""")
        self.tripleDoubleRe = QtCore.QRegularExpression(r'''"""(?!')''')

    @staticmethod
    def initialize_formats():
        base_format = QtGui.QTextCharFormat()
        # base_format.setFontFamily("courier")
        # base_format.setFontPointSize(10)
        for name, color in (("normal", QtCore.Qt.GlobalColor.black),
                            ("keyword", QtCore.Qt.GlobalColor.darkBlue),
                            ("builtin", QtCore.Qt.GlobalColor.darkRed),
                            ("constant", QtCore.Qt.GlobalColor.darkGreen),
                            ("decorator", QtCore.Qt.GlobalColor.darkBlue),
                            ("comment", QtCore.Qt.GlobalColor.darkGreen),
                            ("string", QtCore.Qt.GlobalColor.darkYellow),
                            ("number", QtCore.Qt.GlobalColor.darkMagenta),
                            ("error", QtCore.Qt.GlobalColor.darkRed),
                            ("pyqt", QtCore.Qt.GlobalColor.darkCyan)):
            fmt = QtGui.QTextCharFormat(base_format)
            fmt.setForeground(QtGui.QColor(color))
            if name in ("keyword", "decorator"):
                fmt.setFontWeight(QtGui.QFont.Weight.Bold)
            if name == "comment":
                fmt.setFontItalic(True)
            PythonHighlighter.Formats[name] = fmt

    def highlightBlock(self, text):
        try:
            self.__highlight_block(text)
        except Exception as err:
            print(err)

    def __highlight_block(self, text):
        normal, triple_single, triple_double, error = range(4)

        text_length = len(text)
        prev_state = self.previousBlockState()

        self.setFormat(0, text_length,
                       PythonHighlighter.Formats["normal"])

        if text.startswith("Traceback") or text.startswith("Error: "):
            self.setCurrentBlockState(error)
            self.setFormat(0, text_length,
                           PythonHighlighter.Formats["error"])
            return
        if (prev_state == error and
                not (text.startswith(sys.ps1) or text.startswith("#"))):
            self.setCurrentBlockState(error)
            self.setFormat(0, text_length,
                           PythonHighlighter.Formats["error"])
            return

        for regex, fmt in PythonHighlighter.Rules:
            matches = regex.globalMatch(text)
            # 处理匹配项并设置格式
            while matches.hasNext():
                match = matches.next()  # 获取下一个匹配
                start = match.capturedStart(0)  # 获取匹配的起始索引
                length = match.capturedLength(0)  # 获取匹配的长度
                self.setFormat(start, length, PythonHighlighter.Formats[fmt])

        # Slow but good quality highlighting for comments. For more
        # speed, comment this out and add the following to __init__:
        # PythonHighlighter.Rules.append((QtCore.QRegExp(r"#.*"), "comment"))
        if not text:
            pass
        elif text[0] == "#":
            self.setFormat(0, len(text),
                           PythonHighlighter.Formats["comment"])
        else:
            stack = []
            for i, c in enumerate(text):
                if c in ('"', "'"):
                    if stack and stack[-1] == c:
                        stack.pop()
                    else:
                        stack.append(c)
                elif c == "#" and len(stack) == 0:
                    self.setFormat(i, len(text),
                                   PythonHighlighter.Formats["comment"])
                    break

        self.setCurrentBlockState(normal)

        match = self.stringRe.match(text)
        if match.hasMatch():  # 检查是否有匹配
            return

        # This is fooled by triple quotes inside single quoted strings
        for regex, state in ((self.tripleSingleRe, triple_single),
                             (self.tripleDoubleRe, triple_double)):
            match = regex.match(text)  # 使用 match() 方法获取匹配结果
            i = match.capturedStart(0) if match.hasMatch() else -1  # 获取匹配的起始位置

            if self.previousBlockState() == state:
                if i == -1:  # 如果没有匹配，设置 i 为文本长度
                    i = len(text)
                    self.setCurrentBlockState(state)
                self.setFormat(0, i + 3,
                               PythonHighlighter.Formats["string"])  # 设置格式
            elif i > -1:  # 如果找到匹配
                self.setCurrentBlockState(state)
                self.setFormat(i, len(text),
                               PythonHighlighter.Formats["string"])  # 设置格式


class PythonEditOld(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super(PythonEditOld, self).__init__(parent)
        self.__highlighter = PythonHighlighter(self.document())
        # self.setStyleSheet('background-color: white')

    def event(self, event):
        if event.type() == QtCore.QEvent.Type.KeyPress and event.key() == QtCore.Qt.Key.Key_Tab:
            cursor = self.textCursor()
            cursor.insertText("    ")
            return True
        return QtWidgets.QTextEdit.event(self, event)
