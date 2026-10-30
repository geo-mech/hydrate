# zmlx.ui — 图形用户界面

## 概述

`zmlx.ui` 提供基于 PyQt6（自动降级至 PyQt5）的完整图形用户界面系统，包括多标签页编辑器、代码编辑器、文件浏览器、控制台（后台线程执行脚本）、matplotlib 绘图、图像查看、环境变量管理等功能。（PDF 查看由插件 `plugins/builtin/pdf_view.py` 提供，默认启用，依赖可选库 `PyQt6-WebEngine`。）

**设计目标**：
- 提供最基础的 UI 功能
- 后续将逐步精简，减少依赖以提高稳定性
- 最终目标是不依赖于 `zmlx` 中任何其他包（甚至不依赖 `zml`），可作为独立包使用

---

## GUI 执行方式（重要）

### 正确的启动方式

**仅在 `if __name__ == '__main__'` 下调用 `gui.execute()`**：

```python
if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
```

**不要在函数内部调用 `gui.execute()`**，否则会导致嵌套执行，产生不可预期的行为。参考 demo 文件（如 `zmlx/demos/flow_1ph/darcy_1d.py`）。

### 导入 PyQt

**不要直接 `from PyQt6 import ...`**，应通过 `zmlx.ui.pyqt` 导入，确保 Qt 版本与 zmlx 一致：

```python
from zmlx.ui.pyqt import QtWidgets, QtGui, QtCore
from zmlx.ui.pyqt import QAction, QWebEngineView
```

`pyqt.py` 会自动选择 PyQt6（优先）或 PyQt5 降级，并在无头模式下跳过加载。

选定绑定后，`pyqt.py` 会把它钉死（设置 `QT_API` / `FORCE_QT_API`），使 `qtpy` 以及依赖它的第三方库（`pyvistaqt`、`pyqtribbon` 等）跟随同一个绑定。这一点很重要：`qtpy` 默认会选 PyQt5，且「已导入者获胜」的规则又让 PyQt5 排在 PyQt6 之前；一旦它与 zmlx 实际使用的绑定分裂，混用两套绑定会导致原生崩溃（Python 层无法捕获）。因此**不要**在本层之前直接导入 `qtpy`。

### 无头模式

```bash
python demo.py --no-gui       # 命令行模式
python demo.py --headless     # 等效
```

`gui.execute()` 内部会自动检测无头模式（`is_headless()`），不需要手动处理。

### gui.xxx() 系列函数

在 `gui.execute()` 启动的程序中可以直接使用 `gui.break_point()`、`gui.progress()`、
`gui.information()`、`gui.question()`、`gui.show_attrs()` 等函数；**在非 GUI 模式下这些调用
自动变为空操作**，不需要 `if gui.exists()` 判断。长循环、大量迭代的求解过程中应多放置
`gui.break_point()`，否则界面会卡死直到计算结束。完整函数表见
[`projects/zml/AGENTS.md`](../../AGENTS.md) 的「`gui.*` functions」。

### 右侧栏的宽度与可见性会被记住（2026-10-26）

`MainWindow` 的中央区是一个水平 `QSplitter`：**左边**是顶部标签页（拉伸因子 1），
**右边**是右侧栏（控制台常驻其中，拉伸因子 0）。三件事都自动保存 / 恢复：

| 行为 | 什么时候 | 存哪 |
|---|---|---|
| **拖动分隔条** | 任何时候（`splitter` 可拖，用户决定宽度） | `resizeEvent` 把「> 0 的宽度」记到 `_last_console_width` |
| **宽度记忆** | 关闭窗口时 `settings.save_console_width(win)` | `app_data` 的 `main_window_console_width_px` |
| **可见性恢复** | 关闭时写 `console_visible`（`Yes`/`No`），下次 `__on_show` 读 | `app_data` 的 `console_visible` |
| **宽度恢复** | 启动时 `init_splitter_sizes()`：存盘值夹到 `[settings.MIN_CONSOLE_WIDTH, 窗口宽度×MAX_CONSOLE_RATIO]`；**没有存盘时按 `DEFAULT_CONSOLE_RATIO`（0.22，2026-10-26 由 0.30 调窄）** | —— |

⚠️ **隐藏时不会用 0 覆盖已存宽度**：隐藏后 `splitter.sizes()` 的右项是 0；重新显示时
`set_side_tabs_visible(True)` 会还原成隐藏前的宽度。

### 「显示 → 重置布局」：改乱了就点它（2026-10-26）

`MainWindow.reset_layout(ask=True)`，菜单「显示 → 重置布局」，也是命令 `gui.reset_layout()`。
它做两件事：

1. **当前窗口立即生效**：右侧栏恢复显示 + 默认宽度（`settings.DEFAULT_CONSOLE_RATIO`，约 22%）；
2. **清掉存盘**（`settings.reset_layout(style_sheet=None)`，键表见 `settings.LAYOUT_KEYS`）：
   右侧栏宽度 / 上次可见宽度 / 是否显示 —— 下次启动也是默认。

⚠️⚠️ **它不碰这两样**（2026-10-26 按用户要求收窄）：

- **窗口大小 / 位置** —— 那是用户自己拖出来的，重置布局不该把窗口拽回屏幕居中 75%；
  `main_window_size*` 因此**不在** `LAYOUT_KEYS` 里，存盘值保留；
- **样式表** —— 外观不是布局，清掉等于把用户的主题一起删了；`reset_layout()` 的
  `style_sheet` 参数默认就是 `None`（真要清得显式传）。

⚠️ **不清的东西**：已打开的标签页、插件名单、工作路径 —— 那些也不是布局。

⚠️ 实现上的坑（都实测过）：
- `settings.save()` 写的是**文件**（`app_data.temp(key)`），若要清样式表必须**删文件**才算真清；
- 只重排右侧栏时不必动窗口几何，但**宽度也不能读 `splitter.width()`** —— 父布局没重排完
  时它可能是旧值。默认宽度从**父控件布局**反推（`_splitter_target_width`）。
  ⚠️ 也**不要**用 `QSplitter.activate()` —— 那是 `QLayout` 的方法，`QSplitter` 上没有。

