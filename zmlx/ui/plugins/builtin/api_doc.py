# ** name = 'GUI 接口文档'
# ** desc = '「帮助 → GUI 接口」：把 gui 命令表列成一个可搜索、可按用途筛选、带签名与用例的说明页（注册 gui.show_api_doc）'
# ** enabled = True
"""「帮助 → GUI 接口」：``gui`` 命令的**图形化说明书**.

问题：界面上到底有哪些 ``gui.xxx()`` 能调？以前只能 ``print(gui.list_all())`` 拿一串光秃秃
的名字（见 ``plugins/builtin/architecture.py`` 的「不知道有哪些命令？」），名字背后是
什么、要传什么参数、返回什么、能不能从后台线程调 —— 全靠翻源码。本插件把这份说明做成
一个正经的界面页，思路对齐常见 API 文档工具（Dash / DevDocs 的三栏：导航 · 列表 · 正文；
Qt Assistant 的目录 · 索引 · 看看；以及「双击一行 → 复制」这种手到擒来的用法）。

=======================  =========================================================
入口                     调用
=======================  =========================================================
GUI 命令                 ``gui.show_api_doc(name=None)``（给名字时直接定位到那一条）
菜单项                   「帮助 → GUI 接口」
=======================  =========================================================

界面（上 → 下、左 → 右）
------------------------

::

    ┌ 搜索框 ─────────────┬ 只看 ▾ ┬ 来源 ▾ ┬ ☐ 只显示示例 ┬  共 N 条  刷新 ┐
    ├─────────────┬─ 列表（名字 · 签名摘要 · 来源）────────┬─ 详情 ─────────┤
    │ 显示窗口     │  close        关闭当前窗口            │ gui.close()     │
    │ 标签页       │  get_widget   获取/创建标签页 ...     │ ▸ 签名          │
    │ 对话框       │  ...                                 │ ▸ 参数          │
    │ 绘图         │                                      │ ▸ 返回值        │
    │ ...          │                                      │ ▸ 说明          │
    └─────────────┴──────────────────────────────────────┴────────────────┘

- **左侧目录**按用途分组（显示窗口 / 标签页 / 对话框 / 绘图 / 运行控制 / 插件 / 基础 …），
  点一下就只看那一组；
- **搜索框**同时匹配名字、签名、说明、参数名（空格分词，全部命中，大小写不敏感）；
- **列表**三列：名字、签名摘要（灰字）、来源标记（下面的表）；
- **详情**按节展开（签名 / 参数 / 返回值 / 说明 / 用例），链接可点，**双击一行就复制**
  ``gui.名字(`` 到剪贴板 —— 直接粘到控制台里；参数表里也有「复制」。

信息从哪来：预分类目录 + **每次打开时实时扫描**
------------------------------------------------

⚠️ **说明文字全部运行时现读**，本文件不维护任何命令清单：

- 名字：``gui.list_all()``（``GuiApi.list_all``，排好序）；
- 函数体：``gui.get_func(name)`` —— 这就是需求里说的「``f = gui.get_func(name)``」；
- 签名 / 参数 / 返回 / 说明：``inspect`` 读函数的**真实签名与 docstring**（优先
  :func:`inspect.getdoc`，它会沿继承链找到真正的说明）；
- 用例：docstring 里的 ``Example:`` / ``Usage:`` 段，没有就不显示「用例」这一节。

⚠️ **``gui.xxx(...)`` 是唯一出口**，本文件不写 ``gui.get().xxx()``：上面两条命令都经
``GuiBuffer.__getattr__`` → ``Agent`` → ``command(...)`` 派发到 GUI 线程里的 ``GuiApi``；
绕过这层去拿 ``GuiApi`` 对象再调方法，跨线程时没有任何线程保证，也让「出口」变成两个。

**什么时候重扫**：只有在**用户明确操作**时才重扫，不会自己刷新 ——

- 标签页**建出来时**一次（``gui.get_widget`` 的 ``oper``）；
- 点顶部「**刷新**」按钮。

⚠️ **刻意不接 ``refresh()``**（框架的刷新钩子）：``MainWindow.refresh`` 会在「显示 →
刷新」以及 ``create_action`` 包装过的**每个菜单动作**之后被调用，而本页的内容是「接口
说明」，它在启动之后就基本定型了，没必要跟着每次点菜单重扫一遍。命令表真变了（插件
「临时加载」不重启就 ``add_func``），点一下「刷新」即可。

**预分类目录**（``_PREBUILT_CATALOG_TEXT``，**本文件里自带的一份快照**）只做一件事：
告诉页面「这个名字属于哪一组」。规则是「运行时的名字规则优先 → 目录兜底 → 都没有就进
『基础与其它』」，所以库怎么变都不会丢命令：

- 新增一条命令 → 名字规则认得出就先按规则，认不出再查目录，都没有就进兜底；
- 改了某条命令的分组 → 以**运行时的规则**为准（目录过时也不会错位）；
- 改了签名 / docstring → 直接反映，因为说明根本不经过目录。

要更新这份快照，在本页顶部点「刷新」之后**不需要**动它（它只是给未知名字兜底的）；
真想让新名字也落进合适的分组，把名字补进相应的 ``GROUPS`` 规则即可 —— 那才是唯一的
分类来源，目录只是它的备份。⚠️ 目录**留空**也完全可用，只是未知名字会落进「基础与其它」。

来源标记（列表第四列那种）
--------------------------

========================  ==================================================
标记                       含义
========================  ==================================================
**主窗口**                  ``MainWindow`` 的公开方法（``__init_gui_api`` 自动注册）
**gui_api**                ``GuiApi`` 自带的几条（``list_all`` / ``get_func`` …）
**内建**                   ``zmlx.ui`` 里注册的（``edit_in_tab`` 之类）
**插件 · XXX**             某个插件用 ``gui.add_func`` 加的（XXX 是插件名）
**脚本**                   由 Python 脚本（``__main__``）注册的
**别名**                   与另一条命令是**同一个函数**（例如 ``status`` ↔ ``show_status``）
========================  ==================================================

⚠️ 别名是**运行时按函数身份算出来的**（``id(func)``），不是写死的表：``MainWindow`` 在
``__init_gui_api`` 里正是把 ``close`` / ``status`` / ``title`` 指向别的方法，插件也可能这么干。

安全边界（写这个页面时最容易越界的地方）
----------------------------------------

1. **加载期只接线**（``plugins/AGENTS.md`` §0.5）：插件加载时只做 ``add_action`` /
   ``add_func``，命令表一个都不扫 —— 重活全在打开标签页的第 :meth:`ApiDocView.reload` 里做。
2. **运行期只读**：本页唯一会「动」的动作是**写剪贴板**；除此之外只有用户主动点的
   ``gui.open_code``（在代码编辑器里打开实现文件）。**绝不** ```exec``、**绝不**执行任何
   ``gui`` 命令 —— 示例里可能有 ``close``，执行与否是用户自己的选择，不是本页的选择。
3. **不碰别人的控件**：本页不访问 ``MainWindow``、不找控制台的输入行，只操作自己的子控件
   与系统剪贴板。

除 ``gui.xxx`` 之外，本文件还调用了什么（清单即约束）
------------------------------------------------------

⚠️ **操纵主窗口与命令表的出口只有 ``gui.xxx(...)`` 一个**（``list_all`` / ``get_func`` /
``get_widget`` / ``add_func`` / ``add_action`` / ``open_code`` …），**不写 ``gui.get().xxx()``**
—— 那会绕过 ``GuiBuffer`` 的派发层，跨线程时没有线程保证。

其余外部调用及其理由（**没有一条是在碰主窗口**）：

====================  ==============================================================
调用                   用途 / 为什么不能用 ``gui.xxx``
====================  ==============================================================
``execute_once``      ``zmlx.system``：插件注册的装饰器，``plugins/AGENTS.md`` 规定的入口形式
Qt 三个模块            建本页**自己的**控件（``QWidget`` / ``QSplitter`` / ``QTableWidget`` …）
``TextBrowser``       ``zmlx.ui.widgets``：项目统一的只读正文控件，自带「清除内容」右键与
                      悬停状态栏提示；换成裸 ``QTextBrowser`` 会丢掉这两样
``load_icon``         ``zmlx.ui.settings``：读图标资源。命令表里**没有**图标命令
                      （``gui.list_all()`` 实测无 ``icon`` 相关项）
``app_data``          ``zmlx.system``：记住「上次看的是哪一条」。纯数据、不碰界面，
                      命令表里没有等价物
``inspect``           读函数的真实签名 / docstring / 源文件行号（本页的数据来源）
``html`` / ``re`` / ``json`` / ``textwrap``  纯标准库：转义、分词、解析预分类目录、折行
====================  ==============================================================

⚠️ **``zmlx.ui.alg.create_action`` 刻意不用**：它执行完会 ``gui.refresh()`` 整窗刷新、还写一条
``log``，而本页的动作全是本地的（复制命令名、回首页、刷新列表）。统一走本文件的
:func:`_make_action`（``QAction`` + ``load_icon``，取不到图标就退化成纯文字）。

⚠️ **命令名一旦发布不能改**（标签页状态存的是 ``gui.show_api_doc()`` 这串原文，重启时按
原文重放）。所以 ``setup_ui`` 里用 ``gui.add_func`` 显式注册它，写法同 ``doc_view.py``。

⚠️ **菜单标题必须与 ``main.py`` 里逐字一致（``'帮助'``）**，否则 ``get_menu`` 会另建一个
同名顶层菜单，界面上出现两个「帮助」。

Created by DeepSeek, 2026-11-01: 新增「帮助 → GUI 接口」—— 图形化的 ``gui`` 命令说明页
"""

import html
import inspect
import re
import types

from zmlx.system import execute_once
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets

_TITLE = 'GUI 接口'
_RESTORE = 'gui.show_api_doc()'

