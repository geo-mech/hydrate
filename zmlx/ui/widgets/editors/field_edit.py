"""单字段编辑器（把一个字段的读写函数绑定成一行控件）.

三个类共用一个协议：构造时传入 ``get_value`` / ``set_value`` 两个回调，控件自己
不持有数据，而是持有**被编辑的模型对象**（``set_data(model)``）。

- 传 ``set_value`` → 可编辑，改动时写回模型并发 ``sig_changed``；
- 不传 ``set_value`` → 只读（仅显示 ``get_value(model)`` 的结果）。

| 类 | 底层 Qt 控件 | 适用字段 |
|---|---|---|
| :class:`TextFieldEdit` | ``QTextEdit`` | 字符串 / 多行文本 |
| :class:`IntFieldEdit` | ``QSpinBox`` | 整数 |
| :class:`FloatFieldEdit` | ``QDoubleSpinBox`` | 浮点数 |

⚠️ **``sig_changed`` 只在「用户改」时发**（2026-10-22 修订，编辑器统一约定）：
``set_data()`` 是「把数据推上控件」，**不得**发出 ``sig_changed``。三个类的 ``set_data``
都用 ``self.blockSignals(True/False)`` 包住 —— 因为 ``setPlainText`` / ``setValue`` 会
触发 ``textChanged`` / ``valueChanged``，而它们接到的 ``on_changed`` 会**写回模型并发信号**。
不屏蔽的话，打开文件 / 刷新一次就等于「把刚读出来的值又写回模型一遍」，外部会误判为脏。

⚠️ **与模型类型无关**（2026-10-22 落实）：控件**真正需要的只是回调** —— ``set_data`` 要
``callable(self.get_value)``，写回要 ``callable(set_value)``（构造时已判）。模型是**任何**
对象都可以，不必是 ``Seepage``。本模块因此是**纯控件**，不 import ``zmlx.exts``。

⚠️ **本模块 2026-10-22 随 ``seepage_edit.py`` 搬进 ``zmlx/scen/editors/``，2026-10-22
又搬回本子包**（``scen/editors`` 整个删除）：它本来就是**纯控件**，与模型类型无关，
放在编辑器子包里才是它的归属。

⚠️ **类名 2026-10-22 改过**：原来叫 ``SeepageTextEdit`` / ``SeepageIntEdit`` /
``SeepageFloatEdit``。去掉「只认 Seepage」的判断后，名字里的 ``Seepage`` 就成了**误导** ——
它们从不要求 Seepage。**旧名仍可用**（本模块末尾的同名别名，访问时发
:class:`DeprecationWarning`，**2027-10-22 删除**）。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-22: 三个类的 ``set_data`` 屏蔽信号（``set_data`` 不发
    ``sig_changed``，也不回写模型）
Modified by DeepSeek, 2026-10-22: 去掉 ``isinstance(self.data, Seepage)``，判据改为
    「回调是否可调」—— 与模型类型无关，也不再 import ``zmlx.exts``
Modified by DeepSeek, 2026-10-22: 改名 ``SeepageTextEdit`` / ``SeepageIntEdit`` /
    ``SeepageFloatEdit`` → ``TextFieldEdit`` / ``IntFieldEdit`` / ``FloatFieldEdit``
    （旧名保留为弃用别名，2027-10-22 删除）
Modified by DeepSeek, 2026-10-22: 随 ``seepage_edit`` 搬进 ``zmlx/scen/editors/``
Modified by DeepSeek, 2026-10-22: ``scen/editors`` 删除，本模块搬回 ``ui/widgets/editors/``
"""

from zmlx.system import warn
from zmlx.ui.pyqt import QtCore, QtWidgets


