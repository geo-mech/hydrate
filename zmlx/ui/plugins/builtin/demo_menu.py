# ** name = '示例浏览'
# ** desc = '把「帮助 → 示例」的 Demo 浏览器入口挂到界面上：注册 gui.show_demo 命令（110 个可运行算例）'
# ** enabled = True
"""示例浏览插件：``DemoView`` 控件 + ``gui.show_demo`` 命令 + 「帮助 → 示例」菜单项.

⚠️ **它是插件（可关闭），不是核心功能**（2026-10-22）：这个入口原先以
``MainWindow.show_demo`` 的形式常驻在界面骨架里，并连带在 ``__init_actions`` 里挂了
一个菜单项。现在整体搬到这里：不想在界面上看到它的人，可以在「设置 → 插件」里关掉。

**默认启用**（``# ** enabled = True``）：示例浏览是发现 zmlx 用法的主要入口，
正常安装下应该在界面上。

控件本体也在这里（2026-10-22 由 ``ui/tabs/demo_view.py`` 整体并入）
--------------------------------------------------------------------

:class:`DemoView` **只有本插件在用**（全仓与外部工作区核实过），所以它按
``plugins/AGENTS.md`` §0.2 的「**完全自含**」形态收进这一个文件：控件 + 扫描线程 +
命令 + 菜单，一个文件就是全部。这样「禁用本插件」连控件代码一起不再加载。

⚠️ **搬进来之后这几处的转发必须同步改**（否则 ``ImportError``）：
``ui/tabs/__init__.py`` 删掉 ``DemoView`` 转发；两个弃用垫片
``ui/widget/demo_view.py`` 与 ``ui/widget/__init__.py`` 改指向本模块；
``ui/widgets/base.py``（显式 anchor）也改。

注册了什么
----------

| 注册物 | 内容 | 用途 |
|---|---|---|
| ``gui.show_demo`` | :func:`show_demo` | 命令。⚠️ **被多处引用**，见下 |
| 文件 → 帮助菜单 | 「帮助 → 示例」（工具栏按钮 ``demo``） | 菜单项 |

⚠️ **``gui.show_demo`` 这个命令名不能改**，它至少被四处引用：

1. **历史标签页的 ``gui_restore``** —— 存的就是 ``gui.show_demo()``，重启时按原文重放；
2. ``zmlx/__init__.py`` 的 ``_demo()``（``python -m zmlx demo`` 那条路）；
3. ``zmlx/demos/__main__.py``（``python -m zmlx.demos``）；
4. ``ui/tabs/readme_browser.py`` —— ReadMe 里 ``zmlx/demo`` 链接就地打开示例浏览器。

⚠️ 所以本插件**必须**自己 ``gui.add_func('show_demo', show_demo)``：命令原先靠
``MainWindow`` 的「所有公开方法自动注册」得来，方法一搬走就不会自动出现了
（同 ``vtk_view.py`` / ``pdf_view.py`` 的坑）。

控件说明（原 ``ui/tabs/demo_view.py`` 的模块文档，随控件一并搬来）
------------------------------------------------------------------

在 GUI 中以表格形式展示所有 demo 文件，四列布局：
- 第 0 列：文件路径（点击打开编辑）
- 第 1 列：`# ** desc =` 描述文字（点击运行）
- 第 2 列：`# ** author =` 作者
- 第 3 列：运行按钮（点击在控制台执行 demo）

表格布局特性：
- 列宽：第 0 列自适应内容（不超过总宽 50%），第 1 列填充剩余
- 行高：根据描述文字长度自动换行撑高，确保内容完整显示
- 窗口缩放时自动重算列宽约束

为什么列表是异步载入的（启动 + 切标签页的流畅性）
--------------------------------------------------

列表的数据来源要**遍历整个 demo 目录、逐个解析源文件**（本机 173 个 .py，
逐个 ``tokenize`` 提取 ``# **`` 配置），实测约 150 ms。这 150 ms 以前是
**同步**跑在 GUI 线程上的，于是有两处都能感觉到：

1. **启动**：``DemoView.__init__`` 会扫一遍，:func:`show_demo` 的 ``oper``
   紧接着又扫一遍（合计约 300 ms）；若上次退出时开着本页，「恢复标签」会让它在
   启动阶段就跑起来。
2. **切标签页**：``top_tabs.currentChanged`` 接到 ``MainWindow.refresh``，
   后者 duck-typing 地调当前页面的 ``refresh()`` —— 因此**每次切到本页**
   都要原地停 150 ms，感觉「顿一下、不丝滑」。

现在的做法：

- ``__init__`` 只建表头和一个「正在载入 ...」占位行（几毫秒返回，界面马上
  可见），真正的扫描放进后台线程 :class:`DemoScanThread`，扫完由信号回到
  GUI 线程再填表；
- 扫描期间重复调用 :meth:`DemoView.refresh` 会被合并（不叠加线程），启动时
  的两连扫因此只扫一次；
- 已经有数据时**不改动表格**（只核对一遍），且核对结果与当前缓存一致就什么
  都不做 —— 切标签页的常态是 **0 ms GUI 开销**，不闪、不丢滚动位置和选中行；
- 刚查过 :data:`RESCAN_INTERVAL` 秒内直接跳过，避免频繁来回切标签页时反复
  去读那 173 个文件（OneDrive 目录下每次都是真 IO）。

⚠️ **依赖方向**：本插件用 ``zmlx.ui.gui_buffer.gui`` / ``zmlx.ui.pyqt``（第 3 层）、
``zmlx.algs`` 与 ``zmlx.demos``，自己住在 ``ui/plugins/`` —— 与其它内置插件一致
（``image_browser`` 也这么 import）。

Created by DeepSeek, 2026-10-22: 由 ``MainWindow.show_demo`` + ``__init_actions`` 里
    那条「帮助 → 示例」菜单项合并而来
Modified by DeepSeek, 2026-10-22: ``ui/tabs/demo_view.py`` 整体并入本文件
    （``DemoView`` 只有本插件在用 → 完全自含）
"""