#: **预分类目录**（本文件自带的一份快照；由 :attr:`_Docs.GROUPS` 的规则算出后写下）.
#:
#: ⚠️ 只存 ``{命令名: 分组键}`` —— **不存签名、不存说明**：那些必须运行时现读，因为库
#:    一直在变（新增命令、改签名、改 docstring）。这里只是一份「名字 → 用途」的快照。
#: ⚠️ 空表也完全可用：所有命令落到兜底分组「基础与其它」—— 分类差一点，但一条不丢。
_PREBUILT_CATALOG_TEXT = '''{
 "about": "dialog",
 "add_action": "plugin",
 "add_file_handler": "file",
 "add_func": "plugin",
 "add_task": "run",
 "call": "api",
 "channel_n": "api",
 "check_update": "window",
 "click_pause": "run",
 "close": "window",
 "closeEvent": "other",
 "close_all_tabs": "tab",
 "close_tab_object": "tab",
 "cls": "api",
 "console_state": "run",
 "count_tabs": "tab",
 "device_pixel_ratio": "window",
 "drop_files": "file",
 "edit_in_tab": "file",
 "exec_current": "run",
 "exec_file": "run",
 "exec_tab_func": "tab",
 "fileno": "other",
 "find_widget": "tab",
 "find_widgets": "tab",
 "flush": "other",
 "get_action": "plugin",
 "get_console": "run",
 "get_current_tab_index": "tab",
 "get_current_widget": "tab",
 "get_double": "dialog",
 "get_existing_directory": "dialog",
 "get_figure_widget": "plot",
 "get_func": "api",
 "get_gui_api": "api",
 "get_int": "dialog",
 "get_item": "dialog",
 "get_menu": "other",
 "get_multi_line_text": "dialog",
 "get_open_file_name": "dialog",
 "get_output_html": "run",
 "get_output_text": "run",
 "get_output_widget": "run",
 "get_plot_widget": "plot",
 "get_save_file_name": "dialog",
 "get_style_sheet": "window",
 "get_tab_caption": "tab",
 "get_tab_widget": "tab",
 "get_tab_widgets": "tab",
 "get_tabs": "tab",
 "get_text": "dialog",
 "get_toolbar": "other",
 "get_widget": "tab",
 "hide_console": "window",
 "in_dark_mode": "window",
 "information": "dialog",
 "init_splitter_sizes": "window",
 "is_maximized": "window",
 "is_paused": "window",
 "is_running": "window",
 "isatty": "other",
 "kill_thread": "run",
 "list_actions": "plugin",
 "list_all": "api",
 "list_member_functions": "api",
 "new_code": "file",
 "new_file": "file",
 "open_code": "file",
 "open_file": "file",
 "open_file_by_dlg": "dialog",
 "open_image": "file",
 "open_text": "file",
 "parse_value": "api",
 "play_sound": "window",
 "plot": "plot",
 "progress": "run",
 "question": "dialog",
 "refresh": "window",
 "refresh_action": "window",
 "reg_file_type": "file",
 "reset_layout": "window",
 "resize": "window",
 "resizeEvent": "other",
 "set_console_visible": "window",
 "set_cwd": "file",
 "set_cwd_by_dialog": "dialog",
 "set_paused": "window",
 "set_side_tabs_visible": "window",
 "set_style_sheet": "window",
 "set_tab_caption": "tab",
 "set_title": "window",
 "showEvent": "other",
 "show_attrs": "run",
 "show_console": "window",
 "show_maximized": "window",
 "show_next": "tab",
 "show_prev": "tab",
 "show_status": "window",
 "start": "run",
 "start_func": "run",
 "start_last": "run",
 "status": "window",
 "stop_console": "run",
 "tab_count": "tab",
 "title": "window",
 "toolbar_warning": "other",
 "trigger": "window",
 "update_system_state": "window",
 "warning": "dialog",
 "window": "plugin",
 "write": "other"
}'''


def _load_prebuilt_catalog():
    """把 :data:`_PREBUILT_CATALOG_TEXT` 解析成 ``dict``（出错就当空表，绝不抛）."""
    try:
        import json
        data = json.loads(_PREBUILT_CATALOG_TEXT or '{}')
    except Exception as err:
        print('Warning: 解析 gui 命令的预分类目录失败（将全部归入「基础与其它」）: %s' % err)
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value) for key, value in data.items() if isinstance(value, str)}


#: 解析后的缓存（模块加载时解析一次）
_PREBUILT_CATALOG = _load_prebuilt_catalog()


# ======================================================================
# 取数据：从运行时的命令表读出每一条命令的说明
# ======================================================================

