import sys

from zmlx.exts import app_data, core
from zmlx.ui.pyqt import QtWidgets


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
    core.parallel_enabled = value
    return value


class CoreParallelEdit(QtWidgets.QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("内核并行")
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
