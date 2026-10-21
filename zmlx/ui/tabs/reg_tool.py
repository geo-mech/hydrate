"""许可登录工具 widget（旧的 USB 序列号 + 授权码方式，已不再挂到界面上）.

2026-09-24 起，界面上的登录入口（帮助菜单 / 关于对话框 / ReadMe 右键菜单）一律
打开 :class:`zmlx.ui.setups.license_register.LicenseRegister`（联网登录：邮箱收
验证码、再把本机硬件码登记到该邮箱）。本模块保留的原因只有一个：
``zmlx.exts.reg`` 仍在，需要「离线授权码」那条老路时可以直接 import 使用。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-09-24
"""

from zmlx.ui.pyqt import QtWidgets


class RegTool(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel(self)
        label.setText('第1步，请将以下硬件码发给作者: ')
        layout.addWidget(label)

        output = QtWidgets.QTextBrowser(self)
        try:
            from zmlx.exts import reg
            output.setPlainText(reg())
        except Exception as err:
            output.setPlainText(f"Error (RegTool.__init__): {err}")
        layout.addWidget(output)

        label = QtWidgets.QLabel(self)
        label.setText('第2步，请将作者返回的登录码粘贴到下面: ')
        layout.addWidget(label)

        self.code = QtWidgets.QTextEdit(self)
        layout.addWidget(self.code)

        button = QtWidgets.QPushButton(self)
        button.setText('第3步，点击此按钮完成登录')
        button.clicked.connect(self.apply_reg)
        layout.addWidget(button)

    def apply_reg(self):
        text = self.code.toPlainText()
        if len(text) > 0:
            try:
                from zmlx.exts import reg
                code = reg(text)
                print(code)
            except Exception as err:
                print(f"Error (RegTool.apply_reg): {err}")
        else:
            QtWidgets.QMessageBox.information(
                self,
                '提示', '请输入激活码后再试')