class TextFieldEdit(QtWidgets.QTextEdit):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, *, get_value=None, set_value=None):
        super().__init__(parent)
        self.data = None
        self.get_value = get_value

        if callable(set_value):
            def on_changed():
                # ``set_value`` 在这里一定可调（构造时判过）；只需防「模型还没设进来」
                if self.data is not None:
                    set_value(self.data, self.toPlainText())
                    self.sig_changed.emit()

            self.textChanged.connect(on_changed)
        else:
            self.setReadOnly(True)

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data
        if not callable(self.get_value):
            return
        # ⚠️ 必须屏蔽信号：``setPlainText`` 会触发 ``textChanged`` → ``on_changed``
        #    → 不仅发 ``sig_changed``，还会把**刚读出来的值再 set_value 写回模型**
        #    （见本模块文档的「只有用户改才发」）。不屏蔽时打开文件/刷新会让模型
        #    被凭空改一次、并被外部当成「用户改过」。
        # ⚠️ 必须 ``try/finally``：``get_value`` 是外部回调，返回值类型不归控件管
        #    （实测传入返回 int 的回调时 ``setPlainText`` 会抛 ``TypeError``）。中途
        #    抛异常而没复位，控件会**永久哑掉** —— 此后用户怎么改都不再发信号。
        self.blockSignals(True)
        try:
            self.setPlainText(self.get_value(self.data))
        finally:
            self.blockSignals(False)


class IntFieldEdit(QtWidgets.QSpinBox):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, *, get_value=None, set_value=None, value_range=None):
        super().__init__(parent)
        self.data = None
        self.get_value = get_value

        if value_range is not None:
            self.setRange(*value_range)
        else:
            self.setRange(-999999999, 999999999)

        if callable(set_value):
            def on_changed():
                if self.data is not None:  # 理由同 TextFieldEdit
                    set_value(self.data, self.value())
                    self.sig_changed.emit()

            self.valueChanged.connect(on_changed)
        else:
            self.setReadOnly(True)

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data
        if not callable(self.get_value):
            return
        # 理由同 TextFieldEdit.set_data（含 try/finally 的必要性）
        self.blockSignals(True)
        try:
            self.setValue(self.get_value(self.data))
        finally:
            self.blockSignals(False)


class FloatFieldEdit(QtWidgets.QDoubleSpinBox):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, *, get_value=None, set_value=None, value_range=None):
        super().__init__(parent)
        self.data = None
        self.get_value = get_value

        if value_range is not None:
            self.setRange(*value_range)
        else:
            self.setRange(-1e20, 1e20)

        if callable(set_value):
            def on_changed():
                if self.data is not None:  # 理由同 TextFieldEdit
                    set_value(self.data, self.value())
                    self.sig_changed.emit()

            self.valueChanged.connect(on_changed)
        else:
            self.setReadOnly(True)

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data
        if not callable(self.get_value):
            return
        # 理由同 TextFieldEdit.set_data（含 try/finally 的必要性）
        self.blockSignals(True)
        try:
            self.setValue(self.get_value(self.data))
        finally:
            self.blockSignals(False)


class _OldNames:
    """旧类名（2026-10-22 改名；2027-10-22 删除）的转发.

    ⚠️ 用模块级 ``__getattr__``（PEP 562）而不是 ``SeepageTextEdit = TextFieldEdit``：
    只在**有人真正取这个名字**时才发警告，``import`` 本模块本身不再多出一条。
    ``__all__`` 里**不列**旧名 —— 它们只是兼容出口，新代码不该用。
    """

    NAMES = {
        'SeepageTextEdit': 'TextFieldEdit',
        'SeepageIntEdit': 'IntFieldEdit',
        'SeepageFloatEdit': 'FloatFieldEdit',
    }


def __getattr__(name):
    """旧名转发 + :class:`DeprecationWarning`（PEP 562）.

    ⚠️ 只对 :data:`_OldNames.NAMES` 里的三个名字生效，**不**兜底任意名字 —— 否则
    ``hasattr(模块, x)`` 会永远为真，掩盖拼写错误。未知名字照常抛 :class:`AttributeError`。
    """
    new_name = _OldNames.NAMES.get(name)
    if new_name is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    warn(
        f'``{__name__}.{name}`` 已改名（2026-10-22）：请改用 ``{new_name}``；'
        '旧名将于 **2027-10-22** 删除。',
        DeprecationWarning,
        stacklevel=2,
    )
    return globals()[new_name]


__all__ = ['TextFieldEdit', 'IntFieldEdit', 'FloatFieldEdit']
