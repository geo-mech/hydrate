"""「帮助 → 架构」：zmlx 代码库的图文入门文档.

一句话：**把 ``zmlx`` 这个代码库"是什么、由什么组成、各部分怎么配合、在界面哪里点开"
全部画出来、写清楚，并且每一条"值得点开"的文字都是链接。**

为什么需要它
------------

``帮助 → ReadMe`` 讲的是**怎么装、怎么登录、怎么反馈**；
[`zmlx/ReadMe.md`](zmlx://doc/zmlx/ReadMe.md) 讲的是**怎么建模**；
[`zmlx/demos/ReadMe.md`](zmlx://doc/zmlx/demos/ReadMe.md) 讲的是**怎么照着一个例子改**。

唯独缺一份"**这个代码库本身长什么样**"的入门材料：30 多个子包、110 个可运行的 demo、
六层架构、两百多个顶层 API —— 新读者不知道从哪看起；知道要看哪个包，也未必知道
**在界面里哪个入口能看见它**。

本模块补的就是这一格。

它是怎么实现的（读了这一段，就知道怎么改它）
--------------------------------------------

**一个文件、一个控件、一组页面。**

1. **页面**：每一节（总览、架构、API 速查……）都是 :class:`_Catalog` 里的一条记录
   （``key`` + 标题 + 一段 Markdown + 可选配图）。全部页面**一次性**渲染进同一个
   ``QTextBrowser``，页内链接写成 ``[文字](#key)``（= Markdown 的标题锚点）。
2. **回退**：页内跳转走 ``QTextBrowser`` 自己维护的**历史栈**，所以
   :meth:`_ArchitectureView.show_section` / 点链接 / 顶部按钮三者用的是**同一套**机制 ——
   不会出现"我自己记的栈和控件的历史对不上"。顶部「返回 / 前进」直接连
   ``backward()`` / ``forward()``，永远可以回到上一步。
3. **图**：六张配图全部用**原生 Qt**（``QPainter``）画：颜色只从 ``QPalette`` 取，
   换主题（暗色 / 用户自定义样式表）时会**自动重画**。不用 matplotlib —— 那会往输出目录
   写 PNG，而且慢（见 ``widgets/AGENTS.md`` 的「图表控件：简单图用原生 Qt」）。
   ⚠️ 它们是**文档内嵌图片**（``QTextCursor.insertImage`` 插进去的位图资源），
   不是浮在正文上的控件 —— 滚动、换行、选中全由 Qt 负责。``_Figure`` 只当**离屏渲染器**。
   2026-10-24 之前是悬浮 ``QWidget`` + 文档坐标，那套「两套坐标系」把图钉死在屏幕固定
   位置（不随滚动、压住正文、窗口一小就看不见），缺陷记录见 PLAN ``T-20261023-05``。
4. **链接**：正文里三种链接，点击统一交给 :meth:`_ArchitectureView._on_link`：

   ==========================  =========================================================
   写法                          点击之后
   ==========================  =========================================================
   ``[文字](#key)``             跳到本页的某一节（记进历史，可以「返回」）
   ``[文字](zmlx://gui/命令名)`` 执行 ``gui.<命令名>()`` —— **等价于点那个菜单项**
   ``[文字](zmlx://doc/路径)``   打开仓库里的文档（Markdown 视图）或源码（代码编辑器）
   ==========================  =========================================================

   例：``[「帮助 → 示例」](zmlx://gui/show_demo)`` 就是"点它 = 点菜单「帮助 → 示例」"；
   ``[`zmlx/tfc/`](zmlx://doc/zmlx/tfc/)`` 就是"点它 = 打开 tfc 包的文档"。

挂出来的入口
------------

==========================  =====================================================
入口                          调用
==========================  =====================================================
菜单「帮助 → 架构」             :func:`show_architecture`
GUI 命令                      ``gui.show_architecture()``
直达某一节                     ``gui.show_architecture('data_model')``
==========================  =====================================================

⚠️ **``gui.show_architecture`` 这个名字一旦发布就不能改**：标签页被存进标签状态后，
重启时会按 ``gui.show_architecture()`` 这串原文重放（``gui_restore``）。要改就得照
``extra_setups/license_query.py`` 末尾那样留旧名别名。

⚠️ 名字**不与** ``MainWindow`` 的任何公开方法撞车 —— ``__init_gui_api`` 会把主窗口的
公开方法**自动注册**进命令表，撞名会把那个方法悄悄顶掉。

为什么整个功能都在这一个文件里
------------------------------

按用户要求：**新增这一个文件 + 在 ``extra_setups/__init__.py`` 挂一行**，
其余现有文件**一律不动**。于是：

- 控件是**顶层**的（只被 ``extra_setups`` 打开成一个标签页、不被任何控件复用），
  按 ``tabs/AGENTS.md`` 的判据它本该归 ``tabs/``；"只新增这一个文件"这条要求更具体，
  所以放在 ``extra_setups/`` 里。它仍然遵守 ``widgets/AGENTS.md`` 的全部规范。
- 它**不进**任何 ``__init__.py`` 的转发（``ui/AGENTS.md`` §1）—— 要用就按子模块路径导入。
- ``extra_setups/__init__.py`` 里那一段用 **``getattr`` 类型探测**挂载：模块不在
  （老版本、被删掉、导入失败）时那一行是**空操作**，不会带崩整个 ``setup_ui``。

内容怎么更新
------------

全部内容都在 :class:`_Catalog` 里。代码库结构变了，**只改 ``_Catalog``** 即可，
渲染 / 导航 / 配图都不用碰。核对办法：

- 本页现在共 :data:`_Catalog.PAGE_KEYS` 那么多个页面；
- 每条 ``zmlx://gui/<命令>`` 都必须真的在命令表里（改之前先在控制台
  ``print(gui.get().get_func('<命令>'))`` 确认）；
- 每条 ``zmlx://doc/<路径>`` 都必须真的存在（正文里的路径都相对**仓库根目录**）。

打开时为什么先显示骨架（2026-10-24）
-------------------------------------

整篇渲染实测约 **322 ms**（``markdown``→HTML 90 + ``setHtml`` 39 + 6 张配图
``QPainter`` 渲染 89），全塞进构造里就是「点菜单后界面卡一下」。所以改成两步：

1. :meth:`_ArchitectureView._load_skeleton` —— 目录 + 一句「正在排版……」，约 27 ms；
2. ``QTimer.singleShot(_RENDER_DELAY_MS, _load)`` —— 隔一小段再做整篇排版。

⚠️ **延迟必须是 50 ms，不能是 0**（2026-10-24 实测）：``singleShot(0, ...)`` 在事件
循环**一开头**就触发，骨架那帧还没画就被整篇排版（约 300 ms）占掉 ⇒ 用户看到的仍然
是全文。实测首帧内容：0 ms 时为「全文」，50 ms 起才是「骨架」。详见
``_ArchitectureView._RENDER_DELAY_MS`` 的对照表。

⚠️ **没有引入线程**：那 90 ms 的 markdown→HTML 是唯一能挪到后台的纯 Python 部分，
其余 ``setHtml`` / 配图全是 Qt 绘制、本来就只能在 GUI 线程做。实测后台最多只能移走
1/3，却要额外背一套线程生命周期与关标签收尾 —— 不划算。

⚠️ 两个必须记住的配套点（都是实测踩出来的）：

- **骨架里不放 ``@@figure:`` 占位**：占位一出现，:meth:`_on_contents_changed` 就会
  把它当成「图片丢了」去补救；
- **排版前请求的跳转要补做**：``gui.show_architecture('pitfalls')`` 是在骨架阶段调到
  :meth:`show_section` 的，那次跳转作用在马上要被替换掉的骨架上 ⇒ 由 ``_pending_section``
  记下、:meth:`_load` 结束时补跳（否则静默丢失，实测滚动值停在 0）。

Created by DeepSeek, 2026-10-18
"""

import os

from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets
from zmlx.ui.widgets.md_view import MarkdownView


class _Catalog:
    """全部页面内容（**改内容只改这里**）.

    模块级只留 import / 类定义 / ``test_1()`` / ``if __name__``，所以常量与内容统一收进
    这个私有类当命名空间（写法见 ``widgets/AGENTS.md`` §2「模块级内容」）。

    一条页面 = :meth:`entry` 返回的 dict：

    - ``key``：锚点名。既用于 ``[文字](#key)`` 页内跳转，也是
      ``gui.show_architecture(key)`` 的参数，还显示在顶部「ID」里；
    - ``title``：标题（同时是左侧目录的文字，**必须与正文里的 ``## 标题`` 逐字一致**）；
    - ``figure``：可选，``(图键, 图标题, 设计宽, 设计高)``；图键对应 :class:`_Figure`
      里的一支画法。
      ⚠️ **这两个数只用来算宽高比**，实际显示高度按当前列宽等比换算
      （见 :meth:`_ArchitectureView._figure_height`）。所以填的值必须反映**画布内容的
      真实形状** —— 画布是 **1000×1000 正方形**，所以这里填**近似 1:1**
      （统一写 ``900×900``）；写成宽扁的会在 ``paintEvent`` 的 ``min(w,h)/1000``
      里被按高度缩小、两侧留白。
      2026-10-24 之前这里写的是 ``860×330`` 这类宽扁数字，把图压成 1/3、字全糊在一起
      （PLAN ``T-20261023-05``）。
    - ``body``：Markdown 正文。可用 ``{repo}`` / ``{zmlx}`` 两个占位符（见 :meth:`text`）。
    """

    # ------------------------------------------------------------------
    # 常量
    # ------------------------------------------------------------------
    TITLE = '架构'

    #: 仓库根目录（= ``zmlx/`` 的上一级）。正文里 ``zmlx://doc/...`` 的路径都相对它。
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))

    #: 正文里的链接前缀
    GUI_SCHEME = 'zmlx://gui/'
    DOC_SCHEME = 'zmlx://doc/'

    #: 全部页面的 ``key``，顺序即目录顺序
    PAGE_KEYS = [
        'overview', 'map', 'layers', 'packages', 'cpp', 'data_model',
        'physics', 'demos', 'data_flow', 'boundary', 'api',
        'gui', 'gui_map', 'gui_cmds',
        'reading', 'run', 'extending', 'pitfalls', 'troubleshooting',
        'docs', 'glossary',
    ]

    # ------------------------------------------------------------------
    # 正文里的占位符
    # ------------------------------------------------------------------
    @classmethod
    def text(cls, body):
        """把正文里的 ``{repo}`` / ``{zmlx}`` 换成**本机的绝对路径**.

        换完的路径可以直接复制去 ``gui.open_code(...)``（正文里出现的那些行就是给人抄的）。
        不替换 ``{{`` / ``}}``：正文里的花括号一律按字面处理，不需要转义。
        """
        if not isinstance(body, str):
            return ''
        return (body.replace('{repo}', cls.ROOT)
                    .replace('{zmlx}', os.path.join(cls.ROOT, 'zmlx')))

    # ------------------------------------------------------------------
    # 页面
    # ------------------------------------------------------------------
    @classmethod
    def entry(cls, key, title, body, figure=None):
        return dict(key=key, title=title, body=body, figure=figure)

    @classmethod
    def entries(cls):
        """返回全部页面（**顺序即目录顺序**）."""
        return _PAGES


#: 页面数据（与 :class:`_Catalog` 分开放，免得那个类被上万行字符串淹没）
#:
#: ⚠️ 每条 ``title`` 必须与正文里的 ``## 标题`` **逐字一致** —— 左侧目录、当前位置、
#: ``scrollToAnchor`` 都按标题文字认页面。
_PAGES = []


