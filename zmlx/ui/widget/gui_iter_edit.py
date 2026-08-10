"""GuiIterator 显示与编辑控件.

上部: MatplotWidget 显示迭代耗时曲线
下部: 参数编辑 (ratio、清空 history 等)

通过 set_data(iter) 设置要显示/编辑的 GuiIterator 对象，
get_data() 获取当前对象。
"""

from zmlx.ui.pyqt import QtCore, QtWidgets


class GuiIteratorEdit(QtWidgets.QWidget):
    """GuiIterator 可视化面板.

    依赖:
        - zmlx.utility.gui_iterator: GuiIterator, get_gui_iter
        - zmlx.ui.widget.plt: MatplotWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._iter = None
        self._build_ui()
        self.set_data(None)  # 默认使用全局单例

    def set_data(self, data):
        """设置要显示/编辑的 GuiIterator 对象.

        Args:
            data: GuiIterator 实例，None 则使用全局单例 get_gui_iter().
        """
        if data is None:
            from zmlx.utility.gui_iterator import get_gui_iter
            data = get_gui_iter()
        self._iter = data
        self._sync_from_iter()

    def get_data(self):
        """获取当前的 GuiIterator 对象."""
        return self._iter

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── 上部: 耗时曲线图 ──
        from zmlx.ui.widget.plt import MatplotWidget
        self._plt = MatplotWidget()
        layout.addWidget(self._plt, 1)

        # ── 下部: 参数 / 操作（可水平滚动）──
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMaximumHeight(60)

        ctrl = QtWidgets.QWidget()
        ctrl_layout = QtWidgets.QHBoxLayout(ctrl)
        ctrl_layout.setContentsMargins(8, 4, 8, 4)
        ctrl_layout.setSpacing(4)

        ctrl_layout.addWidget(QtWidgets.QLabel('绘图比例:'))

        self._ratio_spin = QtWidgets.QDoubleSpinBox()
        self._ratio_spin.setRange(0.001, 0.3)
        self._ratio_spin.setDecimals(3)
        self._ratio_spin.setSingleStep(0.01)
        self._ratio_spin.setToolTip('GUI 绘图占总时长的比例 (0.001~0.3)')
        self._ratio_spin.valueChanged.connect(self._on_ratio_changed)
        ctrl_layout.addWidget(self._ratio_spin)

        ctrl_layout.addWidget(QtWidgets.QLabel('最大绘图间隔:'))

        self._max_interval_spin = QtWidgets.QSpinBox()
        self._max_interval_spin.setRange(0, 10000)
        self._max_interval_spin.setSpecialValueText('不限制')
        self._max_interval_spin.setToolTip('最大绘图间隔 (step 数)，0 = 不限制')
        self._max_interval_spin.valueChanged.connect(self._on_max_interval_changed)
        ctrl_layout.addWidget(self._max_interval_spin)

        self._btn_clear = QtWidgets.QPushButton('清空历史')
        self._btn_clear.clicked.connect(self._on_clear_history)
        ctrl_layout.addWidget(self._btn_clear)

        self._btn_refresh = QtWidgets.QPushButton('刷新图表')
        self._btn_refresh.clicked.connect(self._on_refresh)
        ctrl_layout.addWidget(self._btn_refresh)

        self._status = QtWidgets.QLabel()
        ctrl_layout.addWidget(self._status)

        ctrl_layout.addStretch()
        scroll.setWidget(ctrl)
        layout.addWidget(scroll)

    def _sync_from_iter(self):
        """将控件值同步到当前 GuiIterator."""
        if self._iter is None:
            return
        self._ratio_spin.blockSignals(True)
        self._ratio_spin.setValue(self._iter.ratio)
        self._ratio_spin.blockSignals(False)
        self._max_interval_spin.blockSignals(True)
        self._max_interval_spin.setValue(
            self._iter.max_plot_interval
            if self._iter.max_plot_interval is not None else 0)
        self._max_interval_spin.blockSignals(False)
        self._update_status()

    def _on_ratio_changed(self, value):
        if self._iter is not None:
            self._iter.ratio = value

    def _on_max_interval_changed(self, value):
        if self._iter is not None:
            self._iter.max_plot_interval = value if value > 0 else None

    def _on_clear_history(self):
        if self._iter is not None:
            self._iter.history.clear()
            self._iter.step = 0
            self._iter.step_last_plot = None
            self._plt.figure.clear()
            self._plt.draw()
            self._update_status()

    def _on_refresh(self):
        if self._iter is not None and len(self._iter.history) >= 2:
            self._plt.plot_on_figure(self._iter.show_timing)

    def _update_status(self):
        if self._iter is None:
            return
        self._status.setText(
            f'Step: {self._iter.step}  |  '
            f'Iter: {self._iter.time_iter:.2f}s  |  '
            f'Plot: {self._iter.time_plot:.2f}s  |  '
            f'History: {len(self._iter.history)}')

    def refresh(self):
        self._sync_from_iter()
        self._on_refresh()

    @staticmethod
    def test():
        import sys
        app = QtWidgets.QApplication(sys.argv)
        w = GuiIteratorEdit()
        w.resize(800, 600)
        w.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    GuiIteratorEdit.test()
