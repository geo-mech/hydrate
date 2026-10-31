# AGENTS.md

**`zmlx/ui/plugins/`** 的规范补充页：**插件加载机制 + 随包分发的内置插件**。

⚠️ **本文件回答三件事**：插件体系**要达到什么**（§0）、本目录怎么分层（§1）、
**加一个插件要做 / 不要做什么**（§2 起）。
加载机制的 API 参考（11 个公共函数、名单 / 优先级 / 禁用三个概念）在 [`__init__.py`](__init__.py)
的模块文档；插件各自干什么在 [`../ReadMe.md`](../ReadMe.md) 的 `plugins/` 一行。
**三份文档各管一件事、不互相复制**（理由见 §5）。

上承 `projects/zml/AGENTS.md` 与 [`../AGENTS.md`](../AGENTS.md)；冲突时以更具体者为准
（本文件 > `../AGENTS.md` > `projects/zml/AGENTS.md` > 仓库根 `AGENTS.md`）。

## 0. 目标与本质：插件体系到底在做什么

这一节讲**为什么**。§1 之后讲的都是**怎么做**；两者冲突时，以本节的目的为准 ——
任何"流程上合规、但违背了这里的目标"的写法，都是错的。

### 0.1 要解决的问题：**不修改 `MainWindow` 就能加功能**

`main.py` 里的 `MainWindow` 是界面的骨架 —— 菜单栏、标签容器、命令表、控制台、状态栏。
插件体系存在的**唯一理由**是：让新功能**不必改动这个骨架**就能装上去。

由此得到唯一真正的准入判据：

> **这个功能能不能在不碰 `main.py` 的前提下装上去？**
> 能 → 可以做成插件；不能（必须新增 `MainWindow` 方法、必须改 `__init_actions`
> 或 `__init_gui_api`）→ 它就不是插件的活，按普通功能开发走。

`seepage_menu` / `editors_menu` 这类"只挂几行菜单"的插件之所以**完全合法**，
正是因为它们对 `main.py` **一个字都没要求**。（⚠️ 这两个文件 2026-10-22 已合并成
`builtin/editors.py`，成立的理由不变。）

⚠️ 反过来看也成立：如果某功能**非得**改 `main.py` 才装得上，说明插件体系在这里
没覆盖到 —— 该修的是 `gui` 的接口，不是"临时给 `main.py` 加个钩子让插件用"。
后者会让插件变成 `main.py` 的隐式补丁，下次重构就散架。

### 0.2 「尽可能独立、完整」是目标，但**不是**全部

写插件时应当尽量做到：

- **独立** —— 自己的代码、自己的资源，不依赖"别的插件先执行过"；
- **完整** —— 一个文件（以及它自己 import 的模块）就能实现整个功能。

这是**努力方向**，不是准入门槛。现有内置插件（`builtin/` 里 **17 个**，外加住在 `scen/`
下的**自包含**插件 `zmlx/scen/easter_eggs/`）的实际形态：

| 形态 | 数量 | 代表 | 是否合法 |
|---|---|---|---|
| **完全自含**：控件 + 算法 + 资源都在插件文件里 | 10 | `runtime_env` / `fractal_demo` / `easter_eggs`（两个游戏各是一个自含模块）/ `demo_menu`（连 `DemoView` 一起）/ `style_sheet_menu`（连 `StyleSheetEdit` 一起）/ `fn2_view`（连 `Fn2Widget` 一起）/ `pg_console`（连 `PgConsole` 一起）/ `viewers`（连 `TimerView` / `CwdView` / `TabDetailView` / `AppPathEdit` 四个小控件一起）/ `doc_view`（2026-10-22 由 `MainWindow.show_changelog` / `show_roadmap` / `_show_md` 搬来；自含，但没自带控件）/ `architecture`（2026-10-31 由 `setups/` 搬来；自含的文档页）—— 后几个都是 2026-10-22 / 10-31 由 `ui/tabs/`、`MainWindow` 或 `setups/` 并入 | ✅ |
| **半自含**：算法在文件内，界面借用 `gui` 的通用控件 | 2 | `zip_files` / `pdf_view`（借用 QtWebEngine） | ✅ |
| **只有入口**：控件在 `main.py` / `ui/widgets/` / `ui/tabs/`，文件里只有装配代码 | 2 | `admin_menu` / `editors`（全是 `gui.reg_file_type` + `gui.add_action`，控件在 `ui/widgets/editors/`） | ✅ |
| **入口 + 控件**：本来是「只有入口」，后来把「只有它在用」的控件也并了进来 | 3 | `solver_menu`（`SolverSelector`，2026-10-22）/ `image_browser`（`ImageBrowser` 连同 3 个后台线程，2026-10-30 由 `ui/tabs/image_browser.py` 整体并入，原模块删除、不留垫片）/ `user_admin`（`UserAdminView` 连同 `_Jobs` / `_Worker` 后台线程，2026-10-31 由 `setups/user_admin.py` + `ui/tabs/user_admin_view.py` + `ui/tabs/check_count_view.py` 合并，原模块删除、不留垫片；现住 `UserAdminView` 与 `CheckCountView` 两个控件） | ✅ |