import os
import time

from zmlx.system import execute_once
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets

#: 列表还没扫出来时的占位文字。
WAITING_TEXT = '正在载入示例列表，请稍候 ...'

#: 扫描完成、但一个示例都没找到时的提示。
EMPTY_TEXT = '未找到示例文件。'

#: 距上次扫描不到这么多秒时，:meth:`DemoView.refresh` 直接跳过（不再读目录）。
#:
#: demo 列表是随包发布的**静态内容**，只在用户自己增删 demo 文件时才会变；
#: 而 ``MainWindow.refresh`` 在**每次切换标签页**时都会调过来。没有这个闸门，
#: 来回切标签页就会反复去读那 173 个源文件（OneDrive 目录下是真 IO）。取 5 秒
#: 是「手滑来回切完全无感」与「改完文件很快能看到」的折中。
RESCAN_INTERVAL = 5.0

#: 正在后台扫描的线程（模块级强引用）。
#:
#: ⚠️ **不要把线程的 parent 设成本控件**：标签页关闭或程序退出时控件会被
#: ``deleteLater()`` 销毁，而 ``QThread`` 在运行中被析构会让进程直接崩
#: （"QThread: Destroyed while thread is still running"，本项目真踩过）。
#: 挂在模块级列表里线程一定能跑完；控件若已销毁，Qt 会自动断开信号连接，
#: 迟到的结果被安全丢弃。
_RUNNING = []


def _forget(thread):
    """把已经跑完的线程从登记表里摘掉（主线程调用）."""
    try:
        _RUNNING.remove(thread)
    except ValueError:
        pass


