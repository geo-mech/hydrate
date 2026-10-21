"""标签页列表管理 widget（查看/删除已打开的标签页）.

本控件是「已打开标签页」的总览：内容随时会被别处改掉（新开 / 关闭 / 重命名标签页），
而主窗口的刷新链到不了它（它开在**右侧**栏，见 :meth:`TabDetailView.showEvent`），
所以**可见时每秒自动刷新一次**（:data:`TabDetailView.REFRESH_INTERVAL_MS`）、
隐藏时停掉。

Modified by Claude, 2026-08-12
"""

from zmlx.ui.pyqt import QtCore, QtWidgets


class TabDetailView(QtWidgets.QTableWidget):
    #: 可见时的自动刷新间隔（毫秒）。1 秒足够「跟得上」，而一次刷新的成本只是
    #: 遍历几个标签（标签数通常个位数），不会成为负担。
    REFRESH_INTERVAL_MS = 1000

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
        #: 定时刷新用的计时器（**只在控件可见时运行**，见 :meth:`showEvent`）
        self._timer = None
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
        # ⚠️ **整张表禁止就地编辑**（这里只是「已打开标签页」的清单，没有可编辑项）。
        #    Qt 的默认触发器是 ``DoubleClicked|EditKeyPressed|AnyKeyPressed``，
        #    于是双击任一单元格会当场弹出**行内编辑器**；而在 WSLg 下，编辑器还
        #    开着时再双击**另一个**单元格会让 Qt 在 C++ 层直接**段错误**
        #    （不是异常，Python 侧兜不住，表现就是「整个软件卡死」）。
        #    这一处比「关于」页更危险：它本来是双击就该「切到那个标签页」的，
        #    双击反而弹出编辑器已经不对，再双击一次就直接崩。
        #    ``setEditTriggers`` 是总闸；:meth:`refresh` 里建单元格时还会清掉
        #    ``ItemIsEditable`` 标志（双保险）。
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

    def _connect_signals(self):
        self.cellClicked.connect(self._on_cell_clicked)
        self.customContextMenuRequested.connect(
            self._show_context_menu)  # 右键菜单信号

    def showEvent(self, event):
        """显示时：立刻刷新一次，并**开始每秒定时刷新**（主线程调用）.

        ⚠️ **为什么要自己定时刷**：主窗口那条刷新链到不了本控件 ——
        ``MainWindow.refresh`` 只刷新 ``get_current_widget()``（**顶部**栏的当前页），
        而本控件是 ``show_tab_details`` 用 ``position="right"`` 开在**右侧**栏的；
        所以切标签页 / 菜单「显示 → 刷新」都不会调到 :meth:`refresh`，
        列表会一直停在打开那一刻的内容（实测：在别处新开标签页，行数纹丝不动）。

        本控件是「已打开标签页」的总览，**内容随时会被别处改掉**，所以用定时器
        每秒对齐一次 —— 比去接各个 ``TabWidget`` 的增删信号简单得多，也不会漏掉
        「重命名 / 换位置」这类不增删的变化。

        ⚠️ **只在可见时跑**（``hideEvent`` 里停）：切走后还在刷就是白烧 CPU，
        而且用户看不见。

        ⚠️ 计时器的 parent 是本控件，所以它随控件一起销毁 —— 不会像线程那样
        在关标签页时把进程带崩（见 ``widget/AGENTS.md`` 的线程生命周期那节）。
        """
        super().showEvent(event)
        self.refresh()
        self._start_timer()

    def hideEvent(self, event):
        """隐藏时停掉定时刷新（控件不可见就没必要刷了）."""
        self._stop_timer()
        super().hideEvent(event)

    def _start_timer(self):
        """开始每秒刷新（重复调用无副作用）"""
        if self._timer is None:
            self._timer = QtCore.QTimer(self)
            self._timer.setInterval(TabDetailView.REFRESH_INTERVAL_MS)
            self._timer.timeout.connect(self.refresh)
        self._timer.start()

    def _stop_timer(self):
        """停止定时刷新（没有计时器时什么都不做）"""
        if self._timer is not None:
            self._timer.stop()

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
            # 数值列（直接显示值）；⚠️ 用只读单元格，见 _init_ui 的说明
            self.setItem(row, 0, self._make_item(str(value)))
            # 类型列（使用type获取类型）
            self.setItem(row, 1, self._make_item(name))
            # 删除按钮
            btn = QtWidgets.QToolButton(self)
            btn.setText('x')
            btn.clicked.connect(lambda _, r=row: self._handle_delete(r))
            self.setCellWidget(row, 2, btn)

    @staticmethod
    def _make_item(text):
        """造一个**只读**单元格（清掉 Qt 默认给的 ``ItemIsEditable`` 标志）.

        ``QTableWidgetItem`` 默认带 ``ItemIsEditable``，这正是「双击单元格会弹出
        编辑器」的直接原因（触发器见 :meth:`_init_ui` 的 ``setEditTriggers``）。
        本表全是只读信息，所以逐项清掉这个标志 —— 与 ``NoEditTriggers`` 互为
        双保险。保留其它标志（可选中 / 启用），只去掉可编辑。

        Args:
            text: 单元格文本。

        Returns:
            QtWidgets.QTableWidgetItem: 只读单元格。
        """
        item = QtWidgets.QTableWidgetItem(text)
        item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        return item

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
