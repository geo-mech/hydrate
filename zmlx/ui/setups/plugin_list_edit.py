"""插件列表编辑器（``PluginListEdit``）+ 命令 ``gui.edit_setup_files`` + 「设置 → 插件」菜单项.

**本文件自含**：控件 :class:`PluginListEdit`（以及它的后台扫描线程 ``_ScanWorker``）、
入口 :func:`edit_setup_files`、菜单项与命令都在这里。

⚠️ **2026-10-31 由 ``zmlx/ui/tabs/plugin_list_edit.py`` 搬到 ``setups/``**（原模块删除、
**不留垫片**），同时把 `MainWindow.edit_setup_files` 的方法体与「设置 → 插件」那条
``add_action`` 原样搬到这里。控件本体一字未改。

为什么在 ``setups/`` 而不是 ``tabs/``
------------------------------------

判据是 ``setups/AGENTS.md`` §1 那条：**关掉它，软件还能不能正常用？**

- **不能** —— 这一页是**插件机制的开关面板本身**。把它做成一个可以被关掉的插件，
  就成了「关掉『开关』」的循环：用户一旦取消勾选，界面上**再也找不回来**的正是
  「启用 / 禁用插件」这个入口。
- 它也**带着菜单项**（``设置 → 插件``），不只是一个「被装配层打开成页面」的控件 ——
  ``tabs/`` 收的是后者。

⚠️ 由 ``setups/__init__.py`` 的 ``setup_ui()`` 统一调用（那里是**唯一**的登记点）。

菜单与命令（**与搬迁前完全一致**）
----------------------------------

=========================  ==================================================
项                          值
=========================  ==================================================
菜单                        设置 → 插件（``name='setup_files'``、``icon='plugin'``）
命令                        ``gui.edit_setup_files()``
标签页                      标题「插件」，``gui_restore = 'gui.edit_setup_files()'``
=========================  ==================================================

⚠️⚠️ **``edit_setup_files`` 与 ``name='setup_files'`` 都是「命名遗留」，一个都不能改**：

| 名字 | 谁在用 |
|---|---|
| ``gui.edit_setup_files()`` | ``zmlx://gui/edit_setup_files`` 文档链接（``tabs/readme_browser.py`` 按命令名取函数）、标签页存档串、外部脚本、``scen/ai_assistant`` |
| action ``name='setup_files'`` | ribbon 配置、已保存的界面布局（按 ``name`` 定位这一项） |

名字里那个 ``setup_file`` 是「启动文件」这个旧叫法的残留 —— 显示文字早就改成「插件」了，
但**按钮 id 与命令名没动**。详见 ``../ReadMe.md`` 的「命名遗留」一节。

下面是控件本身的说明
--------------------

插件列表编辑器（「设置 → 插件」里的那个列表）.

每一行 = 一个插件，七列分别是「默认加载」「优先级」「名称」「描述」「来源」「状态」「临时加载」：

==========  ==============================================================
列           能做什么
==========  ==============================================================
**默认加载** ☑ / ☐ —— 取消勾选的插件**启动时不执行**（这段代码整个不跑）
**优先级**   高 / 正常 / 低 —— 只决定**执行**先后，任何档位都不改列表顺序
**名称**     插件自报的名字；**鼠标悬停显示完整文件路径**
**描述**     插件自报的一句话说明
**来源**     自动（目录扫描发现）/ 手动（用「添加」登记的）
**状态**     已执行 / 未执行 / 失败 / 已禁用 / 文件不存在
**临时加载** 按钮：**当场**执行这个插件，不必勾选、不必重启
==========  ==============================================================

⚠️ **「临时加载」与「默认加载」是两件事**：勾选决定**下次启动**跑不跑（持久设置，
写进 ``zml_plugins``）；「加载」只管**现在**跑一次（运行时事实，不写盘）。
所以一个「已禁用」的插件照样可以临时加载 —— 重启之后它仍然不会自己跑。

⚠️ 第一列 2026-10-25 由「启用」改名为「**默认加载**」：它管的正是「**启动时要不要
自动加载**」，而「启用」听起来像「这个插件现在能不能用」—— 实际不是（禁用的插件照样
能临时加载，见上一段）。⚠️ **机制侧的称呼没变**（``is_disabled`` /「禁用」= 仅启动
过滤，见 ``plugins/AGENTS.md`` §3）：改的只是这一列的显示文字，设置文件
``zml_plugins`` 里的标记、函数名一个都没动。

⚠️ **每个插件在本次运行里只加载一次**：``plugins.load_now`` 用进程级的
``_loaded`` 表拦住第二次（成功了按钮就变成「已加载」并置灰）。失败**不**拦截 ——
用户改完文件可以再点一次重试，失败原因在按钮的 tooltip 里。

⚠️ **执行通道**：按钮**不自己起线程**，而是 ``gui.start(...)`` —— 跑在界面自己的
**控制台线程**里（与启动时 ``load_all`` 同一条通道）；界面更新经 ``post_task``
回到 GUI 线程。控制台当时正忙（在跑别的脚本）时会先提示、不排队。

⚠️ **没有「文件」列**（2026-10-19 移除）：路径动辄上百字符，占掉近一半宽度，却只在
排查问题时才看。现在**完整路径放在名称列的 tooltip 里**（悬停即见），双击任意一行
仍可在代码编辑器中打开。路径同时存在名称单元格的 ``UserRole`` 里 —— 列表不再有任何
一列的 ``text()`` 是路径，取路径一律走 :meth:`PluginListEdit._row_path`。

⚠️ **「来源」决定能不能移除**：只有**手动**登记的才能移除（与
:func:`zmlx.ui.plugins.add_file` 成对）；**自动**发现的移除了也会在下次启动
扫描时自己回来，所以不允许移除 —— 不想让它跑请**取消勾选「默认加载」**。

⚠️ **没有拖动排序**：用户控制的是「是否默认加载」与「优先级」，不排顺序。列表顺序
= 用户登记的（按加入先后）在前、自动发现的在后。理由见
:mod:`zmlx.ui.plugins` 的模块文档。

⚠️ 「状态」列来自 ``app_data`` 里的 ``gui_setup_logs``（上次启动时 ``load_all``
的逐条记录）。改了「默认加载」**必须重启**才生效，所以这里只如实显示「上次启动时
发生了什么」，不假装「现在改了就马上跑」。

旧的类名 ``SetupFileEdit`` 与文件名 ``setup_file_edit.py`` 已改为
``PluginListEdit`` / ``plugin_list_edit.py``（「插件列表」比「启动文件编辑」准确）。

⚠️ **没有留兼容转发层**：插件机制这块没有任何外部调用（本仓与外部工作区都零引用），
旧路径 ``zmlx.ui.tabs.setup_file_edit`` 直接失效 —— 留着转发只会让「旧名到底还活
多久」变成一个没人维护的悬案。

Created by DeepSeek, 2026-10-18
Modified by DeepSeek, 2026-10-18: 按收敛后的 8 个插件 API 重写；去掉拖动排序
Modified by DeepSeek, 2026-10-18: 改名为 PluginListEdit / plugin_list_edit.py；
    加「来源」列；移除只对手动登记的生效（自动发现的给出明确提示）
Modified by DeepSeek, 2026-10-19: 去掉「文件」列 —— 路径改存名称单元格的 ``UserRole``，
    并在名称列 tooltip 里显示完整路径；删除 `_PathText` / `_PathDelegate`（路径省略
    绘制已无用处），列宽重新分配给名称与描述两列
"""

import os

from zmlx.system import app_data, execute_once
from zmlx.ui import plugins
from zmlx.ui.alg import create_action
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets

# 优先级的显示顺序与文字（值本身是英文，见 plugins 模块文档）
_PRIORITY_TEXT = {'high': '高', 'normal': '正常', 'low': '低'}
_PRIORITY_ORDER = ['high', 'normal', 'low']

#: 优先级色块（``None`` = 不画色块，即「正常」保持默认外观）。
#:
#: ⚠️ **亮色 / 暗色各一套**：暗色下用浅一档的色，否则深红 / 深绿在深色背景上
#: 对比度不足（见 ``widgets/AGENTS.md`` 的「控件里的颜色」一节）。
#: ⚠️ **只画 ``QIcon`` 色块，不给文字 ``setStyleSheet('color: ...')``**：那样会
#: 盖掉用户可编辑的 ``zml_window_style.qss``，且 ``QComboBox`` 的弹出列表未必跟着变。
_PRIORITY_COLOR = {
    'high': ('#c62828', '#ef9a9a'),      # 红：亮色 / 暗色
    'normal': None,
    'low': ('#2e7d32', '#a5d6a7'),       # 绿：亮色 / 暗色
}

