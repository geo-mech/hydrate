"""由「自持值编辑器」生成「引用模型编辑器」的通用包装器.

**设计动机**：本子包的编辑器只有两种语义（见 ``AGENTS.md`` §1）——

| 形态 | ``get_data()`` 返回 | 值在哪 |
|---|---|---|
| 自持值 | 数据本身 | 控件自己 |
| 引用模型 | 模型引用 | 被编辑的模型上（经 ``get_value`` / ``set_value`` 中转） |

两者差别**只在于「值从哪来、到哪去」**，中转逻辑是通用的。于是「引用模型编辑器」= 
**自持值编辑器 + 一层中转**，这层中转由 :class:`ObjectEdit` 承担，不必每加一种字段类型
就从头写一个类。

用法::

    from zmlx.ui.widgets.editors import IntSpin, ObjectEdit

    # 一个「把 model.n 当作整数编辑」的控件
    edit = ObjectEdit(IntSpin(),
                      get_value=lambda m: m.n,
                      set_value=lambda m, v: setattr(m, 'n', v))
    edit.set_data(model)        # 内部: inner.set_data(model.n)

**为什么不用「裸 Qt 控件」**：``QSpinBox`` / ``QTextEdit`` 本身**不是**编辑器（没有
``set_data`` / ``get_data``），不能直接包。所以本模块同时提供三个**自持值叶子**：
:class:`TextInput` / :class:`IntSpin` / :class:`FloatSpin` —— 每个都只是给对应 Qt 控件补上
编辑器协议，各约 10 行。⚠️ 与 ``text_edit.TextEdit`` 的区别：``TextEdit`` 是**多行**纯文本
编辑器（``QTextEdit``），``TextInput`` 是**单行**输入框（``QLineEdit``）。

⚠️ **约定与全子包一致**：

- ``sig_changed`` 只在**用户改**时发；``set_data()`` **不发**（§4.1a）；
- 用户改动时**先写回模型再 emit**，所以监听者读到的是新值；
- 包装器持有的是**模型**，``get_data()`` 返回**模型引用**；
- 没给 ``set_value`` ⇒ 只读（照 ``field_edit`` 的老规矩）。

⚠️ **本模块是新增能力**：``field_edit.py`` 里那三个手写类（``TextFieldEdit`` /
``IntFieldEdit`` / ``FloatFieldEdit``）**保持不变** —— 它们是 ``QTextEdit`` 等的子类，
外部可能 ``isinstance`` / 直接调 ``setRange()``。要迁移时再单独评估。

Created by DeepSeek, 2026-10-22
"""

from zmlx.ui.pyqt import QtCore, QtWidgets


class TextInput(QtWidgets.QLineEdit):
    """单行文本的**自持值**编辑器（``QLineEdit`` + 编辑器协议）."""
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.textChanged.connect(self.sig_changed.emit)

    def set_data(self, data):
        # ⚠️ 必须屏蔽 + try/finally：setText 会触发 textChanged → sig_changed。
        #    不屏蔽则「程序灌值」也被当成「用户改」；不复位则控件永久哑掉（§4.1a）。
        self.blockSignals(True)
        try:
            self.setText('' if data is None else str(data))
        finally:
            self.blockSignals(False)

    def get_data(self):
        return self.text()


class IntSpin(QtWidgets.QSpinBox):
    """整数的**自持值**编辑器（``QSpinBox`` + 编辑器协议）."""
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, *, value_range=None):
        super().__init__(parent)
        if value_range is not None:
            self.setRange(*value_range)
        else:
            self.setRange(-999999999, 999999999)
        self.valueChanged.connect(self.sig_changed.emit)

    def set_data(self, data):
        # 理由同 TextInput.set_data（§4.1a）
        self.blockSignals(True)
        try:
            self.setValue(0 if data is None else int(data))
        finally:
            self.blockSignals(False)

    def get_data(self):
        return self.value()


class FloatSpin(QtWidgets.QDoubleSpinBox):
    """浮点数的**自持值**编辑器（``QDoubleSpinBox`` + 编辑器协议）."""
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, *, value_range=None):
        super().__init__(parent)
        if value_range is not None:
            self.setRange(*value_range)
        else:
            self.setRange(-1e20, 1e20)
        self.valueChanged.connect(self.sig_changed.emit)

    def set_data(self, data):
        # 理由同 TextInput.set_data（§4.1a）
        self.blockSignals(True)
        try:
            self.setValue(0.0 if data is None else float(data))
        finally:
            self.blockSignals(False)

    def get_data(self):
        return self.value()


class ObjectEdit(QtWidgets.QWidget):
    """把一个**自持值编辑器**包成**引用模型编辑器**.

    Args:
        inner: 内层编辑器（任何实现了 ``set_data`` / ``get_data`` 的控件）。
            ⚠️ 它必须是**编辑器**，不是裸 Qt 控件 —— ``QSpinBox`` 之类没有
            ``set_data`` / ``get_data``，请用本模块的 :class:`IntSpin` 等叶子。
        get_value: ``get_value(model) -> 值``，从模型取出要显示的值。**必需**。
        set_value: ``set_value(model, 值)``，把用户改的值写回模型。
            给 ``None`` ⇒ **只读**（仅显示，用户不能改）。
        parent: 父控件。

    ⚠️ ``inner`` 的父控件会被设为**本控件** —— 传进来的那个对象会被 ``setParent`` 收编，
    不要再把它 ``addWidget`` 到别处。
    """

    sig_changed = QtCore.pyqtSignal()

    def __init__(self, inner, *, get_value, set_value=None, parent=None):
        super().__init__(parent)
        if not (hasattr(inner, 'set_data') and hasattr(inner, 'get_data')):
            raise ValueError(
                f'inner 必须是编辑器（要有 set_data / get_data），'
                f'实际是 {type(inner).__name__}。裸 Qt 控件请用本模块的 IntSpin / FloatSpin 等。')

        self.inner = inner
        self.data = None
        self.get_value = get_value
        self.set_value = set_value

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(inner)

        if hasattr(inner, 'sig_changed'):
            inner.sig_changed.connect(self._on_value_changed)

        if not callable(set_value):
            # 只读：内层编辑器仍可显示，但不能让用户改
            for meth in ('setReadOnly',):
                if hasattr(inner, meth):
                    getattr(inner, meth)(True)

    def _on_value_changed(self):
        """内层编辑器报告「用户改了」→ 写回模型，再向上发信号."""
        if self.data is None or not callable(self.set_value):
            return
        # ⚠️ 先写回、再 emit：监听者拿到信号时，模型里已经是新值（与 field_edit 一致）
        self.set_value(self.data, self.inner.get_data())
        self.sig_changed.emit()

    def set_data(self, data):
        """把**模型**灌进控件（内部只读 ``get_value(model)``，不写回、不发信号）."""
        self.data = data
        if not callable(self.get_value):
            return
        if data is None:
            return
        self.inner.set_data(self.get_value(data))

    def get_data(self):
        """返回**模型引用**（不是数据）—— 这正是「引用模型型」的定义."""
        return self.data
