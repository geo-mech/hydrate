"""zmlx GUI 主窗口与应用程序启动。

``MainWindow`` 是整个 GUI 的主窗口类（菜单、工具栏、标签页管理、文件处理）。
``execute()`` 是应用程序入口：创建 QApplication、启动 Console 内核线程、
恢复上次会话的标签页布局。

Modified by DeepSeek, 2026-09-14
Modified by DeepSeek, 2026-09-24
Modified by DeepSeek, 2026-10-07: 新增样式表 API（set/get_style_sheet）与「设置 → 样式表」
Modified by DeepSeek, 2026-10-07: write() 的状态栏提示过滤 ANSI 转义码（控制台已支持颜色）
Modified by DeepSeek, 2026-10-07: sys.stderr 包装成 _RedStderr（异常钩子也改走 stderr），并补齐 encoding/fileno/isatty

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

import datetime
import io
import os
import sys
from typing import List, Optional, Tuple, Union

from zmlx.algs.fsys import has_permission, samefile, time_string
from zmlx.exts import contain_chinese, core, get_dir, lic
from zmlx.system import app_data, get_hash, log, warn
from zmlx.ui import settings
from zmlx.ui.alg import (
    add_exec_history,
    clear_exec_history,
    get_last_exec_history,
    set_position,
    set_shape,
)
from zmlx.ui.console import Console
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import (
    QAction,
    QtCore,
    QtGui,
    QtMultimedia,
    QtWidgets,
    QWebEngineView,
    is_pyqt6,
)
from zmlx.ui.utils import FileHandler, GuiApi, TaskProc
from zmlx.ui.widgets import CodeEdit, OutputWidget, TabWidget
from zmlx.ui.widgets._parallel import CoreParallelEdit
from zmlx.ui.widgets.license_button import LicenseButton
from zmlx.ui.widgets.run_state_light import (
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RUNNING,
    RunStateLight,
)
from zmlx.ui.widgets.version_button import VersionButton


class Action(QAction):
    """可更新视图的 QAction（支持动态 enabled / visible / text / slot）。

    ★ 2026-10-26 新增 ``slot_func``：点击时执行的动作**不再是直接连上去的槽**，
    而是先存进这个属性、再由 :meth:`_on_triggered` 转发。

    为什么这样做（方案见 ``add_action``）：``overwrite=True`` 撞名时是**就地覆盖**
    同一个 action，如果每次注册都 ``triggered.connect(新槽)``，旧槽并不会自动消失 ——
    实测 Qt 允许重复连接，且 ``disconnect()`` 不带参数断不干净，于是一次点击会依次
    跑完**所有**历史槽（占位函数 + 插件函数 + …）。而“只连一次 + 换属性”从结构上
    根除了这个问题：无论覆盖多少次，``triggered`` 永远只有一条连接，执行时读到的
    永远是最新的那个槽。
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.is_enabled = None  # 检查是否是可执行的
        self.is_visible = None  # 检查是否是可见的
        self.get_text = None
        self.slot_func = None  # 点击时执行的槽（覆盖注册时直接替换）
        self.triggered.connect(self._on_triggered)  # 整个生命周期只连这一次

    def _on_triggered(self):
        """``triggered`` 的唯一入口：转发到当前的 :attr:`slot_func`."""
        if callable(self.slot_func):
            self.slot_func()

    def update_view(self):
        """
        更新视图
        """
        is_enabled = bool(self.is_enabled()) if callable(self.is_enabled) else True
        is_visible = (
            bool(self.is_visible()) if callable(self.is_visible) else is_enabled
        )
        self.setEnabled(is_enabled)
        self.setVisible(is_visible)
        if callable(self.get_text):
            text = self.get_text()
            if isinstance(text, str):
                self.setText(text)