#: 优先级色块的边长（像素）。
_PRIORITY_DOT = 10

# 列的编号（改列顺序时只改这里）
_COL_ENABLED = 0
_COL_PRIORITY = 1
_COL_NAME = 2
_COL_DESC = 3
_COL_SOURCE = 4
_COL_STATE = 5
_COL_LOAD = 6

# 名称列的最小宽度：「螺螺是方块」这种 5 个字的名字别被压成「…」
_COL_NAME_MIN_WIDTH = 90

#: 路径存在名称单元格的这个角色里（``text()`` 是给人看的名字，不是路径）
_PATH_ROLE = QtCore.Qt.ItemDataRole.UserRole


def _norm_key(path):
    """把路径规范化成「比较 / 查日志用」的键（绝对 + 按平台归一大小写）."""
    return os.path.normcase(os.path.abspath(path))


class _StateLog:
    """从 ``gui_setup_logs`` 里读出每个插件的上次执行结果."""

    @staticmethod
    def get():
        """返回 ``{规范化路径: '已执行' | '失败：<原因>'}``."""
        result = {}
        logs = app_data.get('gui_setup_logs', None)
        if not isinstance(logs, (list, tuple)):
            return result
        for line in logs:
            if not isinstance(line, str):
                continue
            if line.startswith('Exec File: '):
                result.setdefault(_norm_key(line[len('Exec File: '):].strip()),
                                  '已执行')
            elif 'path = ' in line and 'error = ' in line:
                # 形如 "path = <路径>, error = <原因>"
                _, _, rest = line.partition('path = ')
                path, _, error = rest.partition(', error = ')
                result[_norm_key(path.strip())] = f'失败：{error.strip()}'
            elif line.startswith('Skipped (disabled): '):
                path = line[len('Skipped (disabled): '):].strip()
                result[_norm_key(path)] = '已跳过（禁用）'
            elif line.startswith('Skipped (missing): '):
                path = line[len('Skipped (missing): '):].strip()
                result[_norm_key(path)] = '已跳过（文件不存在）'
        return result

    @staticmethod
    def text(path, log, disabled=None):
        """给一个插件算状态文字.

        Args:
            path: 插件文件路径。
            log: :meth:`get` 的返回值。
            disabled: 这个插件是否禁用；``None`` 表示现场算。
                ⚠️ 传进来是为了**避免重复解析名单** —— ``plugins.is_disabled``
                内部要整份解析 ``zml_plugins``，逐个插件各调一次会明显变慢
                （实测 19 个插件 1.6 ms）。调用方通常在 :func:`collect_states` 里
                已经算过一次，直接传进来即可。

        Returns:
            str: 例如 ``'已执行'`` / ``'失败：...'`` / ``'已禁用（不执行）'``。
        """
        if not os.path.isfile(path):
            return '文件不存在'
        if disabled is None:
            disabled = plugins.is_disabled(path)
        if disabled:
            return '已禁用（不执行）'
        found = log.get(_norm_key(path))
        if found is not None:
            return found
        return '未执行（重启后执行）'

    @staticmethod
    def is_normal(path, log, disabled=None, state=None):
        """这条记录是不是「一切正常」（决定状态列要不要加警告图标）.

        Args:
            path: 插件文件路径。
            log: :meth:`get` 的返回值。
            disabled: 是否禁用（``None`` = 现场算；理由同 :meth:`text`）。
            state: :meth:`text` 已算出的状态文字（``None`` = 现场算）。
        """
        if not os.path.isfile(path):
            return False
        if disabled is None:
            disabled = plugins.is_disabled(path)
        if disabled:
            return False
        if state is None:
            state = _StateLog.text(path, log, disabled)
        return '失败' not in state


#: 正在跑的扫描线程（模块级强引用）.
#:
#: ⚠️ **线程的 parent 一律留空**，靠这张表持有强引用。理由与 ``check_count_view``
#: 同一条：走标签页关闭用的是 ``TabWidget.close_tab`` → ``deleteLater()``，会连同
#: **子对象**一起销毁；线程若以控件为 parent，就会在还在跑的时候被析构 ——
#: ``QThread: Destroyed while thread is still running``，那是**进程级崩溃**，
#: ``try/except`` 兜不住。
#:
#: 挂在这里线程一定能跑完；控件销毁后迟到的结果由 :func:`_is_deleted` 拦掉。
_RUNNING_SCANNERS = []


def _forget_scanner(worker):
    """把已经跑完的线程从登记表里摘掉（主线程调用）."""
    try:
        _RUNNING_SCANNERS.remove(worker)
    except ValueError:
        pass


def _is_deleted(obj):
    """判断一个 Qt 对象的底层 C/C++ 对象是否已经被销毁.

    ⚠️ **为什么需要它**：扫描结果的槽是用 ``lambda`` 连的，而 Qt 只能对
    「接收者是 QObject 的**绑定方法**」自动断连 —— lambda 没有接收者对象，控件被
    ``deleteLater()`` 销毁后连接依然有效，线程回来时照样被调用，于是在一个已经
    死掉的控件上碰子控件，抛::

        RuntimeError: wrapped C/C++ object of type QTableWidget has been deleted

    （``check_count_view.py`` 与 ``image_browser.py`` 都踩过同一个坑。）

    Args:
        obj: 任意 Qt 对象。

    Returns:
        bool: 底层对象已被销毁返回 True。
    """
    # ⚠️ 名字必须**按绑定逐个试**：PyQt6 的 sip 在 ``PyQt6.sip`` 下，顶层
    #    ``import sip`` 在 PyQt6 环境里找不到（会静默退化成「没被删」= 没生效）。
    for name in ('PyQt6.sip', 'PyQt5.sip', 'sip', 'shiboken6', 'shiboken2'):
        try:
            mod = __import__(name, fromlist=['_'])
        except ImportError:
            continue
        try:
            return bool(mod.isdeleted(obj))
        except Exception:
            return False
    return False


class _ScanWorker(QtCore.QThread):
    """在后台线程里收集插件列表与各插件的元信息（**绝不碰界面**）.

    ⚠️ **为什么必须放线程**：``update_items()`` 里最贵的一步是 ``plugins.get_meta()`` ——
    它要**读每个插件文件的正文**再交给 ``code_config`` 解析 ``# **`` 配置。实测
    50 个插件约 **700 ms**（每个 ~14 ms，其中 ``read_text`` 占 ~11 ms，是真实 I/O，
    优化不掉）。插件数量取决于自动扫描找到多少外部 ``zml_plugin.py``，在别人的机器
    上可能远多于开发机的 10 个 —— 放在 UI 线程里就是「点一下『设置 → 插件』卡住
    再出页面」。

    ⚠️ 线程里**只算数据、不建控件**：算好的快照经 :attr:`sig_done` 发回主线程，
    由 :meth:`PluginListEdit._apply` 铺行。

    Attributes:
        sig_done: 信号，携带一份快照（``list[dict]``，见 :meth:`run`）。
    """

    sig_done = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        """初始化。

        Args:
            parent: Qt 父对象。⚠️ 正常调用应当**留空** —— 线程的 parent 设成控件
                会让它在控件被销毁时连带析构 = 进程崩溃（见
                :data:`_RUNNING_SCANNERS`）。
        """
        super().__init__(parent)
        self.setObjectName('PluginListScanWorker')

    def run(self):
        """线程体：算出每个插件的一行所需数据，装进 list 发回主线程."""
        rows = []
        try:
            rows = collect_rows()
        except Exception as err:     # 防御性：扫描失败也要让界面退出「扫描中」
            print(f'Error (when scanning plugins): {err}')
        self.sig_done.emit(rows)