def _build_pages():
    """构造全部页面（只在模块导入时跑一次；放在函数里是为了让上面的常量先就位）."""
    E = _Catalog.entry
    return [
        E('overview', '总览', '''\
**IGG-Hydrate**（Python 包名 `zmlx`，`import zmlx`）是**储层多场耦合数值模拟**模块：把
**热（Thermal）- 流（Hydraulic）- 力（Mechanical）- 化（Chemical）**四类过程放进同一套
时间推进里求解。主要面向三类问题：天然气水合物（可燃冰）的成藏与开发、页岩油原位转化
（ICP）、CO₂ 地质封存，以及其它储层内的流动 / 传热 / 化学 / 变形问题。

### 它长什么样

一个 **「Python 前台 + C++ 内核」** 的代码库：

- **C++ 内核**（仓库根的 `zml/`，header-only，C++17）负责真正吃 CPU 的数值计算，编译成
  `zml.dll`（Windows）/ `zml.so`（Linux），随包放在 `zmlx/exts/` 里；
- **Python 层**（`zmlx/`，30 多个子包）负责建模、物性、耦合策略、绘图与图形界面；
- 两者之间只有**一层薄薄的 ctypes 绑定**（[`zmlx/exts/`](zmlx://doc/zmlx/exts/)）——
  一个 C++ 导出对应一个 Python 函数，业务逻辑不长在那里；
- 内核源码**不在本仓修改**（由作者单独维护）。

### 三句话记住它

1. **数据只有一个中心**：所有物理过程都围绕一个 `Seepage` 对象转 —— 它装着网格单元
   （`cell`）、连接面（`face`）、流体（`fluid`）和化学反应（`reaction`）。
   见 [核心数据模型](#data_model)。
2. **分层是硬约束**：上层可以调用下层，**下层绝不 import 上层**。看懂
   [五层架构](#layers) 那张图，就懂了一半的代码结构。
3. **每个功能都有两个入口**：界面上点菜单，或代码里调 `gui.xxx()` —— **两者完全等价**。
   见 [界面地图](#gui_map)。

### 想直接开始

| 你的目的 | 从这里走 |
|---|---|
| 先跑起来看看 | [「帮助 → 示例」](zmlx://gui/show_demo) —— 110 个可以直接运行的算例 |
| 想知道代码怎么组织 | [全图导航](#map) → [五层架构](#layers) → [子包索引](#packages) |
| 要写自己的算例 | [示例集导读](#demos) → [一次求解](#data_flow) → [边界条件与井](#boundary) |
| 要查某个函数 | [API 速查](#api) —— 按包列出签名与一句话说明 |
| 想知道某个类有哪些字段 | [核心数据模型](#data_model) |
| 想改代码 / 加功能 | [如何阅读源码](#reading) → [扩展点](#extending) → [常见陷阱](#pitfalls) |
| 报错了 | [报错排查](#troubleshooting) |
| 想查个词 | [术语表](#glossary) |

> 本页所有**蓝色的字都可以点**：「帮助 → 示例」这类是**菜单项**（点它 = 真的去点那个菜单），
> `zmlx/tfc/` 这类是**代码或文档**，`#锚点` 这类是**本页内的小节**。
> 顶部有「返回 / 前进 / 回到开头」，点了哪里都能退回来看。
''', ('overview', '从「一个算例」到「屏幕上的图」：五步与对应的代码', 900, 900)),

        E('map', '全图导航：这个代码库的骨架', '''\
下面这张"骨架图"是本页全部内容的入口：左列是你会问的问题，右列是回答它的小节。

### 按"我想干什么"找

| 我想…… | 去这一节 | 一句话 |
|---|---|---|
| 知道**整体怎么分层** | [五层架构](#layers) | 六层，上层调用下层 |
| 知道**每个包是干什么的** | [子包索引](#packages) | 30+ 个子包的定位与核心对象 |
| 知道 **C++ 与 Python 怎么接** | [C++ 内核与绑定](#cpp) | 薄封装、指针共享、不改内核 |
| 知道**核心类有哪些字段** | [核心数据模型](#data_model) | `Seepage` / `Cell` / `Face` / `FluDef` … |
| 知道**物理模型怎么实现的** | [物理模型](#physics) | 水合物、干酪根、相渗、毛管力…… |
| **查一个函数**的签名 | [API 速查](#api) | 按包列出 |
| **找一个能跑的算例** | [示例集导读](#demos) | 13 个主题目录、110 个 demo |
| 知道**一次求解做了什么** | [一次求解](#data_flow) | `iterate` 内部的子过程顺序 |
| 知道**边界条件 / 井怎么设** | [边界条件与井](#boundary) | 定压、恒温、注入、生产 |
| 知道**界面里有什么** | [图形界面](#gui) → [界面地图](#gui_map) | 菜单、工具栏、状态栏、控件 |
| **查一条命令** | [命令与控制台](#gui_cmds) | `gui.xxx()` 速查 |
| **读源码**从哪开始 | [如何阅读源码](#reading) | 三条路线 |
| **跑起来**（含无头、批量测试） | [运行与测试](#run) | `--no-gui`、`test_all_demos` |
| **加一个新功能** | [扩展点](#extending) | 按"加什么"查表 |
| 躲开**已知的坑** | [常见陷阱](#pitfalls) | 10+ 条 |
| **报错了**怎么办 | [报错排查](#troubleshooting) | 现象 → 原因 → 办法 |
| 查**文档在哪** | [文档地图](#docs) | 十几份文档的分工 |
| 查一个**术语** | [术语表](#glossary) | THMC、cfl、gui_restore…… |

### 两条主线

**结构主线**（数据怎么组织）：

```
zml/  C++ 内核 ──绑定──▶ zmlx/exts/  Seepage · Cell · Face · FluDef · Reaction
                              │
                              ▼
                    zmlx/tfc/   iterate：流动 → 传热 → 反应 → 定步长
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        zmlx/fluids/    zmlx/reactions/   zmlx/krs/
                 zmlx/scen/   场景：hydrate / icp
                              │
                              ▼
             zmlx/plt/ · zmlx/fig/ · zmlx/ui/   看得见
```

**使用主线**（你要写什么）：

```
写算例  ─▶  造模型  ─▶  推进时间  ─▶  取出数据  ─▶  画图 / 保存
zmlx/demos   create()   iterate()     tfc.get_p()   plot_on_figure()
             zmlx/tfc    zmlx/tfc       zmlx/tfc       zmlx/plt
```

### 建议的阅读顺序

- **第一次来**：总览 → 五层架构 → 子包索引 → 一次求解 → 界面地图（约 15 分钟）；
- **要建模**：示例集导读 → 一次求解 → 边界条件与井 → API 速查；
- **要改代码**：如何阅读源码 → 扩展点 → 常见陷阱 → 文档地图。
'''),

        E('layers', '五层架构', '''\
代码自上而下分层。**上层可以调用下层，下层绝不 import 上层** —— 这条纪律是读懂目录结构的
关键：看到 [`zmlx/scen/`](zmlx://doc/zmlx/scen/) 里的代码可以随便调 `tfc`、`fluids`，
而 [`zmlx/exts/`](zmlx://doc/zmlx/exts/) 里出现 `from zmlx.scen import ...` 就一定是错的。

### 六层

| 层 | 目录 | 一句话职责 | 典型入口 |
|---|---|---|---|
| **L5 应用场景** | [`zmlx/scen/`](zmlx://doc/zmlx/scen/) | 把一类完整工程问题（水合物、ICP……）打包成"建好就能算"的场景 | `hydrate.create()` / `hydrate.solve()` |
| **L4 耦合引擎** | [`zmlx/tfc/`](zmlx://doc/zmlx/tfc/) | 时间推进，以及各物理过程之间的耦合顺序 | `tfc.seepage.iterate()` / `tfc.solve()` |
| **L3 工具与界面** | [`zmlx/ui/`](zmlx://doc/zmlx/ui/) [`zmlx/utils/`](zmlx://doc/zmlx/utils/) [`zmlx/plt/`](zmlx://doc/zmlx/plt/) [`zmlx/fig/`](zmlx://doc/zmlx/fig/) | 图形界面、高层工具（场、迭代器、存档）、绘图 | `gui.execute()` / `Field` / `plot_on_figure()` |
| **L2 物理定义** | [`zmlx/fluids/`](zmlx://doc/zmlx/fluids/) [`zmlx/reactions/`](zmlx://doc/zmlx/reactions/) [`zmlx/krs/`](zmlx://doc/zmlx/krs/) | 流体物性、化学反应速率、相对渗透率 | `create_ch4()` / `create_reaction()` / `create_kr()` |
| **L1 Python 绑定** | [`zmlx/exts/`](zmlx://doc/zmlx/exts/) | 一层薄薄的 ctypes 绑定，**一个导出一个函数** | `Seepage` / `Cell` / `Face` / `FluDef` |
| **L0 C++ 内核** | `zml/`（仓库根） | 真正的数值内核（header-only，C++17） | 编译好的 `zml.dll` / `zml.so` |

### 横贯各层的支撑包

这几个包不占"层"的位置，但被各层普遍使用：

| 包 | 定位 | 关键点 |
|---|---|---|
| [`zmlx/system/`](zmlx://doc/zmlx/system/) | **最底层的基础服务** | `app_data`（全局配置）、`is_headless`（无头模式）、`execute_once`、`log` / `warn`。**不依赖 zmlx 里任何其它东西** |
| [`zmlx/geometries/`](zmlx://doc/zmlx/geometries/) | 几何计算 | 点、线段、三角形、3D 矩形、DFN |
| [`zmlx/meshes/`](zmlx://doc/zmlx/meshes/) [`zmlx/seepage_meshes/`](zmlx://doc/zmlx/seepage_meshes/) | 网格生成与变换 | `Mesh3`（几何网格）与 `SeepageMesh`（渗流网格）是**两种不同的网格** |
| [`zmlx/io/`](zmlx://doc/zmlx/io/) | 输入输出 | 文本 / JSON / .py 格式 / 坐标数据 |
| [`zmlx/algs/`](zmlx://doc/zmlx/algs/) | 通用算法（与业务无关） | `linspace`、`join_paths`、`is_sorted`、多进程、文件系统 |
| [`zmlx/fem/`](zmlx://doc/zmlx/fem/) | 有限元（开发中） | 基于 `Mesh3` + `DynSys` |

### 几条"不成文但很重要"的规矩

- **新东西一般先落 [`zmlx/utils/`](zmlx://doc/zmlx/utils/)**（无 Qt 依赖的高层工具），
  再把界面接到 [`zmlx/ui/`](zmlx://doc/zmlx/ui/)；
- **`zmlx/exts/` 不给它加依赖**：它只做"把 Python 调用转给 DLL"，业务逻辑不许长在这里；
- **`zmlx/config/` 与 `zmlx/base/` 已弃用**：看到它们出现在新代码里就是写错了；
- **旧名兼容包**（`zmlx/alg/` `zmlx/fluid/` `zmlx/react/` `zmlx/kr/` `zmlx/mesh/`
  `zmlx/geometry/` `zmlx/utility/` `zmlx/seepage_mesh/` `zmlx/demo/`）导入会发
  `DeprecationWarning`，**2027-10-16 删除** —— 新代码用复数名。
''', ('layers', '六层架构：越往上越接近「应用」，越往下越接近「机器」', 900, 900)),

        E('packages', '子包索引', '''\
`zmlx/` 下一共有 **30 多个**子包。下表按用途分组，**点包名**可以打开该目录的文档
（`ReadMe.md` / `AGENTS.md`），没有文档的包里打开 `__init__.py`。

### 核心六个

| 包 | 定位 | 核心对象 | 什么时候来看它 |
|---|---|---|---|
| [`zmlx/system/`](zmlx://doc/zmlx/system/) | 基础服务，**无内部依赖** | `app_data`、`is_headless`、`execute_once`、`log`、`warn` | 读全局配置、判断无头模式 |
| [`zmlx/exts/`](zmlx://doc/zmlx/exts/) | C++ 绑定层 | `Seepage`、`Cell`、`Face`、`FluDef`、`Fluid`、`Reaction`、`Vector`、`Tensor3` | 想知道模型对象有哪些字段 |
| [`zmlx/tfc/`](zmlx://doc/zmlx/tfc/) | 耦合引擎 | `seepage.iterate()`、`tfc.create()`、`tfc.solve()` | 想看时间步怎么推进 |
| [`zmlx/fluids/`](zmlx://doc/zmlx/fluids/) | 流体物性 | `create_ch4`、`create_h2o`、`create_aqueous`、`create_mixture` | 要定义新组分 / 相态 |
| [`zmlx/reactions/`](zmlx://doc/zmlx/reactions/) | 化学反应速率 | `create_reaction`、`add_reaction`、`create_inh`、`add_inh` | 要做相变 / 裂解 / 自定义反应 |
| [`zmlx/krs/`](zmlx://doc/zmlx/krs/) | 相对渗透率 | `create_kr`、`create_krf`、`create_fracture_kr` | 要改相渗曲线 |

### 应用场景

| 包 | 定位 | 核心对象 |
|---|---|---|
| [`zmlx/scen/`](zmlx://doc/zmlx/scen/) | **应用场景（最大的子包）** | `hydrate.create/solve`、`icp.create`、`frac`、`geothermal_helium`、`mineralization_reactor`、`quick_look`、`uv_equilibrium`、`editors` |

### 几何与网格

| 包 | 定位 | 核心对象 |
|---|---|---|
| [`zmlx/geometries/`](zmlx://doc/zmlx/geometries/) | 几何计算 | `get_distance`、`get_angle`、`seg_intersection`、`dfn2`、`dfn_v3` |
| [`zmlx/meshes/`](zmlx://doc/zmlx/meshes/) | **几何网格 `Mesh3`** | `layered_triangles`、`get_triangles`、`create_cube_mesh`、`create_ring` |
| [`zmlx/seepage_meshes/`](zmlx://doc/zmlx/seepage_meshes/) | **渗流网格 `SeepageMesh`**（给 Seepage 用） | `create_cube`、`create_xz`、`create_xyz`、`create_cylinder`、`add_cell_face`、`create_wellbore` |

> ⚠️ **`meshes` 与 `seepage_meshes` 是两种不同的东西**：前者是通用几何三角网格
> （节点 / 连线 / 面 / 体），后者是渗流计算用的 cell-face 网格。建模时你需要的是
> **`seepage_meshes`**。

### 工具

| 包 | 定位 | 核心对象 |
|---|---|---|
| [`zmlx/utils/`](zmlx://doc/zmlx/utils/) | 高层工具 | `Field`、`GuiIterator`、`SaveManager`、`AttrKeys`、`PressureController`、`SeepageCellMonitor`、`CapillaryEffect`、`Interp2/3` |
| [`zmlx/algs/`](zmlx://doc/zmlx/algs/) | 通用算法（无业务含义） | `linspace`、`clamp`、`time2str`、`join_paths`、`apply_async`、`list_files` |
| [`zmlx/io/`](zmlx://doc/zmlx/io/) | 输入输出 | `opath`、`json_ex`、`read_py`、`load_txt`、`TaskFolder` |
| [`zmlx/filesys/`](zmlx://doc/zmlx/filesys/) | 文件系统（**已弃用**，迁到 `algs.fsys`） | 转发层 |
| [`zmlx/fem/`](zmlx://doc/zmlx/fem/) | 有限元（开发中） | 刚度矩阵、`DynSys` |

### 可视化与界面

| 包 | 定位 | 核心对象 |
|---|---|---|
| [`zmlx/plt/`](zmlx://doc/zmlx/plt/) | matplotlib 可视化（三层：on_axes → on_figure → on_ui） | `plot_on_figure`、`add_contourf`、`show_field2` |
| [`zmlx/fig/`](zmlx://doc/zmlx/fig/) | 声明式 Figure 构建 | `fig.axes2`、`fig.contourf`、`fig.show` |
| [`zmlx/ui/`](zmlx://doc/zmlx/ui/) | PyQt6 图形界面 | `gui`（全局单例）、`MainWindow`、各标签页控件 |

### 数据、脚本与示例

| 包 | 定位 |
|---|---|
| [`zmlx/data/`](zmlx://doc/zmlx/data/) | 随包发布的文档（`README.md` / `CHANGELOG.md` / `ROADMAP.md`）与示例数据（`mesh_c10000`、`igg.png` 等） |
| [`zmlx/scripts/`](zmlx://doc/zmlx/scripts/) | 一次性小脚本：`install_dep.py`、`create_ui_lnk_on_desktop.py`、`write_pip_config.py` |
| [`zmlx/demos/`](zmlx://doc/zmlx/demos/) | **110 个可运行算例** —— 最该先看的地方，见 [示例集导读](#demos) |

### 已被改名 / 弃用的包

2026-10-16 有一批包改成了**复数**名（判据是"这个包是装东西的容器"）。旧名保留为兼容垫片，
导入即发 `DeprecationWarning`，**2027-10-16 删除**：

| 旧名 | 新名 |
|---|---|
| `zmlx.alg` | `zmlx.algs` |
| `zmlx.fluid` | `zmlx.fluids` |
| `zmlx.react` | `zmlx.reactions` |
| `zmlx.kr` | `zmlx.krs` |
| `zmlx.mesh` | `zmlx.meshes` |
| `zmlx.geometry` | `zmlx.geometries` |
| `zmlx.utility` | `zmlx.utils` |
| `zmlx.seepage_mesh` | `zmlx.seepage_meshes` |
| `zmlx.demo` | `zmlx.demos` |

另外 `zmlx/config/` 与 `zmlx/base/` 是更早就弃用的包，`zmlx/ui/widget/`（单数）则是
`zmlx.ui.widgets` + `zmlx.ui.tabs` 的兼容垫片。
'''),

        E('cpp', 'C++ 内核与 Python 绑定', '''\
仓库根的 `zml/` 是**真正的计算内核**：C++17 header-only，编译成 `zml.dll`（Windows）与
`zml.so`（Linux），放在 [`zmlx/exts/`](zmlx://doc/zmlx/exts/) 里随包发布。
[`zmlx/exts/`](zmlx://doc/zmlx/exts/) 里的 Python 代码通过 **ctypes** 调用它 —— 所以这里
**不是** pybind11 之类的自动绑定，而是**手写的薄封装**。

### 为什么是"薄封装"

一条纪律：

> **`zmlx/exts/` 里一个导出对应一个函数，不在这里写业务逻辑，也不给它加依赖。**

两个好处：**好对**（C++ 改了签名，Python 只有一处要对）、**好换**（将来换绑定方式，
业务代码一行不用动）。所以你在 `zmlx/exts/` 里看到的几乎都是
`core.use(...)` + 一行 `return core.xxx(...)`，**真正的算法不在这里**。

### 跨语言的数据怎么传

核心对象（`Seepage` / `Cell` / `Face` / `FluDef`）在 C++ 里**连续存放**，Python 侧用
**numpy 数组直接看那块内存**（基于指针，不拷贝）：

- 读一个 `cell` 的属性是"读一个 float"，不是"发一次请求"；
- 在 Python 里算完（比如空间分布函数）可以**原地写回**，没有来回搬运的开销。

这就是"基于指针处理各模块之间的数据交换"的实际含义，也是
`tfc.get_p(model, shape=(nx, nz))` 这类函数能一次性返回整个数组的原因
（见 [`zmlx/tfc/_base.py`](zmlx://doc/zmlx/tfc/_base.py) 的 `get_ca` / `set_fa` / `as_numpy`）。

### `zmlx/exts/` 里都有什么

| 模块 | 内容 |
|---|---|
| `_seepage.py` | **核心**：`Seepage`、`Cell`、`Face`、`FluDef`、`FluData`、`Reaction`、`Injector`、`FlowSol`、`ThermalSol`、`calc_recommended_dt` |
| `_mesh.py` | `Mesh3`（几何网格）、`SeepageMesh`、`Groups`、`ElementMap` |
| `_dyn.py` | `DynSys`：弹簧-质点-阻尼器动力学系统（固体变形 / 应力波） |
| `_frac.py` | `Dfn2`、`Lattice3`、`FractureNetwork`、`DDMSolution2`（2D 位移间断法） |
| `_ip.py` | `InvasionPercolation`：孔隙尺度多相驱替 |
| `_vec.py` `_ary.py` `_tensor.py` `_mat.py` | `Vector`、`Array2/3`、`Tensor2/3`、`Matrix2/3` |
| `_interp.py` `_coord.py` `_map.py` | `Interp1/2/3`、`Coord2/3`、`Map` |
| `_sol.py` | 线性求解器：`ConjugateGradientSolver`、`SparseLUSolver`、`BiCGSTABSolver`、`ICCGSolver` 等（Eigen 后端） |
| `_pool.py` `_timer.py` `_fmap.py` | `ThreadPool`、`Timer` / `clock`、`FileMap` |
| `_lic.py` | `lic`（本机授权）与 `web_license`（在线登录） |

### 与内核有关的坑

- **必须是 64 位 Python**：与 `zml.dll` 位数不一致会加载失败；
- **Windows 建议装 VC 运行库**：[VC_redist.x64.exe](https://gitee.com/geomech/hydrate/attach_files)；
- **安装路径不能有中文**：`import zmlx` 时会检查并警告（`contain_chinese`）；
- **不要改 `zml/` 下的 C++ 文件**：那份由作者单独维护，改了会在下一次同步时被覆盖。

> 想知道当前内核的编译时间与编译器：控制台里跑
> `import zmlx.exts as zml; print(zml.about())`，或打开
> [「帮助 → 关于」](zmlx://gui/show_about)。
'''),

        E('data_model', '核心数据模型：Seepage 与它的零件', '''\
整个代码库只有一个中心数据结构：**`Seepage`**。它装着网格、流体、反应和迭代状态；
所有物理过程都绕着它转。搞清它的字段，后面的一切都好理解。

### 结构一览

```
Seepage  (多相多组分渗流模型)
├── cell[i]      : Cell     —— 网格单元（位置、体积、孔隙、压力、孔渗、导热…）
│   └── fluid[j] : FluData  —— 该单元里第 j 种流体（质量、体积、密度、粘度…）
├── face[i]      : Face     —— 两个 cell 之间的连接（导流系数 cond）
├── flu_def[i]   : FluDef   —— 流体"定义"（密度/粘度随 P、T 变化、比热、组分）
├── reaction[i]  : Reaction —— 化学反应（左右组分、平衡温度、反应热、速率）
├── injector[i]  : Injector —— 注入点（往某个 cell 注入流体或能量）
└── temps / tags / keys     —— 迭代状态（时间 time、步长 dt、步数 step、标签开关）
```

> ⚠️ **`FluDef` 与 `FluData` 不要混**：`FluDef` 是"这个流体是什么"（定义，模型级，
> 例如"甲烷"）；`FluData` 是"某个单元里这一份流体有多少"（实例，单元级，有质量和体积）。
> 一个模型有一份 `flu_def` 表，每个 cell 各自持有一组 `FluData`。

### Seepage —— 模型本体

**属性**

| 属性 | 含义 |
|---|---|
| `cell_number` / `face_number` | 单元数 / 面数 |
| `cells` / `faces` / `injectors` | 三个容器（可按索引取） |
| `gravity` | 重力加速度向量（如 `[0, 0, -10]`） |
| `fludef_number` / `reaction_number` / `kr_number` / `pc_number` | 各类子对象的数量 |
| `fluid_mass` / `fluid_vol` | 整体的流体质量 / 体积（汇总） |

**取元素**：`get_cell(i)`、`get_face(i)`、`get_fluid(fid)`（取 `FluDef`）、`get_injector(i)`、
`get_reaction(i)`、`get_kr(i)`、`find_fludef(name)`。

**增删**：`add_cell()`、`add_face(i0, i1)`、`add_injector(...)`、`add_fludef(flu)`、
`add_reaction(r)`、`set_kr(...)`、`remove_cell(i)`、`clear_cells_and_faces()`。

**状态与标签**：`get_text(key)` / `set_text(key, text=...)`（存任意文本或字典，例如
`model.set_text(key='solve', text={...})`）、`add_tag('check_dt')` / `has_tag(...)` / `del_tag(...)`。

**属性键**：模型的"动态属性"用整数键 —— `reg_cell_key(name)` 注册、`get_cell_key(name)`
取回。tfc 里大量使用，例如 `model.get_cell_key('temperature')`。

**推进**：`iterate(dt=None)`（推进一步）、`iterate_thermal(dt=None)`（只推温度）、
`get_recommended_dt(...)`、`update_den()` / `update_vis()` / `update_cond()`。

**保存与读写**：`save('xxx.seepage')` / `load('xxx.seepage')`；`cells_write` / `cells_read`、
`faces_write` / `faces_read`、`fluids_write` / `fluids_read`。

**批量取数据**：`get_cell_gradient`、`get_cell_average`、`get_face_average`、`get_face_diff`、
`get_face_sum`、`get_fluid_mass()`、`get_fluid_vol()`。

### Cell —— 网格单元

| 属性 | 单位 | 含义 |
|---|---|---|
| `pos` / `x` `y` `z` | m | 单元中心坐标（`pos` 可整体读写） |
| `v0` | m³ | 单元总体积 |
| `k` | — | 体积比例系数（`v0` 的有效部分，一般 1.0） |
| `pre` | Pa | 孔隙压力 |
| `fluid_number` | — | 该单元里有多少种流体 |
| `fluid_vol` / `fluid_mass` | m³ / kg | 汇总的流体体积 / 质量 |

**孔隙与压力**：`set_pore(p=..., v=..., dp=..., dv=...)`（给定当前压力和孔隙体积，以及
一对参考点）、`v2p(v)`（体积 → 压力）、`p2v(p)`（压力 → 体积）。
⚠️ **孔隙度不是 Cell 的直接字段**，而是通过 `set_pore` 换算进来的。

**属性（含用户自定义的）**：`get_attr(key)` / `set_attr(key, value)`。
tfc 里常用的键：

| 键 | 单位 | 含义 |
|---|---|---|
| `porosity` | — | 孔隙度 |
| `perm` | m² | 渗透率 |
| `heat_cond` | W/(m·K) | 导热系数 |
| `denc` | J/(m³·K) | 密度 × 比热 |
| `pore_modulus` | Pa | 孔隙模量 |
| `temperature` | K | 温度 |

**流体**：`get_fluid(i)` 取第 i 个 `FluData`、`get_component(...)`、
`get_fluid_vol_fraction(fid)`。

### Face —— 单元之间的连接

| 属性 | 单位 | 含义 |
|---|---|---|
| `cond` | — | **导流系数**：流动的传导能力 |
| `dr` | m⁻¹ | 距离相关的系数 |

**底层建模必须自己算对这一行**：

```
face.cond = area * perm / dist
```

其中 `area` 是横截面积（m²）、`perm` 是渗透率（m²）、`dist` 是流动距离（m）。
高层 `tfc.create()` 会替你算好。

方法：`get_cell(i)`（取两端的 cell）、`distance()`、`get_another(cell)`、
`get_attr` / `set_attr`、`get_dv()`、`get_ikr()` / `set_ikr()`。

### FluDef —— 流体定义

| 属性 | 单位 | 含义 |
|---|---|---|
| `den` | kg/m³ | 密度（可以是 P、T 的函数） |
| `vis` | Pa·s | 粘度 |
| `specific_heat` | J/(kg·K) | 比热 |
| `component_number` / `components` | — | 组分（混合物才有） |
| `name` | — | 名字（**饱和度字典里用的就是这个名字**） |

方法：`get_den(p, t)` / `get_vis(p, t)`、`add_component(...)`、`create(...)`、
`clone()` / `get_copy()`。

**怎么造一个 `FluDef`**：用 [`zmlx/fluids/`](zmlx://doc/zmlx/fluids/) 里的工厂函数 ——
`create_h2o()`、`create_ch4()`、`create_co2()`、`create_ch4_hydrate()`、`create_h2o_ice()`、
`create_aqueous()`、`create_mixture()`，或 `from_file()` 读表格。

### FluData —— 单元里的流体实例

| 属性 | 单位 | 含义 |
|---|---|---|
| `mass` | kg | 质量 |
| `vol` | m³ | 体积 |
| `den` | kg/m³ | 当前密度 |
| `vis` | Pa·s | 当前粘度 |
| `is_solid` | — | 是否固相 |

方法：`get_attr` / `set_attr`、`add(...)`、`get_component(i)`、`set_components(...)`、
`set_property(...)`、`clone()`。

### Reaction —— 化学反应

| 属性 | 含义 |
|---|---|
| `temp` / `heat` | 参考温度（K）/ 反应热（J/kg，正值为吸热） |
| `p2t` | 压力 → 平衡温度的插值函数（水合物等用它判断"该不该反应"） |
| `t2q` | 温度 → 反应进度的插值函数（控制反应速率） |
| `component_n` / `components` | 参与反应的组分（左侧为负、右侧为正的权重） |
| `inhibitor_n` / `inhibitors` | 抑制剂（盐、醇等对平衡温度与速率的影响） |
| `rate` | 反应速率系数 |

方法：`add_component(...)`、`add_inhibitor(...)`、`react(...)`、`get_rate(...)`、
`set_p2t(...)` / `set_t2q(...)`、`clone()`。

**怎么造一个 `Reaction`**：见 [物理模型](#physics) 的「相变与反应」一节 —— 参数通常写成一个
dict，交给 `add_reaction(model, data)`。

### 其它零件

| 类 | 作用 |
|---|---|
| `Injector` | 注入点：`cell_id`（注入到哪个 cell）、`flu`（注入的 `FluDef`）、`value`（速率 kg/s 或功率 W）、`time`、`radi`、`g_heat`（加热量） |
| `FlowSol` / `ThermalSol` | 流动 / 传热求解器的句柄：`iterate()`、`get_sol()`、`get_report()` |
| `Thermal` | **独立的纯热传导模型**（只有 cell / face 与温度，没有流动） |
| `calc_recommended_dt(...)` | 按 CFL 条件算推荐步长 |

> 完整的字段与方法清单（`Seepage` 就有 127 个方法）可以直接看源码：
> [`zmlx/exts/_seepage.py`](zmlx://doc/zmlx/exts/_seepage.py)。
'''),

        E('physics', '物理模型：原理与代码位置', '''\
本页回答"**这个库到底算了什么物理，那些公式在代码哪里**"。

⚠️ 先说一个容易误解的结构：**方程本身的装配与求解在 C++ 内核里**，Python 层提供的是
**参数、相平衡曲线、反应热、相对渗透率 / 毛管力曲线**。所以每一节都会分成两栏：
"方程在哪"与"参数在哪"。

### 多相多组分渗流（流动）

储层被离散成**控制体 Cell** 与**界面 Face**。每个 Face 上存一个**导流系数** `cond`，
它就是达西定律的有限体积离散：

```
cond = area * perm / length          （tfc.set_face 里算的）
流量 ∝ cond × ΔP                     （再按相对渗透率与粘度修正）
```

`Seepage.get_cond_for_exchange(fid0, fid1)` 负责"根据相对渗透率曲线、粘性系数，
计算相邻两个 Cell 交换流体时的导流系数"。求解是全隐式 / 牛顿迭代 + 线性求解器。

| | 位置 |
|---|---|
| 主入口 | `tfc.seepage.iterate_flow(...)`（`tfc/_base.py`） |
| 求解器 | `Seepage.get_flow_sol().iterate(...)` → C++ `seepage_fs_iterate` |
| 相渗修正 | `Seepage.get_cond_for_exchange(fid0, fid1)` |
| 导流更新 | `Seepage.update_cond(...)` / `update_g0(...)`，由 `tfc._cond.iterate` 每步调用 |

⚠️ **惯性**：要模拟流体的惯性（`flow_dy` 类算例），必须同时给定 `fa_s`（面积）、
`fa_q`（速率）、`fa_k`（惯性系数）**并且有初值**，否则惯性项不生效。

### 热传导、对流与固-流换热

热量走**两个通道**：

1. **Cell 之间经 Face 的导热**：`g_heat = area * heat_cond / length`，单位时间过 Face 的热量
   `dH = g * dT`；
2. **Cell 内流体与骨架的换热**：`g_heat = vol * heat_cond / dist²`，`dist` 是"土体和流体
   换热的距离"，越大换热越慢。

Cell 的热容存在 `mc = vol * denc`（`denc` = 土体密度 × 比热，例如 2000 kg/m³ × 1000 J/(kg·K)
= `2.0e6`）。**对流不需要额外方程** —— 流体本身带 `temperature` 与 `specific_heat`，
流动时自然携带热量。

| | 位置 |
|---|---|
| 主入口 | `tfc.seepage.iterate_thermal(...)` |
| 求解器 | `Seepage.get_thermal_sol().iterate(...)` → C++ `seepage_ts_iterate` |
| 固-流换热 | `Seepage.exchange_heat(...)` → C++ `seepage_exchange_heat` |
| 独立的纯传热模型 | `Thermal` 类（不依附 Seepage），可 `Thermal.exchange_heat(model, ...)` 与渗流耦合 |

⚠️ **各向异性导热会被取平均值**（`tfc/_main.py` 的 `set_model` 有一处 TODO），
建各向异性模型时要留意。

### 相变与反应：通用框架

**所有反应都由同一个底层工厂构造**：`reactions.endothermic.create(left, right, temp, heat,
rate, ...)`。反应物（`left`）转化为生成物（`right`）**吸热**，温度升高驱动反应。

反应速率的完整计算流程（见 `Seepage.Reaction` 的 docstring）：

```
1. T0 = p2t(当前压力)                    ← 由压力查"平衡温度"
2. T0 按抑制剂修正（盐度、固体占比…）      ← Inhibitor 的 c2t 曲线
3. dT = 当前温度 - T0
4. q  = t2q(dT)                          ← 正向速率
   qr = t2qr(dT)                         ← 逆向速率
5. Q = q - qr，再乘以抑制剂系数 c2q
6. Q *= irate                            ← 总体速率系数
```

⚠️ **这里不是 Kim-Bishnoi 动力学**，而是"**平衡温度 + 温度驱动的速率曲线**"：
`p2t` 给出该压力下的平衡温度，`t2q` 给出偏离平衡温度后的反应快慢。

### 水合物相变

| | 甲烷水合物 | CO₂ 水合物 |
|---|---|---|
| 定义 | `reactions/ch4_hydrate.py` | `reactions/co2_hydrate.py` |
| 平衡曲线 | `vt`/`vp` 共 **45 点**，取自 TOUGH+ Hydrate 手册（148.7 K/5.3 kPa → 320.2 K/447.9 MPa） | `vt`/`vp` 共 **22 点**，来自 Anderson (2003) 与 Zhou et al. (2008) |
| 水合数 `nh` | **6.0** | **5.75** |
| 质量比 `mg` | `16/(18×6+16)` = **0.129** | `44.01/(18.015×5.75+44.01)` ≈ 0.298 |
| 分解热 `heat` | **4.37×10⁵ J/kg** | **4.065×10⁵ J/kg**（每 mol 约 60 kJ） |
| 固体物性 | `den=919.7`、`vis=1e30`、`cp=2100` | `den=1112`、`vis=1e30`、`cp=2190` |

反应构造用 `reactions.hydrate.create(gas, liq, hyd, mg, vp, vt, temp, heat, ...)`：
`left = [(hyd, 1.0)]`、`right = [(gas, mg), (liq, 1-mg)]`。

**盐度的影响**：盐度**不进状态方程**，只作为**平衡温度的偏移** ——
`reactions/alpha/salinity.py` 给出一条 21 点表（盐度 0~0.2 → 平衡温度降 0~−11.68 K @ 15 MPa），
挂到反应的抑制剂上。

⚠️ **盐度一律指质量浓度**（盐的质量 / 溶液的质量），不是体积浓度 —— 这是 docstring 里
特别强调的一点。

**稳定性技巧**（`scen/hydrate/_react.py`）：给水合物反应加一个抑制剂，
"当固体占比超过 0.8 之后把平衡温度压到极低"，从而**禁止继续生成**、避免孔隙被完全堵死。
代码注释写着"抑制固体比例过高，增强计算稳定性（非常必要）"。

### 水/冰相变与水蒸发

| 过程 | 参数 | 代码 |
|---|---|---|
| 水 ↔ 冰 | 熔点 **273.15 K**、潜热 **336000 J/kg** | `reactions/h2o_ice.py::create(...)` |
| 水 ↔ 汽 | 相变点 **373.15 K**、潜热 **2.26×10⁶ J/kg**；饱和蒸气压用 **Antoine 方程** `p = exp(9.3876 − 3826.36/(T−45.47)) × 10⁶ Pa` | `reactions/vapor.py::create(...)` |
| 冰的物性 | `den=917`、`vis=1e30`、`cp=2100` | `fluids/h2o_ice.py` |
| 水蒸气的物性 | 密度与粘度来自 NIST 插值表（IAPWS-95），`cp=1850` | `fluids/h2o_gas/` |

⚠️ 两个"如实标注"的注意点：

- `vapor.py` 自己写着："使用 Antoine 公式，**实际上这个温度范围可能已经超过了该公式的
  适用范围**"（它允许 `temp_max` 到 700 K，断言上限 1200 K）；
- `heat=2.26e6` 只是"相变"那一项；要算"常温液态水 → 高温蒸汽"的**总**能耗，用
  `get_heat_need(water_t, steam_t)`，它把显热也算了进去。

### 干酪根裂解 / 重油裂解（页岩油原位转化 ICP）

走 **`decomposition.create`（不可逆吸热分解）**。⚠️ **不是 Arrhenius 动力学**，
而是"阶梯温度阈值 + 线性速率"。两个反应定义在 `scen/icp/_react.py`：

| 反应 | 反应物 | 生成物（质量权重） | `temp` | `heat` | `rate` |
|---|---|---|---|---|---|
| 干酪根裂解 | `kg` | — | **565 K** | **161600 J/kg** | **1e-8** |
| 重油裂解 | `ho` | — | **603 K** | **206034 J/kg** | **1e-8** |

（生成物权重见 `scen/icp/_react.py` 的源码；固体物性见 `fluids/kerogen.py`：
`den=2590`、`cp=829`，数据来自龙马溪组。）

⚠️ `rate` 的语义是"**温度超过阈值 1 K 时的反应速率**"。因为 `t2q` 只在
`[−1e3, 0, 1e3]` 上线性插值，所以实际速率对温度**极不敏感** —— 除非温度偏离阈值上千 K，
速率基本就等于 `rate` 本身。要标定活化能，得自己给一条密集的 `t2q` 曲线。

另外挂了一个**限位器**：重油裂解时"当固体占比达到 80% 之后抬高裂解温度"，避免孔隙被
固体完全占据。

### CO₂ 封存

CO₂ 以三种形态共存：**游离气相**（走多相流）+ **溶解相** + **水合物相**。

- **溶解**用 `reactions.dissolution.create(...)`：可逆、溶解度由 `ca_sol` 给出，
  ⚠️ **和温度压力无关**（代码里的原话）。实现上把"溶解度"编码成一条**虚拟的平衡温度**；
- **浮力**由 `gravity` 项承担；深海场景的初值用静水压力 `p = p_seabed − 1e4·z`
  （每 10 m 约增 0.1 MPa）与地温梯度 `T = t_seabed − grad_t·z`；
- 完整装配见 `scen/hydrate/_react.py::create_reactions(..., has_co2=, has_co2_in_liq=)`
  与 `scen/hydrate/_fluid.py::create_fludefs(...)`；
- 算例：[`zmlx/demos/`](zmlx://doc/zmlx/demos/) 下的 `hydrate/co2.py`、`co2_cylinder.py`。

### 相对渗透率

相渗以**饱和度 → k_r 的插值曲线**存储（`Seepage.set_kr` / `add_kr` / `set_default_kr`）。
最多可存 10000 条曲线 + 一条默认曲线；每个 Face 可以用 `Face.set_ikr` 选不同曲线；
**不设置时第 i 种流体默认用第 i 条**，缺失则回退到默认曲线。
[`zmlx/krs/`](zmlx://doc/zmlx/krs/) 只提供**曲线生成器**，真正的取用在内核。

| 模型 | 函数 | 公式 |
|---|---|---|
| Corey 两相（气-水） | `create_kr(srg=0.02, srw=0.2, ag=3.5, aw=4.5)` | `s > srg`: `kg = clamp(((s−srg)/(1−srw))^ag, 0, 1)`；`s > srw`: `kw = clamp(((s−srw)/(1−srw))^aw, 0, 1)`。要求 `1 ≤ ag, aw ≤ 6` |
| 水合物占据孔隙的折减 | `create_krf(faic=0.2, n=2.0)` | `s ≤ faic`: 0；否则 `k = clamp(((s−faic)/(1−faic))^n, 0, k_max)`。`faic` = 临界孔隙度 / 原始孔隙度，取值 `[0, 0.98)` |
| 裂缝（立方定律） | `create_fracture_kr()` | `kr = s³` —— 导流能力与裂缝开度的**三次方**成正比 |
| 三相 Stone Model I | `stone_model_I(...)` | 两个 Corey 两相系统 + Aziz & Settari (1979) 归一化 Stone I + Fayers & Matthews (1984) 残余油处理 |

### 毛细管压力

毛管力被实现为**驱动相邻 Cell 之间流体交换的"驱动压力"**，而**不改变各 Cell 的流体总体积**。
❗**代码里没有内置的解析毛管力公式**（van Genuchten / Brooks-Corey 都没有）——
**必须由用户提供一条 `饱和度 → 毛管压力` 的表**。

| | 位置 |
|---|---|
| 配置 | `tfc.capillary.add_setting(model, fid0, fid1, get_idx, data, gravity)` |
| 线性化 | `Seepage.get_linear_dpre(...)` —— 在当前饱和度附近取 `ds` 宽度，得到 `vs0`（等压饱和度）与 `vk`（斜率） |
| 求解 | `Seepage.diffusion(...)`，实际 `ds_max = ds × 0.5`（默认 `ds=0.05`） |

⚠️ **曲线的符号约定不统一**：一个示例里第二列是"气压力 − 水压力"（正数），另一个示例里
第二列是"水压力 − 油压力"。**使用者必须自己保证符号与 `fid0` / `fid1` 的顺序一致**。

### 扩散

**Fick 扩散**，但用了一个巧妙的复用：把"浓度"当作"温度"、把"溶液质量"当作"热容 `mc`"，
直接**借用传热求解器 `ThermalSol`** 解浓度场。扩散导流系数由 Fick 定律离散给出：

```
g = area * D / length
```

| | 位置 |
|---|---|
| 配置 | `tfc.diffusion.add_setting(model, flu0=, flu1=, ...)`（`flu0` 是溶质、`flu1` 是溶液） |
| 实现 | `tfc/_diff.py::iterate_1` |
| 每步调用 | `tfc/_main.py` 的 `_apply_diffusions` |

⚠️ **两条必须知道的注意点**（docstring 原话）：

1. **浓度是"质量分数"**（溶质质量 / 溶液质量），**不是化学里常用的 mol/L**。
   这个差异**会影响扩散系数的单位** —— 从文献拿到 `D` 时要先确认它配的是哪种浓度梯度；
2. "在迭代的时候，假设溶液质量 `m1` 是不变的。**注意：这其实是一个近似**"。

### 力学 / 变形

[`zmlx/fem/`](zmlx://doc/zmlx/fem/) + `zmlx/exts/_dyn.py` 里有**完整的线弹性有限元 +
集中质量显式动力学**，但 ⚠️ **尚未与 `Seepage` 双向耦合** —— 目前是"独立的力学求解器 + 算例"，
不是完整的 T-H-M 耦合。

`Seepage` 里的"变形"只以**孔隙弹性**的形式出现：孔隙体积随压力变化
（`set_pore(p, v, dp, dv)`、`Seepage.update_pore(...)`），**不是**真正的位移场求解。

力学求解器的工作原理（`DynSys` 的 docstring）：每个自由度上
`f = a·x + b`（受力是位移的线性函数，`a` 为稀疏刚度矩阵），牛顿第二定律
`x = x₀ + v₀·dt + 0.5·(f/m)·dt²`，整理成 `x = c·f + d`，两式组成线性方程组，
**每步解一次即完成一次迭代**。

| | 位置 |
|---|---|
| 动力学系统 | `zmlx/exts/_dyn.py::DynSys` |
| 二维有限元 | `zmlx/fem/xy.py`（支持 8 种单元：平面应力/应变的 CST / Quad4 / T6 / Quad8） |
| 三维有限元 | `zmlx/fem/xyz.py`（基于 `Mesh3.Body`，集中质量矩阵） |
| 单元刚度 | `zmlx/fem/compute_face_stiff2.py`、`zmlx/fem/stiff2.py` / `stiff3.py` |
| 边界与载荷 | `zmlx/fem/boundary.py`、`zmlx/fem/alg.py`（⚠️ **`alg.py` 已弃用**，2027-6-26 删除） |

> ⚠️ 开发状态如实标注：`fem/alg.py` 已弃用；`create2.py` / `create3.py` 已弃用；
> 目前**没有流固耦合的回写路径**（压力只作为载荷施加，不回写孔隙度 / 渗透率）。

### 砂运移（实验性）

砂分"**流动砂**"与"**沉降砂**"两种流体，两者按**剪切力（压力梯度）→ 目标浓度曲线**交换体积。
配置入口 `tfc.sand.add_setting(model, sol_sand=, flu_sand=, ca_i0=, ca_i1=)`。

⚠️ 模块 docstring 自己标注为实验性："用于模拟砂的沉降及脱离（测试中）。
**存在已知问题，即梯度的计算不准确，造成无法很好地计算砂子的脱离**"。

### 时间步长控制

这是一个"**各子过程提交建议值、全局取最小**"的架构，而不是单一公式。

1. **CFL 的定义**：`dt` 内流体流过的"最大距离"与网格尺寸的比值；
2. 每步开始时 `clear_dt_next(model)` 清空建议列表；
3. 各子过程完成后用 `add_dt_next(model, dt, desc=...)` 提交建议
   （`iterate_flow` → `"flow"`、`iterate_thermal` → `"thermal"`、扩散 → `"diffusion"`）；
4. 每步结束时 `dt = get_dt_next(model)` —— **取所有建议的最小值**，再钳制到
   `[dt_min, dt_max]`（默认 `1e-15` ~ `1e10` 秒）。没有任何建议就沿用当前 `dt`；
5. 建议值的算法（`calc_recommended_dt(prev_dt, prev_cfl, target_cfl=0.1)`）：
   - `prev_cfl > target_cfl` → `dt = prev_dt × (target_cfl × 0.99 / prev_cfl)`
     （**直接压到目标以下**）；
   - 否则 → `dt = prev_dt × min(2.0, sqrt(target_cfl / prev_cfl))`
     （**每步最多放大 2 倍**）。

| 相关项 | 说明 |
|---|---|
| `cfl` | 默认 **0.1**；三个层级：全局 `cfl` → `flow_cfl` → `thermal_cfl`，逐级回退 |
| `check_dt` 标签 | **决定 cfl 是否真的传给内核**。不加这个标签时 `cfl=None`，内核**必须完全接受给定的 dt**，可能不稳定 |
| `dv_relative` | **已弃用**（2027-6-17 后移除），现在等价于 `cfl` |

⚠️ 实务惯例：建模后 `model.add_tag('check_dt')`；**注入 / 加热之后**
`tfc.set_dt(model, 1e-3)` 重置步长（因为上一阶段的大步长不适合下一阶段）。

### 一张表：公式 vs 参数

| 你关心的 | 方程 / 求解在哪 | 参数 / 曲线在哪 |
|---|---|---|
| 达西流动 | C++ `seepage_fs_iterate` ← `FlowSol.iterate` | `tfc.set_face`（`cond = area×perm/length`） |
| 导流 + 相渗修正 | `Seepage.get_cond_for_exchange` | `zmlx/krs/`、`Seepage.set_kr` |
| 传热 | C++ `seepage_ts_iterate` ← `ThermalSol.iterate` | `tfc.set_cell` / `set_face`（`g_heat`、`mc`） |
| 固-流换热 | C++ `seepage_exchange_heat` ← `Seepage.exchange_heat` | Cell `g_heat = vol×heat_cond/dist²` |
| 反应速率 | C++（`Reaction` 的 10 步流程） | `zmlx/reactions/`（`t2q`、`p2t`、`c2t`） |
| 毛管力 | C++ `seepage_diffusion` ← `Seepage.diffusion` | `tfc.capillary` + 用户提供 `s→Pc` 表 |
| 扩散 | 复用 `ThermalSol` | `fa_d`（m²/s，**质量分数梯度**） |
| 力学 | C++ `dynsys_iterate` / `fem_alg_create2` | `zmlx/fem/`（`E`、`μ`、`h`、`ρ`） |
| 步长 | `calc_recommended_dt`（纯 Python） | `cfl`、`dt_min`/`dt_max`、`check_dt` 标签 |
'''),

        E('demos', '示例集导读：110 个可以跑的算例', '''\
[`zmlx/demos/`](zmlx://doc/zmlx/demos/) 是全库**最该先看的地方**。目录里有 171 个 `.py`，
但只有 **110 个**是 GUI 里可见、可独立运行的 demo —— 其余是 `__init__.py`、废弃代码
（`__Trash/`）、调试草稿（`debugging/`）和辅助脚本。

> **怎么认出一个 demo**：文件首行有 `# ** desc = '中文描述'` 注释。没有 `desc` 的文件
> 在 [「帮助 → 示例」](zmlx://gui/show_demo) 里**不可见**。这是一条硬约定 —— 辅助模块
> 正是靠"没有 desc"才不被当成 demo 列出来。

### 怎么运行

```bash
python zmlx/demos/flow_1ph/darcy_1d.py            # GUI 模式（默认）
python zmlx/demos/flow_1ph/darcy_1d.py --no-gui   # 无头模式，图保存到文件
```

也可以直接从界面里跑：[「帮助 → 示例」](zmlx://gui/show_demo) 会列出全部 110 个 demo
（路径 / 描述 / 作者 / 运行按钮）。

### 13 个主题目录

| 目录 | 主题 | 数量 | 代表性文件 | 学什么 |
|---|---|---|---|---|
| `flow_1ph/` | 单相达西流、扩散、压降漏斗 | 12 | `darcy_1d.py`、`p_evolution1d.py`、`diffusion1.py` | **最适合入门**。底层手搭 `Seepage`、`cond = area×perm/dist`、极大体积做定压边界、与达西解析解对拍 |
| `flow_2ph/` | 两相驱替、重力分异、毛管力 | 13 | `gas_mig.py`、`gravity.py`、`wat_disp_oil.py`、`capillary.py` | 高层 `tfc.create()` + 空间分布函数；NIST 物性；相渗与毛管压力曲线；浮力运移成藏 |
| `flow_dy/` | 流体惯性 / 压力波 | 3 | `dyn_0d.py`、`dyn_1d.py`、`dyn_2d.py` | 与稳态渗流不同的**动力学模式**：惯性项、压力波往复振荡 |
| `flow_thermal/` | 流动 + 传热耦合 | 1 | `heat_convection.py` | 温度差 → 密度差 → 自然对流 |
| `thermal/` | 纯热传导、地热、EGS | 9 | `thermal1d.py`、`thermal2.py`、`egs2.py`、`geothermal.py` | `iterate_thermal()` 底层热传导；误差函数解析解对拍；**极大热容 `denc=1e20` 钉扎温度** |
| `hydrate/` | 水合物成藏、开采、实验尺度 | 20 | `prod_v2.py`、`prod_v2_inj_hot_water.py`、`prod_v2_electric_heating.py`、`form.py` | 场景级 `hydrate.create()`；降压 / 注热水 / 电加热三种开采方式；变相渗；CO₂ 置换；岩心尺度合成与分解 |
| `heavy_oil/` | 油页岩原位转化 ICP | 2 | `icp_xz.py`、`icp_cylinder.py` | **热-流-化三场耦合**最完整的范例 |
| `mech/` | 固体力学（FEM） | 15 | `test_01.py`、`test_01b.py`、`test_03.py`、`wave_01.py` | 三角网格 + 刚度矩阵；静力 / 动态应力波；带 `b` 的版本改用高层 API，**成对对比两套写法** |
| `spring/` | 弹簧-质量动力学 | 4 | `spring_sys.py`、`wave_01.py` | 点源径向波与多源干涉 |
| `aqueous/` | 水溶液多组分对流扩散 | 3 | `test_1.py`、`test_2.py`、`test_3.py` | `create_aqueous()` 加气态组分；密度差驱动的重力对流 |
| `plt/` | matplotlib 绘图专题 | 8 | `contourf.py`、`tricontourf_demo.py`、`sin.py` | 与物理无关、纯可视化；`sin.py` 演示 `gui.progress()` + `gui.break_point()` |
| `gui_input/` | GUI 交互控件 | 1 | `test_1.py` | pyqtgraph 参数树：纯字典声明参数界面 |
| `others/` | 杂项合集 | 19 | `IP.py`、`dfn_v3.py`、`sand.py`、`Timer.py` | 侵入逾渗、DFN 三维裂缝网络、出砂、性能计时 |

### 推荐学习顺序

1. `flow_1ph/darcy_1d.py` —— 起点。底层手搭，与解析解对拍；
2. `flow_1ph/p_evolution1d.py` → `pressure.py` —— 压力场演化、二维压降漏斗；
3. `flow_1ph/diffusion1.py` —— 渗流 + Fick 扩散；
4. `flow_2ph/`（`gravity.py` → `gas_mig.py` → `wat_disp_oil.py` → `capillary.py`）
   —— 切到高层建模，两相 / 毛管力；
5. `thermal/thermal2.py` → `thermal1d.py` → `thermal7.py` —— 纯传热、各向异性；
6. `flow_thermal/heat_convection.py` —— 热与流的耦合；
7. `hydrate/prod_v2.py` → `prod_v2_inj_hot_water.py` → `prod_v2_vari_kr.py`
   —— 水合物主线；
8. `heavy_oil/icp_xz.py` —— 热-流-化三场耦合；
9. `mech/test_01.py` → `test_03.py` → `wave_01.py` —— 固体力学；
10. `aqueous/test_1.py` —— 水溶液多组分输运。

### 怎么写一个新的 demo

| 要求 | 说明 |
|---|---|
| `# ** desc = '...'` | **必须写在文件首行**，否则 GUI 里看不到它 |
| `# ** highlight = '#4575b4'` | 可选：给 GUI 里这一行着色 |
| 入口 | `gui.execute(main, close_after_done=False)`，**只**写在 `if __name__ == '__main__'` 里 |
| 风格 | `from zmlx import *`、中文注释、代码自包含 |
| 放哪 | 放进与物理领域匹配的子目录 |

⚠️ 两个陷阱：`frac/` 目录有 `ReadMe.md` 说"压裂演示"，但**只有一个空的 `__init__.py`，
零个 demo**；`others/` 里有一批**大小写重复**的旧脚本（`GasMig.py` vs `gas_mig.py`），
旧的多数没有 `desc`。

### 批量测试

```bash
python zmlx/demos/test_all_demos.py [--jobs N] [--timeout N] [--verbose]
```

它把每个 demo 以 `--no-gui` 起**独立子进程**跑一遍，收集 stdout/stderr，最后汇总成
`test_report.log`（输出目录 `test_output_<时间戳>/`）。

| 选项 | 默认 | 含义 |
|---|---|---|
| `--jobs N` | CPU 核心数 | 并发数（= 同时跑几个子进程） |
| `--timeout N` | **60 秒** | 单个 demo 的超时；超时记为 **TIMEOUT，不算失败** |
| `--verbose` | 关 | 额外打印每个 demo 输出的最后 2 行 |

⚠️ **`test_all_demos.py` 自己不解析 `--no-gui`** —— 它给每个子 demo 硬编码传这个参数。
在外层加 `--no-gui` 没有任何效果。

结果分类：退出码 `0` = 通过、`-1` = 超时（计算量大，非错误）、`-2` = 测试框架自身出错、
其它非零 = 失败。
''', ('demos', 'demo 的推荐学习顺序（由浅入深）', 900, 900)),

        E('data_flow', '一次求解发生了什么', '''\
这一页把"按一下运行"拆开看：一次 `iterate()` 里到底按什么顺序做了哪些事。

### 顶层四步

1. **建模**：`tfc.create(...)` / `hydrate.create(...)` 造出一个 `Seepage`；
2. **时间推进**：`seepage.iterate(step)` 或 `tfc.solve(model, ...)`；
3. **步长控制**：各子过程提交建议，取最小值（见 [物理模型](#physics) 最后一节）；
4. **后处理**：取出数组 → `show_field2` / `plot_on_figure` / 存盘。

### `tfc.iterate()` 内部的顺序

`tfc/_main.py::iterate` 严格按下面的顺序调用各子过程（这就是"耦合"的全部含义）：

| # | 子过程 | 干什么 |
|---|---|---|
| 1 | `_time.iterate` | 时间触发器：到点执行用户注册的回调 |
| 2 | `_step.iterate` | 步进触发器：每 N 步执行一次回调 |
| 3 | `_fluid.iterate` | 更新流体密度 / 粘度（受 `disable_update_den` / `disable_update_vis` 控制） |
| 4 | `_inj.iterate` | 执行注入器 |
| 5 | `_prod.iterate` | 按时间-压力曲线控制生产井 |
| 6 | `_heating.iterate` | 分布式加热 |
| 7 | `_solid.backup` | **把固体相临时弹出**（有 `has_solid` 标签时） |
| 8 | `_cond.iterate` | 按孔隙体积变化更新 Face 的导流系数 |
| 9 | **`iterate_flow`** | **流动求解**（达西 + 相渗 + 粘度修正），提交步长建议 |
| 10 | `_apply_diffusions` | 扩散 |
| 11 | `_cap.iterate` | 毛管压力驱动的组分交换 |
| 12 | `_diff.iterate` | 扩散（新版设置） |
| 13 | `_solid.restore` | 把固体相推回去 |
| 14 | `_sand.iterate` | 砂运移（实验性） |
| 15 | **`iterate_thermal`** | **传热求解**，提交步长建议 |
| 16 | `_exchange_heat` | 流体 ↔ 骨架换热 |
| 17 | `_apply_reactions` | 化学反应 |
| 18 | —— | 更新 `time` / `step`，`set_dt(get_dt_next())` |

> ⚠️ **为什么要把固体相 backup / restore**：模型里有固体（水合物、冰、干酪根）时，
> 流动求解期间"最后一种流体不存在" —— 固体不参与流动。⚠️ **只允许最后一种流体是固体**。

### `tfc.solve()` 做了什么

`solve(model, time_forward=..., folder=..., extra_plot=...)` 是"帮你循环"的封装：

- 按 `dt` 反复 `iterate()` 直到 `time_forward`；
- 每一步（或每 N 步）调一次 `extra_plot` 画图；
- 定期把模型存盘到 `folder`（存成 `.seepage` 文件）；
- 通过 `GuiIterator` 控制绘图频率，保证"画图时间不超过迭代时间的 `ratio`"。

⚠️ `gui_mode=True` 参数**已弃用**（2027-07-15 移除）。要在界面里跑，正确写法是：

```python
def main():
    tfc.solve(model, time_forward=365 * 24 * 3600, folder='output')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
```

### 手动推进

要完全自己控制节奏时：

```python
dt = 1.0e8
for step in range(100):
    model.iterate(dt=dt)
    dt = model.get_recommended_dt(previous_dt=dt, cfl=0.1)
```

或直接用 `tfc.iterate_until(model, target_time=...)`。

### 结果怎么取出来

```python
x = tfc.get_x(model, shape=(nx, nz))      # 坐标
p = tfc.get_p(model, shape=(nx, nz))      # 压力
t = tfc.get_temperature(model, shape=(nx, nz))
s = tfc.get_v(model, fid=0, shape=(nx, nz))   # 某流体的体积

cells = as_numpy(model).cells             # 直接看内存的适配器
```

`shape=` 参数会把扁平数组 reshape 成网格形状，方便直接交给等值线函数。

### 保存与恢复

```python
model.save('model.seepage')
model = Seepage()
model.load('model.seepage')
```
''', ('data_flow', '一次时间步：主流程与 iterate 内部的子过程顺序', 900, 900)),

        E('boundary', '边界条件与井', '''\
`zmlx` **不是**用"指定边界上的值"来做边界条件的，而是**通过操作模型属性**让某个区域
在数值上"钉住"。这是最容易踩坑的地方，也是最需要记住的几条惯例。

### 定压边界

**方法一：把边界 cell 的体积设成极大值**（例如 `1e6` m³）—— 体积大意味着流动中压力几乎不变：

```python
c.set_pore(p=1e6, v=1e6, dp=1e6, dv=1e5)
```

**方法二：把边界 cell 的孔隙度设成极大值**（例如 `1e10`）—— 效果相同：

```python
def get_fai(x, y, z):
    return 1.0e10 if is_upper(x, y, z) else 0.3
```

⚠️ **不要直接去改边界 cell 的压力** —— 流动一开始它就被别人拉扯走了，钉不住。

### 恒温边界

把边界 cell 的热容（`denc` = 密度 × 比热）设成极大值（例如 `1e20`）：

```python
def denc(*pos):
    return 1e20 if is_upper(*pos) or is_lower(*pos) else 5e6
```

冷源 / 热源同理，只是 `denc` 之外还要配一个温度。

### 封闭边界

- **无流动**：不给那个 cell 连 face（或者把 `perm` 设成 0）；
- **绝热**：不给它连传热的 face（或者把 `heat_cond` 设成 0）。

### 井：注入与生产

**注入井**（注入速率 kg/s）：

```python
model.add_injector(cell=target_id, fluid_id=1, flu=injection_fluid, value=rate)
```

**生产井**：在 `tfc.create` / `hydrate.create` 里用 `prods` 指定
（`index` 是 cell 编号，`p` 是井底流压随时间的变化）：

```python
prods=[{'index': cell_index, 't': [0, 1e20], 'p': [3e6, 3e6]}]
```

**电加热**（纯热注入，功率 W）：

```python
model.add_injector(cell=target_id, ca_mc=model.get_cell_key('mc'),
                   ca_t=model.get_cell_key('temperature'), value=500)
```

### 虚拟 Cell / Face：把井接到模型上

`add_cell_face(mesh, pos=..., offset=..., vol=..., area=..., length=...)` 会在指定位置
创建一个**虚拟的 cell + face**，作为生产井 / 注入井的接口：

```python
add_cell_face(mesh, pos=[0, 0, -50], offset=[0, 10, 0],
              vol=1000, area=5, length=1)
```

⚠️⚠️ **虚拟 face 会漏热** —— 它是一条真实的传热通道。所以 `add_cell_face` 之后**必须**
在附近把 `heat_cond` 设成 0：

```python
def heat_cond(x, y, z):
    return 1.0 if abs(y) < 2 else 0.0     # 只在井附近导热
```

### 多阶段模拟：注入 / 加热时关井

注热水或加热阶段，如果生产井还开着，流体就会"短路"直接跑掉。惯例是**临时关掉虚拟 face
的渗透性**，做完再恢复：

```python
virtual_face = model.get_face(-1)
perm_backup = virtual_face.get_attr('perm')
tfc.set_face(virtual_face, perm=0.0, heat_cond=0.0)
#  ... 注入 / 加热 ...
tfc.set_face(virtual_face, perm=perm_backup, heat_cond=0.0)
```

### 空间分布函数：`zmlx` 的核心建模范式

把物性写成 `(x, y, z) → 值` 的闭包，交给 `create` 系列函数，它会**自动应用到每个 cell**：

```python
def get_k(x, y, z):
    return 1.0e-14 if -70 < z < -30 else 1.0e-15      # 储层 vs 盖层

def get_s(x, y, z):
    return {'ch4': 0.5, 'h2o': 0.5}                    # 两相
```

三种常见模式：

1. **分段函数**（上面这样，按坐标分层）；
2. **圆形 / 球形区域**：`get_distance([x,y,z], center) < radius`；
3. **网格边界**：`mesh.get_pos_range(2)` 取 z 范围，再判断"是不是顶面 / 底面"。

⚠️ **饱和度字典里的名字必须与 `FluDef.name` 一致**，而且**各相之和 ≤ 1**。
'''),

        E('api', 'API 速查：按包列出公开接口', '''\
这一页把各包**真正会被调用的公开函数**列出来（签名取自源码，说明取自 docstring 首行）。
想找某个功能时用浏览器/编辑器的**查找**（Ctrl+F）直接在下面搜名字。

> ⚠️ 三个必须知道的全局注意点：
>
> 1. **参数校验用的是 `assert`，不是 `raise ValueError`** —— 所以 `python -O` 跑起来会
>    **静默跳过所有校验**，出了错也看不到提示；
> 2. **很多函数要求 SI 单位**（Pa、K、m、kg、s），传 MPa 或 ℃ 会得到**静默的错误值**；
> 3. **`zmlx.dfn2` / `dfn_v3` / `rect_3d` / `rect_v3` 在顶层拿到的是「模块」而不是函数**，
>    要写全路径：`from zmlx.geometries.dfn2 import dfn2`。

### 不知道用哪个包？

| 我要…… | 包 |
|---|---|
| 造模型、推进时间、取数据 | [`zmlx/tfc/`](zmlx://doc/zmlx/tfc/) |
| 定义流体（水、气、水合物、水溶液…） | [`zmlx/fluids/`](zmlx://doc/zmlx/fluids/) |
| 加反应（相变、裂解、溶解…） | [`zmlx/reactions/`](zmlx://doc/zmlx/reactions/) |
| 改相渗曲线 | [`zmlx/krs/`](zmlx://doc/zmlx/krs/) |
| 建网格 | [`zmlx/seepage_meshes/`](zmlx://doc/zmlx/seepage_meshes/)（渗流）、[`zmlx/meshes/`](zmlx://doc/zmlx/meshes/)（几何） |
| 几何计算、裂缝网络 | [`zmlx/geometries/`](zmlx://doc/zmlx/geometries/) |
| 画图 | [`zmlx/plt/`](zmlx://doc/zmlx/plt/)（`show_*` / `add_*`）、[`zmlx/fig/`](zmlx://doc/zmlx/fig/)（声明式） |
| 高层工具（场、迭代器、存档、监测） | [`zmlx/utils/`](zmlx://doc/zmlx/utils/) |
| 文件、JSON、路径 | [`zmlx/io/`](zmlx://doc/zmlx/io/)、[`zmlx/algs/`](zmlx://doc/zmlx/algs/) |
| 全局配置、日志、无头判定 | [`zmlx/system/`](zmlx://doc/zmlx/system/) |
| 现成的应用场景 | [`zmlx/scen/`](zmlx://doc/zmlx/scen/) |

### 最容易用错的六个

| 函数 | 要点 |
|---|---|
| `tfc.create(mesh, ...)` | **建模主入口**。所有物性参数都可以传**数值或 `f(x,y,z)` 闭包** |
| `tfc.solve(model, time_forward=..., folder=...)` | 一键求解 + 自动存盘 + 定时绘图。⚠️ `gui_mode=True` 已弃用 |
| `tfc.seepage.iterate()` | 推进一步（`iterate` 的别名）。内部按固定顺序调 18 个子过程 |
| `as_numpy(model)` | 拿到 numpy 适配器，批量读写比逐个 cell 快得多 |
| `create_kr(...)` | 返回 `(vs, kg, kw)` **三个数组**，不是 `Interp1` |
| `plot(on_figure, caption=...)` | **绘图唯一出口**：GUI 开标签页、无头存文件、脚本里 `plt.show()` |

### 顶层 `import zmlx` 里有什么

`zmlx/__init__.py` 把两百多个名字提到了顶层，多数脚本写 `from zmlx import *` 就够了。
主要包括：`seepage`（= tfc 引擎）、`create_ch4` / `create_h2o` / `create_co2` /
`create_aqueous`、`create_kr` / `create_krf`、`create_reaction` / `add_reaction`、
`hydrate` / `icp`、`create_cube` / `create_xz` / `add_cell_face`、
`plot` / `show_field2` / `plot_on_figure`、`Field` / `GuiIterator` / `SaveManager`、
`get_path` / `getenv` / `setenv`、`gui` / `information` / `question`。

⚠️ 顶层的 `TherFlowConfig` / `SeepageTher` 是**已弃用**的旧接口。

### zmlx/tfc/ —— 耦合引擎（建模 / 求解 / 步长 / 取数据）

**建模**

| 函数 | 签名 | 说明 |
|---|---|---|
| `create` | `create(mesh=None, *, fludefs=None, reactions=None, gravity=None, dt_max=None, dt_min=None, dt_ini=None, cfl=None, kr=None, default_kr=None, gr=None, caps=None, has_solid=False, prods=None, injectors=None, texts=None, **kwargs)` | **主入口**：一站式创建渗流模型。其余参数（`porosity` / `perm` / `p` / `temperature` / `s` / `heat_cond` / `denc` / `pore_modulus`）直接传给 `set_model` |
| `set_model` | `set_model(model, *, porosity=0.1, pore_modulus=1e9, denc=1e6, dist=0.1, temperature=280.0, p=None, s=None, perm=1e-14, heat_cond=1.0, mesh=None, **ignores)` | 批量设全场初值。**每个参数都可传数值或 `f(x,y,z)`** |
| `add_mesh` | `add_mesh(model, mesh)` | 由 `SeepageMesh` 建 Cell（位置/体积）与 Face（面积/长度） |
| `set_cell` | `set_cell(cell, pos=None, vol=None, porosity=0.1, pore_modulus=1e9, denc=1e6, dist=0.1, temperature=280.0, p=1.0, s=None, use_mass=False, heat_cond=1.0)` | 设置单个 Cell 的初始状态 |
| `set_face` | `set_face(face, area=None, length=None, perm=None, heat_cond=None, igr=None, bk_g=True)` | 设置单个 Face，**自动算 `cond = area×perm/length`** |
| `add_injector` | `add_injector(model, data)` | `data` 为 dict 或 dict 列表 |

**求解与推进**

| 函数 | 签名 | 说明 |
|---|---|---|
| `iterate` | `iterate(*models, pool=None, **global_opts)` | **推进一步**（核心）。返回实际迭代的模型数 |
| `iterate_until` | `iterate_until(*models, target_time=1e200, n_loop_max=9999999999, **opts)` | 迭代到目标时间，返回 `(n_loop, n_iter)` |
| `solve` | `solve(model=None, folder=None, fname=None, extra_plot=None, save_dt=None, time_unit='y', **opt_sol)` | **一键求解**：循环 iterate + 定时存盘 + 定时绘图 |
| `iterate_flow` | `iterate_flow(*models, pool=None, **opts)` | 只推流动（流体性质不变） |
| `iterate_thermal` | `iterate_thermal(*models, pool=None, **opts)` | 只推传热 |
| `print_cells` | `print_cells(path, model, ca_keys=None, fa_keys=None, fmt='%.18e', export_mass=False)` | 导出 Cell 表（前 3 列 xyz） |

**时间步与状态**

| 函数 | 签名 | 说明 |
|---|---|---|
| `get_dt` / `set_dt` | `get_dt(model, as_str=False)` / `set_dt(model, dt)` | 时间步长（默认 `1e-10` 秒） |
| `get_time` / `set_time` | `get_time(model, as_str=False)` / `set_time(model, value)` | 模型时间（默认 0） |
| `get_step` / `set_step` | `get_step(model)` / `set_step(model, step)` | 迭代步数 |
| `get_dt_min` / `get_dt_max` | `get_dt_min(model)` / `get_dt_max(model)` | 步长硬约束（默认 `1e-15` / `1e10`） |
| `get_dt_next` / `add_dt_next` | `get_dt_next(model, clear=True)` / `add_dt_next(model, dt, desc=None)` | 建议步长队列（取最小值） |
| `get_cfl` / `set_cfl` | `get_cfl(model)` / `set_cfl(model, value)` | CFL（默认 **0.1**） |
| `get_flow_cfl` / `get_thermal_cfl` | `(model)` | 分项 CFL，未设时回落到 `get_cfl` |

**取数据（都是 numpy 数组）**

| 函数 | 签名 | 说明 |
|---|---|---|
| `get_x` / `get_y` / `get_z` | `(model, mask=None, shape=None)` | Cell 坐标 |
| `get_p` / `get_cell_pre` | `(model, mask=None, shape=None)` | 压力数组 |
| `get_t` / `get_cell_temp` | `(model, mask=None, shape=None)` | 温度数组 |
| `get_v` / `get_cell_fv` | `(model, fid=None, mask=None, shape=None)` | 流体体积 |
| `get_m` / `get_cell_fm` | `(model, fid=None, mask=None, shape=None)` | 流体质量 |
| `get_c` / `get_cell_fc` | `(model, sol, liq, mask=None, shape=None)` | 质量浓度 = sol / liq |
| `get_sat` | `get_sat(names, table)` | 按名字取饱和度 |
| `get_ca` / `get_fa` / `set_fa` | `(model, ca, ...)` / `(model, fid, fa, ...)` | 任意 Cell / 流体属性 |
| `get_cell_mask` | `get_cell_mask(model, xr=None, yr=None, zr=None)` | 按坐标范围筛出布尔掩码 |
| `as_numpy` | `as_numpy(model)` | 返回 `SeepageNumpy` 适配器（`.cells` / `.faces` / `.fluids(fid)`） |

**场运算**（由 Cell 值 → Face 值，或反过来）

`get_face_gradient`（`(c1-c0)/dist`）、`get_face_diff`（`c1-c0`）、`get_face_sum`（`c1+c0`）、
`get_face_average`、`get_face_left` / `get_face_right`、`get_cell_average` / `get_cell_max`。

**子过程配置**（都在 `tfc.` 命名空间下，统一风格：`add_setting(model, ...)`）

| 模块 | 主要函数 |
|---|---|
| `tfc.capillary` | `add_setting(model, fid0=None, fid1=None, get_idx=None, data=None, gravity=None)` |
| `tfc.diffusion` | `add_setting(model, flu0=None, flu1=None, ca_m1=None, fa_g=None, fa_d=None, ca_c=None, cfl=None, d=None)` |
| `tfc.prod` | `add_setting(model, index=None, pos=None, t=None, p=None)` |
| `tfc.sand` | `add_setting(model, *, sol_sand, flu_sand, ca_i0, ca_i1, use_average=False)` |
| `tfc.step_iteration` | `add_setting(model, *, start=0, step=1, stop=999999999, name=None, args=None, kwds=None)` |
| `tfc.timer` | `add_setting(model, *, time, name, args=None, kwds=None)` |
| `tfc.adjust_vis` | `add_setting(model, name=None, key=None)` |
| `tfc._heating` | `add_setting(model, fluid=None, power=None, temp_max=None)`（**全储层分布式加热**） |
| `tfc.show_cells` | `show_cells(model, dim0, dim1, ...)`（⚠️ 无界面时直接返回） |

**其它**：`check_seepage(model)`（返回模型问题清单）、`get_cells_along_seg(p0, p1, model)`、
`get_cells_along(points, model)`、`subdomain.create/iterate/split`（子域并行）。

### zmlx/fluids/ —— 流体物性

| 函数 | 签名 | 返回 |
|---|---|---|
| `create_h2o` | `create(t_min=272, t_max=300, p_min=1e6, p_max=40e6, name=None, specific_heat=4200.0)` | 液态水（经验公式） |
| `create_ch4` | `create(t_min=270, t_max=290, p_min=1e6, p_max=40e6, name=None)` | 甲烷气（理想气体 + 压缩修正） |
| `create_co2` | `create(name=None)` | CO₂（NIST 插值表），cp=2844.8 |
| `create_ch4_hydrate` | `create(name=None)` | 甲烷水合物固体（den=919.7, vis=1e30, cp=2100） |
| `create_co2_hydrate` | `create(name=None, den=1112.0, specific_heat=2190.0)` | CO₂ 水合物固体 |
| `create_h2o_ice` | `create(name=None)` | 冰（den=917, vis=1e30, cp=2100） |
| `create_h2o_gas` | `create(name=None)` | 水蒸气（NIST 插值表），cp=1850 |
| `create_aqueous` | `create_aqueous(name='liq', *, h2o=None, solutes=None, **others)` | 水溶液（溶质为 `[name, c, den_times, vis_times]`） |
| `create_solute` | `create_solute(solvent, c=0.01, den_times=1.0, vis_times=1.0, name=None)` | 溶质（要求 `0 < c ≤ 0.2`） |
| `create_mixture` | `create_mixture(name, *components, **others)` | 混合气（组分必须是无组分的纯流体） |
| `from_data` | `from_data(data, get_t, get_p, get_den, get_vis, t_min=None, t_max=None, p_min=None, p_max=None, name=None, specific_heat=None)` | 从散点表建流体 |
| `from_file` | `from_file(fname, t_min=None, t_max=None, p_min=None, p_max=None, name=None, specific_heat=None)` | 读 txt（列：`T[K] P[Pa] den vis`） |
| `load_fludefs` | `load_fludefs(option, folder)` | 从 JSON / 文件批量加载 |
| `get_density` / `get_viscosity` | `get_density(pre, temp, flu_def)` / `get_viscosity(pre, temp, flu_def)` | 快捷查物性 |

**子模块访问**：`from zmlx.fluids import ch4, h2o, co2, oil, kerogen, char`，各模块内是 `create(...)`。

**高精度物性引擎**（可选依赖）：

- `zmlx.fluids.cp`（**CoolProp**，Helmholtz 状态方程，误差 < 0.1%）：8 种流体
  `h2o_/h2_/he_/ch4_/c2h6_/n2_/o2_/co2_` × `_density / _viscosity / _specific_heat`，
  签名统一为 `fn(P, T)`。装法：`pip install CoolProp`；
- `zmlx.fluids.rkt`（**Reaktoro**，地质化学，基于 Supcrt98）：7 种流体（**没有粘度**），
  另有 `rkt/aq/` 提供水溶液密度与溶解度。装法：`conda install -c conda-forge reaktoro`。

### zmlx/reactions/ —— 化学反应

| 函数 | 签名 | 说明 |
|---|---|---|
| `add_reaction` | `add_reaction(model, data, need_id=False)` | **主入口**：`data` 是配置 dict 或 `Seepage.Reaction` |
| `create_inh` | `create_inh(sol, liq, c=None, t=None, *, use_vol=False, c2t=None, c2q=None, exp=None, exp_r=None)` | 构造抑制剂配置 |
| `add_inh` | `add_inh(r, *args, **kwargs)` | 把抑制剂追加到反应配置里 |
| `load_reactions` | `load_reactions(option, folder)` | 从文件批量读反应 |
| `endothermic.create` | `create(left, right, temp, heat, rate=None, fa_t=None, fa_c=None, l2r=True, r2l=True, p2t=None, t2q=None, inhibitors=None)` | **所有反应的底层构建块** |
| `hydrate.create` | `create(gas, liq, hyd, mg, vp, vt, temp, heat, ..., dissociation=True, formation=True)` | 通用水合物反应 |
| `ch4_hydrate.create` | `create(gas, wat, hyd, fa_t=None, fa_c=None, dissociation=True, formation=True, nh=6.0)` | 甲烷水合物（平衡曲线取自 TOUGH+ Hydrate） |
| `co2_hydrate.create` | `create(gas, wat, hyd, ..., nh=5.75)` | CO₂ 水合物 |
| `h2o_ice.create` | `create(flu, sol, fa_t=None, fa_c=None, temp=273.15, heat=336000.0, enable_melt=True, enable_freeze=True)` | 水 ↔ 冰 |
| `vapor.create` | `create(vap, wat, fa_t=None, fa_c=None, temp_max=None)` | 水 ↔ 汽（Antoine 方程） |
| `melt.create` | `create(sol, flu, temp, heat, fa_t=None, fa_c=None, vp=None, vt=None, t2q=None, ...)` | 融化 / 气化 / 升华 |
| `freeze.create` | `create(flu, sol, vp, vt, temp, heat, ...)` | 凝固 / 凝结 |
| `dissolution.create` | `create(*, sol=None, sol_in_liq=None, liq=None, ca_sol=None, rate=1.0, ...)` | 溶解（⚠️ 溶解度与 T、P 无关） |
| `decomposition.create` | `create(left, right, temp, heat, rate, fa_t=None, fa_c=None)` | **不可逆**吸热分解（干酪根 / 重油） |
| `combustion.create` | `create(left, right, temp, heat, rate, fa_t=None, fa_c=None)` | 燃烧（超过燃点才发生） |

**几个有用的常数函数**：`ch4_hydrate.get_mg_vs_mh(nh=6.0)` → 0.129（1 kg 水合物产甲烷质量）、
`ch4_hydrate.get_dheat(nh=6.0)` → 437096.77 J/kg、`ch4_hydrate.get_p(t)` / `get_t(p)`（平衡曲线）、
`co2_hydrate.get_dheat(nh=5.75)` → 406514.3 J/kg、`vapor.get_heat_need(water_t, steam_t)`。

### zmlx/krs/ —— 相对渗透率

| 函数 | 签名 | 返回 |
|---|---|---|
| `create_kr` | `create_kr(srg=0.02, srw=0.2, ag=3.5, aw=4.5, count=100)` | `(vs, kg, kw)` 三个数组 |
| `create_krf` | `create_krf(faic=0.2, n=2.0, as_interp=False, k_max=1.0, s_max=1.0, count=100)` | 折减曲线；`as_interp=True` 返回 `Interp1`（可直接作 `tfc.create(gr=...)`） |
| `create_fracture_kr` | `create_fracture_kr()` | `(vs, [s**3])` 立方定律 |
| `stone_model_I` | `stone_model_I(swir, sorg, sorw, sgc, krwro, kroiw, krgro, nw, nsorw, ng, nog)` | 三相；**要从 `zmlx.krs.stone_model_I` 导入**（包顶层没有） |

### zmlx/seepage_meshes/ —— 渗流网格

| 函数 | 签名 | 说明 |
|---|---|---|
| `create_cube` | `create_cube(x=(-0.5,0.5), y=(-0.5,0.5), z=(-0.5,0.5), boxes=None, ...)` | 长方体网格（坐标序列须递增）。别名 `create_cube_seepage_mesh` |
| `create_xyz` | `create_xyz(*, x_min, dx, x_max, y_min, dy, y_max, z_min, dz, z_max, **kwargs)` | 均匀三维网格 |
| `create_xz` / `create_xy` | `create_xz(*, x_min, dx, x_max, z_min, dz, z_max, y_min, y_max, ...)` | 二维网格（厚度方向只留 1 层） |
| `create_cylinder` | `create_cylinder(x=(0,1,2), r=(0,1,2))` | 极坐标圆柱（**对称轴为 x**） |
| `create_wellbore` | `create_wellbore(trajectory, length=1.0, area=0.01)` | 井筒网格 |
| `add_cell_face` | `add_cell_face(mesh, *, offset, pos=None, cell=None, vol=1.0, area=1.0, length=1.0)` | 在网格外接一个"虚拟 cell + face"（**井接口**） |
| `seepage_mesh_rescale` | `scale(mesh, factor, on_pos=True, on_area=True, on_vol=True, on_dist=True)` | 缩放 |
| `swap_xy` / `swap_yz` / `swap_xz` | `(mesh)` | 换轴 |

### zmlx/meshes/ —— 几何网格 `Mesh3`

`create_cube_mesh(xs, ys, zs)`、`create_rect_mesh(xs, ys, z=0.0)`、
`get_triangles(nodes)`（Delaunay）、`layered_triangles(x_min, x_max, nx, y_min, y_max, ny, as_mesh=False)`、
`mesh3_from_triangles(faces, nodes, i_beg=0)`、`create_ring(vr, angle_step, z=0.0)`、
`load_trimesh(node_file, triangle_file, i_beg=0)`、`filter_mesh(mesh, keep)`、
`remove_orphan_nodes/links/faces(mesh)`、
`generate_circle_mesh_improved(r, l, center=(0,0), ...)` / `analyze_mesh_quality(...)`。

### zmlx/geometries/ —— 几何

`get_distance(p0, p1)`、`get_angle(x, y)`、`get_norm(p)`、`get_center(p1, p2)`、
`get_seg_angle(x0, y0, x1, y1)`、`seg_intersection(ax, ay, bx, by, cx, cy, dx, dy)`、
`seg_point_distance(seg, point)`、`triangle_area(a, b, c)`（三边长）、
`dfn2(...)` / `dfn_v3(...)`（⚠️ **要从子模块导入**）、`get_length(fracture)`、`get_total_length(fractures)`、
`create_links(fractures)`、`from_segs(segs, z_min, z_max, heights)`、`to_rc3(fractures)`、
`save_c14(path, fractures)`。

### zmlx/utils/ —— 高层工具

| 名字 | 签名 | 说明 |
|---|---|---|
| `Field` / `LinearField` | `Field(value)` / `LinearField(x0=0, y0=0, z0=0, v0=0, dx=0, dy=0, dz=0)` | 空间场（可直接传给 `create`） |
| `GuiIterator` | `GuiIterator(iterate=None, plot=None, info=None, ratio=None, figure_caption=None, max_plot_interval=None, gui_only=None)` | 自适应"迭代 + 绘图"控制器（绘图耗时 ≤ 迭代 × ratio，默认 0.2） |
| `get_gui_iter` | `get_gui_iter(...)` | 取全局单例 |
| `SaveManager` | `SaveManager(folder=None, dtime=None, get_time=None, save=None, ext=None, time_unit=None, always_save=True)` | 周期性自动存盘 |
| `SeepageCellMonitor` | `SeepageCellMonitor(get_t, cell)` | 监测 Cell 质量变化（产量 / 产率 / 绘图 / 存盘） |
| `PressureController` | `PressureController(cell, t, p, modify_pore=False)` | 按时间-压力曲线控压 |
| `CapillaryEffect` | `CapillaryEffect(fid0, fid1, s2p=None)` | 两相毛管力驱动交换 |
| `HeatInjector` | `HeatInjector(cell, ca_mc, ca_t, power=None, temp=None, cond=None)` | 恒功率 / 恒温注入 |
| `FrameRateCtrl` | `FrameRateCtrl(update=None, rate=20)` | 帧率限制器 |
| `AttrKeys` | `AttrKeys(*args, path=None)` | 属性名 → int 映射（访问即注册，可存 JSON） |
| `Interp2` / `Interp3` | `Interp2(x, y, v, rescale=True)` / `Interp3(x, y, z, v, rescale=True)` | 散点插值（scipy，逐级降级） |
| `load_field3` | `load_field3(filename)` | 读 txt（每行 `x y z v`）→ `Interp3` |
| `RuntimeFunc` | `RuntimeFunc(pack_name, func_name, deprecated_name=None, deprecated_date=None)` | 延迟加载函数 |

### zmlx/io/ + zmlx/algs/ —— 文件与工具

| 函数 | 签名 | 说明 |
|---|---|---|
| `opath` / `get_path` | `get_path(*args, tag=None, key=None)` | 输出路径。⚠️ 路径含中文 / 有异常时**返回 `None`**（不抛） |
| `set_path` | `set_path(folder=None, tag=None, key=None)` | 设置工作目录 |
| `json_ex.write` / `json_ex.read` | `write(path, obj, indent=2)` / `read(path, encoding=None, default=None)` | JSON 读写（读失败返回 `default`） |
| `load_txt` / `load_col` | `load_txt(*args, **kwargs)` / `load_col(fname=None, index=0, ...)` | 读表（**返回 list**，不是 ndarray） |
| `read_py` / `write_py` | `read_py(path=None, ...)` / `write_py(path, data=None, **kwargs)` | Python 格式的数据文件 |
| `TaskFolder` | `TaskFolder(*names)` | 带时间戳的任务目录 |
| `linspace` | `linspace(start, stop, num=50)` | 等间距（⚠️ **不含终点**，与 numpy 不同） |
| `clamp(value, left, right)` / `time2str(s)` / `mass2str(kg)` / `fsize2str(size)` | | 数值与格式化 |
| `join_paths(a, b)` / `join_cols(*args)` / `join_rows(*args)` | | 路径与数组拼接 |
| `list_files(path, keywords, exts)` / `get_latest_file(folder)` / `prepare_dir(folder)` | | 文件系统 |
| `apply_async(tasks, processes=None)` / `create_async(func, args, kwds)` | | 多进程并行（⚠️ `func` 必须是**全局函数**） |
| `interp1(x, y, xq, kind='linear')` | | 一维插值（类似 Matlab） |

### zmlx/plt/ —— 绘图

**三层结构**：`on_axes`（`add_*`，第一个参数是 `ax`）→ `on_figure`（`plot_on_figure` / `plot_on_axes`）
→ `on_ui`（`show_*`，一键出图）。

| 类别 | 函数 |
|---|---|
| 入口 | `plot_on_figure(kernel, ...)`、`plot_on_axes(on_axes, dim=2, ...)`、`add_subplot(fig, ...)`、`add_axes2` / `add_axes3`、`AutoLayout(fig, num_plots)` |
| 加到坐标轴 | `add_curve(ax, ...)`、`add_contourf(ax, ...)`、`add_tricontourf(ax, ...)`、`add_trisurf(ax, ...)`、`add_surf(ax, x, y, z, c)`、`add_field2(ax, f, xr, yr)`、`add_scatter(ax, ...)`、`add_fn2(ax, pos=, w=, c=)`、`add_dfn2(ax, dfn2)`、`add_rc3(ax, rc3)`、`add_legend`、`add_cbar` |
| 一键出图 | `show_xy(x, y, ...)`、`show_contourf(x, y, z, ...)`、`show_tricontourf(x, y, z, ...)`、`show_trisurf(...)`、`show_trimesh(triangles, points)`、`show_scatter(...)`、`show_field2(f, xr, yr)`、`show_dfn2(dfn2)`、`show_fn2(pos, w, c)`、`show_rc3(rc3)`、`show_flu_def(flu, pr, tr)` |
| 辅助 | `set_chinese_font()`、`get_cm(name, levels)`、`get_color(cmap, lr, rr, val)`、`set_plt_save_path(path)` |

⚠️ `show_*` 通过 `zmlx.ui.plot` 出口：**GUI 开标签页、无头存文件**。

### zmlx/fig/ —— 声明式绘图

先构造"绘制意图"，再一次性渲染：

```python
import zmlx.fig as fig
fig.show(
    fig.axes2(fig.contourf(x, y, p, cbar={'label': 'p/Pa'}),
              title='压力', xlabel='x/m', ylabel='y/m'),
    caption='压力分布',
)
```

原语 `item(name, *args, **kwargs)`；坐标轴元素 `fig.contourf / tricontourf / curve / scatter /
surface / trimesh / fn2 / dfn2 / rc3 / colorbar / text / xlabel / title / view_opts / aspect /
xlim / ylim / legend / grid`；图元素 `fig.subplot / axes2 / axes3 / auto_layout / tight_layout / suptitle`。

### zmlx/system/ —— 基础服务

| 函数 | 签名 | 说明 |
|---|---|---|
| `app_data` | 单例 | `getenv` / `setenv`（**落盘**）、`get` / `put`（内存）、`root()` / `temp()` / `proj()`、`get_paths()` / `find()` / `find_all()`、`add_tag_today()` |
| `is_headless()` | | 无头模式判定：命令行 → `app_data` → 环境变量 |
| `execute_once(func=None, *, name=None, file=None)` | | "只执行一次"装饰器 |
| `first_execute(name, key=None)` | | 是否首次执行 |
| `warn(message, category=None, stacklevel=1, tag=None)` | | **zmlx 统一的警告入口**（额外记日志，同 tag 当天只记一次） |
| `log(text, tag=None)` | | 记日志 |
| `deprecated(func=None, *, remove_after=None, alternative=None)` | | 弃用装饰器 |
| `read_text` / `write_text` | `read_text(path, encoding=None, default=None)` / `write_text(path, text=None, encoding=None)` | 文本读写（写是原子的） |
| `make_dirs` / `make_parent` / `get_hash` | | 目录与哈希 |
| `SelfPath` | `SelfPath(this_file)` | `get_path = SelfPath(__file__)` 的实现 |
| `in_windows` / `in_linux` / `in_macos` | | 平台判定 |

### zmlx/scen/ —— 应用场景

⚠️ `zmlx/scen/__init__.py` **不导出任何东西**，要显式 `from zmlx.scen import hydrate`。
顶层 `zmlx` 只预导入了 `hydrate` 与 `icp`。

**`scen/hydrate/`（水合物，最完整的场景）**

| 函数 | 签名 | 说明 |
|---|---|---|
| `create` | `create(**opts)` | **主入口**：内部 = `create_opts()` + `tfc.create()` |
| `create_opts` | `create_opts(has_co2=False, has_steam=False, has_inh=False, has_ch4_in_liq=False, has_co2_in_liq=False, gr=None, gravity=None, dt_max=None, ...)` | 返回可直接喂给 `tfc.create` 的 dict（默认 `dt_max=86400`、`gravity=[0,-10,0]`、`gr=create_krf(as_interp=True)`） |
| `create_fludefs` | `create_fludefs(has_co2=False, has_steam=False, has_inh=False, ...)` | 返回 `[gas, liq, sol]` 三个 `FluDef` |
| `create_reactions` | `create_reactions(has_co2=False, ..., sol_dt=None)` | 反应列表（水合物 + 冰 + 蒸汽 + 溶解） |
| `create_t_ini` / `create_p_ini` | `create_t_ini(z_top=0.0, t_top=276.0, grad_t=0.04466)` / `create_p_ini(z_top=0.0, p_top=12e6, grad_p=0.01e6)` | 线性初始场 |
| `create_denc_ini` / `create_fai_ini` | `create_denc_ini(z_min, z_max, denc=3e6)` / `create_fai_ini(*, z_max, fai=0.2)` | 用超大 `denc` / 超大孔隙度做**等温 / 等压边界** |
| `solve` | `solve(*args, **opts)` | 转发 `tfc.solve` |
| `show_2d_v2` | `show_2d_v2(model, caption=None, dim0=None, dim1=None, ...)` | 多子图（温度 / 压力 / 饱和度） |

**`scen/icp/`（页岩油原位转化）**：`create(fludefs=None, reactions=None, **opts)`、
`create_fludefs()`、`create_reactions(temp_max=None)`、`solve(...)`、`show_xz(model, ...)`、
`find_by_day(folder, day)` / `find_by_year(folder, year)`。

**其它场景**：`scen/frac`（裂缝网络）、`scen/helium`（氦气）、`scen/quick_look`（快速评估）、
`scen/mineralization_reactor`（需要 Reaktoro）、`scen/geothermal_helium`、`scen/uv_equilibrium`、
`scen/rkt` —— 多数是实验性或论文复现代码，API 不稳定。

⚠️ `scen/` 下只有 `easter_eggs` 是「包自己就是一个插件」的子包（2026-10-22）：
`zml_plugin.py` 与两个游戏模块放在同一个包里，默认不启用，挂「帮助 → 彩蛋」。
其它场景只是在包根放一个 `zml_plugin.py` 当入口（`quick_look` / `frac`），实现仍在各处。
⚠️ 数据编辑器一度也是这种形态（`scen/editors/`），同一天取消了 —— 控件退回
`zmlx/ui/widgets/editors/`，装配合成 `zmlx/ui/plugins/builtin/editors.py` 一个文件。
'''),

        E('gui', '图形界面（zmlx/ui/）', '''\
[`zmlx/ui/`](zmlx://doc/zmlx/ui/) 是基于 **PyQt6**（自动降级到 PyQt5）的完整界面系统：
多标签页、代码编辑器、控制台（后台线程跑脚本）、绘图页、文件浏览、环境变量、登录、反馈……

### 入口怎么写

界面程序的入口**只有一条规矩**：

> `gui.execute(main, close_after_done=False)` **只**出现在 `if __name__ == '__main__'` 里。

放进函数里会导致嵌套执行，行为不可预期。

```python
from zmlx.ui import gui


def main():
    ...                       # 用户点了"运行"之后跑的就是这里


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
```

长循环里记得放 `gui.break_point()` —— 它让「暂停 / 终止」按钮有机会生效。

### 无头模式

```bash
python script.py --no-gui       # 命令行模式
python script.py --headless     # 等效
```

**无头模式由 `gui.execute()` 内部自动识别**，不需要手工判断。此时：

- `gui.break_point()` / `gui.progress()` / `gui.information()` / `gui.show_attrs()`
  **全部自动变成空操作**，不必写 `if gui.exists()`；
- `plot()` 把图**保存到文件**而不是弹窗。

⚠️ 例外：`gui.question()` 在无头模式下**退化为 `input()`**，会阻塞等待输入 —— 脚本里别乱用。

### 目录怎么分

| 位置 | 收什么 |
|---|---|
| [`zmlx/ui/pyqt.py`](zmlx://doc/zmlx/ui/pyqt.py) | **Qt 绑定层**：自动选 PyQt6 / PyQt5，并把选择"钉死"防止两套绑定混用 |
| `zmlx/ui/gui_buffer.py` | 全局 `gui` 单例：把 `gui.xxx()` 派发到 GUI 线程 |
| [`zmlx/ui/main.py`](zmlx://doc/zmlx/ui/main.py) | `MainWindow`：菜单、工具栏、标签容器、控制台 |
| `zmlx/ui/utils/` | 界面工具包（`GuiApi` 跨线程调用、`BreakPoint`、共享容器……） |
| `zmlx/ui/widgets/` | **底层控件**：会被别的控件当作零件用（编辑器、Markdown 视图、图表……） |
| `zmlx/ui/tabs/` | **顶层控件**：只被打开成一个标签页，不被任何控件复用 |
| [`zmlx/ui/extra_setups/`](zmlx://doc/zmlx/ui/extra_setups/) | **额外菜单动作**：新增菜单项放这里，**不动 `main.py`** |
| [`zmlx/ui/plugins/`](zmlx://doc/zmlx/ui/plugins/) | **插件机制**（发现 / 记录状态 / 执行 `zml_plugin.py`），内置插件在 `builtin/` 子目录 —— 用户能关掉的功能放那里 |

### 控件分两处，判据只有一条

> **这个控件会不会被别的控件当作零件（子控件）用？**
> 会 → `widgets/`；不会（只被打开成标签页）→ `tabs/`。

依赖方向是**单向**的：`tabs/` 可以用 `widgets/`，反过来不行。

### 最常用的几个 `gui.*`

| 调用 | 作用 |
|---|---|
| `gui.break_point()` | 暂停 / 终止检查点 |
| `gui.progress(label, val_range, value)` | 进度条 |
| `gui.information(title, text)` | 信息对话框 |
| `gui.question(text)` | 是 / 否询问（⚠️ 无头模式下会 `input()`） |
| `gui.show_attrs(**attrs)` | 在输出面板显示动态变量 |
| `gui.status(text, 3000)` | 状态栏提示 |
| `gui.get_widget(...)` | 打开（或切到）一个标签页 —— **同一类型 + 同一标题只开一个** |
| `gui.add_func(name, fn)` | 注册一个命令，之后 `gui.name()` 就能调 |
| `gui.add_action(...)` | 往菜单加一项 |
| `gui.add_action(menu='操作', text='---')` | **插一条分隔线**（`text='---'` 是分隔符的专用写法，其余参数都不用给；2026-10-26 加） |

⚠️ **分隔符只能加在菜单里**：`text='---'` 不建 action、不带名字、不判重（连插两条就是两条线），
`on_toolbar=True` 对它**不生效** —— 想给工具栏分隔，仍要自己 `QToolBar.insertSeparator`。

### 三条最容易踩的界面规矩

1. **切标签页会调用当前页的 `refresh()`** —— 里面不能读磁盘、联网、重画大图（会"顿一下"），
   慢活要放后台线程，结果用信号回主线程；
2. **新界面元素默认不在 `__init__.py` 转发** —— 按子模块路径导入，避免导入期副作用与循环导入；
3. **后台线程不设 parent + 用模块级列表持有强引用** —— 两条缺一不可，否则关标签页时进程
   直接崩（不是异常，是退出码 `0xC0000409`）。

完整的控件清单见 [`zmlx/ui/ReadMe.md`](zmlx://doc/zmlx/ui/ReadMe.md)；
写新控件前先看 [`zmlx/ui/widgets/AGENTS.md`](zmlx://doc/zmlx/ui/widgets/AGENTS.md) 与
[`zmlx/ui/tabs/AGENTS.md`](zmlx://doc/zmlx/ui/tabs/AGENTS.md)。
''', ('gui_map', '主窗口的结构：每个区域里有什么', 900, 900)),

        E('gui_map', '界面地图：菜单通向哪里', '''\
下表的**菜单路径可以点** —— 点它等于真的去点那个菜单项（在仿真运行时那几项会置灰，
与菜单本身的行为一致）。

### 五个顶层菜单

⚠️ 2026-10-19：原先的顶层「用户」菜单已**整体并入「帮助」**，菜单栏回到五个顶层菜单；
并且**没有任何三级菜单**（2026-10-24 起「查询」子菜单已并入「用户」；2026-10-26 起
「文件 → 浏览」**有一个子菜单**，仍是两级，见下）。

### 文件

⚠️ 2026-10-26：「浏览」与「图片浏览」合并成一个**子菜单**「文件 → 浏览」，其下两项
「工作目录」（原「文件 → 浏览」）与「图片」。两者都是「看文件」的入口，原先却分在两处
（图片浏览还是插件提供的、可被关掉）—— 现在同进同出。

⚠️ **其余条目保持原本顺序**（2026-10-26 核对过历史版本）：唯一调整是把「退出」放回
**末尾** —— 它在历史版本里一直在最后，是 2026-10-07 加入导入 / 保存 / 导出时被夹到了
「脚本」后面。

| 菜单路径 | 快捷键 | 打开什么 |
|---|---|---|
| 文件 → 工作路径 | `Ctrl+W` | 选择工作目录（**所有相对路径的基准**，开工前先设好） |
| 文件 → 打开 | `Ctrl+O` | 按扩展名分发：`.py` 进代码编辑器、`.txt/.json` 进文本编辑器、`.png/.jpg` 进图片查看、`.pdf` 进内置浏览器（**由插件 `pdf_view` 提供**，可关闭） |
| 文件 → 新建 | `Ctrl+N` | 新建各类文件 |
| 文件 → 脚本 | | 打开工作目录下的 `temp_code.py` |
| 文件 → 保存 / 导入 / 导出 | `Ctrl+S` / — / `Ctrl+Shift+S` | **作用于当前标签页**（这一页有 `save_file` 才亮） |
| 文件 → 退出 | | 关窗口（内核在跑时会先问一句） |
| ▸ 文件 → 浏览 → [图片](zmlx://gui/show_image_browser) | | 左侧缩略图相册 + 右侧大图的图片浏览器（「图片浏览」插件提供） |
| ▸ 文件 → 浏览 → [工作目录](zmlx://gui/view_cwd) | `Ctrl+B` | 当前目录的文件列表（「小型查看器」插件提供：双击打开文件，含子文件夹） |

⚠️ 上面那张表按**真实显示顺序**写：`工作路径 → 打开 → 新建 → 脚本 → 导入 → 保存 → 导出 →
退出`，最后才是**子菜单**「▸浏览」（``get_menu`` 让子菜单永远排在所有普通条目之后）。
子菜单内部按**登记先后**排 —— ``builtin/`` 按文件名加载，``image_browser.py``（i）先于
``viewers.py``（v），所以「图片」在「工作目录」之前。

### 显示

⚠️ 2026-10-26：「刷新」已从「显示」**移到「操作」** —— 它是动作，而这一组收的是页面入口。

| 菜单路径 | 打开什么 |
|---|---|
| 显示 → 变量 | 全局变量查看器（`app_data`） |
| [显示 → 重置布局](zmlx://gui/reset_layout) | 把**右侧栏**的宽度与显示状态恢复成默认（2026-10-26 加）。⚠️ **不动窗口大小、不动样式表**，已打开的标签页也不受影响 |
| 显示 → 耗时 | CPU 计时统计表 |
| 显示 → 标签列表 | 已开标签页总览（开在**右侧栏**） |
| 文件 → 浏览 → 图片 | 左侧缩略图相册 + 右侧大图的图片浏览器 |
| 显示 → 通知(N) | 通知中心（**有消息时才出现**） |

### 操作

| 菜单路径 | 快捷键 | 打开什么 |
|---|---|---|
| 操作 → 刷新 | | 重设标题、刷新当前页、刷新所有菜单项的灰/亮状态 |
| 操作 → 运行 | `Ctrl+R` | 执行当前标签页的代码（在**后台线程**里跑） |
| 操作 → 暂停 | `Ctrl+Shift+P` | 暂停（**需要脚本里调了 `gui.break_point()`**） |
| 操作 → 继续 | `Ctrl+Shift+R` | 继续（同样需要 `break_point`） |
| 操作 → 停止 | `Ctrl+Q` | 安全终止（同样需要 `break_point`） |
| 操作 → 强制结束 | | 直接 `terminate()` 线程（可能丢结果） |
| 操作 → 隐藏 / 显示 | `Ctrl+H` | 右侧栏（输出面板）的显示与隐藏（两项**共用** `Ctrl+H`：任一刻只有一项可用） |
| 操作 → 再次运行 | `F5` | 重跑上一次执行的脚本 |
| 操作 → 关闭所有页面 | | 关掉顶部所有标签页 |
| 操作 → 播放图片 | | 顺序播放当前目录的图片 |

⚠️ **2026-10-26 快捷键调整**（原先三处互相顶掉）：`运行` 与 `继续` 都写 `Ctrl+R`、
`继续` 与 `再次运行` 都写 `Ctrl+Shift+R`，Qt 遇到重复快捷键时触发哪个**不确定**。
现在：`运行`=`Ctrl+R`、`暂停`=`Ctrl+Shift+P`、`继续`=`Ctrl+Shift+R`、`停止`=`Ctrl+Q`、
`再次运行`=`F5`。`暂停` 原先**没有**快捷键，这是新补的。

### 设置

| 菜单路径 | 快捷键 | 打开什么 |
|---|---|---|
| [设置 → 系统](zmlx://gui/show_env_edit) | `Ctrl+E` | 环境变量 / 配置表单 |
| [设置 → 插件](zmlx://gui/edit_setup_files) | | 插件脚本列表（`zml_plugin.py`，**启动时自动执行**） |
| [设置 → 路径](zmlx://gui/show_file_finder) | | 应用搜索路径管理 |
| [设置 → 求解器](zmlx://gui/show_solver_selector) | | 默认线性求解器配置 |
| [设置 → 迭代器](zmlx://gui/show_gui_iter) | | 迭代耗时曲线 + 绘图频率参数 |
| [设置 → 样式表](zmlx://gui/show_style_sheet) | | QSS 可视化编辑器（调字体、配色） |
| 设置 → 运行环境 | | 检查第三方依赖，缺的可以一键安装 |

### 帮助

**登录 / 反馈**是高频操作，直接放在「帮助」**一级**；账号管理与两个在线记录页
（管理 / 登录记录 / 反馈记录）收在**唯一的**「用户」子菜单里，其余是文档类条目。

⚠️ **2026-10-26 顺序回到「原本的」**：`关于` 回到最上面，其余沿用一级的登录 / 反馈 ——
即 **关于 → ReadMe → 登录 → 反馈 → ▸用户 → 示例 / 其它**。上一版（2026-10-24）把
`关于` 挪到了 ReadMe 之后，与更早的历史（`ReadMe → 关于 → 示例`）不一致，这次改回。

⚠️ **2026-10-24 结构调整**：`登录` / `反馈` 从「用户」子菜单**提到一级**（高频操作
不该点两下），`查询` 子菜单**并入「用户」**（「查记录」与「管账号」本来不是两层概念）
⇒ 现在**只剩一个子菜单**，仍是两级、没有任何三级菜单。

⚠️ **子菜单永远排在所有普通条目之后**（2026-10-26 定）：`get_menu` 新建子菜单时把它归到
末尾、`add_action` 每次挂完条目再归位一次 —— 所以「▸用户」「▸其它」「▸浏览」总在最后一组。
「示例」是**插件**在启动后才挂的，位置由「插件注册」与「子菜单归位」的先后决定
（默认加载下它在「架构」之后，见下方「结构」）。

历史：2026-10-19 原先**独立的顶层「用户」菜单整体并回了「帮助」**（菜单栏因此少一个
顶层菜单），原先的 `用户 → 查询 → X` 变成 `帮助 → 查询 → X`；同日两个子菜单下移到
文档类条目之后（原先排在最前面，太抢眼）。

结构（两级，即菜单里的实际先后；默认插件全开时的实测顺序）::

    帮助 ─┬─ 关于
          ├─ ReadMe
          ├─ 登录
          ├─ 反馈
          ├─ 示例        ← 插件「示例浏览」注册（晚于骨架，落在「架构」前后）
          ├─ 架构        ← extra_setups 注册
          ├─ ▸ 其它 → 生成测试数据 …（插件「数据编辑器」）
          └─ ▸ 用户 → 管理 · 登录记录 · 反馈记录

| 菜单路径 | 快捷键 | 打开什么 |
|---|---|---|
| [帮助 → ReadMe](zmlx://gui/show_readme) | `F1` | 软件说明：安装、登录、反馈、隐私 |
| [帮助 → 关于](zmlx://gui/show_about) | `Ctrl+Shift+A` | 版本、安装路径、Python / Qt 版本、登录状态 |
| [帮助 → 示例](zmlx://gui/show_demo) | | Demo 浏览器（110 个可运行算例） |
| [帮助 → 登录](zmlx://gui/show_reg_tool) | | 邮箱验证码登录 |
| [帮助 → 反馈](zmlx://gui/show_feedback) | | 给作者提交反馈 |
| [帮助 → 用户 → 管理](zmlx://gui/show_user_admin) | | 按用户查看并修改授权的到期日与功能清单（**仅管理员**；非管理员只看到自己的信息与一条出路） |
| [帮助 → 用户 → 登录记录](zmlx://gui/show_check_count_view) | | 某邮箱的查询次数（按天柱状图，**要联网**） |
| [帮助 → 用户 → 反馈记录](zmlx://gui/show_feedbacks_view) | | 某用户某天的反馈内容（**要联网**） |
| [帮助 → 架构](zmlx://gui/show_architecture) | | **就是本页** |

### 插件的菜单（默认大多不加载）

⚠️ **「帮助 → 加载」这一层已经空了**（2026-10-18）：原来它下面的 `Admin功能`、
`Editors`、`Seepage功能` 三项都是「点一下才生成子菜单」，现在全部做成了**插件**。

插件一被执行菜单就**当场出现**，不需要再点「加载」。当前 `plugins/builtin/` 里的：

| 插件 | 菜单 | 默认 |
|---|---|---|
| `image_browser` | 文件 → 浏览 → 图片 | **启用** |
| `vtk_view` | 帮助 → VtkView | 不加载 |
| `zip_files` | 操作 → 零碎文件处理 | 不加载 |
| `admin_menu` | 操作 / 帮助 / 帮助→打开 / 帮助→显示 共 14 条 | 不加载 |

⚠️ 2026-10-22 起，原来的 `tetris` + `lianliankan` **合并成一个插件**
`zmlx/scen/easter_eggs/`（彩蛋，默认**不启用**）：一个开关，「帮助 → 彩蛋」下两项
（连连看 / 螺螺是方块）。它也**不在** `plugins/builtin/` 里。

⚠️ 2026-10-22 起，原来的 `editors_menu` + `seepage_menu` **合并成一个插件**
`builtin/editors.py`（数据编辑器，默认**启用**）：它同时注册 7 种文件类型
（「文件 → 打开 / 新建」）与「帮助 → 其它 → 生成测试数据」下 6 条示例数据
（2026-10-25 由「文件 → 生成测试数据」下沉到「帮助 → 其它」下 —— 造示例是调试入口，
不是日常的文件操作）。
⚠️ 它曾一度住进 `zmlx/scen/editors/`（「包自己就是一个插件」），同日取消：控件退回
`ui/widgets/editors/`，装配只剩这一个文件。

⚠️ **想用哪个就去「设置 → 插件」里勾上，然后重启** —— 没勾的插件，它那些菜单项
在界面上根本不出现。

### 窗口里还有什么

- **工具栏**：文件（工作路径 / 打开 / 新建 / 保存 / 导出）、操作（运行 / 暂停 / 停止）、
  帮助（ReadMe / 示例）、显示（通知）；
- **状态栏右侧**四个常驻控件（从左到右）：**运行状态灯**（○ 空闲 / ● 运行中 /
  ⏸ 已暂停，2026-10-26 加；**点它会显示控制台**，等价于 `gui.show_console()`）、
  **并行**复选框（内核的 for 循环是否并行化，
  2026-10-26 由「内核并行」简化）、**版本号**按钮（→关于）、
  **登录状态**按钮（→登录页）；
- **标签栏右键**：关闭所有 / 列出标签 / 重命名 / 关闭 / 关闭其它；
- **控制台**（右侧栏）：可以直接敲任意 `gui.xxx()` 命令，见 [命令与控制台](#gui_cmds)。
  ⚠️ 右侧栏与顶部标签页区之间是一条**可拖动的分隔条**：宽度、以及「上次是否显示」
  都会在关窗时记住、下次启动恢复（2026-10-26）。

### 本页链接的三种去向

1. **「菜单名」** → 等于点那个菜单项；
2. **目录名**（如 `zmlx/tfc/`）→ 打开该目录的文档，没有文档就打开 `__init__.py`；
3. **文档名 / 源码文件名** → Markdown 用阅读视图打开，源码用代码编辑器打开（可直接改、直接运行）。

### 一个很少有人注意的细节

菜单项的**可见性默认跟随"是否可点"**：所以"运行中置灰"那些项实际上是**消失**了，不是变灰。
只有「工作路径」「打开」两项显式写了"永远可见"，它们在运行中是真的**变灰**。
'''),

        E('gui_cmds', '命令与控制台', '''\
界面上每一个菜单项背后都有一个**命令名**，用 `gui.<命令名>()` 就能调用 —— **两者完全等价**。
在界面底部的控制台里直接敲即可。

### 命令表是怎么填满的

`MainWindow` 在初始化时会做两件事：

1. **自动注册所有公开方法** —— `MainWindow` 上任何不以 `_` 开头的函数**都会立刻变成一个
   `gui.xxx` 命令**；
2. 再手工补一批**别名**与**转接**（例如 `gui.status` → `show_status`、`gui.resize` → Qt 自己的
   `resize`、`gui.set_style_sheet` → `setStyleSheet`）。

⚠️ 这带来一个直接影响：**给 `extra_setups` 加命令时，名字不能与 `MainWindow` 的公开方法撞车**,
否则会把那个方法悄悄顶掉。

### 打开页面

```python
gui.show_architecture()                  # 本页
gui.show_architecture('data_model')      # 直接跳到"核心数据模型"
gui.show_readme()                        # 帮助 → ReadMe
gui.show_demo()                          # 帮助 → 示例
gui.show_about()                         # 帮助 → 关于
gui.show_reg_tool()                      # 帮助 → 登录
gui.show_env_edit()                      # 设置 → 系统
gui.show_gui_iter()                      # 设置 → 迭代器
gui.show_style_sheet()                   # 设置 → 样式表
gui.show_solver_selector()               # 设置 → 求解器
gui.show_file_finder()                   # 设置 → 路径
gui.edit_setup_files()                   # 设置 → 插件
gui.view_cwd()                           # 文件 → 浏览 → 工作目录
gui.show_changelog()                     # 修改记录
gui.show_memory()                        # 显示 → 变量
gui.show_timer()                         # 显示 → 耗时
gui.show_image_browser()                 # 文件 → 浏览 → 图片
gui.show_check_count_view()              # 帮助 → 用户 → 登录记录
gui.show_feedbacks_view()                # 帮助 → 用户 → 反馈记录
```

### 打开文件

```python
gui.open_file('C:/path/to/model.seepage')   # 按扩展名自动选打开方式
gui.open_code('C:/path/to/demo.py')         # 用代码编辑器打开（可以直接运行）
gui.open_text('C:/path/to/data.txt')        # 用文本编辑器打开
gui.open_image('C:/path/to/pic.png')        # 用图片查看器打开
gui.open_url('https://gitee.com/geomech/hydrate')
```

### 通用开页

```python
gui.get_widget(the_type=SomeWidget, caption='标题', on_top=True, icon='info')
gui.get_widget(the_type=MarkdownView, caption='说明', on_top=True,
               oper=lambda w: w.set_markdown(text))
gui.show_text_in_tab('一段文本', caption='标题')
gui.show_string_table(['a', 'b', 'c'], caption='表')
```

`oper` 是"每次调用都会执行"的回调 —— ⚠️ 点菜单也会执行，所以里面**不要放有副作用的动作**
（比如刷新），否则就变成"点一次菜单重刷一次"。

### 状态与对话框

```python
gui.status('已保存', 3000)               # 状态栏提示 3 秒
gui.information('标题', '正文')           # 信息框
gui.question('确定吗？')                  # 是 / 否（⚠️ 无头模式下会 input()）
gui.progress('求解中', [0, 100], 42)      # 进度条
gui.show_attrs(time=t, dt=dt, p=p)       # 在输出面板显示动态变量
gui.title('新标题')                       # 改窗口标题
```

### 跨线程与内核控制

```python
gui.break_point()        # 暂停 / 终止检查点（无头模式下空操作）
gui.is_running()         # 是否有脚本在跑
gui.start_func(code)     # 在控制台线程里执行代码
gui.command('some_func', arg)   # 派发任意命令（返回值与异常都能带回）
```

### 注册自己的命令与菜单项

```python
gui.add_func('my_command', my_function)     # 之后 gui.my_command() 可用
gui.add_action(menu='显示', name='my_view', text='我的面板',
               slot=show_my_view, overwrite=False)
```

### 不知道有哪些命令？

在控制台里跑：

```python
print(gui.list_all())          # 所有命令名
print(gui.list_actions())      # 所有菜单项的名字
```

或者在「设置 → 插件」里启用 **Admin 功能**、重启后打开
**帮助 → 显示 → 命令列表**，会弹出一个表格。
'''),

        E('reading', '如何阅读源码（推荐路线）', '''\
给新读者的三条路线。**共同的第一步都是"先跑一个 demo"** —— 能跑起来，才知道每一步在算什么。

### 路线 A：只想用（改参数、跑算例）

1. 打开 [「帮助 → 示例」](zmlx://gui/show_demo)，挑一个与你的问题最像的例子；
2. 点运行，看输出与成图；
3. 在代码编辑器里改参数（渗透率、边界压力、井位），再跑一次。

### 路线 B：要建模（写自己的算例）

按 **demo → scen → tfc** 的顺序往前追：

1. 在 [`zmlx/demos/`](zmlx://doc/zmlx/demos/) 里找到最接近的示例，看它怎么 `create`、
   怎么设边界、怎么 `solve`；
2. 看它调用的场景函数（[`zmlx/scen/`](zmlx://doc/zmlx/scen/) 里的 `hydrate` / `icp`）内部
   怎么组装 `Seepage`；
3. 需要理解"为什么这一步要这样设"时，进 [`zmlx/tfc/`](zmlx://doc/zmlx/tfc/) 看
   `seepage.iterate()`。

配套的建模指南：[`zmlx/demos/ReadMe.md`](zmlx://doc/zmlx/demos/ReadMe.md) 与
[`zmlx/ReadMe.md`](zmlx://doc/zmlx/ReadMe.md)。

### 路线 C：要改内核行为（改物理过程）

1. 先确认**能不能在 Python 侧解决**：多数"新反应 / 新物性"只需要
   [`zmlx/fluids/`](zmlx://doc/zmlx/fluids/) + [`zmlx/reactions/`](zmlx://doc/zmlx/reactions/)
   的组合，不需要碰 C++；
2. 确实要改迭代策略 → [`zmlx/tfc/`](zmlx://doc/zmlx/tfc/)（这是 Python 侧的耦合层，
   鼓励在这里改）；
3. 确实要改 C++ → 联系作者（`zml/` 不在本仓维护）。

### 一条最重要的经验

> **从 demo 往前追，而不是从 `__init__` 往后读。**

[`zmlx/__init__.py`](zmlx://doc/zmlx/__init__.py) 只是把两百多个名字摆到顶层，信息量不大；
而每个 demo 都是一条完整的、能跑的调用链。

### 读代码时的三个抓手

| 想搞清楚 | 抓手 |
|---|---|
| 某个函数在哪 | 全仓搜名字；本页 [API 速查](#api) 里也按包列了 |
| 某个类的字段 | [核心数据模型](#data_model)；或直接看 `zmlx/exts/_seepage.py` |
| 为什么这样写 | 本仓的 docstring 是**中文写的、非常详细**，很多坑都记在里面 —— 先读 docstring |

### 顺手可以用的工具

- [「设置 → 迭代器」](zmlx://gui/show_gui_iter)：跑 demo 时打开，能看见每一步耗多久；
- [「文件 → 浏览 → 工作目录」](zmlx://gui/view_cwd)：确认相对路径的基准；
- 控制台：`gui.show_architecture()` 随时回到本页。
''', ('reading', '三条阅读路线', 900, 900)),

        E('run', '运行与测试', '''\
### 三种运行方式

```bash
python zmlx/demos/flow_1ph/darcy_1d.py            # ① GUI 模式（默认）
python zmlx/demos/flow_1ph/darcy_1d.py --no-gui   # ② 无头模式（图存到文件）
python -m zmlx ui                                  # ③ 打开空界面
```

| 方式 | 行为 |
|---|---|
| GUI 模式 | 开界面，`gui.*` 全部生效，`plot()` 在标签页里出图 |
| 无头模式 | 不开界面，`gui.*` 全部变空操作，`plot()` 把图**写进文件** |
| `python -m zmlx ui` | 直接打开界面（等于双击 `zml_ui.pyw`） |

论文 / 服务器上跑用**无头模式**；调试用 GUI 模式（可以随时暂停）。

### 其它命令行子命令

```bash
python -m zmlx ui       # 打开界面
python -m zmlx demo     # 打开界面并停在「示例」页
python -m zmlx test     # 无头模式跑全部 demo
python -m zmlx env      # 安装依赖
python -m zmlx ver      # 显示版本信息
python -m zmlx help     # 帮助
```

### 批量测试

```bash
python zmlx/demos/test_all_demos.py [--jobs N] [--timeout N] [--verbose]
```

它把每个 demo 以 `--no-gui` 起**独立子进程**跑一遍，最后汇总成 `test_report.log`。

| 选项 | 默认 | 含义 |
|---|---|---|
| `--jobs N` | CPU 核心数 | 并发数 |
| `--timeout N` | **60 秒** | 单个 demo 超时；超时记为 **TIMEOUT，不算失败** |
| `--verbose` | 关 | 额外打印每个 demo 输出的最后 2 行 |

**耗时很长**（十几分钟起）。快速跑一遍用 `--timeout 30`，想仔细测用 `--timeout 500`。

⚠️ 它**自己不吃 `--no-gui`** —— 它给每个子 demo 硬编码传了这个参数，外层加没效果。

### 交互式调试：暂停与终止

长循环里放了 `gui.break_point()` 之后，「操作 → 暂停 / 停止」才有用：

```python
def main():
    for step in range(10000):
        model.iterate(dt=dt)
        gui.break_point()          # ← 每次迭代都停一下，检查是否被要求暂停/终止
```

没有 `break_point()` 的话，点"暂停"要等到循环结束才生效。

### 求解时看进度

```python
gui.progress('求解中', [0, 100], int(step / total * 100))
gui.show_attrs(time=model.get_text('time'), dt=dt, p=p)
```

两个在无头模式下都是空操作，可以放心写在计算循环里。

### 结果保存在哪

- 相对路径的基准是**工作目录**（[文件 → 工作路径] / `zmlx.io.set_path`）；
- `tfc.solve(folder='output')` 会往 `output/` 下按时间戳存 `.seepage` 文件；
- 无头模式下 `plot()` 的图默认存到工作目录下的图片文件夹（可用 `set_plt_save_path()` 改）。

### 安装依赖

```bash
python zmlx/scripts/install_dep.py       # 装齐所有依赖
python zmlx/scripts/write_pip_config.py  # 换成清华镜像源（下载慢时先跑这个）
```

或者直接打开 **设置 → 运行环境**，缺哪个点哪个的"安装"按钮。
'''),

        E('extending', '扩展点：想加东西加在哪', '''\
按"你要加什么"查这张表。**总原则**：能放在上层就别往下层塞，能写成新文件就别改老文件
（尤其是 `main.py`）。

### 加一个算例 / 场景 / 物理模型

| 加什么 | 放哪 | 参考 |
|---|---|---|
| 一个能跑的例子 | [`zmlx/demos/`](zmlx://doc/zmlx/demos/) 下新建主题目录 | 照现有 demo 抄；首行写 `# ** desc = '...'` |
| 一类工程问题（建好就能算） | [`zmlx/scen/`](zmlx://doc/zmlx/scen/) | `zmlx/scen/hydrate` |
| 一种流体 / 组分 | [`zmlx/fluids/`](zmlx://doc/zmlx/fluids/) + `create_xxx()` | `create_ch4` |
| 一个化学反应 | [`zmlx/reactions/`](zmlx://doc/zmlx/reactions/) | `add_reaction(model, data)` |
| 一条相渗曲线 | [`zmlx/krs/`](zmlx://doc/zmlx/krs/) | `create_kr` |

### 加一个界面功能

| 加什么 | 放哪 | 注意 |
|---|---|---|
| 一个**顶层**页面（只当标签页用） | `zmlx/ui/tabs/` | 判据：不被别的控件当零件用 |
| 一个**底层**控件（会被别人嵌进去） | `zmlx/ui/widgets/` | 规范见 [`widgets/AGENTS.md`](zmlx://doc/zmlx/ui/widgets/AGENTS.md) |
| 一个**菜单项 / 命令**（产品功能） | `zmlx/ui/extra_setups/` | **不要改 `main.py`** —— 本页就是这么挂上去的 |
| 一个**菜单项 / 命令**（用户能关掉的工具） | `zmlx/ui/plugins/builtin/` | 第六节「插件体系」有完整对照 |
| 一个**跨线程调用** | `zmlx/ui/utils/` 里的 `GuiApi` | 不要从后台线程直接碰控件 |

### 往 `extra_setups/` 里加菜单项的最小写法

```python
# zmlx/ui/extra_setups/my_feature.py
from zmlx.system import execute_once


def show_my_feature():
    from zmlx.ui import gui
    gui.command('show_my_feature')       # 让"开标签页"一定发生在 GUI 线程


def _open():
    from zmlx.ui import gui
    from zmlx.ui.tabs.my_page import MyPage

    def oper(w):
        w.gui_restore = 'gui.show_my_feature()'   # 重启后按这串恢复标签页

    gui.get_widget(the_type=MyPage, caption='我的功能', on_top=True, oper=oper)


@execute_once(file=__file__)
def setup_ui():
    from zmlx.ui import gui
    gui.add_func('show_my_feature', _open)
    gui.add_action(menu='显示', name='my_feature', text='我的功能',
                   slot=show_my_feature, overwrite=False,
                   is_enabled=lambda: not gui.is_running(),
                   is_visible=lambda: True)      # ← 见下面第 3 条
```

写完还要在 [`zmlx/ui/extra_setups/__init__.py`](zmlx://doc/zmlx/ui/extra_setups/__init__.py)
里**登记一段**（照现有的 `try/except` 写法）。

**四个容易踩的点**：

1. **命令名不能和 `MainWindow` 的公开方法撞名** —— 会被悄悄顶掉；
2. **命令名一旦发布就不能改** —— `gui_restore` 里存的是 `gui.show_xxx()` 原文，
   重启时按原文重放（要改就照
   [`license_query.py`](zmlx://doc/zmlx/ui/extra_setups/license_query.py) 末尾那样留旧名别名）；
3. **`is_visible` 缺省会跟着 `is_enabled`** —— 想"运行中置灰"而不是"运行中消失"，
   必须显式写 `is_visible=lambda: True`；
4. **`oper` 里不要放有副作用的动作** —— 点一次菜单就会执行一次。

### 插件体系：不改代码、也不改框架就能加东西

上面几节说的都是「**改** zmlx」。插件是另一条路：**加一个文件**就够了 ——
不用改 `main.py`，不用改任何 `__init__.py`，也不用改
[`extra_setups/__init__.py`](zmlx://doc/zmlx/ui/extra_setups/__init__.py)。

#### 判据：放 `plugins/` 还是 `extra_setups/`

> **关掉它，软件还能不能正常用？** 能 → 插件；不能 → `extra_setups/`。

| 放哪 | 收什么 | 用户能关掉吗 |
|---|---|---|
| `zmlx/ui/plugins/builtin/` | **非核心功能**：工具、演示、彩蛋 | ✅ 能 |
| [`zmlx/ui/extra_setups/`](zmlx://doc/zmlx/ui/extra_setups/) | **产品功能**：授权查询、用户管理 | ❌ 不能 |

把「授权查询」做成插件，等于允许用户关掉产品功能 —— 那是错的。

#### 插件就是一段代码，没有接口要继承

**定义只有一句**：

> 插件 = **界面启动时，在控制台（console）线程里被执行的一段代码**。
> 执行时，机制会自动把运行空间里的 `__name__` 设为 `'__zml_plugin__'`。
> **除此之外，没有其它限制。**

不是某个基类的子类，也不需要 `register()` 成某种对象，**也没有固定入口函数** ——
机制不做「找 `main()` / 找 `setup_ui()`」这种事，它只 `exec` 你写下的代码。
所以「在哪一行注册」完全由作者决定：顶层直接调用、放进
`if __name__ == '__zml_plugin__':` 分支、包成函数再调，**都合法**。
它可以是挂菜单、注册 `gui` 命令、开标签页（`gui.get_widget`）、起后台任务，
或者什么都不挂、只做一次性初始化。

⚠️⚠️ **「能否正确、快速地执行」是作者自己的责任** —— 机制什么也不替你保证：

| 作者要保证 | 不保证的后果 |
|---|---|
| **在 `__name__ == '__zml_plugin__'` 下能跑通** | 把注册放进 `__main__` 分支 = 插件加载时**静默不执行**（有一条警告兜底，但不报错） |
| **执行要快** | 它处在界面启动的**关键路径**上、同步执行；慢一点就是整个软件启动变慢，且不会提示是哪个插件 |

唯一的基本条件是**动界面必须走 `gui.xxx(...)`**：插件体跑在**控制台内核线程**里，
`gui.*` 会把调用派发到 GUI 线程；直接抓 `MainWindow` 或改控件就是跨线程操作，
轻则显示错乱、重则崩，而且 `main.py` 的内部结构会变成事实上的公共 API。
⚠️ 这条不等于「不能写 Qt 代码」：插件可以自己定义 `QWidget` 子类，
只是**把控件挂到窗口上**必须走 `gui.get_widget(...)`。

#### 一个最小的插件

```python
# my_plugin/zml_plugin.py            ← 文件名必须是 zml_plugin.py
# ** name = '我的备忘'
# ** desc = '在帮助菜单里加一条说明'
# ** enabled = True                  # 可选；省略视为启用
from zmlx.ui import gui
from zmlx.system import execute_once


@execute_once(file=__file__)         # 一次运行里可能被调多次，防止重复挂菜单
def setup_ui():
    gui.add_action(menu='帮助', name='my_note', text='我的备忘',
                   slot=lambda: gui.information('备忘', '记得改渗透率'),
                   overwrite=False)


if __name__ == '__zml_plugin__':
    setup_ui()      # 被插件机制执行：只注册，不开窗口

if __name__ == '__main__':
    setup_ui()      # 直接 python 运行：方便自测
```

顶部三行 `# ** name` / `# ** desc` / `# ** enabled` 是**可选的元数据**，只给
「设置 → 插件」列表显示用（解析走 `zmlx.algs.code_config`，**不执行插件体**）。

#### 放在哪、什么时候执行

| 位置 | 文件名 | 谁把它登记进名单 |
|---|---|---|
| 你的工程目录（任意搜索路径下，或 `zmlx/scen/` 的一层子目录） | `zml_plugin.py` | **首次启动自动发现**（只扫一次；之后可在「设置 → 插件」里手动添加 / 移除） |
| `zmlx/ui/plugins/builtin/` | 任意名（但**不要**叫 `zml_plugin.py`） | **不需要登记** —— 目录即语义，除 `__init__.py` 外每个 `.py` 都是插件 |

执行时机：界面启动时 `main.py` 在控制台内核线程里调 `plugins.load_all()`，
把**启用**的插件在各自**独立命名空间**里逐个 `exec`。
⚠️ 这意味着插件**处在启动的关键路径上**：顶层只该「接线」（`gui.add_action` /
`gui.add_func`），扫描目录、读大文件、跑计算一律推迟到菜单被点的那一刻、或扔进后台线程。

#### 三个概念，只用两个旋钮

「设置 → 插件」（[`gui.edit_setup_files()`](zmlx://gui/edit_setup_files)）里的七列是：

- **启用** —— 决定**下次启动**跑不跑（持久设置）；
- **优先级** —— 高 / 正常 / 低，只决定谁**先**执行，**不**改列表顺序，也没有排序接口；
- **临时加载** —— 点一下**当场**执行（不写盘、不必重启），每个插件在本次运行只跑一次；
  它与「启用」互不写入，重启后是否执行**仍只看勾选**。

⚠️ **「禁用」≠ 撤销**：它只表示**下次启动不执行这段代码**；插件已经派生的菜单项、
后台线程不会被回收。所以改了启用状态要**重启**才看得出效果。

⚠️ 插件之间**不共享**命名空间（只有 `__name__ == '__zml_plugin__'` 与 `__file__`），
模块级常量不会互相覆盖 —— 要用 `app_data` 就**自己 import**。

#### 别踩这四条

1. **把注册代码整段放进 `if __name__ == '__main__':`** —— 机制执行时 `__name__` 是
   `'__zml_plugin__'`，那段**不会执行**，表现为「勾上了、菜单却没出现」且不报错；
2. **往 `plugins/builtin/` 放工具模块** —— 会被当成插件执行。工具放上一层并以 `_` 开头；
3. **插件文件不是 UTF-8** —— 读取按 UTF-8，读不出即记为失败（其余插件照常执行）；
4. **改了插件文件名却忘了路径迁移** —— 名单里存的是**绝对路径**，旧记录会被当「文件缺失」
   静默跳过，用户勾开过的插件悄悄退回默认状态。

规范与完整清单：加插件的六步、目录分层与禁忌见
[`zmlx/ui/plugins/AGENTS.md`](zmlx://doc/zmlx/ui/plugins/AGENTS.md)（§0 讲清「为什么要有插件」），
13 个内置插件各挂在哪见 [`zmlx/ui/ReadMe.md`](zmlx://doc/zmlx/ui/ReadMe.md) 的 `plugins/` 一行。

### 加一份文档

| 文档 | 位置 | 备注 |
|---|---|---|
| 用户说明（随包发布） | `README.md` 与 `zmlx/data/README.md` | ⚠️ **两份必须逐字节相同** |
| 修改记录 | [`zmlx/data/CHANGELOG.md`](zmlx://doc/zmlx/data/CHANGELOG.md) | 唯一的 CHANGELOG，每个版本一条 |
| 使用指南 | [`zmlx/ReadMe.md`](zmlx://doc/zmlx/ReadMe.md) | 建模方式、常见陷阱 |
| 子包说明 | 各子包目录的 `ReadMe.md` | 与子包同生共死 |
| 开发者规范 | 各级 `AGENTS.md` | 改代码前先读 |
'''),

        E('pitfalls', '常见陷阱', '''\
这一页是"看起来像 bug、其实是用法问题"的清单。前六条来自建模指南，后面几条是写界面 /
写代码时的坑。

### 物理与建模

1. **虚拟 face 热泄漏** —— `add_cell_face` 创建的 face 会真实导热。**必须**在附近把
   `heat_cond` 设成 0，否则热量会从这条"井"边漏进漏出；
2. **定压边界**要用极大体积（`1e6` m³）或极大孔隙度（`1e10`）实现，**不要直接改 cell 压力**
   —— 一迭代它就被拉扯走了；
3. **恒温边界**用极大热容（`denc = 1e20`）。⚠️ **不要把 `heat_cond` 设成 0 来"固定温度"** ——
   那是**切断传热**，不是"恒温"；
4. **步长管理**：加 `model.add_tag('check_dt')` 并选合理的 `cfl`（默认 0.1）；
   **注入 / 加热之后**记得 `tfc.set_dt(model, 1e-3)` 重置步长；
5. **饱和度之和必须 ≤ 1**；字典里的名字必须与 `FluDef.name` 一致；
6. **注入 / 加热时关井** —— 生产井还开着会导致流体短路，要临时把虚拟 face 的 `perm` 置 0；
7. **多阶段模拟要备份状态** —— 注入器、加热设置、虚拟 face 属性在阶段切换时要
   backup / restore。

### 界面与代码

8. **切标签页会调用当前页的 `refresh()`** —— 里面不能读磁盘、联网、重画大图，
   慢活放后台线程，结果用信号回主线程；
9. **后台线程不设 parent + 用模块级列表持有强引用** —— 两条缺一不可，否则关标签页时进程
   直接崩（**不是异常**，是退出码 `0xC0000409`）；
10. **新界面元素默认不在 `__init__.py` 转发** —— 按子模块路径导入；
11. **不要把 `gui.execute()` 放进函数里** —— 只能出现在 `if __name__ == '__main__'`；
12. **`closeEvent` 不是关标签页的钩子** —— 标签页走 `deleteLater()`，请用
    `cleanup_before_tab_close()` / `save_file()`；
13. **安装路径不能有中文** —— `import zmlx` 时会警告，`opath()` 甚至会直接返回 `None`。

### 数据与类型

14. **参数校验是 `assert`** —— `python -O` 会**静默跳过全部校验**，别在优化模式下调试；
15. **`FluDef` 与 `FluData` 不是一个东西**（定义 vs 实例）；
16. **`FluData.vol` 是导出量**（`mass/den`），给它赋值实际改的是质量 —— 质量守恒请只跟踪 `mass`；
17. **`denc` 不是密度**，是"密度 × 比热"，单位 J/(m³·K)；
18. **`Face` 上没有 `area` / `perm` / `length` 属性** —— 那些是 `tfc` 约定的**自定义属性**，
   用 `get_attr('perm')` 读；
19. **扩散的浓度是质量分数**，不是 mol/L —— 从文献拿到的扩散系数要确认口径；
20. **`tfc.linspace` 不含终点**，与 numpy 不同（`linspace(0, 10, 5)` 得到 0/2/4/6/8）。

### 关于本页

- 本页的**回退**用的是 `QTextBrowser` 自己的历史栈。**关掉标签页**再打开，历史会从头开始
  （标签页被销毁了）；想直接到某一节，用控制台 `gui.show_architecture('pitfalls')` 直达；
- 本页显示的所有路径都是**本机的绝对路径**（取的是 `zmlx` 的安装位置），换机器会跟着变。
'''),

        E('troubleshooting', '报错排查', '''\
按"现象 → 原因 → 办法"整理。**每一条的报错原文都是代码里真实存在的字符串**，可以直接
在源码里搜到。

### 一、环境与安装

| 现象 | 原因 | 办法 |
|---|---|---|
| `Please make sure to install zmlx in a pure English path, otherwise it may cause unpredictable errors.` | `import zmlx` 时检测到安装目录含中文 / 非 ASCII | 把 zmlx 整体移到**纯英文、无空格**的路径下（例如 `D:\\zml\\hydrate`） |
| 弹窗「注意：1. 程序安装路径包含中文，请务必安装在纯英文路径下.」 | 界面启动时的一次性自检（同一天只弹一次） | 同上。只是想暂时不弹：把环境变量 `init_check` 设成 `No`（**不解决根因**） |
| 弹窗「注意：2. 界面将在2026年6月之后停止支持PyQt5，请更新至PyQt6」 | 当前用的是 PyQt5 | `pip install PyQt6`；装了两个而程序选了 PyQt5 时，用环境变量 `Qt_version=PyQt6` 强制定死 |
| `The root contains Chinese. key=..., root = ...`，随后 `opath()` 返回 `None` | 工作目录含中文 | 把工作目录改成英文路径 |
| `Error: folder contains Chinese. folder = ...`（`AssertionError`） | `set_path()` 传了中文路径 | 改传英文路径。⚠️ 这是 `assert`，`python -O` 下会**静默放行** |
| `安装失败(...): 返回码 ...` | pip / conda 子进程失败 | 先跑 `python zmlx/scripts/write_pip_config.py` 换清华源；网络问题重试 |

### 二、DLL 与内核（最常见）

| 现象 | 原因 | 办法 |
|---|---|---|
| `Error load library from <...zml.dll>. Message = [WinError 126] 找不到指定的模块` | 找到了 dll 但**它依赖的库缺失**——最常见是**没装 Visual C++ 运行库** | 装 [VC_redist.x64.exe](https://gitee.com/geomech/hydrate/attach_files)（**必须是 x64**），装完重启程序 |
| 同上，但 `Message` 是 `[WinError 193] 不是有效的 Win32 应用程序` | **位数不匹配**：64 位 Python 去加载 32 位 dll（或反过来） | 换成 **64 位 Python**，并确认 `zml.dll` 也是 64 位 |
| `Error load library from <zml.dll>. Message = ...`（路径是裸文件名） | **根本没找到** `zml.dll` | 确认它在 `zmlx/exts/` 目录下 |
| `Warning: can not find function <xxx> in <...>` | **dll 与 Python 代码版本不匹配**（旧 dll / 新代码） | 让两者同源同版本。用 `python -m zmlx.exts` 看内核编译时间 |
| `calling null function xxx(args=...)` | 上一条的直接后果：调用了占位函数，**什么也没做**就返回 `None` | 同上，版本对齐 |
| `RuntimeError: <内核错误原文>` | **C++ 内核自己报的错**（参数不合理 / 数据有问题） | 按原文改输入；完整错误也写进了当天日志 |
| `Meet error when get version: ...` | 读不到内核版本 | 同上，先修 dll 加载 |
| 控制台红字 `Exception Type: ... Message : ... Object : ...` | 内核线程里的未捕获异常（全局兜底输出） | 看 `Message :` 那一行；`RuntimeError` 多是内核报错，`AssertionError` 是参数校验没过 |

### 三、登录与授权

| 现象 | 原因 | 办法 |
|---|---|---|
| 状态栏「未登录」，悬停显示 `服务器原话：Please register with your email first.` | 本机从未用邮箱登录过 | 走 [「帮助 → 登录」](zmlx://gui/show_reg_tool)，填姓名 / 单位 / 邮箱 → 发验证码 → 填 6 位码 |
| 状态栏「登录状态未知」 | **没查到，不代表没登录** —— 可能是离线、超时（最长 60 秒）或服务端回了别的文案 | 先看悬停里的"服务器原话"：连接问题查网络，过期问题重新登录 |
| `计算中 stderr：The software is not logged in for feature <flow> on this computer.` | 授权校验没过。⚠️ 每个 feature 每次运行**只查一次**，断网那次不会重试 | 按提示登录（GUI 模式下程序会自动弹登录窗）；重启程序可让闸门复位 |
| 登录页：`本机 zml.dll 未加载。` / `硬件码为空` | `machine_id()` 返回空 —— 根因几乎总是 **dll 没加载** | 先修 dll（见上一节） |
| `发送得太频繁了：a code was sent recently, please wait 412s and try again` | 同一邮箱 10 分钟只能发一次 | **照着那句秒数等**，它是精确的剩余时间 |
| 正文 `连不上服务器：SocketException...` | 网络 / 代理 / 防火墙 / DNS | 检查网络 |
| 正文 `没有拿到任何答复（可能是网络中断，或 zml.dll 未加载）。` | 答复为空 | 先确认 dll 加载，再查网络 |
| `「姓名」不能包含半角竖线或冒号` | 这些字符会破坏服务端的分段协议 | 删掉 `|` 和 `:` |
| `请先停止正在运行的计算，再在这台电脑上退出。` | 计算在跑时不允许退出登录 | 先停止计算 |

### 四、界面

| 现象 | 原因 | 办法 |
|---|---|---|
| 退出时问「内核似乎正在运行，确定要退出吗？」 | 控制台里还有脚本在跑 | 点"否"回去先停止，再退出 |
| 点「运行」没反应、只响一声错误音 | **内核已经在跑了**（同一时刻只允许一个）。⚠️ 这一处没有文字提示 | 先停止 / 等当前算完 |
| `call gui failed: ...` 之后程序照常跑但没界面 | `zmlx.ui.main` 起不来（通常是 **Qt 没装**），**自动降级为无界面运行** | 这是优雅降级不是崩溃。要界面就 `pip install PyQt6` |
| `Warning: qtpy was imported before the Qt binding was pinned; ...` | 你的脚本在 `import zmlx` **之前**就 import 了 `qtpy`，两套绑定混用会**原生崩溃** `0xC0000409` | 把 `import qtpy` / `pyvistaqt` / `pyqtribbon` 移到 `import zmlx` **之后** |
| `QWebEngineView is not installed` | 缺 **PyQt6-WebEngine**（内嵌网页 `open_url` 与 PDF 查看 `open_pdf` 都用它） | `pip install PyQt6-WebEngine`，装完**重启进程** |
| `Error when setup action: ...` / `Error when setup xxx: ...` | 界面启动时某个附加模块挂了（每个模块有独立的兜底，**不会**拦住整个界面） | 看是哪一项：多半缺 pyvista 等可选库。⚠️ 插件（`plugins/`）的失败**不走这条**：报错落在启动日志里 `Exec File: <路径>` 后跟 `Failed: ...`，同时在消息区弹出 `path = ..., error = ...` |
| `gui function <xxx> not found` | 脚本调了不存在的 `gui.xxx()` | 用 `print(gui.list_all())` 核对名字 |

### 五、可选依赖（不影响主体功能）

| 现象 | 缺什么 | 装法 |
|---|---|---|
| 三维视图打不开 | `pyvista` / `vtk` / `pyvistaqt` | `pip install pyvista vtk pyvistaqt` |
| Markdown 表格、样式显示不全 | `markdown` | `pip install markdown` |
| 代码编辑器没有语法高亮 | `pyqt6-qscintilla` | `pip install pyqt6-qscintilla` |
| `CoolProp 未安装，请运行: pip install CoolProp` | CoolProp（高精度物性） | `pip install CoolProp` |
| `Reaktoro 未安装，请运行: conda install -c conda-forge reaktoro` | Reaktoro（地质化学） | **只能 conda 装** |
| `numpy is not installed` | numpy | `pip install numpy`。⚠️ 这是 `assert`，`-O` 下不报错而是算出乱数 |
| `scipy is not installed` | scipy（三角剖分 / 插值） | `pip install scipy` |

> 一劳永逸：打开 **设置 → 运行环境**，它列出所有依赖并逐条告诉你缺哪个、怎么装。

### 六、计算中的警告

| 现象 | 原因 | 办法 |
|---|---|---|
| `AssertionError: dt must be float. dt = ...` | 传了 `int` / numpy 标量 / `None` | 显式 `float(dt)` |
| `gravity should be [0, 0, -9.8], but here it is ...` | 重力与惯例偏差超过 1.0 | 确认是否真的要这么设 |
| `The key (...) is None and default_val is None when get_attr` | 取一个没设过的属性，又没给默认值 | 先 `set_attr` 补上，或传 `default_val=` |
| `The pool is None, but there are more than 1 models to iterate.` | 多模型迭代没给线程池，退化为串行 | 传 `pool=ThreadPool()`，或忽略（只是慢） |
| `模型 ... 没有 check_dt 标签` | 子域分解要求 CFL 检查开启 | `model.add_tag('check_dt')` |
| `dv_relative is deprecated ... please use cfl instead` | 用了弃用参数 | 改用 `cfl` |
| `tfc.solve(gui_mode=True) is deprecated ...` | 用旧写法在 `solve` 里开界面 | 用 `gui.execute(lambda: tfc.solve(...), close_after_done=False)` 包一层 |
| `<xxx> will be removed after <日期>` | 用了**已弃用的旧路径 / 旧名字** | 照警告里的新路径改 import |

### 两条"没有文字提示"的坑

1. **点「运行」没反应、只响一声** —— 内核已在运行（见上）；
2. **在无 Qt 的环境里想开界面** —— `call gui failed: ...` 之后**静默降级为无界面运行**，
   你以为界面崩了，其实计算在跑。
'''),

        E('docs', '文档地图', '''\
代码库里有多份文档，各有分工。下表从上到下就是**建议的阅读顺序**。

| 文档 | 讲什么 | 谁该看 |
|---|---|---|
| [`zmlx/data/README.md`](zmlx://doc/zmlx/data/README.md) | 简介、作者、安装、登录、反馈、隐私声明 —— 随包发布的**唯一**用户说明 | 所有人 |
| [`zmlx/ReadMe.md`](zmlx://doc/zmlx/ReadMe.md) | 使用指南：架构速览、子包表、建模模式、常见陷阱 | 要建模的人 |
| [`zmlx/demos/ReadMe.md`](zmlx://doc/zmlx/demos/ReadMe.md) | 建模指南（与 110 个 demo 配套）：空间分布函数、边界条件、时间步进、可视化 | 要写算例的人 |
| [`AGENTS.md`](zmlx://doc/AGENTS.md)（仓库根） | 项目指引：分层、编码规范、GUI 模式、工作流 | 要改代码的人 |
| [`zmlx/ui/ReadMe.md`](zmlx://doc/zmlx/ui/ReadMe.md) | 界面层速查：启动方式、控件清单、模块表 | 要改界面的人 |
| [`zmlx/ui/widgets/AGENTS.md`](zmlx://doc/zmlx/ui/widgets/AGENTS.md) | **控件规范**（唯一来源）：骨架、线程生命周期、调色板取色、自测 | 写控件的人 |
| [`zmlx/ui/tabs/AGENTS.md`](zmlx://doc/zmlx/ui/tabs/AGENTS.md) | 哪些控件归 `tabs/`、依赖方向 | 写顶层页面的人 |
| [`zmlx/ui/AGENTS.md`](zmlx://doc/zmlx/ui/AGENTS.md) | 界面元素要不要在 `__init__.py` 转发 | 所有人 |
| [`zmlx/data/CHANGELOG.md`](zmlx://doc/zmlx/data/CHANGELOG.md) | 每个版本改了什么 | 想知道"什么时候变的" |
| [`zmlx/data/ROADMAP.md`](zmlx://doc/zmlx/data/ROADMAP.md) | 未来工作 | 想参与的人 |
| 各子包的 `ReadMe.md` | 该子包的设计、关键函数、常见用法 | 深入某个包时 |

### 三条"元规则"

1. **两份 README 必须逐字节相同** —— [`README.md`](zmlx://doc/README.md) 与
   [`zmlx/data/README.md`](zmlx://doc/zmlx/data/README.md)。改一份就要覆盖另一份：界面的
   [「帮助 → ReadMe」](zmlx://gui/show_readme) 读的是 `zmlx/data/` 那份；
2. **每个子包的文档跟着子包走** —— 子包改名 / 删除，它的 `ReadMe.md` / `AGENTS.md` 一起处理；
3. **`AGENTS.md` 是给"改代码的人"看的**（包括 AI 助手）：规范冲突时**更具体者为准**
   （子目录的 `AGENTS.md` > 仓库根的 > 一般约定）。

### 本页与它们的关系

本页（架构）**不替代**上面任何一份，它回答的是"**这些文档各自负责什么、代码库整体长什么样**"。
真正的操作指南仍然在上面那几份里 —— 本页见到相关内容时直接给了链接。
'''),

        E('glossary', '术语与词汇表', '''\
| 词 | 含义 |
|---|---|
| **THMC** | 热（Thermal）- 流（Hydraulic）- 力（Mechanical）- 化（Chemical），本项目要耦合的四类过程 |
| **TFC** | Thermal-Flow-Chemical，`zmlx/tfc/` 这个耦合引擎的名字来源 |
| **ICP** | In-situ Conversion Process，油页岩原位转化（干酪根加热裂解） |
| **EGS** | Enhanced Geothermal System，增强型地热系统 |
| **DFN** | Discrete Fracture Network，离散裂缝网络 |
| **IP** | Invasion Percolation，侵入逾渗（孔隙尺度驱替） |
| **Seepage** | 核心模型对象：装着 cell / face / fluid / reaction |
| **cell / face** | 网格单元 / 单元之间的连接面 |
| **FluDef / FluData / Fluid** | 流体**定义**（模型级）/ 流体**实例**（单元级）/ 带编号的实例视图 |
| **iterate** | 时间推进一步；内部按固定顺序跑完流动、传热、反应等子过程 |
| **CFL** | Courant-Friedrichs-Lewy 数：`dt` 内流体流过的距离与网格尺寸的比值。默认 0.1 |
| **dt / dt_min / dt_max** | 时间步长及其硬约束（默认 1e-10 / 1e-15 / 1e10 秒） |
| **cond（导流系数）** | `Face` 上流动的传导能力，`= area × perm / dist` |
| **denc** | **不是密度**，是密度 × 比热，单位 J/(m³·K) |
| **mc** | 热容 = 体积 × `denc`，单位 J/K |
| **g_heat** | 导热通量：Face 上 `= area × heat_cond / length`；Cell 上 `= vol × heat_cond / dist²` |
| **perm / kr** | 渗透率（m²）/ 相对渗透率（无量纲） |
| **Voronoi / Delaunay** | 网格剖分方式（`zmlx/meshes` 用 Delaunay） |
| **Mesh3 / SeepageMesh** | 几何网格（节点/线/面/体）/ 渗流网格（cell-face）—— **两种不同的东西** |
| **gui / GUI 线程** | `zmlx.ui` 的主线程；所有控件操作都必须在它上面做 |
| **headless（无头模式）** | 不显示窗口，`gui.xxx()` 全部变成空操作 |
| **gui_restore** | 标签页存下的"怎么重新打开我"的代码串，重启后按原文重放 |
| **extra_setups** | 额外菜单动作的落脚处：新增菜单项放这里，不动 `main.py` |
| **zml_plugin.py** | 插件脚本：GUI 启动时自动执行的用户代码（旧名 `zml_gui_setup.py` 仍兼容） |
| **exe / dll / so** | `zml.dll`（Windows）/ `zml.so`（Linux）是编译好的 C++ 内核 |
| **REFPROP / NIST / CoolProp / Reaktoro** | 四种物性数据来源：NIST 表、CoolProp 状态方程、Reaktoro 地质化学 |

### 几个容易混的说法

- **"demo"** 一般指 `zmlx/demos/` 下的可运行示例；**"场景（scen）"** 指 `zmlx/scen/` 里已经
  打包好的工程问题。前者给人看，后者给程序用，场景里经常调用 demo 里的写法；
- **"ReadMe"** 在界面上特指 [`zmlx/data/README.md`](zmlx://doc/zmlx/data/README.md)（软件说明），
  不是仓库根目录那份代码文档；
- **"文档"** 这个界面的[「帮助 → ReadMe」](zmlx://gui/show_readme) 是一个 Markdown 阅读器，
  和"文档"这个词本身不是一回事；
- **"架构"** 就是本页：代码库的结构与各部分的职责。

### 单位约定

本库**统一使用 SI 单位**。最容易记错的几个：

| 量 | 单位 | 常见错法 |
|---|---|---|
| 压力 | Pa | 传 MPa（1e6 倍错误） |
| 温度 | K | 传 ℃（差 273.15） |
| 长度 | m | 传 cm / mm |
| 时间 | s | 传小时 / 天（要自己乘 3600 / 86400） |
| 渗透率 | m² | 传 mD 或 Darcy（1 D ≈ 1e-12 m²） |
| 质量 | kg | 传 g |
| 能量 / 反应热 | J/kg | 传 J/mol |
'''),
    ]