class MainWindow(QtWidgets.QMainWindow):
    """zmlx 主窗口。

    管理标签页容器（TabWidget）、控制台（Console）、菜单栏、工具栏、
    状态栏和文件处理器（FileHandler）。是 GUI 应用的核心窗口类。
    """

    sig_cwd_changed = QtCore.pyqtSignal(str)
    sig_do_task = QtCore.pyqtSignal()
    sig_play_sound = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(settings.load_icon("app"))
        self.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.task_proc = TaskProc(self)

        self.file_handler = FileHandler(self)

        def _do_nothing(fname):
            pass

        def new_empty_file(fname):
            from zmlx.system import make_parent

            with open(make_parent(fname), "w") as file:
                pass

        for opt in [
            {
                "desc": "Python文件",
                "exts": [".py"],
                "func": {"open_file": self.open_code, "new_file": _do_nothing},
            },
            {
                "desc": "文本文件",
                "exts": [".txt", ".json", ".xml", ".qss"],
                "func": {"open_file": self.open_text, "new_file": new_empty_file},
            },
            # ⚠️ 「二维裂缝」(.fn2) 2026-10-22 **已移出**：它指向的 ``show_fn2`` 连同
            #    ``Fn2Widget`` 控件都搬进了插件 ``plugins/builtin/fn2_view.py``，
            #    ``.fn2`` 文件类型由那个插件自己注册（默认启用，所以「文件 → 打开」
            #    照常能选到 .fn2）。
            # ⚠️ 「图片」走 ``self.open_image``：它是**底层能力**（欢迎页在构造期就要用），
            #    2026-10-22 曾短暂搬进插件，同日还原 —— 文件类型不必随插件开关。
            {"desc": "图片", "exts": [".png", ".jpg"], "func": self.open_image},
            # ⚠️ 「PDF文件」(.pdf) 2026-10-22 **已移除**：它指向的 ``open_pdf`` 需要可选库
            #    ``QWebEngineView``，不该常驻在骨架里。``.pdf`` 因此不再有专门的处理器 ——
            #    「文件 → 打开」选到 .pdf 时会走 ``FileHandler.show_info``（显示文件信息），
            #    而不是报错。
        ]:
            self.add_file_handler(**opt)

        self.console = Console(self)

        widget = QtWidgets.QWidget(self)
        h_layout = QtWidgets.QVBoxLayout(widget)
        splitter = QtWidgets.QSplitter(widget)
        splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        # ⚠️ 分隔条要**可拖**：右侧栏（控制台）的宽度由用户决定，不能是固定比例。
        #    ``setStretchFactor`` 只决定「窗口缩放时谁跟着长」——左边（顶部标签页）拿走
        #    全部增量，右边保持用户拖出来的宽度。⚠️ 拉伸因子 (1, 0) 相当于「右侧栏不参与
        #    伸缩」，但**不是**「右侧栏不可调」；真正的可调性看 ``setChildrenCollapsible``
        #    与 ``setHandleWidth``。默认值已经很合适，这里只把「能不能拖没」说清楚。
        splitter.setChildrenCollapsible(True)
        #: 左侧（顶部标签页）与右侧（控制台那一栏）之间的分隔条。
        #: ⚠️ 2026-10-26 起它成了**公开属性** ``self.splitter``：宽度要存盘 / 恢复
        #: （``settings.save_console_width`` / ``load_console_width``），而那两个函数
        #: 要拿到它。原先它是个局部变量。
        self.splitter = splitter
        #: 右侧栏「上次可见时」的宽度（像素）。隐藏时 ``splitter.sizes()`` 里那一项是 0，
        #: 用它保住用户拖出来的宽度；``resizeEvent`` 里更新、关窗时存盘时一并写入。
        self._last_console_width = None

        # 顶部标签页
        self.top_tabs = TabWidget(splitter)
        self.top_tabs.currentChanged.connect(self.refresh)

        # 右侧标签页
        self.right_tabs = TabWidget(splitter)
        self.right_tabs.currentChanged.connect(self.refresh)

        self.gui_api = GuiApi(
            widget, self.console.get_break_point(), self.console.get_flag_exit()
        )

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        h_layout.addWidget(splitter)
        self.setCentralWidget(widget)
        self.title = None
        self.__init_gui_api()  # 在成员声明了之后，第一时间初始化API
        self.__init_actions()

        # 右侧栏的初始宽度（**必须在布局就位之后设**，否则 ``setSizes`` 会被随后的
        # 布局计算覆盖掉）：窗口宽度的 ~22%（``settings.DEFAULT_CONSOLE_RATIO``，
        # 2026-10-26 由 30% 调窄），夹在 [MIN_CONSOLE_WIDTH, MAX_CONSOLE_RATIO] 之间；
        # 有上次存的宽度就用那个。
        self.init_splitter_sizes()

        # 设置标签的形状和位置
        set_position(self.top_tabs)
        set_shape(self.top_tabs)

        set_shape(self.right_tabs)
        self.right_tabs.setTabPosition(QtWidgets.QTabWidget.TabPosition.East)

        # 连接信号
        self.sig_cwd_changed.connect(self.refresh)
        # ⚠️ 「工作路径变了就刷新浏览页」原来直接连 ``self.view_cwd``，但那个方法
        #    2026-10-22 已搬进插件 ``plugins/builtin/viewers.py``。这里改成**按命令名**调
        #    ``gui.view_cwd``（插件注册的命令）—— 插件被禁用 / 未装时命令不存在，
        #    安静跳过，不会让界面启动就崩。
        self.sig_cwd_changed.connect(self.__refresh_cwd_view_if_any)

        self.console.sig_refresh.connect(self.refresh)
        # ---- 状态栏右侧的四个常驻控件（按添加顺序从左到右）----
        # 「运行状态灯」：圆点 + 文字，显示控制台正在空闲 / 运行 / 暂停。
        # ⚠️ 2026-10-26 新加：这个位置原先由**版本按钮借用**（``console_state`` 往那格写
        #    「控制台：运行中」），一物两用 —— 用户看那格时不知道它此刻代表版本还是状态。
        #    现在拆开：状态归本控件，版本按钮**只属于版本号**。
        self.run_state_light = RunStateLight(self)
        self.statusBar().addPermanentWidget(self.run_state_light)

        # 「并行」开关：它是**全局**的运行期开关（存 app_data 的 disable_parallel，
        # 并写 core.parallel_enabled），所以放在状态栏这个「全局且常驻」的位置。
        # ⚠️ 2026-10-26：显示文字由「内核并行」改为「并行」（更短，状态栏不挤）；
        #    它管的仍是**内核**里的 for 循环并行，说明留在 CoreParallelEdit 的 tooltip 里。
        #
        # ⚠️ **原先它挂在控制台的输出面板里**（``OutputWidget``），而那个面板可以不开 /
        #    被收起 —— 开关就跟着看不见了；而「大任务开并行、小任务关掉」是随时可能想
        #    改的事（见 CoreParallelEdit 的 tooltip）。
        self.parallel_edit = CoreParallelEdit(self)
        self.statusBar().addPermanentWidget(self.parallel_edit)

        # 版本号（点击 → 「关于」）。⚠️ 2026-10-26 起**只属于版本号**：
        # 控制台运行状态改由上面的 ``run_state_light`` 显示。
        self.version_button = VersionButton(self)
        self.statusBar().addPermanentWidget(self.version_button)

        # 授权状态（点击 → 注册页面）。首次显示时自己起后台线程查一次。
        self.license_button = LicenseButton(self)
        self.statusBar().addPermanentWidget(self.license_button)

        # ---- 尺寸策略：**一处也不设**（2026-10-26 按用户要求删掉）----
        # 这三个按钮 2026-10-26 起都是 ``QToolButton``（原来是 ``QPushButton``）：
        # QToolButton 默认就紧凑（不会像 QPushButton 那样在文字两侧各留一大截），
        # 所以之前那些「重写 sizeHint / padding QSS / 手动锁宽高 / 统一最小高度」
        # 全部取消 —— 尺寸完全交给 Qt 按字体算，换高分屏 / 调大字体也不会裁切。
        #
        # ⚠️ 曾经在这里做过 ``setMinimumHeight(基准)`` 之类的高度对齐（先试 ``setFixedHeight``，
        #    发现换字体后会被裁切，改成只设下限）。已一并删除：用户明确要求"去除掉尺寸
        #    相关的策略"。若将来又发现几个控件高低不齐，**先查是不是有人给某个控件写了
        #    自定义 sizeHint / QSS**，而不是在这里加补偿代码。

        # 授权查询的答复里带着「最新版本」时，让版本按钮补上「（有更新）」后缀。
        # ⚠️ 这是两个**兄弟控件**之间的值传递，用 Qt 信号连接即可（在装配时就连好、
        #    且发送方本来就在主线程）；**不要**为此注册一个 gui 函数 —— ``gui.xxx``
        #    是「向主窗口要能力」的通道，为一次性转发往全局命令表里加名字并不合适。
        self.license_button.sig_update.connect(self.version_button.set_has_update)

        # 初始为None，当首次调用get_output_widget的时候，创建控件
        self.__output_widget = None

        # 用以播放声音
        if QtMultimedia is not None:
            self.sound = QtMultimedia.QSoundEffect()
        else:
            self.sound = None

        def play(name):
            if self.sound is not None:
                self.sound.setSource(QtCore.QUrl.fromLocalFile(name))
                self.sound.play()

        self.sig_play_sound.connect(play)

        # ⚠️ 「启动即打开欢迎页」那一段已于 2026-10-28 **删除**：它一直在找 ``welcome``
        #    图标（``settings.find_icon_file("welcome")``），而 ``zml_icons/`` 里**从来
        #    没有**这个文件，git 历史里也查不到它曾经存在过 —— 于是 ``if`` 分支永久不执行。
        #    它留下的那条理由（「``open_image`` 必须是底层方法、不能做成插件」）仍然成立，
        #    已写进 :meth:`open_image` 的 docstring。要恢复欢迎页，请先真的往
        #    ``zmlx/ui/data/zml_icons/`` 放一张 ``welcome.png``，再在这里重新加回调用。

        # ⚠️ 启动时**不再**做「本机 USB 授权」的检查（用户 2026-10-05 要求）：
        #    新的 web 授权（web_license / 状态栏右下角）已经取代它，而这一项
        #    在有效期不是远期时会去取网络时间，失败即判过期、还会弹一句红字
        #    「此电脑未授权」—— 对已用 web 授权注册的用户纯属误报。
        #    :meth:`check_license` 已随之**弃用**（见它的 docstring），且不再有
        #    任何自动触发点（原先的启动检查与「关于」页面里的调用都已移除）。

        self.refresh()

    # ── 文本流协议 ──
    # 本窗口被当作 ``sys.stdout`` / ``sys.stderr`` 使用（见 __on_init），所以除了 write /
    # flush，还要补齐下面这几个成员：缺了它们，第三方库里的 ``sys.stdout.encoding`` 之类
    # 就是 AttributeError。⚠️ 方法（fileno / isatty）会被 :meth:`list_member_functions`
    # 自动注册进 GUI API（``gui.fileno()``）——协议要求名字照旧，删不掉，但都无害；
    # ``encoding`` 是普通属性，不会被注册。

    #: 对外**声称**的编码。控件内部是 Unicode，写进来的 str 不会被真正编码；声明 utf-8
    #: 是给库里的 `getattr(stream, 'encoding', None)` 用的（否则它们会退回系统编码 GBK）。
    encoding = "utf-8"

    def write(self, text):
        # ⚠️ **整段都必须投递到 GUI 线程**：本方法被设为 ``sys.stdout``，而用户脚本
        #    是在 ``ConsoleThread`` 里 exec 的，于是每一次 ``print`` 都会**在内核
        #    线程**里走到这里。Qt 的控件只能在 GUI 线程碰 —— 哪怕只是读一下
        #    ``isVisible()``、或者调 ``statusBar().showMessage()`` 都不行（前者是
        #    只读但同属控件访问，后者还会触发重绘，从别的线程发起属未定义行为）。
        #    原先只有第一句在 ``add_task`` 里、后面两句是直接执行的，属跨线程访问
        #    控件；这里把整段收进同一个投递任务。
        self.add_task(lambda: self._write_output(text))

    def _write_output(self, text):
        """（GUI 线程）写输出面板；面板没开着时，把首行也显示到左侧状态栏.

        由 :meth:`write` 投递到本线程后执行 —— **不要**从别处直接调用。
        """
        self.get_output_widget().add_text(text)
        if not self.get_output_widget().isVisible():
            # 输出面板没开着时，把这一行也显示到**左侧**状态栏 —— 否则脚本里
            # print 的东西用户根本看不见（面板是关着的）。
            #
            # ⚠️ **不要**写进 ``version_button``（右侧角落里那个版本按钮）：
            #    它固定显示版本号，把 print 的内容塞进去会把它顶掉。
            # ⚠️ 也别写进 ``run_state_light``（它的「运行中 / 已暂停」由 ``refresh``
            #    按控制台状态设置，塞文本进去下一次 ``refresh`` 就会被覆盖）。
            # ⚠️ 也不走 ``gui.status(text, 3000)`` 那种**带超时**的写法：那是瞬时
            #    消息，会被下一条消息（甚至鼠标划过状态栏控件）顶掉，用户错过就
            #    再也看不到；这里要的是「常驻到最后一次输出」，所以不传 timeout
            #    （``showMessage`` 缺省 msecs=0 就是「直到被下次消息替换」）。
            # ⚠️ 只放一行纯文本：ANSI 转义码要先去干净，否则这里会显示成乱码。
            lines = OutputWidget.plain_text(text).strip().splitlines()
            if len(lines) > 0:
                self.show_status(lines[0][:80])

    def flush(self):
        pass

    def fileno(self):
        """没有任何文件描述符，抛 ``io.UnsupportedOperation``（与 ``io.StringIO`` 一致）。

        ⚠️ **不要**在这里返回一个伪造的 fd（比如 1）：有库会拿它去 ``os.isatty`` / ``select``
        / ``msvcrt``，伪造的 fd 会指向**真正的**控制台（GUI 模式下可能是 ``None`` 甚至无效），
        得到的结论和真实行为完全对不上。抛标准异常才能让它们走「不是文件」的回退分支。
        """
        raise io.UnsupportedOperation("fileno")

    def isatty(self):
        """本控制台**不是**真正的终端（``sys.stdout`` / ``sys.stderr`` 指向本对象）。

        ``print`` 不需要它，但有些第三方库会直接 ``sys.stdout.isatty()`` —— 没有这个方法就是
        ``AttributeError``（实测本机装着的 tqdm / rich / click 都用 ``hasattr`` /
        ``getattr(..., None)`` / ``try/except`` 兜住了，但公开方法是这类调用唯一的保障）。

        返回 **False 是有意的**：QTextBrowser 做不了光标定位 / 行覆盖（``\\033[1A`` 这类序列
        被 :class:`_Ansi` 过滤掉、``\\r`` 会变成换行），返回 True 会让 tqdm / rich 按「可交互
        终端」输出，在控制台里刷成一大片重复内容；返回 False 时它们会退化成「只打最终结果 /
        不打进度条」。颜色与此无关 —— 我们自己做（stderr 见 :class:`_RedStderr`）。
        """
        return False

    def closeEvent(self, event):
        if self.console.is_running():
            reply = QtWidgets.QMessageBox.question(
                self, "退出UI", "内核似乎正在运行，确定要退出吗？"
            )
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        if callable(on_close := getattr(self, "on_close", None)):
            on_close()  # 在确定要关闭之前执行的操作

    def showEvent(self, event):
        super().showEvent(event)
        # ⚠️ 第一次显示时才恢复右侧栏宽度（2026-10-26）：``QSplitter.setSizes`` 必须在
        #    窗口**已有真实尺寸**之后设，否则会被随后的布局计算覆盖。只做一次 ——
        #    之后用户拖出来的宽度由 ``resizeEvent`` 跟踪，不该被再次覆盖。
        if not getattr(self, "_splitter_restored", False):
            self._splitter_restored = True
            self.init_splitter_sizes()
        self.refresh()

    def resizeEvent(self, event):
        """窗口尺寸变了：记下右侧栏（控制台）当前可见的宽度.

        宽度的三个来源（2026-10-26 加的「右侧栏可调 + 尺寸记忆」）：

        1. **用户拖分隔条** —— 直接改 ``splitter.sizes()``；
        2. **窗口缩放** —— 拉伸因子是 ``(1, 0)``，增量全给左边，右边保持用户拖出来的宽度；
        3. **隐藏 / 显示右侧栏**（``操作 → 隐藏/显示``）—— 隐藏时 ``sizes()`` 里那一项是 0。

        本方法只做一件事：**只要右侧栏可见且宽度 > 0，就把宽度记到
        ``self._last_console_width``**。关窗时由 ``__on_close`` 交给
        ``settings.save_console_width`` 存盘；隐藏状态下不会用 0 把已记的宽度覆盖掉。
        """
        super().resizeEvent(event)
        try:
            if not self.right_tabs.isVisible():
                return
            sizes = self.splitter.sizes()
            if len(sizes) >= 2 and sizes[1] > 0:
                self._last_console_width = int(sizes[1])
        except Exception as err:
            print(f"Error: {err}")

    def __init_gui_api(self):
        # 默认，将所有新的定义的函数都添加到GUI API中
        # ⚠️ 所以下面的显式 add_func 只用于三类：**别名**（status→show_status、
        #    title→set_title…）、把 Qt 自己的函数**转接**出去（resize、
        #    set_style_sheet…），以及需要包一层的函数；同名的方法交给上面这个循环。
        for key in self.list_member_functions():
            func = getattr(self, key)
            if callable(func):
                self.gui_api.add_func(key, func)
        self.gui_api.add_func("close", self.close)
        self.gui_api.add_func("status", self.show_status)
        self.gui_api.add_func("start", self.start_func)
        self.gui_api.add_func("tab_count", self.count_tabs)
        self.gui_api.add_func("title", self.set_title)
        self.gui_api.add_func("window", lambda: self)
        self.gui_api.add_func("is_maximized", lambda: self.isMaximized())
        self.gui_api.add_func("show_maximized", lambda: self.showMaximized())
        self.gui_api.add_func("resize", self.resize)
        self.gui_api.add_func("device_pixel_ratio", self.devicePixelRatioF)
        # 窗口样式表：直接把 Qt 自己的 setStyleSheet / styleSheet **转接**出去，
        # 不在这里加任何包装（落盘之类的逻辑在「设置 → 样式表」控件里做）。
        self.gui_api.add_func("set_style_sheet", self.setStyleSheet)
        self.gui_api.add_func("get_style_sheet", self.styleSheet)

        try:
            from zmlx.ui.alg import edit_in_tab, reg_file_type

            for key, func in [
                ("reg_file_type", reg_file_type),
                ("edit_in_tab", edit_in_tab),
            ]:
                self.gui_api.add_func(key, func)
                gui.mark_direct(key)  # 直接调用的函数
        except Exception as err:
            print(err)

        for key in ["window"]:
            gui.mark_direct(key)

    def __init_actions(self):
        """
        初始化内置的菜单动作
        """

        def not_running():
            return not self.is_running()

        self.add_action(
            menu="文件",
            name="set_cwd",
            icon="open",
            tooltip="设置工作路径 (在进行各种操作前，务必确保工作路径正确)",
            text="工作路径",
            shortcut="Ctrl+W",
            slot=self.set_cwd_by_dialog,
            on_toolbar=True,
            is_enabled=not_running,
            is_visible=lambda: True,
        )

        self.add_action(
            menu="文件",
            name="open",
            icon="open",
            tooltip="打开文件",
            text="打开",
            slot=self.open_file_by_dlg,
            on_toolbar=True,
            shortcut=QtGui.QKeySequence.StandardKey.Open,
            is_enabled=not_running,
            is_visible=lambda: True,
        )

        self.add_action(
            menu="文件",
            name="new_file",
            icon="new",
            text="新建",
            shortcut=QtGui.QKeySequence.StandardKey.New,
            slot=self.new_file,
            on_toolbar=True,
            is_enabled=not_running,
        )

        self.add_action(
            menu="文件",
            name="temp_code",
            icon="python",
            text="脚本",
            slot=lambda: self.open_code("temp_code.py"),
            on_toolbar=True,
            is_enabled=not_running,
        )

        # ⚠️ **「退出」排在文件菜单的最后**（2026-10-26 归位）：历史版本里它一直在末尾
        #    （`… 新建 → 脚本 → … → 导入 → 保存 → 导出 → 退出`，见 v1.8.17 / v1.9.19），
        #    而当时它排在「脚本」后面，是因为那时后面**还没有**导入 / 保存 / 导出
        #    （2026-10-07 才加）。这里把它的注册挪到导出之后，顺序回到「退出在最后」，
        #    菜单里其余条目（工作路径 → 打开 → 新建 → 脚本 → 导入 → 保存 → 导出）一个字没动。
        #    ⚠️ action name ``quit`` 不变。

        # ★ 分隔线 1（2026-10-28，``text='---'``）：上面是**打开 / 新建 / 切工作路径**，
        #    下面「导入 / 保存 / 导出」都是**当前这一页的数据操作** —— 而且它们的
        #    ``is_visible`` 都跟「当前页有没有这个能力」绑定，会一起出现 / 消失，
        #    分成两段才看得出这不是同一类东西。
        #    ⚠️ 分隔线只能**插在末尾**（``get_menu(menu).addSeparator()``），所以它的位置
        #    就是「注册到这里」的位置：这条必须在「导入」**之前**注册。
        #    ⚠️ 本菜单插件不会往里挂条目（唯一相关的是「文件 → 浏览」那个**子菜单**，
        #    由 ``image_browser`` 插件建），所以线不会被后挂的条目挤到下面。
        self.add_action(menu="文件", text="---")

        def import_data():
            widget = self.get_current_widget()
            if callable(f := getattr(widget, "import_data", None)):
                try:
                    f()
                    self.refresh_action()
                except Exception as e:
                    print(e)

        self.add_action(
            menu="文件",
            text="导入",
            name=None,
            slot=import_data,
            icon="import",
            on_toolbar=True,
            is_visible=lambda: (
                hasattr(self.get_current_widget(), "import_data")
                and not self.is_running()
            ),
        )

        def is_enabled():
            widget = self.get_current_widget()
            if hasattr(widget, "need_save"):
                try:
                    return widget.need_save()
                except Exception as err:
                    print(err)
                    return True
            else:
                return True

        def save_file():
            widget = self.get_current_widget()
            if callable(f := getattr(widget, "save_file", None)):
                try:
                    f()
                    self.refresh_action()
                except Exception as e:
                    print(e)

        self.add_action(
            menu="文件",
            text="保存",
            name=None,
            slot=save_file,
            icon="save",
            shortcut="Ctrl+S",
            on_toolbar=True,
            is_enabled=is_enabled,
            is_visible=lambda: (
                hasattr(self.get_current_widget(), "save_file")
                and not self.is_running()
            ),
        )

        def export_data():
            widget = self.get_current_widget()
            if callable(f := getattr(widget, "export_data", None)):
                try:
                    f()
                    self.refresh_action()
                except Exception as e:
                    print(e)

        self.add_action(
            menu="文件",
            name="export_data",
            icon="export",
            text="导出",
            shortcut="Ctrl+Shift+S",
            slot=export_data,
            on_toolbar=True,
            is_visible=lambda: (
                hasattr(self.get_current_widget(), "export_data")
                and not self.is_running()
            ),
        )

        # ★ 分隔线 2（2026-10-28）：上面是**数据操作**，下面是**退出程序** ——
        #    「退出」不该和「保存 / 导出」挤在一起（误点的后果完全不同）。
        self.add_action(menu="文件", text="---")

        # 「退出」放最后（历史顺序，见上面那段说明）
        self.add_action(
            menu="文件",
            name="quit",
            icon="quit",
            text="退出",
            slot=self.close,
        )

        # ⚠️ 「刷新」2026-10-26 由「显示」**移到「操作」**：它是**动作**（重设标题、
        #    刷新当前页、重算所有菜单项的灰/亮），而「显示」那一组收的是**页面入口**
        #    （变量 / 耗时 / 标签列表 / 通知 …）。原来它与那些页面入口并列，读起来
        #    像是"打开一个叫刷新的页面"。
        #    ⚠️ ``name`` 仍是 ``'refresh'``（ribbon 配置、已保存的界面布局按 name 定位）；
        #    本项**不在工具栏上**（原来也不在），所以只影响菜单里那一行。
        self.add_action(
            menu="操作", name="refresh", icon="refresh", text="刷新", slot=self.refresh
        )

        self.add_action(
            menu="显示",
            name="memory",
            icon="variables",
            text="变量",
            slot=self.show_memory,
        )

        # ★ 「显示 → 重置布局」（2026-10-26 新加）：布局现在可调（右侧栏可拖、宽度与
        #    可见性都会记住），这是"改乱了怎么办"的出口。槽指向本类的公开方法
        #    ``reset_layout`` —— 它同时被自动注册成 ``gui.reset_layout()``，所以脚本里
        #    可以 ``gui.reset_layout(ask=False)`` 无确认地重置。
        #    ⚠️ 菜单文字用「重置布局」四个字，与 Ribbon/界面上其它两字菜单不同 —— 它本来
        #       就不是"打开一个页面"，长一点反而不会被误点。
        #    ⚠️ 文案必须与 :meth:`reset_layout` 的实际范围一致：**只动右侧栏**，
        #       不动窗口大小、不动样式表（2026-10-26 用户要求）。改行为时一起改这里。
        self.add_action(
            menu="显示",
            name="reset_layout",
            icon="refresh",
            tooltip="把右侧栏的宽度与显示状态恢复成默认"
            "（窗口大小、样式表、已打开的标签页都不受影响）",
            text="重置布局",
            slot=self.reset_layout,
        )

        # 标签列表：原先**只有**标签栏右键菜单里那一个入口（「列出标签」），
        # 菜单栏里没有 —— 用户得先知道有右键菜单才找得到这个总览视图。
        # ⚠️ 这里**不给 icon**：``zml_icons/`` 里没有「清单 / 标签页」这一类的图，
        #    而 ``load_icon`` 对找不到的名字会返回**空图标**（不报错、只是没图形）；
        #    与其拿一个语义无关的图（如 ``variables`` 的 (x)）凑数，不如不画。
        #    将来若补了合适的图，在这里加一个 ``icon=`` 即可。
        # ★ 分隔线（2026-10-28，``text='---'``）：「刷新」是**独立动作**（重设标题、
        #    刷新当前页、重算所有菜单项的灰/亮），与内核运行**无关**；下面一整组
        #    （运行 / 暂停 / 继续 / 停止 / 强制结束）才是**内核控制**。11 项平铺太乱，
        #    这里用线分出第一段。
        #    ⚠️ 「操作」菜单**没有插件往里挂条目**（插件挂的是显示 / 帮助 / 文件→浏览），
        #    所以这条线不会被后挂的条目挤到下面。
        self.add_action(menu="操作", text="---")

        def exec_enabled():
            if self.is_running():
                return False
            else:
                f = getattr(self.get_current_widget(), "console_exec", None)
                return callable(f)

        def console_exec():
            f = getattr(self.get_current_widget(), "console_exec", None)
            if callable(f):
                f()

        self.add_action(
            menu="操作",
            name="console_exec",
            icon="begin",
            tooltip="运行当前标签页面显示的脚本 (执行当前标签的console_exec函数)",
            text="运行",
            shortcut="Ctrl+R",
            slot=console_exec,
            on_toolbar=True,
            is_enabled=exec_enabled,
        )

        # ⚠️ 快捷键（2026-10-26 统一）：**运行 / 暂停 / 继续 / 再次运行**必须各占一个键，
        #    不能有两个 action 抢同一个。原先「运行」与「继续」都是 ``Ctrl+R``、
        #    「继续」与「再次运行」都是 ``Ctrl+Shift+R``，而 Qt 对重复快捷键触发哪个
        #    是**不确定的**（暂停后按 Ctrl+R 有可能重开一次任务，而不是继续）。
        #    现在的分配：
        #        Ctrl+R       运行
        #        Ctrl+Shift+P 暂停
        #        Ctrl+Shift+R 继续（暂停之后的"接着跑"）
        #        Ctrl+Q       停止
        #        F5           再次运行
        #    给「暂停」补了快捷键：原先它一个都没有，而任务执行中的人最想按的恰恰是它。

        def pause_enabled():
            c = self.get_console()
            if not c.is_running():
                return False
            return not c.get_pause()

        self.add_action(
            menu="操作",
            name="console_pause",
            icon="pause",
            tooltip="暂停内核的执行 (需要提前在脚本内设置break_point)",
            text="暂停",
            shortcut="Ctrl+Shift+P",
            slot=lambda: self.get_console().set_pause(True),
            on_toolbar=True,
            is_enabled=pause_enabled,
        )

        self.add_action(
            menu="操作",
            name="console_resume",
            icon="begin",
            tooltip=None,
            text="继续",
            shortcut="Ctrl+Shift+R",
            slot=lambda: self.get_console().set_pause(False),
            on_toolbar=True,
            is_enabled=lambda: self.is_running() and self.get_console().get_pause(),
        )

        self.add_action(
            menu="操作",
            name="console_stop",
            icon="stop",
            tooltip="安全地终止内核的执行 (需要提前在脚本内设置break_point)",
            text="停止",
            shortcut="Ctrl+Q",
            slot=lambda: self.get_console().stop(),
            on_toolbar=True,
            is_enabled=self.is_running,
        )

        self.add_action(
            menu="操作",
            name="console_kill",
            icon="kill",
            text="强制结束",
            slot=self.kill_thread,
            is_enabled=self.is_running,
        )

        # ★ 分隔线（2026-10-28）：上面是**内核控制**（运行 / 暂停 / 继续 / 停止 / 强制结束），
        #    下面是**右侧控制台栏**与**历史 / 页面**——三组语义完全不同，分开才看得清。
        self.add_action(menu="操作", text="---")

        # ⚠️ 「隐藏」与「显示」是一对**互斥**的开关（``is_enabled`` 互为取反），所以
        #    它们**共用** ``Ctrl+H`` 是对的：任何时刻只有一项可用，不会真的竞争。
        #    ⚠️ 这里**刻意写字符串**：本机 PyQt6 6.9.1 的 ``QKeySequence.StandardKey``
        #    里**没有** ``ToggleTabView`` / ``ShowTabView`` 这两个成员（实测 71 个成员里
        #    与 Tab 相关的只有 ``AddTab``，``hasattr`` 两者都是 False），若写成 StandardKey
        #    就会 ``AttributeError``，整个窗口起不来。
        self.add_action(
            menu="操作",
            name="console_hide",
            icon="console",
            tooltip="隐藏主窗口右侧的控制台",
            text="隐藏",
            shortcut="Ctrl+H",
            slot=self.hide_console,
            on_toolbar=True,
            is_enabled=lambda: self.right_tabs.isVisible(),
        )

        self.add_action(
            menu="操作",
            name="console_show",
            icon="console",
            tooltip="显示主窗口右侧的控制台",
            text="显示",
            # ⚠️ 与「隐藏」**共用** ``Ctrl+H`` —— 理由同上。
            shortcut="Ctrl+H",
            slot=self.show_console,
            on_toolbar=True,
            is_enabled=lambda: not self.right_tabs.isVisible(),
        )

        # ★ 分隔线（2026-10-28）：上面是「隐藏 / 显示控制台栏」，下面
        #    「再次运行 / 清除历史 / 关闭所有页面」是**历史与页面**的杂项。
        self.add_action(menu="操作", text="---")

        self.add_action(
            menu="操作",
            name="console_start_last",
            text="再次运行",
            tooltip="在控制台重新执行上一次的操作",
            # ⚠️ 2026-10-26：**原先这里也是 ``Ctrl+Shift+R``、与「继续」撞车**。现在
            #    「继续」占 ``Ctrl+Shift+R``，本项改用 ``F5``（「重新运行」在多数 IDE 里
            #    就是 F5，用户不必重新记）。⚠️ 它**不能**用 ``Ctrl+R``：那是「运行」的。
            #    ⚠️ ``F5`` **不是**直接取 ``StandardKey.Refresh``：本机实测 ``Refresh``
            #    恰好解析成 ``F5``，但那是"碰巧"—— 其他平台/主题下它可能是 ``Ctrl+R``，
            #    正好又和「运行」撞车。写死 ``F5`` 才稳定。
            shortcut="F5",
            on_toolbar=True,
            slot=self.get_console().start_last,
            is_enabled=lambda: (
                not self.is_running() and get_last_exec_history() is not None
            ),
        )

        self.add_action(
            menu="操作",
            name="console_clear_exec_history",
            icon="clean",
            tooltip="清除掉控制台执行的历史",
            text="清除历史",
            slot=clear_exec_history,
            on_toolbar=False,
            is_enabled=lambda: (
                get_last_exec_history() is not None and not self.is_running()
            ),
        )

        self.add_action(
            menu="操作",
            name="close_all_tabs",
            icon="close_all",
            text="关闭所有页面",
            slot=self.close_all_tabs,
            is_enabled=lambda: self.count_tabs() > 0,
        )

        self.add_action(
            menu="设置",
            name="env",
            icon="set",
            text="系统",
            shortcut="Ctrl+E",
            slot=self.show_env_edit,
        )

        # 显示文字是「插件」，但 name 仍沿用 'setup_files'：ribbon 配置、
        # 外部脚本和已保存的界面布局都按 name 定位这个动作，改名会让它们失效。
        # 见 zmlx/ui/ReadMe.md「命名遗留」一节。
        self.add_action(
            menu="设置",
            name="setup_files",
            icon="plugin",
            text="插件",
            slot=self.edit_setup_files,
        )

        # ★ 「设置 → 求解器」**不在这里**（2026-10-18 移）：那一行 ``add_action``
        #    已搬进插件 ``plugins/builtin/solver_menu.py``（默认不加载）。
        #    ⚠️ 2026-10-22 起 ``show_solver_selector`` 方法**也搬过去了**（连同控件），
        #    命令由那边 `gui.add_func` 注册；本类**不留**同名方法 —— 见
        #    「``show_solver_selector`` 已搬到插件」那段注释。

        self.add_action(
            menu="设置",
            name="gui_iter",
            text="迭代器",
            slot=lambda: self.show_gui_iter(on_top=True),
        )

        # ★ 「设置 → 样式表」**不在这里**（2026-10-18 移）：那一行 ``add_action``
        #    已搬进插件 ``plugins/builtin/style_sheet_menu.py``（**默认启用** —— 样式是用户
        #    随时会调的外观设置，做成插件只是为了**可被禁用**，不是为了藏起来）。
        #    ⚠️ 2026-10-22 起 ``show_style_sheet`` 方法与 ``StyleSheetEdit`` 控件也一并搬到
        #    那个插件了（它只有这个插件在用 → 完全自含）。命令 ``gui.show_style_sheet``
        #    由插件显式注册；插件没启用时由 ``extra_setups/plugin_placeholders.py`` 的
        #    占位给出一句提示（所以命令**总是存在**，历史标签页照常重放）。

        # ---- 「帮助」菜单 ----
        #
        # 最终结构（两级，没有更深的一层）::
        #
        #     帮助 ─┬─ 关于                (Ctrl+Shift+A)
        #           ├─ ReadMe              (F1)
        #           ├─ 登录
        #           ├─ 反馈
        #           ├─ ▸ 用户 → 管理 · 登录记录 · 反馈记录   ← 构造期建，紧跟「反馈」
        #           ├─ 示例                ← 插件「示例浏览」注册（构造后追加，排在子菜单后）
        #           └─ ▸ 其它 / 架构        ← extra_setups 后注册
        #
        # ★ 2026-10-26：「用户」子菜单排在「反馈」**正下方**（用户点名的顺序）。
        #   上一版（2026-10-24）为了「高频操作别点两下」把登录 / 反馈提到一级、并把关于
        #   放到了 ReadMe 后面 —— 那次**顺带把「关于」挪了位置**。现在关于回到最上面，
        #   登录 / 反馈仍在一级（「直接点一下就到位」这个改进保留）。
        #
        # ★ 2026-10-24：`登录` / `反馈` 在**一级**，`查询` 子菜单**并入 `用户`**
        #   （「管理 / 登录记录 / 反馈记录」三项并列其下）。
        #
        # ★ 2026-10-19：原先独立的顶层「用户」菜单**整体并入「帮助」**（菜单栏因此
        #   少一个顶层菜单）。⚠️ **没有三级菜单**：登录记录 / 反馈记录现在处于
        #   「帮助 → 用户 → X」这一层，与「管理」同深。
        #
        # ⚠️ 顺序由**建菜单 / 注册的先后**决定，先来的排在前面。两条规则：
        #
        #    1. **子菜单的位置**：``get_menu`` 把新子菜单插在「骨架条目」之后、
        #       「插件条目」之前（判据是「是不是 ``__init_actions`` 期间加的」，见
        #       :meth:`_sub_menu_insert_after`）。所以本函数末尾那次
        #       ``get_menu(['帮助','用户'])`` 建出来的「用户」正好落在「反馈」之后、
        #       「示例」（插件后挂）之前。
        #    2. 普通条目由下面的 ``add_action`` 按顺序追加；**这里写的顺序就是显示顺序**。
        #
        #   ⚠️ 「示例」不在这里：它由插件 ``demo_menu`` 在**控制台内核**里注册，
        #   晚于 ``__init_actions`` —— 所以它是「插件条目」，排在子菜单之后。
        #
        # ⚠️⚠️ **菜单路径必须逐字一致**：``extra_setups/user_admin.py`` 与
        #   ``extra_setups/license_query.py`` 注册时写的是 ``['帮助', '用户']``。
        #   任何一处写成别的（例如旧的 ``['帮助', '查询']``），``get_menu`` 就会**另建**
        #   一个同名子菜单，界面上出现两个「用户」。
        #
        # ⚠️ **action name 一律沿用旧名**（``readme`` / ``about`` / ``reg`` / ``feedback``）：
        #    ribbon 配置、已保存的界面布局、外部脚本都按 name 定位，改名会让它们失效。

        # ---- 第 1 组：关于（历史顺序里排第一）----
        def about():
            print(lic.desc)
            self.show_about()

        self.add_action(
            menu="帮助",
            name="about",
            text="关于",
            shortcut="Ctrl+Shift+A",
            icon="info",
            slot=about,
            is_enabled=not_running,
        )

        # ---- 第 2 组：ReadMe（最常用的文档入口，紧跟在关于之后）----
        self.add_action(
            menu="帮助",
            name="readme",
            icon="info",
            text="ReadMe",
            shortcut="F1",
            slot=self.show_readme,
            on_toolbar=True,
        )

        # ---- 第 3 组：登录 / 反馈（一级，点一次就到）----
        self.add_action(
            menu="帮助",
            name="reg",
            icon="reg",
            text="登录",
            slot=self.show_reg_tool,
        )

        self.add_action(
            menu="帮助",
            name="feedback",
            text="反馈",
            icon="info",
            slot=self.show_feedback,
            is_enabled=not_running,
        )

        # ⚠️ 「帮助 → 示例」2026-10-22 **已搬到插件** ``plugins/builtin/demo_menu.py``
        #    （默认启用）：菜单项与 ``gui.show_demo`` 命令都由那边的 ``setup_ui()`` 注册。
        #    ⚠️ 这里**不要再加菜单项** —— 加回来会出现**两个**「帮助 → 示例」。
        #    ``gui.show_demo`` 的**占位**在 ``extra_setups/plugin_placeholders.py`` 里。

        # ---- 第 4 组：「用户」子菜单（条目在 extra_setups；位置 = 紧跟「反馈」之后）----
        self.get_menu(["帮助", "用户"])

        # ★ 「管理 / 登录记录 / 反馈记录」三项都注册在「帮助 → 用户」下（2026-10-24
        #    起「查询」不再单独存在）。它们**不在这里注册**：分别在
        #    ``extra_setups/user_admin.py`` 与 ``extra_setups/license_query.py``。
        #
        #    ⚠️ 它们的命令（``gui.show_user_admin`` / ``gui.show_check_count_view`` /
        #    ``gui.show_feedbacks_view``）也由各自文件用 ``gui.add_func`` 注册 ——
        #    原先靠 ``__init_gui_api`` 扫描本类的公开方法来注册，方法搬走之后必须
        #    由那边补上。旧名（``show_license_count`` / ``show_license_feedback``）
        #    作为**别名**也一并注册，好让老标签页的 ``gui_restore`` 还能恢复。
        #    ⚠️ 它们注册的 menu 必须写 ``['帮助', '用户']``（与上面一行逐字一致），
        #    否则 ``get_menu`` 会另建一个同名菜单，界面上出现两个「用户」。
        #
        #    ⚠️ 它的位置**不需要**在这里额外安排：「用户」是构造期建的子菜单，而
        #    ``get_menu`` 会把新子菜单插在「骨架条目」之后 —— 也就是紧跟上面刚挂的
        #    「反馈」之后、插件条目（示例 etc.）之前（2026-10-26 的规则，见
        #    ``_sub_menu_insert_after``）。

        # ★ 记下「骨架自己注册了哪些条目」（2026-10-26）：``get_menu`` 靠它把子菜单夹在
        #   「骨架条目」与「插件后挂条目」之间。**必须放在本函数的最后** —— 上面所有
        #   ``add_action`` / ``get_menu`` 都跑完之后再记，才是完整的骨架集合。
        self._record_builtin_actions()

    def reset_layout(self, ask=True):
        """「显示 → 重置布局」：把窗口布局恢复成默认（**立即生效 + 清掉存盘，下次启动也默认**）.

        ★ 2026-10-26 新加。布局现在可调（右侧栏可拖、宽度 / 可见性都会记住），所以需要
        一个「改乱了怎么办」的出口。

        立即做的事（**当前窗口**）：

        1. 右侧栏恢复默认宽度（``settings.DEFAULT_CONSOLE_RATIO``，约 22%；夹在
           ``settings.MIN_CONSOLE_WIDTH`` 以上）；
        2. 右侧栏恢复显示。

        同时调 ``settings.reset_layout()`` 清掉存盘的布局类键（右侧栏宽度 / 可见性）——
        **下次启动也是默认**。

        ⚠️⚠️ **2026-10-26 按用户要求收窄了范围**：本操作**不碰**这两样东西 ——

        - **窗口大小 / 位置**：用户把窗口拖成什么尺寸是"他知道自己在干什么"，重置布局
          不该把它拽回屏幕居中 75%；
        - **样式表**：外观（字体 / 配色 / 圆角）不是布局，清掉等于把用户的主题一起删了。
          ``settings.reset_layout()`` 的 ``style_sheet`` 参数因此传空元组。

        ⚠️ **不清的东西**：已打开的标签页（那是内容，不是布局）、插件名单、工作路径。

        Args:
            ask: 为真时先弹一个确认框（默认）；脚本里调用传 ``ask=False`` 直接执行。

        Returns:
            bool: 真执行了返回 True；用户取消 / 出错返回 False。
        """
        try:
            if ask:
                reply = QtWidgets.QMessageBox.question(
                    self,
                    "重置布局",
                    "将右侧栏的宽度与显示状态恢复成默认。\n"
                    "（窗口大小、样式表、已打开的标签页都不受影响）\n\n确定继续吗？",
                )
                if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                    return False

            # 1) 清存盘（下次启动也回到默认）。
            # ⚠️ **不传 style_sheet**：清掉样式表等于把用户的主题删了，而它不是布局。
            # ⚠️ ``settings.reset_layout`` 只删 ``settings.LAYOUT_KEYS`` 里的键 —— 窗口尺寸
            #    （``main_window_size*``）不在其中，所以"下次启动的窗口大小"也保持原样。
            cleared = settings.reset_layout(style_sheet=None)
            print(f"布局已重置，清除的存盘项：{cleared}")

            # 2) 当前窗口立即生效：显示右侧栏 + 默认宽度。
            # ⚠️ 这里**只重排右侧栏**，窗口几何一概不动（用户要的是「右侧栏改乱了」时
            #    点一下复原，而不是把窗口也拽回去）。宽度从父控件布局反推、当场就对，
            #    不需要等事件循环（见 ``_reset_splitter_sizes``）。
            self._last_console_width = None
            self.set_side_tabs_visible(True)
            self._reset_splitter_sizes()

            self.refresh()
            return True
        except Exception as err:
            print(f"Error when reset_layout: {err}")
            return False

    def _reset_splitter_sizes(self):
        """把右侧栏设成**默认比例**（窗口宽度的 ~30%）.

        抽出来给 :meth:`reset_layout` 用：它要在「窗口几何改完」之后**立刻**重新分配，
        而 ``init_splitter_sizes`` 会去读存盘（那时已清空，语义一样，但这里更直白）。

        ⚠️ **宽度不能取 ``splitter.width()``**：``setGeometry`` 之后布局还没重排，那里读到的
        是**旧**宽度（实测：新窗口 582 px 时仍返回 582 之前的值，按它分配就成了 78%）。
        改成从**父控件**的布局反推：``splitter.width()`` 若已等于新窗口宽度就直接用，
        否则用 ``父控件宽度 - 父布局的边距 - 分隔条宽度`` —— 这个数**当场就是对的**，
        不用等下一轮事件循环。

        ⚠️ 窗口比 ``MIN_CONSOLE_WIDTH`` 还窄时，按 :data:`settings.MAX_CONSOLE_RATIO` 夹断，
        免得把左边挤没。
        """
        splitter = getattr(self, "splitter", None)
        if splitter is None:
            return
        total = self._splitter_target_width()
        if total <= 0:
            return
        default = max(
            settings.MIN_CONSOLE_WIDTH, int(total * settings.DEFAULT_CONSOLE_RATIO)
        )
        default = min(default, max(1, int(total * settings.MAX_CONSOLE_RATIO)))
        self._last_console_width = int(default)
        splitter.setSizes([max(1, total - default), int(default)])

    def _splitter_target_width(self):
        """估算 splitter 在**当前窗口几何**下应有的宽度（不依赖布局是否已刷新）.

        Returns:
            int: 宽度（像素）；算不出来返回 0。
        """
        splitter = getattr(self, "splitter", None)
        if splitter is None:
            return 0
        width = splitter.width()
        # 父控件（中央 widget）的布局：左右边距 + 分隔条宽度都要扣掉
        try:
            parent = splitter.parentWidget()
            if parent is not None:
                layout = parent.layout()
                if layout is not None:
                    margins = layout.contentsMargins()
                    computed = (
                        parent.width()
                        - margins.left()
                        - margins.right()
                        - splitter.handleWidth()
                    )
                    if computed > 0:
                        return computed
        except Exception as err:
            print(f"Error when compute splitter width: {err}")
        if width <= 0:
            return max(self.width(), 800)
        return width

    def init_splitter_sizes(self):
        """给「顶部标签页 / 右侧栏」设初始宽度（有存盘记录就用记录）.

        ★ 2026-10-26：右侧栏从「固定比例、拖不动」改成「**用户可拖 + 宽度记下来**」。
        本方法负责**启动时**那一半（恢复），另一半在 ``resizeEvent``（跟踪用户拖出来
        的宽度）与 ``__on_close``（关窗存盘，走 ``settings.save_console_width``）。

        ⚠️ **必须在窗口已布局之后调用**：``QSplitter.setSizes`` 设完会被紧随其后的
        第一次布局计算覆盖 —— 所以这里不在 ``__init__`` 里图省事，而是由
        ``showEvent``（第一次）触发；``__init__`` 末尾那次调用只是**兜底**（不显示窗口
        直接跑脚本时也要有个合理比例）。

        ⚠️ **默认宽度** = ``splitter`` 宽度 × :data:`settings.DEFAULT_CONSOLE_RATIO`
        （2026-10-26 由 0.30 调成 0.22）；用户拖过之后以存盘值为准，这个比例**只在
        没有记录时**生效。
        """
        splitter = getattr(self, "splitter", None)
        if splitter is None:
            return
        total = splitter.width()
        if total <= 0:
            # 还没布局：用窗口宽度估算（``QSplitter`` 会按比例分）
            total = max(self.width(), 800)
        default = max(
            settings.MIN_CONSOLE_WIDTH, int(total * settings.DEFAULT_CONSOLE_RATIO)
        )
        default = min(default, max(1, int(total * settings.MAX_CONSOLE_RATIO)))
        width = settings.load_console_width(self, default_width=default)
        if width is None:
            width = default
        self._last_console_width = int(width)
        splitter.setSizes([max(1, total - width), int(width)])

    def list_member_functions(self):
        """
        列出所有成员函数（排除以下划线开头的私有方法，包括__xxx__和_MainWindow__xxx）
        """
        import inspect

        return [
            name
            for name, _ in inspect.getmembers(self.__class__)
            if inspect.isfunction(getattr(self.__class__, name))
            and not name.startswith("_")
        ]

    def parse_value(self, value):
        if callable(value):  # 直接是一个函数，直接运行
            return value()

        if isinstance(value, dict):  # 字典，则尝试作为带有参数的函数
            if callable(on_window := value.get("on_window")):
                return on_window(self)

            if callable(func := value.get("func")):
                args = value.get("args", [])
                args = [self if item == "@window" else item for item in args]
                return func(*args)

        # 直接返回数值
        return value

    def get_menu(self, name):
        """
        返回给定name的菜单
        """
        assert name is not None, "Error: name is None when get_menu"
        if isinstance(name, str):
            keys = [name]
        else:
            keys = name
        if len(keys) == 0:
            return None

        keys = [settings.get_text(key) for key in keys]  # 替换字符串

        menu = None
        for action in self.menuBar().actions():
            if isinstance(action.menu(), QtWidgets.QMenu) and action.menu().title() == keys[0]:
                menu = action.menu()
                break

        if menu is None:
            menu = QtWidgets.QMenu(self.menuBar())
            menu.setTitle(keys[0])
            self.menuBar().addAction(menu.menuAction())

        # 现在，主menu找到了，下面，找次一级的menu
        for idx in range(1, len(keys)):
            key = keys[idx]
            sub_menu = None
            for action in menu.actions():
                if isinstance(action.menu(), QtWidgets.QMenu) and action.menu().title() == key:
                    sub_menu = action.menu()
                    break
            if sub_menu is None:
                sub_menu = QtWidgets.QMenu(menu)
                sub_menu.setTitle(key)
                # ⚠️⚠️ **新子菜单排在「菜单自身注册的条目」之后、插件条目之前**
                #    （2026-10-26 定的最终规则，替换此前「永远排到最后」）：
                #
                #    文件  工作路径 · 打开 · 新建 · 脚本 · 导入 · 保存 · 导出 · 退出   →  ▸ 浏览
                #    帮助  关于 · ReadMe · 登录 · 反馈   →  ▸ 用户   →  示例（插件后挂的）
                #
                #    为什么不是「追加到末尾」：插件（``demo_menu`` 等）在启动后才往菜单里
                #    **追加**普通条目，子菜单于是被挤到它们后面（实测「帮助 → 用户」跑到
                #    「示例」之后、「文件 → 浏览」跑到「更新」之后）。
                #    为什么不是「第一个普通条目之前」：``get_menu`` 在构造期就会被调用
                #    （本类 ``__init_actions`` 末尾），那时普通条目还没挂完 —— 子菜单会落到
                #    最前面（实测「帮助 → 用户」跑到了「关于」头上）。
                #
                #    ★ 所以判据是「**这一段**是菜单自己注册的、还是插件后来追加的」：
                #    ``MainWindow`` **构造完成**时，菜单里已有的条目 = 骨架自己注册的
                #    （动画顺序就是代码里的书写顺序）；构造之后新增的 = 插件 / extra_setups
                #    后挂的。子菜单插在「构造期最后一条」之后 —— 即**夹在两段之间**。
                #    构造期创建的菜单（例如「帮助 → 用户」）：那时菜单里还没有任何插件条目，
                #    于是它落在所有条目之后；插件随后追加的条目排在它后面。两种情形都对。
                #
                #    ⚠️ 锚点**每次调用时现算**（见 :meth:`_sub_menu_insert_after`），
                #    而不是记一个"第几条"，这样即使某个插件用自己的 ``get_menu`` 又建了
                #    子菜单，索引也不会错位。
                #    ⚠️ **不能复用已有子菜单的 action 去 addAction**：同一个 action 在一个
                #    菜单里只能出现一次，那样 Qt 会把它**直接挪**到末尾、连带打乱别的顺序
                #    （实测「文件」的固有条目因此被整块甩到了「浏览」之后）。
                menu.insertAction(
                    self._sub_menu_insert_after(menu), sub_menu.menuAction()
                )
            menu = sub_menu  # 设置为当前层级的目录
        # 完成了所有的遍历，找到对应的menu
        return menu

    def _sub_menu_insert_after(self, menu):
        """返回「把新子菜单插在**它后面**」的那个 action（锚点）.

        规则见 :meth:`get_menu` 里那段说明：子菜单要夹在「菜单自身注册的条目」与
        「插件后挂的条目」之间。

        判据：遍历（按显示顺序），**第一个「在 ``__init_actions`` 之后才加进去的」普通
        条目之前的位置**就是子菜单该去的地方。因为 ``__init_actions`` 在构造期同步跑完，
        那时菜单里的条目是连续的一段前缀；之后追加的都在后面。

        Args:
            menu: 父菜单（``QMenu``）。

        Returns:
            QAction | None: ``insertAction`` 的锚点（插在它前面）；``None`` = 插到末尾。
        """
        actions = menu.actions()
        if not actions:
            return None
        # 构造期最后一条普通条目（子菜单不参与，它们由本方法自己归位）
        last_builtin = None
        for idx, action in enumerate(actions):
            if action.menu() is not None:
                continue
            if self._is_builtin_action(action):
                last_builtin = action
        if last_builtin is None:
            # 这个菜单里一个"骨架自己注册的条目"都没有 —— 落到末尾
            return None
        idx = actions.index(last_builtin)
        # 找「构造期最后一条」之后的第一条 —— 新子菜单就插在它前面（没有就插到末尾）
        for action in actions[idx + 1 :]:
            if action.menu() is not None:
                continue  # 跳过已有的子菜单
            return action
        return None

    def _is_builtin_action(self, action):
        """判断一个 action 是不是**骨架（``MainWindow``）自己在构造期注册的**.

        做法：``__init_actions`` 跑完时把当时已有的 action 记进
        ``self._builtin_actions``（id 集合），之后新增的（插件 / extra_setups）不在里面。

        ⚠️ 用 **id()** 而不是 objectName：后者可空、可重复，而 ``QAction`` 是 Qt 对象，
        在界面存活期间 id 稳定。

        Args:
            action: ``QAction``。

        Returns:
            bool: 是构造期注册的返回 True。
        """
        return id(action) in getattr(self, "_builtin_actions", ())

    def _record_builtin_actions(self):
        """记下**当前**菜单栏里的全部 action（＝骨架在 ``__init_actions`` 里注册的）.

        在 ``__init_actions`` 的最后调用一次（见那里）。插件与 ``extra_setups`` 在
        ``MainWindow`` 构造**之后**才挂条目 —— 它们都不在这个集合里，于是
        :meth:`_sub_menu_insert_after` 能把「骨架条目」与「插件条目」分开。
        """
        actions = set()
        try:
            for top in self.menuBar().actions():
                menu = top.menu()
                if menu is None:
                    actions.add(id(top))
                    continue
                for action in menu.actions():
                    actions.add(id(action))
                    sub = action.menu()
                    if sub is not None:
                        for sub_action in sub.actions():
                            actions.add(id(sub_action))
        except Exception as err:
            print(f"Error when record builtin actions: {err}")
        self._builtin_actions = actions

    def get_toolbar(self, name: str):
        """
        返回对应的菜单的工具栏
        """
        for toolbar in self.findChildren(QtWidgets.QToolBar):
            if toolbar.windowTitle() == name:
                return toolbar
        return self.addToolBar(name)

    def add_action(
        self,
        menu=None, text=None, name=None, slot=None,
        icon=None, tooltip=None, shortcut=None, on_toolbar=None,
        is_enabled=None, is_visible=None, overwritable=None, overwrite=None,
    ):
        """
        添加一个Action. 这是一个新的版本，将替代后续的直接基于File的ActionX的创建方法，
        并且将支持动态地创建Action。
        Since 2026-6-9.

        Args:
            menu: 菜单路径。``str`` 表示一级菜单名（``'显示'``），``list`` / ``tuple``
                表示多级路径（``['帮助', '用户']`` / ``('帮助', '用户')``）。
                ⚠️ 每一级的标题必须与别处注册时**逐字一致**，
                否则 :meth:`get_menu` 会另建一个同名菜单。省略时归到「其它」。
                ★ 2026-10-28：``text`` 省略时，**长度 ≥ 2** 的序列（``list`` / ``tuple``）
                会把它**最后一级**当作菜单文字
                （``['帮助', '用户', '管理']`` ⇔ 在「帮助 → 用户」下挂「管理」），
                不必把最后一级再写一遍。⚠️ 内部先转成新 list，调用者传进来的对象不会被改动。
            text: 菜单文字。可以是 ``str``，也可以是一个**返回文字的 callable**
                （每次刷新时重新取，用于带计数的标题）。**必填**（分隔符除外）：
                两者都不是会抛 ``ValueError`` —— 它不是可选装饰，而是菜单项的正文，
                也是自动命名与判重的依据，没有合理的默认值。
                ⚠️ 唯一的例外是上面那条：多级 ``menu`` 的最后一级可以充当它。
                传 ``'---'`` 表示插**分隔线**（见下面的 Note）。
            name: action 的 ``objectName``，也是 :meth:`get_action` 的查找键。
                省略时**任何情况下**都由 :meth:`_auto_action_name` 按 ``menu`` + ``text``
                自动生成（不是只在某个 ``overwrite`` 取值下才算）：

                - ``text`` 是 str → ``auto_<sha256(menu 路径 + text)>``；
                - ``text`` 是 callable → 按函数的**身份**（模块名 + 限定名 + 定义行号，
                  绑定方法再加实例）生成，**不调用它**；见 :meth:`_callable_id`。

                于是「同一菜单 + 同一文字」的两次注册会得到**同一个**名字，判重因此对
                所有调用方式一致生效（见下面的 ``overwrite``）。
            slot: 点击后执行的动作（经 :meth:`parse_value` 解析，见那里的三种形态）。
            icon: 图标名（``zml/ui/data/zml_icons/`` 下的文件名，不带扩展名）。
                ⚠️ 名字不存在时**静默**得到空图标，不会报错。
            tooltip: 悬停提示。
            shortcut: 快捷键，``str`` 或 ``QKeySequence``。
            on_toolbar: 为真时同时把该 action 挂到同名工具栏上（用 ``menu`` 的第一级命名）。
            is_enabled: 可选的 callable，动态决定该项是否可用。
            is_visible: 可选的 callable，动态决定该项是否可见。
            overwrite: **「``name`` 已经被占用时怎么办」**：

                - ``True``（默认）：**就地覆盖** —— 找到那个已有的 action，用本次的
                  ``slot`` / ``icon`` / ``tooltip`` / ``text`` / ``shortcut`` / 动态回调
                  把它**重新设置**一遍，它**留在原来的菜单位置**，菜单里**始终只有一条**。
                  于是「先挂一条占位、插件加载后用同名再挂一次」就能真正生效。
                - ``False``：只注册一次 —— 撞了就发出 ``UserWarning``（说明撞的是哪个
                  菜单项）并**直接 ``return``**，已有那条**保持原样**。

                ★ 2026-10-27 由 ``overwritable`` 改名而来（旧名仍可用，见下一条）：
                那个名字是**形容词**（「（这个 action）可被覆盖」），描述的是**别人对我**
                的操作；而本参数管的是**这一次调用要不要覆盖已经存在的那条**，描述的是
                **本次调用的动作** —— 视角正好反了。

                ⚠️ 命中的判据是 ``name``：显式给了就用它；没给时由
                :meth:`_auto_action_name` 按 ``menu`` + ``text`` 自动算出同一个名字，
                所以「同 menu + 同 text」的第二次注册同样会走覆盖。

                ⚠️ 历史（阅读旧代码时别被注释误导）：2026-10-25 之前，``True`` 会
                **另挂一条**（``unnamed_XXX`` / ``<原名>_001``，菜单里出现两条），
                ``False`` 是静默跳过。``show_pg_console`` 的菜单一度因此「命令是真的、
                点菜单却只打印提示」—— 现在的覆盖语义正是为这类场景准备的。
            overwritable: **已弃用（2026-10-27 改名，2027-10-27 删除）**，请改用
                ``overwrite``。给了它就会发一条 ``DeprecationWarning``，然后把它当作
                ``overwrite`` 使用，**行为完全等价**；两个都给且含义相反时抛 ``TypeError``
                （不替调用者猜）。保留原名只为过渡。

        Note:
            **分隔符**：``text='---'`` 时本函数**不建 action**，只在 `menu` 末尾插一条
            分隔线，其余参数全部忽略（`slot` / `shortcut` / `on_toolbar` /
            `overwrite` 一个都不用给）。用法::

                gui.add_action(menu='操作', text='---')
                gui.add_action(menu='操作', text='我的命令', slot=...)

            - 判据是 **``text``**（2026-10-26 改；此前是 ``name='---'``）—— 分隔符没有
              名字，也不会走下面的自动命名；
            - **必须给 ``menu``**：``menu is None`` 时直接返回，不插线、也不会为了它
              凭空造一个「其它」菜单（2026-10-26 改）；
            - 只用于**菜单**：``on_toolbar`` 在这里不生效（工具栏的分隔符仍要用
              ``QToolBar.insertSeparator`` 自己插）；
            - **不判重**：连插两条就是两条分隔线（它根本没有 action，菜单项列表里只是
              多了一条分隔）；
            - 无界面时（``gui.exists()`` 为假）整个调用 no-op，与 :func:`zmlx.ui.gui_buffer.add_action` 一致。
        """
        # ★ 2026-10-28：``menu`` 给多级列表、``text`` 却省略时，把 menu 的**最后一级**
        #    当作菜单文字。这是「写法自然」的典型：::
        #
        #        add_action(menu=['帮助', '用户', '管理'], slot=...)
        #
        #    读起来就是「在『帮助 → 用户』下挂一个『管理』」，不必把「管理」再写一遍。
        #
        #    ⚠️ 这段放在**函数最前面**（2026-10-28 从 ``menu is None`` 之后挪来）：
        #    它是**参数规整**，不是处理逻辑 —— 规整完的参数才交给后面的分支去判断。
        #    放最前面有三个好处：
        #      ① 后来的读代码的人一眼就看到「这里会动参数」，不会在下面就着
        #         ``text: None`` 的谜题读半屏才找到答案；
        #      ② 与后面的 ``menu is None → "其它"``、``text`` 校验一起构成完整的前置
        #         规整段（先规整、再校验、最后才建 action），顺序一目了然；
        #      ③ 不必再论证「为什么必须在分隔符之后」—— ``text`` 本为 ``None`` 时
        #         不可能等于 ``'---'``，这段根本改变不了分隔符分支的走向。
        #
        #    只对**长度 ≥ 2** 的序列生效：
        #      - 长度 1（``['操作']``）没有「最后一级」可弹 —— 弹完 menu 就空了，
        #        那正是旧写法 ``add_action(menu='操作')`` 缺 text 的情形，应当照常报错；
        #      - **``tuple`` 同样支持**（2026-10-28 补）：``get_menu`` 对 menu 根本不做
        #        类型检查（只对 str 特判，其余原样当序列用），``_auto_action_name`` 也
        #        是 ``(list, tuple)`` 都认 —— 这里只写 list 会漏掉 tuple。
        #    ⚠️ ``list(menu)`` 一步两用：tuple 没有 ``pop``，且副本保证不改调用者的
        #    对象（否则同一份常量被反复注册时会越弹越短）。
        if (
            text is None
            and isinstance(menu, (list, tuple))
            and len(menu) >= 2
        ):
            menu = list(menu)   # 转 list（tuple 无 pop）+ 副本（不改调用者对象）
            text = menu.pop()   # 最后一级即菜单文字

        if text == "---":
            # 分隔符：只影响菜单，不建 action（见 docstring 的 Note）。
            # ⚠️ 没有 menu 就什么都不做 —— 分隔符必须挂在某个菜单里，不为它凭空造「其它」。
            if menu is not None:
                self.get_menu(menu).addSeparator()
            return

        if menu is None:
            menu = "其它"

        # ★ 2026-10-27：``overwrite`` 取代 ``overwritable``（旧名 2027-10-27 删除）。
        #    两条规矩：
        #    ① 两个都给且**含义相反** → 抛 ``TypeError``，不替调用者猜他想保留哪个
        #       （先判这一步：既然要报错，就不必再发一条与之无关的弃用警告）；
        #    ② 只传旧名 → 发弃用警告，行为与 ``overwrite`` **完全一致**（不改语义）。
        #    ⚠️ 用 ``None`` 作哨兵（而不是默认 ``True``）才能区分「没传」与「传了 False」。
        if (
            overwrite is not None
            and overwritable is not None
            and bool(overwrite) != bool(overwritable)
        ):
            raise TypeError(
                f'add_action 的 overwrite 与 overwritable 不能同时给定且含义相反：'
                f'overwrite={overwrite!r}, overwritable={overwritable!r}'
            )
        if overwritable is not None:
            warn(
                '``add_action(overwritable=...)`` 已弃用（2026-10-27），'
                '请改用 ``overwrite=...``；原名将于 2027-10-27 删除。',
                DeprecationWarning,
                stacklevel=2,
            )
            if overwrite is None:
                overwrite = overwritable
        if overwrite is None:
            overwrite = True

        # ⚠️ ``text`` 必须是「str」或「返回 str 的 callable」—— 它是菜单项的**文字**，
        #    也是自动命名与判重的依据，没有合理的兜底值（旧版会退化成显示 'unnamed'，
        #    那不是给人看的东西）。所以这里**直接抛异常**，不做静默降级，也**不**回落
        #    到 ``name`` 当显示文字（2026-10-26 明确：``text`` 必填；旧写法
        #    ``add_action(menu=..., name='cmd')`` 会当场报错 —— 见 docstring 的 ``text`` 条）。
        #    分隔符（text='---'）已经在上面返回，不会走到这里。
        if not (isinstance(text, str) or callable(text)):
            raise TypeError(
                f'add_action 的 text 是必填项（str 或返回 str 的 callable），'
                f'缺省不再回落到 name 当显示文字；分隔线请用 text="---"：'
                f'menu={menu}, name={name}, text={text!r}'
            )

        if name is None:
            name = self._auto_action_name(menu, text)

        # 撞名处理（只查一次），2026-10-26 起 overwrite=True 的语义是「**就地更新**」：
        #   overwrite=True  → 复用找到的那个 action，按本次参数**重新设置**它的
        #                     slot / icon / tooltip / text / shortcut / 动态回调等，
        #                     不再另挂一条重复条目（菜单里始终只有一条）；
        #   overwrite=False → 只注册一次：撞了就发警告并跳过。
        # ⚠️ 命中的判据是 ``name``（显式给的名字，或按 menu+text 自动算出来的名字），
        #    所以「同名」与「同 menu + 同 text」两种情况都会走到这里。
        existing = self.get_action(name=name)
        if existing is not None:
            if not overwrite:
                warn(
                    f"菜单项已存在，跳过本次注册：menu={menu}, text={text}, name={name}",
                    UserWarning,
                    stacklevel=2,
                )
                return
            else:
                self._update_action(
                    action=existing, menu=menu, text=text, slot=slot, icon=icon,
                    tooltip=tooltip, shortcut=shortcut, on_toolbar=on_toolbar,
                    is_enabled=is_enabled, is_visible=is_visible,
                )
                return

        action = Action(self)
        action.setObjectName(name)
        self._configure_action(
            action=action, menu=menu, text=text, slot=slot, icon=icon,
            tooltip=tooltip, shortcut=shortcut,
            is_enabled=is_enabled, is_visible=is_visible,
            default_icon=True,  # 新建：没给图标就回落到默认图标
        )

        if on_toolbar:
            toolbar_name = menu if isinstance(menu, str) else menu[0]
            self.get_toolbar(toolbar_name).addAction(action)

        target = self.get_menu(menu)
        target.addAction(action)
        # ⚠️ 子菜单的**位置**由 ``get_menu`` 负责（夹在「骨架条目」与「插件后挂条目」
        #    之间，见 :meth:`_sub_menu_insert_after`）；普通条目一律追加到末尾，两者
        #    天然不冲突，这里不需要再挪任何东西。

        # ⚠️ 2026-10-27：新建后也**立即刷新一次视图**，与 :meth:`_update_action` 的收尾
        #    对齐。不刷的话有两处不对：
        #    ① ``text`` 是 callable 时只写了 ``action.get_text``、没 ``setText``，
        #       首帧标题是**空字符串**，要等下一次 ``refresh()`` 才有字；
        #    ② 动态的 ``is_visible`` / ``is_enabled`` 也不会立即生效（``update_view``
        #       才去调它们），新建的条目会带着默认的「可用 + 可见」显示出来。
        #    启动期有 ``refresh()`` 兜底所以看不出来，但运行期由插件新挂的条目会一直
        #    错到下一次刷新为止。⚠️ 用 try 包住：``is_visible`` 等回调是用户代码。
        try:
            action.update_view()
        except Exception as err:
            print(f"Error when update_view after add <{name}>: {err}")

    def _configure_action(
        self, *, action, menu, text, slot, icon, tooltip, shortcut,
        is_enabled, is_visible, default_icon=False,
    ):
        """把「本次 add_action 的参数」应用到 action 上（**新建**与**就地更新**共用）.

        2026-10-26 抽出：``overwrite=True`` 撞名时不再另挂一条，而是把已有 action
        交给本方法**重新设置**，所以这段逻辑只有一份。

        做的事：

        1. 动态回调 ``is_enabled`` / ``is_visible``（传 callable 才设，否则继承原值）；
        2. 图标：给了 ``icon`` 就用它；没给时**只有** ``default_icon=True``（新建）
           才回落到设置里的 ``default_action_icon``，覆盖时保持原图标（见下方 ⚠️）；
        3. ``tooltip`` / ``text`` / ``shortcut``：**给了才覆盖**（``None`` = 保持原样）；
        4. ``slot``：写进 ``action.slot_func``（**替换**，不是追加）—— 见下方的 ⚠️。

        ⚠️ **``default_icon`` 为什么存在**（2026-10-26 修）：新建的 action 没图标难看，
        所以 ``icon=None`` 时给它一个默认图标；但**就地覆盖**时如果也这么做，一个原本
        精心设置了图标的条目会被悄悄换成 ``python`` 图标 —— 与其他参数「``None`` 就
        保持原样」的约定不一致。于是把「要不要回落默认图标」显式化。

        ⚠️ ``text`` 为 str 时顺手清掉 ``action.get_text``：上一次注册可能留下动态标题，
        不清掉的话 :meth:`Action.update_view` 会继续用旧 callable 覆盖新文字。

        Args:
            action: 目标 ``Action``（新建的，或已挂在菜单上的）。
            menu: 菜单路径（只用于日志标签）。
            text: 菜单文字（``str`` 或 callable；已在 ``add_action`` 入口校验过）。
            slot: 点击后执行的动作（经 :meth:`parse_value` 解析）。
            icon: 图标名；``None`` 时**保持原样**（``default_icon=True`` 时回落到默认图标）。
            tooltip: 悬停提示；``None`` 时保持原样。
            shortcut: 快捷键（``str`` 或 ``QKeySequence``）；``None`` 时保持原样。
            is_enabled: 可选的动态回调；不是 callable 时保持原样。
            is_visible: 可选的动态回调；不是 callable 时保持原样。
            default_icon: ``icon`` 为 ``None`` 时是否回落到默认图标（只有**新建**时为 True）。
        """
        name = action.objectName()

        if callable(is_enabled):  # 作为一个函数，动态地判断是否可用
            action.is_enabled = is_enabled

        if callable(is_visible):  # 作为一个函数，动态地判断是否可见
            action.is_visible = is_visible

        if icon is not None:
            action.setIcon(settings.load_icon(icon))
        elif default_icon:  # 新建：没给图标就用设置里的默认图标
            icon = app_data.getenv(key="default_action_icon", default="python")
            if icon is not None:
                action.setIcon(settings.load_icon(icon))

        if tooltip is not None:
            action.setToolTip(settings.get_text(tooltip))

        # text 已在 add_action 入口校验过：一定是 str 或 callable。
        if isinstance(text, str):
            action.get_text = None  # 清掉旧注册可能留下的动态标题
            action.setText(settings.get_text(text))
        else:
            action.get_text = text

        if shortcut is not None:
            if isinstance(shortcut, str):
                action.setShortcut(QtGui.QKeySequence(shortcut))
            else:
                action.setShortcut(shortcut)

        def slot_x():
            try:
                self.parse_value(slot)
                log(f"run <{name}>", tag=f"run <{name}>")
                self.refresh()  # since 2024-10-11
            except Exception as e2:
                info = f"meet error when run <{name}>. \nInfo = \n {e2}"
                print(info)
                log(info, tag=info)

        # ⚠️⚠️ **不要**在这里 ``triggered.connect(slot_x)``：就地覆盖时同一个 action
        #    会被反复注册，每 connect 一次就多挂一个历史槽（Qt 允许重复连接，且
        #    ``disconnect()`` 不带参数断不干净）—— 实测一次点击会把占位函数与插件
        #    函数**全部**跑一遍。做法改为：``Action`` 在构造时只连一条 ``_on_triggered``，
        #    这里只**替换**它的 ``slot_func`` 属性 —— 无论覆盖多少次，都只跑最新的槽。
        action.slot_func = slot_x

    def _update_action(
        self, *, action, menu, text, slot, icon, tooltip, shortcut,
        on_toolbar, is_enabled, is_visible,
    ):
        """``overwrite=True`` 撞名时：**就地更新**已有的 action，不新建条目.

        2026-10-26 改：此前撞名会另起一个 ``<原名>_001`` 再挂一条，菜单里出现两个
        一模一样的条目 —— 那不是「覆盖」，只是一次意外重复。现在的语义是真正的覆盖：

        - 用本次参数重设 action 的 slot / icon / tooltip / text / shortcut / 动态回调；
        - 它**留在原来的菜单位置**（不移动、不重复挂载）；
        - 若本次要求 ``on_toolbar`` 而它还没在工具栏上，就补挂上去。

        Args:
            action: 已存在的 ``Action``（``get_action(name=...)`` 找到的那个）。
            menu: 本次调用的菜单路径。
            text: 本次调用的菜单文字。
            slot: 本次调用的槽。
            icon: 本次调用的图标名。
            tooltip: 本次调用的悬停提示。
            shortcut: 本次调用的快捷键。
            on_toolbar: 本次是否要求挂到工具栏。
            is_enabled: 本次的动态回调（可用）。
            is_visible: 本次的动态回调（可见）。
        """
        self._configure_action(
            action=action, menu=menu, text=text, slot=slot, icon=icon,
            tooltip=tooltip, shortcut=shortcut,
            is_enabled=is_enabled, is_visible=is_visible,
        )

        if on_toolbar:
            toolbar_name = menu if isinstance(menu, str) else menu[0]
            toolbar = self.get_toolbar(toolbar_name)
            # ⚠️ 同一个 action 往同一个工具栏加两次，Qt 会把它挪到末尾 —— 先查一遍。
            if action not in toolbar.actions():
                toolbar.addAction(action)

        # 让「动态启用 / 可见 / 标题」立即体现，而不是等下一次 refresh()。
        try:
            action.update_view()
        except Exception as err:
            print(f"Error when update_view after overwrite <{action.objectName()}>: {err}")

    @staticmethod
    def _callable_id(obj):
        """返回一个 callable 的**稳定标识**字符串（用于生成自动 action 名）.

        优先用 ``__module__ + __qualname__``（同一份代码重复执行时不变），取不到时
        退回 ``id(obj)``（只在本次进程内稳定）。⚠️ **绝不能调用这个 callable** ——
        像「通知(3)」这种标题每次刷新都会变，一旦拿返回值当名字，判重就时灵时不灵。

        ⚠️ **``__qualname__`` 本身不唯一**（2026-10-27 修）：同一函数体内定义的多个
        lambda，``__qualname__`` 全是 ``f.<locals>.<lambda>``；不同实例的同名绑定方法
        也全是 ``C.label``。只按限定名生成标识，会让它们在**同一个菜单**里撞成同一个
        名字 —— 后注册的那条于是静默覆盖前一条（菜单里只剩一项，点击跑的是后者的槽，
        且不发任何警告）。所以再拼两段区分信息：

        - ``__code__.co_firstlineno``：同一函数体内**不同行**的 lambda 因此区分得开；
          同一个 lambda 被重复执行（插件 setup 跑两遍）行号不变，判重照常生效；
        - ``id(__self__)``：只有**绑定方法**带 ``__self__``，用来区分不同实例
          （同一实例在同一进程内 id 稳定，判重仍成立）。

        ⚠️ ``functools.partial`` 之类既没有 ``__qualname__`` 也没有 ``__code__``，
        会退回 ``id(obj)`` —— 那种标识**只在本次进程内**稳定，每次新建一个 partial
        再注册都会被当成新条目，无法判重。

        Args:
            obj: 任意 callable。

        Returns:
            str: 标识字符串。
        """
        qualname = getattr(obj, "__qualname__", None)
        if isinstance(qualname, str) and len(qualname) > 0:
            parts = [f"{getattr(obj, '__module__', '')}.{qualname}"]
            code = getattr(obj, "__code__", None)
            if code is not None:
                parts.append(f"L{code.co_firstlineno}")
            self_obj = getattr(obj, "__self__", None)
            if self_obj is not None:
                parts.append(f"self_{id(self_obj)}")
            return ".".join(parts)
        return f"id_{id(obj)}"

    def _auto_action_name(self, menu, text):
        """没有给 ``name`` 时，按 ``menu`` + ``text`` 自动算一个 action 名字.

        ★ 2026-10-26 新增，被 :meth:`add_action` 在**函数最前面**调用（任何情况下
        ``name is None`` 都会先走这里），于是后续流程（判重、``setObjectName``）
        拿到的永远是一个字符串，不再有「名字可能为空」的分支。

        规则：

        ============  ========================================  ==================
        ``text``       生成的 ``objectName``                      稳定性
        ============  ========================================  ==================
        ``str``         ``auto_<sha256(menu 路径 + text) 前 30 位>``   同 menu + 同文字 → 同名
        callable        ``auto_<sha256(menu 路径 + callable 标识)>``   同 menu + 同函数 → 同名
        ============  ========================================  ==================

        ⚠️ 其它取值（包括 ``None``）**直接抛 ``ValueError``** —— 不做 ``'unnamed'`` 之类的
        兜底（2026-10-26 改）：菜单文字没有合理的默认值，``:meth:`add_action` 在入口
        已经把这种情况挡掉了，这里再兜一次是为了防止有人绕过入口调用本方法。

        ⚠️ **callable 分支用的是「身份」（模块名 + 限定名 + 定义行号 [+ 绑定实例]），
        绝不是调用它** —— 见 :meth:`_callable_id`：带计数的标题每刷新一次就变一次，
        用返回值当名字会让判重失效。⚠️ 只取限定名**不够**（2026-10-27 修）：同一函数体
        内的多个 lambda 限定名相同，会被错认成同一个，后者静默覆盖前者。

        ⚠️ **进哈希的是 ``menu`` 的原文，不做 ``settings.get_text`` 翻译**（2026-10-26
        更正）：翻译是**有损**的（多个原文可能翻成同一个译文），拿它生成唯一标识会让
        两个不同的菜单路径撞成同一个名字、判重时误丢条目；而「同一次调用」的原文是
        固定的，不翻译反而恒等。何况 ``ui_text`` 运行期可改 —— 翻译过的名字会随它漂移。

        Args:
            menu: 菜单路径（``None`` / ``str`` / ``list``）。
            text: 菜单文字（``str`` / callable）。

        Returns:
            str: 自动生成的名字。

        Raises:
            ValueError: ``text`` 既不是 ``str`` 也不是 callable。
        """
        if menu is None:
            keys = ["其它"]
        elif isinstance(menu, str):
            keys = [menu]
        elif isinstance(menu, (list, tuple)):
            keys = list(menu)
        else:
            keys = [str(menu)]

        if isinstance(text, str):
            return "auto_" + get_hash("_".join(keys + [text]))
        if callable(text):
            return "auto_" + get_hash("_".join(keys + [self._callable_id(text)]))
        raise ValueError(f"无法根据 text={text!r} 生成 action 名字（menu={menu}）")

    def get_action(self, name, create_empty=None):
        """
        返回给定 name（即 ``QAction.objectName()``）的菜单 action.

        Args:
            name: action 的 ``objectName``。⚠️ 为了兼容历史写法，除了精确匹配，
                也接受 ``name + '.py'``（同一动作在旧代码里有过这两种名字）。
            create_empty: **已弃用（2026-10-26，2027-10-26 删除）**。

                - 旧版为 ``True``（默认）时：找不到就**发一条警告并返回一个从未
                  挂到任何菜单上的空 ``Action``** —— 调用者拿到它再 ``trigger()``
                  什么也不会发生，属于误导性的默认行为；
                - 现在**统一**为「只查找」：找不到就返回 ``None``。

                该分支在全仓**从未被真实使用**（唯一的默认值消费者
                :meth:`trigger` 本身零调用），所以直接改了默认值。为了给外部脚本
                留出过渡期，**只要显式传了这个参数**（传 ``True`` 或 ``False`` 都算）
                就发一条 ``DeprecationWarning``；``zmlx`` 内部已全部改为不传。

        Returns:
            Action | None: 找到返回 action，找不到返回 ``None``。
        """
        if create_empty is not None:
            warn(
                "``get_action(create_empty=...)`` 已弃用（2026-10-26）：找不到时"
                "现在总是返回 None，不可再创建空 action；该参数将于 2027-10-26 "
                "删除，请直接调用 ``get_action(name)``。",
                DeprecationWarning,
                stacklevel=2,
            )
        if isinstance(name, str):
            # ⚠️ 只查 ``Action``（即 add_action 创建的菜单项），不查全部 QAction
            #    （2026-10-26 改）：``findChildren(QAction)`` 还会带上**菜单自身**的
            #    menuAction（'文件' / '操作' …）与工具栏按钮 —— 它们的 objectName 全是
            #    空串，于是 ``get_action('')`` 会命中一个菜单 action；而且那不是
            #    add_action 建的对象，既没有 update_view 也没有 slot_func。
            for action in self.findChildren(Action):
                if action.objectName() == name or action.objectName() == name + ".py":
                    return action
        return None

    def list_actions(self):
        """返回所有由 :meth:`add_action` 创建的 action 的名字（``objectName``）.

        ⚠️ 只列 ``Action``（2026-10-26 改）：菜单自身的 menuAction 与工具栏按钮
        都不是 ``add_action`` 建的，不该出现在这份清单里。
        """
        names = []
        for action in self.findChildren(Action):
            name = action.objectName()
            if isinstance(name, str):
                if len(name) > 0:
                    names.append(name)
        return names

    def trigger(self, name):
        """
        触发给定的Action（按 ``objectName`` 查找）.

        ⚠️ 找不到时**明确发一条警告**：``get_action`` 现在找不到就返回 ``None``
        （2026-10-26 起不再创建空 action），若这里静默返回，用户看到的会是
        「调了 trigger 却毫无反应」，无从判断是名字写错还是 action 不存在。
        """
        action = self.get_action(name)
        if action is None:
            warn(
                f"cannot find the action with name: <{name}>",
                UserWarning,
                stacklevel=2,
            )
        elif hasattr(action, "trigger"):
            action.trigger()

    def show_next(self, position=None):
        self.get_tab_widget(position=position).show_next()

    def show_prev(self, position=None):
        self.get_tab_widget(position=position).show_prev()

    def count_tabs(self, position=None):
        """
        返回标签的数量
        """
        return self.get_tab_widget(position=position).count()

    def close_all_tabs(self, position=None):
        """
        关闭所有的标签
        """
        self.get_tab_widget(position=position).close_all_tabs()

    def close_tab_object(self, widget, position=None):
        """
        关闭给定对象的标签页面
        """
        return self.get_tab_widget(position=position).close_tab_object(widget)

    def get_tab_caption(self, index, position=None):
        """
        返回给定位置tab的Caption
        """
        return self.get_tab_widget(position=position).tabText(index)

    def set_tab_caption(self, index, caption, position=None):
        """
        设置tab的文本
        """
        self.get_tab_widget(position=position).setTabText(index, caption)

    def exec_tab_func(self, name, *, position=None):
        widget = self.get_current_widget(position=position)
        if hasattr(widget, name):
            f = getattr(widget, name)
            f()

    def get_tab_widgets(self):
        """
        返回所有的标签页容器。

        注意：左侧标签页列已经被移除，这里只返回[顶部, 右侧]两个容器。
        """
        return [self.top_tabs, self.right_tabs]

    @staticmethod
    def _warn_deprecated(message, stacklevel):
        """
        给出一个警告（同时记录日志）。仅用于参数/行为被废弃的场景。

        Args:
            message: 警告的文本
            stacklevel: 调用栈的深度(用于正确的定位调用者)
        """
        try:
            warn(message, UserWarning, stacklevel=stacklevel)
        except Exception:
            pass

    def _parse_position(self, at_side=False, position=None, stacklevel=4):
        """
        解析position(以及已经废弃的at_side)，返回最终的标签页位置。

        返回值保证只有'top'和'right'两种形式：
        'right'表示右侧，其余所有情况(包括None和其它的取值)都表示顶部。

        以下两种情况会给出警告：
        (1) position为None而at_side为真值：at_side已经废弃，请改用position
        (2) position为'left'：左侧列已经移除，将使用右侧的标签页来代替

        Args:
            at_side: 【已废弃】是否使用侧边的标签页。请改为使用position
            position: 标签页的位置，给定时必须是'top'或者'right'
            stacklevel: 警告的调用栈深度(用于正确的定位调用者)

        Returns:
            最终的位置，'top'或者'right'
        """
        if not isinstance(position, str):  # 没有给定位置：解析(已经废弃的)at_side
            if at_side:
                self._warn_deprecated(
                    "The keyword <at_side> is deprecated: "
                    "use <position> ('top' or 'right') instead.",
                    stacklevel,
                )
                return "right"
            return "top"  # 默认使用顶部的标签页
        if position == "right":
            return "right"
        if position == "top":
            return "top"
        elif position == "left":  # 左侧列已经被移除，警告并且使用右侧来代替
            self._warn_deprecated(
                "The keyword <position='left'> is deprecated: the left column of the "
                "main window has been removed, and the right tabs will be used instead.",
                stacklevel,
            )
            return "right"
        else:
            raise ValueError(f"position must be 'top' or 'right', got <{position}>")

    def get_tab_widget(self, *, position=None, at_side=False):
        """
        返回给定位置的标签页容器（公开函数，接口保持不变）。

        Args:
            position: 标签页的位置，'top'或者'right'。'left'已经被移除，
                为了兼容旧代码，此时会警告，并返回右侧的标签页。
            at_side: 【已废弃】是否使用侧边的标签页。请改为使用position。
                仅在position为None的时候生效；此时若为真值，则使用右侧的标签页。

        Returns:
            给定位置的TabWidget对象
        """
        position = self._parse_position(at_side=at_side, position=position)
        if position == "right":
            return self.right_tabs
        else:
            return self.top_tabs

    def get_tabs(self, at_side=False):
        """
        返回标签页容器。at_side为True时返回侧边(右侧)的标签页容器，否则返回顶部的。
        """
        return self.get_tab_widget(position="right" if at_side else "top")

    def cls(self):
        self.get_output_widget().set_text("")

    def show_status(self, *args, **kwargs):
        self.statusBar().showMessage(*args, **kwargs)

    def console_state(self, text):
        """在状态栏的版本按钮上显示控制台运行状态（空串 = 恢复显示版本号）.

        ⚠️⚠️ **2026-10-26 起主窗口自己不再调它**：运行状态改由状态栏的**运行状态灯**
        （:class:`~zmlx.ui.widgets.run_state_light.RunStateLight`）显示，版本按钮
        **只属于版本号**。本方法**保留**只是为了不破坏外部调用方（它是公开方法，
        且被自动注册成 ``gui.console_state``）—— 行为与以前完全一样：写的就是版本按钮。

        新代码请直接调状态灯：``gui.window().run_state_light.set_state('running')``
        （状态名见 :mod:`zmlx.ui.widgets.run_state_light`），或改 :meth:`refresh` 里
        那段状态判断 —— 那里才是「谁在什么时候更新状态灯」的唯一来源。

        Args:
            text: 要显示的文本；超过 20 字符会被截断。
        """
        if not isinstance(text, str):
            text = str(text)
        if len(text) > 20:
            text = text[:20] + "..."
        self.version_button.setText(text)

    def set_title(self, title):
        self.title = title
        self.refresh()

    @staticmethod
    def toolbar_warning(text=None):
        if isinstance(text, str):
            if len(text) > 0:
                try:
                    gui.add_message(text, color="red")  # 警告
                except Exception:
                    print(text)

    def get_console(self):
        return self.console

    def is_running(self):
        return self.console.is_running()

    def is_paused(self):
        return self.console.get_pause()

    def set_paused(self, value):
        if self.is_running():
            self.console.set_pause(value)

    def stop_console(self):
        if self.is_running():
            self.console.stop()

    def start_last(self):
        self.console.start_last()

    def set_side_tabs_visible(self, visible: bool):
        """显示 / 隐藏右侧栏（顶部标签页区之外的那一栏，控制台常驻其中）.

        ★ 2026-10-26：**宽度记忆**。隐藏后 ``splitter.sizes()`` 里那一项是 0，所以：

        - **隐藏前**先把当前宽度记到 ``self._last_console_width``；
        - **显示时**按记下的宽度还原（用户拖出来的宽度不该因为一次隐藏就丢掉）；
        - 关窗时由 ``__on_close`` → ``settings.save_console_width`` 存盘，下次启动
          ``init_splitter_sizes`` 恢复。

        ⚠️ 菜单「操作 → 隐藏/显示」与公开方法 ``gui.set_console_visible`` 走的都是这里。
        """
        if not visible:
            try:
                sizes = self.splitter.sizes()
                if len(sizes) >= 2 and sizes[1] > 0:
                    self._last_console_width = int(sizes[1])
            except Exception as err:
                print(f"Error: {err}")
        self.right_tabs.setVisible(visible)
        if visible:
            try:
                width = getattr(self, "_last_console_width", None)
                if isinstance(width, int) and width > 0:
                    total = self.splitter.width()
                    if total > 0:
                        self.splitter.setSizes([max(1, total - width), width])
            except Exception as err:
                print(f"Error: {err}")
        self.refresh()  # 刷新窗口

    def set_console_visible(self, visible: bool):
        """
        设置控制台是否可见
        """
        self.set_side_tabs_visible(visible)

    def hide_console(self):
        """
        隐藏控制台
        """
        self.set_console_visible(False)

    def show_console(self):
        """
        显示控制台
        """
        self.set_console_visible(True)

    def click_pause(self):
        """
        在界面上点击暂停按钮
        """
        if self.is_running():
            self.console.set_pause(True)

    def exec_file(self, filename):
        self.console.exec_file(filename)

    def start_func(self, *args, **kwargs):
        """
        在控制台执行代码
        """
        self.console.start_func(*args, **kwargs)

    def exec_current(self, position=None):
        widget = self.get_current_widget(position=position)
        if isinstance(widget, CodeEdit):
            widget.save()
            self.console.exec_file(widget.get_fname())
        else:
            self.console.exec_file()

    def kill_thread(self):
        if self.console.thread is not None:
            reply = QtWidgets.QMessageBox.question(
                self,
                "杀死进程",
                "强制结束当前进程，可能会产生不可预期的影响，是否继续?",
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                if self.console.thread is not None:
                    thread = self.console.thread
                    thread.sig_done.emit()
                    thread.terminate()

    def refresh_action(self, name=None):
        """
        刷新给定的Action或者所有的Action
        """
        if name is None:
            for action in self.findChildren(QAction):
                if callable(update_view := getattr(action, "update_view", None)):
                    try:
                        update_view()
                    except Exception as err:
                        print(err)
        else:
            action = self.get_action(name=name)
            if callable(update_view := getattr(action, "update_view", None)):
                try:
                    update_view()
                except Exception as err:
                    print(err)

    def __refresh_cwd_view_if_any(self):
        """工作路径变了：若「浏览」页存在就刷新它（2026-10-22）.

        ⚠️ 「浏览」页（`CwdView`）已搬进插件 `plugins/builtin/viewers.py`，
        `view_cwd` 不再是本类的方法。所以
        :attr:sig_cwd_changed 连的是本函数，由它**按命令名**去调 ——

        ⚠️ 插件未加载 / 被禁用时，``gui.view_cwd`` 由
        ``extra_setups/plugin_placeholders.py`` 的**占位**顶上：它只打印一句「请先启用
        插件」的提示、**什么都不做**，所以这里不会再报 `not found`，也不会误开标签页。
        ⚠️ 但仍然用 `gui.get_func` 判断、**不要** `try: gui.view_cwd() except`：
        后者会把命令内部真正的异常也一起吞掉，排查时看不出是「没这个命令」还是
        「这个命令自己报错了」。这个判断现在只防「gui 尚未接好」这类极端情况。
        """
        from zmlx.ui import gui as _gui

        if not _gui.exists():
            return
        if _gui.get_func("view_cwd") is None:
            return  # gui 不可用（正常启动后插件命令或占位总有一个）
        try:
            _gui.view_cwd()
        except Exception as err:
            print(f"Error when refresh cwd view: {err}")

    def refresh(self):
        """
        尝试刷新标题以及当前的页面
        """
        if self.title is not None:
            self.setWindowTitle(f"{self.title}")
        else:
            self.setWindowTitle(f"WorkDir: {os.getcwd()}")

        try:  # 尝试刷新当前的页面（在定义refresh函数的情况下）
            current = self.get_current_widget()
            if hasattr(current, "refresh"):
                self.task_proc.add(lambda: current.refresh())
        except Exception as err:
            print(f"Error: {err}")

        self.refresh_action()

        # 顺带刷新状态栏右下角的授权状态（**读缓存**，见 update_system_state）
        try:
            self.update_system_state()
        except Exception as err:
            print(f"Error: {err}")

        # 调用刷新
        if not self.is_running():
            self.get_output_widget().progress(visible=False)
            self.show_attrs(copy_to_tab="动态属性")
            self.show_attrs(clear=True)

        running = self.is_running()
        pause = self.is_paused()

        # 控制台运行状态：显示在状态栏的**运行状态灯**上（圆点 + 文字）。
        # ⚠️ 2026-10-26：原先这里是 ``self.console_state('控制台：运行中')`` —— 往版本按钮
        #    那一格写状态，等于让版本号一物两用。现在改走 ``run_state_light``，
        #    版本按钮**只显示版本号**。⚠️ ``console_state`` 方法本身**保留**（公开方法，
        #    外部脚本可能还在调），只是主窗口自己不再调它。
        if not running:
            self.run_state_light.set_state(STATE_IDLE)
        elif pause:
            self.run_state_light.set_state(STATE_PAUSED)
        else:
            self.run_state_light.set_state(STATE_RUNNING)

        if running:
            self.get_output_widget().text_browser.setStyleSheet(
                "QTextBrowser {border: 1px solid red;}"
            )
        else:
            self.get_output_widget().text_browser.setStyleSheet(
                "QTextBrowser {border: 0px solid red;}"
            )

    def find_widget(
        self, the_type=None, text=None, is_ok=None, *, at_side=False, position=None
    ):
        """
        返回给定条件的Widget。给定的所有条件需要同时满足
        Args:
            at_side: 【已废弃】是否在侧边栏查找。请改为使用position
            the_type: 控件的类型
            text: 标题
            is_ok: 一个函数，用于检查控件对象
            position: 标签页的位置，'top'或者'right'

        Returns:
            符合条件的Widget对象，否则返回None
        """
        position = self._parse_position(at_side=at_side, position=position)
        return self.get_tab_widget(position=position).find_widget(
            the_type=the_type, text=text, is_ok=is_ok
        )

    def find_widgets(
        self, the_type=None, text=None, is_ok=None, *, at_side=False, position=None
    ):
        """
        返回所有符合条件的Widget。给定的所有条件需要同时满足
        Args:
            at_side: 【已废弃】是否在侧边栏查找。请改为使用position
            the_type: 控件的类型
            text: 标题
            is_ok: 一个函数，用于检查控件对象
            position: 标签页的位置，'top'或者'right'

        Returns:
            符合条件的Widget对象列表，否则返回空列表
        """
        position = self._parse_position(at_side=at_side, position=position)
        return self.get_tab_widget(position=position).find_widgets(
            the_type=the_type, text=text, is_ok=is_ok
        )

    def get_widget(self, *args, at_side=False, position=None, **kwargs):
        """
        返回(如果需要则创建)给定条件的Widget。

        Args:
            at_side: 【已废弃】是否使用侧边栏。请改为使用position
            position: 标签页的位置，'top'或者'right'
        """
        position = self._parse_position(at_side=at_side, position=position)
        tab_widget = self.get_tab_widget(position=position)
        if not tab_widget.isVisible():  # 确保可见
            tab_widget.setVisible(True)
        return tab_widget.get_widget(*args, **kwargs)

    def get_figure_widget(self, init=None, folder_save=None, position=None, **kwargs):
        """
        返回一个用以 matplotlib 绘图的控件
        """
        return self.get_tab_widget(position=position).get_figure_widget(
            init=init, folder_save=folder_save, **kwargs
        )

    def get_plot_widget(self, *, position=None, at_side=False, **kwargs):
        """
        创建 / 复用一页 matplotlib 画布，返回该控件（**必须在 GUI 线程调用**）。

        给 `GuiBuffer.plot` 用：整条绘图链里**只有**「建标签页」这件事非 GUI 线程
        做不了（约 1 ms）；真正的渲染由调用方在自己的线程完成，见
        `MatplotWidget.plot_on_figure`。

        Args:
            position: 标签页的位置（'top' 或 'right'）
            at_side: 【已废弃】是否使用侧边的标签页
            **kwargs: 传给 `TabWidget.get_figure_widget`
                （caption / on_top / icon / folder_save / init ...）

        Returns:
            绘图控件（`MatplotWidget`），创建失败时为 None
        """
        return self.get_tab_widget(
            position=position, at_side=at_side
        ).get_figure_widget(**kwargs)

    def plot(
        self,
        kernel,
        *args,
        fname=None,
        dpi=None,
        caption=None,
        on_top=None,
        icon=None,
        clear=None,
        tight_layout=None,
        suptitle=None,
        folder_save=None,
        position=None,
        **kwargs,
    ):
        """
        调用matplotlib执行绘图操作 注意，此函数会创建或者返回一个标签，并默认清除标签的绘图，返回使用回调函数
        在figure上绘图。
        Args:
            kernel: 绘图的回调函数，函数的原型为：
                def kernel(figure, *args, **kwargs):
                    ...
            fname: 输出的文件名
            dpi: 输出的分辨率
            *args: 传递给kernel函数的参数
            **kwargs: 传递给kernel函数的关键字参数
            caption: 窗口的标题
            on_top: 是否置顶
            icon: 窗口的图标
            clear: 是否清除之前的内容 (特别注意，默认是要清除之前的内容的，因此，如果要多个视图的时候，就不要使用clear)
            tight_layout: 是否自动调整子图参数，以防止重叠
            suptitle: 图表的标题
            folder_save: 自动保存图的文件夹
            position: 标签页的位置

        Returns:
            None
        """
        return self.get_tab_widget(position=position).plot(
            kernel,
            *args,
            fname=fname,
            dpi=dpi,
            caption=caption,
            on_top=on_top,
            icon=icon,
            clear=clear,
            tight_layout=tight_layout,
            suptitle=suptitle,
            folder_save=folder_save,
            **kwargs,
        )

    # ⚠️ ``show_fn2`` 2026-10-22 **已搬到插件** ``plugins/builtin/fn2_view.py``
    #    （默认启用）：方法、``Fn2Widget`` 控件、``.fn2`` 文件类型都在那边，
    #    那个插件现在**完全自含**。
    #    ⚠️ 它**一直是弃用的**（方法体里有 ``warn('gui.show_fn2 will be removed after
    #    2026-3-5, please use zmlx.plt.show_fn2 instead')``）—— 那条警告搬过去时**原样保留**。
    #    ⚠️ 本类**不留方法**；占位在 ``extra_setups/plugin_placeholders.py``。

    # ⚠️ `view_cwd` 2026-10-22 **已搬到插件** `plugins/builtin/viewers.py`
    #    （默认启用）：方法、`CwdView` 控件与「文件 → 浏览 → 工作目录」菜单项都在那边
    #    （2026-10-26 起收进「浏览」子菜单，与「图片」并列）；本类**不留方法**；
    #    占位在 ``extra_setups/plugin_placeholders.py``。

    def progress(
        self,
        label: Optional[str] = None,
        val_range: Optional[Union[List[int], Tuple[int, int]]] = None,
        value: Optional[int] = None,
        visible: Optional[bool] = None,
        duration=None,
    ):
        """
        显示进度
        """
        if duration is not None:
            warn("duration will not be used in future")
        return self.get_output_widget().progress(
            label=label, val_range=val_range, value=value, visible=visible
        )

    def show_attrs(self, copy_to_tab=None, **attrs):
        """
        在控制台运行的时候显示一些动态属性
        """
        if len(attrs) > 0:
            self.get_output_widget().show_attrs(**attrs)
        if isinstance(copy_to_tab, str):
            data = self.get_output_widget().attr_view.get_data().copy()
            if len(data) > 0:
                from zmlx.ui.widgets.attr_view import AttrView

                def oper(w: AttrView):
                    w.show_attrs(**data)

                self.get_widget(
                    the_type=AttrView,
                    caption=copy_to_tab,
                    on_top=False,
                    oper=oper,
                    position="right",
                    tooltip="控制台动态属性的拷贝",
                )

    def open_code(self, fname, caption=None, position=None):
        if not isinstance(fname, str):
            return
        tab_widget = self.get_tab_widget(position=position)

        def get_widget(name_1):
            for i in range(tab_widget.count()):
                widget_ = tab_widget.widget(i)
                if isinstance(widget_, CodeEdit):
                    if samefile(name_1, widget_.get_fname()):
                        return widget_
                    return None
                return None
            return None

        if len(fname) > 0:
            widget = get_widget(fname)
            if widget is not None:
                tab_widget.setCurrentWidget(widget)
                return
            else:

                def oper(x):
                    x.open(fname)
                    kwds = dict(fname=fname, caption=caption, position=position)
                    x.gui_restore = f"""gui.open_code(**{kwds!r})"""  # 用于重启

                if caption is None:
                    caption = os.path.basename(fname)

                self.get_widget(
                    the_type=CodeEdit,
                    caption=caption,
                    on_top=True,
                    oper=oper,
                    icon="python",
                    tooltip="代码编辑窗口，点击工具栏的运行按钮可以执行",
                )
                if app_data.getenv("show_info_after_code_open", default="") != "No":
                    print(
                        f"文件已打开: \n\t{fname}\n\n请点击工具栏上的<运行>按钮以运行!\n\n"
                    )

    def open_text(self, fname, caption=None, position=None):
        from zmlx.ui.tabs import TextFileEdit

        if not isinstance(fname, str):
            return
        if len(fname) > 0:

            def oper(x: TextFileEdit):
                x.set_fname(fname)
                kwds = dict(fname=fname, caption=caption, position=position)
                x.gui_restore = f"""gui.open_text(**{kwds!r})"""  # 用于重启

            tab_widget = self.get_tab_widget(position=position)

            for i in range(tab_widget.count()):
                widget = tab_widget.widget(i)
                if isinstance(widget, TextFileEdit):
                    if samefile(fname, widget.get_fname()):
                        tab_widget.setCurrentWidget(widget)
                        oper(widget)
                        return

            if caption is None:
                caption = os.path.basename(fname)

            self.get_widget(
                the_type=TextFileEdit,
                caption=caption,
                on_top=True,
                oper=oper,
            )

    def open_image(self, fname, caption=None, on_top=True):
        """用 :class:`~zmlx.ui.tabs.img.ImageView` 打开（或切到）一个图片标签页.

        Args:
            fname: 图片路径。不是 ``str`` 或文件不存在时**什么都不做**（保持一致的历史行为）。
            caption: 标签页标题；缺省用文件名。
            on_top: 是否置顶。

        ⚠️ **本方法 2026-10-22 曾搬进插件** ``plugins/builtin/image_browser.py``，
        同日**还原**：它是**底层能力**，不该随插件开关而消失 —— 打开标签页 / 恢复标签页
        这类「主窗口骨架本来就要有」的动作，不能被插件是否启用左右。
        （它当年的一项**使用者**「启动即显示欢迎页」已于 2026-10-28 删除，但理由不变：
        ``readme_browser`` 显示二维码、``plugins/builtin/image_browser.py``、以及
        ``gui_restore`` 的重放都依赖它。）

        ⚠️ ``gui_restore`` 里写的是 ``gui.open_image(**{...})``：命令名与参数名都不能改。
        """
        if isinstance(fname, str):
            if os.path.isfile(fname):
                from zmlx.ui.tabs.img import ImageView

                def oper(x):
                    x.set_image(fname)
                    kwds = dict(fname=fname, caption=caption, on_top=on_top)
                    # ⚠️ 必须 ``!r``：``caption`` 是**字符串**，直接插进 f-string 会生成
                    #    不带引号的 ``caption=Welcome``（路径里的反斜杠也会被写坏），
                    #    下次启动 ``gui_restore`` 重放时就抛 ``NameError``。
                    #    ``open_code`` / ``open_text`` 同此（2026-10-28 一并修正）。
                    x.gui_restore = f"""gui.open_image(**{kwds!r})"""  # 用于重启

                if caption is None:
                    caption = os.path.basename(fname)

                self.get_widget(
                    the_type=ImageView, caption=caption, on_top=on_top, oper=oper
                )

    # ⚠️ ``open_pdf`` 2026-10-22 **已移除**（``MainWindow`` 不再提供它，也不再注册
    #    ``.pdf`` 文件处理器）。PDF 查看依赖**可选库** ``QWebEngineView``，与核心骨架无关。
    #    ⚠️ 如果将来要把「用浏览器打开 PDF」加回来，请做成**插件**（放到
    #    ``ui/plugins/builtin/``，或在 ``scen/<包>/zml_plugin.py``），并在插件里自己
    #    ``gui.add_func('open_pdf', ...)`` —— 它原来之所以是 ``gui.open_pdf``，靠的是
    #    本类「所有公开方法自动注册」这条规则，方法搬走/删除后命令名会一起消失。

    def new_code(self):
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            caption="新建.py脚本",
            directory=os.getcwd(),
            filter="Python File (*.py)",
        )
        self.open_code(fname)

    def new_file(self):
        return self.file_handler.new_file_by_dlg(folder=os.getcwd())

    def add_file_handler(self, desc, exts, func):
        if callable(func):
            open_file = func
            new_file = None
        else:
            open_file = func.get("open_file", None)
            new_file = func.get("new_file", None)
        return self.file_handler.add(
            desc=desc, exts=exts, open_file=open_file, new_file=new_file
        )

    def open_file(self, filepath):
        return self.file_handler.open_file(filepath)

    def open_file_by_dlg(self, folder=None):
        return self.file_handler.open_file_by_dlg(folder=folder)

    def set_cwd(self, folder):
        if isinstance(folder, str):
            if os.path.isdir(folder):
                if has_permission(folder):
                    try:
                        os.chdir(folder)
                        settings.save_cwd()
                        self.sig_cwd_changed.emit(os.getcwd())
                    except Exception as err:
                        print(f"Error: {err}")

    def set_cwd_by_dialog(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, settings.get_text("请选择工程文件夹"), os.getcwd()
        )
        self.set_cwd(folder)

    def get_current_widget(self, position=None):
        """
        返回当前的标签对象
        """
        tab_widget = self.get_tab_widget(position=position)
        return tab_widget.currentWidget()

    def get_current_tab_index(self, position=None):
        """
        返回当前标签的序号
        """
        tab_widget = self.get_tab_widget(position=position)
        return tab_widget.currentIndex()

    def get_output_widget(self) -> "OutputWidget":
        if self.__output_widget is None:
            self.__output_widget = self.right_tabs.get_widget(
                OutputWidget, caption="控制台", closeable=False, icon="console"
            )
        assert isinstance(self.__output_widget, OutputWidget), (
            "OutputWidget is not found"
        )
        return self.__output_widget

    def get_output_text(self):
        if self.__output_widget is not None:
            return self.__output_widget.get_plain_text()
        else:
            return ""

    def get_output_html(self):
        if self.__output_widget is not None:
            return self.__output_widget.get_html()
        else:
            return ""

    def add_task(self, task):
        self.task_proc.add(task)

    def get_gui_api(self):
        return self.gui_api

    def check_license(self):
        """
        检查本机授权（旧的「USB / 序列号」授权），未授权时在工具栏弹一句红字警告。

        ⚠️ **已弃用**（用户 2026-10-05 要求）：授权已迁移到 web 授权
        （``zmlx.exts.web_license``，见状态栏右下角与「关于」页面），本方法读的
        ``lic.valid`` 是**旧的**本机授权判据，对已用 web 授权注册的用户会误报。
        因此它**不再有任何自动触发点**（原先的启动检查与 ``show_about`` 里的调用
        都已移除），保留只是为了不破坏既有调用方。

        ⚠️ 本方法还会取网络时间（``lic.valid`` → ``is_expired`` → ``os::webtime``），
        离线时可能被判过期 —— 这正是它被弃用的原因之一。
        """
        warn(
            "MainWindow.check_license() is deprecated (will be removed after 2027-10-05), "
            "the license is now checked by the web license "
            "(see zmlx.exts.web_license and the status bar). This method will be removed.",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            while core.has_log():
                core.pop_log()
            if not lic.valid:
                while core.has_log():
                    print(core.pop_log())
                print("\n\n")
                self.toolbar_warning(
                    "此电脑未登录，请确保: 1、使用最新版；2、本机联网!"
                )
        except Exception as err:
            print(f"Error: {err}")

    def show_about(self):
        f = app_data.get("show_about")
        if callable(f):
            f()
        else:
            from zmlx.ui.tabs import About

            def oper(widget):
                widget.gui_restore = """gui.show_about()"""

            self.get_widget(
                the_type=About, caption="关于", on_top=True, icon="info", oper=oper
            )

    def play_sound(self, filename):
        """
        播放声音
        """
        if isinstance(filename, str):
            if not os.path.isfile(filename):
                filename = settings.find_sound(filename)
                if filename is None:
                    return
            if os.path.isfile(filename):
                self.sig_play_sound.emit(filename)

    # ⚠️ `show_tab_details` 2026-10-22 **已搬到插件** `plugins/builtin/viewers.py`
    #    （默认启用）：方法与 `TabDetailView` 控件、「显示 → 标签列表」菜单项都在那边；
    #    本类**不留方法**；占位在 ``extra_setups/plugin_placeholders.py``。
    #    ⚠️ 插件用 `gui.get_tab_widgets()`（本类的**公开方法**，自动注册成命令）
    #    取标签容器 —— 所以 `get_tab_widgets` 必须留在本类，别搬走。

    def show_code_history(self, folder, caption=None):
        from zmlx.ui.tabs import CodeHistoryView

        if not isinstance(folder, str):
            return

        if os.path.isdir(folder):
            kwds = dict(folder=folder, caption=caption)

            if caption is None:
                caption = os.path.basename(folder)

            def oper(widget):
                widget.set_folder(folder=folder)
                widget.gui_restore = f"""gui.show_code_history(**{kwds})"""

            self.get_widget(
                the_type=CodeHistoryView,
                caption=caption,
                on_top=True,
                oper=oper,
                icon="python",
            )

    def show_output_history(self):
        from zmlx.ui.tabs import OutputHistoryView

        def oper(w):
            w.gui_restore = """gui.show_output_history()"""
            w.set_folder()

        self.get_widget(
            the_type=OutputHistoryView, caption="输出历史", on_top=True, oper=oper
        )

    # ⚠️ ``show_demo`` 2026-10-22 **已搬到插件** ``plugins/builtin/demo_menu.py``
    #    （默认启用）：它只是在「开一个 DemoView 标签页」，控件本体在 ``ui/tabs/``，
    #    与主窗口骨架无关。命令 ``gui.show_demo`` 由那边的 ``setup_ui()`` 用
    #    ``gui.add_func`` 注册；本类**不留方法**，占位在 ``extra_setups/plugin_placeholders.py``。

    def show_memory(self):
        from zmlx.ui.tabs import MemView

        def oper(w):
            w.refresh()
            w.gui_restore = """gui.show_memory()"""

        self.get_widget(
            the_type=MemView, caption="变量", on_top=True, icon="variables", oper=oper
        )

    # ⚠️ `show_timer` 2026-10-22 **已搬到插件** `plugins/builtin/viewers.py`
    #    （默认启用）：方法、`TimerView` 控件与「显示 → 耗时」菜单项都在那边；
    #    本类**不留方法**；占位在 ``extra_setups/plugin_placeholders.py``。

    # ⚠️ ``show_pg_console`` 2026-10-22 **已搬到插件**
    #    ``plugins/builtin/pg_console.py``（默认启用）：方法、``PgConsole`` 控件都在那边，
    #    那个插件现在**完全自含**。
    #    ⚠️ 命令 ``gui.show_pg_console`` 由插件 ``setup_ui()`` 用 ``gui.add_func`` 显式注册
    #    （它原来靠的是本类「所有公开方法自动注册」）。
    #    ⚠️ 与旧实现的一处差别：缺 ``pyqtgraph`` 时**会打印一句 pip 提示**，而旧代码是
    #    静默 ``return``（点了没反应，无从排查）。
    #    ⚠️ 本类**不留方法**；占位在 ``extra_setups/plugin_placeholders.py``。

    # ⚠️ `show_file_finder` 2026-10-22 **已搬到插件** `plugins/builtin/viewers.py`
    #    （默认启用）：方法、`AppPathEdit` 控件与「设置 → 路径」菜单项都在那边；
    #    本类**不留方法**；占位在 ``extra_setups/plugin_placeholders.py``。

    # ⚠️ ``show_solver_selector`` 2026-10-22 **已搬到插件** ``plugins/builtin/solver_menu.py``：
    #    方法、控件 ``SolverSelector``（原 ``ui/tabs/solver_selector.py``）与
    #    「设置 → 求解器」菜单项都在那边，合成一个可关闭的单元。命令
    #    ``gui.show_solver_selector`` 由那边的 ``setup_ui()`` 显式注册（它原来靠本类
    #    「所有公开方法自动注册」）。⚠️ 本类**不再提供**同名方法 —— 有它的话自动注册会
    #    把插件（或 ``extra_setups/plugin_placeholders.py`` 的占位）悄悄顶掉。
    #    ⚠️ 插件默认**不加载**，所以默认只有占位在给出「请先启用它」的提示。

    def show_env_edit(self):
        from zmlx.ui.tabs import EnvEdit

        def oper(w):
            w.gui_restore = """gui.show_env_edit()"""

        self.get_widget(
            the_type=EnvEdit,
            caption="系统设置",
            on_top=True,
            icon="set",
            oper=oper,
            type_kw=dict(items=settings.get_env_items()),
        )

    # ⚠️ ``show_style_sheet`` 2026-10-22 **已搬到插件**
    #    ``plugins/builtin/style_sheet_menu.py``（默认启用）：方法与「设置 → 样式表」
    #    菜单项、以及控件 ``StyleSheetEdit`` 都在那边，那个插件现在**完全自含**。
    #    ⚠️ 命令 ``gui.show_style_sheet`` 仍可用 —— 由插件 ``setup_ui()`` 用
    #    ``gui.add_func`` 显式注册（它原来靠的是本类「所有公开方法自动注册」）。
    #    ⚠️ 本类**不留方法**；占位在 ``extra_setups/plugin_placeholders.py``。
    #    ⚠️ 注意 ``gui.set_style_sheet`` / ``gui.get_style_sheet`` **仍在**
    #    ``__init_gui_api`` 里（它们直接转接 Qt 的 ``setStyleSheet`` / ``styleSheet``，
    #    与插件无关）—— 所以禁用插件时已落盘的样式照常生效，只是没有可视化编辑器。

    # ⚠️ ``show_calendar`` 2026-10-22 **已搬到插件** ``plugins/builtin/admin_menu.py``：
    #    它只是「开一个 Qt 自带的 QCalendarWidget 标签页」，而这个功能的条目本来就在
    #    那个插件里（「帮助 → 显示 → 日历」）。
    #    ⚠️ 命令 ``gui.show_calendar`` 由插件 ``setup_ui()`` 用 ``gui.add_func`` 显式注册 ——
    #    它原来靠的是本类「所有公开方法自动注册」。
    #    ⚠️ 那个插件默认**不加载**（``# ** enabled = False``）：所以默认只有本类的
    #    **占位**（``extra_setups/plugin_placeholders.py``）在给出「请先启用它」的提示；
    #    启用插件后命令才真正打开日历。

    def show_string_table(self, data, caption=None, data_columns=3):
        from zmlx.ui.tabs.string_table import StringTable

        opts = dict(data=data, caption=caption, data_columns=data_columns)

        def oper(w):
            w.gui_restore = f"""gui.show_string_table(**{opts})"""
            w.set_data(data)

        widget = self.get_widget(
            StringTable,
            caption="文本表格" if caption is None else caption,
            type_kw=dict(data_columns=data_columns),
            set_parent=True,
            oper=oper,
        )

        return widget

    def edit_setup_files(self):
        """打开插件列表（「设置 → 插件」）。

        ⚠️ 方法名与 action name 仍沿用 ``setup_files``：它们被
        ``zmlx://gui/edit_setup_files`` 文档链接、标签页的 ``gui_restore``
        存档串（``gui.edit_setup_files()``）和外部脚本引用，改名会破坏这些入口。
        控件本身已改名为 ``PluginListEdit``（文件 ``plugin_list_edit.py``）。
        """
        from zmlx.ui.tabs.plugin_list_edit import PluginListEdit

        def oper(w):
            w.gui_restore = """gui.edit_setup_files()"""
            # 每次打开都拉一次最新数据（插件可能刚被执行过）。
            # ⚠️ 方法叫 ``update_items`` 而不是 ``refresh`` —— 后者会被
            #    ``MainWindow.refresh()`` 在**每次切到这个标签页**时调用，
            #    白白重算一遍（见该方法的说明）。
            w.update_items()

        self.get_widget(
            the_type=PluginListEdit,
            caption="插件",
            on_top=True,
            icon="plugin",
            oper=oper,
        )

    def show_readme(self):
        f = app_data.get("show_readme")
        if callable(f):
            f()
        else:
            from zmlx.ui.tabs import ReadMeBrowser

            def oper(w):
                w.gui_restore = """gui.show_readme()"""

            self.get_widget(
                the_type=ReadMeBrowser,
                caption="ReadMe",
                on_top=True,
                icon="info",
                oper=oper,
                tooltip="显示ReadMe信息，与IGG-Hydrate网站首页的ReadMe保持一致",
            )

    # ⚠️ ``show_changelog`` / ``show_roadmap`` / ``_show_md`` 2026-10-22 **已搬到插件**
    #    ``plugins/builtin/doc_view.py``（默认启用）：它们只是「读包内 md → 开一个
    #    ``TextBrowser`` 标签页」，与骨架无关。命令 ``gui.show_changelog`` /
    #    ``gui.show_roadmap`` 由那边的 ``setup_ui()`` 显式注册（原先靠本类「所有公开
    #    方法自动注册」）—— ``ui/tabs/about.py`` 的「日志 / 路线图」按钮与历史标签页的
    #    ``gui_restore`` 都直接用这两个命令名。
    #    ⚠️ 本类**不再提供**同名方法：有它的话自动注册会把插件悄悄顶掉。

    def check_update(self):
        """在控制台线程中执行 git 更新检查。"""
        from zmlx import get_path

        repo_root = get_path("..")  # zmlx/ 的父目录 = 仓库根目录

        def task():
            from zmlx.algs import update_by_git

            print("正在检查更新...")
            ok, msg = update_by_git(cwd=repo_root)
            if ok:
                print(f"更新: {msg}")
            else:
                print(f"更新失败: {msg}")

        self.console.start_func(task, add_history=False)

    # ⚠️ ``_show_md`` 2026-10-22 随 ``show_changelog`` / ``show_roadmap`` 一起搬进了
    #    插件 ``plugins/builtin/doc_view.py``（见上方那段注释）。

    def show_reg_tool(self):
        """显示登录控件（邮箱验证码 + 登录本机硬件码）。

        登录入口一律打开 LicenseRegister（联网登录：邮箱收验证码、把本机硬件码
        登记到该邮箱）。原先的 RegTool（USB 序列号 + 作者返回的授权码）已不再
        挂到界面上，但模块仍在 zmlx/ui/tabs/reg_tool.py，需要时可直接 import。

        帮助菜单、关于对话框、ReadMe 右键菜单都走这一个入口。
        """
        from zmlx.ui.tabs import LicenseRegister

        def oper(w):
            w.gui_restore = """gui.show_reg_tool()"""

        self.get_widget(
            the_type=LicenseRegister, caption="登录", on_top=True, icon="reg", oper=oper
        )

    def show_feedback(self, text=None):
        """打开「反馈」控件；给了 ``text`` 就先把它填进输入框。

        Args:
            text: 预先填好的反馈正文。``None``（默认）表示**不动**输入框。

        用途：别处发现异常时，可以把自己收集到的现场信息（操作步骤、报错原文、
        版本…）先塞进输入框，用户补两句话就能提交::

            gui.show_feedback(text='打开渗流模型时报错：\\nKeyError: ...')

        ⚠️ **每一段不同的 text 各占一个标签页**：标签名由 text 的哈希派生
        （``反馈<hash>``），所以同一个来源重复调用只会复用同一个标签、而不同来源
        打开的是**各自独立的**控件。这样多份反馈互不干扰 —— 也正是
        ``FeedbackTool`` 删掉自动保存草稿的原因（单槽位草稿会让它们互相覆盖）。
        ``text`` 为空时用固定的「反馈」，那是用户自己敲的场景，只留一个。

        ⚠️ **只在 ``init`` 里填**（``init`` 仅在**新建**控件时执行）。控件已经存在
        时 ``get_widget`` 直接返回旧实例、``init`` 不跑，于是这次的 ``text``
        被忽略 —— 这正是我们要的：那个输入框里可能是**用户正在写的东西**，
        为了塞一段新文本而把它覆盖掉，比「这次没预填上」糟糕得多。
        （``oper`` 每次调用都会执行，所以**绝不能**把预填放那里。）
        """
        from zmlx.ui.tabs import FeedbackTool

        # 用 text 的哈希区分不同来源：同一来源反复打开复用同一标签页，
        # 不同来源各开各的（见上面 docstring）
        caption = f"反馈{get_hash(text, 15)}" if text else "反馈"

        def oper(w: FeedbackTool):  # 每次调用都会执行（含控件已存在时）
            w.gui_restore = """gui.show_feedback()"""

        def init(w: FeedbackTool):  # 只在新建控件时执行（显示之前）
            if text is not None:  # 设置显示的反馈文本
                w.set_text(text)

        self.get_widget(
            the_type=FeedbackTool,
            caption=caption,
            on_top=True,
            icon="info",
            oper=oper,
            init=init,
        )

    def open_url(self, url, caption=None, on_top=None, zoom_factor=None, icon=None):
        """
        显示一个html文件或者网址
        """
        if not isinstance(url, str):
            return

        if QWebEngineView is None:
            if os.path.isfile(url):
                from zmlx.algs import startfile

                startfile(url)
            else:
                from webbrowser import open_new_tab

                open_new_tab(url)
            return

        kwds = dict(
            url=url, caption=caption, on_top=on_top, zoom_factor=zoom_factor, icon=icon
        )

        if zoom_factor is None:
            zoom_factor = 1.0 if is_pyqt6 else 1.5

        def oper(widget):
            widget.page().setZoomFactor(zoom_factor)
            if os.path.isfile(url):
                widget.load(QtCore.QUrl.fromLocalFile(url))
            else:
                widget.load(QtCore.QUrl(url))
            widget.gui_restore = f"""gui.open_url(**{kwds})"""

        if icon is None:
            icon = "web"

        self.get_widget(
            the_type=QWebEngineView,
            caption=caption,
            on_top=on_top,
            oper=oper,
            icon=icon,
        )

    def in_dark_mode(self):
        """
        判断目前界面是否处于暗色模式.
        """
        bg_color = self.palette().color(QtGui.QPalette.ColorRole.Window)
        return bg_color.lightness() < 128

    def show_text_in_tab(self, text, caption=None, on_top=None):
        """
        在一个标签页中显示文本
        Args:
            text: 要显示的文本
            caption: 标签页的标题
            on_top: 是否将标签页置顶

        Returns:
            None
        """
        from zmlx.ui.widgets import TextBrowser

        opts = dict(text=text, caption=caption, on_top=on_top)

        def oper(w: TextBrowser):
            w.gui_restore = f"""gui.show_text_in_tab(**{opts})"""
            w.setPlainText(text)

        self.get_widget(the_type=TextBrowser, caption=caption, on_top=on_top, oper=oper)

    # ⚠️ **插件命令的「占位」不在本类里**（2026-10-22）：`get_vtk_view`、
    #    `show_style_sheet`、`show_demo`、`show_fn2`、`show_pg_console`、`open_pdf`、
    #    `show_solver_selector`、`show_timer`、`view_cwd`、`show_tab_details`、
    #    `show_file_finder`、`show_calendar`、`show_changelog`、`show_roadmap` 这 14 条命令
    #    的实现都在插件里；「插件没启用时给一句可操作提示」的占位函数放在
    #    ``extra_setups/plugin_placeholders.py`` —— 它**恰好在插件之前**执行
    #    （``extra_setups.setup_ui()`` → ``plugins.load_all()``），所以「先挂占位、
    #    插件再覆盖」是同一根顺序链上的一前一后，不依赖本类的自动注册。
    #    ⚠️ **不要在本类里再加同名方法**：自动注册会把插件（或占位）的版本覆盖掉，
    #    而且读代码时看不出这层关系 —— 规则见 ``plugins/AGENTS.md`` §2。

    def show_gui_iter(self, data=None, caption=None, on_top=None):
        if data is None:
            from zmlx.utils import get_gui_iter

            data = get_gui_iter()

        if caption is None:
            caption = "迭代器"

        from zmlx.ui.tabs.gui_iter_edit import GuiIteratorEdit

        def oper(w: GuiIteratorEdit):
            w.gui_restore = "gui.show_gui_iter()"
            w.set_data(data)

        return self.get_widget(
            the_type=GuiIteratorEdit, caption=caption, on_top=on_top, oper=oper
        )

    def update_system_state(self, read_cache=True):
        """
        更新状态栏右侧的授权状态显示（``self.license_button``）

        具体就是重新查一次本机的授权状态（是否已注册/绑定到某个用户），并把
        结论显示到状态栏右侧。

        ⚠️ 本函数**不等待联网结果**（最长 60 秒的查询在 LicenseButton 自己的
        后台线程里跑），界面不会被卡住。

        ⚠️ 本函数总是在 GUI 线程里执行 —— 对外的调用入口是
        ``gui.update_system_state()``（等价于 ``gui.command('update_system_state')``）：
        ``GuiApi`` 会把调用排队投递到 GUI 线程（信号跨线程自动排队），所以脚本
        线程里调用也不会踩 Qt 的线程规则。参数经 ``GuiApi.command`` 的 kwargs
        原样透传，所以 ``gui.update_system_state(read_cache=False)`` 也成立。

        Args:
            read_cache: 是否允许直接读结果缓存（默认 True）。
                - ``True``：本机已有结论时不再发网络请求（C++ 侧按 feature 名
                  保留**成功**结果），适合「刷新一下看看」这类日常调用；
                - ``False``：强制向服务端要最新结果 —— **刚注册/绑定完的自检
                  必须传它**，否则会读到「绑定之前」的旧结论，把新机器判成
                  「尚未注册」（见 ``license_register.LicenseRegister._after_bound``）。

        ⚠️ **本函数的调用点之一就是 :meth:`refresh`**（用默认的 ``True``）：
        切标签页 / 换工作目录 / 控制台发刷新信号都会走到那里，所以这条路径
        必须是「读缓存」的 —— 否则每次切标签都发一次网络请求，最长还要占住
        后台线程 60 秒。

        ⚠️ 重复调用是**安全且廉价**的：``LicenseButton.start_license_query``
        在上一次查询没回来时直接返回（不排队、不叠加线程），所以 `refresh`
        被连续触发也只会起一个线程。
        """
        self.license_button.update_license_state(read_cache=read_cache)


class MySplashScreen(QtWidgets.QSplashScreen):
    def mousePressEvent(self, event):
        pass


def __make_splash(app):
    splash_fig = settings.load_pixmap("splash")
    if (
        splash_fig is not None
        and app_data.getenv("disable_splash", default="No", ignore_empty=True) != "Yes"
    ):
        splash = MySplashScreen()
        try:
            rect = settings.get_current_screen_geometry(splash)
            splash_fig = splash_fig.scaled(
                round(rect.width() * 0.3),
                round(rect.height() * 0.3),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            )
        except Exception as err:
            print(f"Error: {err}")
        splash.setPixmap(splash_fig)
        splash.show()
        app.processEvents()  # 处理主进程事件
        return splash
    else:
        return None


class _RedStderr:
    """把写入 stderr 的内容在送进控制台之前**整段染红**。

    ``__on_init`` 把 ``sys.stderr`` 换成它的实例，于是 ``traceback.print_exc()``、
    ``warnings``、``logging`` 默认的 StreamHandler 等任何写往 stderr 的内容都会显示成红色，
    而 stdout（``print``）保持原样（见 ``OutputWidget`` 的 ANSI 支持）。

    ⚠️ 每一段 ``write`` 都**单独**加色并复位，而不是「记住状态、等某次调用来复位」：写往
    stderr 的常见是不带换行的碎片（``sys.stderr.write('a'); write('b')``），一旦漏掉复位，
    红色会一直漏到后面的 stdout 上。

    ⚠️ ``isatty()`` 返回 False：这样第三方库（tqdm / rich 之类）不会在内容里再塞自己的
    颜色码；着色统一由这里负责。若控制台的「ANSI 颜色」被关掉，这些码会被
    ``OutputWidget.add_text`` 过滤掉，不会显示成乱码。
    """

    COLOR = "\033[31m"  # 红色（ANSI SGR）
    RESET = "\033[0m"

    def __init__(self, target):
        self._target = target

    def write(self, text):
        if text:  # 空写入不产生任何颜色码（控制台的状态栏提示靠这个保持干净）
            self._target.write(f"{self.COLOR}{text}{self.RESET}")

    def flush(self):
        self._target.flush()

    def isatty(self):
        return False

    def __getattr__(self, name):
        # 其余属性（encoding 等）透传给被包装的对象
        if name == "_target":  # 理论上到不了这里，避免拷贝 / 反序列化时递归
            raise AttributeError(name)
        return getattr(self._target, name)


def __exception_hook(the_type, value, tb):
    message = f"""Exception Type: {the_type}
Message : {value}
Object : {tb} We are very sorry for this exception. Please check your data according to the above message. If it's 
still unresolved, please contact the author (email: 'zhangzhaobin@mail.iggcas.ac.cn'), Thank you!"""
    # 走 stderr：__on_init 把 stderr 换成了 _RedStderr，于是这条消息在控制台里是**红色**的
    # （这是「真正的异常」最主要的出口）。⚠️ 别用 print(message)：那是 stdout，不会有颜色。
    print(message, file=sys.stderr)


def __restore_history(win):
    # 恢复窗口的输出历史
    try:
        if (
            app_data.getenv(
                key="restore_console_output", default="Yes", ignore_empty=True
            )
            != "No"
        ):
            from zmlx.algs.fsys import get_latest_file, get_size_mb

            filename = get_latest_file(app_data.root("output_history"))
            if filename is not None:
                # ⚠️ 门槛放宽到 4 MB：历史现在存成 **HTML**（见 OutputWidget.SUFFIX），
                #    每段文本都带 <span style=...> 标签，体积约为纯文本的 5-10 倍；
                #    仍按原来 0.5 MB 卡的话，稍微长一点的输出就会被挡在门外 ——
                #    而「被挡掉」的表现与「没保存」完全一样（重启后是空的）。
                if 0 < get_size_mb(filename) < 4.0:
                    win.get_output_widget().load_text(filename)
    except Exception as Err:
        print(f"Error: {Err}")

    # 输出历史显示之后，再输出当前时间。
    # 蓝色（ANSI 34）：浅色主题下取深蓝、暗色主题下取浅蓝，取色见 OutputWidget 的 _Ansi；
    # 控制台关掉「ANSI 颜色」时这两个码会被过滤掉，不会显示成乱码。
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    win.write(f"\033[34m====== {now} ======\033[0m \n")


def __save_history(win):
    # 保存输出历史（扩展名取 OutputWidget.SUFFIX 即 .html —— 只有 HTML 才带得上颜色）
    from zmlx.ui.widgets.output_widget import OutputWidget

    win.get_output_widget().save_text(
        app_data.root("output_history", f"{time_string()}{OutputWidget.SUFFIX}")
    )


def __on_init(win):
    # step 1
    app_data.put("sys_excepthook", sys.excepthook)  # 备份原来的异常处理函数
    sys.excepthook = __exception_hook

    # step 2. 设置main_window
    app_data.space["main_window"] = win

    # step 3. gui
    gui.set(win.get_gui_api())

    # step 4. 恢复输出历史
    __restore_history(win)

    # step 5. stdout and stderr
    sys.stdout = win
    sys.stderr = _RedStderr(win)  # stderr 的内容统一显示成红色（见 _RedStderr）


def __on_exit(win):
    # step 5. stdout and stderr (此时，界面不应该再接收print，这是首先要做的)
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    # step 4 保存输出历史
    __save_history(win)

    # step 3. gui
    gui.set(None)

    # step 2. 恢复 main_window
    app_data.space["main_window"] = None

    # step 1.
    sys_excepthook = app_data.get("sys_excepthook", None)
    if callable(sys_excepthook):
        sys.excepthook = sys_excepthook  # 恢复原来的异常处理函数


def __on_show(win):
    """
    在首次显示窗口之后执行的操作
    """
    # 必须在窗口正式显示之后，否则此函数可能会出错
    settings.load_window_size(win)

    # 恢复右侧栏（控制台那一栏）的可见性（2026-10-26）。
    # ⚠️ **必须在 load_window_size 之后**：先有窗口尺寸，splitter 才分得出宽度；
    # ⚠️ 只有「明确存了 No」才隐藏；**没存过**（首次运行 / 老版本升级上来）保持显示。
    try:
        if (
            app_data.getenv(
                key="console_visible", encoding="utf-8", default="", ignore_empty=True
            )
            == "No"
        ):
            win.set_side_tabs_visible(False)
    except Exception as err:
        print(f"Error: {err}")

    # 窗口尺寸定下来之后再恢复一次右侧栏宽度：``showEvent`` 里那次可能还早于
    # ``load_window_size``（窗口默认尺寸），这次才是用户真正看到的那个尺寸。
    try:
        win.init_splitter_sizes()
    except Exception as err:
        print(f"Error: {err}")

    # 设置窗口风格
    try:
        if (
            app_data.getenv(key="load_window_style", default="Yes", ignore_empty=True)
            != "No"
        ):
            text = settings.load(
                key="zml_window_style.qss",
                default="",
                encoding="utf-8",
                ignore_empty=True,
            )
            if len(text) > 0:
                win.setStyleSheet(text)
    except Exception as err:
        print(f"Error: {err}")


def __add_code_history():
    try:  # 在尝试调用gui执行的时候，添加代码执行历史
        if len(sys.argv) == 1:
            filepath = sys.argv[0]
            if os.path.isfile(filepath):
                from zmlx.ui.alg import add_code_history

                add_code_history(filepath)
    except Exception as err:
        print(f"Error: {err}")


def __check():
    messages = []

    if not is_pyqt6:
        messages.append("界面将在2026年6月之后停止支持PyQt5，请更新至PyQt6")

    if contain_chinese(get_dir()):
        messages.append("程序安装路径包含中文，请务必安装在纯英文路径下. ")

    if len(messages) > 0:
        KEY = "Init_Warnings_Shown"
        if not app_data.has_tag_today(KEY):
            app_data.add_tag_today(KEY)
            text = ""
            for i in range(len(messages)):
                text += f"{i + 1}. {messages[i]}\n"
            gui.information("注意", text)


def __restore_tabs(filename=None):
    """
    恢复标签状态
    """
    if filename is None:
        filename = app_data.temp("tab_start_code.json")
    if os.path.isfile(filename):
        from zmlx.io.json_ex import read as read_json

        data = read_json(filename)
        try:
            os.remove(filename)
        except Exception as err:
            print(err)
        if isinstance(data, list):
            for text in data:
                try:
                    space = {"gui": gui}
                    exec(text, space)
                except Exception as err:
                    print(err)
    if app_data.getenv("show_readme", default="Yes") != "No":
        if gui.count_tabs() == 0:
            gui.show_readme()


def __console_kernel(code):
    """
    在控制台线程执行的工作
    """
    # 在尝试调用gui执行的时候，添加代码执行历史
    __add_code_history()

    try:
        from zmlx.ui.extra_setups import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup action: {err}")

    # 是否执行插件脚本 —— **默认执行**（没设置过就是 True）。
    #
    # ⚠️ 键名 2026-10-22 由 ``run_setup`` 改为 ``run_plugins``：旧名是
    #    ``zml_gui_setup.py`` 那个文件名的残留，而插件文件早就改叫 ``zml_plugin.py`` 了
    #    （``setup`` 这个词和「插件」对不上，光看名字猜不出这一行在干什么）。
    #
    # ⚠️ **两层 get 是兼容，不是笔误**：外层先看新名，取不到再回落旧名，旧名也取不到
    #    才用 ``True``。于是——
    #    · 老调用方 ``put('run_setup', False)`` 仍然生效（见 ``gui_buffer`` 的
    #      ``open_gui_without_setup()``，那是「这一次不跑插件」的唯一开关）；
    #    · **没有设置过时默认仍然是「跑」** —— 插件默认**不是**全部禁用。
    #    旧名保留到 2027-10-22（一年），届时删掉内层那个 ``get`` 即可。
    if app_data.get("run_plugins", app_data.get("run_setup", True)):
        try:
            from zmlx.ui import plugins

            plugins.load_all()
        except Exception as err:
            print(f"Error when loading plugins: {err}")

    if app_data.get("init_check", False):
        __check()

    if app_data.get("restore_tabs", False):  # 尝试载入tab
        __restore_tabs()

    if code is not None:
        return code()  # 执行外部给的代码
    else:
        return None


def __console_done(win, code, close_after_done):
    """
    在控制台线程结束之后执行的操作
    """
    app_data.put("console_result", win.get_console().result)  # 获得结果
    if close_after_done and code is not None:
        win.close()


def __save_tabs(filename=None):
    """
    保存标签状态
    """
    from zmlx.io.json_ex import write as write_json

    data = []
    for tabs in gui.get_tab_widgets():
        for idx in range(tabs.count()):
            code = getattr(tabs.widget(idx), "gui_restore", None)
            if isinstance(code, str):
                data.append(code)
    if filename is None:
        filename = app_data.temp("tab_start_code.json")
    write_json(filename, data)


def __save_tab_files():
    for tabs in gui.get_tab_widgets():
        for idx in range(tabs.count()):
            widget = tabs.widget(idx)
            if callable(f := getattr(widget, "save_file", None)):
                try:
                    f()
                except Exception as e:
                    print(e)


def __on_close(win):
    # 存储是否显示控制台（⚠️ 判断的是**整个右侧栏**：``right_tabs`` 才是 splitter 里的那一栏，
    # 控制台只是它里面常驻的一个标签页 —— 见 ``set_side_tabs_visible``）
    app_data.setenv(
        key="console_visible",
        value="Yes" if win.right_tabs.isVisible() else "No",
        encoding="utf-8",
    )
    settings.save_window_size(win)
    # 右侧栏宽度（2026-10-26）：用户拖出来的宽度要留住
    settings.save_console_width(win)

    # 尝试保存tab
    if app_data.get("restore_tabs", False):
        __save_tabs()

    # 尝试保存文件
    if app_data.getenv(key="disable_auto_save_file", default="No") != "Yes":
        __save_tab_files()

    # 尝试其他操作
    try:
        tasks_when_close = app_data.get("tasks_when_close", [])

        if isinstance(tasks_when_close, (list, tuple)):  # 尝试作为函数列表
            for task in tasks_when_close:
                try:
                    task()
                except Exception as err:
                    print(f"Error: {err}")

        elif callable(tasks_when_close):  # 尝试作为函数
            try:
                tasks_when_close()
            except Exception as err:
                print(f"Error: {err}")

    except Exception as err2:
        print(f"Error: {err2}")


def execute(code=None, keep_cwd=True, close_after_done=True, add_history=True):
    """启动 zmlx GUI 应用程序。

    创建 QApplication、主窗口和控制台内核线程，启动 Qt 事件循环。
    若 GUI 已存在则直接在当前 GUI 中执行 ``code``。

    Args:
        code: 启动后执行的回调函数（可选）。
        keep_cwd: 是否保持当前工作目录（False 时从设置恢复上次工作目录）。
        close_after_done: ``code`` 执行完成后是否自动关闭窗口。
        add_history: 是否将 ``code`` 添加到执行历史中。

    Returns:
        任意 | None: ``app_data['console_result']`` 中保存的控制台执行结果。

    注意:
        仅在 ``if __name__ == '__main__'`` 块中调用此函数。
        不要在函数内部调用，否则会导致 GUI 嵌套执行。
    """
    try:
        _msg = f"gui_execute. file={__file__}. argv={sys.argv}"
        log(_msg, tag=_msg)
    except Exception as err:
        print(f"Error: {err}")

    if gui.exists():
        return code() if callable(code) else None

    if not keep_cwd:  # 工作目录
        settings.load_cwd()

    # 启动界面应用程序
    app = QtWidgets.QApplication(sys.argv)
    splash = __make_splash(app)

    # 建立主窗口对象，并进行最基本的数据初始化
    win = MainWindow()
    __on_init(win)

    # 显示主窗口
    win.show()
    if isinstance(splash, QtWidgets.QSplashScreen):
        splash.finish(win)  # 隐藏启动界面
        splash.deleteLater()

    # 执行显示之后的操作
    __on_show(win)

    # 设置必要的回调函数
    win.on_close = lambda: __on_close(win)

    # 启动核心(但是不阻塞当前线程)
    win.get_console().start_func(
        lambda: __console_kernel(
            code
        ),  # 这里，会启动包含code在内的其它一些在初始化的代码
        post_task=lambda: __console_done(win, code, close_after_done),
        add_history=False,  # 除了code之外，还包括一些初始化的代码，因此，不要添加到历史中
    )

    # 单将code相关的操作添加到历史，这样后续可以重新多次执行
    if code is not None and add_history:
        add_exec_history(dict(code=code))

    app.exec()
    __on_exit(win)  # 执行最后的清理/恢复操作

    # 返回运行的结果
    return app_data.get("console_result", None)


def get_window():
    """返回当前 MainWindow 实例（可能为 None）。"""
    window = app_data.get("main_window")
    if window is not None:
        assert isinstance(window, MainWindow)
        return window
    else:
        return None