def scan_demo_files():
    """遍历 demo 目录，返回表格所需的原始数据（**纯计算，不碰界面**）。

    每行是 ``[相对路径, 描述, 作者, 绝对路径, 是否高亮]``，与原来的组装逻辑
    完全一致；本函数可以在任意线程里调用。

    Returns:
        list: 二维列表，一行对应一个 demo 文件。
    """
    from zmlx.algs import code_config
    from zmlx.demos import get_path, list_demo_files

    folder = get_path()
    data = []
    for path, desc in list_demo_files():
        cfg = code_config(path=path, encoding='utf-8')
        data.append([
            os.path.relpath(path, folder),
            desc,
            cfg.get('author', ''),
            path,
            cfg.get('highlight', False),
        ])
    return data


class DemoScanThread(QtCore.QThread):
    """在后台线程里扫描 demo 目录（**绝不碰界面**）。

    Qt 的规矩是「界面只能在主线程碰」，所以线程里只取数据，结果通过
    :attr:`sig_data` 发回主线程；信号是跨线程自动排队投递的，因此接收槽
    :meth:`DemoView._on_data` 仍然运行在 GUI 线程里，可以安全地填表。

    ⚠️ 异常绝不允许逃出 :meth:`run`：真逃出去线程会静默死掉、信号永不发出，
    表格就会永远停在「正在载入 ...」。

    Attributes:
        sig_data: 信号，携带 :func:`scan_demo_files` 的返回值。
    """

    sig_data = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        """初始化。

        Args:
            parent: Qt 父对象（**留空**，见模块级 ``_RUNNING`` 的说明）。
        """
        super(DemoScanThread, self).__init__(parent)
        self.setObjectName('DemoScanThread')

    def run(self):
        """线程体：扫描目录并把结果发回主线程。"""
        try:
            data = scan_demo_files()
        except Exception as err:  # 防御性：正常路径不会触发
            print(f'Error (when scan demo files): {err}')
            data = []
        self.sig_data.emit(data)


class HtmlDelegate(QtWidgets.QStyledItemDelegate):
    """HTML 渲染委托 — 在 QTableWidget 单元格中渲染 HTML 文本."""

    def paint(self, painter, option, index):
        opt = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        painter.save()
        doc = QtGui.QTextDocument()
        doc.setHtml(opt.text)
        doc.setTextWidth(opt.rect.width())
        opt.text = ''
        style = opt.widget.style() if opt.widget else QtWidgets.QApplication.style()
        style.drawControl(QtWidgets.QStyle.ControlElement.CE_ItemViewItem, opt, painter)

        painter.translate(opt.rect.left(), opt.rect.top())
        doc.drawContents(painter)
        painter.restore()

    def sizeHint(self, option, index):
        doc = QtGui.QTextDocument()
        doc.setHtml(index.data())
        doc.setTextWidth(option.rect.width() if option.rect.width() > 0 else 400)
        return QtCore.QSize(int(doc.idealWidth()), int(doc.size().height()))


