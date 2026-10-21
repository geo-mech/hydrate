"""关于对话框（版本信息、更新日志、操作按钮）.

界面的「快信息」（路径 / 版本 / Python / Qt 等，都是本地读取）在装配表格时就填好，
「慢信息」（管理员权限 / 登录状态，底层要联网查询）放到后台线程
（:class:`AboutThread`）里取，取回来通过信号发给主线程再填表 ——
这样打开本页面永远不会被网络超时卡住。

⚠️ 「管理员权限」一栏的判据是**绑定邮箱**（见 :func:`is_admin_by_web_license`），
不用 ``lic.is_admin``（那是一个本机判据，换机器就失效）。

重新查询
--------

慢信息只会在**首次显示**时自动查一次（:meth:`About.showEvent`）；用户想重查有两个
入口，**它们要刷的东西不一样**：

- 主窗口菜单「显示 → 刷新」进 :meth:`About.refresh`：``MainWindow.refresh`` 会
  duck-typing 地调用**当前页面**的 ``refresh()``（``hasattr(current, "refresh")``），
  本控件的 :meth:`About.refresh` 就是那个接口。状态栏的授权状态由
  ``MainWindow.refresh`` 自己接着刷（**不必**在这里再刷一遍）。
- 本页右键菜单的「刷新」进 :meth:`About.refresh_with_state`：它先
  :meth:`About.refresh`，再补一次 ``gui.update_system_state()`` —— 这条路径不经过
  ``MainWindow.refresh``，状态栏得自己叫。

两种入口的查询都在后台线程里跑（最长 60 秒，界面不卡），且都可重复调用。

代码行数
--------

「关于」页面里还有一行「代码行数」（见 :data:`CODE_LINES_LABEL`）：统计 ``zmlx``
包内所有 Python 源文件的行数与文件个数。这一项**也是**在后台线程里算的
（:class:`CodeLinesThread`），因为要遍历上千个文件；算完同样用信号发回主线程填表。

⚠️ 与慢信息不同，代码行数**不会**被 :meth:`About.refresh` 重算：代码量的变化极其
缓慢，每次刷新都重扫一遍上千个文件是纯浪费。它只在**首次**统计（:meth:`About.setup`
时起线程），此后一直沿用那一份结果。

关标签不崩溃
------------

本控件起了两个后台线程，而**慢信息那一个可能跑很久**（``web_license.check`` 最长
60 秒）。标签页关闭时控件会被 ``TabWidget.close_tab`` 用 ``deleteLater()`` 销毁，
因此两个线程都**不设 parent**、改由模块级 :data:`_RUNNING` 持有强引用，并在
:meth:`About.cleanup_before_tab_close` 里放弃对结果的等待 —— 详见那两个位置的说明。

⚠️ 这条约束是**硬要求**：一旦把线程的 parent 设回本控件，关标签就会让运行中的
线程跟着被析构，进程直接 abort（``QThread: Destroyed while thread is still
running``）——不是异常，Python 侧兜不住。

彩蛋去了哪里（2026-10-18）
--------------------------

本页原来的「彩蛋」按钮（随机玩一局「螺螺是方块」/「连连看」）**已移除**，
环境变量 ``show_easter_egg`` 也随之作废（不再读取）。

两个游戏现在是**插件**（``plugins/builtin/tetris.py`` / ``plugins/builtin/lianliankan.py``），
都声明了 ``# ** enabled = False`` —— **默认不加载**。想去玩的话：

1. 「设置 → 插件」里勾选对应的游戏；
2. 重启界面；
3. 菜单「**帮助 → 彩蛋**」下会出现各自的入口。

这样「要不要彩蛋」变成了一件**显式、可管理**的事（插件列表里看得见、能勾），
比藏在一个环境变量后面更容易发现，也不会出现在正式演示里。

Modified by DeepSeek, 2026-09-14
Modified by DeepSeek, 2026-10-06: 新增「代码行数」一行，统计在后台线程里执行
Modified by DeepSeek, 2026-10-07: 后台线程不再以本控件为 parent，关闭标签页不再崩溃
Modified by DeepSeek, 2026-10-07: 「版本号」改读 zmlx.__version__，不再解析 pyproject.toml
Modified by DeepSeek, 2026-10-11: 移除「机器码」一行（连同它的复制按钮与取值函数）
Modified by DeepSeek, 2026-10-11: 移除「已登录邮箱」一行（慢信息只剩管理员权限与登录状态）
Modified by DeepSeek, 2026-10-11: 行顺序改为按用户关心程度排（版本/账户/联系/环境）
Modified by DeepSeek, 2026-10-11: 「单位」改为「作者单位」（与「通讯作者」并列，明确归属）
Modified by DeepSeek, 2026-10-11: 「网址」改为「软件网址」（与「作者单位」一栏区分开）
Modified by DeepSeek, 2026-10-11: 「当前版本」提到「版本号」前面
Modified by DeepSeek, 2026-10-11: 「安装路径」提到最前面（它是最常被用来确认装的是哪一份的一行）
Modified by WorkBuddy, 2026-10-16: 「彩蛋」按钮改为默认不显示，仅环境变量 show_easter_egg=Yes 时出现
Modified by DeepSeek, 2026-10-18: 移除「彩蛋」按钮与 show_easter_egg 环境变量 ——
    两个游戏改由插件机制管理（plugins/ 里声明 enabled = False，勾选后菜单
    「帮助 → 彩蛋」出现入口）
"""

