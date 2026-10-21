# AGENTS.md

**`zmlx/ui/`** 的规范补充页：**界面元素的注册 / 转发** + **控制台与线程模型**。

⚠️ **控件怎么写**不在本文件里 —— 控件骨架、命名、导入顺序、右键菜单、线程生命周期契约、
`refresh()` 的性能约束、自测与验收，一律看 [`widgets/AGENTS.md`](widgets/AGENTS.md)
（那是全仓控件的唯一规范来源；[`tabs/AGENTS.md`](tabs/AGENTS.md) 补充「哪些控件归 `tabs/`」）。
本文件回答**两件事**：① 新增的界面元素要不要在 `__init__.py` 里转发（§1–§5）；
② **后台线程怎么安全地动界面**、控制台的执行模型（§6）。

上承 `projects/zml/AGENTS.md` 与仓库根 `AGENTS.md`；冲突时以更具体者为准
（本文件 > `widgets/AGENTS.md` > `projects/zml/AGENTS.md` > 根 `AGENTS.md`）。

## 1. 默认**不**转发（2026-10-16 起）

⚠️⚠️ **新增的界面元素 —— 控件、对话框、工具模块、`extra_setups` 动作 —— 默认一律
不在任何 `__init__.py` 里转发（不追加 import、不加 `__getattr__`、不进 `__all__`）。**
需要用它时，写**子模块路径**直接导入：

```python
from zmlx.ui.tabs.image_browser import ImageBrowser        # ✅ 子模块路径（默认这样写）
from zmlx.ui.plugins.image_browser import show_image_browser   # ✅
from zmlx.ui.tabs import ImageBrowser                       # ❌ 新元素不要靠这条
```

### 为什么

| 理由 | 说明 |
|---|---|
| **导入期副作用** | `__init__.py` 是**导入期**就执行的：往里加一行，就等于让每一个 `import zmlx.ui.tabs` 的人都**被迫**付这次导入的代价。控件越重（可选依赖、大表、联网）越明显 |
| **循环导入** | 这正是 2026-10-16 真实踩到的坑：`widget/__init__.py`（当时还是真控件包）静态转发 `tabs/` 的名字，而 `tabs/code_history_view` / `output_history_view` / `readme_browser` 又在自己**顶层** import `widget/` 的底层控件 ⇒ 抛 `cannot import name ... from partially initialized module`。**不转发就没有这个环** |
| **无头模式** | `import zmlx.ui.utils` 曾因转发了「要求 Qt 存在」的模块，在无头模式下直接失败（见 `utils/__init__.py` 的说明） |
| **公共 API 只增不改** | 一旦某名字进了 `__init__.py` 就成了事实上的公共 API，**再也删不掉**；子模块路径没有这个包袱 |

⚠️ **注意「不转发」不等于「不能是顶层控件」。** 归属判据（顶层性 vs 底层组件）看的是
**它会不会被别的控件当子控件用**，与「有没有被 `__init__` 转发」**无关**。
`ImageBrowser` 就是现成范例：它是顶层控件、归 `tabs/`、**已挂菜单**，
但**没有**进 `tabs/__init__.py` —— 挂载点 `plugins/builtin/image_browser.py` 按子模块路径导入它。

## 2. 那什么时候才转发

只有一种情况：**为了「不断老路径」**。

`widget/`（整个包）与 `tabs/__init__.py` 里现有的转发，是 2026-10-16「控件分家」那次
留下的**兼容层**（老路径 `from zmlx.ui.widget import About` 等），**已弃用、2027-10-16 删除**
（详见 [`tabs/AGENTS.md`](tabs/AGENTS.md) §5）。它们是**历史包袱**，不是范例 ——
**新代码不许再往里面加名字**。

判据很简单：**「如果我不加这一行，会不会有人原来的代码就坏了？」**
- 会（老路径已被外部脚本 / 历史 `gui_restore` 用着）→ 才考虑加，且要写明弃用日期；
- 不会（**新元素**）→ **一律不加**。

## 3. 挂到界面上：走 `extra_setups/`，不动 `main.py`

给界面新增一个**入口**（菜单项、命令）时，**不要**去改 `main.py`（那个文件 2600 多行，
是所有界面的共用枢纽）。放到 [`extra_setups/`](extra_setups/)：它就是「额外菜单动作」的
落脚处，与 `vtk_view` / `testing` / `tetris` / `image_browser` 同一套路。