### 切标签页会调用当前页的 `refresh()`（重要）

`MainWindow` 把 `top_tabs.currentChanged` 接到 `refresh()`（菜单「操作 → 刷新」走同一条路径），
**每次切到某个标签页，该控件的 `refresh()` 就会被调一次**。因此 `refresh()` 里不能做慢操作
（读磁盘、解析文件、联网、重画图表）：需要的话必须放进后台 `QThread`，结果用信号回传主线程。

⚠️ **起线程还必须管住它的生命周期**，否则关标签页会**崩进程**（不是异常，退出码
`0xC0000409`）：**线程不设 parent** + 用**模块级列表**持有强引用，**这两条缺一不可**
（`demo_view.py` 就靠这两条，从不崩）。关标签页时 `TabWidget` 还会给控件两次清理机会 ——
`save_file()`（持久化，菜单也用）与 `cleanup_before_tab_close()`（其余收尾，**只在作为标签页
被关闭时**才调）；后者**不是**防线。完整说明、`closeEvent` / lambda 槽这两个死代码坑见
[`widgets/AGENTS.md`](widgets/AGENTS.md) 的「线程的生命周期契约」与「销毁前的两次清理」。

### 图表控件：简单图用原生 Qt

复杂图（多轴、等值线、三维）用 `widgets/plt.py` 的 `MatplotWidget`；「一条折线」「一排柱子」这类
展示性图表改用**原生 Qt** 绘制（`QPainter` 画图 + `QPalette` 取色，跟随主题与暗色模式）：更快、
`sizeHint` 可控、不会自动往输出目录写 PNG。目前已按此改掉两处：`tabs/check_count_view.py` 的
`_BarChart`（按天柱状图）、`tabs/gui_iter_edit.py` 的 `_TimingChart`（迭代耗时曲线），
对照表见各模块文档的「绘图为什么用原生 Qt」。

⚠️ **图表控件不能像 `DemoView` 那样丢进后台线程**：Qt 的绘制必须在 GUI 线程做，原生 Qt 方案够快
是因为一次重画只有毫秒级，而不是因为能并行。用 `QPainter` 画折线时画笔宽度取 1、不要加粗 ——
宽度 > 1 会让 Qt 从画线的快速路径切到「把折线描边膨胀成填充多边形再栅格化」的慢路径，抖动的
曲线上代价会爆掉。

---

## 公共 API

仅以下函数/对象为外部可用的公共接口（来自 `gui_buffer.py`）：

| 接口 | 类型 | 描述 |
|------|------|------|
| `gui` | `GuiBuffer` | 全局 GUI API 单例 |
| `information(*args, **kwargs)` | 函数 | 显示信息对话框 |
| `question(msg, title)` | 函数 | 显示问题对话框（是/否） |
| `plot(on_figure, caption, ...)` | 函数 | 在 GUI 标签页中执行绘图 |
| `break_point()` | 函数 | 插入断点（支持暂停/继续/终止） |
| `gui_exec(func)` | 函数 | 在 GUI 线程中执行代码 |
| `progress(label, val_range, value, visible)` | 函数 | 显示进度条 |
| `show_attrs(clear=False, **attrs)` | 函数 | 显示对象的动态属性 |
| `add_action(text, slot, ...)` | 函数 | 添加菜单动作 |

---

## matplotlib 绘图（重要）

所有 matplotlib 绘图都走统一入口 `zmlx.ui.plot(on_figure, caption=...)`：**给定一个回调函数
`on_figure(fig)`**，在其中操作 figure 对象进行绘图。**不要**在代码中直接创建 `plt.figure()`
然后 `plt.show()`。`plot` 会自动检测运行环境并选择行为：

| 运行环境 | 行为 |
|----------|------|
| **GUI 模式**（`gui.execute` 启动） | 在 GUI 中新建标签页显示图形 |
| **无头模式**（`--no-gui`） | 自动保存图片到文件 |
| **直接运行**（常规 `python` 脚本） | 若未指定 `fname`，调用 `plt.show()` 弹出窗口；若指定则保存文件 |

```python
from zmlx.ui import plot

def on_figure(fig):
    ax = fig.add_subplot(111)
    ax.plot(x, y)
    ax.set_xlabel("X label")

plot(on_figure, caption="图标题")
```

---

## 控件列表

控件分两处（2026-10-16 起）：**底层控件**在 `widgets/`（会被别的控件 `addWidget()` 进去当
组件用），**顶层控件**在 `tabs/`（只被装配层打开成标签页，**不被任何控件复用**，共 27 个）。
⚠️ 依赖方向单向：`tabs/` 可以复用 `widgets/`，**反之不行** —— 一旦 `widgets/` import 了
`tabs/` 的东西，就说明那个控件正在被别人当组件用，它就不该待在 `tabs/`。完整判据与新建
控件该放哪，见 [`tabs/AGENTS.md`](tabs/AGENTS.md)。
⚠️ `widgets/` 里还有两类，既不是"被标签页复用的底层组件"、也不是"标签页页面"：
**宿主不是标签页的常驻控件**（状态栏 `VersionButton` / `LicenseButton`、右侧栏 `OutputWidget`、
标签容器 `TabWidget`）与**对话框/表单组件集**（`editors/`（子包：**全部编辑器都在这里**））。

### widgets/ —— 通用控件