from zmlx.system import app_data
from zmlx.ui.alg import open_url
from zmlx.ui.gui_buffer import gui
from zmlx.ui.utils.lic_utils import ADMIN_EMAIL, is_admin_by_web_license
from zmlx.ui.pyqt import QtCore, QtWidgets, QWebEngineView, qt_name

# 这些行的取值需要读 DLL / 联网，耗时不可控，因此放在后台线程里取
SLOW_LABELS = ('管理员权限', '登录状态')

# 后台线程还没返回结果时，这几行先显示的内容
WAITING_TEXT = '查询中...'

#: 「代码行数」一行的行标题（值由 :class:`CodeLinesThread` 在后台算好后填入）
CODE_LINES_LABEL = '代码行数'

#: 「机器码」一行的行标题。
#:
#: ⚠️ **本行自 2026-10-11 起不再显示**（用户要求从「关于」页面移除机器码的展示）：
#: 机器码由 ``web_license`` 在 C++ 侧自己算、随请求补进 ``machine_id`` 字段，用户无需
#: 看到它；需要报给作者时也不再依赖本页面。此常量保留，供别处引用这个标题。
MACHINE_ID_LABEL = '机器码'

#: 统计代码行数时认哪些后缀（只统计 Python 源码）
CODE_FILE_EXTS = ('.py', '.pyw')

#: 代码行数还没算出来时显示的内容
CODE_LINES_WAITING_TEXT = '统计中...'

#: 正在后台跑的线程（模块级强引用）.
#:
#: ⚠️ **不要把线程的 parent 设成本控件**：标签页关闭时控件会被
#: ``TabWidget.close_tab`` 用 ``deleteLater()`` 销毁，而 ``QThread`` 在运行中被
#: 析构会让进程直接 abort（"QThread: Destroyed while thread is still running"，
#: 本项目的 ``demo_view.py`` 真踩过）。``web_license.check`` 最长要等 60 秒网络
#: 超时，关标签时线程几乎必然还在跑 —— parent 设成控件等于「关标签就崩」。
#:
#: 挂在这个模块级列表里，线程一定能跑完；控件若已销毁，Qt 会自动断开信号连接，
#: 迟到的结果被安全丢弃（填表槽不会再被调用）。
_RUNNING = []


def _forget(thread):
    """把已经跑完的线程从登记表里摘掉（主线程调用）."""
    try:
        _RUNNING.remove(thread)
    except ValueError:
        pass


def get_slow_data():
    """在**后台线程**中获取「慢信息」（本函数绝不碰界面）.

    包含管理员权限（由 :func:`is_admin_by_web_license` 判定）以及
    License（可能要联网查询）。任何一项失败都不能让整个「关于」
    页面打不开，因此统一放在同一个 try 中；失败时整体降级为「未知 / Error」。

    Returns:
        dict: ``{行标题: 显示文本}``，键取自 :data:`SLOW_LABELS`。
    """
    try:
        from zmlx.exts import web_license

        web_lic = web_license.check(feature="*")
        is_admin = "Yes" if is_admin_by_web_license(reply=web_lic) else "No"
    except Exception:
        is_admin = "未知"
        web_lic = "Error"

    # 取授权状态会在内核里留下日志（例如「未授权」的提示），顺手打印出来
    try:
        from zmlx.exts import core

        while core.has_log():
            print(core.pop_log())
    except Exception:
        pass

    return {'管理员权限': is_admin, '登录状态': web_lic}


