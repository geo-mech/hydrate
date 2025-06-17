"""
numpy矩阵相关的控件
"""
import sys
import numpy as np
import numpy.typing as npt
from typing import Optional, Tuple, Union

# 根据环境变量判断使用PyQt5还是PyQt6
from zmlx.ui.pyqt import is_pyqt6

if is_pyqt6:
    from PyQt6.QtCore import Qt, QSignalBlocker, pyqtSignal, QFileInfo, QPoint
    from PyQt6.QtWidgets import (
        QApplication,
        QTableWidget,
        QTableWidgetItem,
        QMenu,
        QAbstractItemView,
        QFileDialog,
        QHeaderView,
        QMainWindow
    )
else:
    from PyQt5.QtCore import Qt, QSignalBlocker, pyqtSignal, QFileInfo, QPoint
    from PyQt5.QtWidgets import (
        QApplication,
        QTableWidget,
        QTableWidgetItem,
        QMenu,
        QAbstractItemView,
        QFileDialog,
        QHeaderView,
        QMainWindow
    )


class ArrayEditor(QTableWidget):
    """
    显示和编辑NumPy ndarray的自定义控件

    功能：
    - set_data() 和 get_data() 接口
    - 右键菜单支持导入/导出、行列操作
    - 数据变化信号
    - 支持PyQt5和PyQt6
    """

    # 定义数据变化的信号
    data_changed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectItems)
        self.setSelectionMode(
            QAbstractItemView.SelectionMode.ContiguousSelection)

        # 兼容不同版本的PyQt
        if is_pyqt6:
            header_resize_mode = QHeaderView.ResizeMode.Stretch
            item_flag_editable = Qt.ItemFlag.ItemIsEditable
            context_menu_policy = Qt.ContextMenuPolicy.CustomContextMenu
        else:
            header_resize_mode = QHeaderView.Stretch
            item_flag_editable = Qt.ItemIsEditable
            context_menu_policy = Qt.CustomContextMenu

        self.horizontalHeader().setSectionResizeMode(header_resize_mode)
        self.verticalHeader().setSectionResizeMode(header_resize_mode)
        self.cellChanged.connect(self._handle_data_change)

        # 存储原始数据参考
        self._data: Optional[np.ndarray] = None

        # 设置右键菜单
        self.setContextMenuPolicy(context_menu_policy)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self._item_flag_editable = item_flag_editable

    def set_data(self, data: npt.ArrayLike) -> None:
        """设置numpy数组数据到表格"""
        if data is None:
            return

        data = np.asarray(data)
        if data.ndim == 0:
            data = np.array([data])
        elif data.ndim == 1:
            data = data.reshape(1, -1)
        elif data.ndim > 2:
            # 将多维数组转换为2D表示
            data = data.reshape(-1, np.prod(data.shape[2:]))

        # 阻止更新信号
        with QSignalBlocker(self):
            self.clear()
            rows, cols = data.shape
            self.setRowCount(rows)
            self.setColumnCount(cols)

            # 设置行和列标签
            self.setHorizontalHeaderLabels([f"Col {i}" for i in range(cols)])
            self.setVerticalHeaderLabels([f"Row {i}" for i in range(rows)])

            # 填充数据
            for i in range(rows):
                for j in range(cols):
                    item = QTableWidgetItem(str(data[i, j]))
                    item.setFlags(item.flags() | self._item_flag_editable)
                    self.setItem(i, j, item)

        # 保存原始数据的引用
        self._data = data
        self.data_changed.emit(self._data)

    def get_data(self) -> Optional[np.ndarray]:
        """从表格获取numpy数组数据"""
        if self.rowCount() == 0 or self.columnCount() == 0:
            return None

        data = []
        for i in range(self.rowCount()):
            row = []
            for j in range(self.columnCount()):
                item = self.item(i, j)
                if item is None:
                    row.append(np.nan)
                else:
                    try:
                        value = float(item.text())
                    except ValueError:
                        value = np.nan
                    row.append(value)
            data.append(row)

        return np.array(data)

    def _handle_data_change(self, row: int, col: int) -> None:
        """当单元格数据改变时发出信号"""
        data = self.get_data()
        if data is not None:
            self._data = data
            self.data_changed.emit(data)

    def _show_context_menu(self, position: QPoint) -> None:
        """显示右键菜单"""
        menu = QMenu(self)

        # 导入导出操作
        import_action = menu.addAction("Import from TXT...")
        export_action = menu.addAction("Export to TXT...")
        menu.addSeparator()

        # 行操作
        add_row_action = menu.addAction("Add Row(s)")
        delete_row_action = menu.addAction("Delete Selected Row(s)")
        menu.addSeparator()

        # 列操作
        add_col_action = menu.addAction("Add Column(s)")
        delete_col_action = menu.addAction("Delete Selected Column(s)")

        action = menu.exec(self.mapToGlobal(position))

        if action == import_action:
            self._import_from_txt()
        elif action == export_action:
            self._export_to_txt()
        elif action == add_row_action:
            self._add_rows()
        elif action == delete_row_action:
            self._delete_selected_rows()
        elif action == add_col_action:
            self._add_columns()
        elif action == delete_col_action:
            self._delete_selected_columns()

    def _get_selected_rows(self) -> Tuple[int, int]:
        """获取选中的行范围（起始行，结束行+1）"""
        ranges = self.selectedRanges()
        if not ranges:
            return 0, 0

        top = self.rowCount()
        bottom = 0

        for rng in ranges:
            top = min(top, rng.topRow())
            bottom = max(bottom, rng.bottomRow())

        return top, bottom + 1

    def _get_selected_columns(self) -> Tuple[int, int]:
        """获取选中的列范围（起始列，结束列+1）"""
        ranges = self.selectedRanges()
        if not ranges:
            return 0, 0

        left = self.columnCount()
        right = 0

        for rng in ranges:
            left = min(left, rng.leftColumn())
            right = max(right, rng.rightColumn())

        return left, right + 1

    def _import_from_txt(self) -> None:
        """从文本文件导入数据"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Data", "", "Text Files (*.txt);;All Files (*)"
        )
        if not filename:
            return

        try:
            data = np.loadtxt(filename)
            self.set_data(data)
        except Exception as e:
            # 简单错误处理，实际应用中应该更详细
            print(f"Error loading TXT file: {str(e)}")

    def _export_to_txt(self) -> None:
        """导出数据到文本文件"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Data", "", "Text Files (*.txt);;All Files (*)"
        )
        if not filename:
            return

        # 确保有扩展名
        if not QFileInfo(filename).suffix():
            filename += ".txt"

        data = self.get_data()
        if data is not None:
            try:
                np.savetxt(filename, data)
            except Exception as e:
                print(f"Error saving TXT file: {str(e)}")

    def _add_rows(self) -> None:
        """添加行"""
        start_row, end_row = self._get_selected_rows()
        row_count = self.rowCount()
        insert_count = max(1, end_row - start_row)

        # 更新行数
        self.setRowCount(row_count + insert_count)

        # 在新行填充默认值0
        for i in range(row_count, row_count + insert_count):
            for j in range(self.columnCount()):
                item = QTableWidgetItem("0")
                item.setFlags(item.flags() | self._item_flag_editable)
                self.setItem(i, j, item)

        # 更新行标签
        for i in range(row_count, row_count + insert_count):
            self.setVerticalHeaderItem(i, QTableWidgetItem(f"Row {i}"))

        self.data_changed.emit(self.get_data())

    def _delete_selected_rows(self) -> None:
        """删除选中行"""
        start_row, end_row = self._get_selected_rows()
        if start_row == end_row:
            return  # 没有选中的行

        # 计算要删除的行数
        delete_count = end_row - start_row

        # 从后往前删除
        for i in range(end_row - 1, start_row - 1, -1):
            self.removeRow(i)

        # 更新行标签
        for i in range(start_row, self.rowCount()):
            self.setVerticalHeaderItem(i, QTableWidgetItem(f"Row {i}"))

        self.data_changed.emit(self.get_data())

    def _add_columns(self) -> None:
        """添加列"""
        start_col, end_col = self._get_selected_columns()
        col_count = self.columnCount()
        insert_count = max(1, end_col - start_col)

        # 更新列数
        self.setColumnCount(col_count + insert_count)

        # 在新列填充默认值0
        for i in range(self.rowCount()):
            for j in range(col_count, col_count + insert_count):
                item = QTableWidgetItem("0")
                item.setFlags(item.flags() | self._item_flag_editable)
                self.setItem(i, j, item)

        # 设置新列标头
        for j in range(col_count, col_count + insert_count):
            self.setHorizontalHeaderItem(j, QTableWidgetItem(f"Col {j}"))

        self.data_changed.emit(self.get_data())

    def _delete_selected_columns(self) -> None:
        """删除选中列"""
        start_col, end_col = self._get_selected_columns()
        if start_col == end_col:
            return  # 没有选中的列

        # 计算要删除的列数
        delete_count = end_col - start_col

        # 从后往前删除
        for j in range(end_col - 1, start_col - 1, -1):
            self.removeColumn(j)

        # 更新列标签
        for j in range(start_col, self.columnCount()):
            self.setHorizontalHeaderItem(j, QTableWidgetItem(f"Col {j}"))

        self.data_changed.emit(self.get_data())


if __name__ == "__main__":
    # 测试代码
    app = QApplication(sys.argv)

    # 创建测试数据
    data = np.array([
        [1.0, 2.5, 3.7],
        [4.9, 5.2, 6.8],
        [7.1, 8.3, 9.6]
    ])

    # 创建控件
    table_widget = ArrayEditor()
    table_widget.set_data(data)
    table_widget.data_changed.connect(
        lambda d: print("\nData changed!\nNew data:\n", d))

    table_widget.show()
    sys.exit(app.exec())
