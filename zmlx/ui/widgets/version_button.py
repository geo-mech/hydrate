"""状态栏版本按钮（VersionButton）.

::

    |  版本: 1.9.7              |                ← 平时（zmlx 包版本号）
    |  版本: 1.9.7（有更新）     |                ← 服务端报了更新的版本

    | 控制台：运行中             |                ← console_state 借用（外部脚本仍可写）

点击显示「关于」页面。悬停提示里带着**内核编译时间**（例如 ``Oct 21 2026``）。

⚠️ **2026-10-26：显示内容由「版本: <内核编译时间>」改为「版本: <zmlx 版本号>」** ——
编译时间是**内核 DLL** 的构建时间，普通用户看不出「我现在装的是哪一版」；
``zmlx.__version__`` 才是这个包对外声明的版本号（``projects/zml/AGENTS.md``：
它是 ``pyproject.toml`` 的影子）。**前缀「版本: 」沿用原格式**（用户定的），
中间**没有** 'v'。编译时间没丢：「关于」页的「当前版本」一行仍有它，悬停提示里也写了。

⚠️⚠️ **2026-10-26：控件由 ``QPushButton`` 改为 ``QToolButton``**，并且**去掉了所有
尺寸相关策略**（不重写 ``sizeHint`` / ``minimumSizeHint``、不设 ``setStyleSheet`` 的
padding、不手动锁宽高）—— 由 Qt 自己想多大就多大：

- ``QToolButton`` 默认就是「文字 + 很窄的内边距」，不像 ``QPushButton`` 把文字两侧
  各留一大截空白（实测同样的 ``版本: 1.9.7``：QPushButton 86 px、QToolButton 更窄）；
- 因此原先那一整套紧凑化代码（``PADDING`` / ``V_PADDING`` / ``_fit_width`` /
  ``_hint_height`` / ``sizeHint`` / ``minimumSizeHint`` / padding QSS）**全部删除**；
- 高度也不锁：字体变大 / 换高分屏时由 Qt 按字体算，不会裁切。

⚠️ ``QToolButton`` 默认会画一个**凸起的边框**（状态栏里显眼）。用户明确表示「是否画出
凸起边框并不重要」，所以这里**不** ``setAutoRaise(True)``、也不写 QSS 去压它 ——
保持默认外观。（想要"看起来像一行字"的话，加一句 ``setAutoRaise(True)`` 即可，
不影响任何尺寸逻辑。）

⚠️ **2026-10-26 起本控件只属于版本号**：控制台的「运行中 / 已暂停」改由状态栏的
运行状态灯（:class:`zmlx.ui.widgets.run_state_light.RunStateLight`）显示，主窗口
不再往这一格写状态。⚠️ 但 ``MainWindow.console_state()`` 那个**公开方法**保留、
行为不变（仍写这里），所以 :meth:`setText` 的「外部可写 + 空串回退版本号」契约
也保留 —— 删掉它会让还在调 ``console_state`` 的外部脚本拿到 ``'ERROR'``。

⚠️ 「有更新」后缀**只加在显示文本里、不写进** :attr:`_version_text`：正文是
:meth:`setText` / :meth:`text` 的契约（外部会拿它比较、拼接），混进后缀会让那些
调用方拿到一个变了样的字符串。见 :meth:`_refresh_text`。

``setText`` 为什么还能被外部写（``console_state`` 的历史契约）
--------------------------------------------------------------

``MainWindow.console_state()`` 用 :meth:`setText` 在这一格显示「控制台：运行中 /
已暂停」，传空串则回退到版本号。这是**历史沿用**的行为（本控件的前身
``SystemStateLabel`` 就这么用）—— 主窗口自己已改走运行状态灯，但这条契约
为了兼容外部调用而保留：:meth:`setText` / :meth:`text` 保留，**空串回退**的语义也保留。

Created by DeepSeek, 2026-10-08: 从 system_state_label.py 拆出
Modified by DeepSeek, 2026-10-26: 状态显示职责已移交 ``RunStateLight``，本控件只属于版本号
Modified by DeepSeek, 2026-10-26: 显示文字由「版本: <编译时间>」改为「版本: <zmlx 版本号>」
Modified by DeepSeek, 2026-10-26: 改 ``QToolButton``，删除全部尺寸策略（紧凑交给控件默认行为）
"""

from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtWidgets

try:
    from zmlx.exts import core
except ImportError:
    core = None

#: 版本号上「有新版本」的提示后缀。
UPDATE_SUFFIX = '（有更新）'