| 控件 | 描述 |
|------|------|
| `CodeEdit` | Python 代码编辑器（QsciScintilla） |
| `MatplotWidget` | matplotlib 嵌入式显示（**复杂图**用它；简单展示图见「图表控件」一节） |
| `TabWidget` | 可关闭标签页管理器（⚠️ 销毁前依次调 `save_file()` 与 `cleanup_before_tab_close()`；用 `deleteLater()` 销毁，故控件的 `closeEvent` **不会**被调 —— 见「销毁前的两次清理」） |
| `OutputWidget` | 输出面板（文本 + 属性 + 进度条）；文本支持 **ANSI 颜色**：`print` 里的 `\033[3xm` 等转义码会被上色，控件不支持的序列（擦行 / 清屏 / 光标定位 / OSC）一律**删除**而不是显示成乱码，`sys.stderr` 的内容显示成红色，控制台的**系统提示**（时间戳分隔行、`Start` / `Done` / `Time used`）显示成蓝色（浅色主题深蓝 / 暗色主题浅蓝）；可用 `get_plain_text()` / `get_html()` 取到当前内容，`MainWindow` 上对应 `get_output_text()` / `get_output_html()` |
| `MarkdownView` | Markdown 查看器（表格 / 代码块 / 可点链接）；公开方法只有 `set_markdown()` 与 `set_link_callback()`；**默认优先用第三方 `markdown` 库**渲染（未装则提示一次并回退 Qt 自带 `setMarkdown`；设置键 `md_by_html` 写成 `No` 可强制 Qt） |
| `AttrView` | 属性键值表格查看器 |
| `RunStateLight` | 状态栏（**「并行」复选框左边**）：**运行状态灯**——圆点 + 文字，在「○ 空闲 / ● 运行中 / ⏸ 已暂停」之间切换，状态由 `MainWindow.refresh()` 按 `is_running()` / `is_paused()` 设置。⚠️ 2026-10-26 新加：把原先**借**版本按钮显示的控制台状态接了过来。★ 它是**按钮**（`QToolButton`）：**点击 = `gui.show_console()`** —— 把右侧栏（控制台）显示出来 / 切过去，悬停提示末尾也写了这句。圆点是**字符**（`●`/`○`/`⏸`）而不是 `QPixmap`（`QLabel.setText()` 会 `clearContents()` 把 pixmap 清掉，实测） |
| `VersionButton` | 状态栏：版本号按钮（`QToolButton`，点击→关于），显示 **`版本: <zmlx.__version__>`**（如 `版本: 1.9.7`；2026-10-26 起，原先显示的是内核编译时间 `Oct 21 2026`）。⚠️ **不设任何尺寸策略**（不重写 `sizeHint`、不写 QSS、不锁宽高），紧凑交给 `QToolButton` 默认行为。⚠️ 2026-10-26 起**只属于版本号**；服务端报了新版本时补「（有更新）」后缀；内核编译时间挪到悬停提示里。⚠️ 历史公开方法 `MainWindow.console_state()` 仍保留（照旧写本按钮），只为兼容外部调用 |
| `LicenseButton` | 状态栏：登录状态按钮（`QToolButton`，点击→登录）。**固定就是一个按钮**，文字在「登录查询中... / 已登录：<姓名> / 未登录 / 登录状态未知」之间变；查询自带后台线程（`LicenseStateThread`，parent 留空 + 模块级登记表，见 `widget/AGENTS.md` 的线程契约）；查到的「是否有更新」经 `sig_update` 转给 `VersionButton`。⚠️ 与另两个一样**不设尺寸策略**，只保留 `MAX_BUTTON_WIDTH` 这个**宽度上限**（超长显示名不能把状态栏撑宽） |
| `editors/`（子包） | **数据编辑器集合**：`set_data()` 给数据 → 用户编辑 → `get_data()` 取回。含 `ArrayEdit`（numpy 矩阵）、`XyEdit` / `XyzEdit`（曲线 / 曲面）、`Interp1Edit` / `Interp2Edit`（插值）、`TextEdit` / `ArrayTextEdit`，读写工具 `NumpyAlgs`；**单浮点数** `Slider` / `Dial`；通用包装器 `ObjectEdit`（+ `TextInput` / `IntSpin` / `FloatSpin`）。⚠️ 2026-10-21 由单文件 `editors.py` 拆成子包，并先后并入原 `widgets/seepage.py` 与 `widgets/float_edit.py` 的全部控件 —— 至此 **`widgets/` 根目录只剩纯控件**；**老路径 `from zmlx.ui.widgets.editors import X` 不变**，`widgets/seepage.py` / `widgets/float_edit.py` 已成弃用垫片（前者**不再提供 `setup_ui`**）。⚠️ 2026-10-22 渗流相关的 10 个类（`SeepageEdit` / `FludefEdit`、容器 `SeepageFormEdit` / `SeepageTabEdit`、组合编辑器 `SeepageSummary` / `SeepageKrEdit` / `SeepageInterp1Edit`、单字段行 `TextFieldEdit` / `IntFieldEdit` / `FloatFieldEdit`，在 `seepage_edit.py` / `field_edit.py`）一度搬进插件包 `zmlx/scen/editors/`，同日又**搬回本子包**（它们是纯控件，那个插件包已整体删除），`__all__` 27 → 18 → 28。类上没有静态 `setup_ui`；文件类型注册（`gui.open_numpy_array` / `gui.open_seepage` 等）由**插件** [`plugins/builtin/editors.py`](plugins/builtin/editors.py) 完成（`setup_file_types()`，默认启用；原 `extra_setups/editors.py` 与 `plugins/builtin/editors_menu.py`、`seepage_menu.py` 都已合并进它并删除）。**加/改编辑器的规范见 [`widgets/editors/AGENTS.md`](widgets/editors/AGENTS.md)** |
| ... | 更多控件详见 `widgets/` 目录 |

### tabs/ —— 标签页专用控件

这 27 个都是**顶层控件**（不被任何控件复用）。其中一部分自己管生命周期（`cleanup_before_tab_close()` / `refresh()`）、一部分不需要 —— 判据见 [`tabs/AGENTS.md`](tabs/AGENTS.md)。