_PAGES = _build_pages()


# ======================================================================
# 配图：原生 Qt 绘制（跟随调色板 / 主题）
# ======================================================================

class _Palette:
    """配图用的取色与画笔工具（不实例化，纯命名空间）.

    颜色**全部**从 ``QPalette`` 取：程序有暗色模式，用户还能在
    [「设置 → 样式表」](zmlx://gui/show_style_sheet) 里换配色，控件里写死色值要么在暗色下
    看不清，要么盖掉用户主题（见 ``widgets/AGENTS.md`` 的「控件里的颜色」）。

    层级配色用的是几个固定的色相（红橙绿蓝紫灰），在暗色主题下自动提亮 —— 只提亮、不换色相，
    这样"哪一层是哪一层"在任何主题下都认得出。
    """

    #: 六层的色相（浅色主题下的 RGB，0~1）
    LAYERS = [
        (0.87, 0.42, 0.32),   # L5 应用场景   红
        (0.93, 0.63, 0.28),   # L4 耦合引擎   橙
        (0.42, 0.66, 0.40),   # L3 工具与界面 绿
        (0.33, 0.55, 0.80),   # L2 物理定义   蓝
        (0.55, 0.45, 0.80),   # L1 绑定       紫
        (0.55, 0.57, 0.60),   # L0 内核       灰
    ]

    @staticmethod
    def role(name):
        """按名字取 ``QPalette.ColorRole``（取不到返回 ``None``）."""
        return getattr(QtGui.QPalette.ColorRole, name, None)

    @classmethod
    def color(cls, palette, kind='text'):
        """按用途取色.

        Args:
            palette: 当前调色板。
            kind: ``text`` / ``muted`` / ``border`` / ``base`` / ``window`` / ``link``。

        Returns:
            ``QColor``。任何一个语义角色取不到时**逐级回退**，最终退回 ``WindowText``
            —— 宁可同色，不可异常。
        """
        names = {
            'text': ('WindowText',),
            'muted': ('PlaceholderText', 'Mid', 'Dark', 'WindowText'),
            'border': ('Mid', 'Dark', 'WindowText'),
            'base': ('Base', 'Window'),
            'window': ('Window', 'Base'),
            'link': ('Link', 'Highlight', 'WindowText'),
        }
        for name in names.get(kind, ('WindowText',)):
            role = cls.role(name)
            if role is None:
                continue
            try:
                return palette.color(role)
            except Exception:
                continue
        return palette.color(cls.role('WindowText'))

    @classmethod
    def is_dark(cls, palette):
        """按窗口背景的亮度判断是不是暗色主题."""
        try:
            return cls.color(palette, 'window').lightness() < 128
        except Exception:
            return False

    @classmethod
    def layer(cls, index, dark):
        """第 ``index`` 层的填充色（暗色主题下提亮，保证与深色背景有对比）."""
        r, g, b = cls.LAYERS[int(index) % len(cls.LAYERS)]
        if dark:
            r, g, b = (1.0 - (1.0 - r) * 0.60,
                       1.0 - (1.0 - g) * 0.60,
                       1.0 - (1.0 - b) * 0.60)
        color = QtGui.QColor.fromRgbF(r, g, b)
        color.setAlpha(230)
        return color

    @staticmethod
    def font(size=0, bold=False):
        """取一个字号/字重可控的字体；``size<=0`` 表示"按默认字号缩一点"."""
        font = QtGui.QFont()
        if size > 0:
            font.setPointSizeF(size)
        else:
            base = font.pointSizeF()
            if base <= 0:
                base = 10.0
            font.setPointSizeF(base * 0.80)
        font.setBold(bold)
        return font

    @classmethod
    def box(cls, painter, palette, rect, text='', fill=None, dark=False,
            radius=6.0, bold=True, font_size=0.0):
        """画一个圆角框（可带居中文字）—— 所有图里的"块"都走这里."""
        painter.save()
        pen = QtGui.QPen(cls.color(palette, 'border'))
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(QtGui.QBrush(fill) if fill is not None else QtCore.Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)
        if text:
            painter.setPen(cls.color(palette, 'text'))
            size = font_size if font_size > 0 else rect.height() * 0.20
            painter.setFont(cls.font(min(size, 34.0), bold=bold))
            painter.drawText(rect,
                             QtCore.Qt.AlignmentFlag.AlignCenter
                             | QtCore.Qt.TextFlag.TextWordWrap, text)
        painter.restore()

    @classmethod
    def arrow(cls, painter, palette, start, end, label=None, label_size=0.0):
        """画一条带箭头的线（可选在中间贴一个小标签）."""
        painter.save()
        pen = QtGui.QPen(cls.color(palette, 'muted'))
        pen.setWidthF(1.4)
        painter.setPen(pen)
        painter.setBrush(QtGui.QBrush(cls.color(palette, 'muted')))
        painter.drawLine(start, end)
        painter.drawPolygon(cls._head(start, end))
        if label:
            painter.setPen(cls.color(palette, 'muted'))
            painter.setFont(cls.font(label_size if label_size > 0 else 0))
            mid = QtCore.QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
            painter.drawText(mid + QtCore.QPointF(6, -6), label)
        painter.restore()

    @staticmethod
    def _head(start, end, size=7.0):
        """箭头三角（贴着 ``end`` 画）."""
        dx, dy = end.x() - start.x(), end.y() - start.y()
        length = max(1e-9, (dx * dx + dy * dy) ** 0.5)
        ux, uy = dx / length, dy / length
        base = QtCore.QPointF(end.x() - ux * size, end.y() - uy * size)
        return QtGui.QPolygonF([
            QtCore.QPointF(end),
            QtCore.QPointF(base.x() - uy * size * 0.55, base.y() + ux * size * 0.55),
            QtCore.QPointF(base.x() + uy * size * 0.55, base.y() - ux * size * 0.55),
        ])

    @classmethod
    def text(cls, painter, palette, rect, text, size=0.0, bold=False,
             kind='text', align=None):
        """在矩形里画一段自动换行的文字."""
        painter.save()
        painter.setPen(cls.color(palette, kind))
        painter.setFont(cls.font(size, bold=bold))
        painter.drawText(rect,
                         (align if align is not None else QtCore.Qt.AlignmentFlag.AlignCenter)
                         | QtCore.Qt.TextFlag.TextWordWrap, text)
        painter.restore()

    @classmethod
    def text_fit(cls, painter, palette, rect, text, size=0.0, bold=False,
                 kind='text', align=None, min_ratio=0.55):
        """同 :meth:`text`，但**放不下就把字号缩下来**，保证不出框、不缺字.

        ⚠️ 为什么必须有它：``text`` 用的是 ``painter.drawText(rect, flags, text)`` ——
        Qt 会把超出 ``rect`` 的部分**直接裁掉**（不是溢出，是整段看不见）。而各图的
        文本框宽、字号都是写死的常数，字一长就出现「``low_1p``」「L4 的标题压住路径行」
        「工具栏条目在右边界被切」这类现象（PLAN ``T-20261024-01``）。

        做法：二分收缩字号，取「仍能完整放进 rect」的最大字号；最多收到 ``min_ratio``
        倍。**仍放不下就按最小字号画** —— 宁可小一点，也不要缺字（缺字会读错）。

        ⚠️ 注意 ``_Palette.font`` 用的是 ``setPointSizeF``，1 pt ≈ 1.33 逻辑像素，
        所以「size=26 的文字」在画布上约占 35 单位高 —— 估算框宽时按 1.33 倍算。

        Args:
            painter: 画笔。
            palette: 调色板。
            rect: 文本框（画布坐标）。
            text: 文字（可含 ``
``）。
            size: 期望字号；``<=0`` 表示不收缩、直接交给 :meth:`text`。
            bold: 是否加粗。
            kind: 颜色种类（``text`` / ``muted`` …）。
            align: 对齐方式（默认居中）。
            min_ratio: 字号最多收缩到原值的多少倍。

        Returns:
            float: 实际使用的字号（便于自检；``size<=0`` 时返回 0）。
        """
        size = float(size)
        if size <= 0:
            cls.text(painter, palette, rect, text, size=size, bold=bold,
                     kind=kind, align=align)
            return 0.0
        flags = int((align if align is not None else QtCore.Qt.AlignmentFlag.AlignCenter)
                    | QtCore.Qt.TextFlag.TextWordWrap)
        # ⚠️ 留 2% 安全边距：``QFontMetricsF`` 报「940 恰好放进 940 的框」时，
        #    ``drawText`` 仍会切掉最后一字的右边缘（实测 2026-10-24，工具栏那一行）。
        limit_w = rect.width() * 0.98
        limit_h = rect.height() * 0.98
        target = QtCore.QRectF(0.0, 0.0, limit_w, limit_h)
        low = size * float(min_ratio)
        high = size
        best = low
        for _ in range(12):
            mid = (low + high) / 2.0
            metrics = QtGui.QFontMetricsF(cls.font(mid, bold=bold))
            need = metrics.boundingRect(target, flags, text)
            if need.width() <= limit_w and need.height() <= limit_h:
                best = mid
                low = mid
            else:
                high = mid
        cls.text(painter, palette, rect, text, size=best, bold=bold,
                 kind=kind, align=align)
        return best


