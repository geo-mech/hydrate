"""Demo 浏览器控件。

在 GUI 中以表格形式展示所有 demo 文件，四列布局：
- 第 0 列：文件路径（点击打开编辑）
- 第 1 列：`# ** desc =` 描述文字（点击运行）
- 第 2 列：`# ** author =` 作者
- 第 3 列：运行按钮（点击在控制台执行 demo）

表格布局特性：
- 列宽：第 0 列自适应内容（不超过总宽 50%），第 1 列填充剩余
- 行高：根据描述文字长度自动换行撑高，确保内容完整显示
- 窗口缩放时自动重算列宽约束
"""
import os

from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets


class HtmlDelegate(QtWidgets.QStyledItemDelegate):
    """HTML 渲染委托 — 在 QTableWidget 单元格中渲染 HTML 文本."""

    def paint(self, painter, option, index):
        opt = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        painter.save()
        doc = QtGui.QTextDocument()
        doc.setHtml(opt.text)
        opt.text = ''
        style = opt.widget.style() if opt.widget else QtWidgets.QApplication.style()
        style.drawControl(QtWidgets.QStyle.ControlElement.CE_ItemViewItem, opt, painter)

        painter.translate(opt.rect.left(), opt.rect.top())
        doc.drawContents(painter)
        painter.restore()

    def sizeHint(self, option, index):
        doc = QtGui.QTextDocument()
        doc.setHtml(index.data())
        doc.setTextWidth(option.rect.width() if option.rect.width() > 0 else 400)
        return QtCore.QSize(int(doc.idealWidth()), int(doc.size().height()))


class DemoView(QtWidgets.QTableWidget):
    """Demo 浏览器表格。

    数据来源：zmlx.demo.list_demo_files()，每行包含 [相对路径, 描述, 作者, 绝对路径]。
    四列布局：文件名 | 描述 | 作者 | 运行按钮。
    """

    def __init__(self, parent=None):
        super(DemoView, self).__init__(parent)
        self.__data = []
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setWordWrap(True)
        self.clicked.connect(self.item_clicked)
        self.setItemDelegateForColumn(1, HtmlDelegate(self))
        self.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self._sort_order = {}  # {col: ascending}
        self.refresh()

    def refresh(self):
        from zmlx.alg import code_config
        from zmlx.demo import list_demo_files, get_path
        folder = get_path()
        self.__data = []
        for path, desc in list_demo_files():
            cfg = code_config(path=path, encoding='utf-8')
            author = cfg.get('author', '')
            highlight = cfg.get('highlight', False)
            self.__data.append([os.path.relpath(path, folder), desc, author, path, highlight])

        if len(self.__data) == 0:
            self.clear()
            return

        self._apply_sort()

        self.setRowCount(len(self.__data))
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(['项目 (点击打开)', '说明 (点击运行)', '作者', ''])

        hdr = self.horizontalHeader()
        hdr.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(3, 50)

        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for row_id in range(len(self.__data)):
            try:
                name, desc, author, path, highlight = self.__data[row_id]
                item0 = QtWidgets.QTableWidgetItem(name)
                item1 = QtWidgets.QTableWidgetItem(desc)
                item2 = QtWidgets.QTableWidgetItem(author)
                if highlight:
                    color = QtGui.QColor(200, 50, 50) if highlight is True else QtGui.QColor(highlight)
                    item0.setForeground(color)
                self.setItem(row_id, 0, item0)
                self.setItem(row_id, 1, item1)
                self.setItem(row_id, 2, item2)

                # 运行按钮（仅 .py/.pyw 文件）
                ext = os.path.splitext(path)[-1].lower()
                if ext in ('.py', '.pyw'):
                    btn = QtWidgets.QPushButton('运行')
                    fpath = path
                    btn.clicked.connect(
                        lambda checked, p=fpath: gui.exec_file(p))
                    self.setCellWidget(row_id, 3, btn)
            except Exception as err:
                print(err)
                for col_id in range(3):
                    self.setItem(row_id, col_id, QtWidgets.QTableWidgetItem(''))

        self._constrain_col0()

    def _on_header_clicked(self, col):
        """点击列标题: 切换升序/降序并重建表格."""
        self._sort_order[col] = not self._sort_order.get(col, True)
        self.refresh()

    def _apply_sort(self):
        """按 _sort_order 对 __data 排序."""
        if not self._sort_order:
            return
        for col, asc in reversed(list(self._sort_order.items())):
            self.__data.sort(key=lambda x: x[col], reverse=not asc)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._constrain_col0()

    def _constrain_col0(self):
        self.resizeColumnToContents(0)
        max_w = max(self.viewport().width() // 2, 60)
        if self.columnWidth(0) > max_w:
            self.setColumnWidth(0, max_w)

    def item_clicked(self, index):
        """点击第 0 列打开文件，第 1 列运行 demo。"""
        row_id = index.row()
        col = index.column()
        if row_id >= len(self.__data) or col >= 3:
            return

        try:
            name, desc, author, path, highlight = self.__data[row_id]
            if col == 1 and os.path.isfile(path):
                gui.exec_file(path)
            elif os.path.isfile(path):
                gui.open_code(path)
            elif os.path.isdir(path):
                from zmlx.alg import startfile
                startfile(path)
        except Exception as err:
            print(err)


def test_1():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = DemoView()
    w.resize(800, 600)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test_1()