def count_zmlx_code_lines():
    """统计 ``zmlx`` 包内 Python 源码的行数与文件个数（本函数绝不碰界面）.

    在**后台线程**里执行（见 :class:`CodeLinesThread`）：要遍历上千个文件，
    放在主线程会把「关于」页面卡住。只统计 :data:`CODE_FILE_EXTS` 里的后缀
    （即 ``.py`` / ``.pyw``），``zmlx`` 以外的代码（例如 C++ 内核）不算。

    单个文件读失败（权限、编码等）时跳过该文件，不影响整体统计。

    Returns:
        tuple: ``(总行数, 文件个数)``；两项都是 int，失败时为 0。

    Added by DeepSeek, 2026-10-06
    """

    import os

    from zmlx import get_dir

    total_lines = 0
    file_count = 0
    try:
        # zmlx 包的根目录（本文件在 zmlx/ui/widget/ 下面，这里要的是 zmlx 本身）
        root = get_dir()
        for folder, _sub_folders, names in os.walk(root):
            for name in names:
                if not name.endswith(CODE_FILE_EXTS):
                    continue
                file_count += 1
                try:
                    # 用二进制读、只数换行符：不关心编码，也不会被 GBK 源文件绊倒
                    with open(os.path.join(folder, name), 'rb') as file:
                        total_lines += file.read().count(b'\n')
                except Exception:
                    continue
    except Exception:
        return 0, 0
    return total_lines, file_count


def _keep_alive(thread):
    """把一个刚建好的线程登记到模块级列表，并安排它跑完后自我清理.

    三件事（顺序有意为之）：

    1. 线程**自身不设 parent**（调用方负责 ``CodeLinesThread()`` 而不是
       ``CodeLinesThread(self)``）：否则控件被销毁时线程会被连带析构；
    2. 登记进 :data:`_RUNNING`：Python 侧只有这里还引用它，因此它**一定**
       能活到自己跑完（否则会被 GC 掉 —— 同样触发 "Destroyed while running"）；
    3. 跑完 / 线程 ``finished`` 时依次「摘登记表」再 ``deleteLater``：
       槽按连接顺序触发，先摘再删才能保证 :func:`_forget` 拿到的是有效对象。

    Args:
        thread: 刚创建、尚未 ``start()`` 的 :class:`QtCore.QThread`。
    """
    thread.finished.connect(lambda t=thread: _forget(t))
    thread.finished.connect(thread.deleteLater)
    _RUNNING.append(thread)


class CodeLinesThread(QtCore.QThread):
    """在后台线程中统计 zmlx 的代码行数.

    与 :class:`AboutThread` 同样的规矩：线程里只算数据，结果通过 :attr:`sig_lines`
    发回主线程再填表（界面只能在主线程碰）。异常绝不允许逃出 :meth:`run`：
    真逃出去的话线程会静默死掉、信号永不发出，那一行就会永远停在「统计中...」。

    Attributes:
        sig_lines: 信号，携带 ``(总行数, 文件个数)``。
    """

    sig_lines = QtCore.pyqtSignal(int, int)

    def __init__(self, parent=None):
        super(CodeLinesThread, self).__init__(parent)
        self.setObjectName('CodeLinesThread')

    def run(self):
        """线程体：统计代码行数并把结果发回主线程。"""
        try:
            total_lines, file_count = count_zmlx_code_lines()
        except Exception:  # 防御性：正常路径不会触发
            total_lines, file_count = 0, 0
        self.sig_lines.emit(total_lines, file_count)