def collect_rows():
    """收集插件列表的**全部纯数据**（可在任意线程调用，不碰界面）.

    ⚠️ 这是「**重扫**」：会走 ``plugins.get_files()``（顺带首次扫描目录、把新出现的
    ``zml_plugin.py`` 并入名单）并读每个插件的文件头。**插件集合基本固定**，日常
    刷新用不着它 —— 那种场合请用 :func:`collect_states`（只重算会变的那几项）。

    Returns:
        list[dict]: 每项含 ``path`` / ``disabled`` / ``priority`` /
        ``name`` / ``desc`` / ``standard`` / ``state`` / ``normal``。
    """
    log = _StateLog.get()
    rows = []
    for path in plugins.get_files():
        meta = plugins.get_meta(path)
        rows.append({
            'path': path,
            'disabled': plugins.is_disabled(path),
            'priority': plugins.get_priority(path),
            'name': meta['name'],
            'desc': meta['desc'],
            'standard': plugins.is_standard(path),
            'state': _StateLog.text(path, log),
            'normal': _StateLog.is_normal(path, log),
        })
    return rows


def collect_states(paths):
    """按给定的插件路径**只重算会变的那几项**（不扫目录、不读文件正文）.

    插件集合在多数会话里是固定的（内置 12 个 + 外部项目里那几个），而
    ``plugins.get_meta()`` 本身已经按 ``(路径, mtime)`` 缓存。于是「再看一眼列表」
    真正会变的东西只有三样：

    - **默认加载 / 优先级**：用户可能刚勾过、刚改过；
    - **状态**：``plugins.is_loaded()``（临时加载过没有）、上次执行的结果
      （``app_data`` 的 ``gui_setup_logs``）、以及文件有没有被删掉；
    - **临时加载按钮**：由上面两项决定（见 ``_sync_load_button``）。

    ``name`` / ``desc`` / ``standard`` **不在这里重算** —— 它们要么来自插件文件
    （mtime 没变就不会变），要么来自名单标记（本控件一改就自己刷那一格）。

    ⚠️⚠️ **必须批量取状态，不要逐个调 ``is_disabled`` / ``get_priority``**（2026-10-22）：
    这两个函数内部各自调 ``_registry.find()`` → ``get_entries()``，而那一步要
    **读名单字符串并整份解析**。逐个查 19 个插件 = 解析 4×19 次 —— 实测
    ``collect_states`` **6.5 ms**，其中 76% 耗在这上面。而 ``get_state_list()``
    只解析**一次**、返回全部记录，再按路径查字典。

    ⚠️ 这个函数在**切标签页的路径上**（``MainWindow.refresh`` → 控件 ``update_items``
    → :meth:`PluginListEdit._refresh_states` → 本函数），所以省下来的就是
    用户切回插件页时感觉到的那一下卡顿。

    Args:
        paths: 要重算的插件路径（**顺序即表格的行序**）。

    Returns:
        list[dict]: 每项含 ``path`` / ``disabled`` / ``priority`` / ``state`` /
        ``normal``（键是 :func:`collect_rows` 的子集）。
    """
    log = _StateLog.get()
    # ★ 一次取全部记录：避免「每个插件都把名单重新解析一遍」
    by_key = {_norm_key(item['path']): item
              for item in plugins._registry.get_state_list()}
    rows = []
    for path in paths:
        item = by_key.get(_norm_key(path), None)
        if item is None:
            # 不在名单里（例如尚未迁移的老登记表）：退回逐个查，语义不变
            disabled = plugins.is_disabled(path)
            priority = plugins.get_priority(path)
        else:
            priority = item['priority']
            # 三态判定，与 ``_registry.is_disabled`` **完全一致**：
            #   · 用户表过态（``choice`` 非 None）→ 名单里的 ``disabled`` 标记；
            #   · 没表过态 → 插件自报的默认值。
            # ⚠️ 这里**不能**再调 ``plugins.is_disabled(path)`` 做回落 —— 它内部
            #    又会 ``find()`` 重新解析一遍名单。实测 19 个插件**全部**走这条
            #    回落（用户没表过态），等于白优化。``get_state_list`` 已经告诉我们
            #    「有没有表态」，而「默认值」只是读插件文件头（``get_meta``，
            #    按 mtime 缓存，很便宜）。
            if item['choice'] is not None:
                disabled = item['disabled']
            else:
                disabled = not plugins.get_meta(path)['enabled']
        state = _StateLog.text(path, log, disabled)
        rows.append({
            'path': path,
            'disabled': disabled,
            'priority': priority,
            'state': state,
            'normal': _StateLog.is_normal(path, log, disabled, state),
        })
    return rows


