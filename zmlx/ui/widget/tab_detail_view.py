from zmlx.ui.pyqt import QtCore, QtWidgets


class TabDetailView(QtWidgets.QTableWidget):
    class TabWrapper:
        def __init__(self, *tab_widgets):
            self.tab_widgets = tab_widgets

        def count(self):
            return sum([w.count() for w in self.tab_widgets])

        def get(self, index):
            for widget_idx in range(len(self.tab_widgets)):
                widget = self.tab_widgets[widget_idx]
                if index < widget.count():
                    return widget.tabText(index), type(widget.widget(index)).__name__
                else:
                    index -= widget.count()
            return "", ""

        def remove(self, index):
            for widget_idx in range(len(self.tab_widgets)):
                widget = self.tab_widgets[widget_idx]
                if index < widget.count():
                    widget.close_tab(index)
                    break
                else:
                    index -= widget.count()

        def show(self, index):
            for widget_idx in range(len(self.tab_widgets)):
                widget = self.tab_widgets[widget_idx]
                if index < widget.count():
                    if not widget.isVisible():
                        widget.setVisible(True)
                    widget.setCurrentIndex(index)
                    break
                else:
                    index -= widget.count()

    def __init__(self, parent=None, obj=None, header_labels=None):
        super().__init__(parent)
        self.header_labels = header_labels
        self.obj = obj
        self._init_ui()
        self._connect_signals()
        self.refresh()

    def _init_ui(self):
        self.setColumnCount(3)
        if self.header_labels is not None:
            assert len(self.header_labels) == 3
            self.setHorizontalHeaderLabels(
                self.header_labels)
        else:
            self.setHorizontalHeaderLabels(['标题', '类型', '操作'])
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(True)
        self.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu)  # 启用右键菜单

    def _connect_signals(self):
        self.cellClicked.connect(self._on_cell_clicked)
        self.customContextMenuRequested.connect(
            self._show_context_menu)  # 右键菜单信号

    def refresh(self):
        if (not hasattr(self.obj, 'count')
                or not hasattr(self.obj, 'get')
                or not hasattr(self.obj, 'remove')
                or not hasattr(self.obj, 'show')):
            return
        row_count = self.obj.count()
        self.setRowCount(row_count)

        for row in range(row_count):
            value, name = self.obj.get(row)
            # 数值列（直接显示值）
            self.setItem(row, 0, QtWidgets.QTableWidgetItem(str(value)))
            # 类型列（使用type获取类型）
            self.setItem(row, 1, QtWidgets.QTableWidgetItem(name))
            # 删除按钮
            btn = QtWidgets.QToolButton(self)
            btn.setText('x')
            btn.clicked.connect(lambda _, r=row: self._handle_delete(r))
            self.setCellWidget(row, 2, btn)

    def _handle_delete(self, row):
        self.obj.remove(row)
        self.refresh()

    def _on_cell_clicked(self, row, column):
        if column in (0, 1):
            self.obj.show(row)

    def _show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        refresh_action = menu.addAction("刷新表格")
        refresh_action.triggered.connect(self.refresh)
        menu.exec(self.viewport().mapToGlobal(pos))