**后两种同样合法**，而且在某些情况下**更正确**：

- 控件已被别的控件复用（`widgets/plt.py` 的 `MatplotWidget` 被 `widgets/editors/` 的
  `data_edit.py` 与 `interp_edit.py` 用）→ 搬进插件会把复用关系拆散；
- 控件是 `MainWindow` 的公开方法、且 `gui_restore` 依赖它的命令名（`show_solver_selector` /
  `show_style_sheet`）→ 搬走时**命令名必须保持不变**（插件里 `gui.add_func` 显式注册 +
  `setups/plugin_placeholders.py` 的占位兜底），已保存的标签页才能照常恢复。
  ⚠️ 2026-10-22 起这两个都已连同控件并入插件，可作为「命令名不变」的范例。

⚠️ 所以：**不能拿「它不够独立」当作拒绝一个插件的理由。** 判据只有 §0.1 那一条。
「独立、完整」只在**有选择余地**时用来排序：能自含就自含，不能就老实做一个入口。

### 0.3 本质：**一段在 console 线程里执行、`__name__` 被设成 `__zml_plugin__` 的代码**

**这就是插件的全部定义**（2026-10-22 定，`__init__.py` 的模块文档里是同一份）：

> 插件 = **界面启动时，在控制台（console）线程里被执行的一段代码**。
> 执行时，机制会自动把运行空间里的 `__name__` 设为 `'__zml_plugin__'`。
> **除此之外，没有其它限制。**

剥掉所有形态差异，一个插件就是**一段代码**。它不是某个基类的子类，不需要实现固定接口、
也不需要"注册"成某种对象 —— 顶部的 `# ** name = ...` 只是给「设置 → 插件」列表显示用的
注释，`code_config` 读它时**并不执行插件体**。

**没有任何固定入口函数**：机制不做「找 `main()` / 找 `setup_ui()`」这种事，它只
`exec` 你写下的代码。所以「在哪一行注册」完全由作者决定 —— 顶层裸调用、放进
`if __name__ == '__zml_plugin__':` 分支、包成函数再调，**都是合法的**。

它可以是：

- 挂几个菜单项 / 工具按钮；
- 在 `gui` 上注册几个新命令（`gui.add_func`），供脚本或别的插件调用；
- 开一个标签页（`gui.get_widget`）；
- 注册文件类型、改默认参数；
- 起一个后台任务；
- 什么都不挂，只做一次性的初始化。

在 §0.4 那条底线之上，**插件可以处理任何事情**：读写文件、起子进程、跑计算、开线程。
插件体系**不是沙箱** —— 没有能力白名单、没有权限隔离、也不做代码审计。要限制一个插件，
唯一的旋钮是「启用 / 禁用」，而它的含义只是**下次启动不执行这段代码**（见 §3）。

⚠️⚠️ **「能否正确、快速地执行」是作者自己的责任** —— 因为机制什么也不替你保证：

| 作者要保证的 | 为什么 |
|---|---|
| **在 `__name__ == '__zml_plugin__'` 下能跑通** | 机制只会用这个 `__name__` 执行一次。把注册放进 `__main__` 分支 = 插件加载时**静默不执行**（`_alg` 有一条警告兜底，但**不报错**） |
| **执行要快** | 它处在**界面启动的关键路径**上、同步执行。慢一个插件，用户看到的是整个软件启动变慢，且没有任何提示指出是哪个插件（见 §0.5） |

⚠️ **技术上的准确说法**：插件体本身是在**控制台内核线程**里 `exec` 的
（`main.py` 的 `plugins.load_all()` 位于 `__console_kernel` 内），
但它对界面的每一次修改都由 `gui` **派发到 GUI 线程**执行。所以从效果上看，
它就是"一段在 GUI 线程上跑的代码" —— 这正是下面这条基本条件存在的原因。

### 0.4 最基本的条件：动界面**只能**经过 `gui` 缓冲区

插件与"随手写 Qt 代码"的分界线，也是**最基本**的一条规则：

> **对 GUI 的所有操作，都必须借助 `gui` 这个缓冲区，通过 `gui.xxx(...)` 发起。**

```python
# ✅ 一律走 gui.*
from zmlx.ui import gui

gui.add_action(menu='帮助', text='我的功能', slot=...)
gui.add_func('do_something', do_something)
gui.information('标题', '内容')

# ❌ 不要自己抓窗口、不要直接改控件
from zmlx.ui.main import MainWindow     # 不持有 MainWindow
main_win.menuBar().addMenu(...)         # 不碰 Qt 对象树
widget.setText('...')                   # 不跨线程改控件
```