class _Docs:
    """命令表 → 说明页需要的全部数据（纯逻辑，不碰 Qt，可在任意线程跑）.

    ⚠️ **不缓存跨次结果**：命令表随时会被插件 ``add_func`` 改写，而本表最贵的部分不过是
    ``inspect`` 遍历（实测百来条命令 < 20 ms），缓存反而会让页面说谎。一次 ``scan()``
    的结果由调用方持有（每次打开 / 刷新 / 自动刷新都会重建一次）。

    **两层信息，各管一段**：

    ======================  ======================================================
    层                       内容与来源
    ======================  ======================================================
    **预分类目录**            ``{名字: 分组键}``，打包期生成 —— 只决定「排在哪一组」
    **实时扫描**              名字 / 函数 / 签名 / docstring / 别名 / 来源，
                             每次都从 ``gui.list_all()`` + ``gui.get_func()`` 现读
    ======================  ======================================================

    合起来的规则：**分组**以运行时的名字规则为准，规则没覆盖的才查目录，都没有就落进
    「基础与其它」；**说明**永远只有一个来源 —— 运行时那个函数本身。
    """

    #: 用途分组：``(键, 标题, 说明, 关键词正则, 额外匹配的名字集合)``
    #:
    #: ⚠️ 顺序就是左侧目录的顺序，**先匹配先生效**：越靠前越具体。
    #: ``'基础'`` 由 ``build()`` 兜底追加，写法上放在最后但**不在这里** —— 它是「谁都不属于」
    #: 的落点，不是一条规则。
    GROUPS = [
        ('window', '显示窗口', '窗口本身：标题、样式、尺寸、关闭',
         r'^(title|set_title|get_style_sheet|set_style_sheet|resize|show_maximized|'
         r'is_maximized|device_pixel_ratio|close|quit|set_side_tabs_visible|'
         r'set_console_visible|init_splitter_sizes|reset_layout|hide_console|'
         r'show_console|show_status|status|trigger|refresh|update_view|'
         r'refresh_action|is_running|is_paused|set_paused|in_dark_mode|'
         r'update_system_state|play_sound|check_update)$', None),
        ('tab', '标签页', '``gui.get_widget`` 是打开任何页面的总入口',
         None,
         {'get_widget', 'get_tab_widget', 'get_tabs', 'get_tab_widgets',
          'get_tab_caption', 'set_tab_caption', 'count_tabs', 'tab_count',
          'show_next', 'show_prev', 'close_all_tabs', 'close_tab_object',
          'get_current_widget', 'get_current_tab_index', 'find_widget',
          'find_widgets', 'exec_tab_func', 'show_widget', 'set_position'}),
        ('dialog', '对话框与提示', '模态对话框；无头模式下会自动降级',
         r'^(question|information|about|warning|get_open_file_name|'
         r'get_save_file_name|get_existing_directory|get_int|get_double|'
         r'get_text|get_multi_line_text|get_item|open_file_by_dlg|'
         r'set_cwd_by_dialog)$', None),
        ('plot', '绘图', 'matplotlib 标签页；``plot`` 在 GUI 线程里一次做完',
         None,
         {'plot', 'get_plot_widget', 'get_figure_widget'}),
        ('run', '运行控制', '控制台线程：启动、暂停、终止、退出标志',
         None,
         {'start', 'start_func', 'start_last', 'is_running', 'is_paused',
          'set_paused', 'stop_console', 'click_pause', 'kill_thread',
          'exec_file', 'exec_current', 'get_console', 'break_point',
          'breakpoint', 'pause', 'progress', 'show_attrs', 'add_task',
          'get_output_widget', 'get_output_text', 'get_output_html',
          'console_state'}),
        ('file', '打开文件', '按扩展名自动选打开方式（``open_file``）',
         None,
         {'open', 'open_file', 'open_code', 'open_text', 'open_image',
          'open_url', 'new_code', 'new_file', 'new_empty_file', 'set_cwd',
          'add_file_handler', 'edit_in_tab', 'reg_file_type'}),
        ('plugin', '插件', '菜单项 / 插件开关 / 程序的加载与退出',
         None,
         {'add_action', 'add_func', 'edit_setup_files', 'get_action',
          'list_actions', 'show_window', 'window', 'proc_argv', 'execute',
          'open_gui', 'open_gui_without_setup'}),
        ('api', '自省与调用', '命令表本身：查有什么、取函数、转发调用',
         None,
         {'list_all', 'get_func', 'channel_n', 'call', 'command', 'gui_exec',
          'get_gui_api', 'list_member_functions', 'parse_value',
          'show_api_doc', 'cls'}),
    ]

    #: 不属于任何用途分组时的兜底分组名
    FALLBACK = ('other', '基础与其它', '其余命令（含文本页、内存、字符串表格等通用出口）')

    #: 类别判定**按类的名字**而不是直接 import 那些类：本文件不该为了判断「是不是主窗口方法」
    #: 去拉起 ``zmlx.ui.main``（它会连带拉起一大片界面模块，而且插件加载期就付这个代价）。
    #: ⚠️ 名字是 ``type(func).__name__``：内置函数是 ``'builtin_function_or_method'``，
    #: 插件里定义的闭包是 ``'function'``。
    SOURCE_LABELS = {
        'MainWindow': ('main', '主窗口'),
        'GuiApi': ('gui_api', 'gui_api'),
    }

    #: docstring 里哪些小标题算「用例」（大小写不敏感）
    EXAMPLE_HEADINGS = ('example', 'examples', 'usage', '用例', '示例')
    #: docstring 里哪些小标题算「注意事项」（单独成块、加粗显示）
    NOTE_HEADINGS = ('note', 'notes', 'warning', '注意', '提示', '⚠️')

    # ------------------------------------------------------------------
    @classmethod
    def group_of(cls, name):
        """只按名字判断用途分组（不读函数、不碰 Qt）—— 预分类与实时扫描**共用**这一份规则.

        Args:
            name: 命令名（不带 ``gui.``）。

        Returns:
            tuple: ``(key, title, hint)``。
        """
        for key, title, hint, pattern, names_set in cls.GROUPS:
            if (names_set is not None and name in names_set) or (
                    pattern is not None and re.fullmatch(pattern, name) is not None):
                return key, title, hint
        key, title, hint = cls.FALLBACK
        return key, title, hint

    @classmethod
    def _catalog(cls):
        """**预分类目录**：``{命令名: 分组键}``（本文件自带的一份快照，见模块文档）.

        ⚠️ 它**只**决定「一条命令属于哪一组」，好让分区展示时新命令排在自己所属的分组里，
        而不是全掉进兜底的「基础与其它」。签名 / 说明 / 别名 / 来源**一律运行时现读**。
        ⚠️ 目录里**没有**的名字照样正常显示（落进兜底分组）—— 库一直在变，这正是
        「预分类 + 实时扫描」两件事必须结合的的原因。

        Returns:
            dict: 名字 → 分组键。
        """
        return _PREBUILT_CATALOG

    # ------------------------------------------------------------------
    def build(self):
        """**实时读一遍命令表**：从 ``gui`` 现取命令名与函数，返回 ``{'items': ...}``.

        ⚠️ 每次调用都重新读：名字来自 ``gui.list_all()``、函数来自 ``gui.get_func(name)``、
        签名与说明用 ``inspect`` 现读 —— 所以插件后来注册的命令、改过的 docstring，只要
        再调一次 ``build()`` 就能反映出来（页面的「刷新」走的就是这里）。

        ⚠️ 只走 ``gui.xxx(...)`` 这一个出口：``gui.list_all()`` / ``gui.get_func()`` 都是
        ``GuiBuffer.__getattr__`` → ``command(...)`` → GUI 线程里的 ``GuiApi``，**不要**
        先 ``gui.get()`` 拿对象再调方法（那一步没有线程保证，也让出口变成两个）。

        ⚠️ 界面上的两处调用（打开页面、点刷新）都在 **GUI 线程**，于是每条命令是一次
        直连就地调用（100+ 条约 20 ms）；若改到后台线程调，同样这些命令会变成 100+ 次
        跨线程往返 —— 那才是真正的代价。

        Returns:
            dict: ``items`` 每项含 ``name`` / ``sig`` / ``doc`` / ``source`` / ``group``
            / ``alias`` 等字段（见 :meth:`_describe`）；``groups`` 是**实际出现过的**
            分组（按 :data:`GROUPS` 顺序）；``warnings`` 是取不到函数时留下的提示。
        """
        warnings = []
        source_names, name_warnings = self._read_names()
        warnings.extend(name_warnings)

        from zmlx.ui.gui_buffer import gui as _gui

        funcs = {}
        for name in source_names:
            try:
                funcs[name] = _gui.get_func(name)
            except Exception as err:
                funcs[name] = None
                warnings.append('取不到 <%s>：%s' % (name, err))

        # ---- 别名：同一个函数挂在多个名字上（运行时按身份算，不写死）----
        by_identity = {}
        for name, func in funcs.items():
            if func is None:
                continue
            key = id(getattr(func, '__func__', func))
            by_identity.setdefault(key, []).append(name)
        canonical = {}
        for names in by_identity.values():
            if len(names) > 1:
                names.sort()
                for name in names:
                    others = [item for item in names if item != name]
                    canonical[name] = others[0]
        aliases_of = {}
        for name, owner in canonical.items():
            aliases_of.setdefault(owner, []).append(name)

        # ---- 分组：先按集合 / 正则（= 实时规则），再按预分类目录，最后兜底 ----
        #
        # ⚠️ 三层的优先级是刻意的：**当前代码里的规则**说了算（它跟库一起演进），
        #    规则没覆盖的新名字才去看预分类目录（打包期写下的那一份），
        #    目录里也没有的才落进「基础与其它」。于是：
        #      · 打包之后新增的命令 —— 有规则就按规则，没规则照样显示（不会丢）；
        #      · 打包之后**改过**的分组 —— 以运行时的规则为准，不会因为目录过时而错位。
        all_names = sorted(funcs.keys())
        catalog = self._catalog()
        groups = []
        assigned = {}
        for key, title, hint, pattern, names_set in self.GROUPS:
            members = []
            regex = re.compile(pattern) if pattern is not None else None
            for name in all_names:
                if name in assigned:
                    continue
                if (names_set is not None and name in names_set) or (
                        regex is not None and regex.search(name)):
                    assigned[name] = key
                    members.append(name)
            # 规则没覆盖、但预分类目录说它属于这一组的，也归到这里
            if names_set is not None or pattern is not None:
                for name in all_names:
                    if name in assigned:
                        continue
                    if catalog.get(name) == key:
                        assigned[name] = key
                        members.append(name)
                members.sort()
            if members:
                groups.append((key, title, hint, members))
        rest = [name for name in all_names if name not in assigned]
        if rest:
            key, title, hint = self.FALLBACK
            groups.append((key, title, hint, rest))

        # ---- 逐条展开 ----
        items = []
        for key, title, hint, members in groups:
            for name in members:
                try:
                    items.append(self._describe(
                        name, funcs.get(name), key, title,
                        canonical.get(name), sorted(aliases_of.get(name, []))))
                except Exception as err:
                    warnings.append('解析 <%s> 失败：%s' % (name, err))
        return {'items': items, 'groups': groups, 'warnings': warnings}

    #: 首页默认停在的那一条（``gui.list_all`` —— 它正是「想知道有哪些命令」的起点）
    HOME_ITEM = 'list_all'

    @staticmethod
    def _read_names():
        """从 ``gui`` 取当前**全部命令名**（``gui.list_all()``，唯一的读法）.

        ⚠️ 这里刻意**不用 ``gui.get()``**：``GuiBuffer`` 对外的出口只有 ``gui.xxx(...)``
        —— ``__getattr__`` → ``Agent`` → ``command('list_all')`` → GUI 线程里执行
        ``GuiApi.list_all``。先取 ``GuiApi`` 对象再调方法是绕过派发层，跨线程时没有
        任何线程保证（而本函数按设计可能被非 GUI 线程调用）。

        ⚠️ 无界面时 ``GuiBuffer.command`` 恒返回 ``None``（不抛异常），所以「读不到」
        与「命令表是空的」要分开报，别把前者写成后者。

        Returns:
            tuple: ``(names, warnings)``。读不到时 ``names`` 为空、``warnings`` 里会有
            一句原因 —— 调用方据此显示「读不到命令表」。
        """
        from zmlx.ui.gui_buffer import gui as _gui

        warnings = []
        try:
            names = _gui.list_all()
        except Exception as err:
            warnings.append('list_all() 失败：%s' % err)
            return [], warnings
        if names is None:
            warnings.append('当前没有界面（无 GUI 模式）：命令表不存在')
            return [], warnings
        if len(names) == 0:
            warnings.append('命令表是空的：界面还没注册任何命令')
            return [], warnings
        return [str(name) for name in names], warnings

    @staticmethod
    def sort_key(item):
        """列表展示排序键：别名排在**它所指的那条**之后，其余按名字."""
        name = str(item.get('name', ''))
        if item.get('alias'):
            return (item.get('alias', ''), 1, name)
        return (name, 0, name)

    # ------------------------------------------------------------------
    @classmethod
    def _describe(cls, name, func, group_key, group_title, alias, aliases):
        """把一条命令展开成说明页需要的字段（任何异常都降级成半条记录，不抛）."""
        source = cls._source_of(name, func)
        item = {
            'name': name,
            'group': group_key,
            'group_title': group_title,
            'source': source,
            'alias': alias or '',
            'aliases': aliases,
            'sig': '',
            'call_sig': '',
            'one_line': '',
            'doc': '',
            'params': [],
            'returns': '',
            'raises': [],
            'example': '',
            'note': '',
            'module': '',
            'qualname': '',
            'file': '',
            'line': 0,
            'callable': callable(func),
        }
        if func is None:
            item['one_line'] = '（命令表里没有这个函数）'
            return item
        if not callable(func):
            item['one_line'] = '（这一条不是可调用对象）'
            return item

        # ---- 签名与参数 ----
        try:
            sig = cls._signature_of(func, item)
            item['sig'] = str(sig)
            item['call_sig'] = cls._call_signature(name, sig)
            item['params'] = cls._params_of(sig)
        except (TypeError, ValueError) as err:
            item['sig'] = '(%s)' % err

        # ---- docstring：说明 / 返回值 / 异常 / 用例 ----
        doc = ''
        try:
            doc = inspect.getdoc(func) or ''
        except Exception:
            doc = ''
        item['doc'] = doc
        item['one_line'] = cls._first_line(doc) or cls._fallback_summary(item)
        item['returns'], item['raises'] = cls._returns_of(doc, item['sig'])
        item['example'] = cls._section(doc, cls.EXAMPLE_HEADINGS)
        item['note'] = cls._section(doc, cls.NOTE_HEADINGS)

        # ---- 出处（供「到源码」用）----
        try:
            target = inspect.unwrap(getattr(func, '__func__', func))
            item['qualname'] = getattr(target, '__qualname__', '') or ''
            module = getattr(target, '__module__', '') or ''
            item['module'] = module
            try:
                item['file'] = inspect.getsourcefile(target) or ''
                item['line'] = int(inspect.getsourcelines(target)[1])
            except (OSError, TypeError):
                pass
        except Exception:
            pass
        return item

    # ------------------------------------------------------------------
    @classmethod
    def _signature_of(cls, func, item):
        """取函数签名；对**已绑定的方法**去掉 ``self``.

        Args:
            func: 候选函数。
            item: 正在填写的条目（本方法只会写入 ``qualname``，失败时也保留）。

        Returns:
            ``inspect.Signature``。

        Raises:
            TypeError: 根本拿不到签名（例如不支持的 Qt 内建）—— 由调用方降级。
        """
        try:
            sig = inspect.signature(func)
        except (TypeError, ValueError):
            # ⚠️ PyQt 把 QWidget 的成员（``resize`` / ``close``）暴露成
            #    ``builtin_function_or_method``，``inspect.signature`` 读不出参数表 ——
            #    此时退回**类上的普通 Python 方法**：``MainWindow.close`` 指向
            #    ``QWidget.close``，不是 Python 函数，会继续失败（那是合理的），
            #    但 ``MainWindow.get_widget`` 这类就有救了。
            base = type(getattr(func, '__self__', None))
            name = str(getattr(func, '__name__', '') or '')
            raw = getattr(base, name, None) if name else None
            if raw is not None and inspect.isfunction(raw):
                return inspect.signature(raw)
            raise
        owner = str(getattr(func, '__qualname__', '') or '')
        if owner and not item.get('qualname'):
            item['qualname'] = owner
        if isinstance(func, types.MethodType):
            # 绑定方法：签名里仍带着 self，去掉它 —— 否则页面上写的是
            # ``gui.get_widget(self, ...)``，用户照着抄就错。
            params = [p for key, p in sig.parameters.items() if key != 'self']
            sig = sig.replace(parameters=params)
        return sig

    @staticmethod
    def _qualname_of(func):
        """取「定义它的类.方法名」（优先 ``__qualname__``，退回 ``__name__``）."""
        for attr in ('__qualname__', '__name__'):
            value = getattr(func, attr, None)
            if isinstance(value, str) and len(value) > 0:
                return value
        return ''

    @classmethod
    def _source_of(cls, name, func):
        """判断这条命令来自哪里（见模块文档的「来源标记」表）.

        Returns:
            str: 人类可读的来源文字，例如 ``'主窗口'``、``'插件 · 图片浏览'``。
        """
        if func is None:
            return '未知'
        # ⚠️ 判据是 ``__qualname__`` 的**前缀**，不是 ``type(func).__name__``：
        #    PyQt 的 ``QWidget.close`` 绑到 ``MainWindow`` 实例后是
        #    ``builtin_function_or_method``，类名叫不出来，但 qualname 仍是
        #    ``'MainWindow.close'``（2026-11-01 实测）。所以先看 qualname，再看类型名。
        qualname = cls._qualname_of(func)
        owner_name = qualname.split('.', 1)[0] if qualname else ''
        for class_name, (_key, label) in cls.SOURCE_LABELS.items():
            if owner_name == class_name or type(
                    getattr(func, '__func__', func)).__name__ == class_name:
                return label
        module = str(getattr(func, '__module__', '') or '')
        if module.startswith('zmlx.ui.plugins.'):
            return '插件 · ' + cls._plugin_name(module)
        if module.startswith('zmlx.ui.utils'):
            return 'gui_api'
        if module.startswith('zmlx'):
            return '内建'
        if not module:
            # 没有 ``__module__`` 的只剩内建（C 实现）—— 说不清就写「内建」
            return '内建'
        return '外部'

    @staticmethod
    def _plugin_name(module):
        """由模块名取插件显示名（拿不到就退化成文件名的主干）.

        ⚠️ 插件是 ``exec`` 执行的，``__module__`` 往往是 **main.py** 而不是插件文件名
        （命名空间里没有 ``__name__ = '__zml_plugin__'`` 之外的模块身份）。所以这一步
        **可能只能退化成「插件」**，宁可粗一点，也不能瞎猜。
        """
        try:
            base = module.rsplit('.', 1)[-1]
        except Exception:
            base = ''
        if not base or base in ('main', '__init__'):
            return '插件注册'
        return base

    # ------------------------------------------------------------------
    @staticmethod
    def _call_signature(name, sig):
        """拼出「怎么调」的写法：``gui.<name>(...)``，去掉 ``self`` 与多余的 ``*``."""
        try:
            params = [p for key, p in sig.parameters.items() if key != 'self']
            sig = sig.replace(parameters=params)
            text = str(sig)
        except Exception:
            text = '(...)'
        return 'gui.%s%s' % (name, text)

    @staticmethod
    def _params_of(sig):
        """把签名拆成参数表（名字 / 类型 / 默认值 / 是否必填 / 说明）."""
        rows = []
        try:
            for key, param in sig.parameters.items():
                if key == 'self':
                    continue
                kind = param.kind
                if kind is inspect.Parameter.VAR_POSITIONAL:
                    default = '…'
                elif param.default is not inspect.Parameter.empty:
                    default = repr(param.default)
                else:
                    default = ''
                required = (param.default is inspect.Parameter.empty
                            and kind not in (inspect.Parameter.VAR_POSITIONAL,
                                             inspect.Parameter.VAR_KEYWORD))
                annotation = ''
                if param.annotation is not inspect.Parameter.empty:
                    if isinstance(param.annotation, str):
                        annotation = param.annotation
                    else:
                        annotation = getattr(
                            param.annotation, '__name__', None) or str(param.annotation)
                rows.append({
                    'name': key, 'default': default, 'required': required,
                    'annotation': annotation,
                    'keyword': kind in (inspect.Parameter.KEYWORD_ONLY,
                                        inspect.Parameter.VAR_KEYWORD),
                })
        except Exception:
            pass
        return rows

    @staticmethod
    def _first_line(doc):
        """docstring 的第一句（多行就取第一段直到句号）."""
        if not doc:
            return ''
        text = str(doc).strip()
        first = text.split('\n\n')[0].replace('\n', '').strip()
        if len(first) > 90:
            cut = first.find('。')
            if 0 < cut < 90:
                first = first[:cut + 1]
            else:
                first = first[:88] + '…'
        # ⚠️ 列表里这一行是**纯文本**（只有正文才做 RST→HTML），所以行内标记要剥掉：
        #    否则用户看到的是 ```MainWindow```、`**重点**` 这种字面符号。
        #    先剥双反引号再剥单反引号，顺序不能反。
        first = re.sub(r'``([^`]+)``', r'\1', first)
        first = re.sub(r'`([^`]+)`', r'\1', first)
        first = re.sub(r'\*\*([^*]+)\*\*', r'\1', first)
        return first
    @staticmethod
    def _fallback_summary(item):
        """没有 docstring 时的摘要：至少让列表里那一行不是空的."""
        if item.get('sig'):
            return '（无说明）可直接调用'
        return '（无说明）'

    @classmethod
    def _returns_of(cls, doc, sig_text):
        """从 docstring 的 ``Returns:`` / ``Raises:`` 段取返回值与异常.

        Returns:
            tuple: ``(returns_text, [raises_text, ...])``。
        """
        returns = ''
        raises = []
        if not doc:
            return returns, raises
        current = None
        for raw in str(doc).splitlines():
            line = raw.rstrip()
            stripped = line.strip()
            lower = stripped.lower()
            if lower.startswith('returns:') or lower.startswith('return:'):
                current = 'returns'
                returns = stripped.split(':', 1)[1].strip()
                continue
            if lower.startswith('raises:') or lower.startswith('raise:') or \
                    lower.startswith('yaoi:'):  # 历史笔误，不影响读取
                current = 'raises'
                continue
            if lower.startswith('args:') or lower.startswith('arguments:') or \
                    lower.startswith('parameters:'):
                current = None
                continue
            if current == 'returns':
                if stripped and (line.startswith(' ') or line.startswith('\t')):
                    returns = (returns + ' ' + stripped).strip()
                else:
                    current = None
            elif current == 'raises':
                if stripped and (line.startswith(' ') or line.startswith('\t')):
                    raises.append(stripped)
                else:
                    current = None
        if len(returns) == 0 and sig_text:
            if '-> None' in sig_text:
                returns = 'None'
        return returns, raises

    @classmethod
    def _section(cls, doc, headings):
        """截取 docstring 里某个小标题下的正文（``Example:`` / ``Note:`` 之类）.

        Args:
            doc: 整段 docstring。
            headings: 认作标题的**小写**词表。

        Returns:
            str: 该段正文（已去掉缩进）；没有返回 ``''``。
        """
        if not doc:
            return ''
        lines = str(doc).splitlines()
        start = None
        base_indent = None
        for idx, line in enumerate(lines):
            key = line.strip().lower().rstrip(':')
            if key in headings:
                start = idx + 1
                base_indent = cls._indent(line)
                break
        if start is None:
            return ''
        body = []
        for line in lines[start:]:
            if not line.strip():
                body.append('')
                continue
            indent = cls._indent(line)
            # 退回顶格（或比标题更靠左）= 这一段结束了
            if indent <= (base_indent or 0) and not line.startswith(' '):
                if not line.strip().startswith('::'):
                    break
            body.append(line)
        return cls._dedent('\n'.join(body)).strip('\n')

    @staticmethod
    def _indent(line):
        """这一行的缩进宽度（tab 按 4 算；空行返回 0 ⇒「不参与缩进比较」）."""
        if not line.strip():
            return 0
        expanded = line.replace('\t', '    ')
        return len(expanded) - len(expanded.lstrip())

    @staticmethod
    def _dedent(text):
        """去掉公共缩进（空行不参与计算 —— ``textwrap.dedent`` 正是这个语义）."""
        import textwrap
        return textwrap.dedent(text)

    # ------------------------------------------------------------------
    @staticmethod
    def filter_items(items, keyword='', group=None, source=None, only_documented=False,
                     only_example=False):
        """按搜索词 / 分组 / 来源筛选清单（纯函数，界面与自测共用）.

        Args:
            items: :meth:`build` 出来的 ``items``。
            keyword: 搜索词。空格分词，**每个词都要命中**（名字 / 签名 / 说明 / 参数名 /
                别名），大小写不敏感。
            group: 只看这个分组键；``None`` 表示全部。
            source: 只看这个来源文字；``None`` 表示全部。
            only_documented: 只看有 docstring 的。
            only_example: 只看带用例的（点击「只显示示例」后，搜索框为空时会**退化成**只看带
                用例的；这里只负责**这个开关本身**）。

        Returns:
            list: 命中的条目（保持原顺序）。
        """
        words = [word for word in str(keyword or '').lower().split() if word]
        result = []
        for item in items:
            if group is not None and item.get('group') != group:
                continue
            if source is not None and item.get('source') != source:
                continue
            if only_documented and not item.get('doc'):
                continue
            if only_example and not item.get('example'):
                continue
            if words:
                haystack = ' '.join([
                    str(item.get('name', '')),
                    str(item.get('sig', '')),
                    str(item.get('doc', '')),
                    str(item.get('one_line', '')),
                    ' '.join(str(p.get('name', '')) for p in item.get('params', [])),
                ]).lower()
                if not all(word in haystack for word in words):
                    continue
            result.append(item)
        return result