```python
# zmlx/ui/extra_setups/xxx.py
from zmlx.system import execute_once

@execute_once(file=__file__)
def setup_ui():
    from zmlx.ui import gui
    gui.add_func('show_xxx', _open)                     # 命令（给 gui_restore 重放用）
    gui.add_action(menu='显示', name='xxx', text='……',
                   slot=show_xxx, overwritable=False)   # 菜单项
```

写完**还要**在 [`extra_setups/__init__.py`](extra_setups/__init__.py) 里按现有
`try/except` 风格加一段调用（那里是**唯一**需要登记的地方 —— 那不算「转发公共 API」，
而是「让装配层知道有这个 setup」，正是 `extra_setups` 的用途）。

⚠️ **三个必须注意的点**（都是真踩过的，细节见 `plugins/builtin/image_browser.py` 的模块文档）：

1. **命令名要与 `MainWindow` 的方法名不撞车** —— `__init_gui_api` 会把主窗口的**所有公开
   方法自动注册**进命令表，撞名会把那个方法悄悄顶掉；
2. **命令名一旦发布就不能改** —— 标签页状态里存的就是 `gui.show_xxx()` 这串原文，
   重启时按原文重放（`gui_restore`）。要改就得照
   [`extra_setups/license_query.py`](extra_setups/license_query.py) 末尾那样留旧名别名；
3. **`oper` 里不要放有副作用的动作** —— `get_widget` 每次调用都会跑到它（点菜单也不例外），
   放个 `refresh()` 就等于「点一次菜单重扫一次」。

## 4. 现状速查

| 位置 | 是否转发 | 说明 |
|---|---|---|
| `ui/__init__.py` | 转发**极少**（`gui` / `plot` / `break_point` …） | 这是**门面**，外部唯一该用的入口；**只增不改**，新元素别往里塞 |
| `ui/widgets/__init__.py` | 静态转发底层控件（**真控件在这儿**） | 新代码用它 |
| `ui/widget/`（整个包） | **纯兼容垫片**：转发到 `widgets/` 与 `tabs/` | ⚠️ 导入即发 `DeprecationWarning`，**2027-10-16 删**；zmlx 内部**不得**再从这里导入 |
| `ui/tabs/__init__.py` | 静态转发 27 个顶层控件中的一部分 | ⚠️ 同为**兼容层**；**新控件不要加进去**（`ImageBrowser` 就没加） |
| `ui/utils/__init__.py` | 转发需要 Qt 的基础设施 | 见该文件 docstring：「三条转发」与「两条不转发」 |
| `ui/extra_setups/*` | **不**转发 | 靠 `extra_setups/__init__.py` 的 `setup_ui()` 登记 |
| [`ui/plugins/`](plugins/AGENTS.md) | **不**转发 | 机制（`_alg` / `_registry`）不对外暴露；`builtin/` 里的插件由启动时 `exec` 加载，不走 `import`。加插件的规范见 [`plugins/AGENTS.md`](plugins/AGENTS.md) |

## 5. 历史

- **2026-10-16（同日）**：控件包 **`zmlx.ui.widget` 改名为 `zmlx.ui.widgets`**（单数与
  Qt 自己的 `QtWidgets` 太像，极易看错）。旧名整个包变成**兼容垫片**：
  它把**所有**老路径都转发过来（底层控件→`widgets/`、顶层控件→`tabs/`，
  共 44 个模块 + 包级名字），导入即发 `DeprecationWarning`，**2027-10-16 删除**。
  ⚠️ 这也让「哪里是兼容层」变得一眼可见：**整个 `widget/` 就是**。
- **2026-10-16**：确立本约定「**新增界面元素默认不在 `__init__` 转发**」。
  同日 `ImageBrowser` 挂菜单时即按此办：挂载点 `plugins/builtin/image_browser.py` 按子模块
  路径导入 `zmlx.ui.tabs.image_browser.ImageBrowser`，**没有**动 `tabs/__init__.py`。
  此前 `widgets/AGENTS.md` §2「注册」一节写的是相反的规则（「想让
  `from zmlx.ui.widget import XxxView` 可用就追加一行 import」），已改为指向本文件。

## 6. 控制台与线程模型（2026-10-20 实测补写）

**一句话**：界面上跑长任务的地方只有**一个线程槽位**（控制台内核），而所有「从别的线程
动界面」的操作都必须经过 `gui` 缓冲区。这一章说的是这两件事的边界与用法 —— 写插件、
写菜单动作、写带后台线程的控件之前先读它。