三条理由：

1. **线程安全** —— 插件体在控制台内核线程里跑，Qt 控件只能由 GUI 线程碰。
   `gui.xxx` 会把调用**排队派发**到 GUI 线程；直接改控件就是跨线程改 UI，
   轻则显示错乱、重则崩进程。
2. **不穿透框架** —— 一旦插件直接操作 `MainWindow` 或 Qt 对象树，`main.py` 的内部结构
   就成了**事实上的公共 API**，它一重构，插件全废。走 `gui` 则只依赖那一层薄接口。
3. **无头模式自动降级** —— 没有界面时 `gui.*` 一律 no-op，同一段插件代码在无 GUI
   环境下不会炸。

⚠️ **这不等于「插件里不能有 Qt 代码」**：插件**可以**定义自己的 `QWidget` 子类
（`tetris.py` 就有 `TetrisWidget`）。区别在于 —— **造控件**是自己的事，
**把控件挂到窗口上**必须走 `gui.get_widget(...)`。控件内部的绘制、事件、
子控件布局当然直接用 Qt，那条线画在"与主窗口的边界"上，不是画在"有没有 Qt"上。

⚠️ 本节讲的是**写插件代码**的约束。机制层面另有几条**硬约束**（独立命名空间 /
禁用≠撤销 / 必须 UTF-8 / 临时加载≠启用），见 §3 —— 两者是不同层面的东西，不要混为一谈。

⚠️ **`gui.xxx` 没有你要的那个函数时**，不要退回「直接改控件」，用 `gui.call`：

```python
gui.call(self.btn.setEnabled, False)              # 在 GUI 线程执行，返回结果/抛异常
gui.call(lambda: self.label.setText(f'进度 {n}%'))
```

它把「任意可调用对象」派发到 GUI 线程执行（同步、阻塞到执行完），所以闭包里的控件访问
也是安全的。⚠️ 别在持有锁时调它。**长任务**另外要用 `gui.start(func, post_task=...)`，
而它是**单任务**的（忙时会被丢弃）—— 完整的四条通道、单任务约束与死锁排查见
[`../AGENTS.md`](../AGENTS.md) §6。

⚠️ **`Console` 仍是长任务唯一槽位**：需要暂停/继续/停止的工作走 `gui.start`；
「多个短/中任务并发」（批量小请求、扫描）走 `zmlx.ui.utils.thread_runner`
（§6.8），不要反复调 `gui.start`（第二个必被丢），也不要新写 `QThread` 子类。

### 0.5 执行要快：加载期只「接线」，不「干活」

插件加载发生在**界面启动的关键路径**上：`main.py` 启动时调 `load_all()`，逐个 `exec`
所有启用的插件。每个插件多花 100 ms，十个就是 1 秒 —— 用户看到的是**整个软件启动变慢**，
而且没有任何一处提示告诉他"是某个插件拖的"。

所以加载期的正事**只有两件**：**把功能挂到界面上**（`gui.add_action` 之类），
或者**在 `gui` 上添加新的 API**（`gui.add_func`，让脚本或其它插件能调）。
除此之外的一切，都应当推到"用户真正用到它"的时刻：

| 加载期该做 | 加载期**不**该做 |
|---|---|
| `gui.add_action` / `gui.add_func` | 扫描目录、读大文件、解析数据 |
| 注册文件类型、定义类与常量 | 预建标签页控件、做布局计算 |
| 读取**很小的**配置 | 连网请求、`pip install`、跑仿真 |
| 建少量轻量对象 | 打开数据库、遍历工作路径 |

**重活要么推迟、要么进后台线程**：

- 推迟到：点菜单的那一刻，或标签页**首次打开**时；
- 后台：`gui.start(...)` 或自建 `QThread`；**子线程里绝不碰控件**，结果用信号回主线程。

现有代码处处如此，可作参照：`image_browser` 的目录扫描在 3 个后台线程里、
`runtime_env` 的依赖检测在 `EnvCheckThread` 里、`plugin_list_edit` 的扫描走
`_ScanWorker` —— **没有一个是在插件加载时干的**。

⚠️ 反过来说：如果一个功能**必须**在加载时干重活（例如启动即恢复上次的全部标签页），
那它多半不该做成插件 —— 它是框架自己的职责。

## 1. 目录结构：机制在上层，插件在 `builtin/`

```
zmlx/ui/plugins/
├── __init__.py      公共 API（8 个）+ load_all / rescan / get_meta；机制说明也在这里
├── _alg.py          发现（扫目录）与执行（exec 源码）
├── _registry.py     名单 / 优先级 / 禁用 —— 状态的唯一真相
└── builtin/         随包分发的插件：这里每个 .py 都是一个插件
    ├── __init__.py  包标记 + 「目录即语义」的说明（**不是**插件）
    └── image_browser.py …（17 个）
```

