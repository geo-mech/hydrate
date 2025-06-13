import os
import sys
from zml import app_data
from zmlx.ui import gui
from zmlx.ui.pyqt import is_pyqt6

if is_pyqt6:
    from PyQt6.QtWidgets import (QApplication, QWidget, QListWidget,
                                 QPushButton,
                                 QVBoxLayout, QHBoxLayout, QListWidgetItem,
                                 QFileDialog,
                                 QAbstractItemView, QMessageBox)
    from PyQt6.QtCore import Qt, QSize
    from PyQt6.QtGui import QFont

    # PyQt6 中的标准常量
    InternalMove = QAbstractItemView.DragDropMode.InternalMove
else:
    from PyQt5.QtWidgets import (QApplication, QWidget, QListWidget,
                                 QPushButton,
                                 QVBoxLayout, QHBoxLayout, QListWidgetItem,
                                 QFileDialog,
                                 QAbstractItemView, QMessageBox)
    from PyQt5.QtCore import Qt, QSize
    from PyQt5.QtGui import QFont

    # PyQt5 中的标准常量（整数值）
    InternalMove = QAbstractItemView.InternalMove


def on_item_double_clicked(item):
    """双击打开文件编辑"""
    file_path = item.text()
    if os.path.isfile(file_path):
        try:
            gui.open_code(file_path)
        except Exception as e:
            print(f"打开文件失败: {str(e)}")
    else:
        print(f"文件不存在: {file_path}")


class SetupFilesEditor(QWidget):
    KEY = 'zml_gui_setup_files'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_files()

    def init_ui(self):
        # 创建列表控件
        self.listWidget = QListWidget()

        # 设置拖拽模式（跨版本兼容的解决方案）
        try:
            self.listWidget.setDragDropMode(InternalMove)
        except Exception as e:
            # 回退机制：如果设置失败，使用整数值
            print(f"设置拖拽模式失败，使用回退方案: {e}")
            self.listWidget.setDragDropMode(4)  # InternalMove的整数值

        self.listWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.listWidget.itemDoubleClicked.connect(on_item_double_clicked)
        self.listWidget.setMinimumHeight(300)

        # 创建按钮
        self.addButton = QPushButton("添加启动文件")
        self.removeButton = QPushButton("移除选中的文件")
        self.upButton = QPushButton("上移")
        self.downButton = QPushButton("下移")
        self.saveButton = QPushButton("保存配置")

        # 按钮布局
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.addButton)
        buttonLayout.addWidget(self.removeButton)
        buttonLayout.addWidget(self.upButton)
        buttonLayout.addWidget(self.downButton)
        buttonLayout.addWidget(self.saveButton)

        # 主布局
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.listWidget)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)

        # 设置窗口属性
        self.setWindowTitle("启动文件编辑器")

        # 连接信号
        self.addButton.clicked.connect(self.add_file)
        self.removeButton.clicked.connect(self.remove_selected)
        self.upButton.clicked.connect(self.move_up)
        self.downButton.clicked.connect(self.move_down)
        self.saveButton.clicked.connect(self.save_files)

    def load_files(self):
        """从环境变量加载启动文件列表"""
        files_data = app_data.getenv(
            key=self.KEY,
            encoding='utf-8',
            default=''
        )
        if files_data:
            files = [f.strip() for f in files_data.split(';') if f.strip()]
            for file_path in files:
                self.add_file_to_list(file_path)

    def save_files(self):
        """保存当前列表到环境变量"""
        file_paths = []
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            file_paths.append(item.text())

        # 将列表转换为分号分隔的字符串
        files_data = ";".join(file_paths)

        app_data.setenv(
            key=self.KEY,
            encoding='utf-8',
            value=files_data
        )

    def add_file(self):
        """添加新的启动文件"""
        file_path, _ = QFileDialog.getOpenFileName(
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
        item = QListWidgetItem(file_path)
        item.setToolTip(file_path)
        item.setFlags(
            item.flags() | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDragEnabled)
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

    def move_up(self):
        """将选中项上移"""
        current_row = self.listWidget.currentRow()
        if current_row > 0:
            current_item = self.listWidget.takeItem(current_row)
            self.listWidget.insertItem(current_row - 1, current_item)
            self.listWidget.setCurrentRow(current_row - 1)
            self.save_files()  # 自动保存
            print("项已上移")

    def move_down(self):
        """将选中项下移"""
        current_row = self.listWidget.currentRow()
        if 0 <= current_row < self.listWidget.count() - 1:
            current_item = self.listWidget.takeItem(current_row)
            self.listWidget.insertItem(current_row + 1, current_item)
            self.listWidget.setCurrentRow(current_row + 1)
            self.save_files()  # 自动保存
            print("项已下移")


def main():
    app = QApplication(sys.argv)
    editor = SetupFilesEditor()
    editor.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()