> **`Console` 仍是长任务唯一槽位**
>
> 这里说的「长任务」指仿真、批量计算这类**要能被暂停/停止**、动辄几分钟到几小时的工作。
> **这句话不因新增工具而改变**：2026-10-20 加入的 `zmlx.ui.utils.thread_runner`（§6.8）
> 只解决「**多个短/中任务并发**」（扫描目录、加载图片、批量小请求），**不是** `Console`
> 的替代品 —— 它不接管工具栏的「暂停 / 继续 / 停止」（那三个按钮只对 `gui.break_point()`
> 生效），也不参与 `Console.thread` 的单槽位记账，两者**互不知情**。
>
> 于是三条边界，写代码前先确认自己没越界：
>
> 1. **别把长任务塞进 `thread_runner`** —— 它停不下来，只能「取消 + 放弃」（§6.8）；
> 2. **别把并发短任务塞给 `gui.start`** —— 单槽位，第二个请求被直接丢弃（§6.3）；
> 3. **更不要自己写 `QThread` 子类** —— 既有的 17 处属历史遗留，新代码走 §6.8。

### 6.1 涉及的角色

| 角色 | 位置 | 线程亲和性 |
|---|---|---|
| `MainWindow` | `main.py` | GUI 线程（它就是 `sys.stdout`，见 §6.4） |
| `Console` | `console.py` | GUI 线程（`QObject`，`parent=MainWindow`） |
| `ConsoleThread`（`QThread`） | `console.py` | **内核线程**：用户脚本/长任务真正跑的地方 |
| `GuiApi` | `utils/gui_api.py` | GUI 线程；**命令桥**：非 GUI 线程的调用在这里被搬到 GUI 线程 |
| `TaskProc` | `utils/task_proc.py` | GUI 线程；**异步队列**（丢下就走，拿不到结果） |
| `OutputWidget` | `widgets/output_widget.py` | GUI 线程；右侧常驻的「控制台」标签（§6.5） |
| `ThreadRunner` | `utils/thread_runner.py` | 无 Qt 依赖；**daemon 线程**（不是 `QThread`），每个任务一条，完成回调由信号泵回投 GUI 线程（§6.8） |

### 6.2 四条通道，怎么选

| 想要 | 用什么 | 谁执行 | 同步？ | 拿得到返回值/异常？ |
|---|---|---|---|---|
| 改界面（有现成导出函数） | `gui.xxx(...)` | GUI 线程 | ✅ 阻塞等 | ✅ |
| 改界面（**没有**导出函数） | `gui.call(func, ...)` | GUI 线程 | ✅ | ✅ |
| 跑长任务（脚本、仿真） | `gui.start(func, post_task=...)` | **内核线程** | ❌ 立刻返回 | 结果在 `Console.result` |
| 只是「稍后在 GUI 线程跑一下」 | `gui.add_task(func)` | GUI 线程 | ❌ | ❌（异常只打印） |

`gui.xxx` / `gui.call` 走的都是 `GuiApi.command`：把「命令名 + 参数」塞进一个通道，
`emit` 一个信号，由 Qt 的信号/槽把执行搬到 GUI 线程；调用线程**阻塞等待**，返回值与
异常原样带回（实测：`gui.call` 与 `gui.command` 的 `QThread.currentThreadId()` 都与主窗口
相同，而内核线程是另一个 id）。

⚠️ **通道池上限 20 个**：每个并发调用占一个，用满后打印 `Gui Command Ignored: ...` 并返回
`None`（**不排队**，不是「稍后重试」）。正常顺序调用只占 1 个，不会碰到；只有在一个线程里
同时起多个 `gui.xxx` 才可能撞上。

### 6.3 单任务约束（硬约束，2026-10-20 实测）

`Console` 只有**一个** `thread` 槽位，`start_func` 的第一件事是：

```python
if self.is_running():
    play_error()      # 响一声
    return            # 直接丢弃，不排队、不抛异常
```

实测：一个任务在跑时再调 `gui.start(...)`，第二个任务**根本不会执行**（标记列表保持空）。

⚠️ 这里的「只允许一个」指**这个机制**（控制台的线程槽位），不是「进程里只能有一个线程」——
界面里本来就有别的工作线程（图片浏览的扫描/解码、插件列表的 `_ScanWorker` 等）。它们
**不能**借控制台跑长任务，动界面同样要按 §6.4 走 `gui.*`。控制台线程的优先级由设置决定
（`load_priority()`，实测默认 `LowPriority`）—— 刻意不与界面抢 CPU。

推论（每条都踩过或会踩）：

1. **调 `gui.start` 之前必须自己判 `gui.is_running()`**，并把「忙」明确告诉用户。
   否则用户看到的是「点了没反应」——插件页的「临时加载」就是这么处理的
   （`plugin_list_edit._on_load_clicked`：忙时 `gui.status('控制台正在执行其它任务…')`）。