⚠️ 2026-10-22 起「内置插件」有**两个位置**：`builtin/`（本目录），以及 **`zmlx/scen/<包>/`**
（把入口 `zml_plugin.py` 与它 import 的实现模块一起放进去，即「包自己就是一个插件」，
范例 `zmlx/scen/easter_eggs/`）。后者靠自动发现：`scen` 是搜索
路径之一，扫它**一层子目录**里的 `zml_plugin.py`。地位与 `builtin/` 插件完全相同
（都受「启用 / 禁用」控制）。选哪个：**能自含就放 `scen/<包>/`**（关掉功能时连装配代码
一起关掉），只在 `ui/` 里留一个入口的「只有入口」型仍放 `builtin/`。

⚠️ **但「控件」不属于插件**：只有当**装配代码 + 实现**都属于那个可关掉的功能时，才配
「包自己就是一个插件」。控件若本身是通用的（`ui/widgets/editors/seepage_edit.py` 就是
纯控件），它该留在控件层，插件只留装配 —— 2026-10-22 数据编辑器正是因此从
`scen/editors/` 退回 `builtin/editors.py`（「只有入口」型）。

⚠️ **一个目录只能有一个 `zml_plugin.py`**：几个自含模块想共享一个开关，就放**同一个**
`scen/<包>/` 下、由那一个入口去调它们（范例 `scen/easter_eggs/`：一个入口、两个游戏）。
不要再往 `scen/<包>/<子包>/zml_plugin.py` 嵌套 —— 那样「`scen/<包>` 自己算不算插件」
就没有答案了。

**判据：目录即语义。** `builtin/` 里除 `__init__.py` 外**每个 `.py` 都会在启动时被执行**；
`plugins/` 根目录下的 `.py` 是**机制代码**，一个都不会被执行。

⚠️ `_` 前缀**只表示「内部实现」**（`_alg` / `_registry`），与「会不会执行」**无关** ——
执行只看文件在哪个目录。2026-10-19 之前两者同目录，靠「不以 `_` 开头即插件」区分，
于是往 `plugins/` 丢一个临时脚本 / 实验文件 / 单测就会被**静默执行**；下沉一层正是为了
消掉这条隐式判据。

## 2. 加一个内置插件：六步

1. **在 `builtin/` 新建文件**（不放 `plugins/` 根；也**不要**叫 `zml_plugin.py` —— 那是
   外部插件的标准名，语义完全不同）。
2. **顶部写元数据**（`algs.code_config` 只 `exec` 这些注释行，**不会执行插件体**）：

   ```python
   # ** name = '图片浏览'
   # ** desc = '扫描工作路径下的图片，左侧缩略图相册 + 右侧大图预览'
   # ** enabled = False      # 彩蛋 / 依赖可选库 / 实验性：默认不加载
   ```

   三项都可选：没 `name` 用文件名，没 `desc` 显示「（无描述）」，没 `enabled` 视为启用。

   ⚠️ 另有**两个只读不生效**的预留键（2026-10-23 加，给将来的插件依赖用）：

   ```python
   # ** inner_name = 'image_browser'              # 内部标识（str），缺省 None
   # ** dependencies = ['viewers', 'data_editor'] # 依赖的 inner_name 列表，缺省 None
   ```

   - **`inner_name` 没写就是 `None`，不回落到文件名** —— `name` 那条回落规则**不要**照搬，
     否则每个插件都「有了标识符」，「没写」与「写了」就分不清。
   - **`dependencies` 缺省是 `None` 而不是 `[]`**：`None` = 没声明，`[]` = 明确无依赖。
   - `inner_name` 目前**只被当成「可以用名字指代插件」的标识**（`load_now` / `is_loaded` /
     `get_load_error` 接受它），不参与排序、界面也不显示；写坏了只发警告，
     不会让该插件的其它配置失效。详见 `_alg._parse_inner_name`。
   - `dependencies` **会被加载流程使用**（见下），写坏了同样只发警告。

   ⚠️ **但 `dependencies` 自 2026-10-24 起会被「加载」使用**：把一个插件加载成功后，
   会递归加载它声明的依赖（`_alg.load_with_deps`）。三条硬约束：

   1. **顺序**：执行自己 → 成功才标记 → 再拉依赖；自己失败就不标记、也不碰依赖。
      这个顺序**天然截断循环依赖**，不要改成「先拉依赖」。
   2. **依赖不看「禁用」**：禁用只表示「启动时不自动加载它」，依赖是被主插件拉起来的。
      所以「A 启用、B 禁用、A 依赖 B」⇒ B 仍会执行（只执行一次）。
   3. **依赖失败只警告**：主插件已经执行、无法回滚，`load_now` 仍返回 True。
3. **注册函数用 `@execute_once(file=__file__)` 包住** —— `load_all` 在一次运行里可能
   被调用多次，没有它就会重复挂菜单。
