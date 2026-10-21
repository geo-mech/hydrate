"""单浮点数编辑器（滑块 ``Slider`` / 拨盘 ``Dial``）.

两者都实现了编辑器的标准协议：``set_data(value)`` 把浮点数推上控件、``get_data()``
取回当前值，改动时发 ``sig_changed``。与 :mod:`field_edit` 的区别：

- ``field_edit`` 的类**绑定模型的某个字段**（构造时给 ``get_value`` / ``set_value`` 回调）；
- 这里的类**自己持有那个值**，任何模块都能直接拿来编辑一个独立的浮点数。

⚠️ 类名 ``Slider`` / ``Dial`` 很通用，本子包已经是它们的唯一实现处。

Modified by Claude, 2026-08-12
"""

from zmlx.ui.pyqt import QtWidgets, QtCore


class Slider(QtWidgets.QWidget):
    """
    使用滑块来编辑浮点数
    """
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, name='', unit='', val_range=None, value=None):
        """
        初始化滑块编辑浮点数的控件

        Args:
            parent: 父控件
            name: 名称
            unit: 单位
            val_range: 范围
            value: 初始值
        """
        super().__init__(parent)
        self._name = name
        self._unit = unit

        # ⚠️ 先就地归一化：set_val_range() 只在自己内部把 None 换成默认值，
        #    改动不会传回这里，所以下面的 val_range[0] 仍会下标到 None。
        if val_range is None:
            val_range = [0.0, 1.0]

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._label = QtWidgets.QLabel()
        self._label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self._label)

        self._slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._slider.setTickPosition(
            QtWidgets.QSlider.TickPosition.TicksBelow)
        self._scale = 1.0
        self.set_val_range(val_range)
        main_layout.addWidget(self._slider)
        self._slider.valueChanged.connect(self._on_value_changed)

        self.set_data(val_range[0] if value is None else value)

    def set_val_range(self, val_range):
        if val_range is None:
            val_range = [0.0, 1.0]
        self._scale = 200.0 / (val_range[1] - val_range[0])
        self._slider.setRange(
            int(val_range[0] * self._scale),
            int(val_range[1] * self._scale)
        )
        self._slider.setTickInterval(
            int((val_range[1] - val_range[0]) * self._scale / 10)
        )
        self.set_data(self.get_data())

    def set_name(self, name):
        self._name = name
        self._update_label()

    def set_unit(self, unit):
        self._unit = unit
        self._update_label()

    def _on_value_changed(self):
        """
        当滑块值改变时，更新标签和发射信号
        """
        self._update_label()
        self.sig_changed.emit()

    def _update_label(self):
        """
        更新标签显示当前值
        """
        self._label.setText(f"{self._name}: {self.get_data():.2f} {self._unit}")

    def set_data(self, value):
        """
        设置当前值

        Args:
            value: 新值
        """
        # ⚠️ try/finally 不可省：``int(value * self._scale)`` 在 value 为 None / 字符串
        #    时会抛 TypeError，中途不复位 ``blockSignals`` 会让滑块**永久哑掉**
        #    （用户此后拖动都不再发 sig_changed）。
        self._slider.blockSignals(True)
        try:
            self._slider.setValue(int(value * self._scale))
            self._update_label()
        finally:
            self._slider.blockSignals(False)

    def get_data(self):
        """
        获取当前值

        Returns:
            当前值
        """
        return self._slider.value() / self._scale


def test_slider():
    """
    测试滑块编辑浮点数的控件
    """
    import sys
    app = QtWidgets.QApplication(sys.argv)
    view = Slider(name='Test', unit='m', val_range=[0.0, 1.0])

    def show():
        print(view.get_data())

    view.sig_changed.connect(show)
    view.show()
    sys.exit(app.exec())


class Dial(QtWidgets.QWidget):
    """
    使用拨盘来编辑浮点数
    """
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, name='', unit='', val_range=None,
                 value=None, wrapping=None, offset=0.0):
        """
        初始化拨盘编辑浮点数的控件

        Args:
            parent: 父控件
            name: 名称
            unit: 单位
            val_range: 范围
            value: 初始值
            wrapping: 是否循环
            offset: 偏移量
        """
        super().__init__(parent)
        self._name = name
        self._unit = unit
        # ⚠️ 归一化必须在这一行**之前**：原先把 `if val_range is None` 写在下面
        #    （第 146 行），而这里已经用 val_range[1] 算了 _scale —— 那句判断
        #    永远到不了，调用方按签名默认值构造 Dial() 会直接 TypeError。
        if val_range is None:
            val_range = [0.0, 1.0]
        self._scale = 360.0 / (val_range[1] - val_range[0])

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._label = QtWidgets.QLabel()
        self._label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self._label)

        self._range = val_range  # 允许的值的范围
        self._dial = QtWidgets.QDial()
        self._dial.setRange(
            int(val_range[0] * self._scale),
            int(val_range[1] * self._scale))
        self._dial.setNotchesVisible(True)
        if wrapping is not None:
            self._dial.setWrapping(wrapping)
            self._offset = offset if wrapping else 0.0
        else:
            self._offset = 0.0

        main_layout.addWidget(self._dial)
        self._dial.valueChanged.connect(lambda: [
            self._update_label(),
            self.sig_changed.emit(),
        ])
        if value is not None:
            self.set_data(value)
        else:
            self.set_data(val_range[0])

    def _update_label(self):
        """
        更新标签显示当前值
        """
        self._label.setText(f"{self._name}: {self.get_data():.2f} {self._unit}")

    def set_data(self, value):
        """
        设置当前值

        Args:
            value: 新值
        """
        if self._dial.wrapping():
            value = (value - self._offset - self._range[0]) % (self._range[1] - self._range[0]) + self._range[0]
        else:
            value -= self._offset
            if value > self._range[1]:
                value = self._range[1]
            if value < self._range[0]:
                value = self._range[0]
        # ⚠️ try/finally 不可省：理由同 Slider.set_data —— 中途抛异常会把拨盘永久哑掉。
        self._dial.blockSignals(True)
        try:
            self._dial.setValue(int(value * self._scale))
            self._update_label()
        finally:
            self._dial.blockSignals(False)

    def get_data(self):
        """
        获取当前值

        Returns:
            当前值
        """
        value = self._dial.value() / self._scale + self._offset
        if self._dial.wrapping():
            while value > self._range[1]:
                value -= (self._range[1] - self._range[0])
            while value < self._range[0]:
                value += (self._range[1] - self._range[0])
        else:
            if value > self._range[1]:
                value = self._range[1]
            if value < self._range[0]:
                value = self._range[0]
        return value


def test_dial():
    """
    测试拨盘编辑浮点数的控件
    """
    import sys
    app = QtWidgets.QApplication(sys.argv)
    view = Dial(name='Test', unit='m', val_range=[-20, 20], value=0, offset=20, wrapping=True)

    def show():
        print(view.get_data())

    view.sig_changed.connect(show)
    view.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    test_slider()
