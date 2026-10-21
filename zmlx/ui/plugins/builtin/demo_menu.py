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
- **说明列的宽度一变就重算行高**（2026-10-31）：宽窗口打开、再缩小窗口时，行高会
  按新宽度重新测量；以前只在「打开那一刻」量一次，缩窄后文字会被截掉。见
  :meth:`DemoView._remind_row_heights` 与 :class:`HtmlDelegate`。

「最近运行」分组（2026-11-02 新增）
-----------------------------------

110 个 demo 平铺在一起太难找；测试阶段实际反复用的就那么几个，所以列表**不再是**
一维的，而是分成两段：

```
┌──────────────────────────────────────────────────────┐
│ 项目 (点击打开) │ 说明 (点击运行) │ 作者 │             │ ← 表头（不随内容滚动）
├──────────────────────────────────────────────────────┤
│ 最近运行 (3)                                          │ ← 全宽分组行
│ hydrate/co2.py  │ ……            │ 张三 │ [运行]      │
│ ……                                                    │
│ 全部示例 (110)                                        │ ← 全宽分组行
│ thermal/egs.py  │ ……            │ 李四 │ [运行]      │
│ ……                                                    │
└──────────────────────────────────────────────────────┘
```

- **怎么算「运行过」**：这个控件自己的运行入口（「运行」按钮 / 点说明列）记一次；
  另外在 :data:`RECENT_POLL_MS` 毫秒的定时器里看一眼控制台 —— 不是本控件发起的运行
  （编辑器里点运行、命令行 ``gui.exec_file``）也算，条件是「上一次看到时没在跑、
  现在在跑、且 ``__file__`` 就在示例目录下」。只看**状态跳变**，所以同一个 demo
  跑到一半不会被重复记。
- **记到哪**：``app_data.temp('demo_recent_files.json')`` 这个**文件**（JSON 数组，
  最近跑的在前，最多 :data:`RECENT_MAX` 条）。它落在应用缓存目录的 ``temp/`` 下，
  所以**重启仍在** —— 与 ``console_cmd_history.txt`` / ``tab_start_code.json``
  同一档。⚠️ 刻意**不用** ``app_data.put``（内存键，重启即丢），也**不用**
  ``setenv``（那是「环境变量」那一套，而且只能存字符串）。
- **要不要显示这一组**：见 :meth:`DemoView.refresh` 的 ``show_recent`` 参数 ——
  **0 条不显示**，**菜单显式打开才显示**，单击标签页切回来不会把它变出来
  （原因见那个方法的说明）。
- **分组行在「载入中 / 未找到」时隐藏**：那时表格只有一行跨列文字，显示分组行会让
  占位行跑到它上面去。
- **排序不影响分组**：点列标题仍然对整个表排序，分组行始终在自己的组头顶上。

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
Modified by DeepSeek, 2026-10-31: 说明列宽度一变就重算行高（此前窗口缩小后文字显示不全）
Modified by DeepSeek, 2026-11-02: 按用户要求拆成「最近运行」+「全部示例」两组，
    运行过的 demo 记到 ``app_data.temp('demo_recent_files.json')``（跨进程保留）