class DemoView(QtWidgets.QTableWidget):
    """Demo 浏览器表格。

    数据来源：:func:`scan_demo_files`（内部走 ``zmlx.demos.list_demo_files()``），
    每行是 ``[相对路径, 描述, 作者, 绝对路径, 是否高亮]``。
    四列布局：文件名 | 描述 | 作者 | 运行按钮。

    ⚠️ **列表是异步载入的**：构造时只放一个「正在载入 ...」占位行，扫描在
    :class:`DemoScanThread` 里跑，结果经 :meth:`_on_data` 回到 GUI 线程填表。
    因此构造后 ``rowCount()`` 会先是 1、稍后变成真实条数 —— 调用方不要假设
    「构造完就有数据」。详见模块文档。
    """

    def __init__(self, parent=None):
        super(DemoView, self).__init__(parent)
        self.__data = []
        self.__loaded = False  # 是否已经成功扫过一次（空结果也算）
        self.__scanned_at = 0.0  # 上次扫描结束的 time.monotonic()
        self._thread = None  # 在飞的扫描线程（持有引用，防被 GC）
        self._col0_width = None  # 第 0 列的自然宽度（缓存，见 _constrain_col0）
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setWordWrap(True)
        self.clicked.connect(self.item_clicked)
        self.setItemDelegateForColumn(1, HtmlDelegate(self))
        self.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self._sort_order = {}  # {col: ascending}
        self._setup_columns()
        self._show_placeholder(WAITING_TEXT)
        # 延后一拍再起线程：构造/showEvent 期间窗口还没画出来，此时起线程会让
        # 「打开这个标签页」这件事变得不可预期
        QtCore.QTimer.singleShot(0, self.refresh)

    def _setup_columns(self):
        """建立表头与列宽约束（与数据无关，只做一次）."""
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(
            ['项目 (点击打开)', '说明 (点击运行)', '作者', ''])

        hdr = self.horizontalHeader()
        hdr.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(3, 50)

        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

    def _show_placeholder(self, text):
        """整行显示一句提示文字（跨列），让控件立刻有内容可见."""
        self.clearSpans()
        self.setRowCount(0)  # 清掉旧的行（连同其中的按钮控件）
        self.setRowCount(1)
        self.setItem(0, 0, QtWidgets.QTableWidgetItem(text))
        self.setSpan(0, 0, 1, 4)
        self._col0_width = None  # 行内容变了，自然宽度缓存作废
        self._constrain_col0()

    def refresh(self, force=False):
        """核对一遍 demo 目录（**立即返回，从不阻塞界面**）。

        分三种情况：

        - **还没有数据**：先显示「正在载入 ...」占位行，再起后台线程扫描；
        - **已有数据且刚刚查过**（:data:`RESCAN_INTERVAL` 秒内）：直接返回。
          「切换标签页」走的正是这条路径，因此是 0 ms 开销；
        - **已有数据但已经过时**：起后台线程核对，**不动表格**；结果真的变了
          才重建（见 :meth:`_on_data`）。

        Args:
            force: 忽略 :data:`RESCAN_INTERVAL` 闸门，强制核对一遍。显式打开
                本页的动作（``gui.show_demo()``）用它，保证「刚加了 demo」这种
                场景立刻能看到。

        ⚠️ 上一次扫描还没回来时**总是直接返回**（不叠加线程），这一条同时解决了
        启动时的重复扫描 —— ``DemoView.__init__`` 和 :func:`show_demo` 的
        ``oper`` 会各调一次本方法，去重之后只扫一次。

        ⚠️ 本方法必须**可重复调用**：主窗口「操作 → 刷新」会 duck-typing 地调
        当前页面的 ``refresh()``。
        """
        if self._thread is not None:
            return  # 上一次扫描还没回来，不叠加
        if self.__loaded and not force:
            if time.monotonic() - self.__scanned_at < RESCAN_INTERVAL:
                return  # 刚查过：切标签页时什么都不做
        if not self.__loaded:
            self._show_placeholder(WAITING_TEXT)  # 首次：先给个占位行

        thread = DemoScanThread()
        thread.sig_data.connect(self._on_data)
        thread.finished.connect(self._on_thread_finished)
        # 摘登记表要在 deleteLater 之前连接（槽按连接顺序触发）
        thread.finished.connect(lambda t=thread: _forget(t))
        thread.finished.connect(thread.deleteLater)
        _RUNNING.append(thread)
        self._thread = thread
        thread.start()

    def _on_thread_finished(self):
        """后台扫描结束（主线程调用）：释放引用并记下时刻."""
        self._thread = None
        self.__scanned_at = time.monotonic()

    def _on_data(self, data):
        """扫描结果回来了（主线程调用）：只在内容真的变了时才重建表格。

        内容没变时**什么都不做**是这里的关键：切换标签页会反复走到这条路径，
        若每次都重建，就会出现「表格闪一下、滚动位置跳回顶部、选中行丢失」。

        Args:
            data: :func:`scan_demo_files` 的返回值。
        """
        self.__loaded = True
        candidate = self._apply_sort(list(data or []))
        if candidate == self.__data and self.rowCount() == len(candidate):
            return  # 一模一样：不重建、不重绘
        self.__data = candidate
        self._rebuild()

    def _rebuild(self):
        """按缓存的数据重建表格（**纯 Qt 操作，约十几毫秒**）."""
        if len(self.__data) == 0:
            self._show_placeholder(EMPTY_TEXT)
            return

        data = self._apply_sort(self.__data)

        self.setRowCount(len(data))
        self.clearSpans()
        self._col0_width = None  # 行内容变了，自然宽度缓存作废

        for row_id in range(len(data)):
            try:
                name, desc, author, path, highlight = data[row_id]
                item0 = QtWidgets.QTableWidgetItem(name)
                item1 = QtWidgets.QTableWidgetItem(desc)
                item2 = QtWidgets.QTableWidgetItem(author)
                if highlight:
                    color = QtGui.QColor(200, 50, 50) if highlight is True else QtGui.QColor(highlight)
                    item0.setForeground(color)
                self.setItem(row_id, 0, item0)
                self.setItem(row_id, 1, item1)
                self.setItem(row_id, 2, item2)

                # 运行按钮（仅 .py/.pyw 文件）
                ext = os.path.splitext(path)[-1].lower()
                if ext in ('.py', '.pyw'):
                    btn = QtWidgets.QPushButton('运行')
                    fpath = path
                    btn.clicked.connect(
                        lambda checked, p=fpath: _gui().exec_file(p))
                    self.setCellWidget(row_id, 3, btn)
            except Exception as err:
                print(err)
                for col_id in range(3):
                    self.setItem(row_id, col_id, QtWidgets.QTableWidgetItem(''))

        self._constrain_col0()

    def _on_header_clicked(self, col):
        """点击列标题: 切换升序/降序并重建表格."""
        if len(self.__data) == 0:
            return  # 还在载入，没有可以排序的数据
        self._sort_order[col] = not self._sort_order.get(col, True)
        self._rebuild()  # 只重排已缓存的数据，不再扫一遍目录

    def _apply_sort(self, data):
        """按 _sort_order 对给定的数据排序，并返回它（原地排序）.

        Args:
            data: 形如 ``[相对路径, 描述, 作者, 绝对路径, 是否高亮]`` 的列表。

        Returns:
            排好序的同一个列表对象。
        """
        for col, asc in reversed(list(self._sort_order.items())):
            data.sort(key=lambda x: x[col], reverse=not asc)
        return data

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._constrain_col0()

    def _constrain_col0(self):
        """让第 0 列自适应内容，但不超过可视宽度的一半.

        ⚠️ ``resizeColumnToContents(0)`` 要逐行测量，实测约 9 ms；而
        ``resizeEvent`` 在窗口/标签页变化时会频繁触发，每次都重量一遍会让拖动
        窗口变涩。真正取决于**内容**的自然宽度只需在行数据变化后算一次
        （:meth:`_rebuild` / :meth:`_show_placeholder` 会把缓存置空），其余的
        缩放只是拿缓存值做一次夹取。

        ⚠️ 算出来的宽度和当前一致时**不要调 ``setColumnWidth``**：它会触发列
        布局重算 + 整表重绘（实测约 8 ms），而窗口拖动时绝大多数帧算出来的宽度
        都不变。加上这一句判断，拖动窗口才是顺的。
        """
        if self._col0_width is None:
            self.resizeColumnToContents(0)
            self._col0_width = self.columnWidth(0)
        max_w = max(self.viewport().width() // 2, 60)
        width = min(self._col0_width, max_w)
        if self.columnWidth(0) != width:
            self.setColumnWidth(0, width)

    def item_clicked(self, index):
        """点击第 0 列打开文件，第 1 列运行 demo。"""
        row_id = index.row()
        col = index.column()
        if row_id >= len(self.__data) or col >= 3:
            return

        try:
            name, desc, author, path, highlight = self.__data[row_id]
            if col == 1 and os.path.isfile(path):
                _gui().exec_file(path)
            elif os.path.isfile(path):
                _gui().open_code(path)
            elif os.path.isdir(path):
                from zmlx.algs import startfile
                startfile(path)
        except Exception as err:
            print(err)


def _gui():
    """取 ``gui`` 缓冲区（延迟导入，避免本模块在导入期就把 Qt 拉满）."""
    from zmlx.ui.gui_buffer import gui

    return gui


def show_demo():
    """显示（或切到）「示例」标签页 —— 内置 demo 的浏览器.

    ⚠️ **只通过 ``gui.get_widget`` 打开**（而不是直接 ``DemoView()``）：这样标签页只会
    **一个**，重复调用只是把已有页面切到前面。

    ⚠️ **``oper`` 里用 ``refresh(force=True)``**：忽略 ``DemoView`` 内部的
    ``RESCAN_INTERVAL`` 闸门，保证「刚加了 demo 文件」马上能看到；而「切换标签页」
    走的是普通 ``refresh()``，不受影响（那条路径是 0 ms 开销）。

    ⚠️ 与 ``MainWindow`` 时期一样，**支持用 ``app_data`` 里的 ``show_demo`` 回调覆盖**
    本行为（那里放了可调用对象时就直接调它）。⚠️ 本仓没有任何代码写这个键，它留给
    外部脚本自定义「示例」入口。
    """
    from zmlx.system import app_data

    f = app_data.get('show_demo')
    if callable(f):
        f()
        return

    def oper(w):
        # force=True：显式打开本页时一定核对一遍（忽略 DemoView 内部的 RESCAN_INTERVAL
        # 闸门），这样「刚加了 demo 文件」马上能看到；而切标签页走普通 refresh()，不受影响
        w.refresh(force=True)
        w.gui_restore = 'gui.show_demo()'

    _gui().get_widget(
        the_type=DemoView,
        caption='示例',
        on_top=True,
        oper=oper,
        icon='demo',
        tooltip='内置在模型中的示例。单击条目可以打开，然后，请点击工具条的运行按钮来执行',
    )


@execute_once(file=__file__)
def setup_ui():
    """注册 ``gui.show_demo`` 与「帮助 → 示例」菜单项（插件被执行时调一次）."""
    from zmlx.system import app_data

    gui = _gui()
    gui.add_func('show_demo', show_demo)
    gui.add_action(
        menu='帮助',
        name='demo',
        icon='demo',
        tooltip=None,
        text='示例',
        slot=show_demo,
        on_toolbar=True,
        is_enabled=None,
        # ⚠️ 原样保留「可用 ``HIDE_DEMO_MENU`` 隐藏这一项」的行为（与 ``MainWindow``
        #    时期一致）。⚠️ 这是 **is_visible**，不是「禁用」—— 想让插件整体不加载，
        #    请在「设置 → 插件」里关掉本插件。
        is_visible=lambda: not app_data.get('HIDE_DEMO_MENU', False),
    )


def test_1():
    """直接运行本文件时的自测：单独开一个窗口把 Demo 浏览器跑起来."""
    import sys

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    w = DemoView()
    w.resize(800, 600)
    w.show()
    sys.exit(app.exec())


# ⚠️ 插件路径：由 load_all exec 执行，**没人会替我们调 setup_ui()**，所以本文件
#    把调用写在**模块顶层**的这个分支里（``setups/*.py`` 则由
#    ``setups/__init__.py`` 统一调用 —— 这是两者唯一的区别）。
#    插件机制执行时 ``__name__`` 是 ``'__zml_plugin__'``；直接 ``python demo_menu.py``
#    时才是 ``'__main__'``（见 plugins/__init__.py 的说明）。
if __name__ == '__zml_plugin__':
    setup_ui()

if __name__ == '__main__':
    test_1()