4. **文件末尾自己调**（**没有人**会替你调，这与 `setups/*.py` 不同）：

   ```python
   if __name__ == '__zml_plugin__':
       setup_ui()      # 被插件机制执行：只注册，不开窗口

   if __name__ == '__main__':
       test_1()        # 直接 python 运行：开窗口自测
   ```

   ⚠️ **两支用两个独立的 `if`，不要写成 `if` / `elif`**：两种运行方式互不相干，
   各自独立判断更清楚，而且在 PyCharm 里单独调试「直接运行」那一支更容易
   （`elif` 会让它看起来依附于前一个条件）。

5. **自测**：`python zmlx/ui/plugins/builtin/<name>.py`（此时 `__name__` 是 `__main__`）。
6. **验证**：重启 GUI →「设置 → 插件」→ 点该行的「**临时加载**」—— 当场就能看到它加的
   菜单（不必勾选、不必重启、不写任何设置）。确认要长期生效，再勾上「**默认加载**」并重启
   （第一列，2026-10-25 由「启用」改名 —— 见下方 §2 的说明）。
   ⚠️ **禁用的插件也点得动**（见 §3 第 4 条）—— 能试的恰好就是这一批。

⚠️ **把 `MainWindow` 的方法搬进插件**（范例：`get_vtk_view` 2026-10-22 搬进
`builtin/vtk_view.py`）—— 只适用于「**只服务这个插件、且依赖可选库**」的方法。
搬的时候有一个必然的坑：

> **`MainWindow` 的公开方法会自动变成 `gui.xxx`**（`__init_gui_api` 逐个
> `list_member_functions()` 注册）。方法一搬走，**那串命令名就没了** —— 必须在插件里
> 显式 `gui.add_func('旧命令名', 新函数)` 补回来，否则原来的调用方（很可能就是本插件
> 自己的菜单 slot）会报 `gui function <xxx> not found`，而插件默认不加载、**极容易漏测**。

⚠️ **推荐的补救形态：占位函数放在 `../setups/plugin_placeholders.py`，插件
`add_func` 覆盖它。**（2026-10-22 定；现有 **15 条**：`get_vtk_view`、
`show_style_sheet`、`show_demo`、`show_fn2`、`show_pg_console`、`open_pdf`、
`show_solver_selector`、`show_timer`、`view_cwd`、`show_image_browser`、`show_tab_details`、
`show_file_finder`、`show_calendar`、`show_changelog`、`show_roadmap` —— 全部实测确认
「占位 → 插件覆盖」生效。⚠️ `show_image_browser` 是 2026-10-26 补的：「文件 → 浏览」
子菜单合并之后，关掉「图片浏览」插件时历史标签页得有地方落地。）

⚠️⚠️ **占位只占「命令」，不占「菜单项」**（2026-10-25 定，别再往回加）：

`gui.add_action(slot=...)` 在**调用那一刻**就把那个 callable 绑到 `QAction` 上了；
插件后来 `gui.add_func` 只能换掉**命令表**里的一项，**换不掉已经连上的槽**。想让占位
菜单项在插件加载后变「活」，就得靠 `add_action` 的覆盖能力把那条 action 就地改掉
（语义见下一节）—— 但**仍然不建议**这么做：一条占位菜单项只是「插件关掉时菜单里多一行」，
**收益很小、风险很大**。规则一句话：

> **菜单项由插件自己挂；插件关掉，那一行就该消失。插件没启用时，用户调
> `gui.xxx()` 得到的是一句可操作的提示 —— 那才是占位存在的理由。**

### `overwrite` 到底管什么（2026-10-25 初版，2026-10-26 重写，2026-10-27 由 `overwritable` 改名）

⚠️ **它是「`name` 已经被占用时怎么做」，不是「能不能被别人覆盖」这个反问**：

| `overwrite` | `name` 已被占用 | `name` 不存在 |
|---|---|---|
| `True`（默认） | **就地覆盖**：用本次参数重设那个已有 action（槽、图标、提示、文字、快捷键、动态回调），它**留在原来的菜单位置**，菜单里**始终只有一条** | 正常挂上 |
| `False` | 发一条 `UserWarning`（说明撞的是哪个菜单项）并**直接 `return`**，已有那条**保持原样** | 正常挂上 |

⚠️ **参数名为什么改**（2026-10-27）：`overwritable` 是形容词
（「（这个 action）**可被**覆盖」），说的是**别人对我**的操作；而它实际管的是**这一次调用
要不要覆盖已经存在的那条**，说的是**本次调用的动作** —— 视角正好反了。旧名仍可用，但会发
`DeprecationWarning`，**2027-10-27 删除**；两个都给且含义相反时直接抛 `TypeError`。

⚠️ **判据是 `name`**：显式给了就用它；没给时 `add_action` 会按「`menu` 路径 + `text`」
自动生成（`text` 是函数时按其身份，**不调用它**），所以「同 menu + 同 text」的第二次
注册同样会命中覆盖。