class _Figure(QtWidgets.QWidget):
    """一张配图（只画图，不处理交互）.

    绘制坐标系统一用一块 **1000×1000 的逻辑画布**，再按控件实际大小**等比缩放**，
    所以拉大窗口时文字不会糊、也不会溢出。

    ⚠️ **它只是「渲染器」，不是可见控件**（2026-10-24 起）：本类从不 ``show()``，
    由 :meth:`_ArchitectureView._render_figure` 用 ``QWidget.render(painter)`` 画进
    ``QImage``，再作为**文档内嵌图片**插进正文。所以这里只管「怎么画」，
    「放在哪、怎么滚动」全归 ``QTextDocument``。

    ⚠️ **配色一律现取 ``QPalette``**：换样式表 / 切暗色模式后，视图会重新调
    ``_render_figure`` 重画一张 —— 位图本身是**缓存**，缓存的有效期由
    ``_ArchitectureView.changeEvent``（``PaletteChange`` / ``FontChange``）管。
    ⚠️ **不要**在 ``paintEvent`` 里读 ``self.grab()`` 或写文件。

    Attributes:
        kind: 画哪一张图 —— ``overview`` / ``layers`` / ``data_flow`` / ``gui_map`` /
            ``reading`` / ``demos``。
        caption: 图标题（画在图的下方）。
    """

    #: 逻辑画布尺寸
    CANVAS = QtCore.QSizeF(1000.0, 1000.0)

    def __init__(self, parent=None, kind='layers', caption=''):
        super().__init__(parent)
        self.kind = kind
        self.caption = caption
        self._wanted = QtCore.QSize(700, 260)     # 声明的"期望尺寸"
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(int(self._wanted.height()))
        self.setToolTip(caption or '示意图')

    def set_wanted_size(self, width, height):
        """设置期望尺寸（宽跟着正文走，高按这里给的值）."""
        height = int(height)
        if height > 0:
            self._wanted = QtCore.QSize(max(320, int(width)), height)
            self.setMinimumHeight(height)
            self.updateGeometry()

    def sizeHint(self):
        return self._wanted

    def event(self, e):
        """调色板一变就 ``update()``（离屏渲染时这不会触发重画，重画由视图负责）.

        ⚠️ 保留它是为了「万一被直接 ``show()`` 出来调试」时行为仍然正确 ——
        正常路径下本控件不可见，重画由 :meth:`_ArchitectureView.changeEvent` 驱动。
        """
        if e.type() == QtCore.QEvent.Type.PaletteChange:
            self.update()
        return super().event(e)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing, True)
        palette = self.palette()

        # 背景用一个比正文略深的底，好让图与文字区分开
        background = QtGui.QColor(_Palette.color(palette, 'base'))
        if _Palette.is_dark(palette):
            background = background.lighter(112)
        else:
            background = background.darker(104)
        painter.fillRect(self.rect(), background)

        area = QtCore.QRectF(self.rect()).adjusted(6, 6, -6, -6)
        if self.caption:
            painter.setPen(_Palette.color(palette, 'muted'))
            painter.setFont(_Palette.font(0))
            painter.drawText(QtCore.QRectF(area.left(), area.bottom() - 18,
                                           area.width(), 18),
                             QtCore.Qt.AlignmentFlag.AlignHCenter
                             | QtCore.Qt.AlignmentFlag.AlignVCenter, self.caption)
            area.setBottom(area.bottom() - 24)
        if area.width() < 30 or area.height() < 30:
            return

        scale = min(area.width() / self.CANVAS.width(),
                    area.height() / self.CANVAS.height())
        painter.save()
        painter.translate(area.x() + (area.width() - self.CANVAS.width() * scale) / 2,
                          area.y() + (area.height() - self.CANVAS.height() * scale) / 2)
        painter.scale(scale, scale)
        try:
            self._dispatch(painter, palette)
        except Exception as err:      # 图画坏了不能带崩整个页面
            painter.setPen(QtGui.QColor(200, 60, 60))
            painter.setFont(_Palette.font(30))
            painter.drawText(QtCore.QRectF(0, 400, 1000, 200),
                             QtCore.Qt.AlignmentFlag.AlignCenter,
                             '配图绘制失败：%s' % err)
        painter.restore()

    # ------------------------------------------------------------------
    # 分派
    # ------------------------------------------------------------------
    def _dispatch(self, painter, palette):
        dark = _Palette.is_dark(palette)
        drawer = {
            'overview': self._draw_overview,
            'layers': self._draw_layers,
            'data_flow': self._draw_data_flow,
            'gui_map': self._draw_gui_map,
            'reading': self._draw_reading,
            'demos': self._draw_demos,
        }.get(self.kind)
        if drawer is not None:
            drawer(painter, palette, dark)

    # ------------------------------------------------------------------
    # 1. 总览：五步
    # ------------------------------------------------------------------
    def _draw_overview(self, painter, palette, dark):
        """从左到右五步：写算例 → 造模型 → 推进 → 取数 → 出图."""
        steps = [
            ('① 写算例', 'zmlx/demos/', '挑一个最像的\n例子改参数'),
            ('② 造模型', 'tfc.create()', '→ Seepage 对象\ncell / face / fluid'),
            ('③ 推进时间', 'iterate()', '流动 → 传热 → 反应\n自动定步长'),
            ('④ 取数据', 'tfc.get_p()', 'numpy 数组\n批量、不拷贝'),
            ('⑤ 出图 / 存盘', 'plot()', 'GUI 标签页\n或无头存文件'),
        ]
        n = len(steps)
        left, right, gap = 20.0, 980.0, 16.0
        width = (right - left - gap * (n - 1)) / n
        top, height = 250.0, 420.0
        for i, (title, api, detail) in enumerate(steps):
            x = left + i * (width + gap)
            rect = QtCore.QRectF(x, top, width, height)
            _Palette.box(painter, palette, rect, '', _Palette.layer(i * 1.3, dark), dark,
                         radius=12.0)
            # ⚠️ 标题框只有 width-16 ≈ 163 宽；size 36 时「③ 推进时间」需要 185 ⇒
            #    折成两行、压住下面的 api 行。改成 22，并让过长的那条（⑤）精简。
            _Palette.text_fit(painter, palette, QtCore.QRectF(x + 8, top + 26, width - 16, 52),
                          title, size=22.0, bold=True)
            _Palette.text_fit(painter, palette, QtCore.QRectF(x + 8, top + 92, width - 16, 44),
                          api, size=30.0, kind='muted')
            _Palette.text_fit(painter, palette, QtCore.QRectF(x + 6, top + 172, width - 12, 200),
                          detail, size=24.0)
            if i + 1 < n:
                _Palette.arrow(painter, palette,
                               QtCore.QPointF(x + width + 2, top + height / 2),
                               QtCore.QPointF(x + width + gap - 3, top + height / 2))
        _Palette.text_fit(painter, palette, QtCore.QRectF(20, 70, 960, 70),
                      '从「一个算例」到「屏幕上的图」',
                      size=46.0, bold=True)
        _Palette.text_fit(painter, palette, QtCore.QRectF(20, 148, 960, 48),
                      '下面每个方框都能在左侧目录里找到对应的小节',
                      size=26.0, kind='muted')
        _Palette.text_fit(painter, palette, QtCore.QRectF(20, 720, 960, 200),
                      '所有阶段的中间产物只有一个：Seepage 对象'
                      '（cell / face / fluid / reaction）。\n'
                      '这正是“多场耦合”能够成立的原因 —— '
                      '流动、传热、反应改的都是同一份数据。',
                      size=27.0, kind='muted')


    # ------------------------------------------------------------------
    # 2. 五层架构
    # ------------------------------------------------------------------
    def _draw_layers(self, painter, palette, dark):
        """从上到下六层堆叠，右侧标注依赖方向."""
        layers = [
            ('L5  应用场景', 'zmlx/scen/', 'hydrate · icp · frac · helium · editors'),
            ('L4  耦合物理引擎', 'zmlx/tfc/', 'iterate → solve'),
            ('L3  工具与界面', 'zmlx/ui/  zmlx/utils/  zmlx/plt/', 'Field · GuiIterator · PyQt6'),
            ('L2  物理定义', 'zmlx/fluids/  zmlx/reactions/  zmlx/krs/', 'FluDef · Reaction · kr 曲线'),
            ('L1  Python→C++ 绑定', 'zmlx/exts/', 'Seepage · Cell · Face · FluDef'),
            ('L0  C++ 内核', 'zml/', 'header-only  C++17  →  zml.dll / zml.so'),
        ]
        top, row_h, gap = 40.0, 118.0, 14.0
        left, right = 40.0, 760.0
        for i, (name, path, cores) in enumerate(layers):
            y = top + i * (row_h + gap)
            rect = QtCore.QRectF(left, y, right - left, row_h)
            _Palette.box(painter, palette, rect, '', _Palette.layer(i, dark), dark, radius=8.0)
            # ⚠️ 标题框必须**整行宽**（原先写死 300）：``_Palette.text`` 一律带
            #    ``TextWordWrap``，而 300 装不下「L4  耦合物理引擎」这种长名字 ⇒ 折行后
            #    溢出 42 高的框、压住下面的路径行（2026-10-24 图第一次真正显示出来才发现，
            #    见 PLAN ``T-20261024-01``）。
            _Palette.text_fit(painter, palette, QtCore.QRectF(left + 18, y + 6, right - left - 36, 42),
                          name, size=31.0, bold=True,
                          align=QtCore.Qt.AlignmentFlag.AlignLeft
                                | QtCore.Qt.AlignmentFlag.AlignVCenter)
            _Palette.text_fit(painter, palette, QtCore.QRectF(left + 18, y + 52, right - left - 36, 32),
                          path, size=26.0, bold=False,
                          align=QtCore.Qt.AlignmentFlag.AlignLeft
                                | QtCore.Qt.AlignmentFlag.AlignVCenter)
            _Palette.text_fit(painter, palette, QtCore.QRectF(left + 18, y + 84, right - left - 36, 28),
                          cores, size=22.0, kind='muted',
                          align=QtCore.Qt.AlignmentFlag.AlignLeft
                                | QtCore.Qt.AlignmentFlag.AlignVCenter)

        # 右侧：依赖方向（竖箭头，从上往下 = 上层可调用下层）
        x = right + 26
        y0 = top + 18
        y1 = top + len(layers) * (row_h + gap) - gap - 18
        _Palette.arrow(painter, palette, QtCore.QPointF(x, y0), QtCore.QPointF(x, y1))
        _Palette.text_fit(painter, palette, QtCore.QRectF(x - 14, 6, 220, 30),
                      '上层', size=22.0, kind='muted',
                      align=QtCore.Qt.AlignmentFlag.AlignLeft)
        _Palette.text_fit(painter, palette, QtCore.QRectF(x - 14, y1 + 6, 220, 30),
                      '底层', size=22.0, kind='muted',
                      align=QtCore.Qt.AlignmentFlag.AlignLeft)
        painter.save()
        painter.translate(x + 30, (y0 + y1) / 2)
        painter.rotate(90)
        _Palette.text_fit(painter, palette, QtCore.QRectF(-240, -18, 480, 36),
                      '上层可以调用下层 · 下层绝不 import 上层',
                      size=24.0, kind='muted')
        painter.restore()

    # ------------------------------------------------------------------
    # 3. 一次求解
    # ------------------------------------------------------------------
    def _draw_data_flow(self, painter, palette, dark):
        """一次时间步：主流程在左，`iterate` 内部的子过程在右。"""
        # ---------- 左：四个阶段 ----------
        stages = [
            ('① 建模', 'tfc.create(mesh, ...)  \u2192  Seepage', 4),
            ('② 时间推进', 'seepage.iterate(dt) / tfc.solve(...)', 0),
            ('③ 步长控制', '各子过程提交建议 \u2192 取最小 \u2192 钳制', 1),
            ('④ 后处理', 'tfc.get_p()  \u2192  show_field2()', 3),
        ]
        left, width, height = 24.0, 470.0, 74.0
        top, gap = 96.0, 128.0
        for i, (title, detail, color) in enumerate(stages):
            y = top + i * gap
            rect = QtCore.QRectF(left, y, width, height)
            _Palette.box(painter, palette, rect, '', _Palette.layer(color, dark), dark, radius=9.0)
            _Palette.text_fit(painter, palette, QtCore.QRectF(left + 12, y + 4, 160, height - 8),
                          title, size=20.0, bold=True,
                          align=QtCore.Qt.AlignmentFlag.AlignLeft
                                | QtCore.Qt.AlignmentFlag.AlignVCenter)
            _Palette.text_fit(painter, palette, QtCore.QRectF(left + 176, y + 4, width - 188, height - 8),
                          detail, size=22.0,
                          align=QtCore.Qt.AlignmentFlag.AlignLeft
                                | QtCore.Qt.AlignmentFlag.AlignVCenter)
            if i + 1 < len(stages):
                _Palette.arrow(painter, palette,
                               QtCore.QPointF(left + width / 2, y + height + 3),
                               QtCore.QPointF(left + width / 2, y + gap - 3),
                               label='反复循环' if i == 1 else None, label_size=19.0)

        # ---------- 右：iterate 内部的子过程 ----------
        subs = ['时间 / 步数触发', '流体密度与粘度', '注入 · 生产 · 加热',
                '固体相备份', '导流系数更新', '▶ 流动求解',
                '扩散 · 毛管力', '固体相恢复', '▶ 传热求解',
                '固流换热 · 化学反应', '更新 time / step / dt']
        x0 = 560.0
        y0 = 66.0
        row = 38.0
        _Palette.text_fit(painter, palette, QtCore.QRectF(x0, 22, 420, 34),
                      'iterate 内部按此顺序执行', size=24.0, bold=True,
                      align=QtCore.Qt.AlignmentFlag.AlignLeft)
        for i, text in enumerate(subs):
            y = y0 + i * row
            major = text.startswith('\u25b6')
            rect = QtCore.QRectF(x0, y, 416.0, row - 8)
            _Palette.box(painter, palette, rect, '',
                         _Palette.layer(2 if major else 5, dark), dark, radius=4.0)
            _Palette.text_fit(painter, palette, QtCore.QRectF(x0 + 10, y, 396, row - 8),
                          text, size=21.0, bold=major,
                          align=QtCore.Qt.AlignmentFlag.AlignLeft
                                | QtCore.Qt.AlignmentFlag.AlignVCenter)

        _Palette.text_fit(painter, palette, QtCore.QRectF(24, 636, 950, 300),
                      '▪ 流动求解与传热求解是两个独立的线性系统，在同一时间步里按固定顺序先后求解。\n'
                      '▪ 每一步都会提交“下一步建议步长”，最终取所有建议里的最小值 —— 这就是自适应步长。\n'
                      '▪ 固体相（水合物 / 冰 / 干酪根）在流动求解前被临时弹出，因为固体不参与流动。',
                      size=22.0, kind='muted',
                      align=QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)


    # ------------------------------------------------------------------
    # 4. 界面地图
    # ------------------------------------------------------------------
    def _draw_gui_map(self, painter, palette, dark):
        """主窗口的分区."""
        def block(rect, text, index, radius=7.0, size=24.0):
            _Palette.box(painter, palette, rect, '', _Palette.layer(index, dark), dark,
                         radius=radius)
            _Palette.text_fit(painter, palette, rect, text, size=size, bold=False)

        block(QtCore.QRectF(30, 30, 940, 58),
              '菜单栏    文件 · 显示 · 操作 · 设置 · 帮助', 3, size=25.0)
        block(QtCore.QRectF(30, 100, 940, 50),
              '工具栏    工作路径 · 打开 · 保存 · 运行 / 暂停 / 停止 · ReadMe · 示例', 4, size=23.0)
        block(QtCore.QRectF(30, 164, 660, 330),
              '标签页区（顶部）\n\n'
              '代码编辑器 · 绘图页 · 本页（架构）\n'
              '文件浏览 · 示例浏览器 · 环境变量 · 样式表 ……', 2, size=25.0)
        block(QtCore.QRectF(706, 164, 264, 330), '右侧栏\n\n标签页总览\n\n输出面板', 1, size=24.0)
        block(QtCore.QRectF(30, 510, 940, 110),
              '控制台（后台线程执行脚本）\n可以直接敲任意 gui.xxx() 命令', 0, size=25.0)
        block(QtCore.QRectF(30, 634, 940, 46),
              '状态栏    运行状态灯 · 并行 · 版本号（→关于） · 进度 · 登录状态（→登录页）',
              5, size=23.0)
        _Palette.text_fit(painter, palette, QtCore.QRectF(30, 700, 940, 200),
                      '运行脚本的地方是"控制台线程"，界面在"GUI 线程"。\n'
                      '任何时候脚本里想动界面，都必须走 gui.xxx()（它会自动派发到 GUI 线程）。',
                      size=24.0, kind='muted')

    # ------------------------------------------------------------------
    # 5. 阅读路线
    # ------------------------------------------------------------------
    def _draw_reading(self, painter, palette, dark):
        """三条阅读路线."""
        lanes = [
            ('路线 A\n只想用', ['帮助 → 示例', '跑起来', '改参数再跑']),
            ('路线 B\n要建模', ['找最像的 demo', 'scen/', 'tfc/']),
            ('路线 C\n改行为', ['先试 fluids/\nreactions/', '再改 tfc/', '最后才 C++']),
        ]
        lane_h = 260.0
        for i, (name, steps) in enumerate(lanes):
            y = 70.0 + i * (lane_h + 30.0)
            _Palette.text_fit(painter, palette, QtCore.QRectF(20, y + 60, 200, 130),
                          name, size=30.0, bold=True,
                          align=QtCore.Qt.AlignmentFlag.AlignLeft
                                | QtCore.Qt.AlignmentFlag.AlignVCenter)
            x = 240.0
            width = 236.0
            for j, step in enumerate(steps):
                rect = QtCore.QRectF(x, y + 60.0, width, 130.0)
                _Palette.box(painter, palette, rect, '', _Palette.layer(i * 2 + j, dark),
                             dark, radius=10.0)
                _Palette.text_fit(painter, palette, rect, step, size=26.0)
                if j + 1 < len(steps):
                    _Palette.arrow(painter, palette,
                                   QtCore.QPointF(x + width + 4, y + 125.0),
                                   QtCore.QPointF(x + width + 22, y + 125.0))
                x += width + 26.0
        _Palette.text_fit(painter, palette, QtCore.QRectF(20, 20, 960, 46),
                      '三条阅读路线', size=38.0, bold=True,
                      align=QtCore.Qt.AlignmentFlag.AlignLeft)


    # ------------------------------------------------------------------
    # 6. demo 学习顺序
    # ------------------------------------------------------------------
    def _draw_demos(self, painter, palette, dark):
        """demo 的推荐学习顺序（阶梯）."""
        steps = [
            ('flow_1ph', '单相达西流', 12),
            ('flow_2ph', '两相驱替', 13),
            ('flow_dy', '流体惯性', 3),
            ('thermal', '纯传热', 9),
            ('hydrate', '水合物', 20),
            ('heavy_oil', '原位转化', 2),
            ('mech', '固体力学', 15),
        ]
        n = len(steps)
        left, right = 20.0, 980.0
        width = (right - left) / n - 8.0
        base_y, rise = 830.0, 92.0
        box_h = 150.0
        _Palette.text_fit(painter, palette, QtCore.QRectF(20, 24, 960, 56),
                      '推荐的 demo 学习顺序（由浅入深）',
                      size=40.0, bold=True, align=QtCore.Qt.AlignmentFlag.AlignLeft)
        _Palette.text_fit(painter, palette, QtCore.QRectF(20, 92, 960, 44),
                      '每个主题目录下都有十几个算例；'
                      '本页「示例集导读」一节列出了全部 13 个目录。',
                      size=24.0, kind='muted', align=QtCore.Qt.AlignmentFlag.AlignLeft)
        # ⚠️ **先画连线、再画方框**：反过来的话连线会从方框上穿过、压住里面的字
        #    （2026-10-24 实测：七条斜线正压在 flow_dy / thermal 的名字上）。
        #    连线画在「下方框的顶边 → 上方框的底边」之间 —— 那是台阶的斜缝，
        #    画完方框之后只露出缝里那一段，看起来才是「一级级往上走」。
        for i in range(1, n):
            x0 = left + (i - 1) * (right - left) / n + width / 2.0
            y0 = base_y - (i - 1) * rise
            x1 = left + i * (right - left) / n + width / 2.0
            y1 = base_y - i * rise + box_h
            _Palette.arrow(painter, palette,
                           QtCore.QPointF(x0 + 10, y0 + 2),
                           QtCore.QPointF(x1 - 10, y1 - 2))

        for i, (name, topic, count) in enumerate(steps):
            x = left + i * (right - left) / n
            y = base_y - i * rise
            rect = QtCore.QRectF(x, y, width, box_h)
            _Palette.box(painter, palette, rect, '', _Palette.layer(i, dark), dark, radius=10.0)
            _Palette.text_fit(painter, palette, QtCore.QRectF(x + 4, y + 14, width - 8, 46),
                          name, size=26.0, bold=True)
            _Palette.text_fit(painter, palette, QtCore.QRectF(x + 4, y + 64, width - 8, 40),
                          topic, size=23.0)
            _Palette.text_fit(painter, palette, QtCore.QRectF(x, y + 106, width, 34),
                          '%d 个' % count, size=21.0, kind='muted')


