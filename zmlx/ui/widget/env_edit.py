"""环境变量编辑器。

以表单形式展示 zml_env_items.json 中定义的所有配置项，
根据值的类型自动选择最合适的控件：
- Yes/No 选项 → 复选框 (QCheckBox)
- 枚举选项 → 下拉框 (QComboBox)
- 数值配置 → 数字输入 (QSpinBox)
- 自由文本 → 文本框 (QLineEdit)
"""
from zmlx.system import app_data
from zmlx.ui.pyqt import QtCore, QtWidgets


class EnvEdit(QtWidgets.QScrollArea):
    """环境变量编辑器。

    在 QScrollArea 中以垂直表单布局展示所有配置项，
    每行包含：标签 (QFrame) + 输入控件 + 备注说明。
    """

    def __init__(self, parent=None, items=None):
        super().__init__(parent)
        self.env_items = items
        self._widgets = []  # [(key, widget, load_fn, save_fn)]

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 容器
        container = QtWidgets.QWidget()
        self._layout = QtWidgets.QVBoxLayout(container)
        self._layout.setContentsMargins(12, 8, 12, 8)
        self._layout.setSpacing(4)
        self.setWidget(container)

        self._build_ui()

    def _build_ui(self):
        """根据 env_items 构建表单。"""
        if not self.env_items:
            return

        for item in self.env_items:
            label = item.get('label', '')
            key = item.get('key', '')
            options = item.get('items')
            note = item.get('note', '')

            if not key:
                continue

            row = QtWidgets.QFrame()
            row_layout = QtWidgets.QHBoxLayout(row)
            row_layout.setContentsMargins(4, 2, 4, 2)

            # ---- 标签 ----
            lbl = QtWidgets.QLabel(label)
            lbl.setMinimumWidth(120)
            lbl.setMaximumWidth(200)
            lbl.setAlignment(
                QtCore.Qt.AlignmentFlag.AlignRight |
                QtCore.Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(lbl)

            # ---- 输入控件 ----
            widget = self._create_widget(key, options)
            row_layout.addWidget(widget, stretch=1)

            # ---- 备注 ----
            if note:
                note_lbl = QtWidgets.QLabel(note)
                note_lbl.setWordWrap(True)
                note_lbl.setMinimumWidth(150)
                note_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
                row_layout.addWidget(note_lbl, stretch=2)

            self._layout.addWidget(row)

            # 分隔线
            sep = QtWidgets.QFrame()
            sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
            sep.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
            self._layout.addWidget(sep)

        # 底部弹簧
        self._layout.addStretch()

    def _create_widget(self, key, options):
        """根据配置类型创建最合适的输入控件。"""
        is_bool = options and set(o for o in options if o) == {'Yes', 'No'}

        if is_bool:
            return _CheckBox(key)
        elif options:
            return _ComboBox(key, options)
        elif key and ('dpi' in key.lower()):
            return _SpinBoxDPI(key)
        else:
            return _LineEdit(key)


# ============================================================
# 控件实现
# ============================================================

class _BaseWidget:
    """所有配置控件的基类（mixin 模式用于类型标注）。"""
    pass


class _LineEdit(QtWidgets.QLineEdit, _BaseWidget):
    """自由文本输入。"""

    def __init__(self, key):
        super().__init__()
        self._key = key
        self.editingFinished.connect(self._save)
        self._load()

    def _load(self):
        self.setText(
            app_data.getenv(self._key, encoding='utf-8', default=''))

    def _save(self):
        app_data.setenv(key=self._key, value=self.text(), encoding='utf-8')


class _ComboBox(QtWidgets.QComboBox, _BaseWidget):
    """枚举选项下拉框。"""

    def __init__(self, key, items):
        super().__init__()
        self._key = key
        self.addItems(items)
        self.currentTextChanged.connect(self._save)
        self._load()

    def _load(self):
        val = app_data.getenv(self._key, encoding='utf-8', default='')
        if val:
            self.setCurrentText(val)

    def _save(self):
        app_data.setenv(key=self._key, value=self.currentText(),
                        encoding='utf-8')


class _CheckBox(QtWidgets.QCheckBox, _BaseWidget):
    """布尔开关（Yes/No 选项自动转换为复选框）。"""

    def __init__(self, key):
        super().__init__()
        self._key = key
        self.toggled.connect(self._save)
        self._load()

    def _load(self):
        val = app_data.getenv(self._key, encoding='utf-8', default='')
        self.setChecked(val == 'Yes')

    def _save(self):
        app_data.setenv(key=self._key,
                        value='Yes' if self.isChecked() else 'No',
                        encoding='utf-8')


class _SpinBoxDPI(QtWidgets.QSpinBox, _BaseWidget):
    """数值配置（DPI 等），自动关联 yes/no 选项。"""

    def __init__(self, key, min_val=30, max_val=1200, step=10):
        super().__init__()
        self._key = key
        self.setRange(min_val, max_val)
        self.setSingleStep(step)
        self.setSuffix(' dpi')
        self.valueChanged.connect(self._save)
        self._load()

    def _load(self):
        val = app_data.getenv(self._key, encoding='utf-8', default='')
        try:
            self.setValue(int(val))
        except (ValueError, TypeError):
            self.setValue(300)

    def _save(self):
        app_data.setenv(key=self._key, value=str(self.value()),
                        encoding='utf-8')


# ============================================================
# 测试
# ============================================================

def test_1():
    import sys
    from zmlx.ui import settings
    app = QtWidgets.QApplication(sys.argv)
    w = EnvEdit(items=settings.get_env_items())
    w.resize(750, 550)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test_1()