# ======================================================================
# 正文渲染：把一条命令画成 HTML（配色全部取 QPalette，跟随暗色 / 自定义样式表）
# ======================================================================

class _Html:
    """把 :class:`_Docs` 的条目渲染成正文 HTML（不实例化，纯命名空间）.

    ⚠️ **颜色一律从 ``QPalette`` 现取**，不写死色值：程序有暗色模式，用户还能在
    「设置 → 样式表」里换配色（见 ``widgets/AGENTS.md`` 的「控件里的颜色」）。
    ⚠️ 正文里**只用** Qt 富文本认得的子集：``h1``-``h3`` / ``p`` / ``table`` / ``pre`` /
    ``ul`` / ``a`` / ``b`` / ``code``。``div`` 的 ``style`` 在 Qt 里只有部分生效，
    所以分节靠标题与表格，不靠花哨的盒子 —— 两条渲染路径（``markdown`` 库 / Qt 自带）
    看起来要一致。
    """

    #: 名字到「复制到剪贴板」的链接协议（与 :meth:`ApiDocView._on_anchor_clicked` 对应）
    COPY_SCHEME = 'apidoc-copy:'
    #: 「到源码」链接协议
    SOURCE_SCHEME = 'apidoc-src:'

    @classmethod
    def palette(cls, pal):
        """按用途取色（``text`` / ``muted`` / ``border`` / ``code_bg`` / ``link`` / ``accent``）."""
        def color(*roles):
            for role_name in roles:
                role = getattr(QtGui.QPalette.ColorRole, role_name, None)
                if role is None:
                    continue
                try:
                    return pal.color(role)
                except Exception:
                    continue
            return pal.color(QtGui.QPalette.ColorRole.WindowText)

        dark = color('Base', 'Window').lightness() < 128
        return {
            'text': color('WindowText', 'Text'),
            'muted': color('PlaceholderText', 'Mid', 'Dark', 'WindowText'),
            'border': color('Mid', 'Dark', 'WindowText'),
            'code_bg': QtGui.QColor('#3c3c3c' if dark else '#f0f0f0'),
            'link': color('Link', 'Highlight'),
            'accent': color('Highlight', 'Link'),
            'base': color('Base', 'Window'),
            'dark': dark,
        }

    @classmethod
    def document(cls, items, title, subtitle, colors):
        """一整页（含页首标题与「怎么用」三条）—— 详情为空时显示它."""
        esc = html.escape
        parts = [
            '<h1>%s</h1>' % esc(title),
            '<p style="color:%s">%s</p>' % (colors['muted'].name(), esc(subtitle)),
            '<h2>怎么用</h2>',
            '<table border="1" cellspacing="0" cellpadding="4" width="100%">',
            '<tr><th width="30%%">想做的事</th><th>写法</th></tr>',
            '<tr><td>列出全部命令名</td><td><code>print(gui.list_all())</code></td></tr>',
            '<tr><td>取某个函数</td><td><code>f = gui.get_func(\'get_widget\')</code></td></tr>',
            '<tr><td>看它的帮助</td><td><code>help(f)</code>（或本页右侧详情）</td></tr>',
            '<tr><td>直接调用</td><td><code>gui.get_widget(SomeWidget, caption=\'标题\')</code></td></tr>',
            '</table>',
            '<p style="color:%s">共 <b>%d</b> 条命令。左侧按用途分组，顶部可搜索；'
            '双击列表一行把 <code>gui.名字(</code> 复制到剪贴板。</p>'
            % (colors['muted'].name(), len(items)),
            '<p style="color:%s">⚠️ 本页只读：所有「复制」都只写剪贴板，'
            '不会替你执行任何命令。</p>' % (colors['muted'].name()),
        ]
        return '\n'.join(parts), []

    @classmethod
    def item(cls, item, colors):
        """一条命令的详情正文.

        Args:
            item: :class:`_Docs` 的条目。
            colors: :meth:`palette` 的结果。

        Returns:
            tuple: ``(html_text, anchors)`` —— ``anchors`` 是文档内锚点列表
            （不含 ``#``），供「跳到签名 / 跳到参数」这类链接使用。
        """
        esc = html.escape
        anchors = []
        name = item.get('name', '')
        muted = colors['muted'].name()
        link = colors['link'].name()
        parts = []

        parts.append('<h1><code style="color:%s">gui.%s</code></h1>'
                     % (colors['accent'].name(), esc(name)))
        # 一行元信息：来源 · 所在分组 · 别名
        meta = ['来源：<b>%s</b>' % esc(item.get('source', '未知'))]
        meta.append('分组：%s' % esc(item.get('group_title', '')))
        if item.get('alias'):
            meta.append('是 <a href="#item-%s"><code>gui.%s</code></a> 的别名'
                        % (esc(item['alias']), esc(item['alias'])))
        if item.get('aliases'):
            meta.append('别名：' + '、'.join(
                '<a href="#item-%s"><code>gui.%s</code></a>' % (esc(a), esc(a))
                for a in item['aliases']))
        parts.append('<p style="color:%s">%s</p>' % (muted, '　·　'.join(meta)))

        # ---- 签名 ----
        parts.append('<h2 name="signature" id="signature">签名</h2>')
        anchors.append('signature')
        if item.get('call_sig'):
            parts.append('<pre style="background-color:%s">%s</pre>'
                         % (colors['code_bg'].name(), esc(item['call_sig'])))
        if item.get('qualname'):
            where = item.get('module', '') or ''
            if item.get('file'):
                where += '  ·  ' + (item.get('file') or '')
                if item.get('line'):
                    where += ':%d' % item['line']
            parts.append('<p style="color:%s">实现：<code>%s</code></p>'
                         % (muted, esc(where.strip(' ·'))))
            if item.get('file'):
                parts.append('<p><a href="%s%s">在代码编辑器里打开它</a></p>'
                             % (cls.SOURCE_SCHEME, esc(name)))

        # ---- 参数 ----
        parts.append('<h2 name="parameters" id="parameters">参数</h2>')
        anchors.append('parameters')
        params = item.get('params') or []
        if not params:
            parts.append('<p style="color:%s">（无参数）</p>' % muted)
        else:
            parts.append('<table border="1" cellspacing="0" cellpadding="4" width="100%">')
            parts.append('<tr><th width="24%%">名字</th><th width="20%%">类型</th>'
                         '<th width="30%%">默认值</th><th width="10%%">必填</th>'
                         '<th>复制</th></tr>')
            for param in params:
                default = param.get('default', '') or '—'
                annotation = param.get('annotation', '') or '—'
                name_text = param['name']
                if param.get('keyword'):
                    name_text = '**' + name_text
                elif default == '…':
                    name_text = '*' + name_text
                parts.append(
                    '<tr><td><code>%s</code></td><td>%s</td><td><code>%s</code></td>'
                    '<td>%s</td><td><a href="%s%s">复制</a></td></tr>'
                    % (esc(name_text), esc(annotation), esc(default),
                       '是' if param.get('required') else '',
                       cls.COPY_SCHEME, esc('param:' + param['name'])))
            parts.append('</table>')
            parts.append('<p style="color:%s">点「复制」把 <code>参数名=</code> 放进剪贴板。</p>'
                         % muted)

        # ---- 返回值 / 异常 ----
        parts.append('<h2 name="returns" id="returns">返回值</h2>')
        anchors.append('returns')
        returns = item.get('returns', '')
        parts.append('<p>%s</p>' % (esc(returns) if returns
                                    else '<span style="color:%s">（未说明）</span>' % muted))
        raises = item.get('raises') or []
        if raises:
            parts.append('<p><b>可能抛出：</b>%s</p>'
                         % '；'.join(esc(item) for item in raises))

        # ---- 说明 ----
        parts.append('<h2 name="description" id="description">说明</h2>')
        anchors.append('description')
        doc = item.get('doc', '')
        if doc:
            parts.append(cls._text_to_html(cls._strip_sections(doc)))
        else:
            parts.append('<p style="color:%s">（这条命令没有 docstring —— '
                         '说明只能从签名与「到源码」去读。）</p>' % muted)

        # ---- 用例 ----
        example = item.get('example', '')
        if example:
            parts.append('<h2 name="example" id="example">用例</h2>')
            anchors.append('example')
            parts.append('<pre style="background-color:%s">%s</pre>'
                         % (colors['code_bg'].name(), esc(example)))

        # ---- 注意 ----
        note = item.get('note', '')
        if note:
            parts.append('<h2 name="note" id="note">注意</h2>')
            anchors.append('note')
            parts.append('<p><b>%s</b></p>' % esc(note).replace('\n', '<br/>'))

        # ---- 按钮式链接（正文里给一条明显的「复制」入口）----
        parts.append('<p style="color:%s">' % link
                     + '<a href="%s%s">复制 gui.%s(</a>' % (cls.COPY_SCHEME, esc(name), esc(name))
                     + '　·　<a href="#item-%s">在列表里定位</a>' % esc(name)
                     + '</p>')
        return '\n'.join(parts), anchors

    # ------------------------------------------------------------------
    @classmethod
    def _strip_sections(cls, doc):
        """去掉已单独成节的 ``Example:`` / ``Note:``（免得详情里重复两遍）.

        ⚠️ 缩进判断复用 :meth:`_Docs._indent`（「比标题更靠左 = 这一段结束」），
        不要在这里另写一套 —— 两处规则一旦不同，就会出现「说明里少了一段」这种
        很难察觉的截断。
        """
        keep = []
        skipping = False
        base_indent = 0
        for line in str(doc).splitlines():
            indent = _Docs._indent(line)
            key = line.strip().lower().rstrip(':')
            if not skipping and key in (_Docs.EXAMPLE_HEADINGS + _Docs.NOTE_HEADINGS):
                skipping = True
                base_indent = indent
                continue
            if skipping:
                if line.strip() and indent <= base_indent:
                    skipping = False
                else:
                    continue
            keep.append(line)
        return '\n'.join(keep).strip('\n')

    @classmethod
    def _text_to_html(cls, text):
        """docstring 正文 → 极简 HTML（保留换行与缩进代码块）.

        ⚠️ 刻意**不引第三方 markdown 库**：docstring 不是 Markdown，硬解析往往画出更糟的
        结果（``***``、表格符号全被当语法）。这里只做三件事：转义、连续缩进行包 ``pre``、
        行尾两空格转 ``<br/>``。缩进代码块在 Qt 里就是「等宽 + 保留空白」。
        """
        esc = html.escape
        lines = str(text or '').splitlines()
        out = []
        code = []

        def flush():
            if code:
                out.append('<pre><code>%s</code></pre>' % esc('\n'.join(code)))
                code.clear()

        for line in lines:
            # ⚠️ 只有**连续的多行**缩进才算「代码块」：单行缩进在 docstring 里往往只是
            #    续行，包成 pre 会让正文莫名其妙地变成等宽字体。
            if (line.startswith('    ') or line.startswith('\t')) and line.strip():
                code.append(line.replace('\t', '    '))
                continue
            if len(code) == 1:
                out.append(esc(code[0].strip()))
                code.clear()
            flush()
            if not line.strip():
                out.append('')
            else:
                out.append(esc(line.rstrip()) + ('<br/>' if line.endswith('  ') else ''))
        if len(code) == 1:
            out.append(esc(code[0].strip()))
            code.clear()
        flush()
        return '<p>%s</p>' % '\n'.join(out)


