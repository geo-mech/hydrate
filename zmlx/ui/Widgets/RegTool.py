from zml import reg
from zmlx.ui.Qt import QtWidgets


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
        if len(text) > 10:
            try:
                code = reg(text)
                print(code)
            except:
                pass
        else:
            QtWidgets.QMessageBox.information(self,
                                              '提示', '请输入激活码后再试')

    @staticmethod
    def get_start_code():
        return """gui.trigger('reg')"""


if __name__ == '__main__':
    from zmlx.ui.alg.show_widget import show_widget

    show_widget(RegTool, use_gui=True)