class VersionButton(QtWidgets.QToolButton):
    """状态栏上的版本号按钮：显示 **zmlx 包版本号**，点击打开「关于」页面。

    Attributes:
        default_text: 没有别的文本要显示时回退到的内容（``版本: <zmlx.__version__>``）。
    """

    def __init__(self, parent=None):
        super(VersionButton, self).__init__(parent)

        # ⚠️ 2026-10-26：显示文字由「版本: <内核编译时间>」改为「版本: <zmlx 版本号>」
        #    （例如 ``版本: 1.9.7``）。理由：编译时间是**内核 DLL** 的构建时间，普通用户
        #    看不出「我现在装的是哪一版」；而 ``zmlx.__version__`` 正是这个包对外声明的
        #    版本号（见 projects/zml/AGENTS.md：它是 ``pyproject.toml`` 的影子，重启后
        #    一眼能对上）。
        #    ⚠️ 格式**沿用原来的「版本: 」前缀**（用户 2026-10-26 定的）：状态的是一种说法、
        #       版本是另一种，前缀让这一格一眼可辨；去掉了 'v' 前缀（与原格式一致）。
        #    ⚠️ 编译时间**没有丢**：它仍在「关于」页的「当前版本」一行里，悬停提示里也写了。
        try:
            from zmlx import __version__ as pkg_version
            self.version_text = f'版本: {pkg_version}'
        except Exception:
            self.version_text = '版本: ?'
        try:
            # ⚠️ ``split(',')[0]`` 在**空串**上会得到 ``''`` 而不是报错；DLL 没加载成时
            #    ``core.time_compile`` 就是空串，所以「取到了空串」也要当成没有。
            text = str(core.time_compile or '').split(',')[0].strip()
            self.compile_text = text if len(text) > 0 else 'ERROR'
        except Exception:
            self.compile_text = 'ERROR'
        self.default_text = self.version_text

        self._has_update = False    # 服务端是否报了更新的版本
        self._version_text = None   # 正文（不含「有更新」后缀）

        # ⚠️ **不设任何尺寸策略**（2026-10-26）：QToolButton 默认已经够紧凑，
        #    见模块文档。下面只设与"尺寸"无关的东西。
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)  # 状态栏角落不抢键盘焦点
        self.clicked.connect(lambda: gui.show_about())

        self.setText('')

    # ------------------------------------------------------------------
    # 文本（对外契约：MainWindow.console_state 仍在用）
    # ------------------------------------------------------------------

    def text(self):
        """返回**正文**（不含「有更新」后缀）."""
        if self._version_text is None:
            return QtWidgets.QToolButton.text(self)
        return self._version_text

    def setText(self, a0):
        """设置正文；空串时回退到 :attr:`default_text`（``版本: <zmlx 版本号>``）.

        ⚠️ 传进来的只是**正文**：若已知有新版本，显示时会自动补上「有更新」后缀
        （见 :meth:`_refresh_text`）；本方法与 :meth:`text` 都只面对正文本身。
        """
        if a0 is None or len(a0) == 0:
            a0 = self.default_text
        self._version_text = a0
        self._refresh_text()

    def _refresh_text(self):
        """把正文（+ 可选的「有更新」后缀）与悬停提示写到按钮上.

        ⚠️ 后缀**只进显示文本**，见模块文档。
        """
        text = self._version_text or self.default_text
        # ⚠️ 编译时间**可能取不到**（DLL 没加载成，例如单元测试 / 精简环境）—— 那时
        #    ``compile_text`` 是 'ERROR'，提示里就只说版本号，不要写出「编译于 ERROR」。
        if self.compile_text and self.compile_text != 'ERROR':
            tip = f'zmlx {self.version_text}（内核编译于 {self.compile_text}）；' \
                  f'点击显示程序内核的详细内容（关于）'
        else:
            tip = f'zmlx {self.version_text}；点击显示程序内核的详细内容（关于）'
        if self._has_update:
            text = f'{text}{UPDATE_SUFFIX}'
            self.setToolTip(f'有新版本可用；{tip}')
        else:
            self.setToolTip(tip)
        QtWidgets.QToolButton.setText(self, text)

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

    # 直接列出当前会显示什么，方便肉眼确认形如「版本: 1.9.5」
    layout.addWidget(QtWidgets.QLabel(
        f'默认文字：{btn.default_text}　｜　悬停：{btn.toolTip()}\n'
        f'内核编译时间：{btn.compile_text}（只在「关于」页与悬停提示里）'))

    row = QtWidgets.QHBoxLayout()
    for text in ('（默认）', '控制台：运行中', '控制台：已暂停'):
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

    w.resize(760, 150)
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    test_1()