# ======================================================================
# 本页自用的 QAction（**不**整窗刷新）
# ======================================================================

def _make_action(parent, text, icon=None, slot=None):
    """建一个本页自用的 ``QAction``（顶部工具栏、详情右键菜单共用）.

    ⚠️ **不用 ``zmlx.ui.alg.create_action``**：那个包装在 ``slot`` 执行完会
    ``gui.refresh()`` 整窗刷新，还写一条 ``log`` —— 而本页的动作全是本地的
    （复制命令名、回首页、刷新列表），不该让主窗口跟着重刷一遍。
    ⚠️ 图标取不到就退化成纯文字（不抛）：图标名写错只影响观感，不该让页面建不出来。

    Args:
        parent: ``QAction`` 的父对象（一般是使用它的控件）。
        text: 菜单 / 按钮文字。
        icon: ``zmlx.ui.settings.load_icon`` 认的图标名（如 ``'refresh'``）。
        slot: 触发时调用的无参可调用对象。

    Returns:
        ``QtGui.QAction``。
    """
    action = QtGui.QAction(text, parent)
    if icon is not None:
        try:
            from zmlx.ui.settings import load_icon
            action.setIcon(load_icon(icon))
        except Exception:
            pass
    if slot is not None:
        action.triggered.connect(lambda _=False: slot())
    return action