# ======================================================================
# 控件：架构页
# ======================================================================

class _ArchitectureView(QtWidgets.QWidget):
    """架构页（顶层控件）：顶部导航 + 左侧目录 + 右侧图文 + 底部入口按钮.

    Attributes:
        content: 右侧正文（``QTextBrowser`` 子类，**自带历史栈**）.
        toc: 左侧目录树.
        sections: ``{key: 页面 dict}`` —— 页内跳转与 ``gui.show_architecture(key)`` 都用它.
    """

    #: 正文里三种链接的协议前缀
    GUI_SCHEME = _Catalog.GUI_SCHEME
    DOC_SCHEME = _Catalog.DOC_SCHEME

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sections = {item['key']: item for item in _Catalog.entries()}
        self._figures = []
        self._syncing = False        # 防止「目录 ↔ 正文」互相触发成环
        self.context_actions = []

        #: 配图相关状态（见 :meth:`_place_figures`）
        self._placing = False        # 正在插图片：期间不要被 contentsChanged 递归触发
        self._figures_width = 0      # 上次按多宽渲染的（宽度没变就不重画）
        self._pending_ensure = False  # 已经排了一次「补回配图」的调用
        #: 拖动窗口时 ``resizeEvent`` 会连续触发，配图重画要防抖
        self._figure_timer = QtCore.QTimer(self)
        self._figure_timer.setSingleShot(True)
        self._figure_timer.setInterval(120)
        self._figure_timer.timeout.connect(self._refresh_figure_images)

        #: 浏览历史（**自己维护**，理由见 :meth:`_goto`）
        self._history = []
        self._history_index = -1
        #: 排版完成前请求过的小节（由 :meth:`_load` 补做，见那里的说明）
        self._pending_section = None
        #: 是否已经完成过一次整篇排版（``False`` 时文档里只有骨架）
        self._rendered = False

        self.content = self._create_content()
        self.toc = self._create_toc()
        self.navigation = self._create_navigation()

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.toc)
        splitter.addWidget(self.content)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([216, 864])

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.navigation)
        layout.addWidget(splitter, 1)

        # ⚠️ 两步走（2026-10-24）：先把**骨架**铺上去，整篇排版往后推。
        #    实测整篇渲染约 322 ms（markdown→HTML 90 + setHtml 39 + 6 张配图 89），
        #    全放在构造里就是「点菜单后界面卡半秒」。
        #    ⚠️ 这里**不引入线程**：剩下的 setHtml / 配图都是 Qt 绘制，
        #       本来就只能在 GUI 线程做（实测后台最多只能移走那 90 ms）。
        self._load_skeleton()
        self._sync_navigation()
        # 图片尺寸依赖视口宽度，而此刻控件还没 show（视口宽度不准）——
        # 所以整篇排版也必须在事件循环转起来、拿到真实宽度之后再做。
        #
        # ⚠️ 为什么**不是** ``singleShot(0, ...)``：0 ms 的定时器在事件循环**一开头**
        #    就触发，而此刻骨架还没真正画到屏幕上 ⇒ 那一帧被 300 ms 的排版占掉，
        #    用户看到的仍是「卡一下」。留一段延迟，让事件循环先把手头的绘制做完。
        #    实测：骨架帧本身只要 5~10 ms，整帧 245~305 ms。
        QtCore.QTimer.singleShot(self._RENDER_DELAY_MS, self._load)

    #: 骨架铺完后，等多久再做整篇排版（毫秒）.
    #:
    #: 唯一的用途：**让骨架那一帧先真正画到屏幕上**。
    #:
    #: ⚠️⚠️ 这个值不能是 0（2026-10-24 实测）：``singleShot(0, ...)`` 会在事件循环
    #: **一开头**就触发，此时骨架那帧还没画 ⇒ 被整篇排版（约 300 ms）占掉，
    #: 用户看到的**仍然是全文**，等于白拆。实测首帧内容与耗时：
    #:
    #: ==========  ==========  ==========  ==========
    #: 延迟         首帧上屏     正文就绪     首帧是骨架
    #: ==========  ==========  ==========  ==========
    #: 0 ms        297 ms      307 ms      否（全文）
    #: 50 ms         7 ms      287 ms      是
    #: 100 ms       13 ms      325 ms      是
    #: 200 ms       14 ms      434 ms      是
    #: ==========  ==========  ==========  ==========
    #:
    #: ⇒ 取 **50 ms**：骨架绘制本身只要 5~10 ms，50 ms 已经足够它上屏（剩下是给人眼的
    #: 余量）；再往上首帧**不再变快**，只是让正文更晚 —— 100 ms 就白多等约 38 ms。
    _RENDER_DELAY_MS = 50

    # ------------------------------------------------------------------
    # 构造各个部件
    # ------------------------------------------------------------------
    def _create_content(self):
        """创建正文控件，并把它的信号接到本控件.

        ⚠️ 用 ``MarkdownView``（``QTextBrowser`` 的子类）而不是自己解析 Markdown：
        它已经处理好"装了 ``markdown`` 库就转 HTML、否则回退 Qt 自带渲染"、
        以及"标题没有命名锚点"等一批坑。我们**只**接管"链接点了之后做什么"。
        """
        view = MarkdownView()
        view.setOpenLinks(False)
        view.setOpenExternalLinks(False)
        try:
            from zmlx.ui.alg import create_action
            # MarkdownView 默认的右键动作里「重新载入ReadMe」「登录」在本页没意义
            view.context_actions = [
                create_action(view, '从头阅读', icon='home', slot=view.home),
                create_action(view, '重新载入', icon='refresh', slot=self._load),
            ]
        except Exception:
            pass                     # 拿不到 create_action 就保留默认动作
        view.anchorClicked.connect(self._on_anchor_clicked)
        view.backwardAvailable.connect(self._sync_navigation)
        view.forwardAvailable.connect(self._sync_navigation)
        view.verticalScrollBar().valueChanged.connect(self._sync_toc)
        # 正文被**整篇重渲染**时把配图补回来（右键切换 markdown 渲染方式就这样，
        # 见 MarkdownView._toggle_html）—— 否则会看到裸的 ``@@figure:layers@@``。
        view.document().contentsChanged.connect(self._on_contents_changed)
        return view

    def _create_toc(self):
        """左侧目录树（单列、无表头）."""
        tree = QtWidgets.QTreeWidget()
        tree.setHeaderHidden(True)
        tree.setColumnCount(1)
        tree.setIndentation(12)
        tree.setUniformRowHeights(True)
        tree.setMinimumWidth(150)
        tree.setToolTip('点击目录项可以直接跳到那一节（不记入历史，'
                        '所以「返回」仍然回到你原来读的地方）')
        tree.itemClicked.connect(self._on_toc_clicked)
        return tree

    def _create_navigation(self):
        """顶部导航条：回到开头 / 返回 / 前进 + 当前位置.

        三个按钮**直接**连到 ``QTextBrowser.home()`` / ``backward()`` / ``forward()``。
        ⚠️ 这里**不用** ``gui.alg.create_action``：那个包装会在执行后调 ``gui.refresh()``，
        而本页的导航是纯本地操作，不该去刷新别的标签页。
        """
        bar = QtWidgets.QToolBar(self)
        bar.setMovable(False)
        bar.setFloatable(False)
        bar.setIconSize(QtCore.QSize(16, 16))

        def make(text, icon_name, tip, slot):
            try:
                from zmlx.ui.settings import load_icon
                action = QtGui.QAction(load_icon(icon_name), text, bar)
            except Exception:
                action = QtGui.QAction(text, bar)
            action.setToolTip(tip)
            action.triggered.connect(lambda _=False: self._navigate(slot))
            bar.addAction(action)
            return action

        make(' 回到开头', 'home', '回到第一页（总览）', self._home)
        self._back_action = make(' 返回', 'new', '回到上一个位置（Alt+←）', self._back)
        self._back_action.setShortcut(QtGui.QKeySequence('Alt+Left'))
        self._forward_action = make(' 前进', 'refresh', '前进到下一个位置（Alt+→）', self._forward)
        self._forward_action.setShortcut(QtGui.QKeySequence('Alt+Right'))

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                             QtWidgets.QSizePolicy.Policy.Preferred)
        bar.addWidget(spacer)

        self._position = QtWidgets.QLabel('')
        self._position.setToolTip('当前位置（序号 / 总数 · 小节名）；小节名也是 '
                                  'gui.show_architecture(名字) 的参数')
        bar.addWidget(self._position)
        return bar

    def _navigate(self, slot):
        """执行一次导航，并立刻校正按钮状态与位置文字.

        ⚠️ ``backwardAvailable`` / ``forwardAvailable`` 只在"可用性**变化**"时发信号，
        所以"还能继续后退"时连点返回不会再发信号 —— 位置文字就会停在旧值。这里主动补一次。
        """
        try:
            slot()
        except Exception as err:
            print('Warning: 导航失败: %s' % err)
        self._sync_navigation()
        self._sync_toc()

    # ------------------------------------------------------------------
    # 渲染
    # ------------------------------------------------------------------
    def _load_skeleton(self):
        """先铺一层**轻量骨架**：目录 + 一句「正在排版…」，正文留待下一轮事件循环.

        为什么要分两步
        --------------

        整篇渲染实测约 **322 ms**（``markdown`` 库转 HTML 90 + ``setHtml`` 39 +
        6 张配图 ``QPainter`` 渲染 89 + 杂项），全部塞进 ``__init__`` 就是
        「点菜单后界面明显卡一下」。

        ⚠️ 为什么**不**把这个活挪到后台线程：其中只有那 90 ms 的 markdown→HTML 是
        纯 Python，剩下的 ``setHtml`` / 配图渲染都是 **Qt** 操作，本来就只能在 GUI 线程做。
        实测后台最多只能移走 1/3，却要额外背上一套线程生命周期与关标签收尾 —— 不划算。

        ⚠️ 骨架里**不放** ``@@figure:`` 占位：占位符一旦出现在文档里，
        :meth:`_on_contents_changed` 会把它当成「图片丢了」而去补救。骨架的使命只是
        「让标签页立刻有形」，真正的排版由 :meth:`_load` 一次做完。
        """
        marks = list(_Catalog.PAGE_KEYS)
        tree = self.toc
        tree.clear()
        for item in _Catalog.entries():
            node = QtWidgets.QTreeWidgetItem([item['title']])
            node.setData(0, QtCore.Qt.ItemDataRole.UserRole, item['key'])
            node.setToolTip(0, item['key'])
            tree.addTopLevelItem(node)
        if tree.topLevelItemCount() > 0:
            tree.setCurrentItem(tree.topLevelItem(0))
        self.content.setPlainText('正在排版……（共 %d 节）' % len(marks))
        self.content.set_status('zmlx 架构：正在排版，请稍候…')

    def _load(self):
        """（重新）渲染全部页面.

        一次渲染**全部**页面、每页一个 ``##`` 标题 —— 这样正文里的 ``#小节名`` 一定找得到目标
        （``scrollToAnchor`` 与历史栈都要求"目标就在文档里"）。

        ⚠️ 标题一律写成 **Markdown 语法**（``## 标题``），不写裸 ``<h2>``：``MarkdownView``
        有两条渲染路径（装了 ``markdown`` 库 → HTML；没装 → Qt 自带 ``setMarkdown``），
        后者会把裸 HTML 块后面的内容整段吞掉，而 :meth:`_current_key` 要靠
        ``blockFormat().headingLevel()`` 认标题。
        """
        parts = ['## %s —— zmlx 代码库入门' % _Catalog.TITLE,
                 '*图文并茂地说明这个仓库由哪些部分组成、它们之间如何依赖与协作，'
                 '以及每个功能在界面上的入口。左侧是目录，正文里的蓝色文字都可以点。*']
        for item in _Catalog.entries():
            parts.append('## %s' % item['title'])
            body = _Catalog.text(item['body']).strip()
            parts.append(body)
            figure = item.get('figure')
            if figure is not None:
                parts.append('@@figure:%s@@' % figure[0])   # 占位，稍后换成真控件

        self.content.set_markdown('\n\n'.join(parts), base_url=_Catalog.ROOT)
        self.content.set_link_callback(self._on_link)
        self.content.set_status('zmlx 架构：左侧目录可跳转，顶部可返回 / 前进')
        self._place_figures()
        self._reload_toc()
        # ⚠️ 必须在补做跳转**之前**置位：``show_section`` 要看到 ``_rendered`` 为真才会真的跳。
        self._rendered = True

        # ⚠️ 补做「排版前就请求过的小节跳转」：``gui.show_architecture('pitfalls')`` 会在
        #    控件刚构造完（还是骨架）、``singleShot(0, _load)`` 还没跑时就调 ``show_section``。
        #    那次跳转作用在**马上要被替换掉的**骨架上 ⇒ 不补做就等于跳转丢失
        #    （2026-10-24 实测：排版完成后 scroll 仍是 0，而排版后再跳是 29883）。
        pending, self._pending_section = self._pending_section, None
        if pending is not None:
            try:
                self.show_section(pending)
            except Exception as err:
                print('Warning: 打开小节 <%s> 失败: %s' % (pending, err))

    #: 配图左右各留多少像素（让图片与正文左边界对齐）
    _FIGURE_MARGIN = 8

    def _figure_width(self):
        """配图应渲染的宽度（逻辑像素）：跟着正文视口走，两侧留一点边距.

        Returns:
            int: 不小于 240 的像素宽度。
        """
        width = int(self.content.viewport().width()) - 2 * self._FIGURE_MARGIN
        return max(240, width)

    @staticmethod
    def _figure_url(key):
        """配图在文档里的**资源名**（同时用作 ``QTextImageFormat`` 的名字）.

        ⚠️ 必须是 URL；重画时靠这个**同一个名字**覆盖资源（``addResource`` 同名即替换），
        所以**不要**每次生成随机名 —— 那样旧图会一直留在文档资源表里。

        Args:
            key: 配图的键（``layers`` / ``demos`` …）。

        Returns:
            QtCore.QUrl: ``zml-figure://<key>``。
        """
        return QtCore.QUrl('zml-figure://%s' % key)

    def _figure_height(self, aspect, width):
        """按声明的**宽高比**算出实际显示高度.

        ⚠️ 高度必须跟着宽度走，不能写死：``_Figure.paintEvent`` 用
        ``min(w, h) / 1000`` 缩放 1000×1000 的参考画布 —— 只要 ``h`` 小于 ``w``，
        内容就会被**按高度**缩小、两侧留白，字也跟着变小（2026-10-24 之前声明的
        ``860×330`` 就这么把图压到 1/3，文字全糊在一起）。

        Args:
            aspect: 声明的 ``高 / 宽``。
            width: 实际列宽。

        Returns:
            int: 显示高度（像素）。
        """
        return max(120, int(round(float(width) * float(aspect))))

    def _render_figure(self, fig, width, height):
        """把一个**离屏**的 :class:`_Figure` 画成 :class:`QtGui.QImage`.

        ⚠️ ``_Figure`` 现在只剩「渲染器」这一个身份：它从不 ``show()``，
        ``paintEvent`` 里那套 1000×1000 逻辑画布 + ``painter.scale`` 的代码**一行没改**。

        ⚠️ 按 ``devicePixelRatio`` 放大**位图尺寸**再交给 Qt 按逻辑尺寸显示，否则高分屏上
        位图会被放大得发虚（这正是当年 ``MatplotWidget`` 停用 ``FigureCanvasQTAgg``
        之后留下的老问题，见 ``ui/widgets/plt.py`` 的模块文档）。

        ⚠️⚠️ **不要**再对 ``painter`` 调 ``scale(ratio, ratio)``：``QImage`` 一旦设了
        ``setDevicePixelRatio``，``QPainter`` 的逻辑坐标系**已经**按它放大了 ——
        再手动缩放就是**两次**，图会被放大 ~DPR 倍、右下角整块裁掉
        （2026-10-24 实测：175% 缩放下 1029×330 的图被画成 1800×577 只露出左上角）。

        Args:
            fig: 待渲染的 ``_Figure``（父对象给它的调色板决定配色）。
            width: 逻辑宽度。
            height: 逻辑高度。

        Returns:
            QtGui.QImage: 可直接 ``document().addResource`` 的位图。
        """
        width = max(1, int(width))
        height = max(1, int(height))
        ratio = 1.0
        try:
            ratio = max(1.0, float(self.devicePixelRatioF()))
        except Exception:
            pass
        image = QtGui.QImage(int(width * ratio), int(height * ratio),
                             QtGui.QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(QtCore.Qt.GlobalColor.transparent)
        image.setDevicePixelRatio(ratio)

        fig.set_wanted_size(width, height)
        fig.resize(width, height)
        painter = QtGui.QPainter(image)
        try:
            fig.render(painter)
        finally:
            painter.end()
        return image

    def _place_figures(self):
        """把正文里的 ``@@figure:键@@`` 占位换成**真正嵌在文档里的图片**.

        ⚠️⚠️ **2026-10-24 改写（缺陷见 PLAN ``T-20261023-05``）**：旧实现造一个
        ``QWidget`` 挂到 ``self.content`` 下，再把 ``blockBoundingRect()`` 返回的
        **文档坐标**直接当控件坐标用 —— 两者不是一个坐标系：文档 y 从 0 数到三万多，
        控件 y 只在视口那么高之内。后果（当时实测）：图被钉在屏幕固定位置（**不随滚动**）、
        恰好落在视口内的那张**压住正文**、其余全在视口外（**窗口越小越看不到**）。

        现在改为**文档内嵌图片**：``QTextCursor.insertImage`` 把它放进段落里，
        滚动 / 换行 / 选中 / 打印全部由 Qt 负责，不再有「两套坐标系」。

        ⚠️ 图片宽度依赖**视口宽度**，而 :meth:`_load` 在控件 ``show()`` 之前就跑
        ⇒ 首帧宽度可能不准，由 :meth:`_refresh_figure_images` 在 resize / 换主题时重画。
        """
        self._figures = []
        self._placing = True
        document = self.content.document()
        width = self._figure_width()
        try:
            for item in _Catalog.entries():
                figure = item.get('figure')
                if figure is None:
                    continue
                key, caption, box_w, box_h = figure
                # 只取**宽高比**：实际高度跟着当前列宽走（见 :meth:`_figure_height`）
                aspect = float(box_h) / max(1.0, float(box_w))
                height = self._figure_height(aspect, width)

                found = document.find('@@figure:%s@@' % key)
                if found.isNull():
                    continue

                # 1) 删掉占位行（只删行内文字，段落本身留着给图片当容器）
                cursor = QtGui.QTextCursor(found)
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.EndOfBlock,
                                    QtGui.QTextCursor.MoveMode.KeepAnchor)
                if cursor.hasSelection():
                    cursor.removeSelectedText()

                # 2) 离屏画一张图，插进这个空段落
                fig = _Figure(self.content, kind=key, caption=caption)
                # ⚠️⚠️ 必须 ``hide()``，光设 ``WA_DontShowOnScreen`` 不够：
                #    那是「不映射到屏幕」，但 ``QWidget.grab()`` / ``render()`` **仍会
                #    递归绘制子控件** —— 六张图全挂在 ``content`` 的 (0,0)，最晚创建的
                #    那张会盖在最上面，截图/打印时看到的是它而不是正文
                #    （2026-10-24 实测：截图上永远是 ``reading`` 那张）。
                #    ``hide()`` 之后 ``isVisible()`` 为假、不再被绘制，而 ``render()``
                #    对隐藏控件**照常可用**（这正是离屏渲染的标准用法）。
                fig.setAttribute(QtCore.Qt.WidgetAttribute.WA_DontShowOnScreen, True)
                fig.hide()
                image = self._render_figure(fig, width, height)
                url = self._figure_url(key)
                document.addResource(
                    QtGui.QTextDocument.ResourceType.ImageResource, url, image)
                fmt = QtGui.QTextImageFormat()
                fmt.setName(url.toString())
                fmt.setWidth(width)
                fmt.setHeight(height)
                position = cursor.position()
                cursor.insertImage(fmt)
                # 存的是**宽高比**而不是高度：窗口一变，高度要按新宽度重算
                self._figures.append((key, position, fig, aspect))
        finally:
            self._placing = False
        self._figures_width = width

    def _refresh_figure_images(self):
        """按**当前视口宽度**与**当前调色板**重画所有配图.

        ``resizeEvent`` / ``changeEvent``（换主题、换字体）/ :meth:`refresh` 都走这里。
        资源名不变 ⇒ ``addResource`` 直接替换旧位图，再 ``markContentsDirty`` 让排版重算。
        """
        if not self._figures:
            return
        document = self.content.document()
        width = self._figure_width()
        for key, position, fig, aspect in self._figures:
            try:
                height = self._figure_height(aspect, width)
                image = self._render_figure(fig, width, height)
                url = self._figure_url(key)
                document.addResource(
                    QtGui.QTextDocument.ResourceType.ImageResource, url, image)
                fmt = QtGui.QTextImageFormat()
                fmt.setName(url.toString())
                fmt.setWidth(width)
                fmt.setHeight(height)
                # 图片只占**一个**字符（object replacement char）⇒ 选中它再套格式
                cursor = QtGui.QTextCursor(document)
                cursor.setPosition(int(position))
                cursor.setPosition(int(position) + 1,
                                   QtGui.QTextCursor.MoveMode.KeepAnchor)
                cursor.setCharFormat(fmt)
            except Exception as err:
                print('Warning: 重画配图 <%s> 失败: %s' % (key, err))
        document.markContentsDirty(0, document.characterCount())
        self._figures_width = width

    def _ensure_figures(self):
        """文档里还留着 ``@@figure:`` 占位就重新放一遍.

        ⚠️ 什么时候会留占位：``MarkdownView`` 右键切换「用 markdown 库渲染」时会
        ``setHtml``/``setMarkdown`` **整篇重渲染**，而源码里本来就写着占位符 ——
        于是图片没了、占位文字回来了。这一步是自愈：发现占位就重新插入。
        """
        if self._placing:
            return
        document = self.content.document()
        if document.find('@@figure:').isNull():
            return
        self._place_figures()

    def _on_contents_changed(self):
        """``contentsChanged`` 回调：只在「占位符回来了」时才排一次补救.

        ⚠️ 我们自己插图片/改图片格式也会触发这个信号，所以必须用 :attr:`_placing`
        与 :attr:`_pending_ensure` 两道闸挡住递归；判断依据是**文档里是否还有占位符**，
        没有就直接返回 —— 这样本回调对正常渲染是**零动作**的。
        """
        if getattr(self, '_placing', True) or getattr(self, '_pending_ensure', True):
            return
        try:
            if self.content.document().find('@@figure:').isNull():
                return
        except Exception:
            return
        self._pending_ensure = True
        # 延到本轮排版结束再做：此刻文档正处在 setHtml/setMarkdown 的中途
        QtCore.QTimer.singleShot(0, self._do_ensure_figures)

    def _do_ensure_figures(self):
        """（内部）执行一次延后的「补回配图」."""
        self._pending_ensure = False
        try:
            self._ensure_figures()
        except Exception as err:
            print('Warning: 补回配图失败: %s' % err)

    # ------------------------------------------------------------------
    def _reload_toc(self):
        """按 :data:`_PAGES` 的顺序重建左侧目录."""
        tree = self.toc
        tree.clear()
        for item in _Catalog.entries():
            node = QtWidgets.QTreeWidgetItem([item['title']])
            node.setData(0, QtCore.Qt.ItemDataRole.UserRole, item['key'])
            node.setToolTip(0, item['key'])
            tree.addTopLevelItem(node)
        if tree.topLevelItemCount() > 0:
            tree.setCurrentItem(tree.topLevelItem(0))

    def _on_toc_clicked(self, item, column):
        """点目录：跳到对应标题（**记入历史**，所以「返回」能回到原来读的地方）."""
        key = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(key, str) or key not in self.sections:
            return
        self._goto(key, record=True)
        self.content.setFocus()

    def _scroll_to_heading(self, key):
        """把某一节的标题精确对齐到视口顶部."""
        title = self.sections[key]['title']
        block = self.content.document().begin()
        while block.isValid():
            if self._is_heading(block) and self._plain(block.text()) == title:
                try:
                    rect = self.content.document().documentLayout().blockBoundingRect(block)
                    self.content.verticalScrollBar().setValue(int(rect.top()))
                except Exception:
                    pass
                return
            block = block.next()

    @staticmethod
    def _is_heading(block):
        """判断一个文本块是不是标题.

        ⚠️ 两条渲染路径下 ``headingLevel`` 都可能拿不到值（Qt 自带渲染路径有时不设这个格式），
        所以再看一眼"有没有设置标题级别这个属性"。
        """
        try:
            if block.blockFormat().headingLevel() > 0:
                return True
        except Exception:
            pass
        try:
            fmt = block.blockFormat()
            for name in ('HeadingLevel', 'heHeadingLevel'):
                prop = getattr(QtGui.QTextFormat.Property, name, None)
                if prop is not None and fmt.hasProperty(prop):
                    return True
        except Exception:
            return False
        return False

    @staticmethod
    def _plain(text):
        """把标题里的行内标记去掉再比较（目录里是纯文字，正文里可能带 ``**``）."""
        return str(text).replace('*', '').replace('`', '').strip()

    def _current_key(self):
        """视口顶部所在的小节（还没到第一个标题时返回 ``None``）."""
        titles = {item['title']: item['key'] for item in _Catalog.entries()}
        cursor = self.content.cursorForPosition(QtCore.QPoint(0, 0))
        block = cursor.block()
        while block.isValid():
            if self._is_heading(block):
                key = titles.get(self._plain(block.text()))
                if key is not None:
                    return key
            block = block.previous()
        return None

    def _sync_toc(self, *args):
        """滚动正文时，把目录高亮到当前小节."""
        if self._syncing:
            return
        key = self._current_key()
        if key is None:
            return
        for i in range(self.toc.topLevelItemCount()):
            node = self.toc.topLevelItem(i)
            if node.data(0, QtCore.Qt.ItemDataRole.UserRole) == key:
                if node is not self.toc.currentItem():
                    self._syncing = True
                    try:
                        self.toc.setCurrentItem(node)
                        self.toc.scrollToItem(node)
                    finally:
                        self._syncing = False
                return

    def _sync_navigation(self, *args):
        """刷新顶部三个按钮的可用状态，以及"当前位置"文字（由自己维护的历史栈驱动）."""
        try:
            can_back = self._history_index > 0
            can_forward = 0 <= self._history_index < len(self._history) - 1
            if getattr(self, '_back_action', None) is not None:
                self._back_action.setEnabled(can_back)
            if getattr(self, '_forward_action', None) is not None:
                self._forward_action.setEnabled(can_forward)
        except Exception:
            pass
        keys = [item['key'] for item in _Catalog.entries()]
        key = self._current_key()
        index = keys.index(key) + 1 if key in keys else 1
        # 骨架阶段（还没排版）视口顶部认不出小节 ⇒ 显示「…」而不是字面的 None
        show = key if key is not None else '…'
        try:
            self._position.setText('  %02d / %02d  ·  %s  ' % (index, len(keys), show))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 交互入口
    # ------------------------------------------------------------------
    def show_section(self, key=None):
        """跳到某一节（等价于点正文里的页内链接，**会记入历史**）.

        Args:
            key: 小节名（:attr:`sections` 的键，例如 ``'data_model'``）。
                为 ``None`` 或认不出时回到第一页。

        Returns:
            bool: 是否找到了这一节。
        """
        if key is None or key not in self.sections:
            self.content.home()
            self._sync_navigation()
            self._sync_toc()
            return False
        # 还没排版完（文档里只有骨架）：先记下，等 :meth:`_load` 排完再补做 ——
        # 否则这次跳转作用在马上要被替换掉的骨架上，等于白跳。
        if not self._rendered:
            self._pending_section = key
            return True
        self._goto(key, record=True)
        return True

    def _goto(self, key, record=False):
        """把某一节的标题滚到视口顶部.

        ⚠️ **不使用 ``scrollToAnchor``**：``MarkdownView`` 有两条渲染路径，其中
        「Qt 自带 ``setMarkdown``」那条**不给标题建命名锚点**，``scrollToAnchor`` 会静默失败
        （实测：滚动条纹丝不动）。所以这里一律**按标题文字**找块，再自己设滚动值 ——
        两条渲染路径都管用。

        ⚠️⚠️ **浏览历史是自己维护的**（:attr:`_history`），不是靠 `QTextBrowser` 的历史栈。

        原因（实测过，别再改回去）：`QTextBrowser` 只把**用户真的点了超链接**记入历史；
        代码里调 `scrollToAnchor()` / `ensureCursorVisible()` / `setTextCursor()` 都**不会**
        产生历史记录 —— `isBackwardAvailable()` 从头到尾是 `False`。而本页有一半跳转来自
        "目录点击"与"打开某一节"，那些必须也能「返回」。

        Args:
            key: 小节名。
            record: 是否把这次跳转记入历史（页内链接 / 目录点击要记；``home`` 重置。
                程序内部的"定位"不记）。
        """
        title = self.sections[key]['title']
        document = self.content.document()
        block = document.begin()
        while block.isValid():
            if self._is_heading(block) and self._plain(block.text()) == title:
                try:
                    rect = document.documentLayout().blockBoundingRect(block)
                    self.content.verticalScrollBar().setValue(int(rect.top()))
                except Exception as err:
                    print('Warning: 跳转 <%s> 失败: %s' % (key, err))
                if record:
                    self._push(key)
                self._sync_navigation()
                self._sync_toc()
                return
            block = block.next()

    # ------------------------------------------------------------------
    # 浏览历史（自己维护的栈）
    # ------------------------------------------------------------------
    def _push(self, key):
        """把 ``key`` 记入历史；若当前不在栈顶（用户回退过），先截断"未来"."""
        if isinstance(key, str) and len(key) > 0:
            if 0 <= self._history_index < len(self._history) - 1:
                del self._history[self._history_index + 1:]
            if len(self._history) == 0 or self._history[-1] != key:
                self._history.append(key)
            self._history_index = len(self._history) - 1

    def _current_entry(self):
        """历史栈里当前位置对应的小节（没有历史时返回 ``None``）."""
        if 0 <= self._history_index < len(self._history):
            return self._history[self._history_index]
        return None

    def _back(self):
        """后退一步；没有历史时不动."""
        if self._history_index > 0:
            self._history_index -= 1
            self._goto(self._history[self._history_index], record=False)

    def _forward(self):
        """前进一步."""
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._goto(self._history[self._history_index], record=False)

    def _home(self):
        """回到第一页（并清空"未来"那一段历史）."""
        self._goto('overview', record=True)
        self._history_index = len(self._history) - 1

    def showEvent(self, event):
        super().showEvent(event)
        # 第一次显示才知道真实视口宽度 ⇒ 按它重画一遍配图
        if self._figures_width != self._figure_width():
            self._refresh_figure_images()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # ⚠️ 拖动窗口时这个事件会连续触发，而重画 6 张图并不便宜 ⇒ 防抖到停下来再画
        if self._figures:
            self._figure_timer.start()

    def changeEvent(self, event):
        super().changeEvent(event)
        # 换主题（暗色 / 自定义样式表）或换字体：``_Figure`` 的配色是从 ``QPalette``
        # 现取的，位图必须跟着重画 —— 否则图会停在旧配色上（这正是旧实现
        # "不要缓存像素"那条注释的等价要求）。
        #
        # ⚠️ **不能在这里立即重画**：``PaletteChange`` 是**同步**派发的，
        #    此刻调色板往往还没传播到 ``content`` 的子控件；立即画出来用的是旧配色
        #    （2026-10-24 实测：切暗色后图仍是浅色背景）。交给防抖定时器，
        #    等本轮事件循环把调色板发完再画。
        if event.type() in (QtCore.QEvent.Type.PaletteChange,
                            QtCore.QEvent.Type.FontChange):
            if getattr(self, '_figures', None):
                self._figure_timer.start()

    def refresh(self):
        """GUI 刷新钩子（切回本页时被调）：只做很轻的事.

        ⚠️ **不重建正文** —— 那会丢掉滚动位置与历史栈。这里只把按钮状态核对一遍；
        配图只在「宽度变了」或「占位符又回来了」时才动。
        """
        self._sync_navigation()
        self._ensure_figures()
        if self._figures and self._figures_width != self._figure_width():
            self._refresh_figure_images()

    def cleanup_before_tab_close(self):
        """关标签页时的收尾：停掉防抖定时器，把**离屏渲染器**摘掉（**不阻塞**）.

        ⚠️ 配图现在在文档里是**位图资源**（滚动/排版由 Qt 管），这几个 ``_Figure``
        只是渲染用的离屏控件 —— 留着会白白占内存，所以一并删掉。
        """
        try:
            self._figure_timer.stop()
        except Exception:
            pass
        for _key, _position, fig, _height in self._figures:
            try:
                fig.setParent(None)
                fig.deleteLater()
            except Exception:
                pass
        self._figures = []

    # ------------------------------------------------------------------
    # 链接
    # ------------------------------------------------------------------
    def _on_anchor_clicked(self, url):
        """``anchorClicked`` 信号 → 统一交给 :meth:`_on_link`."""
        text = url.toString() if hasattr(url, 'toString') else str(url)
        self._on_link(text)

    def _on_link(self, url):
        """处理正文里的一次链接点击.

        Args:
            url: 目标地址原文。

        Returns:
            bool: 一律返回 ``True`` —— 点了做什么完全由本控件决定，**不交给 Qt 默认行为**
            （默认会把自定义协议丢给系统浏览器，弹一个"找不到应用"）。
        """
        if not isinstance(url, str) or len(url) == 0:
            return True
        if url.startswith('#'):
            key = url[1:]
            if key in self.sections:
                self._goto(key, record=True)      # 页内跳转：记入历史，可「返回」
            return True
        if url.startswith(self.GUI_SCHEME):
            return self._open_gui(url[len(self.GUI_SCHEME):].split('/')[-1])
        if url.startswith(self.DOC_SCHEME):
            return self._open_doc(url[len(self.DOC_SCHEME):])
        return self._open_url(url)

    def _open_gui(self, name):
        """执行 ``gui.<name>()`` —— 等价于点那个菜单项.

        命令不存在时**降级为一句说明**，而不是让链接"点了没反应"。

        ⚠️ 这里**不能**再调 ``gui.show_architecture()``：那会把本页又切回最前面，
        用户就看不到刚打开的那一页了。
        """
        name = (name or '').strip()
        if len(name) == 0:
            return True
        if name == 'show_architecture':       # 「帮助 → 架构」指向本页自己
            self.content.home()
            return True
        try:
            from zmlx.ui.gui_buffer import gui as _gui
            if _gui.exists():
                func = _gui.get().get_func(name)
                if callable(func):
                    func()
                    return True
        except Exception as err:
            print('Warning: 执行 gui.%s() 失败: %s' % (name, err))
            return True
        self._inform('这个版本里没有 gui.%s()' % name,
                     '本页记录的入口是 gui.%s()，但当前界面里没有注册这个命令。\n\n'
                     '可能是这一版还没有这个功能，或者它被改名了。' % name)
        return True

    def _open_doc(self, relative):
        """打开 ``zmlx://doc/...`` 指向的文档或源码.

        - **目录**：按 ``ReadMe.md`` → ``README.md`` → ``AGENTS.md`` → ``__init__.py`` 的顺序找；
        - **``.md`` 文件**：用 ``MarkdownView`` 开一个标签页；
        - **其它文件**：用代码编辑器打开；不行就交给系统。
        """
        relative = (relative or '').strip().strip('/')
        if len(relative) == 0:
            return True
        path = os.path.normpath(os.path.join(_Catalog.ROOT, relative))
        if os.path.isdir(path):
            for name in ('ReadMe.md', 'README.md', 'AGENTS.md'):
                candidate = os.path.join(path, name)
                if os.path.isfile(candidate):
                    return self._open_markdown(candidate, relative)
            candidate = os.path.join(path, '__init__.py')
            if os.path.isfile(candidate):
                return self._open_code(candidate)
            return self._open_path(path)
        if not os.path.isfile(path):
            self._inform('找不到 %s' % relative,
                         '本机没有这个路径：\n%s\n\n它可能已经改名或被移动了。' % path)
            return True
        if path.lower().endswith('.md'):
            return self._open_markdown(path, os.path.basename(path))
        return self._open_code(path)

    def _open_code(self, path):
        """用主窗口的代码编辑器打开一个源文件."""
        try:
            from zmlx.ui.gui_buffer import gui as _gui
            if _gui.exists():
                _gui.open_code(path)
                return True
        except Exception as err:
            print('Warning: 打开源码 <%s> 失败: %s' % (path, err))
        return self._open_path(path)

    def _open_markdown(self, path, caption):
        """用 ``MarkdownView`` 开一个标签页显示文档（与「帮助 → ReadMe」同一套控件）."""
        try:
            from zmlx.system import read_text
            from zmlx.ui.gui_buffer import gui as _gui
            if not _gui.exists():
                raise RuntimeError('当前没有 GUI')
            text = read_text(path, encoding='utf-8')
            if not text:
                raise FileNotFoundError(path)
            base = os.path.dirname(path)

            def oper(widget):
                widget.set_markdown(text, base_url=base)
                widget.set_status(path)

            _gui.get_widget(the_type=MarkdownView, caption=caption or os.path.basename(path),
                            on_top=True, icon='info', oper=oper)
            return True
        except Exception as err:
            print('Warning: 打开文档 <%s> 失败: %s' % (path, err))
        return self._open_path(path)

    @staticmethod
    def _open_path(path):
        """兜底：交给系统（资源管理器 / 默认程序）打开."""
        try:
            from zmlx.algs import startfile
            startfile(path)
        except Exception as err:
            print('Warning: 无法打开 <%s>: %s' % (path, err))
        return True

    @staticmethod
    def _open_url(url):
        """普通网址：交给 ``open_url``（界面里开标签页，否则系统浏览器）."""
        try:
            from zmlx.ui.alg import open_url
            open_url(url=url)
        except Exception as err:
            print('Warning: 打开网址 <%s> 失败: %s' % (url, err))
        return True

    @staticmethod
    def _inform(title, text):
        """弹一个信息框（无头模式下自动变成空操作）."""
        try:
            from zmlx.ui.gui_buffer import gui as _gui
            _gui.information(title, text)
        except Exception:
            print('%s：%s' % (title, text))


