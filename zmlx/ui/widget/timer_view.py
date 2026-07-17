import timeit

from zmlx.alg.base import time2str, clamp
from zmlx.exts import make_parent, timer
from zmlx.ui.pyqt import QtCore, QtWidgets


class TimerView(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

        self._sort_col = 0       # 当前排序的列
        self._sort_asc = True    # True=升序，False=降序

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(500)
        self.refresh()

    def _on_header_clicked(self, col):
        """点击列标题时切换排序方式。"""
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc  # 同列 → 切换升降序
        else:
            self._sort_col = col
            self._sort_asc = True  # 换列 → 默认升序
        self.refresh()

    def export_data(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, '导出Timer',
            '',
            f'Text File(*.txt)')
        with open(make_parent(fpath), 'w', encoding='utf-8') as file:
            for key, val in timer.key2nt.items():
                n, t = val
                file.write(f'{key}\t{n}\t{t}\n')

    def refresh(self):
        """
        更新
        """
        if not self.isVisible():
            return

        cpu_t = timeit.default_timer()

        data = []
        for key, nt in timer.key2nt.items():
            n, t = nt
            data.append([f'{key}', n, t, t / n])

        # 按当前排序列排序
        reverse = not self._sort_asc
        data.sort(key=lambda row: row[self._sort_col], reverse=reverse)

        # 格式化显示（排序在原始值上进行，此处转为字符串）
        for row in data:
            row[1] = f'{row[1]}'             # 调用次数
            row[2] = time2str(row[2])        # 总耗时
            row[3] = time2str(row[3])        # 单次耗时

        self.setRowCount(len(data))
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(
            ['名称', '调用次数', '总耗时', '单次耗时'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for i_row in range(len(data)):
            for i_col in range(4):
                self.setItem(
                    i_row, i_col,
                    QtWidgets.QTableWidgetItem(data[i_row][i_col]))

        cpu_t = timeit.default_timer() - cpu_t
        msec = clamp(int(cpu_t * 200 / 0.001), 200, 8000)
        self.timer.setInterval(msec)
