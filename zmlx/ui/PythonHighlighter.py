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

        self.initializeFormats()

        KEYWORDS = ["and", "as", "assert", "break", "class",
                    "continue", "def", "del", "elif", "else", "except",
                    "exec", "finally", "for", "from", "global", "if",
                    "import", "in", "is", "lambda", "not", "or", "pass",
                    "print", "raise", "return", "try", "while", "with",
                    "yield"]
        BUILTINS = ["abs", "all", "any", "basestring", "bool",
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
        CONSTANTS = ["False", "True", "None", "NotImplemented",
                     "Ellipsis"]

        PythonHighlighter.Rules.append((QtCore.QRegExp(
            "|".join([r"\b%s\b" % keyword for keyword in KEYWORDS])),
                                        "keyword"))
        PythonHighlighter.Rules.append((QtCore.QRegExp(
            "|".join([r"\b%s\b" % builtin for builtin in BUILTINS])),
                                        "builtin"))
        PythonHighlighter.Rules.append((QtCore.QRegExp(
            "|".join([r"\b%s\b" % constant
                      for constant in CONSTANTS])), "constant"))
        PythonHighlighter.Rules.append((QtCore.QRegExp(
            r"\b[+-]?[0-9]+[lL]?\b"
            r"|\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b"
            r"|\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b"),
                                        "number"))
        PythonHighlighter.Rules.append((QtCore.QRegExp(
            r"\bPyQt4\b|\bQt?[A-Z][a-z]\w+\b"), "pyqt"))
        PythonHighlighter.Rules.append((QtCore.QRegExp(r"\b@\w+\b"),
                                        "decorator"))
        stringRe = QtCore.QRegExp(r"""(?:'[^']*'|"[^"]*")""")
        stringRe.setMinimal(True)
        PythonHighlighter.Rules.append((stringRe, "string"))
        self.stringRe = QtCore.QRegExp(r"""(:?"["]".*"["]"|'''.*''')""")
        self.stringRe.setMinimal(True)
        PythonHighlighter.Rules.append((self.stringRe, "string"))
        self.tripleSingleRe = QtCore.QRegExp(r"""'''(?!")""")
        self.tripleDoubleRe = QtCore.QRegExp(r'''"""(?!')''')

    @staticmethod
    def initializeFormats():
        baseFormat = QtGui.QTextCharFormat()
        # baseFormat.setFontFamily("courier")
        # baseFormat.setFontPointSize(12)
        for name, color in (("normal", QtCore.Qt.black),
                            ("keyword", QtCore.Qt.darkBlue), ("builtin", QtCore.Qt.darkRed),
                            ("constant", QtCore.Qt.darkGreen),
                            ("decorator", QtCore.Qt.darkBlue), ("comment", QtCore.Qt.darkGreen),
                            ("string", QtCore.Qt.darkYellow), ("number", QtCore.Qt.darkMagenta),
                            ("error", QtCore.Qt.darkRed), ("pyqt", QtCore.Qt.darkCyan)):
            format = QtGui.QTextCharFormat(baseFormat)
            format.setForeground(QtGui.QColor(color))
            if name in ("keyword", "decorator"):
                format.setFontWeight(QtGui.QFont.Bold)
            if name == "comment":
                format.setFontItalic(True)
            PythonHighlighter.Formats[name] = format

    def highlightBlock(self, text):
        try:
            self.__highlightBlock(text)
        except:
            pass

    def __highlightBlock(self, text):
        NORMAL, TRIPLESINGLE, TRIPLEDOUBLE, ERROR = range(4)

        textLength = len(text)
        prevState = self.previousBlockState()

        self.setFormat(0, textLength,
                       PythonHighlighter.Formats["normal"])

        if text.startswith("Traceback") or text.startswith("Error: "):
            self.setCurrentBlockState(ERROR)
            self.setFormat(0, textLength,
                           PythonHighlighter.Formats["error"])
            return
        if (prevState == ERROR and
                not (text.startswith(sys.ps1) or text.startswith("#"))):
            self.setCurrentBlockState(ERROR)
            self.setFormat(0, textLength,
                           PythonHighlighter.Formats["error"])
            return

        for regex, format in PythonHighlighter.Rules:
            i = regex.indexIn(text)
            while i >= 0:
                length = regex.matchedLength()
                self.setFormat(i, length,
                               PythonHighlighter.Formats[format])
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

        self.setCurrentBlockState(NORMAL)

        if self.stringRe.indexIn(text) != -1:
            return
        # This is fooled by triple quotes inside single quoted strings
        for i, state in ((self.tripleSingleRe.indexIn(text),
                          TRIPLESINGLE),
                         (self.tripleDoubleRe.indexIn(text),
                          TRIPLEDOUBLE)):
            if self.previousBlockState() == state:
                if i == -1:
                    i = text.length()
                    self.setCurrentBlockState(state)
                self.setFormat(0, i + 3,
                               PythonHighlighter.Formats["string"])
            elif i > -1:
                self.setCurrentBlockState(state)
                self.setFormat(i, text.length(),
                               PythonHighlighter.Formats["string"])
