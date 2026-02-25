import os

from zmlx.ui import setup_files
from zmlx.ui.alg import create_action
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtWidgets


class SetupFileEdit(QtWidgets.QListWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(
            QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
        # 连接拖拽完成信号
        self.model().rowsMoved.connect(self.on_rows_moved)
        for file_path in setup_files.get_files():
            self.add_file_to_list(file_path)

    def contextMenuEvent(self, event):  # 右键菜单
        menu = QtWidgets.QMenu(self)
        menu.addAction(create_action(self, '添加', slot=self.add_file))
        menu.addAction(create_action(self, '忽略', slot=self.remove_selected))
        menu.addAction(create_action(self, '重置', slot=self.reset_files))
        menu.exec(event.globalPos())

    def on_rows_moved(self, parent, start, end, destination, row):
        """
        当拖拽操作完成后触发的槽函数
        """
        print(f"项目从位置 {start} 移动到 {row}")
        self.save_files()  # 自动保存新的顺序

    def reset_files(self):
        while self.count() > 0:
            self.takeItem(0)
        setup_files.set_files([])  # 把额外保存的删除掉
        for file_path in setup_files.get_files(rank_max=1.0e200):
            self.add_file_to_list(file_path)
        self.save_files()  # 自动保存

    def save_files(self):
        """保存当前列表到环境变量"""
        file_paths = []
        for i in range(self.count()):
            file_paths.append(self.item(i).text())
        setup_files.set_files(file_paths)

    def add_file(self):
        """添加新的启动文件"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择Python启动文件",
            "",
            "Python文件 (*.py);;所有文件 (*)"
        )
        if file_path and os.path.isfile(file_path):
            existing_files = [self.item(i).text() for i in
                              range(self.count())]
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
        self.addItem(item)

    def remove_selected(self):
        """移除选中的文件"""
        selected = self.selectedItems()
        if not selected:
            return

        for item in selected:
            self.takeItem(self.row(item))
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
