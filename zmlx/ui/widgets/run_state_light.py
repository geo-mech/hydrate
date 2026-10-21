"""状态栏运行状态灯（RunStateLight）.

::

    |  ● 运行中  |  ○ 空闲  |  ⏸ 已暂停  |        ← 悬停可看提示

一个**圆点 + 文字**的常驻控件，放在状态栏右侧、**「并行」复选框左边**。三种状态：

========================  ============================  ====================
状态                       圆点                           文字
========================  ============================  ====================
空闲（没在跑）             灰色空心点（○）                 「空闲」
运行中                     红色实心点（●）                 「运行中」
已暂停                     橙色暂停点（⏸）                 「已暂停」
========================  ============================  ====================

★ **它是个按钮**（2026-10-26 起）：点击 = ``gui.show_console()``，把右侧栏（控制台）
显示出来 / 切到「控制台」那一页。理由：右侧栏可以被「操作 → 隐藏」收起来，收起后用户
没有明显入口把它叫回来；这个状态灯恰好一直在、又与控制台相关，点它最自然。

为什么要它
----------

在此之前，控制台的运行状态是**借**右上角的 ``VersionButton`` 显示的
（``MainWindow.console_state()`` 往那格写「控制台：运行中」）。于是那一格**一物两用**：
平时显示版本号、跑仿真时变成运行状态 —— 用户看那一格时不知道它此刻代表哪个意思。
本控件把这件事接过来，版本按钮因此**只属于版本号**。

⚠️ 向后兼容：``console_state(text)`` 这个**公开方法**保留、行为不变（仍写版本按钮），
外部脚本 / 历史代码照常可调；只是主窗口自己**不再**调它（见 ``MainWindow.refresh``）。

为什么圆点是**文字**而不是 ``QPixmap``
--------------------------------------

第一版用 ``QLabel.setPixmap()`` + ``setText()``，实测**圆点根本不显示**：Qt 文档写明
``setText()`` 会 ``clearContents()``，也就是**把刚设的 pixmap 清掉**（``isNull()`` 变
True；本机 PyQt6 6.10 实测如此）。先 pixmap 后 text 不行，反过来也不行 —— ``setText``
本身就会清。

所以这里用**字符**画圆点（``●`` / ``○`` / ``⏸``）：一个字、随字体缩放、与文字同基线、
不需要手动管 devicePixelRatio，也不会被 ``setText`` 清掉。
（代价：极少数字体可能缺字形 —— 缺字形时 Qt 会回退到系统字体；Windows / Linux 的常见
界面字体都有这几个字符。）

⚠️⚠️ **2026-10-26：控件由 ``QPushButton`` 改为 ``QToolButton``，并删除全部尺寸策略** ——
不重写 ``sizeHint`` / ``minimumSizeHint``、不写 padding QSS、不手动锁宽高。
``QToolButton`` 默认就紧凑（不会像 ``QPushButton`` 那样在文字两侧各留一大截），
尺寸交给 Qt 按字体算，换高分屏 / 调大字体也不会裁切。

⚠️ ``QToolButton`` 默认会画凸起边框。用户明确说「是否画出凸起边框并不重要」，所以这里
**不** ``setAutoRaise(True)``、也不写 QSS 去压。

颜色
----

**不写死任何色值**（理由同 ``widgets/AGENTS.md`` 的「控件里的颜色：用图标 / 调色板」）：
圆点与文字都用状态栏的调色板前景色，靠**字形**区分（实心 / 空心 / 暂停）。

Created by DeepSeek, 2026-10-26：从 ``VersionButton`` 的「借位显示」里拆出来
Modified by DeepSeek, 2026-10-26: 由 QLabel 改为 QPushButton —— 点击 = 显示控制台（gui.show_console）
Modified by DeepSeek, 2026-10-26: 按文字宽度紧凑显示（PADDING=1，不再留 6/10 px 外边距）
Modified by DeepSeek, 2026-10-26: 改 ``QToolButton``，删除全部尺寸策略（紧凑交给控件默认行为）
"""

from zmlx.ui.pyqt import QtCore, QtWidgets

#: 三种状态的内部名（:meth:`RunStateLight.set_state` 接受它们）
STATE_IDLE = 'idle'
STATE_RUNNING = 'running'
STATE_PAUSED = 'paused'