| 控件 | 描述 |
|------|------|
| `About` | 「关于」页：快信息（版本 / 路径 / Python / Qt，本地读取）在装配表格时就填好，「慢信息」（管理员权限 / 登录状态，要联网）走后台线程回填；表格只读（双击不弹编辑器）。版本号一行形如 `261007 (zmlx 1.10.22)`。每行最后一列按行配一个按钮（ReadMe / 更新 / 日志 / 登录 / 统计 / 打开），「代码行数」那一行是 **架构**（→ 帮助 → 架构；2026-10-26 加） |
| `CheckCountView` | 「帮助 → 查询 → 登录记录」：某个邮箱对应用的登录查询次数，按天柱状图（⚠️ **原生 Qt 绘制**，非 matplotlib）；左侧邮箱名单仅管理员可见。⚠️ 名字说的是"这是 `check_count` 那个接口的视图"，不是"登录检查"——数据是被数出来的那些 check 的**次数** |
| `FeedbackTool` | 用户反馈工具：一个输入框 + 一个按钮，把文本提交给作者；有未提交内容时 `need_save()` 为真（菜单「保存」据此点亮），关标签前会问一次是否存盘 |
| `FeedbacksView` | 「帮助 → 查询 → 反馈记录」：某个用户**某一天**的反馈文件名 + 单条反馈的内容（**本人或管理员**）；内容按「合法 JSON → 缩进 / 否则原文 / 二进制 → hex 摘要」三级显示，JSON 记录会把 `text` **单独拿出来**（与其余字段分两块、可拖动）；`Truncated:` 与 0 字节文件分别提示；⚠️ **不落盘**——显示的可能是别人的反馈正文，故本控件**不实现** `save_file()`。★ **左栏「选什么」、右栏「看什么」**：邮箱与日期都只在左栏输入，发起查询的按钮也只有左栏那个「刷新文件」——右侧只有一个只读的邮箱回显（`date_view` / `query_button` 分别是左栏日期框与「刷新文件」的**别名**，为兼容旧调用而保留） |
| `LicenseRegister` | 登录控件（邮箱验证码 + 登录本机）：**一个控件、两种形态** —— 未登录时填资料收验证码走 `submit`，已登录后同一个按钮变「更新信息」；换绑邮箱 = 直接改邮箱框 |
| `CwdView` | 当前目录文件浏览器（`refresh()`：切回本页时重扫目录） |
| `DemoView` | Demo 脚本浏览器（⚠️ 列表**异步载入**：先显示「正在载入 ...」占位行，扫描在后台线程；切标签页不阻塞）。⚠️ **2026-10-22 不在 `ui/tabs/` 了**：它只有「示例浏览」插件在用，已随 `gui.show_demo` 整体并入 `plugins/builtin/demo_menu.py`；老路径 `from zmlx.ui.widget import DemoView` 仍可用（弃用垫片已改指新位置） |
| `GuiIteratorEdit` | GUI 迭代器面板：迭代耗时曲线（⚠️ **原生 Qt 绘制**，非 matplotlib）+ ratio / 最大绘图间隔编辑 |
| `MemView` | 内存变量查看/编辑器 |
| `MessageEdit` | 通知消息中心（控制台命令 `gui.show_messages()`）：列出通知条目，双击执行 / 删除 |
| `SolverSelector` | 求解器选择面板。⚠️ **2026-10-22 不在 `ui/tabs/` 了**：它只有「求解器」插件在用，已随 `gui.show_solver_selector` 整体并入 `plugins/builtin/solver_menu.py`（默认**不加载**）；老路径 `from zmlx.ui.tabs import SolverSelector` 与 `from zmlx.ui.widget import SolverSelector` 仍可用 |
| `TabDetailView` | 已打开标签页总览（开在**右侧栏**）：列出标题 / 类型 / 关闭按钮，点击切页、双击删除；⚠️ 主窗口的刷新链到不了它（`MainWindow.refresh` 只刷顶栏当前页），故**可见时每秒自刷**（`refresh()` + `showEvent`/`hideEvent` 起停计时器） |
| `TimerView` | CPU 计时表（`refresh()` + 自带 `QTimer`） |
| `AppPathEdit` | 搜索路径浏览器 |
| `CodeHistoryView` | 历史代码浏览 |
| `EnvEdit` | 环境变量编辑器（菜单「设置 → 系统」）：按 `data/zml_env_items.py` 每项的 `kind` 选控件、按 `default` 初始化 —— **界面初始显示的就是程序实际生效的取值**；选「默认」或「全部还原为默认」= 删除持久化文件。⚠️ 系统环境变量优先：被覆盖的键显示生效值并置灰 |
| `Fn2Widget` | 2D 裂缝网络可视化。⚠️ **2026-10-22 不在 `ui/tabs/` 了**：它只有「二维裂缝查看」插件在用，已随 `gui.show_fn2` 整体并入 `plugins/builtin/fn2_view.py`（默认启用，同时注册 `.fn2` 文件类型）；老路径 `from zmlx.ui.widget import Fn2Widget` 仍可用 |
| `ImageView` | 图片查看器（滚轮缩放 / 拖拽）。⚠️ 2026-10-22 曾连同 `open_image` 并入「图片浏览」插件，**同日还原**：欢迎页在 `MainWindow` 构造期就要用 `gui.open_image`，它是**底层能力**，不该随插件开关消失 |
| `OutputHistoryView` | 历史输出浏览 |
| `PgConsole` | 交互式 Python 控制台（可选依赖：没装 pyqtgraph 时该名字为 `None`）。⚠️ **2026-10-22 不在 `ui/tabs/` 了**：它只有「Python 控制台」插件在用，已随 `gui.show_pg_console` 整体并入 `plugins/builtin/pg_console.py`（默认启用）；老路径 `from zmlx.ui.widget import PgConsole` 仍可用 |
| `ReadMeBrowser` | ReadMe 查看器：`QWidget` 容器 = **左侧标题目录**（`QTreeWidget`，标题层级归一化后建树）+ **右侧正文**（私有 `_ReadMeContent`，继承 `MarkdownView`）；点目录项把该小节顶到视口顶部，滚动正文时目录自动高亮当前小节；微信 / 登录 / `zmlx/demos` / 新建Issue 等链接就地处理（显示本地二维码、打开登录控件或 Demo 浏览器，而不是去开浏览器） |
| `RegTool` | 许可登录工具（旧的 USB 序列号 + 授权码方式，已不挂界面，留作离线授权码那条老路） |
| `PluginListEdit` | 插件列表编辑器（「设置 → 插件」）：七列「默认加载 / 优先级 / 名称 / 描述 / 来源 / 状态 / 临时加载」。可勾选「默认加载」（= 启动时是否自动加载；2026-10-25 由「启用」改名）、改高/正常/低优先级；「来源」区分**自动发现**与**手动登记**，**只有手动登记的能移除**（自动发现的移了下次扫描也会回来，只能禁用）。**临时加载**：点按钮**当场执行**该插件脚本（不必勾选、不必重启），不写任何设置；每个插件在本次运行只加载一次 —— **启动时已执行过的也算**（勾选着启动的插件，按钮直接显示「已加载」且点不动），失败可重试。⚠️ **没有「文件」列**（2026-10-19 移除）：**完整路径在名称列的鼠标悬停提示里**，双击任意一行可在代码编辑器中打开。⚠️ **不支持拖动排序** —— 顺序由插件来源决定，用户只控制「是否执行」与「谁先执行」。⚠️ **刷新只更新状态、不重建表单**（2026-10-21）：表格已有内容时 `update_items()` 只重算「默认加载 / 优先级 / 状态」并原地写回（不起线程、不扫目录、不读文件），名称 / 描述 / 来源三列不动；只有首次显示、或插件集合变了（添加 / 移除 / 恢复默认）才重扫重铺 |
| `StringTable` | 字符串表格查看器 |
| `StyleSheetEdit` | 窗口样式表(QSS)编辑器（「设置 → 样式表」）：可选字体/配色/圆角等参数实时生成，也可直接用自定义文本；应用走转接出来的 `gui.set_style_sheet(text)`，**落盘与参数记忆都由控件自己负责**（写入 `zml_window_style.qss`）。⚠️ **2026-10-22 不在 `ui/tabs/` 了**：它只有「样式表」插件在用，已随 `gui.show_style_sheet` 整体并入 `plugins/builtin/style_sheet_menu.py`；老路径 `from zmlx.ui.widget import StyleSheetEdit` 仍可用（弃用垫片已改指新位置） |
| `TextFileEdit` | 可编辑文本文件视图 |
| `ImageBrowser` | **图片浏览器**：打开即扫描「工作路径」及其下 2 层子目录的图片（格式以 Qt 图片插件为准，默认不收 `pdf`），左侧缩略图相册（手机相册式），点哪张右侧显示大图；支持上一张/下一张、按帧率连续播放（进度条 + 循环开关）、以及显式「刷新」按钮。⚠️ **故意不实现 `refresh()`**（切标签不自动重扫）；三个后台线程（扫描/缩略图/解码）全部压低 OS 优先级，解码**按显示尺寸**；关标签走 `cleanup_before_tab_close()`；播放中切走标签会自动暂停并亮出「继续播放」。单文件自足（只依赖 `zmlx.ui.pyqt`）。⚠️ **2026-10-30 起不在 `ui/tabs/` 了**：控件连同入口整体并入 `plugins/builtin/image_browser.py`（原 `tabs/image_browser.py` 删除、**不留垫片**），新代码请 `from zmlx.ui.plugins.builtin.image_browser import ImageBrowser`。**入口**：菜单「文件 → 浏览 → 图片」或命令 `gui.show_image_browser()`（不动 `main.py`） |

