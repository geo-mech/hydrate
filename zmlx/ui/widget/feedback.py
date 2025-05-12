import os

from zml import sendmail, app_data
from zmlx.ui.pyqt import is_pyqt6

if is_pyqt6:
    from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                                 QLineEdit, QTextEdit, QPushButton, QMessageBox,
                                 QSizePolicy)
    from PyQt6.QtCore import Qt

    Policy = QSizePolicy.Policy  # PyQt6的特殊处理
else:
    from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                                 QLineEdit, QTextEdit, QPushButton, QMessageBox,
                                 QSizePolicy)
    from PyQt5.QtCore import Qt

    Policy = QSizePolicy  # PyQt5的兼容处理


class FeedbackWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.temp_file = os.path.join(app_data.temp(),
                                      "the_feedback_widget.tmp")
        self.init_ui()
        self.setup_autosave()
        self.load_autosave()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.setWindowTitle("问题反馈")
        # self.setMinimumSize(400, 500)

        # 设置窗口策略（兼容不同版本）
        self.setSizePolicy(
            Policy.Expanding,  # 水平策略
            Policy.Expanding  # 垂直策略
        )

        # 固定高度区域
        fixed_layout = QVBoxLayout()
        fixed_layout.setContentsMargins(0, 0, 0, 0)
        fixed_layout.setSpacing(10)

        # 姓名输入
        lbl_name = QLabel("姓名（最多10个字符）:")
        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(10)
        self.name_edit.setSizePolicy(
            Policy.Expanding,  # 水平策略
            Policy.Fixed  # 垂直策略
        )
        fixed_layout.addWidget(lbl_name)
        fixed_layout.addWidget(self.name_edit)

        # 联系方式输入
        lbl_contact = QLabel("联系方式（电话/邮箱，最多100字符）:")
        self.contact_edit = QLineEdit()
        self.contact_edit.setMaxLength(100)
        self.contact_edit.setSizePolicy(
            Policy.Expanding,  # 水平策略
            Policy.Fixed  # 垂直策略
        )
        fixed_layout.addWidget(lbl_contact)
        fixed_layout.addWidget(self.contact_edit)

        main_layout.addLayout(fixed_layout)

        # 反馈内容区域（自适应高度）
        lbl_feedback = QLabel("反馈内容（最多2000字符）:")
        self.feedback_edit = QTextEdit()
        self.feedback_edit.setSizePolicy(
            Policy.Expanding,  # 水平策略
            Policy.Expanding  # 垂直策略
        )
        self.feedback_edit.setPlaceholderText("请详细描述您遇到的问题或建议")

        # 自适应区域布局
        scroll_layout = QVBoxLayout()
        scroll_layout.setContentsMargins(0, 5, 0, 0)
        scroll_layout.addWidget(lbl_feedback)
        scroll_layout.addWidget(self.feedback_edit, stretch=1)
        main_layout.addLayout(scroll_layout, stretch=1)

        # 提交按钮
        self.submit_btn = QPushButton("提交反馈")
        self.submit_btn.setSizePolicy(
            Policy.Fixed,  # 水平策略
            Policy.Fixed  # 垂直策略
        )
        self.submit_btn.clicked.connect(self.submit_feedback)
        main_layout.addWidget(self.submit_btn,
                              alignment=Qt.AlignmentFlag.AlignRight)

        # 设置布局拉伸比例
        main_layout.setStretch(0, 0)  # 固定区域
        main_layout.setStretch(1, 1)  # 自适应区域
        main_layout.setStretch(2, 0)  # 按钮区域

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
        except Exception as e:
            print(f"自动保存失败: {str(e)}")

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
            except Exception as e:
                print(f"加载自动保存失败: {str(e)}")

    def validate_input(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "输入错误", "姓名不能为空")
            return False
        if not self.contact_edit.text().strip():
            QMessageBox.warning(self, "输入错误", "联系方式不能为空")
            return False
        if len(self.feedback_edit.toPlainText().strip()) < 10:
            QMessageBox.warning(self, "输入错误", "反馈内容至少需要10个字符")
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
            success = sendmail(
                address="zhangzhaobin@mail.iggcas.ac.cn",
                subject=subject,
                text=text,
                name_from="用户反馈系统"
            )

            if success:
                QMessageBox.information(self, "发送成功",
                                        "反馈已成功提交，感谢您的支持！")
                self.name_edit.clear()
                self.contact_edit.clear()
                self.feedback_edit.clear()
                if os.path.exists(self.temp_file):
                    os.remove(self.temp_file)
            else:
                QMessageBox.critical(self, "发送失败",
                                     "邮件发送失败，请检查网络连接")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生未知错误: {str(e)}")


if __name__ == "__main__":
    import sys

    app = QApplication.instance() or QApplication(sys.argv)
    window = FeedbackWidget()
    window.show()

    if is_pyqt6:
        sys.exit(app.exec())
    else:
        sys.exit(app.exec_())