"""

import json
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

#: 「最近运行」记录的文件名（存在 ``app_data.temp()`` 下，**跨进程保留**）。
#:
#: ⚠️ 用 ``app_data.temp(...)`` 建**文件**，不用 ``app_data.setenv``：这里是
#: 一个列表 / 一份缓存，属于「应用自己的数据文件」，与 ``console_cmd_history.txt``
#: 「``tab_start_code.json``」同一档（见 ``zmlx/system/_app_data.py`` 的
#: 「两套存储」）。文件内容是 JSON 数组，最近跑的在前。
RECENT_FILE = 'demo_recent_files.json'

#: 「最近运行」最多保留多少条。
#:
#: 比界面上显示的那几条多留一些：将来若要「显示最近 5 条」不必改存储格式，
#: 而且用户中途删掉某几个 demo 时，列表还有余量可退。
RECENT_MAX = 20

#: 界面上「最近运行」这一组最多显示几条（2026-11-02 按用户要求取 3）。
RECENT_SHOWN = 3

#: 「最近运行」与「全部示例」两个分组行的文字（``{}`` 处补条数）。
GROUP_TEXT_RECENT = '最近运行 ({})'
GROUP_TEXT_ALL = '全部示例 ({})'

#: 多少毫秒看一眼控制台有没有新发起的运行（见 :meth:`DemoView._poll_running`）。
RECENT_POLL_MS = 1000

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


def _path_key(path):
    """把路径规整成「同一个文件只有一种写法」（用于比对与去重）.

    ⚠️ Windows 上路径**不区分大小写**，而同一个 demo 既可能以 ``D:/a/b.py``
    被记进来，也可能以 ``d:/A/B.py`` 再来一次 —— 不 ``normcase`` 就会在
    「最近运行」里出现两行。``normpath`` 顺带消掉 ``..`` 与重复分隔符。
    """
    try:
        return os.path.normcase(os.path.normpath(os.path.abspath(path)))
    except Exception:  # 防御性：非法路径原样返回（比对不到时最多多一条记录）
        return path


def recent_file():
    """「最近运行」记录文件在磁盘上的完整路径（``app_data.temp`` 下）.

    Returns:
        str: 路径。⚠️ 只算路径、**不建文件**（何时建由 :func:`save_recent` 决定）。
    """
    from zmlx.system import app_data

    return app_data.temp(RECENT_FILE)


def load_recent():
    """读出「最近运行」的 demo 路径列表（**最近跑的在前**）.

    Returns:
        list: 绝对路径列表。以下情况一律返回 ``[]``（**都属于正常状态，不是错误**）：
        第一次运行（文件还不存在）、文件被「清理临时文件」删掉、文件是空的、
        内容不是 JSON 数组。

        唯一会打印一句的是「文件存在但读不出来」（编码 / 权限 / 磁盘错误）——
        那时同样返回 ``[]``。本函数**从不抛异常**，也**不写文件**。

    ⚠️ 存成 :func:`recent_file` 那个**文件**（``app_data.temp`` 下），不是
    ``app_data.put`` 的内存键（重启即丢），也不是 ``setenv``（那是环境变量那一套，
    留给更重要的设置）。运行历史属于**缓存性质**，丢了最多「最近运行」不再显示，
    用 :meth:`DemoView._compose` 的降级逻辑保证界面照常可用。
    """
    try:
        path = recent_file()
        if not os.path.isfile(path):
            return []  # 首次运行 / 被清理过：正常状态
        with open(path, 'r', encoding='utf-8') as file:
            text = file.read()
        if len(text.strip()) == 0:
            return []  # 空文件：同上
        data = json.loads(text)
    except Exception as err:
        print(f'Error (when load recent demo files): {err}')
        return []
    if not isinstance(data, list):
        return []
    return [x for x in data if isinstance(x, str) and len(x) > 0]


def save_recent(paths):
    """把「最近运行」列表写回 :func:`recent_file` 那个文件.

    Args:
        paths: 路径序列，**最近跑的在前**（调用方负责去重与截断）。

    ⚠️ 先写临时文件再 ``os.replace``：程序中途被杀时不会留下半个 JSON
    （那样下次启动就整份记录读不出来了）。写失败（只读目录、磁盘满）只打印一句、
    **不抛异常**：记不上「最近运行」不该让人用不了示例浏览。
    """
    path = None
    try:
        from zmlx.system import make_parent

        path = recent_file()
        make_parent(path)
        temp = path + '.tmp'
        with open(temp, 'w', encoding='utf-8') as file:
            json.dump(list(paths), file, ensure_ascii=False, indent=1)
        os.replace(temp, path)
    except Exception as err:
        print(f'Error (when save recent demo files): {err}')


def mark_run(path):
    """把 ``path`` 记成「刚刚运行过」（排到最前；旧位置删掉）.

    Args:
        path: demo 文件的绝对路径。

    Returns:
        bool: 记录**变了**返回 ``True``（调用方据此决定要不要重建表格）；
        路径非法时返回 ``False``。

    ⚠️ 这里是**唯一的**写入口，所以「去重」与「最多几条」只在 :data:`RECENT_MAX`
    这一处维护。

    ⚠️ **落盘前统一存绝对路径**（:func:`_path_key` 走 ``abspath``）：记录是按
    「规整后的绝对路径」与表格里的 demo 比对的（见 :meth:`DemoView._compose`），
    写进去的要是相对路径，下次启动就会一条都匹配不上、「最近运行」凭空消失。
    """
    if not isinstance(path, str) or len(path) == 0:
        return False
    key = _path_key(path)
    new = [key]  # 存规整后的绝对路径，别存调用方给的原样字符串
    for old in load_recent():
        k = _path_key(old)
        if k != key:
            new.append(k)
    save_recent(new[:RECENT_MAX])
    return True


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
    """HTML 渲染委托 — 在 QTableWidget 单元格中渲染 HTML 文本.

    ⚠️ **``sizeHint`` 的宽度必须是「说明列当下的宽度」，不能是 ``option.rect.width()``**
    （2026-10-31 修正行高不随宽度变化的问题）：整行 ``ResizeToContents`` 测量时传进来的
    ``option.rect`` 是**默认宽度**（100 px），而 ``paint`` 用的却是**真实列宽**。按 100 px
    量出来的行高在宽列下会偏大、窄列下又偏小；更糟的是这个 hint 在每个平台上的用途不同
    （Qt 可能把它写进行高缓存），于是「先缩小窗口再打开」与「先打开再缩小」量出来的行高
    不一致，文字就显示不全。委托被装在「说明」列上，所以这里直接问 ``option.widget``
    要那一列的真实宽度；拿不到才退回 ``option.rect.width()``。
    """

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
        doc.setTextWidth(_column_width(option, index) or 400)
        return QtCore.QSize(int(doc.idealWidth()), int(doc.size().height()))


def _column_width(option, index):
    """取 ``option`` / ``index`` 所指向的那一列**当前的真实宽度**（拿不到返回 ``0``）.

    ⚠️ ``option.rect`` 在整行测量时是默认宽度，不能拿它当列宽用（见
    :class:`HtmlDelegate` 的说明）。
    """
    view = option.widget
    if not isinstance(view, QtWidgets.QTableView):
        return 0
    try:
        return int(view.columnWidth(index.column()))
    except Exception:  # 控件正在析构等边缘情况：交给调用方退回默认宽度
        return 0


class DemoView(QtWidgets.QTableWidget):
    """Demo 浏览器表格。

    数据来源：:func:`scan_demo_files`（内部走 ``zmlx.demos.list_demo_files()``），
    每行是 ``[相对路径, 描述, 作者, 绝对路径, 是否高亮]``。
    四列布局：文件名 | 描述 | 作者 | 运行按钮。

    表格最上面（数据行之上）是**分组行**：「最近运行 (N)」+ 它下面 N 行，然后是
    「全部示例 (M)」+ 它下面剩下的行。见模块文档的「最近运行分组」。

    ⚠️ **列表是异步载入的**：构造时只放一个「正在载入 ...」占位行，扫描在
    :class:`DemoScanThread` 里跑，结果经 :meth:`_on_data` 回到 GUI 线程填表。
    因此构造后 ``rowCount()`` 会先是 1、稍后变成真实条数 —— 调用方不要假设
    「构造完就有数据」。详见模块文档。

    ⚠️ **``rowCount()`` 与「数据条数」不是一回事**（2026-11-02 起）：前者还包含
    至多两行分组行。要「表格第几行 == 哪条数据」请用 :meth:`get_shown_data` /
    :meth:`get_shown_paths`，别自己假定两者相等。
    """

    #: 本页标签的标题（:func:`show_demo` 用它打开本页）。
    CAPTION = '示例'

    def __init__(self, parent=None):
        super(DemoView, self).__init__(parent)
        #: 扫描到的**全部**数据，口径同 :func:`scan_demo_files`。
        self.__data = []
        #: 上一次成功扫到数据时设置的工作目录（见 :meth:`_poll_running`）。
        self._demo_folder = None
        self.__loaded = False  # 是否已经成功扫过一次（空结果也算）
        self.__scanned_at = 0.0  # 上次扫描结束的 time.monotonic()
        #: 是否显示「最近运行」分组（见 :meth:`refresh` 的说明）。
        self.__show_recent = False
        #: 上一次「排到了最前的那几条」—— 变了才重建表格（见 :meth:`_poll_running`）。
        self.__recent_paths = []
        #: 上一次轮询时控制台是否在跑（用来抓「没在跑 → 在跑」这个跳变）。
        self.__was_running = False
        self._thread = None  # 在飞的扫描线程（持有引用，防被 GC）
        self._col0_width = None  # 第 0 列的自然宽度（缓存，见 _constrain_col0）
        #: 上一次「确定行高」时说明列的宽度（见 :meth:`_remind_row_heights`）。
        self._row_hint_col1 = -1
        #: 行内容换过、但还没按列宽重新测量过行高（见 :meth:`_remind_row_heights`）。
        self._row_hint_dirty = True
        #: 表格行号 → :meth:`_compose` 返回列表里的下标（**每次重建时整体重算**）。
        self._row_ids = []
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setWordWrap(True)
        self.clicked.connect(self.item_clicked)
        self.setItemDelegateForColumn(1, HtmlDelegate(self))
        self.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self._sort_order = {}  # {col: ascending}
        self._setup_columns()
        self._show_placeholder(WAITING_TEXT)
        # ⚠️ 计时器**要设 parent 为本控件**（与后台线程的规矩相反，见
        #    ``zmlx/ui/widgets/AGENTS.md``）：QTimer 随控件销毁是安全的。它只做
        #    一次 ``is_running()`` 判断，与「本页是否可见」无关 —— 关着标签页时
        #    用户照样可能在代码编辑器里跑 demo。
        self._poll_timer = QtCore.QTimer(self)
        self._poll_timer.setInterval(RECENT_POLL_MS)
        self._poll_timer.timeout.connect(self._poll_running)
        self._poll_timer.start()
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
        # ⚠️ 说明列是 Stretch：**用户拖动分隔条 / 窗口被父布局挤压**时它照样会变宽变窄，
        #    而这时本控件自己的尺寸可能一个像素都没变（``resizeEvent`` 不触发）。
        #    只靠 resizeEvent 会让「行高按旧列宽算完就不动了」，文字显示不全 ——
        #    真正要看的是**列宽**，所以在这里盯住它（见 _remind_row_heights）。
        hdr.sectionResized.connect(self._on_section_resized)

    def _show_placeholder(self, text):
        """整行显示一句提示文字（跨列），让控件立刻有内容可见."""
        self.clearSpans()
        self.setRowCount(0)  # 清掉旧的行（连同其中的按钮控件）
        self._row_ids = []
        self.setRowCount(1)
        self.setItem(0, 0, QtWidgets.QTableWidgetItem(text))
        self.setSpan(0, 0, 1, 4)
        self._col0_width = None  # 行内容变了，自然宽度缓存作废
        self._constrain_col0()
        self._row_hint_dirty = True  # 行换了，行高必须按当前列宽重算一遍
        self._remind_row_heights()

    def refresh(self, force=False, show_recent=None):
        """核对一遍 demo 目录，并（可选）展开「最近运行」分组（**立即返回，从不阻塞界面**）。

        分三种情况：

        - **还没有数据**：先显示「正在载入 ...」占位行，再起后台线程扫描。
          ⚠️ 此时分组行一定隐藏（表格只有那一行跨列占位），扫描回来之后再按
          ``show_recent`` 的决定重建；
        - **已有数据且刚刚查过**（:data:`RESCAN_INTERVAL` 秒内）：直接返回。
          「切换标签页」走的正是这条路径，因此是 0 ms 开销；
        - **已有数据但已经过时**：起后台线程核对，**不动表格**；结果真的变了
          才重建（见 :meth:`_on_data`）。

        Args:
            force: 忽略 :data:`RESCAN_INTERVAL` 闸门，强制核对一遍。显式打开
                本页的动作（``gui.show_demo()``）用它，保证「刚加了 demo」这种
                场景立刻能看到。
            show_recent: 是否显示「最近运行」分组。``None``（默认）**保持原状**，
                所以「切标签页 / 菜单『显示 → 刷新』」这类 duck-typing 调用不会
                把分组变出来、也不会把它收回去 —— 只有显式打开本页
                （:func:`show_demo`）才传 ``True``。
                ⚠️ 与 :data:`RESCAN_INTERVAL` 闸门无关：值真的变了就当场重建
                表格，不依赖目录有没有变。

        ⚠️ 上一次扫描还没回来时**总是直接返回**（不叠加线程），这一条同时解决了
        启动时的重复扫描 —— ``DemoView.__init__`` 和 :func:`show_demo` 的
        ``oper`` 会各调一次本方法，去重之后只扫一次。

        ⚠️ 本方法必须**可重复调用**：主窗口「操作 → 刷新」会 duck-typing 地调
        当前页面的 ``refresh()``（只传位置参数，不传 ``show_recent``）。
        """
        old = self.__show_recent
        if show_recent is not None:
            self.__show_recent = bool(show_recent)
        changed = self.__show_recent != old

        if self._thread is not None:
            return  # 上一次扫描还没回来，不叠加（结果到了按最新的开关重建）
        if self.__loaded and not force:
            if time.monotonic() - self.__scanned_at < RESCAN_INTERVAL:
                if changed:
                    self._rebuild()  # 目录没变，但分组要换一种排法
                return  # 刚查过：切标签页时什么都不做
        if not self.__loaded:
            self._show_placeholder(WAITING_TEXT)  # 首次：先给个占位行
        elif changed:
            self._rebuild()  # 立刻响应「展开 / 收起」，不必等这次扫描回来

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
        try:
            from zmlx.demos import get_path

            self._demo_folder = get_path()
        except Exception:  # 防御性：拿不到就退回「不判断目录」（见 _poll_running）
            self._demo_folder = None
        # ⚠️ 只把**未排序**的原始数据存下来：排序、分组都在 :meth:`_rebuild`
        #    里现算。以前这里存的是排过序的那份，于是「点列标题」会把排序叠加
        #    进缓存里，来回点几次顺序就乱了。
        candidate = list(data or [])
        if candidate == self.__data and self.rowCount() == len(self._compose()):
            return  # 一模一样：不重建、不重绘
        self.__data = candidate
        self._rebuild()

    def _compose(self):
        """把缓存的数据排成「表格行的顺序」（**纯计算**，不碰 Qt）.

        Returns:
            list: 每项是一个六元组 ::

                ('group', 分组文字, None, None, None, False)
                ('data',  相对路径, 描述, 作者, 绝对路径, 是否高亮)

        ⚠️ 分组行只是**占用整整一行**的成员，不是数据行 —— :meth:`_rebuild`
        按这里的顺序逐行放。要「表格第几行是哪条数据」一律走这里，不要直接读
        ``self.__data``。

        ⚠️ **「最近运行」没有可显示的东西时，整段降级成普通列表**：记录文件不存在
        （首次运行 / 被清理掉）、内容坏了、或者记录里的 demo 都已经被删掉，
        :func:`load_recent` 都会给出 ``[]``，这里就只输出「全部示例」一行分组 ——
        表格照常完整可读，**不会**出现一个空分组、也不会少掉任何一条 demo。
        """
        rows = self._apply_sort(list(self.__data))
        if not self.__show_recent or len(rows) == 0:
            return [self._group_row(GROUP_TEXT_ALL, len(rows))] + [
                self._data_row(x) for x in rows]

        # —— 按「最近运行」的顺序，从当前数据里挑出那几行 ——
        recent = []
        seen = set()
        if len(rows) > 0:
            by_key = {}
            for x in rows:
                by_key.setdefault(_path_key(x[3]), x)
            for path in load_recent():
                key = _path_key(path)
                if key in seen:
                    continue
                x = by_key.get(key)
                if x is None:
                    continue  # 已经不在示例目录里了（删掉了 / 改了名）
                seen.add(key)
                recent.append(x)
                if len(recent) >= RECENT_SHOWN:
                    break

        if len(recent) == 0:
            # 一条可显示的都没有（没有记录文件 / 记录失效）：只留「全部示例」
            return [self._group_row(GROUP_TEXT_ALL, len(rows))] + [
                self._data_row(x) for x in rows]

        out = [self._group_row(GROUP_TEXT_RECENT, len(recent))]
        out += [self._data_row(x) for x in recent]
        rest = [x for x in rows if _path_key(x[3]) not in seen]
        if len(rest) > 0:
            out.append(self._group_row(GROUP_TEXT_ALL, len(rest)))
            out += [self._data_row(x) for x in rest]
        return out

    @staticmethod
    def _group_row(text, count):
        """拼一个分组行（``text`` 里的 ``{}`` 换成条数）."""
        return ('group', text.format(count), None, None, None, False)

    @staticmethod
    def _data_row(x):
        """把一条原始数据转成 :meth:`_compose` 的一行."""
        return ('data',) + tuple(x)

    def _rebuild(self):
        """按缓存的数据重建表格（**纯 Qt 操作，约十几毫秒**）."""
        rows = self._compose()
        if len(rows) == 0:
            self._show_placeholder(EMPTY_TEXT)
            return

        self.setRowCount(len(rows))
        self.clearSpans()
        self._row_ids = []
        self._col0_width = None  # 行内容变了，自然宽度缓存作废

        for row_id in range(len(rows)):
            try:
                kind, name, desc, author, path, highlight = rows[row_id]
                if kind == 'group':
                    self._fill_group_row(row_id, name)
                    self._row_ids.append(None)
                    continue
                item0 = QtWidgets.QTableWidgetItem(name)
                item1 = QtWidgets.QTableWidgetItem(desc)
                item2 = QtWidgets.QTableWidgetItem(author)
                if highlight:
                    color = QtGui.QColor(200, 50, 50) if highlight is True else QtGui.QColor(highlight)
                    item0.setForeground(color)
                self.setItem(row_id, 0, item0)
                self.setItem(row_id, 1, item1)
                self.setItem(row_id, 2, item2)
                self._row_ids.append(row_id)

                # 运行按钮（仅 .py/.pyw 文件）
                ext = os.path.splitext(path)[-1].lower()
                if ext in ('.py', '.pyw'):
                    btn = QtWidgets.QPushButton('运行')
                    fpath = path
                    btn.clicked.connect(
                        lambda checked, p=fpath: self._run(p))
                    self.setCellWidget(row_id, 3, btn)
            except Exception as err:
                print(err)
                self._row_ids.append(None)
                for col_id in range(3):
                    self.setItem(row_id, col_id, QtWidgets.QTableWidgetItem(''))

        self._constrain_col0()
        self._row_hint_dirty = True  # 行换了，行高必须按当前列宽重算一遍
        self._remind_row_heights()

    def _fill_group_row(self, row_id, text):
        """把第 ``row_id`` 行做成一条**跨全部列**的分组标题.

        ⚠️ 分组行与数据行的四处不同：① 跨列（``setSpan``）；② 只留
        ``ItemIsEnabled``（不可选中 —— 它不是一条 demo，点到它不该有「选中了一
        行」的错觉，也顺带消掉了就地编辑器的隐患）；③ 前面那个向下的三角用
        **字体字符**画，不用 ``setStyleSheet``，免得与用户的
        ``zml_window_style.qss`` / 暗色模式打架（见 ``zmlx/ui/widgets/AGENTS.md``
        的「控件里的颜色」）；④ 用粗体字区分层级（``setFont`` 只改本项）。
        """
        item = QtWidgets.QTableWidgetItem(f'\u25bc  {text}')
        item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
        font = QtGui.QFont(self.font())
        font.setBold(True)
        item.setFont(font)
        self.setItem(row_id, 0, item)
        for col in range(1, self.columnCount()):
            self.setItem(row_id, col, QtWidgets.QTableWidgetItem(''))
        self.setSpan(row_id, 0, 1, self.columnCount())

    def _run(self, path):
        """由本页发起一次运行：**先记账，再交给控制台**.

        ⚠️ 顺序不能反： ``exec_file`` 会把 ``__file__`` 写进 ``app_data.space``
        并置上「正在跑」，:meth:`_poll_running` 下一拍就会看到这个跳变 —— 先记账
        才能把基线更新掉，否则同一个 demo 会被记两遍。

        ⚠️ 「运行按钮」与「点说明列」**走同一条路**（都调到本方法）：以前按钮直接
        连 ``_gui().exec_file``、点说明列另走一条，两边都得记账，迟早漏一边。
        """
        try:
            self._remember_run(path)
        except Exception as err:  # 记账失败不该挡住运行本身
            print(err)
        if self.__show_recent:
            self._rebuild()  # 最近一组变了：当场把它挪到最上面
        _gui().exec_file(path)

    def _remember_run(self, path):
        """把 ``path`` 记成「刚运行过」，并同步 :attr:`__recent_paths` 这个基线.

        ⚠️ 基线按**记录文件里的前 :data:`RECENT_SHOWN` 条**算，与
        :meth:`_poll_running` 用同一个口径（它只拿「恰好显示的这几条」来比）。
        口径一旦不一致，后续的重排会被当成「没变化」而静默跳过。
        """
        mark_run(path)
        self.__recent_paths = self._recent_head()

    @staticmethod
    def _recent_head():
        """「最近运行」记录的前 :data:`RECENT_SHOWN` 条（规整后的路径，去重保序）."""
        keys = []
        for old in load_recent():
            try:
                k = _path_key(old)
            except Exception:
                continue
            if k not in keys:
                keys.append(k)
        return keys[:RECENT_SHOWN]

    def refresh_recent(self):
        """重新读一遍「最近运行」记录并重建表格（**只重排缓存，不扫目录**）.

        平时不需要调 —— :meth:`_poll_running` 每秒自己看一次。它给「在别处改了
        记录、想让本页立刻跟上」的场合用。
        """
        if self.__loaded:
            self._rebuild()
        # 还没载入完：扫描回来时会按最新的记录重建，这里什么都不用做

    def _poll_running(self):
        """每秒看一眼：控制台是不是**刚刚**开始跑一个示例目录下的 demo.

        判据是**状态跳变**（上一拍没在跑 → 这一拍在跑），所以：同一个 demo 跑
        第二次也会记（两次之间必然先回到「没在跑」）；长任务跑到一半切回本页不会
        重复记；本页自己发起的运行已经由 :meth:`_run` 记过并更新了基线。

        ⚠️ 只认 ``app_data.space['__file__']`` **在示例目录下**的运行：别处跑的
        脚本（用户自己的算例、插件）不该出现在「最近运行的示例」里。示例目录取自
        ``zmlx.demos.get_path()``，与列表有没有扫出来无关。

        ⚠️ 这个方法**绝不能抛异常**：它在 GUI 线程的计时器里，抛出去就会刷屏。
        """
        try:
            running = bool(_gui().is_running())
        except Exception:  # 主窗口还没建好 / 没有界面：按「没在跑」处理
            running = False
        was = self.__was_running
        self.__was_running = running
        if not running or was:
            return  # 没在跑、或者上一拍就在跑（不是新发起的）
        try:
            path = self._current_running_file()
            if path is None:
                return
            mark_run(path)
            keys = self._recent_head()
            if keys == self.__recent_paths:
                return  # 记录没有变化：不重建、不重绘
            self.__recent_paths = keys
            if self.__show_recent and self.__loaded:
                self._rebuild()
        except Exception as err:  # 轮询绝不能把界面拖垮
            print(f'Error (when record recent demo): {err}')

    def _current_running_file(self):
        """取「控制台此刻在跑的那个文件」的绝对路径；不在示例目录下时返回 ``None``.

        ``__file__`` 由 ``Console.start_func`` 写进 ``app_data.space``；先在
        ``app_data`` 里找，拿不到再退回 ``sys.modules['__main__'].__file__``。
        """
        from zmlx.system import app_data

        path = app_data.space.get('__file__')
        if not isinstance(path, str) or len(path) == 0:
            import sys

            path = getattr(sys.modules.get('__main__'), '__file__', None)
        if not isinstance(path, str) or len(path) == 0:
            return None
        if not os.path.isfile(path):
            return None
        folder = self._demo_folder
        if not isinstance(folder, str) or len(folder) == 0:
            try:
                from zmlx.demos import get_path

                folder = get_path()
            except Exception:
                return None
        try:
            if _path_key(path).startswith(_path_key(folder) + os.sep):
                return path
        except Exception:
            return None
        return None

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
        self._remind_row_heights()

    def _on_section_resized(self, logical_index, old_size, new_size):
        """某一列宽度变了（可能来自用户拖动，也可能来自 Stretch 重排）.

        ⚠️ **不能只在 ``resizeEvent`` 里重算行高**：说明列的宽度会因「窗口缩小、
        被父布局 / 分隔条挤压」而变化，而这时本控件自身的尺寸可能一点都没变，
        ``resizeEvent`` 根本不会来 —— 行高就停在按旧列宽算出来的那个值上，文字被
        截断。:meth:`_remind_row_heights` 自带去重，所以哪种来源触发的都能安全合并。
        """
        if logical_index == 1:
            self._remind_row_heights()

    def _remind_row_heights(self):
        """说明列的宽度变了：让各行按**新列宽**重新计算高度.

        ``setWordWrap(True)`` + 垂直表头 ``ResizeToContents`` 只能保证「测量用的是
        当下列宽」，前提是**有人重新测量**。而行高一旦算出来，只要行数据没变，Qt 就
        不会再问一遍 —— 于是「窗口先大后小」和「先小后大」会得到两种不同的行高，
        后者文字显示不全。这里在列宽真的变了时发一个 ``dataChanged``（角色
        ``SizeHintRole``），逼视图重新测量**全部**行。

        ⚠️ **一次发全部行，不要只发一半**：整行重算时，前一行到底占多少高度取决于
        后面几行的高度 —— 「视口高度 ÷ 行高」一变，Qt 就知道「剩下的行反正看不见」，
        于是不再逐行测量，那些行的高度会**停在上一次的旧值**（实测：大窗口打开再缩到
        窄列，前 3 行是新的 79/79/79，第 4 行却还是 65、第 5 行是 51）。全发一遍，
        Qt 就得把 110 行都量一遍，量完的才是真值。

        ⚠️ **宽度没变、行也没换时什么都不做**：Windows 上 ``dataChanged`` 会让视图为
        每一行重建「运行」按钮（那是 ``setCellWidget`` 放进来的），110 行时有肉眼可见的
        顿挫；而窗口拖动时绝大多数帧的列宽是不变的（同 :meth:`_constrain_col0` 的取舍）。
        ⚠️ 反过来，**行内容换了（``_rebuild`` / ``_show_placeholder``）就必须重发一次**：
        新表按缓存列宽排出来时，行高已经按列宽量好了（见 ``HtmlDelegate.sizeHint``），
        而「载入中 → 110 行」恰好在列宽没变的情况下发生，靠 ``_row_hint_dirty`` 标记。

        ⚠️ **用 ``dataChanged`` 而不是 ``setRowHeight(row, -1)``**：后者是「逐行重设
        高度」，与垂直表头的 ``ResizeToContents`` 互相打架（高度一被显式设置就不再
        自动测量），还得自己再 ``resizeRowsToContents()``。
        """
        width = int(self.columnWidth(1))
        if width == self._row_hint_col1 and not self._row_hint_dirty:
            return  # 列宽没变、行的内容也没换：行高仍然是按这个宽度算的
        self._row_hint_col1 = width
        self._row_hint_dirty = False
        rows = self.rowCount()
        if rows <= 0:
            return
        model = self.model()
        model.dataChanged.emit(
            model.index(0, 0), model.index(rows - 1, self.columnCount() - 1),
            [QtCore.Qt.ItemDataRole.SizeHintRole])
        # 触发一次垂直方向的重排（行高是懒算的：只发信号不一定会把所有行量完）
        self.verticalScrollBar().setValue(self.verticalScrollBar().value())

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
        """点击第 0 列打开文件，第 1 列运行 demo（点到分组行则什么都不做）."""
        row = self.data_row(index.row())
        col = index.column()
        if row is None or col >= 3:
            return  # 分组行 / 占位行：没有关联的文件

        try:
            name, desc, author, path, highlight = row
            if col == 1 and os.path.isfile(path):
                self._run(path)
            elif os.path.isfile(path):
                _gui().open_code(path)
            elif os.path.isdir(path):
                from zmlx.algs import startfile
                startfile(path)
        except Exception as err:
            print(err)

    def data_row(self, row_id):
        """取「表格第 ``row_id`` 行」对应的数据；不是数据行时返回 ``None``.

        Args:
            row_id: 表格行号（含分组行、占位行）。

        Returns:
            list | None: ``[相对路径, 描述, 作者, 绝对路径, 是否高亮]``；
            分组行、占位行、越界都返回 ``None``。

        ⚠️ 返回的是**五元组**（与 ``zmlx.demos`` 那边一致），已经去掉了
        :meth:`_compose` 内部用的 ``'data'`` 类型标记。2026-11-02 第一版直接把
        :meth:`_compose` 那一行**原样**返回，调用方按五元组解包就报
        ``too many values to unpack (expected 5)`` —— 点「说明」列时必现。
        """
        if row_id is None or row_id < 0 or row_id >= len(self._row_ids):
            return None
        row = self._row_ids[row_id]
        if row is None:
            return None
        try:
            x = self._compose()[row]
        except Exception:
            return None
        if not isinstance(x, tuple) or len(x) != 6 or x[0] != 'data':
            return None  # 防御性：分组行 / 格式变了，一律当成「没有数据」
        return list(x[1:])

    def get_shown_data(self):
        """返回当前表格里**真正显示着的**数据行（顺序与表格一致，不含分组行）.

        Returns:
            list: 每项 ``[相对路径, 描述, 作者, 绝对路径, 是否高亮]``（**五元组**，
            与 :func:`scan_demo_files` 同口径；:meth:`_compose` 的 ``'data'``
            标记已经去掉）。
        """
        return [list(x[1:]) for x in self._compose() if x[0] == 'data']

    def get_shown_paths(self):
        """返回当前表格里显示的 demo 路径（顺序与表格一致）.

        Returns:
            list: 绝对路径列表。

        ⚠️ 在 :meth:`get_shown_data`（已去掉 ``'data'`` 标记）上取下标：直接在
        :meth:`_compose` 的六元组上取会**整体错一位**（2026-11-02 第一版写成
        ``x[4]``，取到的是「作者」而不是「绝对路径」）。
        """
        return [data[3] for data in self.get_shown_data()]

    def get_recent_paths(self):
        """返回「最近运行」分组里**正显示着**的路径（最近跑的在前）.

        没有「最近运行」分组（还没跑过 / 记录失效 / 未展开）时返回 ``[]``。

        ⚠️ 判据必须**同时**看两件事，少一条都会错：
        ① 表格第一个成员**就是**分组行，所以不能写成「遇到非数据行就停」（那样
           永远返回空列表）；
        ② 第一个分组行**必须真的是「最近运行」** —— 否则在「一条记录都没有」的
           常见状态下，第一个分组行是「全部示例」，跳过它就会把**全部 110 条**
           都当成最近运行（2026-11-02 自测抓到）。
        """
        comp = self._compose()
        if len(comp) == 0:
            return []
        first = comp[0]
        if first[0] != 'group' or not str(first[1]).startswith(
                GROUP_TEXT_RECENT.split('(')[0].strip()):
            return []  # 首个分组不是「最近运行」⇒ 这一组没显示
        out = []
        for x in comp[1:]:
            if x[0] != 'data':
                break  # 到下一个分组行（「全部示例」）为止
            # 六元组：('data', 相对路径, 描述, 作者, 绝对路径, 是否高亮)
            out.append(x[4])
        return out


def _gui():
    """取 ``gui`` 缓冲区（延迟导入，避免本模块在导入期就把 Qt 拉满）."""
    from zmlx.ui.gui_buffer import gui

    return gui


def show_demo():
    """显示（或切到）「示例」标签页 —— 内置 demo 的浏览器.

    ⚠️ **只通过 ``gui.get_widget`` 打开**（而不是直接 ``DemoView()``）：这样标签页只会
    **一个**，重复调用只是把已有页面切到前面。

    ⚠️ **``oper`` 里用 ``refresh(force=True, show_recent=True)``**：
    ``force=True`` 忽略 ``DemoView`` 内部的 ``RESCAN_INTERVAL`` 闸门，保证「刚加了
    demo 文件」马上能看到；``show_recent=True`` 是本页的**显式展开**动作 ——
    「最近运行」分组只在这里展开（切标签页走的普通 ``refresh()`` 不会把它变出来，
    也没有「收起」的入口，见 :meth:`DemoView.refresh`）。两条路径都是 0 ms 级的
    判断 + 必要时一次后台扫描。

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
        # 闸门），这样「刚加了 demo 文件」马上能看到；而切标签页走普通 refresh()，不受影响。
        # show_recent=True：显式打开才展开「最近运行」分组。
        w.refresh(force=True, show_recent=True)
        w.gui_restore = 'gui.show_demo()'

    _gui().get_widget(
        the_type=DemoView,
        caption=DemoView.CAPTION,
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
    """直接运行本文件时的自测：单独开一个窗口把 Demo 浏览器跑起来（**展开「最近运行」**）."""
    import sys

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    w = DemoView()
    w.refresh(show_recent=True)  # 自测要把分组那一块也显示出来，否则等于没测
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