### extra_setups/ —— 额外菜单动作自带的页面

这几个控件**不在**上面的 `tabs/` 清单里（它们随各自的菜单挂载点一起维护），
按 `ui/AGENTS.md` §3「挂到界面上：走 `extra_setups/`」放在那里：

| 控件 | 描述 |
|---|---|
| `_ArchitectureView`（`extra_setups/architecture.py`，标题「架构」） | **代码库图文入门页**：21 个小节（总览 / 五层架构 / 子包索引 / 核心数据模型 / 物理模型 / 示例集导读 / 一次求解 / 边界条件与井 / API 速查 / 图形界面 / 界面地图 / 命令与控制台 / 如何阅读源码 / 运行与测试 / 扩展点 / 常见陷阱 / 报错排查 / 文档地图 / 术语表），左侧目录 + 右侧正文 + 6 张原生 Qt 配图（颜色只从 `QPalette` 取，暗色主题自动提亮）。正文里三种可点链接：`zmlx://gui/<命令>` = 点那个菜单项、`zmlx://doc/<路径>` = 打开文档或源码、`#锚点` = 页内跳转。⚠️ **回退靠自己维护的历史栈**：实测 `QTextBrowser` 只在用户真点超链接时记历史，代码发起的 `scrollToAnchor` / `ensureCursorVisible` **完全不入栈**（`isBackwardAvailable()` 恒为 `False`）。⚠️ 也不用 `scrollToAnchor` 定位 —— Qt 自带 Markdown 渲染路径不给标题建命名锚点，改为按标题文字找块。**入口**：菜单「帮助 → 架构」或命令 `gui.show_architecture()`，`gui.show_architecture('data_model')` 直达某一节（挂载点 `extra_setups/__init__.py`，用 `getattr` 探测 `provide_gui_setup`，不动 `main.py`） |
| `RuntimeEnvView`（`plugins/builtin/runtime_env.py`，标题「运行环境」） | 第三方依赖检查表，缺的可以一键安装（两个后台 QThread）。⚠️ 整个模块是一个**插件**（默认不加载），勾选后「设置 → 运行环境」才出现 |

⚠️ 老路径 `from zmlx.ui.widget import <上面这些类>` 仍然可用：整个 `widget/` 现在是一层**兼容垫片**（导入即发 `DeprecationWarning`，2027-10-16 删除）——
一层转发（照 `license_count.py` 的既有写法）。**新代码请用 `from zmlx.ui.tabs import X`。**
两边共用的「许可答复解析与查询」工具已下沉到 `utils/lic_utils.py`（无 Qt 依赖），
理由见 [`tabs/AGENTS.md`](tabs/AGENTS.md) 的「公共工具放 `../utils/lic_utils.py`」。

> 写新控件之前先看 [`widgets/AGENTS.md`](widgets/AGENTS.md)：控件骨架、命名与导入约定、右键菜单
> （`context_actions` + `create_action`）、可选依赖的两种写法、`app_data` 的两套存储、
> `refresh()` 的性能约束、线程崩溃坑，以及无头环境下的自测与验收手法。
> ⚠️ **若新控件不会被任何控件复用（只作为标签页打开），它属于 `tabs/`** ——
> 先看 [`tabs/AGENTS.md`](tabs/AGENTS.md) 的归属判据（那份文档同时声明：`widgets/AGENTS.md` 的
> 规范对 `tabs/` 同样有效，并给出两条硬约束：依赖单向 `tabs/ → widgets/`、`tabs/` 内控件
> 相互独立）。

