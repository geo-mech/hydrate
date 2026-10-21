"""并行计算开关复选框（CoreParallelEdit）.

Modified by Claude, 2026-08-12
"""

import sys

from zmlx.system import app_data
from zmlx.ui.pyqt import QtWidgets

try:
    from zmlx.exts import core
except ImportError:
    core = None


def _parallel_enabled(value=None):
    """
    设置/检查内核并行是否启用
    """
    key = 'disable_parallel'
    if value is not None:
        if value:
            app_data.setenv(key=key, value='No')
        else:
            app_data.setenv(key=key, value='Yes')
    else:
        value = app_data.getenv(key=key, default='') != 'Yes'
    if core is not None:
        core.parallel_enabled = value
    return value


class CoreParallelEdit(QtWidgets.QCheckBox):
    #: 复选框显示文字。⚠️ 2026-10-26 由「内核并行」简化为「并行」：状态栏那一格到底
    #: 只是在开关**内核**的 for 循环并行，说明写在悬停提示里即可，不必占着状态栏宽度。
    TEXT = '并行'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText(self.TEXT)
        self.setToolTip(
            '在C++层面，是否对for循环进行并行化. 任务比较大的时候，并行有益. '
            '但是，在任务比较小的时候，并行可能会导致性能下降.'
        )
        self.setChecked(_parallel_enabled())
        self.stateChanged.connect(self._changed)

    def _changed(self):
        enabled = self.isChecked()
        _parallel_enabled(enabled)


def test():
    app = QtWidgets.QApplication(sys.argv)
    w = CoreParallelEdit()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test()