所以：

- `overwrite=False` 是「**只挂一次**」—— 适合插件自己的条目（`# ** enabled` 有开关、
  `setup_ui` 又有 `@execute_once`，本来就只跑一次；`False` 是双保险，防止临时加载 +
  启动都跑过时挂出第二条）；
- `overwrite=True` 是「**后来者胜**」—— 同一段注册代码跑第二遍时，菜单不会变成两条，
  而且**只有最新的槽生效**（历史槽会被替换掉，不会一次点击跑一串）；
- 两者都**不会**在菜单里留下重复条目。

⚠️ **覆盖时哪些参数会被继承**：``icon`` / ``tooltip`` / ``shortcut`` / ``is_enabled`` /
``is_visible`` 传 ``None``（或不传）就**保持原值**；只有 ``text`` 与 ``slot`` **一定**会被
本次的值替换。别指望「不传图标就变默认图标」—— 那是**新建**时的行为。

```python
# setups/plugin_placeholders.py —— 占位：只给指引，不 import 可选库
def get_vtk_view(*args, **kwargs):
    _say('get_vtk_view', 'VtkView')

PLACEHOLDERS = [('get_vtk_view', get_vtk_view), ...]

@execute_once(file=__file__)
def setup_ui():
    from zmlx.ui import gui
    for name, func in PLACEHOLDERS:
        gui.add_func(name, func)
```

⚠️⚠️ **为什么放 `setups/` 而不是留在 `MainWindow`**（2026-10-22 从 `main.py` 搬出）：

1. **顺序天然正确**：`setups.setup_ui()` 与 `plugins.load_all()` 在
   `__console_kernel` 里**顺序执行**（先 `setups`、后插件），而两者都在 `gui.set(api)`
   之后 —— 「先挂占位、插件再覆盖」是**同一根顺序链**上的一前一后，不依赖「控台线程 vs
   GUI 线程」这种跨线程的时序巧合；
2. **`main.py` 保持骨架**：这些占位一个参数都不读、只打一句话，留在 `MainWindow` 里
   纯粹是给插件擦屁股；而且 `MainWindow` 的公开方法会被**自动注册**成命令，占位写在那儿
   就得靠「插件后写」才能让出位置 —— 读代码时几乎看不出这层关系。

⚠️ **占位用 `*args, **kwargs`，不要抄插件的具名参数**：它一个参数都不读，所以不该声明
参数形状 —— 具名签名等于把插件的参数表**复制**一份，插件一改（加参数、改默认值）这里
立刻过时，而且看起来像真实现。⚠️ 也**不要**补 `return None`：函数体只有这一句提示、
本来就在末尾、隐式返回 `None`，多写一行既没有信息量，又让人以为这里有个「返回值契约」要守。

这么做的前提是**两条都已核实**（别凭印象）：

1. **后写者胜**：`setups.setup_ui()` 在 `plugins.load_all()` **之前**执行
   （`__console_kernel` 的顺序，见 [`../setups/AGENTS.md`](../setups/AGENTS.md) §3）；
   `GuiApi.add_func` 落到的 `funcs` 是普通 `SharedDict`，`set` 就是赋值、不合并 ——
   所以插件里的 `add_func` 一定**覆盖**占位。⚠️ 改 `__console_kernel` 的顺序时要重新确认；
2. **不注销命令**：**不要**用 `gui.add_func(name, None)` 去「删掉」占位（`GuiApi.add_func`
   支持传 `None`）—— 那条路只让 `gui.xxx` 报 `not found`，什么都没说。占位能让命令一直存在。

⚠️ 占位里**不要写实现**（尤其不要 import 可选库）：真正的逻辑只有插件里那一份。

⚠️ **禁用的插件同样受益**：比如 `admin_menu` 默认不加载，它那条 `show_calendar` 的
占位会一直生效 —— 用户调用 `gui.show_calendar()` 看到的是一句「请先启用『Admin 功能』
插件」，而不是 `gui function <show_calendar> not found`。

⚠️ **加/删插件命令时同步这里**：占位表 `PLACEHOLDERS` 与插件名（`# ** name`）必须对得上；
另有一个插件**没启用也必须能调**时（例如 `zmlx.__init__` 里的 `gui.show_demo()`），
也靠它兜底。

⚠️ 反过来说：**不要**为了「让 `main.py` 变短」就把通用方法往插件里搬 —— 通用能力
（`get_widget` / `get_figure_widget` / `get_plot_widget`）留在 `MainWindow`，它们
本来就该是骨架的一部分。

⚠️ **临时加载与「默认加载」是两件事**：前者只让它在**本次运行**里跑一次（`load_now`，进程级
记录，成功后再点无效 —— **启动时 `load_all` 执行过的也算**，所以勾选着启动的插件，
那一列直接显示「已加载」且点不动）；后者是**持久设置**，决定下次启动跑不跑。两者互不写入对方。