2. **不能在任务体里再 `gui.start`**（自嵌套）：要么被丢弃，要么把外层顶掉。
   要串行就在**同一个** `func` 里顺序写。
3. **「跑完再做」用 `post_task`**，不要再 `start` 一个。`post_task` 由
   `Console.__kernel_exited`（GUI 线程的槽）调用，**即使任务抛了异常也会执行** ——
   这正是「回写按钮/状态栏」应该待的地方。
4. `gui.start` 应**在 GUI 线程调用**（`Console.start_func` 的 docstring 明说
   「不支持多线程」）：它要建 `QThread`、连信号、改 `self.thread`。在控件的槽里直接调，
   或从后台线程用 `gui.call(lambda: gui.start(...))` 转一手。
5. 界面侧的配套：`操作 → 运行` 的 `is_enabled` 就是 `not is_running()`；暂停/继续/停止
   也都按 `is_running()` 开关（见 `main.py` 的 `console_exec` / `console_pause` …）。
6. **「多个短/中任务并发」不归本节管** —— 单槽位只约束「长任务」。要并行跑几个短任务，
   用 §6.8 的 `thread_runner`；反复调 `gui.start` 是错的，第二个必定被丢。

### 6.4 内核线程里动界面：规则

**只能用** `gui.xxx(...)`、`gui.call(func, ...)`、`print`。**不能**直接
`widget.setXxx(...)`（Qt 控件只能在 GUI 线程碰：轻则不刷新，重则崩，且不可复现）。

- **`gui.call` 是「没有导出函数时」的出口**。它执行的是你给的任意 callable，所以闭包里的
  控件访问也发生在 GUI 线程：

  ```python
  gui.call(self.btn.setEnabled, False)
  gui.call(lambda: self.label.setText(f'进度 {n}%'))
  ```

  ⚠️ 它是**同步**的：调用线程会等到 GUI 线程执行完。**绝不要**在持有锁时调它，也不要
  让 GUI 线程去等一个正在调 `gui.call` 的内核线程 —— 那是教科书式死锁。只要「稍后跑」、
  不要结果，用 `gui.add_task`。

- **`print` 是安全的**：`MainWindow` 自己被设成 `sys.stdout`（`main.py` 的 `__on_init`），
  它的 `write()` 把**整段**文本 `add_task` 到 GUI 线程再写控件（跨线程直接
  `isVisible()` 都是未定义行为，见那里的注释）。所以内核里 `print` 不需要额外处理。

- **`gui.break_point()` 是「暂停/停止」唯一的生效点**：内核线程在这里**阻塞**等「继续」，
  而 GUI 线程**径直返回**（`BreakPoint.pass_only`，按调用者身份区分 —— 否则 GUI 线程会
  自己等自己，界面彻底冻死）。长循环里必须放，否则「暂停」「停止」按了也没用。
  实测：暂停期间内核在 `break_point` 停住（0.5 s 内一圈都没多走），恢复后继续。

- **`gui.progress` / `gui.show_attrs`**：显示在右侧控制台标签里，内核里直接调即可。
- **`gui.status(text)`**：左侧状态栏的一行字（`statusBar().showMessage`）。
- **`gui.information` / `gui.question`**：模态对话框。`command` 是同步的，所以内核会
  **阻塞到用户点掉**为止（这本身就是一次「断点」）；`gui_buffer` 模块级的同名函数
  （`from zmlx.ui.gui_buffer import information`）还会先显式 `break_point()`；
  无界面时 `question` 退化为终端 `input()`。

### 6.5 右侧「控制台」标签（`OutputWidget`）

- 位置：`MainWindow.right_tabs`，标题「控制台」，`closeable=False`（**常驻、不可关**），
  由 `get_output_widget()` **懒创建**（第一次用到时才建）。
- 承载四样东西：`print` 输出（支持 ANSI 着色）、`progress` 进度条、`show_attrs` 属性表、
  底部的**命令行**（`>>>` 输入框，在控制台线程里 `eval`/`exec`，namespace 就是
  `app_data.space` —— **与脚本共用**，所以命令行里能拿到脚本刚定义的变量）。
- 面板**没打开**时，`print` 的**首行**会同步显示到左侧状态栏（`_write_output`），否则用户
  看不见脚本输出。这是「常驻到最后一次输出」的常显消息，不是 3 秒即逝的 toast。
