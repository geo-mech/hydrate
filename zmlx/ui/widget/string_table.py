import math

from zmlx.ui.pyqt import QtWidgets, QtCore


class StringTable(QtWidgets.QTableWidget):
    def __init__(self, parent=None, data_columns=3):
        """
        创建字符串列表表格控件

        Args:
            parent: 父控件
            data_columns: 数据列数 (默认3列)
        """
        super().__init__(parent)
        # 保存列数参数
        self.data_columns = max(1, data_columns)  # 确保至少1列
        self.setColumnCount(1 + self.data_columns)  # 序号列 + 数据列
        self.setHorizontalHeaderLabels(
            ['序号'] + [f'数据 {i + 1}' for i in range(self.data_columns)])

        # 设置列宽：序号列尽可能窄
        self.horizontalHeader().setSectionResizeMode(0,
                                                     QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(0, 40)  # 40像素宽度的序号列
        for i in range(1, self.columnCount()):
            self.horizontalHeader().setSectionResizeMode(i,
                                                         QtWidgets.QHeaderView.ResizeMode.Stretch)

        # 表格样式设置
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)

    def set_data(self, data):
        """设置要显示的数据

        Args:
            data (list): 字符串列表
        """
        # 计算需要多少行（ceil(数据个数/列数)）
        row_count = math.ceil(len(data) / self.data_columns) if data else 0
        self.setRowCount(row_count)

        # 清除现有数据
        self.clearContents()

        # 填充表格
        for i in range(len(data)):
            row = i // self.data_columns
            col = (i % self.data_columns) + 1  # 数据列从第2列开始（0列是序号）

            # 序号列（0列）
            if self.item(row, 0) is None:
                index_item = QtWidgets.QTableWidgetItem(
                    str(row * self.data_columns + 1))
                index_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.setItem(row, 0, index_item)

            # 数据列
            data_item = QtWidgets.QTableWidgetItem(data[i])
            self.setItem(row, col, data_item)

        # 为空白单元格添加占位符保持表格整洁
        if row_count > 0:
            for row in range(row_count):
                # 处理第一列（序号）
                if self.item(row, 0) is None:
                    index = row * self.data_columns + 1
                    index_item = QtWidgets.QTableWidgetItem(str(index))
                    index_item.setTextAlignment(
                        QtCore.Qt.AlignmentFlag.AlignCenter)
                    self.setItem(row, 0, index_item)

                # 处理数据列
                for col in range(1, self.columnCount()):
                    if self.item(row, col) is None:
                        empty_item = QtWidgets.QTableWidgetItem("")
                        self.setItem(row, col, empty_item)