# ======================================================================
# 入口：菜单「帮助 → 架构」
# ======================================================================

def show_architecture(page=None):
    """打开（或切到）「架构」标签页，可直达某一节.

    Args:
        page: 可选的小节名（见 :data:`_Catalog.PAGE_KEYS`，例如 ``'data_model'``）。
            不给时打开第一页（保持用户上次看到的位置）。

    Example:
        控制台里直接敲::

            gui.show_architecture()                 # 打开本页
            gui.show_architecture('troubleshooting')  # 直接跳到"报错排查"

    ⚠️ 与其它 ``extra_setups`` 的 ``show_xxx`` 一样：这里**只派发命令**，真正开标签页的动作
    在 :func:`_open` 里 —— 这样无论菜单、脚本还是后台线程调用，"开标签页"这件事都发生在
    GUI 线程里。
    """
    from zmlx.ui.gui_buffer import gui as _gui
    _gui.command('show_architecture', page=page)


def _open(page=None):
    """真正打开标签页（注册成命令 ``show_architecture``，故只在 GUI 线程里执行）."""
    from zmlx.ui.gui_buffer import gui as _gui

    def oper(widget):
        # ⚠️ 这里只做「记住怎么重放我」一件事：get_widget 每次调用都会跑到 oper
        #    （点菜单也算），放跳转 / 刷新进去就等于"点一次菜单跳一次 / 刷一次"。
        widget.gui_restore = 'gui.show_architecture()'
        if page is not None:
            try:
                widget.show_section(page)
            except Exception as err:
                print('Warning: 打开小节 <%s> 失败: %s' % (page, err))

    _gui.get_widget(
        the_type=_ArchitectureView,
        caption=_Catalog.TITLE,
        on_top=True,
        icon='info',
        oper=oper,
        tooltip='zmlx 代码库的图文入门：分层结构、子包职责、核心数据模型、物理模型、'
                'API 速查、示例导读、界面地图、常见陷阱与报错排查',
    )