# ======================================================================
# 控件：GUI 接口说明页
# ======================================================================

class ApiDocView(QtWidgets.QWidget):
    """GUI 接口说明页（顶层控件）：左目录 + 中列表 + 右详情.

    Attributes:
        search_edit: 顶部搜索框（``QLineEdit``）。
        group_list: 左侧目录（``QListWidget``，第一项是「全部命令」）。
        table: 中间列表（``QTableWidget``，三列：名字 / 签名摘要 / 来源）。
        detail: 右侧详情正文（``QTextBrowser``，接 ``anchorClicked``）。
        items: 本次扫描读到的全部条目（:class:`_Docs` 的结果）。
        warnings: 本次扫描留下的提示。
    """

    #: 列表三列（第二列是签名摘要，第三列是来源）
    COLUMNS = ('命令', '签名摘要', '来源')

    #: 状态栏 / 悬停提示（``TextBrowser.set_status`` 用的那句）
    _STATUS = ('GUI 接口说明：左侧按用途分组，顶部搜索，双击一行复制到剪贴板；'
               '「到源码」用代码编辑器打开')

    def __init__(self, parent=None):
        super().__init__(parent)
        self.context_actions = []
        self.items = []
        self.groups = []
        self.warnings = []
        self._current = None
        self._loading = False

        # ---- 状态恢复：上次看的是哪一条（只在本进程内记住，不落盘）----
        try:
            from zmlx.system import app_data
            self._last_name = app_data.get('api_doc_last', None)
        except Exception:
            self._last_name = None

        self.search_edit = self._create_search()
        self.group_list = self._create_groups()
        self.table = self._create_table()
        self.detail = self._create_detail()
        self.navigation = self._create_navigation()

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.group_list)
        splitter.addWidget(self.table)
        splitter.addWidget(self.detail)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 2)
        splitter.setSizes([168, 300, 560])

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.navigation)
        layout.addWidget(splitter, 1)

        # ⚠️ 构造里**不读命令表**：整页可能要点两次才真正显示，
        #    而 ``gui.get_widget`` 的 ``oper`` 每次调用都会跑 —— 加载推迟到 ``reload()``。
        self._show_placeholder('正在读取命令表……')

    # ------------------------------------------------------------------
    # 构造各个部件
    # ------------------------------------------------------------------
    def _create_search(self):
        """顶部搜索框（占位文字写明会匹配哪些字段）."""
        edit = QtWidgets.QLineEdit()
        edit.setClearButtonEnabled(True)
        edit.setPlaceholderText(
            '搜索命令…（空格分词，全部命中；匹配名字 / 签名 / 说明 / 参数名）')
        edit.setToolTip('搜索命令名、签名、说明与参数名。按 Esc 清空。')
        edit.textChanged.connect(self._on_filter_changed)
        return edit

    def _create_groups(self):
        """左侧目录（``QListWidget``：单列、无表头；第一项「全部命令」是通配）."""
        tree = QtWidgets.QListWidget()
        tree.setUniformItemSizes(True)
        tree.setMinimumWidth(140)
        tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        tree.setToolTip('按用途分组。点一下只看这一组，点「全部命令」恢复')
        tree.currentRowChanged.connect(self._on_group_changed)
        return tree

    def _create_table(self):
        """中间列表：三列、只读、整行选中、可排序（点标题排序）."""
        table = QtWidgets.QTableWidget(0, len(self.COLUMNS))
        table.setHorizontalHeaderLabels(self.COLUMNS)
        table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setWordWrap(False)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.setToolTip('双击一行：把 gui.名字( 复制到剪贴板；单击选中看右侧详情')
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False)
        table.setColumnWidth(0, 190)
        table.itemSelectionChanged.connect(self._on_selection_changed)
        table.cellDoubleClicked.connect(self._on_double_clicked)
        return table

    def _create_detail(self):
        """右侧详情正文（``TextBrowser``：自带「清除内容」右键项与状态栏提示）."""
        from zmlx.ui.widgets import TextBrowser
        view = TextBrowser()
        view.setOpenLinks(False)
        view.setOpenExternalLinks(False)
        view.anchorClicked.connect(self._on_anchor_clicked)
        view.set_status(self._STATUS)
        self.context_actions = [
            _make_action(view, '复制本页命令名', icon='save',
                         slot=self._copy_current),
            _make_action(view, '回到「怎么用」', icon='home',
                         slot=lambda: self._show_placeholder(
                             '已回到首页：左侧选一条命令看详情')),
        ]
        # ⚠️ 必须 **append/extend**，不能赋值：``TextBrowser.__init__`` 里已经放了
        #    一条「清除内容」（绑它自己的 ``self.clear``），赋值会把它顶掉，而状态栏
        #    文案还写着「右键「清除内容」清空正文」—— 用户会点到一个不存在的菜单项。
        view.context_actions.extend(self.context_actions)
        return view

    def _create_navigation(self):
        """顶部导航条：搜索框 + 「只看」筛选 + 只显示示例 + 计数 + 刷新.

        ⚠️ 按钮与右键菜单统一走 :func:`_make_action`，**不用** ``zmlx.ui.alg.create_action``：
        后者会 ``gui.refresh()`` 整窗刷新并写一条 ``log``，而本页的操作全是本地的。
        """
        bar = QtWidgets.QToolBar(self)
        bar.setMovable(False)
        bar.setFloatable(False)
        bar.setIconSize(QtCore.QSize(16, 16))
        bar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        bar.addWidget(self.search_edit)

        bar.addWidget(QtWidgets.QLabel(' 只看 '))
        self.group_combo = QtWidgets.QComboBox()
        self.group_combo.setMinimumWidth(120)
        self.group_combo.setToolTip('按用途筛选（与左侧目录联动）')
        self.group_combo.currentIndexChanged.connect(self._on_group_combo_changed)
        bar.addWidget(self.group_combo)

        bar.addWidget(QtWidgets.QLabel(' 来源 '))
        self.source_combo = QtWidgets.QComboBox()
        self.source_combo.setMinimumWidth(110)
        self.source_combo.setToolTip('筛选：主窗口方法 / 插件注册 / 内建 …')
        self.source_combo.currentIndexChanged.connect(self._on_filter_changed)
        bar.addWidget(self.source_combo)

        self.check_example = QtWidgets.QCheckBox('只带示例')
        self.check_example.setToolTip('只显示 docstring 里写了 Example / 用例的命令')
        self.check_example.toggled.connect(self._on_filter_changed)
        bar.addWidget(self.check_example)

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                             QtWidgets.QSizePolicy.Policy.Preferred)
        bar.addWidget(spacer)

        self.label_count = QtWidgets.QLabel('')
        self.label_count.setToolTip('当前显示 / 全部命令数，以及本页读取是否有警告')
        bar.addWidget(self.label_count)

        def make(icon_name, text, tip, slot):
            action = _make_action(bar, text, icon=icon_name, slot=slot)
            action.setToolTip(tip)
            bar.addAction(action)
            return action

        make('refresh', ' 刷新', '重新读一遍命令表（插件注册了新命令后点这里）',
             self.reload)
        make('console', ' 复制', '把当前这条命令的 gui.名字( 复制到剪贴板',
             self._copy_current)
        return bar

    # ------------------------------------------------------------------
    # 加载与筛选
    # ------------------------------------------------------------------
    def reload(self, name=None):
        """**重新读一遍命令表**（打开页面时、点顶部「刷新」时都走这里）.

        ⚠️ **同步扫描，不开线程、不调 ``gui.call``**。理由（2026-11-01 实测）：
        之前把扫描派到后台线程、并在 ``gui.call`` 里回 GUI 线程取名字，结果这条链
        与框架的刷新链（``create_action`` 每执行完一个动作就调 ``gui.refresh()`` →
        ``MainWindow.refresh()`` → 当前页 ``refresh()``）纠缠在一起，点菜单直接报
        ``maximum recursion depth exceeded``。整页只有一百多条命令、``inspect`` 约 20 ms，
        **同步做**完全够快，而且行为一眼可见。

        触发点只有两处（都不在刷新链上）：打开 / 切到本页、点顶部「刷新」。
        命令表若被插件「临时加载」改过（``load_now`` 不重启就 ``add_func``），
        点一下「刷新」即可看到新命令。

        Args:
            name: 扫描完成后要定位到的命令名；``None`` 表示保持当前位置
                （恢复「上次看的那一条」；第一次显示时默认停在
                :attr:`_Docs.HOME_ITEM` —— ``gui.list_all``）。
        """
        target = name if isinstance(name, str) and name else self._current_name()
        self._loading = True
        self._show_loading()
        try:
            docs = _Docs().build()
            self.items = docs.get('items', [])
            self.groups = docs.get('groups', [])
            self.warnings = docs.get('warnings', [])
            self._rebuild_combos()
            self._apply(self.search_edit.text(),
                        self._selected_group(),
                        self._selected_source(),
                        self.check_example.isChecked())
            if not target:
                target = _Docs.HOME_ITEM if self._last_name is None else self._last_name
            if target and not self.select_name(target):
                # 指定的名字不在清单里（例如插件被关掉了）：退回首页那一条
                self.select_name(_Docs.HOME_ITEM)
        except Exception as err:
            self._show_placeholder('读取命令表失败：%s' % err)
            print('Error: GUI 接口页读取命令表失败: %s' % err)
        finally:
            self._loading = False
            self._sync_count()

    def _current_name(self):
        """当前选中的命令名（没有就取上次看的那条）."""
        if self._current is not None:
            return self._current.get('name') or None
        return getattr(self, '_last_name', None) or None

    def _rebuild_combos(self):
        """按本次读到的分组 / 来源重建两个下拉框（保持当前选择）."""
        current_group = self._selected_group()
        current_source = self._selected_source()

        self.group_combo.blockSignals(True)
        self.source_combo.blockSignals(True)
        try:
            # ---- 左侧目录 ----
            self.group_list.clear()
            total = QtWidgets.QListWidgetItem('全部命令  (%d)' % len(self.items))
            total.setData(QtCore.Qt.ItemDataRole.UserRole, None)
            self.group_list.addItem(total)
            for key, title, _hint, members in self.groups:
                node = QtWidgets.QListWidgetItem('%s  (%d)' % (title, len(members)))
                node.setData(QtCore.Qt.ItemDataRole.UserRole, key)
                node.setToolTip(_hint)
                self.group_list.addItem(node)

            # ---- 「只看」下拉 ----
            self.group_combo.clear()
            self.group_combo.addItem('全部用途', None)
            for key, title, _hint, members in self.groups:
                self.group_combo.addItem('%s (%d)' % (title, len(members)), key)

            # ---- 来源下拉：按出现次数排序，次数一样按名字 ----
            counts = {}
            for item in self.items:
                source = item.get('source', '未知')
                counts[source] = counts.get(source, 0) + 1
            self.source_combo.clear()
            self.source_combo.addItem('全部来源', None)
            for source in sorted(counts, key=lambda s: (-counts[s], s)):
                self.source_combo.addItem('%s (%d)' % (source, counts[source]), source)
        finally:
            self.group_combo.blockSignals(False)
            self.source_combo.blockSignals(False)

        self._select_data(self.group_combo, current_group)
        self._select_data(self.source_combo, current_source)
        self._select_group_in_list(current_group)

    @staticmethod
    def _select_data(combo, value):
        """在下拉框里选中给定 ``data``（找不到就退回第一项 = 不过滤）."""
        index = combo.findData(value)
        combo.blockSignals(True)
        combo.setCurrentIndex(max(0, index))
        combo.blockSignals(False)

    def _select_group_in_list(self, key):
        """让左侧目录与「只看」下拉一致（阻断信号，免得互相触发成环）."""
        self.group_list.blockSignals(True)
        try:
            for row in range(self.group_list.count()):
                node = self.group_list.item(row)
                if node.data(QtCore.Qt.ItemDataRole.UserRole) == key:
                    self.group_list.setCurrentRow(row)
                    break
        finally:
            self.group_list.blockSignals(False)

    def _selected_group(self):
        """当前分组键（``None`` = 全部）."""
        data = self.group_combo.currentData()
        return data if isinstance(data, str) and data else None

    def _selected_source(self):
        """当前来源文字（``None`` = 全部）."""
        data = self.source_combo.currentData()
        return data if isinstance(data, str) and data else None

    def _apply(self, keyword, group, source, only_example):
        """按条件筛出清单并填进表格（保留「当前选中那条」）."""
        current = self._current.get('name') if self._current else None
        rows = _Docs.filter_items(
            self.items, keyword=keyword, group=group, source=source,
            only_example=only_example)

        table = self.table
        table.blockSignals(True)
        try:
            table.setRowCount(0)
            table.setRowCount(len(rows))
            for row, item in enumerate(rows):
                name_value = 'gui.' + item['name']
                if item.get('alias'):
                    name_value += '  → ' + item['alias']
                for column, value in enumerate((
                        name_value, item.get('one_line', ''), item.get('source', ''))):
                    cell = QtWidgets.QTableWidgetItem(str(value))
                    # ⚠️ 只读表格必须**逐项**去掉 ItemIsEditable（见 widgets/AGENTS.md：
                    #    WSLg 下双击弹编辑器会段错误），总闸已在 _create_table 里设过。
                    cell.setFlags(cell.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                    if column == 0:
                        cell.setToolTip('双击：复制 gui.%s( 到剪贴板\n%s'
                                        % (item['name'], item.get('one_line', '')))
                        cell.setData(QtCore.Qt.ItemDataRole.UserRole, item.get('name', ''))
                    elif column == 2:
                        cell.setToolTip(item.get('source', ''))
                    table.setItem(row, column, cell)
            table.resizeColumnToContents(2)
        finally:
            table.blockSignals(False)
        self._rows = rows

        if len(rows) == 0:
            self._current = None
            self._show_placeholder('没有符合条件的命令 —— 试试清空搜索框或把「只看」'
                                   '切回「全部用途」')
            self._sync_count()
            return
        target = current if current else rows[0].get('name')
        self.select_name(target)

    def select_name(self, name):
        """在**当前筛选结果**里选中给定名字；不在结果里就返回 ``False``."""
        name = str(name or '')
        if name.startswith('gui.'):
            name = name[4:]
        rows = getattr(self, '_rows', None) or []
        for row, item in enumerate(rows):
            if item.get('name') == name:
                self.table.blockSignals(True)
                try:
                    self.table.selectRow(row)
                    self.table.scrollToItem(
                        self.table.item(row, 0),
                        QtWidgets.QAbstractItemView.ScrollHint.PositionAtCenter)
                finally:
                    self.table.blockSignals(False)
                self._show_item(item)
                return True
        return False

    # ------------------------------------------------------------------
    # 显示
    # ------------------------------------------------------------------
    def _show_item(self, item):
        """把一条命令画到右侧详情."""
        self._current = item
        colors = _Html.palette(self.detail.palette())
        try:
            body, _anchors = _Html.item(item, colors)
        except Exception as err:
            body = ('<h1>%s</h1><p>渲染失败：%s</p>'
                    % (html.escape(item.get('name', '?')), html.escape(str(err))))
        self.detail.setHtml(body)
        self.detail.verticalScrollBar().setValue(0)
        try:
            from zmlx.system import app_data
            app_data.put('api_doc_last', item.get('name', ''))
        except Exception:
            pass
        name = item.get('name', '')
        self.detail.set_status('gui.%s —— 双击列表行可复制；右键「清除内容」清空正文' % name)

    def _show_placeholder(self, text):
        """首页 / 空结果 / 出错时的正文."""
        self._current = None
        colors = _Html.palette(self.detail.palette())
        if self.items:
            subtitle = text
            body, _anchors = _Html.document(
                self.items, _TITLE, subtitle + '　共 %d 条命令。' % len(self.items), colors)
        else:
            esc = html.escape
            body = ('<h1>%s</h1><p>%s</p>' % (esc(_TITLE), esc(text)))
            if self.warnings:
                body += '<h2>读取时的提示</h2><ul>%s</ul>' % ''.join(
                    '<li><code>%s</code></li>' % esc(w) for w in self.warnings)
        self.detail.setHtml(body)

    def _show_loading(self):
        """扫描进行中：顶部计数变成「读取中…」，正文保持原样（不闪烁、不清空）."""
        self.label_count.setText('读取命令表…')
        self.label_count.setToolTip('正在从 gui.list_all() 与 gui.get_func() 重新读取…')
        self.detail.set_status('正在读取 gui 命令表…')

    def _sync_count(self):
        """刷新右上角的计数与提示图标."""
        total = len(self.items)
        shown = len(getattr(self, '_rows', None) or [])
        text = '共 %d 条，显示 %d 条' % (total, shown)
        if self.warnings:
            text += '（%d 条警告）' % len(self.warnings)
            self.label_count.setStyleSheet('')
            self.label_count.setToolTip('\n'.join(self.warnings))
        else:
            self.label_count.setToolTip('命令总数 / 当前筛选后显示的条数')
        self.label_count.setText(text)

    # ------------------------------------------------------------------
    # 信号
    # ------------------------------------------------------------------
    def _on_filter_changed(self, *_args):
        """搜索框 / 来源下拉 / 复选框变了：只重填表格，不重读命令表."""
        if self._loading:
            return
        self._apply(self.search_edit.text(), self._selected_group(),
                    self._selected_source(), self.check_example.isChecked())

    def _on_group_changed(self, row):
        """左侧目录换了一项：同步下拉框（下拉框的信号会去刷新表格）."""
        if self._loading or row < 0:
            return
        node = self.group_list.item(row)
        if node is None:
            return
        key = node.data(QtCore.Qt.ItemDataRole.UserRole)
        self.group_combo.blockSignals(True)
        try:
            index = self.group_combo.findData(key)
            self.group_combo.setCurrentIndex(max(0, index))
        finally:
            self.group_combo.blockSignals(False)
        self._on_filter_changed()

    def _on_group_combo_changed(self, *_args):
        """「只看」下拉换了：同步左侧目录，再刷新表格."""
        if self._loading:
            return
        self._select_group_in_list(self._selected_group())
        self._on_filter_changed()

    def _on_selection_changed(self):
        """列表选中项变了：显示它的详情."""
        if self._loading:
            return
        rows = getattr(self, '_rows', None) or []
        row = self.table.currentRow()
        if 0 <= row < len(rows):
            self._show_item(rows[row])

    def _on_double_clicked(self, row, column):
        """双击一行：把 ``gui.名字(`` **复制到剪贴板**（粘贴到控制台即可）."""
        rows = getattr(self, '_rows', None) or []
        if 0 <= row < len(rows):
            self._copy('gui.%s(' % rows[row].get('name', ''))

    def _on_anchor_clicked(self, url):
        """正文里点链接：复制 / 到源码 / 锚点 / 列表内定位，其余交给默认动作."""
        text = url.toString() if hasattr(url, 'toString') else str(url)
        if text.startswith(_Html.COPY_SCHEME):
            target = text[len(_Html.COPY_SCHEME):]
            if target.startswith('param:'):
                # 参数表里的「复制」：只复制 ``参数名=``（整条命令由上面那个按钮负责）
                self._copy('%s=' % target[len('param:'):])
            else:
                self._copy('gui.%s(' % target)
            return True
        if text.startswith(_Html.SOURCE_SCHEME):
            self._open_source(text[len(_Html.SOURCE_SCHEME):])
            return True
        if text.startswith('#item-'):
            name = text[len('#item-'):]
            if self.select_name(name):
                return True
            # 不在当前筛选结果里：清掉筛选再试一次（用户明确点了「在列表里定位」）
            self.search_edit.clear()
            self._select_data(self.group_combo, None)
            self._select_group_in_list(None)
            self._select_data(self.source_combo, None)
            self.check_example.setChecked(False)
            self._apply('', None, None, False)
            self.select_name(name)
            return True
        if text.startswith('#'):
            self.detail.scrollToAnchor(text[1:])
            return True
        return False

    # ------------------------------------------------------------------
    # 动作
    # ------------------------------------------------------------------

    def _copy(self, text):
        """复制到剪贴板，并在详情区底部的状态里去一句（``TextBrowser.set_status``）."""
        try:
            QtWidgets.QApplication.clipboard().setText(text)
        except Exception as err:
            print('Warning: 复制到剪贴板失败: %s' % err)
            return
        self.detail.set_status('已复制到剪贴板：%s' % text)

    def _copy_current(self):
        """把当前这条命令的 ``gui.名字(`` 复制到剪贴板."""
        if self._current is None:
            self.detail.set_status('当前没有选中命令')
            return
        self._copy('gui.%s(' % self._current.get('name', ''))

    def _open_source(self, name):
        """用代码编辑器打开这条命令的实现文件（``gui.open_code``）."""
        item = self._find(name)
        if item is None or not item.get('file'):
            self.detail.set_status('这条命令没有源码位置（内置函数？）：%s' % name)
            return
        try:
            from zmlx.ui.gui_buffer import gui as _gui
            _gui.open_code(item['file'])
        except Exception as err:
            print('Warning: 打开 <%s> 失败: %s' % (item.get('file'), err))

    def _find(self, name):
        """按名字在**全部条目**里找一条（不受当前筛选影响）."""
        for item in self.items:
            if item.get('name') == name:
                return item
        return None

    # ------------------------------------------------------------------
    # 框架钩子
    # ------------------------------------------------------------------
    def showEvent(self, event):
        """显示时同步一次计数（**只做极轻的事**，不重扫命令表）.

        ⚠️ 本页**刻意不提供** ``refresh()``：``MainWindow.refresh`` 会在每次「显示 → 刷新」
        以及 ``create_action`` 包装过的**每个菜单动作**之后被调用 —— 那是「界面刷新」的
        链路，而本页的内容是接口说明，启动之后就基本定型，没必要跟着重扫。刷新时机只保留
        两处，都在用户明确操作时：打开标签页、点顶部「刷新」按钮（见 :meth:`reload`）。
        """
        super().showEvent(event)
        self._sync_count()

    def cleanup_before_tab_close(self):
        """关标签页时的收尾：断开链接回调（本页没有后台线程，也不必 ``wait()``）."""
        try:
            self.detail.anchorClicked.disconnect(self._on_anchor_clicked)
        except Exception:
            pass


# ======================================================================
# 入口：命令 + 菜单
# ======================================================================

def show_api_doc(name=None):
    """打开「GUI 接口」页（GUI 命令 ``gui.show_api_doc()``）.

    Args:
        name: 想直接定位到的命令名（可带 ``gui.`` 前缀）；不给时显示首页，
            并尽量回到上次看的那一条。

    ⚠️ 与其它插件里的 ``show_xxx`` 一样：这里**只派发命令**，真正开标签页的动作在
    :func:`_open` 里 —— 这样无论菜单、脚本还是后台线程调用，「开标签页」都发生在 GUI 线程。

    Example:
        >>> gui.show_api_doc()            # 打开首页（并回到上次看的那一条）
        >>> gui.show_api_doc('plot')      # 直接定位到 gui.plot
    """
    from zmlx.ui.gui_buffer import gui as _gui
    _gui.command('show_api_doc', name=name)


def _open(name=None):
    """真正打开标签页（注册成命令 ``show_api_doc``，故只在 GUI 线程里执行）."""
    from zmlx.ui.gui_buffer import gui as _gui

    target = str(name or '').strip()
    if target.startswith('gui.'):
        target = target[4:]

    def oper(widget):
        """每次调用都会跑（新建与复用两条分支都跑，见 ``TabWidget.get_widget``）.

        ⚠️ 只有**第一次**（页面还没数据）才重扫；之后只按 ``name`` 定位。
        ``oper`` 每次点菜单都会执行，在里面无条件 ``reload()`` 就是「点一次菜单扫一遍命令表」
        —— 没必要（页面内容在启动后基本定型），也让点击变慢。
        """
        if widget is None:
            return
        if not widget.items:
            widget.reload(target or None)
        elif target:
            widget.select_name(target)

    _gui.get_widget(
        the_type=ApiDocView,
        caption=_TITLE,
        on_top=True,
        icon='info',
        oper=oper,
        tooltip='gui 命令的图形化说明：左侧按用途分组、中间可搜索、右侧是签名 / 参数 / '
                '返回值 / 说明 / 用例。双击一行可把 gui.名字( 复制到剪贴板',
    )


@execute_once(file=__file__)
def setup_ui():
    """注册命令与菜单项（由 ``plugins.load_all`` 执行本文件时触发）."""
    from zmlx.ui.gui_buffer import gui as _gui

    # ⚠️⚠️ **命令表里必须指向 ``_open``（真正开标签页的那个），不能指向 ``show_api_doc``**：
    #    ``show_api_doc`` 的全部工作就是 ``gui.command('show_api_doc', ...)`` —— 若把**它自己**
    #    注册成命令，那次派发就会重新执行它，于是无限自递归（实测报
    #    ``maximum recursion depth exceeded``，菜单点了没反应）。
    #    ``architecture.py`` 的 ``_gui.add_func('show_architecture', _open)`` 是同一个道理。
    # ⚠️ 名字一旦发布不能改：标签页状态里存的就是 ``gui.show_api_doc()`` 这串原文。
    _gui.add_func('show_api_doc', _open)

    # 菜单：「帮助 → GUI 接口」。⚠️ 菜单标题必须与 main.py 里逐字一致（'帮助'），
    # 否则 get_menu 会另建一个同名顶层菜单，界面上就会出现两个「帮助」。
    # ⚠️ ``slot`` 用 ``_open`` 而不是 ``show_api_doc``：点菜单时本来就在 GUI 线程，
    #    直接开页即可；再经 ``gui.command`` 派发一次纯属绕路（也是上面那个自递归的入口）。
    _gui.add_action(
        menu='帮助',
        name='api_doc',
        text='GUI 接口',
        icon='info',
        tooltip='gui 命令的图形化说明：列出所有 gui.xxx()，带签名、参数、返回值、'
                '说明与用例（支持搜索 / 按用途分组）',
        slot=_open,
        # ⚠️ 本页只读文档，**不需要**在仿真运行时禁用 —— 用户跑着算例时照样可以查接口。
        #    显式给 is_visible：Action.update_view 里 is_visible 缺省时**跟随**
        #    is_enabled，不写这一行，将来若加上 is_enabled 会变成「消失」而不是「置灰」。
        is_visible=lambda: True,
        overwrite=False,
    )


# ======================================================================
# 自测
# ======================================================================

def test_1():
    """直接运行本文件时的自测：``python zmlx/ui/plugins/builtin/api_doc.py``.

    ⚠️ 这里**不调** ``setup_ui()``（那样会把菜单挂进一个没有主窗口的进程里）；要验
    「菜单 / 命令」那一侧，按 ``plugins/AGENTS.md`` 的验收清单走：重启 GUI →
    「设置 → 插件」→ 该行「临时加载」，或直接看「帮助 → GUI 接口」。

    没有界面时，``gui.list_all()`` 返回 ``None``，:class:`_Docs` 会返回空清单 + 一条警告 ——
    这正好演示了「读不到命令表」那条降级路径。
    """
    import sys
    app = QtWidgets.QApplication(sys.argv)
    widget = ApiDocView()
    widget.setWindowTitle('GUI 接口 —— gui 命令说明')
    widget.resize(1200, 760)
    widget.show()
    widget.reload()
    sys.exit(app.exec())


# ⚠️ 插件的标准形式：**注册写在这个分支里**。
#    插件机制用 ``exec`` 执行本文件时，命名空间里的 ``__name__`` 被设成
#    ``'__zml_plugin__'``，于是这里成立 —— 只注册，不开窗口。
if __name__ == '__zml_plugin__':
    setup_ui()

# ⚠️ 两支用**两个独立的 if**，不要写成 if / else（见 `../AGENTS.md` §2 第 4 步）。
if __name__ == '__main__':
    test_1()
