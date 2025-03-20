from zmlx.ui.Qt import is_PyQt6, is_PyQt5

if is_PyQt6:
    from PyQt6.Qsci import QsciScintilla, QsciLexerPython
    from PyQt6.QtGui import QColor, QPalette
    from PyQt6.QtWidgets import QApplication
else:
    from PyQt5.Qsci import QsciScintilla, QsciLexerPython
    from PyQt5.QtGui import QColor, QPalette
    from PyQt5.QtWidgets import QApplication


class PythonEditor(QsciScintilla):
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
        self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
        self.setAutoCompletionThreshold(2)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionReplaceWord(True)

        # 行号设置
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "0000")
        # self.setMarginsForegroundColor(QColor("#888888"))

        # 括号匹配
        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)

        # 初始化颜色主题
        self._update_theme()

        # 自动检测主题变化
        self.app_palette = QApplication.palette()
        if is_PyQt5:
            QApplication.instance().paletteChanged.connect(self._on_palette_changed)
        else:
            QApplication.instance().paletteChanged.connect(self._on_palette_changed)

    def _is_dark_theme(self):
        # 通过背景色亮度判断是否为暗色主题
        bg_color = self.palette().color(QPalette.ColorRole.Window)
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
        margin_bg = QColor("#F0F0F0")  # 稍亮的背景
        margin_fg = QColor("#606060")  # 深灰色文字

        self.setMarginsBackgroundColor(margin_bg)
        self.setMarginsForegroundColor(margin_fg)

        # 亮色主题颜色配置
        paper = QColor("#FFFFFF")
        text = QColor("#000000")
        caret = QColor("#000000")
        selection = QColor("#C0C0C0")

        # 设置基础颜色
        self.setCaretForegroundColor(caret)
        self.setSelectionBackgroundColor(selection)
        self.setPaper(paper)
        self.setColor(text)

        # 设置语法高亮颜色
        self.lexer.setDefaultPaper(paper)
        self.lexer.setDefaultColor(text)
        self.lexer.setColor(QColor("#008000"), QsciLexerPython.Comment)
        self.lexer.setColor(QColor("#FF0000"), QsciLexerPython.SingleQuotedString)
        self.lexer.setColor(QColor("#FF0000"), QsciLexerPython.DoubleQuotedString)
        self.lexer.setColor(QColor("#0000FF"), QsciLexerPython.Keyword)
        self.lexer.setColor(QColor("#FF00FF"), QsciLexerPython.ClassName)
        self.lexer.setColor(QColor("#FF8000"), QsciLexerPython.FunctionMethodName)

        # 设置边线颜色
        self.setEdgeColor(QColor("#E0E0E0"))

        # 当前行高亮
        self.setCaretLineBackgroundColor(QColor("#F0F0F0"))

    def _setup_dark_theme(self):
        # 暗色主题行号设置
        margin_bg = QColor("#202020")  # 比编辑器背景更深的颜色
        margin_fg = QColor("#A0A0A0")  # 浅灰色文字

        self.setMarginsBackgroundColor(margin_bg)
        self.setMarginsForegroundColor(margin_fg)

        # 暗色主题颜色配置
        paper = QColor("#2D2D2D")
        text = QColor("#E0E0E0")
        caret = QColor("#E0E0E0")
        selection = QColor("#404040")

        # 设置基础颜色
        self.setCaretForegroundColor(caret)
        self.setSelectionBackgroundColor(selection)
        self.setPaper(paper)
        self.setColor(text)

        # 设置语法高亮颜色
        self.lexer.setDefaultPaper(paper)
        self.lexer.setDefaultColor(text)
        self.lexer.setColor(QColor("#608060"), QsciLexerPython.Comment)
        self.lexer.setColor(QColor("#FF8080"), QsciLexerPython.SingleQuotedString)
        self.lexer.setColor(QColor("#FF8080"), QsciLexerPython.DoubleQuotedString)
        self.lexer.setColor(QColor("#CC99FF"), QsciLexerPython.Keyword)
        self.lexer.setColor(QColor("#99CCFF"), QsciLexerPython.ClassName)
        self.lexer.setColor(QColor("#FFCC66"), QsciLexerPython.FunctionMethodName)

        # 设置边线颜色
        self.setEdgeColor(QColor("#505050"))

        # 当前行高亮
        self.setCaretLineBackgroundColor(QColor("#3D3D3D"))


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = PythonEditor()
    window.show()
    sys.exit(app.exec())