class AboutThread(QtCore.QThread):
    """在后台线程中获取「关于」页面的慢信息.

    Qt 的规则是「界面只能在主线程碰」，所以线程里只取数据，结果通过
    :attr:`sig_data` 发回主线程。信号是跨线程自动排队投递的，因此接收槽
    （:meth:`About._on_slow_data`）仍然运行在主线程里，可以安全地填表。

    异常绝不允许逃出 :meth:`run`：真逃出去的话线程会静默死掉、信号永不发出，
    那几行就会永远停在「查询中...」。

    Attributes:
        sig_data: 信号，携带 ``{行标题: 显示文本}``。
    """

    sig_data = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super(AboutThread, self).__init__(parent)
        self.setObjectName('AboutThread')

    def run(self):
        """线程体：取慢信息并把它发回主线程。"""
        try:
            data = get_slow_data()
        except Exception as err:  # 防御性：正常路径不会触发
            data = {key: f'Error: {err}' for key in SLOW_LABELS}
        self.sig_data.emit(data)


class About(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super(About, self).__init__(parent)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        # ⚠️ **整张表禁止就地编辑**（本页全是只读信息，本来就没有可编辑的单元格）。
        #    Qt 的默认触发器是 ``DoubleClicked|EditKeyPressed|AnyKeyPressed``，
        #    于是双击任一单元格会**当场弹出一个行内编辑器**；而在 WSLg 下，
        #    编辑器还开着时再双击**另一个**单元格会让 Qt 在 C++ 层直接**段错误**
        #    （不是异常，Python 侧兜不住，表现为「整个软件卡死」）。
        #    实测：不关触发器时，连续双击两个不同行必崩（第 2 次 DblClick 时崩溃）；
        #    关掉后连续双击十次（含重复同一行）安然无恙。
        #    ``setEditTriggers`` 是总闸；下面建单元格时还会清掉 ItemIsEditable 标志
        #    （双保险：即便有人给某个 item 单独放开了标志，也编辑不了）。
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        # 后台线程与按钮的引用（持有引用，防止被 GC 提前回收）
        # ⚠️ 这两个引用只是「本控件当前关注的线程」；线程**本身**的所有权在
        #    模块级 _RUNNING 里（关标签时本控件会被销毁，线程不能跟着走）。
        self._thread = None
        self._code_thread = None
        self._buttons = {}
        # 慢信息只查一次（显示时会触发 showEvent，切换标签页可能反复触发）
        self._slow_started = False
        self.setup()

    def setup(self):
        """构建「关于」表格（只做本地读取，立即返回）。

        表格中的快信息当场填好；慢信息（见 :data:`SLOW_LABELS`）先占位，
        由 :meth:`start_slow_query` 起后台线程取，回来后由
        :meth:`_on_slow_data` 填表。
        """
        import sys

        from zmlx import core, get_dir
        from zmlx import __version__ as pkg_version

        # ⚠️ 行的顺序按**用户关心程度**排（2026-10-11 重排）：第一行是「安装路径」
        #    （带 ReadMe 按钮，也最常被用来确认「我装的是哪一份」）；接着是
        #    「当前版本 / 版本号」（更新、日志）与「登录状态 / 管理员权限 / 登录记录」
        #    （登录、统计），都排在**第一屏**；再接着是与作者的联系方式（最可能需要
        #    照着填 / 照着抄的几行）；最后才是其余的「运行环境」（Python、Qt、DLL、
        #    代码行数），这些只在报障时才有人看。
        # ⚠️ 顺序与下面按 ``label`` 配按钮的分支**没有**绑定：两处都要改的时候就都要改。
        data = [
            # —— 安装 ——
            ["安装路径", f"{get_dir()}"],
            # —— 版本 ——
            ["当前版本", f"{core.time_compile}; {core.compiler}"],
            ["版本号", f"{core.version} (zmlx {pkg_version})"],
            # —— 账户 ——
            ["登录状态", WAITING_TEXT],
            ["管理员权限", WAITING_TEXT],
            ["登录记录", "按天统计（点右侧按钮查看）"],
            # —— 联系 ——
            ["通讯作者", "张召彬"],
            ["联系邮箱", "zhangzhaobin@mail.iggcas.ac.cn"],
            ["作者单位", "中国科学院地质与地球物理研究所"],
            ["软件网址", "https://gitee.com/geomech/hydrate"],
            # —— 其余的运行环境 ——
            ["Python解释器", sys.executable],
            ["Python版本", sys.version],
            ["Qt版本", qt_name],
            ["QWebEngineView已安装", "Yes" if QWebEngineView is not None else "No"],
            ["并行库", f"{core.parallel_impl}"],
            ["DLL函数数量", f"{len(core.get_dll_funcs())}"],
            [CODE_LINES_LABEL, CODE_LINES_WAITING_TEXT],
        ]
        self.setRowCount(len(data))
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["项目", "值", ""])

        hdr = self.horizontalHeader()
        hdr.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(2, 60)

        for i_row in range(len(data)):
            label, value = data[i_row]
            self.setItem(i_row, 0, self._make_item(label))
            self.setItem(i_row, 1, self._make_item(value))

            # 操作按钮
            btn = None
            if label == "安装路径":
                btn = QtWidgets.QPushButton("ReadMe")
                btn.clicked.connect(lambda: gui.show_readme())
            elif label == "当前版本":
                btn = QtWidgets.QPushButton("更新")
                btn.clicked.connect(self._check_update)
            elif label == "版本号":
                btn = QtWidgets.QPushButton("日志")
                btn.clicked.connect(lambda: gui.show_changelog())
            elif label == "登录状态":
                btn = QtWidgets.QPushButton("登录")
                btn.clicked.connect(lambda: gui.show_reg_tool())
            elif label == "登录记录":
                btn = QtWidgets.QPushButton("统计")
                btn.clicked.connect(lambda: gui.show_check_count_view())
            elif label == "软件网址":
                btn = QtWidgets.QPushButton("打开")
                btn.clicked.connect(lambda checked, u=value: open_url(u))
            elif label == "作者单位":
                btn = QtWidgets.QPushButton("打开")
                btn.clicked.connect(lambda checked: open_url("http://www.igg.cas.cn/"))
            elif label == "Python解释器":
                # ★ 彩蛋**不在这里**（2026-10-18 移走）：两个游戏现在是插件
                #   （``plugins/builtin/tetris.py`` / ``plugins/builtin/lianliankan.py``），
                #   都声明了 ``# ** enabled = False``（默认不加载）。用户在
                #   「设置 → 插件」里勾上之后，菜单「帮助 → 彩蛋」下会出现
                #   各自的入口 —— **菜单就是开关**，本页不必再放一个按钮、
                #   也不必再看 ``show_easter_egg`` 环境变量。
                pass
            if btn is not None:
                self.setCellWidget(i_row, 2, btn)
                if label in SLOW_LABELS:
                    # 慢信息还没取回来之前，先不让点（登录按钮要读到登录状态）
                    btn.setEnabled(False)
                    self._buttons[label] = btn

        # 代码行数也要遍历上千个文件，同样丢到后台线程去算（本方法立即返回）
        self.start_code_lines_query()

    @staticmethod
    def _make_item(text):
        """造一个**只读**单元格（清掉 Qt 默认给的 ``ItemIsEditable`` 标志）.

        ``QTableWidgetItem`` 默认就带 ``ItemIsEditable``，这正是「双击单元格会
        弹出编辑器」的直接原因（触发器见 :meth:`__init__` 的 ``setEditTriggers``）。
        本页全是只读信息，所以逐项清掉这个标志 —— 与 ``NoEditTriggers`` 互为
        双保险：万一将来有人给某个 item 单独放开了标志，也仍编辑不了。

        ⚠️ 保留其它标志（可选中 / 可复制 / 启用），只去掉可编辑。

        Args:
            text: 单元格文本。

        Returns:
            QtWidgets.QTableWidgetItem: 只读单元格。
        """
        item = QtWidgets.QTableWidgetItem(text)
        item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        return item

    def start_code_lines_query(self):
        """启动后台线程统计代码行数（主线程调用，只会跑一次）.

        ⚠️ 与 :meth:`start_slow_query` 一样：线程的 parent 留空、改由模块级
        登记表 :data:`_RUNNING` 持有强引用 —— 见那里的说明（关标签时控件会被
        销毁，parent 设成控件会让运行中的线程跟着被析构 = 进程崩溃）。
        已经在跑就直接返回。
        """
        if self._code_thread is not None:
            return
        thread = CodeLinesThread()
        thread.sig_lines.connect(self._on_code_lines)
        thread.finished.connect(self._on_code_thread_finished)
        _keep_alive(thread)
        self._code_thread = thread
        thread.start()

    def _on_code_thread_finished(self):
        """代码行数线程结束（主线程调用）：释放引用（结果已由信号送达）。"""
        self._code_thread = None

    def _on_code_lines(self, total_lines, file_count):
        """代码行数算好了（主线程调用）：填表.

        Args:
            total_lines: zmlx 内 Python 源码的总行数。
            file_count: 参与统计的文件个数。
        """
        for i_row in range(self.rowCount()):
            item = self.item(i_row, 0)
            if item is None or item.text() != CODE_LINES_LABEL:
                continue
            value_item = self.item(i_row, 1)
            if value_item is not None:
                value_item.setText(f"{total_lines:,} ({file_count:,} 个文件)")
            break

    def showEvent(self, event):
        """首次显示时启动后台线程，去取慢信息（只启动一次）.

        ⚠️ 这里用 :meth:`start_slow_query`（而非 :meth:`refresh`）：切标签页会
        反复触发本事件，不能每次都重新联网查一遍；用户想重查请走菜单
        「显示 → 刷新」，那条路径进 :meth:`refresh`。
        """
        super(About, self).showEvent(event)
        if self._slow_started:
            return
        self._slow_started = True
        # 延后一拍：showEvent 期间窗口还没画出来，此时起线程会让「打开窗口」
        # 这件事变得不可预期
        QtCore.QTimer.singleShot(0, self.start_slow_query)

    def start_slow_query(self):
        """启动后台线程获取慢信息（主线程调用）."""
        if self._thread is not None:
            return
        thread = AboutThread()
        thread.sig_data.connect(self._on_slow_data)
        thread.finished.connect(self._on_thread_finished)
        _keep_alive(thread)
        self._thread = thread
        thread.start()

    def cleanup_before_tab_close(self):
        """关闭本标签页时调用（``TabWidget.close_tab``）：**放弃**后台线程的结果.

        ⚠️ **本方法不是「等线程结束」，而是「让线程活到自然结束」**：线程本来
        就没有 parent（见 :data:`_RUNNING` 与 :func:`_keep_alive`），因此它**不会**
        随控件一起被销毁 —— 关标签只会让「填表」这一步失去接收者，线程自己照旧
        跑完、然后被 :func:`_forget` 摘掉。这正是我们要的效果：关标签**瞬间完成**，
        不阻塞界面（``web_license.check`` 最长 60 秒，同步等会把关标签变成冻结），
        也绝不出现 "Destroyed while thread is still running"。

        ⚠️ 这里只清掉对本控件的引用：控件的 Python 包装对象可能比 C++ 对象活得
        久一点，留着 ``self._thread`` 会让「线程 → 控件」这条链多看一个已死对象。

        ⚠️ 同一进程里可能有多个 About 控件先后出现 / 消失，
        :attr:`AboutThread.sig_data` 连到的是**本实例**的槽；控件被 ``deleteLater``
        销毁后 Qt 会自动断连，因此旧线程的结果不会误填到新控件上。
        """
        self._thread = None
        self._code_thread = None

    def refresh(self):
        """重新查一遍「慢信息」并刷新表格（**菜单「显示 → 刷新」的接口**）.

        主窗口的 :meth:`MainWindow.refresh` 会 duck-typing 地调用**当前页面**的
        ``refresh()``（见 ``hasattr(current, "refresh")``），本方法就是那个接口 ——
        没有它，「显示 → 刷新」在本页面什么也不会发生。

        ⚠️ 与 :meth:`start_slow_query` 的分工：那个是**首次显示**时的入口
        （只启动一次，见 :meth:`showEvent`）；本方法必须**可重复调用**，否则
        刷新一次之后就再也不动了。

        ⚠️ **查询在后台线程里跑**（:class:`AboutThread`，最长 60 秒），因此本方法
        立即返回、界面不会被网络超时卡住 —— 与打开本页面时的取舍一致。
        上一次查询还没回来时**直接返回**：不在途叠加线程，重复按刷新也不会
        排起一队请求。

        ⚠️ 刷新前把慢信息三行**复位成「查询中...」**并重新禁用它们的按钮：
        否则旧结论会一直挂在表里，用户看到的是「刷新了但数字没动」——
        尤其 :data:`SLOW_LABELS` 里的「注册」按钮要用新读到的授权状态。
        """
        if self._thread is not None:
            return          # 上一次还没回来，不叠加
        for i_row in range(self.rowCount()):
            item = self.item(i_row, 0)
            if item is None:
                continue
            label = item.text()
            if label in SLOW_LABELS:
                value_item = self.item(i_row, 1)
                if value_item is not None:
                    value_item.setText(WAITING_TEXT)
                btn = self._buttons.get(label)
                if btn is not None:
                    btn.setEnabled(False)
        self.start_slow_query()

    def _on_thread_finished(self):
        """后台线程结束（主线程调用）：释放引用."""
        self._thread = None

    def _on_slow_data(self, data):
        """慢信息回来了（主线程调用）：填表并恢复按钮.

        Args:
            data: :func:`get_slow_data` 的返回值。
        """
        for i_row in range(self.rowCount()):
            item = self.item(i_row, 0)
            if item is None:
                continue
            label = item.text()
            if label in data:
                value_item = self.item(i_row, 1)
                if value_item is not None:
                    value_item.setText(str(data[label]))
        for label in SLOW_LABELS:
            btn = self._buttons.get(label)
            if btn is not None:
                btn.setEnabled(True)

    @staticmethod
    def _check_update():
        """在后台线程中执行 git 更新检查。"""
        from zmlx import get_path

        def task():
            from zmlx.algs import update_by_git

            repo_root = get_path("..")
            print("正在检查更新...")
            ok, msg = update_by_git(cwd=repo_root)
            if ok:
                print(f"更新: {msg}")
            else:
                print(f"更新失败: {msg}")

        gui.start_func(task, add_history=False)

    def _copy_text(self, text, what='内容'):
        """把 ``text`` 复制到剪贴板，并在状态栏提示一句（主线程调用）.

        ⚠️ 用 ``gui.status`` 而不是弹对话框：复制这类动作要的是「悄无声息地
        成功」，弹窗只会多一次点击。无头模式下 ``gui.status`` 自动 no-op。

        Args:
            text: 要复制的文本。
            what: 提示语里对这一项的称呼。
        """
        text = str(text or '')
        QtWidgets.QApplication.clipboard().setText(text)
        gui.status(f'已复制{what}：{text}', 3000)

    def refresh_with_state(self):
        """右键菜单的「刷新」：刷新本页数据，**并顺带刷新状态栏的授权状态**.

        名字里的 ``state`` 指的就是状态栏那个授权状态（``update_system_state``）。

        ⚠️ 与 :meth:`refresh` 分开、而不是把它并进去：``refresh`` 是主窗口
        :meth:`MainWindow.refresh` duck-typing 调用的**通用接口**，而那个接口在
        ``refresh()`` 之后**本来就会**调 ``update_system_state()``（见
        ``MainWindow.refresh`` 里紧跟着的一句）。若把状态栏刷新塞进
        ``refresh``，从菜单「显示 → 刷新」进来时就会**连刷两次**状态栏。
        右键菜单不经过 ``MainWindow.refresh``，所以这里需要自己补一次。

        ⚠️ **读缓存**（用 ``gui.update_system_state()`` 的默认 ``read_cache=True``）：
        本页刚查过授权（``get_slow_data`` → ``web_license.check('*')``），结论已经
        写回缓存，状态栏直接读它即可；与 ``MainWindow.refresh`` 那一处的取舍一致。

        ⚠️ 没有主窗口时 ``gui.command`` 直接返回 ``None``（不报错），所以本控件
        单独使用（例如 :func:`test_1`）时这里是安静跳过。
        """
        self.refresh()
        try:
            gui.update_system_state()
        except Exception as err:
            print(f'刷新状态栏登录状态失败：{err}')

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        menu.addAction("刷新", self.refresh_with_state)
        menu.addSeparator()
        menu.addAction("ReadMe", gui.show_readme)
        menu.addAction("更新", self._check_update)
        menu.addAction("日志", gui.show_changelog)
        menu.addAction("路线图", gui.show_roadmap)
        menu.addAction("登录", gui.show_reg_tool)
        menu.addAction("登录记录", gui.show_check_count_view)
        menu.addAction(
            "打开IGG-Hydrate主页", lambda: open_url("https://gitee.com/geomech/hydrate")
        )
        menu.addAction(
            "打开中科院地质与地球物理研究所主页",
            lambda: open_url("http://www.igg.cas.cn/"),
        )
        menu.popup(event.globalPos())


def test_1():
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = About()
    w.resize(600, 480)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test_1()