- ⚠️ **`gui.add_message(...)` 不是控制台输出**：它写进「消息」标签/对话框并**落盘**
  （`tabs/message.py`，最多保留 50 条），用于「出了问题需要回看」的消息，别拿它刷日志。

### 6.6 现象 → 原因（排查表）

| 现象 | 原因 |
|---|---|
| 点了「运行」毫无反应，只响一声 | 控制台正忙，`start_func` 直接把请求丢了（§6.3） |
| 界面彻底冻死，「继续」也点不动 | GUI 线程被 `break_point` 挂住，或 GUI 线程在等内核线程 |
| 控件随机不刷新 / 偶发崩溃 | 从内核线程直接碰了控件，没走 `gui.xxx` / `gui.call` |
| 打印 `Gui Command Ignored: ...` | 20 个通道全被并发调用占满（§6.2） |
| 脚本 `print` 的内容看不到 | 面板没开 —— 看左侧状态栏（只有首行）；或面板被别的标签挡住 |
| 后一个任务覆盖/顶掉了前一个 | 单槽位；先判 `is_running()`（§6.3） |
| 暂停按了没效果 | 脚本里没放 `gui.break_point()`，它停不下来 |

### 6.7 要加一个「能在后台动界面」的能力，按这个顺序选

1. **它是主窗口的稳定能力** → 写成 `MainWindow` 的**公开方法**（`__init_gui_api` 会自动把
   所有公开方法注册成 `gui.xxx`），什么额外的都不用做。
2. **只有一次性逻辑 / 需要带一个对象或闭包** → `gui.call(func, ...)`，不要为它新增 API。
3. **只是稍后在 GUI 线程跑一下**（高频、不要结果，例如日志） → `gui.add_task(func)`。
4. **是长任务**（仿真、批量处理、要能被暂停/停止） → `gui.start(func, post_task=...)`，
   并按 §6.3 处理「忙」；任务里按 §6.4 动界面。
5. **是「多个短/中任务并发」**（扫描、加载、批量小请求，**不需要**暂停/停止） →
   `zmlx.ui.utils.thread_runner`（§6.8）；不要塞给 `gui.start`，也不要新写 `QThread` 子类。

### 6.8 多个短/中任务并发：`thread_runner`（2026-10-20 新增）

⚠️ **先记住前提**：`Console` 仍是长任务唯一槽位（见本章开头）。本节讲的是**另一件事** ——
「同时跑好几个短/中任务」，例如图片浏览的扫描/缩略图/解码、插件的批量小请求。这类工作
**不需要**暂停/停止，但需要并行，而且做完要回写界面。

```python
from functools import partial

from zmlx.ui.utils.thread_runner import run, count, cancel_all

btn.setEnabled(False)
handle = run(partial(load, paths), lambda: btn.setEnabled(True))   # 回调自动回投 GUI 线程
count()                 # 还有几个在跑
cancel_all(wait=0.2)    # 立刻叫停；返回「没能停下来」的个数
```

三条硬事实：

1. **线程是 stdlib daemon 线程，不是 `QThread`** —— 句柄被丢弃也不会出现
   `Destroyed while thread is still running` 那种硬崩；无头模式（`--no-gui`）照常可用。
2. **`cancel_all()` 不能真的「杀」线程**（Python 没有 `kill`）—— 它是**协作式取消**：
   任务体必须轮询 `task.check()` / `task.sleep()`，否则只能被**放弃**（daemon，不阻止
   进程退出，收工时也**不再**触发完成回调）。返回值是「没停下来的个数」，不是「全部已停」。
3. **完成回调默认回到 GUI 线程**（模块级信号泵），与「谁调的 `start`」无关；进程里没有
   `QCoreApplication` 时就地执行。它同时提供 `dispatch='inline'` 强制留在工作线程。

与 `Console` 的分工（本节存在的理由）：

| | `Console` / `gui.start` | `thread_runner` |
|---|---|---|
| 用途 | **一个**长任务（仿真、脚本） | **多个**短/中任务并发 |
| 排队 | 单槽位，忙时**丢弃**（§6.3） | 默认不限并发；超 `max_threads` **抛错**，不静默丢 |
| 暂停/停止 | 工具栏按钮 + `gui.break_point()` | ❌ 不参与；只能协作取消 + 放弃 |
| 完成回调 | `post_task`（GUI 线程，异常也执行） | `on_done`（默认回投 GUI 线程） |
| 线程类型 | `QThread`（内核线程） | daemon `threading.Thread` |

⚠️ **判断口诀**：需要「暂停/继续/停止」⇒ `gui.start`；只是「并行做完再回写界面」⇒
`thread_runner`。两者都不要拿来替代对方。

