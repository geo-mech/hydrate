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
from zmlx.system import warn

import datetime
import io
import os
import sys
from typing import List, Optional, Tuple, Union


from zmlx.algs.fsys import has_permission, samefile, time_string
from zmlx.exts import contain_chinese, core, get_dir, lic
from zmlx.system import app_data, get_hash, log
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
    QWebEngineSettings,
    QWebEngineView,
    is_pyqt6,
)
from zmlx.ui.utils import FileHandler, GuiApi, TaskProc
from zmlx.ui.widgets import CodeEdit, OutputWidget, TabWidget
from zmlx.ui.widgets._parallel import CoreParallelEdit
from zmlx.ui.widgets.license_button import LicenseButton
from zmlx.ui.widgets.version_button import VersionButton


class Action(QAction):
    """可更新视图的 QAction（支持动态 enabled/visible/text）。"""

    def __init__(self, parent):
        super().__init__(parent)
        self.is_enabled = None  # 检查是否是可执行的
        self.is_visible = None  # 检查是否是可见的

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
        if callable(get_text := getattr(self, "get_text", None)):
            text = get_text()
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
        super(MainWindow, self).__init__(parent)
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
            dict(
                desc="Python文件",
                exts=[".py"],
                func=dict(open_file=self.open_code, new_file=_do_nothing),
            ),
            dict(
                desc="文本文件",
                exts=[".txt", ".json", ".xml", ".qss"],
                func=dict(open_file=self.open_text, new_file=new_empty_file),
            ),
            dict(desc="二维裂缝", exts=[".fn2"], func=self.show_fn2),
            dict(desc="图片", exts=[".png", ".jpg"], func=self.open_image),
            dict(desc="PDF文件", exts=[".pdf"], func=self.open_pdf),
        ]:
            self.add_file_handler(**opt)

        self.console = Console(self)

        widget = QtWidgets.QWidget(self)
        h_layout = QtWidgets.QVBoxLayout(widget)
        splitter = QtWidgets.QSplitter(widget)
        splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)

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

        # 设置标签的形状和位置
        set_position(self.top_tabs)
        set_shape(self.top_tabs)

        set_shape(self.right_tabs)
        self.right_tabs.setTabPosition(QtWidgets.QTabWidget.TabPosition.East)

        # 连接信号
        self.sig_cwd_changed.connect(self.refresh)
        self.sig_cwd_changed.connect(self.view_cwd)

        self.console.sig_refresh.connect(self.refresh)
        # ---- 状态栏右侧的三个常驻控件（按添加顺序从左到右）----
        # 「内核并行」开关：它是**全局**的运行期开关（存 app_data 的 disable_parallel，
        # 并写 core.parallel_enabled），所以放在状态栏这个「全局且常驻」的位置。
        #
        # ⚠️ **原先它挂在控制台的输出面板里**（``OutputWidget``），而那个面板可以不开 /
        #    被收起 —— 开关就跟着看不见了；而「大任务开并行、小任务关掉」是随时可能想
        #    改的事（见 CoreParallelEdit 的 tooltip）。
        self.parallel_edit = CoreParallelEdit(self)
        self.statusBar().addPermanentWidget(self.parallel_edit)

        # 版本号（点击 → 「关于」）。``console_state()`` 会借用它显示控制台运行状态。
        self.version_button = VersionButton(self)
        self.statusBar().addPermanentWidget(self.version_button)

        # 授权状态（点击 → 注册页面）。首次显示时自己起后台线程查一次。
        self.license_button = LicenseButton(self)
        self.statusBar().addPermanentWidget(self.license_button)

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

        try:
            filename = settings.find_icon_file("welcome")
            if filename is not None:
                if os.path.isfile(filename):
                    self.open_image(filename, caption="Welcome")
        except Exception as err:
            print(f"Error: {err}")

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
    encoding = 'utf-8'

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
            #    它固定显示版本号（只在仿真运行时被 ``console_state`` 借用去显示
            #    「运行中/已暂停」），把 print 的内容塞进去会把它顶掉。
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
        raise io.UnsupportedOperation('fileno')

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
        super(MainWindow, self).showEvent(event)
        self.refresh()

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

        self.add_action(
            menu="文件",
            name="quit",
            icon="quit",
            text="退出",
            slot=self.close,
        )

        self.add_action(
            menu="文件",
            name="view_cwd",
            icon="cwd",
            text="浏览",
            shortcut="Ctrl+B",
            slot=self.view_cwd,
        )

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

        self.add_action(
            menu="显示", name="refresh", icon="refresh", text="刷新", slot=self.refresh
        )

        self.add_action(
            menu="显示",
            name="memory",
            icon="variables",
            text="变量",
            slot=self.show_memory,
        )

        self.add_action(
            menu="显示",
            name="timer",
            icon="clock",
            tooltip="显示cpu耗时统计的结果",
            text="耗时",
            slot=self.show_timer,
        )

        # 标签列表：原先**只有**标签栏右键菜单里那一个入口（「列出标签」），
        # 菜单栏里没有 —— 用户得先知道有右键菜单才找得到这个总览视图。
        # ⚠️ 这里**不给 icon**：``zml_icons/`` 里没有「清单 / 标签页」这一类的图，
        #    而 ``load_icon`` 对找不到的名字会返回**空图标**（不报错、只是没图形）；
        #    与其拿一个语义无关的图（如 ``variables`` 的 (x)）凑数，不如不画。
        #    将来若补了合适的图，在这里加一个 ``icon=`` 即可。
        self.add_action(
            menu="显示",
            name="tab_details",
            tooltip="列出已经打开的标签页（可以切过去或关掉），等同于标签栏右键的「列出标签」",
            text="标签列表",
            slot=self.show_tab_details,
        )

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
            shortcut="Ctrl+R",
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
            shortcut="Ctrl+H",
            slot=self.show_console,
            on_toolbar=True,
            is_enabled=lambda: not self.right_tabs.isVisible(),
        )

        self.add_action(
            menu="操作",
            name="console_start_last",
            text="再次运行",
            tooltip="在控制台重新执行上一次的操作",
            shortcut="Ctrl+Shift+R",
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
            menu="设置", name="setup_files", icon="plugin", text="插件",
            slot=self.edit_setup_files
        )

        self.add_action(
            menu="设置",
            name="search",
            icon="set",
            text="路径",
            slot=self.show_file_finder,
        )

        # ★ 「设置 → 求解器」**不在这里**（2026-10-18 移）：那一行 ``add_action``
        #    已搬进插件 ``plugins/builtin/solver_menu.py``（默认不加载）。
        #    ⚠️ 但 ``show_solver_selector`` 这个方法**必须留着** —— 它是本类的
        #    公开方法，``__init_gui_api`` 会自动把名字注册成命令
        #    ``gui.show_solver_selector``；已保存的标签页存的就是
        #    ``gui_restore = "gui.show_solver_selector()"``，删了方法那些标签页
        #    就恢复不了。

        self.add_action(
            menu="设置",
            name="gui_iter",
            text="迭代器",
            slot=lambda: self.show_gui_iter(on_top=True),
        )

        # ★ 「设置 → 样式表」**不在这里**（2026-10-18 移）：那一行 ``add_action``
        #    已搬进插件 ``plugins/builtin/style_sheet_menu.py``（**默认启用** —— 样式是用户
        #    随时会调的外观设置，做成插件只是为了**可被禁用**，不是为了藏起来）。
        #    ⚠️ 但 ``show_style_sheet`` 这个方法**必须留着** —— 它是本类的公开方法，
        #    ``__init_gui_api`` 会自动把名字注册成命令 ``gui.show_style_sheet``；
        #    已保存的标签页存的就是 ``gui_restore = "gui.show_style_sheet()"``。

        # ---- 「帮助」菜单 ----
        #
        # 最终结构（两级，没有更深的一层）::
        #
        #     帮助 ─┬─ ReadMe
        #           ├─ 关于
        #           ├─ 示例
        #           ├─ ▸ 用户 → 登录 · 反馈 · 管理
        #           ├─ ▸ 查询 → 登录记录 · 反馈记录
        #           └─ 架构
        #
        # ★ 2026-10-19：原先独立的顶层「用户」菜单**整体并入「帮助」**（菜单栏因此
        #   少一个顶层菜单）。⚠️ **没有三级菜单**：原先的「用户 → 查询 → …」是**三层**，
        #   现在把「查询」提到「帮助」下面，于是「登录记录 / 反馈记录」只处在
        #   帮助 → 查询 → X 这一层，与「帮助 → 用户 → 登录」同深。
        #
        # ⚠️ 顺序由**建菜单 / 注册的先后**决定，先来的排在前面。两条规则各管一半：
        #
        #    1. **子菜单的位置在它被创建那一刻就定死了**：``get_menu(['帮助','用户'])``
        #       一旦建出「用户」，它就立刻追加到「帮助」末尾；之后往里塞条目只是
        #       **填充内容**，不会让它再换位置。
        #    2. 普通条目（ReadMe / 关于 / 示例）由下面的 ``add_action`` 按顺序追加。
        #
        #   所以这里的分组顺序就是**最终显示顺序**：先登记文档类条目（ReadMe / 关于 /
        #   示例），**再**在末尾 ``get_menu`` 建出两个子菜单 —— 于是「用户 / 查询」排在
        #   文档条目**之后**（2026-10-19 按用户要求下移；此前它们在最前面，很抢眼）。
        #   ⚠️ 子菜单里的条目本身不在这里：由 ``extra_setups/*.py`` 在 ``MainWindow``
        #   构造**之后**（控制台内核里）填进去 —— 那不影响子菜单的位置。
        #   想再调整先后，就挪动下面「三组之间」的分界：``get_menu`` 两行放在哪一段，
        #   两个子菜单就出现在哪一段的末尾。
        #
        # ⚠️ **action name 一律沿用旧名**（``reg`` / ``feedback``）：ribbon 配置、
        #    已保存的界面布局都按 name 定位，改名会让它们失效。

        # ---- 第一组：文档类条目 ----
        self.add_action(
            menu="帮助",
            name="readme",
            icon="info",
            text="ReadMe",
            shortcut="F1",
            slot=self.show_readme,
            on_toolbar=True,
        )

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

        self.add_action(
            menu="帮助",
            name="demo",
            icon="demo",
            tooltip=None,
            text="示例",
            slot=self.show_demo,
            on_toolbar=True,
            is_enabled=None,
            is_visible=lambda: not app_data.get("HIDE_DEMO_MENU", False),
        )

        # ---- 第二组：两个子菜单（位置在这里定下 = 排在文档条目之后）----
        self.get_menu(["帮助", "用户"])    # 「用户」子菜单（条目在 extra_setups）
        self.get_menu(["帮助", "查询"])    # 「查询」子菜单（条目在 extra_setups）

        # ★ 「登录 / 反馈」注册在「帮助 → 用户」下；「管理」与两条记录页**不在这里**：
        #    它们各只是一个菜单条目，控件与注册分别在 ``extra_setups/user_admin.py``
        #    与 ``extra_setups/license_query.py``（那两个文件的文档写清了为什么这样分）。
        #    本文件只留主窗口自己真正用到的东西。
        #
        #    ⚠️ 它们的命令（``gui.show_user_admin`` / ``gui.show_check_count_view`` /
        #    ``gui.show_feedbacks_view``）也由各自文件用 ``gui.add_func`` 注册 ——
        #    原先靠 ``__init_gui_api`` 扫描本类的公开方法来注册，方法搬走之后必须
        #    由那边补上。旧名（``show_license_count`` / ``show_license_feedback``）
        #    作为**别名**也一并注册，好让老标签页的 ``gui_restore`` 还能恢复。
        #    ⚠️ 它们注册的 menu 必须写 ``['帮助', '用户']`` / ``['帮助', '查询']``
        #    （与上面两行逐字一致），否则 ``get_menu`` 会另建同一个名字的菜单，
        #    界面上出现两个「用户」或两个「查询」。
        self.add_action(
            menu=["帮助", "用户"],
            name="reg",
            icon="reg",
            text="登录",
            slot=self.show_reg_tool,
        )

        self.add_action(
            menu=["帮助", "用户"],
            name="feedback",
            text="反馈",
            icon="info",
            slot=self.show_feedback,
            is_enabled=not_running,
        )

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
        assert name is not None, f"Error: name is None when get_menu"
        if isinstance(name, str):
            keys = [name]
        else:
            keys = name
        if len(keys) == 0:
            return None

        keys = [settings.get_text(key) for key in keys]  # 替换字符串

        menu = None
        for action in self.menuBar().actions():
            if isinstance(action.menu(), QtWidgets.QMenu):
                if action.menu().title() == keys[0]:
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
                if isinstance(action.menu(), QtWidgets.QMenu):
                    if action.menu().title() == key:
                        sub_menu = action.menu()
                        break
            if sub_menu is None:
                sub_menu = QtWidgets.QMenu(menu)
                sub_menu.setTitle(key)
                menu.addAction(sub_menu.menuAction())
            menu = sub_menu  # 设置为当前层级的目录
        # 完成了所有的遍历，找到对应的menu
        return menu

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
        menu=None,
        text=None,
        name=None,
        slot=None,
        icon=None,
        tooltip=None,
        shortcut=None,
        on_toolbar=None,
        is_enabled=None,
        is_visible=None,
        overwritable=True,
    ):
        """
        添加一个Action. 这是一个新的版本，将替代后续的直接基于File的ActionX的创建方法，
        并且将支持动态地创建Action。
        Since 2026-6-9.
        """
        if not overwritable:
            if name is None:  # 此时，需要给定一个name (仅仅用于判断是否已存在)
                if isinstance(text, str):  # 此时，给定一个默认的name
                    if menu is None:
                        name = "auto_" + get_hash("_".join(["其它"] + [text]))
                    elif isinstance(menu, str):
                        name = "auto_" + get_hash("_".join([menu, text]))
                    elif isinstance(menu, list):
                        name = "auto_" + get_hash("_".join(menu + [text]))

        if self.get_action(name=name, create_empty=False) is not None:
            if not overwritable:
                assert name is not None, (
                    f"Error: name should not be None when action not overwritable"
                )
                return
            warn(
                f"The action already exists: {name}", UserWarning, stacklevel=2
            )
            name = None

        if name is None:
            index = 1
            while (
                self.get_action(name="unnamed_%03d" % index, create_empty=False)
                is not None
            ):
                index += 1
            name = "unnamed_%03d" % index

        action = Action(self)
        action.setObjectName(name)

        if callable(is_enabled):  # 作为一个函数，动态地判断是否可用
            action.is_enabled = is_enabled

        if callable(is_visible):  # 作为一个函数，动态地判断是否可见
            action.is_visible = is_visible

        if icon is not None:
            action.setIcon(settings.load_icon(icon))
        else:
            icon = app_data.getenv(key="default_action_icon", default="python")
            if icon is not None:
                action.setIcon(settings.load_icon(icon))

        if tooltip is not None:
            action.setToolTip(settings.get_text(tooltip))

        if text is not None:
            if isinstance(text, str):
                action.setText(settings.get_text(text))
            else:
                assert callable(text)
                setattr(action, "get_text", text)
        else:
            action.setText(name)

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

        action.triggered.connect(slot_x)

        if menu is None:
            menu = "其它"

        if on_toolbar:
            toolbar_name = menu if isinstance(menu, str) else menu[0]
            self.get_toolbar(toolbar_name).addAction(action)

        self.get_menu(menu).addAction(action)

    def get_action(self, name, create_empty=True):
        """
        返回给定name的菜单action
        """
        if isinstance(name, str):
            for action in self.findChildren(QAction):
                if action.objectName() == name or action.objectName() == name + ".py":
                    return action
        if create_empty:
            warn(
                f"cannot find the action with name: <{name}>", UserWarning, stacklevel=2
            )
            action = Action(self)
            if name is not None:
                action.setText(name)
            else:
                action.setText("unnamed")
            return action
        else:
            return None

    def list_actions(self):
        names = []
        for action in self.findChildren(QAction):
            name = action.objectName()
            if isinstance(name, str):
                if len(name) > 0:
                    names.append(name)
        return names

    def trigger(self, name):
        """
        触发给定的Action
        """
        action = self.get_action(name)
        if hasattr(action, "trigger"):
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

    def exec_tab_func(self, name):
        widget = self.get_current_widget()
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

        ⚠️ 这里**借用**版本按钮当作「控制台状态显示位」，是沿用已久的行为
        （见 ``VersionButton`` 的模块文档）；传空串由 ``VersionButton.setText``
        回退到版本号，调用方就是靠这个来「清除」。

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
        """
        设置控制台是否可见
        """
        self.right_tabs.setVisible(visible)
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
            action = self.get_action(name=name, create_empty=False)
            if callable(update_view := getattr(action, "update_view", None)):
                try:
                    update_view()
                except Exception as err:
                    print(err)

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

        if not running:  # 只要发现没有运行，就关闭进度条显示
            self.console_state("")  # 显示默认
        else:
            if pause:
                self.console_state("控制台：已暂停")
            else:
                self.console_state("控制台：运行中")

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
            position=position, at_side=at_side).get_figure_widget(**kwargs)

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

    def show_fn2(self, filepath, **kwargs):
        warn(
            "gui.show_fn2 will be removed after 2026-3-5, "
            "please use zmlx.plt.show_fn2 instead",
            DeprecationWarning,
            stacklevel=2,
        )
        from zmlx.ui.tabs.fn2 import Fn2Widget

        if kwargs.get("caption") is None:
            kwargs["caption"] = "Fractures"
        widget = self.get_widget(the_type=Fn2Widget, **kwargs)
        assert widget is not None
        widget.open_fn2_file(filepath)

    def view_cwd(self):
        from zmlx.ui.tabs import CwdView

        def oper(w):
            w.refresh()
            w.gui_restore = f"""gui.view_cwd()"""  # 用于重启

        self.get_widget(
            the_type=CwdView, caption="浏览", on_top=True, oper=oper, icon="cwd"
        )

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
                    x.gui_restore = f"""gui.open_code(**{kwds})"""  # 用于重启

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
                x.gui_restore = f"""gui.open_text(**{kwds})"""  # 用于重启

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
        """
        打开一个图片
        """
        if isinstance(fname, str):
            if os.path.isfile(fname):
                from zmlx.ui.tabs.img import ImageView

                def oper(x):
                    x.set_image(fname)
                    kwds = dict(fname=fname, caption=caption, on_top=on_top)
                    x.gui_restore = f"""gui.open_image(**{kwds})"""  # 用于重启

                if caption is None:
                    caption = os.path.basename(fname)

                self.get_widget(
                    the_type=ImageView, caption=caption, on_top=on_top, oper=oper
                )

    def open_pdf(self, fname, caption=None, on_top=True):
        """
        打开一个pdf
        """
        assert isinstance(fname, str), f"The given fname is not a string: {fname}"
        if not os.path.isfile(fname):
            print(f"File not exist: {fname}")
            return
        if QWebEngineView is None or QWebEngineSettings is None:
            print("QWebEngineView is not installed")
            return

        def oper(w):
            kwds = dict(fname=fname, caption=caption, on_top=on_top)
            w.gui_restore = f"""gui.open_pdf(**{kwds})"""  # 用于重启
            w._settings().setAttribute(
                QWebEngineSettings.WebAttribute.PluginsEnabled, True
            )
            w._settings().setAttribute(
                QWebEngineSettings.WebAttribute.PdfViewerEnabled, True
            )
            if fname.startswith("file://"):
                w.load(QtCore.QUrl(fname))
            else:
                w.load(
                    QtCore.QUrl(
                        QtCore.QUrl.fromLocalFile(os.path.abspath(fname)).toString()
                    )
                )

        if caption is None:
            caption = os.path.basename(fname)

        self.get_widget(
            the_type=QWebEngineView,
            caption=caption,
            on_top=on_top,
            oper=oper,
        )

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
            'MainWindow.check_license() is deprecated (will be removed after 2027-10-05), '
            'the license is now checked by the web license '
            '(see zmlx.exts.web_license and the status bar). This method will be removed.',
            DeprecationWarning, stacklevel=2)
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
                widget.gui_restore = f"""gui.show_about()"""

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

    def show_tab_details(self):
        from zmlx.ui.tabs import TabDetailView

        def oper(w):
            w.gui_restore = f"""gui.show_tab_details()"""

        self.get_widget(
            the_type=TabDetailView,
            caption="标签列表",
            on_top=True,
            type_kw={"obj": TabDetailView.TabWrapper(*self.get_tab_widgets())},
            oper=oper,
            position="right",
        )

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
            w.gui_restore = f"""gui.show_output_history()"""
            w.set_folder()

        self.get_widget(
            the_type=OutputHistoryView, caption="输出历史", on_top=True, oper=oper
        )

    def show_demo(self):
        f = app_data.get("show_demo")
        if callable(f):
            f()
        else:
            from zmlx.ui.tabs import DemoView

            def oper(w):
                # force=True：显式打开本页时一定核对一遍（忽略 DemoView 内部的
                # RESCAN_INTERVAL 闸门），这样「刚加了 demo 文件」马上能看到；
                # 而切标签页走 MainWindow.refresh 的普通 refresh()，不受影响
                w.refresh(force=True)
                w.gui_restore = f"""gui.show_demo()"""

            self.get_widget(
                the_type=DemoView,
                caption="示例",
                on_top=True,
                oper=oper,
                icon="demo",
                tooltip="内置在模型中的示例。单击条目可以打开，然后，请点击工具条的运行按钮来执行",
            )

    def show_memory(self):
        from zmlx.ui.tabs import MemView

        def oper(w):
            w.refresh()
            w.gui_restore = f"""gui.show_memory()"""

        self.get_widget(
            the_type=MemView, caption="变量", on_top=True, icon="variables", oper=oper
        )

    def show_timer(self):
        from zmlx.ui.tabs import TimerView

        def oper(w):
            w.refresh()
            w.gui_restore = f"""gui.show_timer()"""

        self.get_widget(
            the_type=TimerView, caption="耗时", on_top=True, icon="clock", oper=oper
        )

    def show_pg_console(self):
        from zmlx.ui.tabs.pg import PgConsole

        if PgConsole is None:
            return

        def oper(w):
            w.gui_restore = f"""gui.show_pg_console()"""

        self.get_widget(
            the_type=PgConsole,
            caption="Python控制台",
            on_top=True,
            icon="console",
            oper=oper,
        )

    def show_file_finder(self):
        from zmlx.ui.tabs import AppPathEdit

        def oper(w):
            w.gui_restore = f"""gui.show_file_finder()"""

        self.get_widget(
            the_type=AppPathEdit, caption="路径", on_top=True, icon="set", oper=oper
        )

    def show_solver_selector(self):
        from zmlx.ui.tabs.solver_selector import SolverSelector

        def oper(w):
            w.gui_restore = "gui.show_solver_selector()"

        self.get_widget(
            the_type=SolverSelector,
            caption="求解器",
            on_top=True,
            icon="set",
            oper=oper,
        )

    def show_env_edit(self):
        from zmlx.ui.tabs import EnvEdit

        def oper(w):
            w.gui_restore = f"""gui.show_env_edit()"""

        self.get_widget(
            the_type=EnvEdit,
            caption="系统设置",
            on_top=True,
            icon="set",
            oper=oper,
            type_kw=dict(items=settings.get_env_items()),
        )

    def show_style_sheet(self):
        """显示「样式表」标签页（可视化生成 QSS，或直接编辑文本后应用）。

        控件本体见 :class:`zmlx.ui.widget.style_sheet_edit.StyleSheetEdit`。
        本类**不参与**样式的读写：只是把 Qt 自己的 ``setStyleSheet`` /
        ``styleSheet`` 在 :meth:`__init_gui_api` 里转接成
        ``gui.set_style_sheet`` / ``gui.get_style_sheet``，生成、应用与落盘
        都在控件里做。
        """
        from zmlx.ui.tabs import StyleSheetEdit

        def oper(w):
            w.gui_restore = "gui.show_style_sheet()"

        self.get_widget(
            the_type=StyleSheetEdit,
            caption="样式表",
            on_top=True,
            icon="set",
            oper=oper,
            tooltip="可视化设置字体/配色等并生成样式表(QSS)；也可以直接编辑样式表文本",
        )

    def show_calendar(self):
        def oper(w):
            w.gui_restore = f"""gui.show_calendar()"""

        self.get_widget(
            the_type=QtWidgets.QCalendarWidget, caption="日历", on_top=True, oper=oper
        )

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
            w.gui_restore = f"""gui.edit_setup_files()"""
            w.refresh()  # 每次打开都按最新名单重建（插件可能刚被执行过）

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
                w.gui_restore = f"""gui.show_readme()"""

            self.get_widget(
                the_type=ReadMeBrowser,
                caption="ReadMe",
                on_top=True,
                icon="info",
                oper=oper,
                tooltip="显示ReadMe信息，与IGG-Hydrate网站首页的ReadMe保持一致",
            )

    def show_changelog(self):
        """显示 CHANGELOG.md。"""
        self._show_md("CHANGELOG.md", "修改记录",
                      restore="gui.show_changelog()")

    def show_roadmap(self):
        """显示 ROADMAP.md。"""
        self._show_md("ROADMAP.md", "未来工作",
                      restore="gui.show_roadmap()")

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

    def _show_md(self, filename, caption, restore=None):
        """加载并显示随包发布的 Markdown 文档。

        文档（README / CHANGELOG / ROADMAP）只存在于包内 `zmlx/data/` 目录：仓库根目录
        已不再保留副本，因此直接读包内那一份 —— pip 安装环境与开发环境读到的是同一个
        文件，不再需要任何同步步骤。

        Args:
            filename: 要显示的 md 文件名（如 ``CHANGELOG.md``）。
            caption: 标签页标题。
            restore: **公开入口**给出的「重启后如何还原这个标签页」的 GUI 命令
                （如 ``'gui.show_changelog()'``）。``None`` 表示不设。

        ⚠️ **恢复命令必须由公开入口传进来，不能在这里写死**：本方法是**私有**
        方法，不在 ``gui_api`` 白名单里（以 ``_`` 开头的方法一律被排除），
        而 ``gui_restore`` 会被存进标签页状态、重启时按原样用 ``gui.xxx(...)``
        重放。这里若硬写 ``gui._show_md(...)``，重放时就会报
        ``gui function <_show_md> not found``（见 zmlx/ui/utils.py 的
        ``GuiApi.__proc``），标签页再也打不开。
        """
        from zmlx.data import get_path as data_path
        from zmlx.data import read_doc
        from zmlx.ui.widgets import TextBrowser

        text = read_doc(filename)
        if text is None:
            print(f"未找到文件: {filename}")
            return
        path = data_path(filename)

        def oper(w: TextBrowser):
            if restore is not None:
                w.gui_restore = restore
            w.setOpenLinks(True)
            w.setOpenExternalLinks(True)
            w.setMarkdown(text)
            w.set_status(path)

        self.get_widget(
            the_type=TextBrowser, caption=caption, on_top=True, icon="info", oper=oper
        )

    def show_reg_tool(self):
        """显示登录控件（邮箱验证码 + 登录本机硬件码）。

        登录入口一律打开 LicenseRegister（联网登录：邮箱收验证码、把本机硬件码
        登记到该邮箱）。原先的 RegTool（USB 序列号 + 作者返回的授权码）已不再
        挂到界面上，但模块仍在 zmlx/ui/tabs/reg_tool.py，需要时可直接 import。

        帮助菜单、关于对话框、ReadMe 右键菜单都走这一个入口。
        """
        from zmlx.ui.tabs import LicenseRegister

        def oper(w):
            w.gui_restore = f"""gui.show_reg_tool()"""

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
            w.gui_restore = f"""gui.show_feedback()"""

        def init(w: FeedbackTool):  # 只在新建控件时执行（显示之前）
            if text is not None:    # 设置显示的反馈文本
                w.set_text(text)

        self.get_widget(
            the_type=FeedbackTool, caption=caption, on_top=True, icon="info",
            oper=oper, init=init,
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

    def get_vtk_view(self, caption=None, on_top=None, init=None, oper=None):
        """
        打开一个QtInteractor窗口
        Args:
            caption: 窗口的标题
            on_top: 是否将窗口置顶
            init: 初始化函数
            oper: 操作函数
        """
        from pyvistaqt import QtInteractor

        return self.get_widget(
            the_type=QtInteractor, caption=caption, on_top=on_top, init=init, oper=oper
        )

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

    COLOR = '\033[31m'  # 红色（ANSI SGR）
    RESET = '\033[0m'

    def __init__(self, target):
        self._target = target

    def write(self, text):
        if text:  # 空写入不产生任何颜色码（控制台的状态栏提示靠这个保持干净）
            self._target.write(f'{self.COLOR}{text}{self.RESET}')

    def flush(self):
        self._target.flush()

    def isatty(self):
        return False

    def __getattr__(self, name):
        # 其余属性（encoding 等）透传给被包装的对象
        if name == '_target':  # 理论上到不了这里，避免拷贝 / 反序列化时递归
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
                if 0 < get_size_mb(filename) < 0.5:
                    win.get_output_widget().load_text(filename)
    except Exception as Err:
        print(f"Error: {Err}")

    # 输出历史显示之后，再输出当前时间。
    # 蓝色（ANSI 34）：浅色主题下取深蓝、暗色主题下取浅蓝，取色见 OutputWidget 的 _Ansi；
    # 控制台关掉「ANSI 颜色」时这两个码会被过滤掉，不会显示成乱码。
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    win.write(f"\033[34m====== {now} ======\033[0m \n")


def __save_history(win):
    # 保存输出历史
    win.get_output_widget().save_text(
        app_data.root("output_history", f"{time_string()}.txt")
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

    if app_data.get("run_setup", True):  # 执行插件脚本(默认执行)
        try:
            from zmlx.ui import plugins
            plugins.run_setup()
        except Exception as err:
            print(f"Error when run setup: {err}")

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
    # 存储是否显示控制台
    app_data.setenv(
        key="console_visible",
        value="Yes" if win.get_output_widget().isVisible() else "No",
    )
    settings.save_window_size(win)

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