class PluginListEdit(QtWidgets.QTableWidget):
    """插件列表（七列：默认加载 / 优先级 / 名称 / 描述 / 来源 / 状态 / 临时加载）.

    ⚠️ **构造时不出数据**：本控件不在 ``__init__`` 里扫描 —— 使用方在**显示之后**
    调 :meth:`update_items`（「设置 → 插件」由 ``main.edit_setup_files`` 的 ``oper`` 调）。
    理由见 ``__init__`` 末尾的注释（两处都调会扫两遍并重建表格）。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(
            ['默认加载', '优先级', '名称', '描述', '来源', '状态', '临时加载'])
        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setDragDropMode(
            QtWidgets.QAbstractItemView.DragDropMode.NoDragDrop)  # 不支持排序
        self._loading = False  # 搭界面时不触发保存
        self._loading_plugin = False  # 正在临时加载（防连点）
        self._resizing = False  # 正在分配列宽（防止 setColumnWidth 递归）
        self._scan_seq = 0  # 扫描序号：只有最新一次的结果会铺到界面上
        self._scan_running = False  # 有一轮扫描正在进行（见 refresh 的合并规则）
        self._refresh_again = False  # 扫描期间又有人要求刷新（铺完再补一轮）
        self._scanners = []  # 本控件发起的扫描线程（关标签时清空引用）
        #: 扫描完成后要选中的路径（``None`` = 不选）。见 :meth:`select_after_refresh`。
        self._pending_select = None

        header = self.horizontalHeader()
        mode = QtWidgets.QHeaderView.ResizeMode
        header.setSectionResizeMode(_COL_ENABLED, mode.ResizeToContents)
        header.setSectionResizeMode(_COL_PRIORITY, mode.ResizeToContents)
        header.setSectionResizeMode(_COL_SOURCE, mode.ResizeToContents)
        header.setSectionResizeMode(_COL_STATE, mode.ResizeToContents)
        header.setSectionResizeMode(_COL_LOAD, mode.ResizeToContents)
        # 名称、描述两列**分享**剩余宽度（见 _fit_columns）
        header.setSectionResizeMode(_COL_NAME, mode.Interactive)
        header.setSectionResizeMode(_COL_DESC, mode.Interactive)
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(24)

        self.doubleClicked.connect(self._on_double_clicked)

        # ⚠️ **构造时完全不读数据**（也**不**扫目录）：这里**刻意不调 update_items()** ——
        #    打开「设置 → 插件」时，``TabWidget.get_widget`` 的 ``oper`` 已经会调一次
        #    （见 ``main.edit_setup_files``），两处都调就会**扫两遍**：第二次 ``_apply``
        #    会 ``_clear_cells()`` 把刚铺好的行（含按钮）全部销毁重建，用户看到的是
        #    「列表闪一下」，实测还会让刚点下去的按钮变成悬空引用。
        #    数据由使用方在**显示之后**调 :meth:`update_items` 拉取；本类的 ``test_1`` 也是这么做的。

    def resizeEvent(self, event):
        """窗口尺寸变化时重新分配「名称 / 描述」两列的宽度."""
        super().resizeEvent(event)
        self._fit_columns()

    def _fit_columns(self):
        """把剩余宽度分给「名称 / 描述」两列.

        分配顺序（按「重要性」）：
        1. **名称**至少 ``_COL_NAME_MIN_WIDTH``（它是用户最先看的东西）；
        2. **剩下全给描述** —— 描述是纯附加信息，窄了让它自己省略即可。

        ⚠️ 这两列都用 ``Interactive`` 而不是 ``Stretch``：``Stretch`` 会把宽度
        平均摊到「剩余空间」，窗口一窄就摊得只剩几个字符。用 ``Interactive`` +
        自己算，才能给名称留下限；实在放不下时整体出横向滚动条，而不是把内容
        压没。

        ⚠️ ``_resizing`` 防递归：``setColumnWidth`` 会触发 ``sectionResized``。
        """
        if self._resizing:
            return
        fixed = sum(self.columnWidth(col) for col in range(self.columnCount())
                    if col not in (_COL_NAME, _COL_DESC))
        free = self.viewport().width() - fixed

        name = max(_COL_NAME_MIN_WIDTH, int(free * 0.28))
        desc = max(80, free - name)

        self._resizing = True
        try:
            for col, width in ((_COL_NAME, name), (_COL_DESC, desc)):
                if width != self.columnWidth(col):
                    self.setColumnWidth(col, width)
        finally:
            self._resizing = False

    # ---------------------------------------------------------------- 读
    def update_items(self):
        """重新收集插件数据并在**后台线程**里算好，算完再**就地更新**界面.

        ⚠️⚠️ **刻意不叫 ``refresh``**（2026-10-22 改名）：``MainWindow.update_items()``
        会在**每次切到这个标签页**时调 ``get_current_widget().refresh()``（它挂在
        ``TabWidget.currentChanged`` 上）。本控件的状态**全都由自己的交互触发**
        —— 勾选、改优先级、点「临时加载」、以及打开时的 ``oper`` —— 一个都不依赖
        「切回来时自动刷一遍」。叫 ``refresh`` 只会让用户每次切到这一页都白算一遍
        （19 行 × 重算状态 + 重写状态格），表现出来就是**切到这个标签时有卡顿**。

        ⚠️ **不在 UI 线程里直接算**：``collect_rows()`` 要给每个插件调
        ``plugins.get_meta()``，那一步**读文件正文**，实测 50 个插件约 700 ms。
        插件数量取决于自动扫描能找到多少外部 ``zml_plugin.py``，在别人的机器上
        可能远多于开发机 —— 放在 UI 线程里就是「点一下『设置 → 插件』卡住再出
        页面」（2026-10-18 用户报告的现象）。

        ⚠️ 因此本方法是**异步**的：立刻返回，界面稍后由 :meth:`_on_scanned` 填好。

        ⚠️⚠️ **默认不重建表单，只更新状态**（2026-10-21 改）：
        结果回来之后走 :meth:`_apply_changes` —— **行还是那几行、控件还是那些控件**，
        只把「该显示的值变了」的那几格写进去：

        - 行数、行序、每个位置的路径都没变 ⇒ 只改 item 文字、勾选框、下拉框选项
          与「临时加载」按钮的状态，**一个控件都不重建、一行都不重排**；
        - 只有「多了 / 少了 / 换了插件」（路径序列变了）才 :meth:`_apply` 重建 ——
          Qt 没有「就地替换单元格控件」的便宜做法，插入 / 删除行也会让
          ``setCellWidget`` 建的控件跟着重排，不如一次建干净。

        改之前：结果一到就 ``_clear_cells()`` 把整张表连按钮一起销毁，再逐行重建
        （并先把表格清成一行「正在扫描…」）—— 用户看到「内容全部消失再重建」。
        而打开插件页这一个动作本来就会招来两次 ``update_items()``
        （``MainWindow.get_widget`` 一次、``oper`` 一次），于是那一下**发生两次**。

        ⚠️ 重复调用是安全的：**新的扫描会让旧的作废**（见 :attr:`_scan_seq`）——
        用户连点几次「刷新」不该让几次扫描的结果轮流覆盖界面。

        ⚠️ **「正在跑的时候又被要求刷新」不进新的一轮，只记一笔**：打开「设置 → 插件」
        这一个动作会招来好几处刷新请求（``MainWindow.get_widget`` 里的 ``update_items()``、
        ``TabWidget`` 的 ``oper``）。若每来一次就起一个 ``_ScanWorker``，同一份数据
        就会被算好几遍。这里改成：扫描期间只置 :attr:`_refresh_again`，这一轮铺完
        再补一次 —— 既不会丢请求，也不会叠出好几轮。

        ⚠️⚠️ **插件集合固定时，根本不用「重扫」**（2026-10-21 加）：
        表格里已经有内容时，走的是 :meth:`_refresh_states` —— 只按**现有行**重算
        默认加载 / 优先级 / 状态（:func:`collect_states`，实测 19 个插件 < 1 ms，就在
        UI 线程里同步做完），**不起线程、不扫目录、不读文件正文、不动表格结构**。
        理由很直接：自动发现的插件总是那几个，能变的只是「刚才临时加载了什么、
        执行成功没有、文件还在不在」。

        只有**表格还是空的**（第一次显示）才真正 :func:`collect_rows` 扫一遍并铺表。
        想强制重扫目录（例如新装了插件），用右键「恢复默认」（它调 ``plugins.rescan()``）
        或 :meth:`_rescan_and_apply`。
        """
        if self._scan_running:
            self._refresh_again = True
            return
        if self.rowCount() > 0 and not _is_deleted(self):
            # ★ 快速路径：表单原样保留，只把「状态」这一层重算并就地写回。
            self._refresh_states()
            return
        self._rescan_and_apply()

    def _refresh_states(self):
        """只重算各插件**会变的状态**并就地更新（同步、极轻、不碰表格结构）.

        见 :func:`collect_states` 的说明：插件集合固定时，唯一会变的就是
        「默认加载 / 优先级 / 状态」。这里连 ``_show_scanning`` 都不调 —— 没有异步、
        没有中间态，用户点一下看到的只是勾选框 / 状态文字被更到最新值，
        表单本身**一个控件都不重建**。
        """
        paths = [self._row_path(row) for row in range(self.rowCount())]
        if any(path is None for path in paths):   # 行里没有路径（异常状态），老实重扫
            self._rescan_and_apply()
            return
        try:
            rows = collect_states(paths)
        except Exception as err:   # 取状态不该让整页失败
            print(f'Error (when refreshing plugin states): {err}')
            return
        self._loading = True
        try:
            for row, data in enumerate(rows):
                self._update_row(row, data)
        finally:
            self._loading = False
        self._fit_columns()
        path, self._pending_select = self._pending_select, None
        if path is not None:
            self._select_path(path)

    def _rescan_and_apply(self):
        """**重扫**：重建插件名单并铺表（后台线程）. 仅用于首次显示 / 强制重扫.

        ⚠️ 重扫要在**后台线程**里做：``collect_rows()`` 会给每个插件调
        ``plugins.get_meta()``，那一步**读文件正文**，实测 50 个插件约 700 ms，
        放在 UI 线程就是「点一下『设置 → 插件』卡住再出页面」（2026-10-18 用户报告）。
        """
        self._scan_running = True
        self._scan_seq += 1
        seq = self._scan_seq

        worker = _ScanWorker()
        # ⚠️ 线程的 parent 留空、登记到模块级 _RUNNING_SCANNERS：
        #    见 _RUNNING_SCANNERS 的说明（否则关标签时进程崩溃）。
        worker.sig_done.connect(
            lambda rows, s=seq: self._on_scanned(s, rows))
        worker.finished.connect(lambda w=worker: _forget_scanner(w))
        worker.finished.connect(worker.deleteLater)
        _RUNNING_SCANNERS.append(worker)
        self._scanners.append(worker)

        # ⚠️ **表格还是空的时候不动它**（2026-10-21 加）：控件**首次显示**时本来就
        #    是空的、用户什么也没看见 —— 摆一行「正在扫描…」再抹掉，只是多一次重建
        #    和一次跨列 ↔ 单列的重排版。已有内容时才需要标记：那时用户正看着旧数据，
        #    得让他知道正在重扫（见 _show_scanning，它只擦格子、不动行）。
        if self.rowCount() > 0:
            self._show_scanning()
        worker.start()

    def _show_scanning(self):
        """扫描期间的标记：**只擦掉旧的格子，不动行**.

        ⚠️ **不再把表格清成一行的占位**（2026-10-21 改）：占位行配合 ``setSpan``
        会把整张表清空、再重排一次跨列，视觉上就是「内容全部消失」。现在只把每格的
        item / cellWidget 去掉 —— **行数与行高都还在**，:meth:`_apply_changes` 会把
        新内容原地写回去；扫描很快时用户几乎看不到中间态，而不是看到表格闪成空白。
        """
        self._loading = True
        try:
            self._clear_cells()
        finally:
            self._loading = False

    def _on_scanned(self, seq, rows):
        """扫描线程的结果槽（主线程调用）.

        Args:
            seq: 发起这次扫描时的序号；**不是最新的一次就整个丢弃**。
            rows: :func:`collect_rows` 的返回。
        """
        if _is_deleted(self):
            return
        if seq != self._scan_seq:
            self._scan_running = False   # 这份作废了，但这一轮确实结束了
            return
        self._apply_changes(rows)
        self._scan_running = False
        # 扫描期间收到的刷新请求：现在补一轮（见 refresh 的说明）
        if self._refresh_again:
            self._refresh_again = False
            self.update_items()

    def _apply_changes(self, rows):
        """把扫描结果写进表格：**能就地改的就只改，只有行结构变了才重建**.

        判据一句话：**「这一格该显示什么」与「它现在显示什么」不同，才碰它**。

        - 行数一样、且每个位置的路径都一样 ⇒ 走 :meth:`_update_row` 逐格比差异，
          表格的控件全部保留（用户刚点的按钮、选中的行、滚动位置、列宽都不动）；
        - 否则（插件多了 / 少了 / 顺序变了）⇒ 退回 :meth:`_apply` 重建。

        Args:
            rows: :func:`collect_rows` 的返回。
        """
        if not self._same_paths(rows):
            self._apply(rows)
            return

        self._loading = True
        try:
            for row, data in enumerate(rows):
                self._update_row(row, data)
        finally:
            self._loading = False
        self._fit_columns()   # 名称 / 描述的文字变了，列宽可能跟着变

        # ★ 「扫描完成后选中某一行」在这里兑现（``update_items()`` 是异步的，见
        #   select_after_refresh）。⚠️ 无论找没找到都要清掉 pending —— 否则它会一直
        #   挂到下一次刷新，在用户完全没预期的时刻突然选中一行。
        path, self._pending_select = self._pending_select, None
        if path is not None:
            self._select_path(path)

    def _same_paths(self, rows):
        """扫描结果的路径序列与表格当前的行是否一一对应（且顺序相同）.

        Returns:
            bool: 一一对应返回 True（调用方走「就地更新」），否则走整表重建。
        """
        if self.rowCount() != len(rows):
            return False
        for row, data in enumerate(rows):
            if self._row_path(row) != data['path']:
                return False
        return True

    def _update_row(self, row, data):
        """**就地**更新一行里「会变的那几格」：默认加载 / 优先级 / 状态 / 临时加载按钮.

        ⚠️ **只碰会变的格子**（2026-10-21 定）：名称、描述、来源三列来自插件文件头
        （``get_meta``，按 mtime 缓存）与名单标记，**重新看一遍列表不会让它们变**；
        真要它们变（新装 / 改名 / 改描述），那条路径会把整张表 :meth:`_apply` 重建，
        因此本方法不必也不该去写它们 —— 少碰三列就少三次重绘，也少一类「把用户
        刚编辑的文字冲掉」的风险。

        ⚠️ 各列更新方式不同，不能一律 ``setItem``：

        - **启用**：``QCheckBox`` 只 ``setChecked``，不重建（重建会让用户手里的点击
          失效）。⚠️ 必须先 ``blockSignals`` —— 否则会反过来调
          ``_on_enabled_changed`` 再写一次配置；
        - **优先级**：同理只 ``setCurrentIndex``（``_on_priority_changed`` 会再触发刷新）；
        - **状态**：``item`` 与 ``cellWidget`` 二选一，切换时必须显式移走另一个
          （见 :meth:`_set_state_cell` 的说明）；
        - **临时加载**：复用 :meth:`_sync_load_button` —— 它本来就是「按当前事实
          重算按钮样子」的纯函数。

        Args:
            row: 行号。
            data: :func:`collect_rows` 或 :func:`collect_states` 的一项
                （后者只有 ``path`` / ``disabled`` / ``priority`` / ``state`` /
                ``normal`` 五个键，本方法只用到这些）。
        """
        holder = self.cellWidget(row, _COL_ENABLED)
        check = holder.findChild(QtWidgets.QCheckBox) if holder else None
        if check is not None and check.isChecked() != (not data['disabled']):
            check.blockSignals(True)
            try:
                check.setChecked(not data['disabled'])
            finally:
                check.blockSignals(False)

        holder = self.cellWidget(row, _COL_PRIORITY)
        # ⚠️ 优先级格里**直接**放的就是 ``QComboBox``（见 ``_make_row``），不是容器 ——
        #    所以 ``findChild`` 找不到它（它不会在自己的子树里找到自己）。
        #    这里先认「就是 combo」，再退回 ``findChild``（兼容以后若真包一层容器）。
        combo = holder if isinstance(holder, QtWidgets.QComboBox) else (
            holder.findChild(QtWidgets.QComboBox) if holder else None)
        if combo is not None and combo.currentData() != data['priority']:
            combo.blockSignals(True)
            try:
                # ★ 连图标一起换：``setCurrentIndex`` 只换文字，**不改**该项的图标 ——
                #   跟着「高 / 低」走的色块必须在这里重画，否则色块会停在旧优先级上。
                index = _PRIORITY_ORDER.index(data['priority'])
                # ⚠️ ``setItemIcon`` **不接受 None**：切回「正常」时要用**空 QIcon**
                #    显式清掉色块，否则会抛 TypeError。
                icon = self._priority_icon(data['priority'], self._is_dark(self))
                combo.setItemIcon(index, icon if icon is not None else QtGui.QIcon())
                combo.setCurrentIndex(index)
            finally:
                combo.blockSignals(False)

        self._set_state_cell(row, data['state'], data['normal'])

        holder = self.cellWidget(row, _COL_LOAD)
        button = holder.findChild(QtWidgets.QPushButton) if holder else None
        if button is not None:
            self._sync_load_button(button, data['path'])

    def _update_item_text(self, row, col, text):
        """给一个只读 item 换文字（一样就什么都不做，免得白触发一次重绘）."""
        item = self.item(row, col)
        if item is None:
            self.setItem(row, col, self._make_item(text))
        elif item.text() != text:
            item.setText(text)

    def _apply(self, rows):
        """**重建**表格（行数 / 行序 / 路径集合变了时才走这里）.

        ⚠️ 重建前必须**先把单元格清空**（``_clear_cells``）：状态列有时是
        ``QTableWidgetItem``、有时是 ``setCellWidget`` 放的控件（异常状态带警告图标）。
        ``setRowCount`` **不会**移除已放置的 cell widget —— 只是把多余的行删掉、
        把留下的行原样保留。于是「已禁用（不执行）」那个 label 会赖在格子里，盖住
        之后写进去的新 ``item``：勾选「默认加载」后，状态列仍然显示旧的「已禁用」。

        这正是 2026-10-18 用户报告的现象。教训：**一个格子要么放 item、要么放
        widget，切换时必须显式移走另一个**，不能指望表格帮忙。

        ⚠️ :meth:`_show_scanning` 已改为「只擦格子、不动行」，不再摆跨列占位行；
        ``clearSpans()`` 保留 —— 它同时清掉别处可能留下的 span，代价为零。
        """
        self._loading = True
        try:
            self._clear_cells()
            self.clearSpans()
            self.setRowCount(len(rows))
            for row, data in enumerate(rows):
                self._make_row(row, data)
        finally:
            self._loading = False
        self._fit_columns()  # 行变了，其余列（按内容自适应）的宽度也会变

        # ★ 「扫描完成后选中某一行」只能在这里兑现：``update_items()`` 是异步的，
        #   调用它的那一刻表格还是「正在扫描…」占位行（见 select_after_refresh）。
        #   ⚠️ 无论找没找到都要清掉 pending —— 否则它会一直挂到下一次刷新，
        #   在用户完全没预期的时刻突然选中一行。
        path, self._pending_select = self._pending_select, None
        if path is not None:
            self._select_path(path)

    def _clear_cells(self):
        """把现有每一格的 item 与 cell widget 都移除（重建前的必要一步）."""
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                widget = self.cellWidget(row, col)
                if widget is not None:
                    self.removeCellWidget(row, col)
                    widget.deleteLater()  # 交给 Qt 回收（它是本控件的子对象）
                if self.item(row, col) is not None:
                    self.setItem(row, col, None)

    def _make_row(self, row, data):
        """按 :func:`collect_rows` 算好的**一行数据**铺成一行（只建控件）.

        Args:
            row: 行号。
            data: ``{'path' / 'disabled' / 'priority' / 'name' / 'desc' /
                'standard' / 'state' / 'normal'}``（见 :func:`collect_rows`）。
        """
        path = data['path']

        enabled = QtWidgets.QCheckBox()
        enabled.setChecked(not data['disabled'])
        enabled.setToolTip('取消勾选 = 启动时不自动加载这段代码（重启后生效）。\n'
                           '不影响「临时加载」，也不影响被其它插件作为依赖拉起。')
        enabled.toggled.connect(
            lambda checked, p=path: self._on_enabled_changed(p, checked))
        self.setCellWidget(row, _COL_ENABLED, self._center(enabled))

        combo = QtWidgets.QComboBox()
        # ★ 每项带一个色块（高=红、低=绿，正常不画）—— 只影响**显示**，
        #   取值仍走 itemData，`_on_priority_changed` 拿到的还是英文值。
        dark = self._is_dark(self)
        for value in _PRIORITY_ORDER:
            icon = self._priority_icon(value, dark)
            if icon is None:
                combo.addItem(_PRIORITY_TEXT[value], value)
            else:
                combo.addItem(icon, _PRIORITY_TEXT[value], value)
        combo.setCurrentIndex(_PRIORITY_ORDER.index(data['priority']))
        combo.setToolTip('高优先级整段提前执行、低优先级整段延后 —— 不改列表顺序')
        combo.currentIndexChanged.connect(
            lambda index, p=path, c=combo: self._on_priority_changed(
                p, c.itemData(index)))
        self.setCellWidget(row, _COL_PRIORITY, combo)

        # 名称 / 描述：来自插件文件里的「# ** name = '...'」与「# ** desc = '...'」
        # （见 plugins.get_meta）。没写 name 就用文件名，没写 desc 显示占位文字。
        # ★ 路径存在名称单元格的 UserRole 里，并把**完整路径放在 tooltip 第一行** ——
        #   2026-10-19 去掉「文件」列之后，这里是查看路径的唯一入口（见 _row_path）。
        name = self._make_item(data['name'])
        name.setData(_PATH_ROLE, path)
        name.setToolTip(
            f'{path}\n\n'
            f'名称来自插件文件里的「# ** name = ...」（没写就用文件名）\n'
            f'双击可在代码编辑器中打开')
        self.setItem(row, _COL_NAME, name)

        desc_text = data['desc'] if data['desc'] else '（无描述）'
        desc = self._make_item(desc_text)
        desc.setToolTip(desc_text)  # 列窄被省略时，tooltip 里看全文
        self.setItem(row, _COL_DESC, desc)

        # 来源：自动发现的不能移除（移了下次扫描也会回来），只能禁用
        standard = data['standard']
        source = self._make_item('自动' if standard else '手动')
        source.setToolTip(
            '由目录扫描发现：不能移除，不想执行请取消「默认加载」'
            if standard else '用「添加」手动登记的：可以移除')
        self.setItem(row, _COL_SOURCE, source)

        if data['normal']:
            self.setItem(row, _COL_STATE, self._make_item(data['state']))
        else:
            self.setCellWidget(row, _COL_STATE,
                               self._state_widget(data['state']))

        # 临时加载：按钮自带状态（可加载 / 已加载 / 文件不存在）。
        # ⚠️ 它与「默认加载」勾选**无关** —— 勾选决定的是**下次启动**跑不跑，这里只管
        #    「现在跑一次」，且不写任何设置（见 plugins.load_now）。
        self.setCellWidget(row, _COL_LOAD,
                           self._center(self._make_load_button(path)))

    @staticmethod
    def _state_widget(text):
        """异常状态：图标 + 文字（图标来自系统主题，自动适配亮色与暗色）.

        ⚠️ **不写死颜色**：用户可换主题 / 开暗色模式，写死的色值在暗色下会看不清，
        也会盖掉 QSS。颜色交给系统图标自己去适配。
        """
        label = QtWidgets.QLabel()
        icon = QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning)
        label.setPixmap(icon.pixmap(12, 12))
        label.setText(' ' + text)
        label.setToolTip(text)
        return label

    @staticmethod
    def _is_dark(widget):
        """当前是否暗色主题（决定优先级色块取深色还是浅色那一套）.

        ⚠️ **不调 ``gui.in_dark_mode()``**：那要经过 GuiApi 的通道往返，而本方法在
        建表的循环里被逐行调用。直接读控件自己的调色板就够了（与
        ``output_widget._dark()`` 同一做法）。
        """
        base = widget.palette().color(QtGui.QPalette.ColorRole.Base)
        return base.lightness() < 128

    @staticmethod
    def _priority_icon(value, dark=False):
        """优先级色块（``QIcon``）；``normal`` 返回 ``None``（不画）.

        ⚠️ **用 ``QIcon`` 画，不给文字 ``setStyleSheet('color: ...')``**：写死的
        文字颜色会盖掉用户可编辑的 ``zml_window_style.qss``，而且在暗色主题下可能
        看不清；图标不受样式表与主题影响（见 ``widgets/AGENTS.md`` 的「控件里的
        颜色」一节，``plugins/builtin/style_sheet_menu.py`` 的 ``_ColorButton`` 是同一做法）。

        Args:
            value: 优先级（``'high'`` / ``'normal'`` / ``'low'``）。
            dark: 是否暗色主题（决定取深色还是浅色那一套）。

        Returns:
            QtGui.QIcon | None: 色块图标；``normal``（或未知值）返回 ``None``。
        """
        colors = _PRIORITY_COLOR.get(value)
        if colors is None:
            return None
        pixmap = QtGui.QPixmap(_PRIORITY_DOT, _PRIORITY_DOT)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pixmap)
        try:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            painter.setBrush(QtGui.QColor(colors[1] if dark else colors[0]))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, _PRIORITY_DOT - 1, _PRIORITY_DOT - 1)
        finally:
            painter.end()
        return QtGui.QIcon(pixmap)

    @staticmethod
    def _center(widget):
        """把控件放进一个居中的容器（表格单元格不会自动居中）."""
        holder = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(holder)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(widget)
        return holder

    def _make_load_button(self, path):
        """造一个「临时加载」按钮（状态由 :meth:`_sync_load_button` 决定）."""
        button = QtWidgets.QPushButton()
        button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(
            lambda _=False, p=path, b=button: self._on_load_clicked(p, b))
        self._sync_load_button(button, path)
        return button

    @staticmethod
    def _sync_load_button(button, path):
        """按「文件在不在 / 本次运行加载过没有」刷新按钮的文字、可用性与提示.

        ⚠️ 三种状态都要**显式**处理，不能只让「加载」一种：文件已被删除的记录还在
        名单里（历史遗留），此时按钮必须置灰而不是点了报错；已经加载过的也必须
        置灰 —— 再执行一次会把菜单项挂第二遍。
        """
        if not os.path.isfile(path):
            button.setText('—')
            button.setEnabled(False)
            button.setToolTip(f'{path}\n文件不存在，无法加载')
            return
        if plugins.is_loaded(path):
            button.setText('已加载')
            button.setEnabled(False)
            button.setToolTip('本次运行已经加载过（重复执行会重复挂菜单），重启后按「默认加载」勾选决定')
            return
        error = plugins.get_load_error(path)
        button.setText('加载')
        button.setEnabled(True)
        button.setToolTip(
            '立即执行这个插件（临时加载）：当场出现它加的菜单；'
            '**不改**「默认加载」设置，重启后要不要执行仍只看左边的勾选\n'
            '每个插件在本次运行里只会加载一次'
            + (f'\n\n上次加载失败：{error}' if error else ''))
        if plugins.is_disabled(path):
            # ⚠️ 禁用**不**挡住临时加载（2026-10-22 定稿）：启用的插件启动时早就跑过、
            #    按钮是「已加载」点不动 —— 所以能点的恰好是禁用的这一批。两者若绑在
            #    一起，这个按钮对谁都无效。这里只把两个概念的差别说清楚。
            button.setToolTip(
                '临时加载：**现在**就跑一次，当场出现它加的菜单\n'
                '⚠️ 本插件当前是「禁用」（下次启动不会自动加载），但这不影响临时加载：\n'
                '临时加载不写任何设置，重启后仍按左边的「默认加载」勾选决定\n'
                '每个插件在本次运行里只会加载一次'
                + (f'\n\n上次加载失败：{error}' if error else ''))

    def _on_load_clicked(self, path, button):
        """点「加载」：交给**界面体系自己的控制台线程**执行（``gui.start``）.

        ⚠️ 为什么用 ``gui.start`` 而不是自己起 ``QThread``：插件体里那句
        ``gui.add_action(...)`` 本来就设计成「任意线程发起、由 gui 缓冲区派发到 GUI
        线程」；而控制台线程（``ConsoleThread``）是界面**自己**的执行通道 —— 启动时的
        ``plugins.load_all()`` 就跑在同一个线程里（``main.py`` 的 ``__console_kernel``）。
        用它有三个好处：不用自己管线程生命周期；与按钮共用同一套「忙闲」判断（控制台
        同一时刻只跑一个任务）；执行过程会照常出现在输出面板里。

        ⚠️ 界面更新（按钮状态、状态栏）放在 ``post_task`` 里：``Console.__kernel_exited``
        是 GUI 线程上的槽，它在那里调用 ``post_task``，所以可以安全地碰控件。

        ⚠️ ``button`` 可能在执行期间被 ``update_items()`` 重建掉（用户同时改了勾选），
        因此回写前用 :func:`_is_deleted` 判一下，别在已销毁的控件上操作。
        """
        if self._loading_plugin:
            return
        if not gui.exists():
            # 无界面（headless）：没有控制台线程，当场执行
            plugins.load_now(path)
            self._sync_load_button(button, path)
            return
        if gui.is_running():
            gui.status('控制台正在执行其它任务，等它结束再加载')
            return

        self._loading_plugin = True
        button.setEnabled(False)
        button.setText('加载中…')

        def task(p=path):
            plugins.load_now(p)

        def done(p=path, b=button):
            self._loading_plugin = False
            if not _is_deleted(b):
                self._sync_load_button(b, p)
            name = os.path.basename(p)
            if plugins.is_loaded(p):
                note = '（临时加载，不改变「默认加载」设置；重启后仍按勾选决定）'
                if plugins.is_disabled(p):
                    note = '（临时加载；本插件仍是「禁用」，重启后不会自动加载）'
                gui.status(f'已临时加载：{name}{note}')
            elif plugins.get_load_error(p) is not None:
                gui.status(f'加载失败：{name}（原因见消息区）')

        gui.start(task, post_task=done, add_history=False)

    @staticmethod
    def _make_item(text):
        """只读单元格（⚠️ 必须去掉 ``ItemIsEditable``，否则双击会弹编辑器）."""
        item = QtWidgets.QTableWidgetItem(text)
        item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        return item

    def _row_path(self, row):
        """取某一行对应的插件路径（存在名称单元格的 ``UserRole`` 里）.

        ⚠️ **不能读 ``item.text()``**：名称列的正文是插件自己起的名字，不是路径；
        「文件」列已移除（2026-10-19），路径只存在于 ``UserRole`` 与 tooltip 里。
        双击、选中、移除、右键菜单**一律**走这里，别在别处重新猜路径。

        Args:
            row: 行号。

        Returns:
            str | None: 插件文件路径；该行没有名称单元格（例如「正在扫描…」占位行）
            时返回 None。
        """
        item = self.item(row, _COL_NAME)
        if item is None:
            return None
        value = item.data(_PATH_ROLE)
        return str(value) if value else None

    # ---------------------------------------------------------------- 写
    def _on_enabled_changed(self, path, checked):
        """勾选 / 取消勾选「默认加载」—— 只改这一条的标记与状态格，**不重建整张表**.

        ⚠️⚠️ **这里刻意不调 ``update_items()``**（2026-10-19 改）：

        1. **没有任何列需要重算**。六列里只有「状态」列会随勾选状态变
           （「已启用」↔「已禁用（不执行）」），其余五列（默认加载 / 优先级 / 名称 /
           描述 / 来源）与勾选无关 —— 原地改那一格即可；
        2. **整表刷新会让行序跳变**。``update_items()`` 走 :func:`collect_rows`，它按
           ``plugins.get_files()`` 的顺序排；而 ``set_disabled`` 对**尚未登记**的
           内置插件会调 ``_ensure_in_list`` **把它补登进名单** —— 于是这个插件从
           「名单外的内置插件」区（``get_files`` 的末尾）挪进名单的正常位置，
           **整张表重排**。现象是：用户点了一个勾选框，转眼间鼠标底下已经是别的
           插件了；
        3. 重建还要经历「正在扫描…」占位行 → 重铺，视觉上等于整个界面闪一下。

        真需要整表刷新（例如新装了插件）时，用户可点「刷新」或右键「恢复默认」。
        """
        if self._loading:
            return
        plugins.set_disabled(path, not checked)
        row = self._row_of(path)
        if row < 0:
            return
        log = _StateLog.get()
        self._set_state_cell(
            row, _StateLog.text(path, log), _StateLog.is_normal(path, log))

    def _row_of(self, path):
        """按路径找行号（找不到返回 -1）.

        ⚠️ 只认**名称单元格 ``UserRole`` 里的路径**（见 :meth:`_row_path`），
        不按文本猜。
        """
        for row in range(self.rowCount()):
            if self._row_path(row) == path:
                return row
        return -1

    def _set_state_cell(self, row, text, normal):
        """把第 ``row`` 行的「状态」格换成 ``text``.

        ⚠️ 一个格子要么放 item、要么放 cell widget，**切换时必须显式移走另一个**
        （见 :meth:`_apply` 的说明）：异常状态用 ``setCellWidget`` 放的带图标
        ``QLabel``，正常状态是普通 ``QTableWidgetItem``。⚠️ 两者可以**同时**存在于
        同一格 —— ``setCellWidget`` **不会**删掉已有的 item（2026-10-19 实测：切换后
        ``item(row, col)`` 与 ``cellWidget(row, col)`` 同时非空，旧文字留在底下），
        所以这里必须**两个都清**再写新的。

        Args:
            row: 行号。
            text: 状态文字（来自 :meth:`_StateLog.text`）。
            normal: 是否「一切正常」（False 时用带警告图标的 label）。
        """
        if row < 0 or row >= self.rowCount():
            return
        widget = self.cellWidget(row, _COL_STATE)
        if widget is not None:
            self.removeCellWidget(row, _COL_STATE)
            widget.deleteLater()
        if self.item(row, _COL_STATE) is not None:
            self.takeItem(row, _COL_STATE)
        if normal:
            self.setItem(row, _COL_STATE, self._make_item(text))
        else:
            self.setCellWidget(row, _COL_STATE, self._state_widget(text))

    def _on_priority_changed(self, path, value):
        """改优先级 —— 不移动这一行（只把状态重算一遍，不重扫）. """
        if self._loading or value not in _PRIORITY_ORDER:
            return
        plugins.set_priority(path, value)
        self.update_items()   # 已有内容时只重算状态，见其说明

    def _on_double_clicked(self, index):
        """双击任意一行：用代码编辑器打开该插件（路径取自 :meth:`_row_path`）."""
        path = self._row_path(index.row())
        if path is not None:
            self.open_file(path)

    def open_file(self, file_path):
        """在代码编辑器里打开插件脚本."""
        if os.path.isfile(file_path):
            try:
                gui.open_code(file_path)
            except Exception as err:
                print(f'打开文件失败: {err}')
        else:
            print(f'文件不存在: {file_path}')

    # ---------------------------------------------------------------- 命令
    def add_file(self):
        """手动登记一个新的插件脚本（追加到名单末尾），并选中它."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, '选择插件脚本', '', 'Python文件 (*.py);;所有文件 (*)')
        if not file_path or not os.path.isfile(file_path):
            return
        if not plugins.add_file(file_path):
            gui.status('这个插件已经在列表里了')
            return
        # ⚠️ **先登记、再重扫**：``_rescan_and_apply`` 是异步的，返回时表格里还没有
        #    这一行。若紧跟 ``_select_path(file_path)``，选中会静默失效（2026-10-19
        #    实测选中 0 行）。⚠️ 插件集合变了，必须**强制重扫** —— ``update_items()`` 在
        #    已有内容时只重算状态，发现不了新行。
        self.select_after_refresh(file_path)
        self._rescan_and_apply()

    def select_after_refresh(self, path):
        """登记「**扫描完成之后**选中这个路径所在的行」.

        为什么需要它：``update_items()`` 立刻返回，表格此刻还是占位行 —— 所有「刷新完
        顺便选一下」的写法都必须走这里，在 :meth:`_apply` 铺完行之后才兑现。

        Args:
            path: 要选中的插件文件路径（找不到对应行时什么也不做）。
        """
        self._pending_select = path

    def _select_path(self, path):
        """选中某个路径所在的行（添加后让用户看见它加到了哪）.

        ⚠️ 只能对**已经铺好行**的表格调用。紧跟在 ``update_items()`` 后面调用是无效的，
        那种场景请用 :meth:`select_after_refresh`。
        """
        key = _norm_key(path)
        for row in range(self.rowCount()):
            found = self._row_path(row)
            if found is not None and _norm_key(found) == key:
                self.selectRow(row)
                self.scrollToItem(self.item(row, _COL_NAME))
                return

    def remove_selected(self):
        """移除选中的插件（**只对手动登记的生效**，且不删磁盘文件）.

        ⚠️ 自动发现的插件**不会被移除**（移了下次扫描也会回来），这里把它们
        挑出来明确告诉用户改用什么办法，而不是「点了没反应」。
        """
        rows = sorted({index.row() for index in self.selectedIndexes()})
        if len(rows) == 0:
            return
        removed = 0
        refused = []
        for row in rows:
            path = self._row_path(row)
            if path is None:
                continue
            if plugins.is_standard(path):
                refused.append(os.path.basename(path))
            elif plugins.remove_file(path):
                removed += 1
        # ⚠️ 插件集合变了（少了几行）⇒ 强制重扫，不能只重算状态
        self._rescan_and_apply()
        if len(refused) > 0:
            gui.information(
                '不能移除自动发现的插件',
                '下面这些插件是目录扫描发现的，移除了下次启动也会自己回来：\n\n'
                + '\n'.join('  · ' + name for name in refused)
                + '\n\n不想让它们执行，请**取消勾选「默认加载」**。')
        elif removed > 0:
            gui.status(f'已移除 {removed} 个插件（磁盘文件未删除）')

    def reset_files(self):
        """恢复默认：清掉用户的**所有手动选择**，回到各插件自己的默认.

        具体清掉两样：

        - **启用状态**：清成「用户没表过态」，于是每个插件回到它自己声明的
          `# ** enabled = ...`（彩蛋是「默认不加载」，别的插件是「默认加载」）。
          ⚠️ 这里**不能**写成「全部设为启用」—— 那会把彩蛋也强行打开；
        - **优先级**：全部回到 `normal`。

        ⚠️ 先**问一声**再动手：它会把用户手动调过的设置一起清掉。
        """
        if not gui.question(
                '这会清除所有插件的手动设置：\n'
                '· 启用状态回到各插件自己的默认\n'
                '· 优先级全部恢复为「正常」\n\n'
                '确定继续吗？'):
            return
        plugins.clear_choice()  # 清掉「用户的选择」，回到插件自报的默认值
        for path in plugins.get_files():
            plugins.set_priority(path, 'normal')
        plugins.rescan()
        # ⚠️ 这里刻意**强制重扫**：它的语义就是「连名单一起重来」，也是用户能主动
        #    触发 `plugins.rescan()`（重新扫目录、发现新插件）的唯一入口。
        self._rescan_and_apply()

    def cleanup_before_tab_close(self):
        """关闭本标签页时调用（``TabWidget.close_tab``）：**不等**在跑的扫描.

        ⚠️ **刻意不 ``wait()``**：扫描要读一堆插件文件（见 :class:`_ScanWorker`），
        在这里同步等会把「关标签」变成冻结界面。线程本来就没有 parent（见
        :data:`_RUNNING_SCANNERS`），因此**不会**随控件一起被销毁 —— 关标签只是
        让结果失去接收者，线程照旧跑完，然后被 :func:`_forget_scanner` 摘掉。
        迟到的结果由 :func:`_is_deleted` 拦掉。

        ⚠️ 顺带把 :attr:`_scan_seq` 推进一格：万一某个线程恰好在 ``deleteLater()``
        之后、``_is_deleted`` 生效之前回来，序号已经对不上，结果同样被丢弃。
        """
        self._scan_seq += 1
        self._scanners = []

    def contextMenuEvent(self, event):  # 右键菜单
        menu = QtWidgets.QMenu(self)
        menu.addAction(create_action(self, '添加', slot=self.add_file))

        action = create_action(self, '移除', slot=self.remove_selected)
        # 只对手动登记的可用（自动发现的移除无效，直接置灰更诚实）
        rows = {index.row() for index in self.selectedIndexes()}
        removable = []
        for row in rows:
            path = self._row_path(row)
            removable.append(path is not None and not plugins.is_standard(path))
        stay = create_action(self, '恢复默认', slot=self.reset_files)
        if len(rows) > 0 and not any(removable):
            action.setEnabled(False)
            action.setToolTip('自动发现的插件不能移除；不想执行请取消勾选「默认加载」')
        menu.addAction(action)
        menu.addSeparator()
        menu.addAction(stay)
        if menu.actions():
            menu.exec(event.globalPos())