#: 状态 -> (圆点字形, 文字, 悬停提示)
#: ⚠️ 字形与文字**合成一个字符串**一次性 ``setText``，不要分两次设（见模块文档）。
#: 悬停提示的末尾统一带一句「点击显示控制台」—— 本控件是**按钮**（2026-10-26 起），
#: 点击调用 ``gui.show_console()``（把右侧栏重新显示出来）。
_CLICK_HINT = '（点击显示控制台）'
_STATES = {
    STATE_IDLE: ('○', '空闲', '控制台空闲：当前没有正在执行的任务'),
    STATE_RUNNING: ('●', '运行中',
                    '控制台正在后台线程里执行任务（工具条「停止」可安全终止）'),
    STATE_PAUSED: ('⏸', '已暂停',
                   '控制台已暂停在 gui.break_point() 处（工具条「继续」可恢复）'),
}


class RunStateLight(QtWidgets.QToolButton):
    """状态栏里的「圆点 + 文字」运行状态灯，**可点击**：点它显示控制台.

    Attributes:
        state: 当前状态（``'idle'`` / ``'running'`` / ``'paused'``）。
    """

    def __init__(self, parent=None):
        super(RunStateLight, self).__init__(parent)
        self.state = None
        # ⚠️ **不设任何尺寸策略**（2026-10-26）：QToolButton 默认已经够紧凑，
        #    见模块文档。下面只设与"尺寸"无关的东西。
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        # 状态栏角落不抢键盘焦点
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.clicked.connect(self._on_clicked)
        self.set_state(STATE_IDLE)

    def _on_clicked(self):
        """点击：把右侧栏（控制台）显示出来 —— 等价于 ``gui.show_console()``.

        ⚠️ 走 ``gui`` 命令而不是直接 ``window.show_console()``：状态栏控件不该持有
        主窗口引用；``show_console`` 是 ``MainWindow`` 的公开方法，自动注册成命令。
        ⚠️ 控制台本来就开着时它只是把右侧栏切到「控制台」那一页（``show_console`` →
        ``set_side_tabs_visible(True)``），这也是用户想要的 —— 可能正停在「标签列表」。
        """
        try:
            from zmlx.ui.gui_buffer import gui
            if gui.get_func('show_console') is None:
                print('show_console 命令不可用（gui 尚未接好），无法显示控制台。')
                return
            gui.show_console()
        except Exception as err:
            print(f'Error when show console: {err}')

    def set_state(self, state):
        """设置状态并刷新显示（**主线程调用**；重复设置同一状态什么也不做）.

        Args:
            state: ``'idle'`` / ``'running'`` / ``'paused'``。未知取值按 ``'idle'`` 处理。
        """
        if state not in _STATES:
            state = STATE_IDLE
        if state == self.state:
            return  # 没变就不动，免得每次切标签都重排状态栏
        self.state = state
        dot, text, tooltip = _STATES[state]
        self.setText(f'{dot} {text}')  # ⚠️ 一次设定；不要再单独 setPixmap（会被清）
        self.setToolTip(f'{tooltip}{_CLICK_HINT}')
        # ⚠️ **不调 _fit_width**（2026-10-26 已删）：QToolButton 的 sizeHint 会随文字变，
        #    Qt 自己会重新排；手动锁宽度那套策略已按用户要求去掉。


def test_1():
    """交互式查看：三种状态轮流显示（不启动内核）."""
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(w)
    status_bar = QtWidgets.QStatusBar(w)
    light = RunStateLight(status_bar)
    status_bar.addPermanentWidget(light)
    layout.addWidget(status_bar)
    layout.addWidget(QtWidgets.QLabel(
        '三种状态的文字见状态栏；点它应调用 gui.show_console()（无界面时只打印提示）。'))
    row = QtWidgets.QHBoxLayout()
    for state in (STATE_IDLE, STATE_RUNNING, STATE_PAUSED):
        b = QtWidgets.QPushButton(state)
        b.clicked.connect(lambda _=False, s=state: light.set_state(s))
        row.addWidget(b)
    layout.addLayout(row)
    w.resize(560, 140)
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    test_1()