⚠️ **界面第一列叫「默认加载」**（2026-10-25 由「启用」改名，见
[`../tabs/plugin_list_edit.py`](../tabs/plugin_list_edit.py)）：改的**只有显示文字** ——
函数名 `is_disabled` / `set_disabled`、标记 `disabled`、键 `zml_plugins` 一律照旧，
本文后面出现的「禁用」指的都是机制侧那个概念（= 仅启动过滤），不是界面上的字。

⚠️ `load_now` / `is_loaded` / `get_load_error` 的参数都是「**路径或 `inner_name`**」
（2026-10-24 起），内部**先解析成路径**再查表 —— `_loaded` / `_load_errors` 的键永远只是
规范化路径。所以「按名字加载过」的插件，再按路径调 `load_now` 会正确返回 `False`。
解析顺序写死为「存在的文件 → 名单里 `inner_name` 精确相等」，重名取 `get_files()` 顺序里的
第一个并警告。详见 `_alg._resolve` 的 docstring。

⚠️⚠️ **因此「临时加载不受禁用限制」是必须的**：启用的插件启动时早跑过（按钮是
「已加载」、点不动），能点的只有禁用的那一批 —— 两者一绑，按钮对谁都无效。

⚠️ **它跑在界面的控制台线程**（按钮里调 `gui.start`）—— 与启动时 `load_all` 走的是
**同一条通道**（`main.py` 的 `__console_kernel` 就在那个线程里）。所以插件照常写
`gui.add_action(...)` 即可，**不需要**自己处理线程，也没有「必须在 GUI 线程」的限制：
`gui.*` 的每次调用都由 gui 缓冲区派发到 GUI 线程。代价是控制台同一时刻只跑一个任务 ——
加载期间它在「忙」，别的脚本会被拒。

**不需要**改 `main.py`、`setups/__init__.py` 或任何 `__init__.py` —— 加文件就够了。
（⚠️ 唯一的例外是「搬走主窗口方法后要留占位」：那要去
[`../setups/plugin_placeholders.py`](../setups/plugin_placeholders.py) 加一行，
见本节上方。）

## 3. 五条硬约束

| 约束 | 含义 |
|---|---|
| **独立命名空间** | 插件在自己的 dict 里 `exec`：只有 `__name__ == '__zml_plugin__'` 和 `__file__`。**没有** `app_data.space`、也看不到别的插件的模块级名字。要什么就自己 `from zmlx... import ...` |
| **禁用 = 仅启动过滤** | ⚠️ **这不是「禁止执行」，也不是执行许可。** 它过滤的**只有** `load_all()` 那一层「启动时自动加载」。**三件事不受它影响**：① `load_now`（临时加载，默认 `ignore_disabled=True`）；② **被其它插件作为 `dependencies` 拉起**；③ 已经派生的东西（菜单项、后台线程）**不回收** ⇒ 改启用状态必须**重启**才生效 |
| **必须 UTF-8** | `load_all` 用 `read_text(..., encoding='utf-8')`；读不出即 `OSError`，该插件记为 `Failed`（其余插件继续） |
| **临时加载 ≠ 启用** | `load_now`（临时加载）**不受禁用限制**、也不改任何设置 —— 因为启用的插件启动时早跑过、按钮已是「已加载」，能点的恰好是禁用的那一批；两者一绑，按钮对谁都无效（2026-10-22 实测过的回归）。要严格模式由调用方传 `ignore_disabled=False` |
| **全局开关只管「这一次」** | `main.py` 用 `app_data.get('run_plugins', app_data.get('run_setup', True))` 决定启动时要不要调 `load_all()` —— **默认执行**。⚠️ 注意这里 `run_plugins` / `run_setup` 都是 **`app_data` 的键名**（旧键 2027-10-22 删），与函数名无关：函数在 2026-10-23 已由 `run_setup()` 改名为 `load_all()`。只有 `gui_buffer.open_gui_without_setup()` 写它，**它是运行时开关、不落盘**；想永久关掉某个插件请用 `set_disabled`，别在代码里动这个键 |

⚠️ **「禁用」为什么叫这个名字（以及为什么不改名）**：它的**字面**比**语义**宽，这是已知的。
曾评估改名为 `auto_loadable`，结论是**不改**：① `disabled` 是 `zml_plugins` 里的**持久化
标记**（`<路径>:*:high:disabled`），改名要做数据迁移，属 L2；② `not auto_loadable(path)`
是**双重否定**，并不更好读；③ 语义还要等依赖功能稳定后再审视一次。
详见 PLAN `T-20261023-11`。**定义以本表这一行为准**：禁用 = 仅启动过滤。

## 4. 别放错地方：`plugins/` 还是 `setups/`

判据：**关掉它，软件还能不能正常用？**