# ============================================================
# 入口：菜单「设置 → 插件」与命令 gui.edit_setup_files
# ============================================================

def edit_setup_files():
    """打开（或切到）「插件」标签页；同时也是 GUI 命令 ``gui.edit_setup_files()``.

    ⚠️ 由 ``MainWindow.edit_setup_files`` **原样搬来**（2026-10-31）：那段代码靠「主窗口的
    公开方法被自动注册成 ``gui.xxx``」提供命令；方法搬走后那条链断了，所以本文件的
    :func:`setup_ui` 用 ``gui.add_func('edit_setup_files', edit_setup_files)`` **显式补上**。

    ⚠️ **名字不能改**（见模块文档的「命名遗留」表）：``gui.edit_setup_files()`` 是
    ``zmlx://gui/edit_setup_files`` 文档链接与标签页存档串里写的原文。
    """
    def oper(w):
        w.gui_restore = """gui.edit_setup_files()"""
        # 每次打开都拉一次最新数据（插件可能刚被执行过）。
        # ⚠️ 方法叫 ``update_items`` 而不是 ``refresh`` —— 后者会被
        #    ``MainWindow.refresh()`` 在**每次切到这个标签页**时调用，
        #    白白重算一遍（见该方法的说明）。
        w.update_items()

    gui.get_widget(
        PluginListEdit,
        caption="插件",
        on_top=True,
        icon="plugin",
        oper=oper,
    )