def provide_gui_setup():
    """把菜单项与命令挂上去（由 ``extra_setups/__init__.py`` 以**类型探测**方式调用）.

    为什么是"类型探测"而不是普通的 ``setup_ui``
    ------------------------------------------

    本模块顶部就 ``import MarkdownView``（控件要用它），在没有 Qt 的环境里这一句会失败。
    所以 ``extra_setups/__init__.py`` 里那一段用 ``getattr(module, 'provide_gui_setup', None)``
    去取 —— **取不到就跳过**：模块缺失 / 导入失败时那一行是空操作，不会带崩整个 ``setup_ui``。

    名字不叫 ``setup_ui`` 也是**有意**的：挂载方式一眼就能看出来不是走 ``extra_setups``
    里那批统一的 ``setup_ui`` 机制。

    Returns:
        bool: 本次是否真的挂上了（重复调用返回 ``False``）。
    """
    from zmlx.system import app_data
    from zmlx.ui.gui_buffer import gui as _gui

    marker = 'zmlx.ui.extra_setups.architecture.setup_done'
    if app_data.get(marker, False):
        return False
    app_data.put(marker, True)

    # 命令：菜单项与 gui.show_architecture() 指向**同一个**函数，不会两边各写一套
    _gui.add_func('show_architecture', _open)

    # 菜单：「帮助 → 架构」。⚠️ 菜单标题必须与 main.py 里逐字一致（'帮助'），
    # 否则 get_menu 会另建一个同名顶层菜单，界面上就会出现两个「帮助」。
    _gui.add_action(
        menu='帮助',
        name='architecture',
        text=_Catalog.TITLE,
        icon='info',
        tooltip='zmlx 代码库的图文入门：分层结构、子包职责、核心数据模型、物理模型、'
                'API 速查、示例导读、界面地图（支持返回 / 前进）',
        slot=show_architecture,
        is_enabled=lambda: not _gui.is_running(),
        # ⚠️ **必须显式给 is_visible**：Action.update_view 里 is_visible 缺省时**跟随**
        #    is_enabled —— 不写这一行，仿真跑起来时这一项是"消失"而不是"置灰"。
        is_visible=lambda: True,
        overwrite=False,
    )
    return True


# ======================================================================
# 自测
# ======================================================================

def test_1():
    """单独运行本文件：``python -m zmlx.ui.extra_setups.architecture``."""
    import sys
    app = QtWidgets.QApplication(sys.argv)
    widget = _ArchitectureView()
    widget.setWindowTitle('架构 —— zmlx 代码库入门')
    widget.resize(1120, 780)
    widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    test_1()
