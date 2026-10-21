"""状态栏版本按钮（VersionButton）.

::

    |  版本: Oct  8 2026  |                    ← 平时
    |  控制台：运行中         |                 ← 仿真运行时（console_state）
    |  版本: Oct  8 2026（有更新）              ← 服务端报了更新的版本

点击显示「关于」页面。

⚠️ 「有更新」后缀**只加在显示文本里、不写进** :attr:`_version_text`：正文是
:meth:`setText` / :meth:`text` 的契约（外部会拿它比较、拼接），混进后缀会让那些
调用方拿到一个变了样的字符串。见 :meth:`_refresh_text`。

为什么是按钮而不是 ``QLabel``
------------------------------

``Label`` 只认双击，而状态栏这么小的一格「双击」并不好点；按钮单击就响应。
``setFlat(True)`` 之后它长得仍像一行文字，不会在状态栏里冒出一个凸起的方块
（颜色由主题调色板决定，**不写死色值**）。

``setText`` 会被借去显示控制台的运行状态
----------------------------------------

``MainWindow.console_state()`` 用 :meth:`setText` 在这一格显示「控制台：运行中 /
已暂停」，传空串则回退到版本号。这是**历史沿用**的行为（本控件的前身
``SystemStateLabel`` 就这么用），所以 :meth:`setText` / :meth:`text` 保留，
**空串回退**的语义也保留 —— 调用方靠传空串来「清除」。

Created by DeepSeek, 2026-10-08: 从 system_state_label.py 拆出
"""

from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtWidgets

try:
    from zmlx.exts import core
except ImportError:
    core = None

#: 版本号上「有新版本」的提示后缀。
UPDATE_SUFFIX = '（有更新）'


class VersionButton(QtWidgets.QPushButton):
    """状态栏上的版本号按钮：显示内核编译时间，点击打开「关于」页面。

    Attributes:
        default_text: 没有别的文本要显示时回退到的内容（``版本: <编译时间>``）。
    """

    def __init__(self, parent=None):
        super(VersionButton, self).__init__(parent)

        try:
            text = core.time_compile.split(',')[0]
            self.default_text = f'版本: {text}'
        except Exception:
            self.default_text = '版本: ERROR'

        self._has_update = False    # 服务端是否报了更新的版本
        self._version_text = None   # 正文（不含「有更新」后缀）

        # 看起来像一行文字，但仍是真的按钮；颜色交给主题，这里不写死色值
        self.setFlat(True)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)  # 状态栏角落不抢键盘焦点
        self.setAutoDefault(False)  # 免得在对话框里被回车误触发
        self.clicked.connect(lambda: gui.show_about())

        self.setText('')

    # ------------------------------------------------------------------
    # 文本（对外契约，console_state 依赖）
    # ------------------------------------------------------------------

    def setText(self, a0):
        """设置正文；空串时回退到 :attr:`default_text`（内核编译时间）.

        ⚠️ 传进来的只是**正文**：若已知有新版本，显示时会自动补上「有更新」后缀
        （见 :meth:`_refresh_text`）；本方法与 :meth:`text` 都只面对正文本身。
        """
        if a0 is None or len(a0) == 0:
            a0 = self.default_text
        self._version_text = a0
        self._refresh_text()

    def text(self):
        """返回**正文**（不含「有更新」后缀）."""
        if self._version_text is None:
            return QtWidgets.QPushButton.text(self)
        return self._version_text

    def _refresh_text(self):
        """把正文（+ 可选的「有更新」后缀）与悬停提示写到按钮上.

        ⚠️ 后缀**只进显示文本**，见模块文档。
        """
        text = self._version_text or self.default_text
        if self._has_update:
            text = f'{text}{UPDATE_SUFFIX}'
            self.setToolTip('有新版本可用；点击显示程序内核的详细内容（关于）')
        else:
            self.setToolTip('点击显示程序内核的详细内容（关于）')
        QtWidgets.QPushButton.setText(self, text)

    # ------------------------------------------------------------------
    # 「有更新」标记
    # ------------------------------------------------------------------

    def set_has_update(self, value):
        """设置「有新版本」标记并立刻刷新文字（**主线程调用**）.

        由 :class:`~zmlx.ui.widgets.license_button.LicenseButton` 的
        ``sig_update`` 信号驱动（在 ``MainWindow`` 里连接）。

        Args:
            value: True 表示服务端报了比本机更新的版本。
        """
        value = bool(value)
        if value == self._has_update:
            return          # 没变就不动，免得每次都重排状态栏宽度
        self._has_update = value
        self._refresh_text()

    def has_update(self):
        """返回当前是否提示「有更新」."""
        return self._has_update

    def set_status(self, text):
        """设置悬停提示（沿用 ``Label`` 的命名，供旧代码调用）."""
        self.setToolTip(text)


def test_1():
    """交互式查看：几个状态各显示一遍（不联网）."""
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(w)

    status_bar = QtWidgets.QStatusBar(w)
    btn = VersionButton(status_bar)
    status_bar.addPermanentWidget(btn)
    layout.addWidget(status_bar)

    row = QtWidgets.QHBoxLayout()
    for text in ('（默认）', '控制台：运行中', '控制台：已暂停', '很长的临时文本会被截断'):
        b = QtWidgets.QPushButton(text)

        def apply(text=text):
            btn.setText('' if text == '（默认）' else text)

        b.clicked.connect(apply)
        row.addWidget(b)

    b = QtWidgets.QPushButton('切换「有更新」')

    def toggle():
        btn.set_has_update(not btn.has_update())

    b.clicked.connect(toggle)
    row.addWidget(b)
    layout.addLayout(row)

    w.resize(760, 120)
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    test_1()