| 放哪 | 收什么 | 用户能关掉吗 |
|---|---|---|
| `builtin/`（本目录） | 可关闭的**非核心功能**：工具、演示、彩蛋、文档页、管理 / 查询页 | ✅ 能 |
| [`../setups/`](../setups/) | **必加载**的装配：目前只剩「插件命令的占位」（`plugin_placeholders.py`） | ❌ 不能 |

把「必须存在、否则界面上会出现悬空命令」的东西做成插件，是错的 —— 这也正是
`plugin_placeholders.py` 留在 `setups/` 的理由（它必须**先于**插件注册）。

⚠️ **2026-10-31 有两条搬了进来，判据的写法值得对照**（别再把它们搬回去）：
- `architecture`：纯文档页，关掉只少一个菜单项 ⇒ 明显可关。
- `user_admin`：2026-10-18 曾以「这是产品功能」为由**搬出去**，2026-10-31 **按同一判据
  重判后搬回来** —— 因为关掉它，建模 / 求解 / 绘图照样能用；随后 `license_query.py`
  （登录记录 / 反馈记录两条命令）也并了进来，「帮助 → 用户」整个子菜单因此整块归本插件。
- ⚠️ 判据问的是「**关掉还能不能用**」，不是「重不重要」，也不是「是不是产品功能」。
  真正关不掉的是**登录与授权检查本身**（`MainWindow` / `tabs/license_register.py` /
  `widgets/license_button.py`）—— 它们本来就不在这两个目录里。

## 5. 三份文档各管一件事

| 文档 | 唯一职责 |
|---|---|
| 本文件 | **目标与本质**（§0）+ 目录分层 + 加插件的步骤与禁忌 |
| [`__init__.py`](__init__.py) | 11 个公共 API、三个状态概念、`zml_plugins` 的存储格式 |
| [`../ReadMe.md`](../ReadMe.md) | 插件各做什么、挂在哪（含 `scen/` 下的自包含插件） |

⚠️ **插件清单只在 `../ReadMe.md` 维护**，本文件不复制。2026-10-19 就出现过「12 个」与
「11 个」两套说法（后者是算错 15−3），根源是同一份清单散落在多处。增删改插件时，
**只改 `../ReadMe.md` 的那一行**，并顺手跑一次 §7 的计数命令。

## 6. 常见坑（都踩过）

1. **入口写在 `if __name__ == '__main__':` 里 → 整段静默不执行**。机制执行时 `__name__`
   是 `'__zml_plugin__'`；`_alg._warn_legacy_entry` 会发警告（判据很窄：顶格 `__main__`
   分支 + 分支外无任何顶层调用 + 全文没提 `__zml_plugin__`），但**只有**这条警告，
   不会报错。
2. **往 `builtin/` 放工具模块 → 被当插件执行**。工具放上一层并以 `_` 开头。
3. **搬动已有插件的文件 / 改名 → 必须补路径迁移**。名单 `zml_plugins` 存的是**绝对
   路径**：文件一挪，旧记录被当「文件缺失」跳过（不报错），而新路径没有任何记录 ⇒
   用户勾开过的彩蛋**静默**退回默认关闭。现有规则在
   `_registry.migrate_builtin_paths()`（由 `_alg._scan_once()` 调用）；再搬动时要在那里
   补一条规则，并保证**标记原样保留**、新旧记录**合并**（否则同一插件会被执行两次）。
4. **`gui.add_func` 的命令名不能与 `MainWindow` 方法同名**，也不能事后改名（标签页状态
   里存的就是那串原文）。详见 [`../AGENTS.md`](../AGENTS.md) §3。
   ⚠️ **准确的例外**（2026-10-22 定）：把一个方法搬进插件后，**不要**在 `MainWindow`
   里留同名方法，而是把占位放进 [`../setups/plugin_placeholders.py`](../setups/plugin_placeholders.py)，
   由插件的 `add_func` 覆盖它 —— 前提与做法见本节上方「把 `MainWindow` 的方法搬进插件」。
   除此之外，撞名一律算 bug：后注册者会**悄悄**顶掉主窗口方法。
5. **`builtin/__init__.py` 不要删**：它是包标记，`pyproject.toml` 的 `packages.find`
   靠它识别这个目录；没有它，插件在打包时可能整个丢掉。

## 7. 验收清单

```bash
# 1. 内置插件计数（应为 17；另有 scen/easter_eggs/ 一个自包含插件在该目录外）
ls zmlx/ui/plugins/builtin/*.py | grep -v __init__ | wc -l

# 2. 名单 / 排序 / 禁用 / 路径往返的离线自检（不需要 Qt，会打印 test_1 passed）
python -m zmlx.ui.plugins._alg
```

⚠️ 上面两条都**不需要 Qt**（`import zmlx.ui.plugins` 不会拉起 PyQt）。涉及界面的自测
（真的把菜单挂上去看）要用系统 WinPython，见 `projects/zml/AGENTS.md`。