@execute_once(file=__file__)
def setup_ui():
    """注册命令 ``gui.edit_setup_files`` + 菜单项「设置 → 插件」.

    ⚠️ **``menu="设置"`` 必须与 ``main.py`` 里那一处逐字相同**，否则 ``get_menu`` 会另建
    一个同名顶层菜单，界面上出现两个「设置」。

    ⚠️ **``name='setup_files'`` 保持原样**：它是 ribbon 配置与已保存界面布局的定位依据。
    显示文字是「插件」、图标是 ``plugin`` —— 这两个改了不影响定位，但也别乱动。
    """
    gui.add_func('edit_setup_files', edit_setup_files)

    gui.add_action(
        menu="设置",
        name="setup_files",
        icon="plugin",
        text="插件",
        slot=edit_setup_files,
        overwrite=False,
    )


def test_1():
    """直接运行本文件：用一个临时目录里的假插件演示七个列."""
    import sys
    import tempfile

    app = QtWidgets.QApplication(sys.argv)
    root = tempfile.mkdtemp()
    made = []
    for name in ('demo_high.py', 'demo_normal.py', 'demo_off.py'):
        path = os.path.join(root, name)
        with open(path, 'w', encoding='utf-8') as file:
            file.write('# demo\n')
        made.append(path)

    for path in made:
        plugins.add_file(path)
    plugins.set_priority(made[0], 'high')
    plugins.set_disabled(made[2], True)

    w = PluginListEdit()
    w.resize(960, 420)
    w.setWindowTitle('插件列表（临时目录里的假插件）')
    w.show()
    w.update_items()   # 构造时不再自动加载（见 __init__ 末尾），这里显式拉一次数据
    sys.exit(app.exec())


if __name__ == '__main__':
    test_1()