⚠️ **新增界面元素（控件 / 对话框 / 工具模块 / 菜单动作）默认不要在任何 `__init__.py` 里
转发** —— 直接按**子模块路径**导入，例如 `from zmlx.ui.tabs.about import About`
（已随插件搬走的控件写 `from zmlx.ui.plugins.builtin.<插件> import <类>`，
如 `ImageBrowser` → `plugins/builtin/image_browser.py`）。
给界面加**入口**（菜单项、命令）请放 `extra_setups/`，**不要**改 `main.py`。
完整规则与理由（导入期副作用、循环导入、无头模式、API 只增不改）见
[`AGENTS.md`](AGENTS.md)。

---

## 架构层次

```
zmlx.ui/
├── pyqt.py               Qt 绑定层（PyQt6 → PyQt5 自动降级）
├── utils/                界面工具包（服务于 ui 的工具集合；不要求依赖 Qt）
│   ├── shared.py         SharedValue / SharedList / SharedDict（跨线程容器）
│   ├── gui_api.py        GuiApi —— 通道池模式，跨线程函数调用
│   ├── break_point.py    BreakPoint —— 暂停/恢复机制
│   ├── task_proc.py      TaskProc —— GUI 线程任务队列
│   ├── file_handler.py   FileHandler / CodeFile —— 按扩展名分发文件
│   ├── background_task.py BackgroundTask —— 后台循环任务（最低优先级线程）
│   ├── thread_runner.py  ThreadRunner —— 多任务并发（daemon 线程；⚠️ Console 仍是长任务唯一槽位）
│   └── lic_utils.py      许可答复解析与查询（无 Qt 依赖；widgets/ 与 tabs/ 共用）
├── gui_buffer.py         API 代理层（全局 gui 单例）
├── main.py               应用层（MainWindow 主窗口）
│   └── MainWindow        QMainWindow 子类（~100 方法）
│   └── execute()         GUI 入口点
├── console.py            控制台管理器
│   └── ConsoleThread     后台脚本执行线程
│   └── Console           线程生命周期管理
├── settings.py           配置管理
├── alg.py                辅助函数（动作创建、历史记录、文件注册）
├── widgets/              通用控件集合（底层控件 / 常驻控件 / 对话框组件）
├── widget/               兼容垫片（转发到 widgets/ 与 tabs/；弃用，2027-10-16 删）
├── tabs/                 标签页专用控件（有后台线程生命周期钩子的页面）
├── extra_setups/         额外菜单动作（注册新菜单放这里）
├── plugins/              插件机制（发现 / 记录状态 / 执行 zml_plugin.py）
│   └── builtin/          随包分发的内置插件（此目录内 .py 一律是插件）
└── data/                 默认配置数据
```

⚠️ `utils/` 在 2026-10-16 之前是单文件 `utils.py`（687 行），现按主题拆成包。**老路径
`from zmlx.ui.utils import GuiApi` 完全不变**（`utils/__init__.py` 逐名转发，且不发弃用
警告）。两个**刻意不进** `__init__` 的模块要按子模块路径导入：
`from zmlx.ui.utils.background_task import BackgroundTask`（它需要 Qt，转发会让
``import zmlx.ui.utils`` 在无头模式下失败）、
`from zmlx.ui.utils.lic_utils import ...`（唯一不依赖 Qt 的模块，转发会连带拉起
`zmlx.exts.web_license`）。

---

## 模块列表

