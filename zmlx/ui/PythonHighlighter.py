import sys

from zmlx.ui.Qt import QtCore, QtGui
from zmlx.ui.alg.zml_names import zml_names


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

        PythonHighlighter.Rules.append((QtCore.QRegExp(
            "|".join([r"\b%s\b" % keyword for keyword in keywords])),
                                        "keyword"))
        PythonHighlighter.Rules.append((QtCore.QRegExp(
            "|".join([r"\b%s\b" % builtin for builtin in builtins])),
                                        "builtin"))
        PythonHighlighter.Rules.append((QtCore.QRegExp(
            "|".join([r"\b%s\b" % constant
                      for constant in constants])), "constant"))
        PythonHighlighter.Rules.append((QtCore.QRegExp(
            r"\b[+-]?[0-9]+[lL]?\b"
            r"|\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b"
            r"|\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b"),
                                        "number"))
        PythonHighlighter.Rules.append((QtCore.QRegExp(
            r"\bPyQt4\b|\bQt?[A-Z][a-z]\w+\b"), "pyqt"))
        PythonHighlighter.Rules.append((QtCore.QRegExp(r"\b@\w+\b"),
                                        "decorator"))
        string_re = QtCore.QRegExp(r"""(?:'[^']*'|"[^"]*")""")
        string_re.setMinimal(True)
        PythonHighlighter.Rules.append((string_re, "string"))
        self.stringRe = QtCore.QRegExp(r"""(:?"["]".*"["]"|'''.*''')""")
        self.stringRe.setMinimal(True)
        PythonHighlighter.Rules.append((self.stringRe, "string"))
        self.tripleSingleRe = QtCore.QRegExp(r"""'''(?!")""")
        self.tripleDoubleRe = QtCore.QRegExp(r'''"""(?!')''')

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
                fmt.setFontWeight(QtGui.QFont.Bold)
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
            i = regex.indexIn(text)
            while i >= 0:
                length = regex.matchedLength()
                self.setFormat(i, length,
                               PythonHighlighter.Formats[fmt])
                i = regex.indexIn(text, i + length)

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

        if self.stringRe.indexIn(text) != -1:
            return
        # This is fooled by triple quotes inside single quoted strings
        for i, state in ((self.tripleSingleRe.indexIn(text),
                          triple_single),
                         (self.tripleDoubleRe.indexIn(text),
                          triple_double)):
            if self.previousBlockState() == state:
                if i == -1:
                    i = len(text)
                    self.setCurrentBlockState(state)
                self.setFormat(0, i + 3,
                               PythonHighlighter.Formats["string"])
            elif i > -1:
                self.setCurrentBlockState(state)
                self.setFormat(i, len(text),
                               PythonHighlighter.Formats["string"])