| 模块 | 说明 |
|------|------|
| `gui_buffer.py` | 全局 GUI API 代理 |
| `main.py` | 主窗口实现（QMainWindow） |
| `console.py` | 后台脚本执行控制台（**长任务唯一槽位**——见下方 `utils/thread_runner.py` 的分工） |
| `pyqt.py` | Qt 绑定选择层 |
| `settings.py` | 配置管理（图标、声音、窗口位置） |
| `alg.py` | 辅助函数（动作、历史、文件注册） |
| `utils/` | **界面工具包** —— 服务于 `zmlx.ui` 的工具集合（定位如此，**不要求依赖 Qt**）。`__init__` 转发 `GuiApi` / `BreakPoint` / `TaskProc` / `SharedValue` / `SharedList` / `SharedDict` / `FileHandler` / `CodeFile`，所以老路径 `from zmlx.ui.utils import GuiApi` 照旧可用且**无弃用警告**。⚠️ 下面两个**刻意不转发**，走子模块路径：`utils.background_task`（需要 Qt，转发会让 `import zmlx.ui.utils` 在无头模式下失败）与 `utils.lic_utils`（唯一无 Qt 的模块，转发会连带拉起 `zmlx.exts.web_license`） |
| `utils/gui_api.py` | `GuiApi`：通道池模式，把非 GUI 线程的调用（含返回值与异常）派发到主线程 |
| `utils/break_point.py` | `BreakPoint`：暂停 / 继续；按调用者身份区分 —— 内核线程真的等，GUI 线程径直返回（界面永不冻死） |
| `utils/task_proc.py` | `TaskProc`：信号驱动的异步任务队列（丢下就走，拿不到返回值；要返回值用 `GuiApi`） |
| `utils/shared.py` | `SharedValue` / `SharedList` / `SharedDict`：QMutex 守着的跨线程共享容器 |
| `utils/file_handler.py` | `FileHandler` / `CodeFile`：按扩展名分发「打开 / 新建文件」 |
| `utils/lic_utils.py` | 许可答复的解析与查询（**无 Qt 依赖**，`widgets/` 与 `tabs/` 共用） |
| `utils/background_task.py` | `BackgroundTask`：把无参回调放到**最低优先级**线程里反复执行的「后台循环任务」。公开接口只有 `set_task()`；每执行一次**至少**睡 `min_sleep`（默认 0.2 s），并按 `work/(work+sleep) <= ratio`（默认 0.2）**自适应拉长睡眠**，于是任务再重也只占总时间的 `ratio` 以内。实测占比看 `stats['duty']`。⚠️ 建立在 Qt 线程原语上（`QThread`/`QMutex`/`QWaitCondition`），**无头模式下不可用** |
| `utils/thread_runner.py` | `ThreadRunner` / `TaskHandle`（2026-10-20 新增）：**「多个短/中任务并发」**的通用执行器 —— `run(func, on_done)` 起一条 daemon 线程，`count` 看还有几个在跑，`cancel_all(wait)` 叫停（返回**没能停下来**的个数）。完成回调默认**回投 GUI 线程**（模块级信号泵；无 `QCoreApplication` 时就地执行）。⚠️ **`Console` 仍是长任务唯一槽位**：本模块**不是** `gui.start` 的替代品，不接管「暂停/继续/停止」，两者互不知情；「立即终止」只能是**协作式取消 + 放弃**（Python 无 `kill`，任务体须轮询 `task.check()` / `task.sleep()`）。**尚未加入 `utils/__init__` 转发**，导入写全路径 `from zmlx.ui.utils.thread_runner import run, count, cancel_all`。分工判据与完整说明见 `ui/AGENTS.md` §6.8 |
| `widgets/` | 通用自定义 PyQt6 控件（底层控件 / 常驻控件 / 对话框组件） |
| `widget/` | **兼容垫片**：转发到 `widgets/` 与 `tabs/`（导入即发 `DeprecationWarning`，2027-10-16 删） |
| `tabs/` | 标签页专用控件（实现了 `cleanup_before_tab_close()` 的那一类） |
| `extra_setups` | 额外菜单动作（注册新菜单放这里） |
| `plugins/` | 插件机制：**发现 + 记录状态 + 执行** `zml_plugin.py`（旧名 `zml_gui_setup.py` 仅作兼容）。⚠️ **「插件」的定义、标准写法、三个概念与两个旋钮见下一节「插件是什么」**。三个概念各占一个变量：名单 `zml_plugins`（有哪些）、优先级 `high/normal/low`（谁先跑）、禁用标记（跑不跑）。公共 API 只有 11 个：`get_files` / `get_priority` / `set_priority` / `is_disabled` / `set_disabled` / `is_standard` / `add_file` / `remove_file` / `is_loaded` / `load_now` / `get_load_error`（后三个是**临时加载**：当场执行、不写盘、进程内只跑一次）。⚠️ **没有排序接口**。⚠️ **本目录只放机制**（`__init__.py` / `_alg.py` / `_registry.py`）；**内置插件在 `builtin/` 子目录**（2026-10-19 下沉）——**目录即语义**：`builtin/` 里除 `__init__.py` 外每个 `.py` 都会被启动时执行，工具模块不要放进去（放上层并以 `_` 开头）。内置插件共 **15 个**：默认启用 `doc_view.py`（帮助 → 日志 / 路线图；另注册 `gui.show_changelog` / `gui.show_roadmap`）、`image_browser.py`（文件 → 浏览 → 图片；另注册 `gui.show_image_browser`）、`style_sheet_menu.py`（设置 → 样式表）、`pdf_view.py`（文件 → 打开 `.pdf`，另注册 `gui.open_pdf`）、`demo_menu.py`（帮助 → 示例，另注册 `gui.show_demo`）、`fn2_view.py`（文件 → 打开 `.fn2`，另注册 `gui.show_fn2`）、`pg_console.py`（显示 → 控制台(pg)；另注册 `gui.show_pg_console`，需要 pyqtgraph）、`viewers.py`（耗时 / 浏览→工作目录 / 标签列表 / 路径四个小入口）、`editors.py`（数据编辑器：7 种文件类型 + 「帮助 → 其它 → 生成测试数据」）；默认不加载 `admin_menu.py`（Admin 功能）、`solver_menu.py`（设置 → 求解器）、`runtime_env.py`（设置 → 运行环境）、`fractal_demo.py`（演示 → 经典分形，控件本体也在这个文件里）、`vtk_view.py`、`zip_files.py`。⚠️ 2026-10-22：原 `editors_menu.py` + `seepage_menu.py` **合并成** [`editors.py`](plugins/builtin/editors.py)（默认启用；中途曾住进 `zmlx/scen/editors/`，同日退回 `builtin/`，勾选记录由 `_registry` 自动迁移），原 `tetris.py` + `lianliankan.py` **合并成** [`zmlx/scen/easter_eggs/`](../scen/easter_eggs/ReadMe.md)（彩蛋，默认不启用）—— 后者**不在 `builtin/`**。默认状态写在各插件顶部的 `# ** enabled = False` 里，用户勾选后以用户的为准。⚠️ 插件与 `extra_setups/` 的分工：**用户可关掉的非核心功能**放这里，**产品功能**（授权查询、用户管理）留 `extra_setups` |
| `data/` | 默认配置数据 |

### 插件是什么：一句话定义

> **插件 = 界面启动时，在控制台（console）线程里被执行的一段代码。
> 执行时，机制会自动把运行空间里的 `__name__` 设为 `'__zml_plugin__'`。
> 除此之外，没有其它限制。**

没有基类要继承、没有固定入口函数要定义、不需要注册成某种对象 —— 机制只把源码
`exec` 到一个**独立命名空间**里（里面只有 `__name__` 与 `__file__` 两样），
其余一切靠插件自己 `import`。

**因此「能否正确、快速地执行」是插件作者自己的责任**：

| 作者要保证 | 不保证的后果 |
|---|---|
| 在 `__name__ == '__zml_plugin__'` 下能跑通 | 把注册放进 `if __name__ == '__main__':` ⇒ 插件加载时**静默不执行**（`_alg` 有一条警告兜底，但**不报错**） |
| 执行要快 | 它处在**界面启动的关键路径**上、同步执行；慢一点就是整个软件启动变慢，且不会提示是哪个插件 |

**标准写法**（两支用两个独立的 `if`，不要写成 `elif` —— 便于在 PyCharm 里单独调试）：

```python
from zmlx.system import execute_once
from zmlx.ui import gui


@execute_once(file=__file__)      # 一次运行里可能被调多次，防止重复挂菜单
def setup_ui():
    gui.add_action(menu='帮助', text='我的功能', slot=...)
    gui.add_action(menu='帮助', text='---')          # 分隔线（专用写法，不用给其它参数）
    gui.add_action(menu='帮助', text='我的另一项', slot=...)


if __name__ == '__zml_plugin__':
    setup_ui()                    # 插件机制执行：只注册，不开窗口

if __name__ == '__main__':
    setup_ui()                    # 直接 python 运行：方便自测
```

⚠️ `text='---'` 是**分隔符**（2026-10-26 加；判据是 `text`，不是 `name`）：它不建
action、不占名字、不判重，只在菜单末尾插一条线；`on_toolbar=True` 对它不生效（工具栏的分隔符仍要自己
`QToolBar.insertSeparator`）。

放在哪：外部插件的标准文件名是 `zml_plugin.py`，放在项目目录即可（**首次启动自动发现**，
之后可在「设置 → 插件」里增删）；随包分发的是 `plugins/builtin/` 下的 `.py`（**目录即语义**，
除 `__init__.py` 外每个都是插件，不需要登记）。⚠️ 2026-10-22 起还多一处：**自包含的插件可以
整个住进 `zmlx/scen/<包>/`**（`scen/easter_eggs/zml_plugin.py` + 它 import 的实现模块），
自动发现会展开 `scen` 下**一层**子目录 —— 这样「可关掉的功能」连同它的装配代码能一起搬走，
`ui/` 里不留死代码。两种位置地位相同，都按「启用 / 禁用」控制。
⚠️ 但**控件不属于插件**：只有装配代码与实现在同一个可关掉的功能里时才配这种形态
（2026-10-22 数据编辑器就因此从 `scen/editors/` 退回 `plugins/builtin/editors.py`，
控件留在 `ui/widgets/editors/`）。

哪些功能该做成插件：**关掉它，软件还能不能正常用？** 能 → 插件（`plugins/builtin/` 或
`scen/<包>/`）；不能（授权查询、用户管理这类**产品功能**）→ 留在 `extra_setups/`。

### 插件的三个概念与两个旋钮

「设置 → 插件」（`PluginListEdit`）里的七列：默认加载 / 优先级 / 名称 / 描述 / 来源 / 状态 / 临时加载。

| 概念 | 存在哪 | 作用 |
|---|---|---|
| **名单** | `zml_plugins`（有序） | 有哪些插件、按什么顺序显示与执行 |
| **优先级** | `zml_plugins` 的标记 | `high` / `normal` / `low`，只决定**谁先执行** |
| **禁用** | `zml_plugins` 的标记 | 启动时**不执行**这段代码 |

⚠️ **界面不支持拖动排序**（`setDragDropMode(NoDragDrop)`），也没有「上移 / 下移」接口 ——
**顺序不是用户能调的**（`add_file()` 登记的追加到末尾、自动发现按扫描顺序、`builtin/` 按文件名排序）。
**优先级是唯一能改执行先后的旋钮**：执行时按「高 → 正常 → 低」分三段、段内仍按名单顺序；
它**不改变列表里行的位置**。列表的**优先级列带色块**：高=红、低=绿、正常不画。

⚠️ **「禁用」≠ 撤销**：它只表示**下次启动不执行**；已派生的菜单项 / 后台线程不回收 ⇒
改启用状态必须**重启**。而「临时加载」是另一件事：**当场跑一次**（不写盘、不必重启），
与勾选互不写入，重启后是否执行**仍只看勾选**。

⚠️ **插件之间不该有先后依赖**（每个插件应独立、完整）；优先级只是万一排不开时的兜底手段。

### 命名遗留：显示叫「插件」，标识符仍叫 `setup_files`

2026-10-18 把「启动文件」这一概念统一改名为「插件」（菜单「设置 → 插件」、
插件文件名 `zml_plugin.py`）。**显示层已全部改名，但下面这些标识符刻意保留旧名** ——
它们是对外契约（链接、存档、用户环境变量），改名等于让已有配置失效：

| 保留的旧名 | 位置 | 为什么不能改 |
|---|---|---|
| `name="setup_files"` | `main.py` 的 `add_action` | ribbon 配置与已保存的界面布局按 action name 定位 |
| `edit_setup_files()` | `MainWindow` 方法 | `zmlx://gui/edit_setup_files` 文档链接；标签页存档串 `gui.edit_setup_files()`；外部脚本 |
| `zml_gui_setup_files` | `app_data` 存储键 | 已写入用户环境变量；新机制只**读一次**做迁移（见下） |
| `zml_gui_setup.py` | 旧插件文件名 | 兼容已有项目（`plugins._registry.LEGACY_PLUGIN_NAME`） |

⚠️ **控件已改名**（2026-10-18）：`SetupFileEdit` / `setup_file_edit.py` →
**`PluginListEdit` / `plugin_list_edit.py`**（「插件列表」比「启动文件编辑」准确）。
旧路径**不保留转发层**：插件机制这块本仓与外部工作区都零引用，留着转发只会让
「旧名到底还活多久」变成没人维护的悬案。

⚠️ **`ui/setup_files.py` 已删除**（2026-10-18）：它只转发 `get_rank` / `set_rank` /
`get_files` / `set_files` 四个名字，而前两个随「浮点 rank」一起从模型里去掉了；
全仓与外部工作区（`igg-hydrate-works` 12 个项目）都**零引用**。`get_files` /
`set_files` 请直接用 `zmlx.ui.plugins`。

⚠️ **浮点 rank 已去掉**：顺序由名单（`zml_plugins`）表达，插队由三档优先级
（`high` / `normal` / `low`）表达，禁用由 `disabled` 标记表达。旧环境变量
`zml_gui_setup_files` 与旧的 `rank: <hash>` 只在**首次启动时**被读一次用于迁移。

新增代码请用新叫法（`plugins` / `zml_plugin.py` / 「插件」），**不要**再扩散这些旧标识符。

---

## 与其他模块的关系

- 公共 API（`information`、`plot`、`gui_exec` 等）通过 `zmlx.exts.LazyImport` 在顶层命名空间中可用
- `zmlx.plt`：通过 `plot_on_figure` / `plot_on_axes` 在 GUI 中显示图形
- `zmlx.utils`：`GuiIterator`、`FrameRateCtrl` 与 GUI 系统协同
- 设计上追求独立：未来将减少对 `zmlx` 其他模块的依赖
