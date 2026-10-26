# AGENTS.md

**`zmlx/ui/widgets/`** 的唯一规范来源（新建控件按此做）。上承 `projects/zml/AGENTS.md` 与仓库根
`AGENTS.md`；冲突时以更具体者为准（本文件 > `projects/zml/AGENTS.md` > 根 `AGENTS.md`）。

「控件」= 放在 `widgets/` 或 [`../tabs/`](../tabs/AGENTS.md)、被 `MainWindow` 或其它控件复用的
**QWidget 子类**（少数是 `QGraphicsView` / `QTextBrowser` / `QAbstractTableModel` 的子类）。

## 0.0 目录改名：``widget`` -> ``widgets``（2026-10-16）

⚠️ **本目录 2026-10-16 由 ``widget/`` 改名为 ``widgets/``**。原因：单数 ``widget`` 与 Qt
自己的 ``QtWidgets`` 只差一个前缀，读代码时**极易看错**；改名后也与 ``tabs`` / ``utils``
这些复数目录名一致了。

⚠️ **旧的 ``zmlx/ui/widget/`` 整个变成了兼容垫片**（导入即发 :class:`DeprecationWarning`，
**2027-10-16 删除**）：

- 它把**所有**老路径都转发过来 —— 底层控件转 ``widgets/``、顶层控件转 ``tabs/``，
  共 **44 个模块** + 包级名字，一条不断；
- 于是「哪里是兼容层」变得一眼可见：**整个 ``widget/`` 就是**（在那之前，
  ``widget/`` 下混着真控件与 26 个转发 shim，看不出边界）。

⚠️ **zmlx 内部代码一律只用 ``zmlx.ui.widgets`` / ``zmlx.ui.tabs``，不得再从 ``widget`` 导入**。
判据同 ``tabs/``：**``MainWindow`` 构建全程 0 条弃用警告**（实测为 0）。

## 0. 本目录收什么（与 `tabs/` 的分工）

⚠️ **2026-10-16 起控件分两处**，判据是**「它会不会被别的控件当组件（子控件）用」**：

| | `widgets/`（本目录） | [`../tabs/`](../tabs/AGENTS.md) |
|---|---|---|
| 收什么 | **底层控件** + **宿主非标签页的常驻控件** + **对话框组件集** | **顶层控件**：只被装配层打开成一个标签页，**不被任何控件复用**（**26 个**） |
| 判据 | 会被其它控件 `addWidget()` 进去 / 被继承 / 宿主是状态栏·侧栏·容器 / 注册成对话框里的一行 | 不被任何控件复用 |
| 例子 | `CodeEdit`、`TextBrowser`、`MarkdownView`、`MatplotWidget`、`Label`、`AttrView`、`ObjEditByText`、`editors/`（**子包**：全部编辑器都在这里）；`LicenseButton`、`VersionButton`、`RunStateLight`（状态栏运行状态灯）、`OutputWidget`、`TabWidget` | `About`、`CheckCountView`、`MemView`、`ReadMeBrowser`、`EnvEdit`……（⚠️ `TimerView` / `StyleSheetEdit` / `ImageView` / `Fn2Widget` / `PgConsole` 等已随插件搬走，全表见那边 §3） |

⚠️ **本目录不得 import `zmlx.ui.tabs.*`** —— 一旦有人这么做，就说明那个 tabs 控件**正在
被别人当组件用**，它就不再是顶层控件，**该搬回本目录**。反向是允许的：`tabs/` 可以复用
本目录的控件（如 `MemView` 用 `edit_by_text`、`MessageEdit` 用 `label`、
`ReadMeBrowser` 继承 `md_view`）。确有共用的东西时，把它**下沉**到底层模块
（现成的例子是 `../utils/lic_utils.py`），不要横向互相引用。

⚠️ **唯一例外**：本目录下那 26 个**转发 shim**（`about.py` / `img.py` / …）**确实** import
了 `tabs/`（2026-10-22 起 `img.py` 改指插件 `plugins/builtin/image_browser.py`）—— 它们是
兼容层，**不是控件**，属于预期。检查「有没有反向依赖」时要把它们
排除掉，否则会产生噪音。

⚠️ **这些转发层已弃用**（2026-10-16 起，**2027-10-16 删除**）：26 个模块级 shim、
`__init__.py` 的惰性转发、`license_count.py` / `license_feedback.py` 都会在导入时发
:class:`DeprecationWarning`。新代码请用 `from zmlx.ui.tabs import X`（无警告）。
内部代码**不得**再走老路径 —— 判据是「`MainWindow` 构建全程 0 条弃用警告」。

⚠️ **本目录不得在导入期静态 import `tabs/` 的子模块**：本目录的 `__init__.py` 为兼容
老路径转发 `tabs/` 的名字，若写成顶层 `from zmlx.ui.tabs.xxx import Xxx`，就会与
`tabs/code_history_view` / `output_history_view` / `readme_browser`（它们在**自己的顶层**
import 本目录的底层控件）两头对撞，抛 `partially initialized module`（2026-10-16 实测踩到）。
现用 **PEP 562 的模块级 `__getattr__`** 惰性转发（见 `__init__.py` 里的 `_TABS`）。

⚠️ 本文件下面的规范（骨架、命名、导入、右键菜单、线程契约、自测）**对 `tabs/` 同样有效**；
那边只补充「哪些控件归它」与上面这条依赖方向约束。

## 1. 标准骨架

```python
"""控件简述（一句话说明是什么、干什么）.

需要时写设计说明 / ⚠️ 注意事项。末行注明 Modified by <名字>, <YYYY-MM-DD>.
"""

from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets


class XxxView(QtWidgets.QWidget):
    def __init__(self, parent=None):          # 构造签名固定
        super().__init__(parent)
        self.context_actions = []             # 可选: 右键菜单扩展点

    def set_data(self, data):                 # 公开接口: set_xxx() / get_xxx()
        ...

    def _refresh_menu(self):                  # 内部实现一律以 _ 开头
        ...

    def refresh(self):                        # 可选: 见 §3「refresh() 必须快」
        """GUI 刷新钩子; 只做很轻的事."""


def test_1():                                 # 直接运行本文件时的自测
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = XxxView()
    w.resize(800, 600)
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    test_1()
```

要脱离 IDE 直接跑（`python zmlx/ui/widgets/xxx.py`），在 import 之前把仓库根加入 `sys.path`
（现成写法：`md_view.py` 顶部）。

⚠️ 这个骨架**穷举了模块级该有的东西**：import、类定义、`test_1()`、`if __name__`。此外不要有
别的模块级内容（常量、工具函数、生成器……），一律收进类里 —— 理由与写法见 §2「模块级内容」。

## 2. 硬性规范

| 项 | 要求 |
|---|---|
| Qt 导入 | **一律** `from zmlx.ui.pyqt import ...`，不写 `from PyQt6 import ...`（仅「可选依赖」可例外，如 `code_edit.py` 的 `PyQt6.Qsci`，外套 `try/except ImportError`） |
| 版本兼容 | 同时支持 PyQt6 / PyQt5；枚举写全路径（`QtCore.Qt.AspectRatioMode.KeepAspectRatio`） |
| 编码 | UTF-8 **无 BOM**；docstring 与注释用中文 |
| 文件头 | docstring 末行 `Modified by <名字>, <YYYY-MM-DD>[: 原因]`；新建写 `Created by ...` |
| 导入顺序 | stdlib → `zmlx.system` / `zmlx.ui.*` → 本目录 |
| 构造签名 | `def __init__(self, parent=None)` |
| 参数校验 | 不合法就 `raise ValueError(...)`，**不要** `assert`（`-O` 会剥掉） |
| 导入期副作用 | 模块 import 时不做重活 / 联网 / 弹窗（`__init__.py` 会提前导入） |
| 模块级内容 | **只有 import / 类定义 / `test_1()` / `if __name__`**：常量、工具函数、生成器一律收进类里（见「模块级内容」） |
| 公共 API | 只增不改：新参数必须有默认值，不删不改签名 |

### 模块级内容

模块级**只留** import、类定义、`test_1()` 和 `if __name__ == '__main__'`（外加直接运行本文件
要用的 `sys.path` 引导）。常量、颜色/文本工具、QSS 之类的生成器，全部收进类里；没有实例的
就用一个私有类当「命名空间」：

```python
class _Qss:                              # 不实例化，纯粹当命名空间用
    DEFAULT_OPTIONS = {...}              # 常量 → 类属性
    PRESETS = {...}

    @staticmethod
    def color(value): ...                # 工具函数 → static/classmethod

    @classmethod
    def build(cls, options=None): ...    # 生成器 → classmethod
```

为什么值得这么挪：

- **一眼看得出本文件提供什么**：`vars(module)` 里只剩几个类名，不用先扫一遍「这些全局名是哪来的」。
  多出来的命名空间类还可以按主题拆（`_Qss` / `_ColorButton` / `_StyleTextEdit`），比平铺的模块级
  函数更容易定位。
- **全局常量会被别的模块 import 走**，之后就再也改不动了；`_Qss.DEFAULT_OPTIONS` 至少带着归属。
- 外观 / 生成规则这类「只被本控件用」的东西，本来就不该出现在模块的公共命名空间里。

范例：`style_sheet_menu.py`（整个模块级 = import + 4 个类 + `test_1` + 主入口）。

### 命名

文件 `snake_case.py`（与类名对应：`text_file_edit.py` → `TextFileEdit`）；类 `PascalCase`
（`XxxView` / `XxxEdit` / `XxxWidget`）；公开方法 `set_xxx()` 设值 / `get_xxx()` 取值 / `xxx()`
做事；私有成员单下划线 `_xxx`（只有不给子类用的才双下划线）。

### 注册

⚠️ **默认不在 `__init__.py` 里转发**（2026-10-16 起）—— 新控件用**子模块路径**导入即可：

```python
from zmlx.ui.widgets.my_view import MyView     # ✅ 新控件一律这样用
```

完整规则（为什么、什么时候才该转发）见 [`../AGENTS.md`](../AGENTS.md) §1–§2。
本目录 `__init__.py` 里现有的转发是「不断老路径」的**兼容层**，**不要**再往里加名字。
**用户说「不要修改任何现有代码」时更不要动 `__init__.py`**，在 docstring 里写清导入路径。

## 3. 控件里最容易踩的坑

### `refresh()` 必须快

`MainWindow` 把 `top_tabs.currentChanged` 接到当前页的 `refresh()`（菜单「显示 → 刷新」走同一条
路径），**每次切到该标签页都会调**。所以里面不能读磁盘、联网、整张重画。真踩过两处
（`demo_view.py` 同步扫上百个 demo 文件 ~150 ms、`gui_iter_edit.py` 重画 matplotlib ~63 ms），
均已改掉 —— 详见 `zmlx/ui/ReadMe.md`。

⚠️ 顺带一条：`MainWindow.refresh()` 只刷新 **`get_current_widget()`（顶部栏的当前页）**。
所以**开在右侧栏**的控件（`position="right"`）**永远等不到这条链** —— 切标签、菜单「显示 →
刷新」都不会调到它的 `refresh()`。这类控件要自己找时机刷新，两种做法：

- **只求「切回本页时是最新的」** → `showEvent` 里 `refresh()` 一次（成本一次遍历）；
- **内容会被别处随时改掉**（清单类：已开标签、运行中的任务……）→ 再加一个**每秒定时器**，
  并且**只在可见时跑**：`showEvent` 起、`hideEvent` 停。别指望接数据源的信号 ——
  那要把「新开 / 关闭 / 重命名 / 换位置」全都接上，还容易漏。

```python
def showEvent(self, event):
    super().showEvent(event)
    self.refresh()
    self._timer.start()          # 计时器 parent=self，随控件一起销毁

def hideEvent(self, event):
    self._timer.stop()           # 切走后还刷就是白烧 CPU
    super().hideEvent(event)
```

⚠️ 计时器**要设 parent 为本控件**（与后台线程的规矩**相反**）：`QTimer` 是 Qt 对象，
随控件销毁是安全的；而后台线程 parent 指向控件会在关标签时把进程带崩（见「慢活放线程」那节）。

范例：`tab_detail_view.py`（`REFRESH_INTERVAL_MS = 1000`）—— 它的列表曾停在打开那一刻的内容
（真踩过）。

### 只读表格必须关掉编辑触发器（否则 WSL 下会段错误）

`QTableWidgetItem` **默认带 `ItemIsEditable`**，而 `QAbstractItemView` 的默认编辑触发器是
`DoubleClicked|EditKeyPressed|AnyKeyPressed` —— 于是**双击任一单元格都会弹出就地编辑器**。
这在 WSLg 下会直接崩：**编辑器还开着时再双击另一个单元格，Qt 在 C++ 层段错误**
（不是异常，`try/except` 兜不住，用户看到的是「整个软件卡死」）。Windows 走另一条平台路径，
不暴露这个问题 —— 所以**只在 WSL 上测才会发现**。

凡是「只读信息展示」的表格，两层都要做（互为双保险）：

```python
self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)  # 总闸

@staticmethod
def _make_item(text):                       # 逐项清标志
    item = QtWidgets.QTableWidgetItem(text)
    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
    return item
```

⚠️ 只去掉 `ItemIsEditable`，**保留** `ItemIsSelectable` / `ItemIsEnabled` 等其它标志
（用户还要能选中、复制）。⚠️ `QListWidget` 若像 `setup_file_edit.py` 那样用 `setFlags()`
**从零构造**标志（不含 `ItemIsEditable`），则本身就安全。

真踩过两处：`tabs/about.py`（「关于」页）与 `tab_detail_view.py`（标签列表 —— 它本来双击就该
「切标签」，双击反而弹编辑器，交互本身就是错的）。范例见这两个文件。

### 慢活放线程 + 线程生命周期契约

慢操作用 `QtCore.QThread` 子类，结果经信号回主线程再更新界面（范例：`demo_view.py` 的
`DemoScanThread`、`tabs/about.py` 的 `AboutThread`）。**不要**用 `terminate()` 强杀线程。

⚠️ **崩溃防线只有下面两条**（缺了就会在关标签页时 abort：`QThread: Destroyed while
thread is still running` / 退出码 `0xC0000409`，**不是异常**，`try/except` 兜不住）：

1. **线程不设 parent** —— 写 `FooThread()`，不写 `FooThread(self)`。标签页关闭走
   `TabWidget.close_tab()` → `deleteLater()`，会**连同子对象**一起删除控件；parent 指向控件的
   线程会被连带析构，而联网请求最长 60 秒，关标签时几乎必然还在跑。
2. **用模块级强引用列表持有它**，跑完 `finished` → 摘表 → `deleteLater`
   （现成写法：`demo_view.py` 的 `_RUNNING`、`tabs/about.py` 的 `_keep_alive()`）。

`demo_view.py` 只有这两条且从不崩 —— 这就是「两条足够」的证据。

### 销毁前的两次清理

`TabWidget.close_tab()` 在 `deleteLater()` 之前给控件**两次清理机会**（都是 duck-typing 探测，
按需实现，**都不许阻塞**）：

| 钩子 | 管什么 | 还有谁会调 |
|---|---|---|
| `save_file()`（配 `need_save()` 闸门） | **持久化数据** | 菜单「文件 → 保存」也调它 |
| `cleanup_before_tab_close()` | **其余收尾**：放掉线程引用、复位 `_busy`、取消定时器等 | **只有**关标签页 |

⚠️ 后者的名字里带 `tab_close` 是**有意的**：它**只在控件作为标签页被关闭时**才调 —— 同一个控件
用在别处（对话框、普通子控件）**不会被调**，那些场合要自己收尾。

⚠️ 两个钩子里都别 `wait()`（同步等 60 秒 = 冻结界面）。`cleanup_before_tab_close` **不是**
崩溃防线：实测把它改成空操作后关标签依然安全，而把线程 parent 回控件时**即使有它也照样崩** ——
线程存活靠上面那两条纪律。

⚠️ **`closeEvent` 在这条路径上是死代码**：`deleteLater()` **不发** `closeEvent`（那是 `close()`
才发的）。写 `closeEvent` + `wait(3000)` 挡不住关标签时的崩溃 —— 它只覆盖「控件被单独 `close()`」
（例如直接跑 `test_1()`）那条路径。

⚠️ **lambda 连的槽不会被 Qt 自动断连**（lambda 没有接收者 QObject）：控件销毁后迟到结果仍会调到
它，碰子控件即抛 `RuntimeError: wrapped C/C++ object ... has been deleted`。这类槽开头先判
`_is_deleted(self)`（实现见 `tabs/check_count_view.py`）；写成**绑定方法**则 Qt 会自动断连，更好。

### 跨线程调用 GUI

**后台线程里永远不要直接碰 Qt 控件**。按用途选通道：

| 想要 | 用什么 |
|---|---|
| 改界面（有对应的导出函数） | `gui.xxx(...)`（同步、阻塞等结果） |
| 改界面（**没有**对应导出函数） | `gui.call(widget.setEnabled, False)` / `gui.call(lambda: ...)` |
| 只是稍后在 GUI 线程跑一下 | `gui.add_task(func)`（异步、无结果） |
| 长任务 | `gui.start(func, post_task=...)`（**单任务**，忙时会被丢弃） |

⚠️ 完整规则（单任务约束、`post_task` 在异常时也会执行、死锁禁忌、20 个通道的上限、
排查表）见 [`../AGENTS.md`](../AGENTS.md) §6 —— 那里是**唯一**的权威描述，本节只是入口。

### 要主窗口的能力：**转接 Qt 现成的接口**，别往 `MainWindow` 加方法

`MainWindow.__init_gui_api` 会把它的**公开方法自动**注册进 GUI API，所以「为了控件往
`MainWindow` 加一个方法」= 往全局命令表里多加一个名字。当控件要的只是「窗口本来就有的能力」
时，正确做法是在 `__init_gui_api` 里**转接 Qt 自己的方法**（一行，不包一层）：

```python
self.gui_api.add_func("resize", self.resize)                    # 本来就长这样
self.gui_api.add_func("set_style_sheet", self.setStyleSheet)    # 照这个写
self.gui_api.add_func("get_style_sheet", self.styleSheet)
```

- 控件侧照常 `gui.set_style_sheet(text)` / `gui.get_style_sheet()`（GUI 线程当场派发、非 GUI
  线程排队，见上一节）；
- **落盘、参数记忆、校验、默认值全部留在控件里** —— 控件才是「这份数据该存到哪个文件」的唯一
  知情人（`zml_window_style.qss` 由「设置 → 样式表」控件读写，`MainWindow` 完全不碰）；
- 真需要「显示一个控件」时才加 `show_xxx`（菜单项指向它、`gui_restore` 也用它），这是唯一值得
  往 `MainWindow` 里加的方法。

⚠️ 反面教材（改过一版）：给样式表在 `MainWindow` 里加了带 `save=` 参数的包装方法 —— 一旦包装，
「存哪里 / 存不存」这类业务规则就跑到主窗口里去了，而主窗口本来只该负责菜单和标签页。

### `gui.*` 在无头模式自动 no-op

`gui.status()` / `information()` / `question()` / `progress()` / `break_point()` 在 `--no-gui`
下都是空操作，控件里可放心调用，不必判 `gui.exists()`。但 `gui.execute()` **只能出现在 demo 的
`if __name__ == '__main__'` 里**，控件内部一律不许调。

### 右键菜单：`context_actions` + `create_action`

```python
from zmlx.ui.alg import create_action
self.context_actions = [create_action(self, '清除内容', icon='clean', slot=self.clear)]
```

- 宿主控件通常实现 `contextMenuEvent()`，在 `super().createStandardContextMenu()`（或自己的菜单）
  之后把 `context_actions` 逐项加入；元素可以是 `QAction`，也可以是 `None` / 分隔符占位。
  现成写法：`text_browser.py`、`tab_widget.py`、`editors/` 子包、`plt.py`。
- `create_action(parent, text, *, icon=None, slot=None)` 会**包装**你的 slot：调用后写
  `app_data.log('run <text>')` 并 `gui.refresh()`，所以 slot 里不用自己记日志。
- 可勾选项：`action.setCheckable(True)` + 在 slot 里读 `action.isChecked()`；勾选状态要落到
  `app_data` 才能跨进程保留（范例：`md_view.py` 的渲染方式开关）。

### 「置灰」等于「这里不能改」——别用开关当闸门

控件之间的联动最容易做成「勾了 A 才能用 B」，然后把 B `setEnabled(False)`。用户看到的是**一个
坏掉的控件**，而不是「先去勾 A」：作者以为的暗示，用户完全收不到 —— 本目录第一版给字体加了
「☑ 修改字体」闸门，收到的第一条反馈就是「字体、字号无法修改，是灰色的」。

要表达「这一项没设置」，把状态做进控件**本身**：

| 想表达 | 做法 |
|---|---|
| 这一项不设置（跟随系统） | 下拉框里加一项「跟随系统」（用 `QComboBox`；`QFontComboBox` 的列表就是字体库，塞不进额外项） |
| 数值项不设置 | `QSpinBox.setSpecialValueText('默认')`，最小值当哨兵（`-1` / `0`） |
| 颜色不设置 | 按钮显示「默认」+ 空心图标（❌ 不要靠置灰） |

只有**整块都不参与**时才 `setEnabled(False)`（例：模式切到「自定义文本」后，参数区整体不参与
生成），并且要在界面上写明原因（顶部那句说明）。范例：`style_sheet_menu.py` 的 `_update_enabled`。

⚠️ 还有一种同源毛病：**载入状态与界面不一致**（参数写着「护眼绿」、文本框却空着），用户点
「应用」还以为没生效。载入时就要让两者自洽（见 §3「落盘状态有两份时」）。

### 可选第三方依赖：不能让控件整体挂掉

控件**必须**在没有该依赖时仍然可用。两种写法：

1. **延迟导入 + 设置开关 + 告警一次 + 回退**（推荐；范例 `md_view.py`）：不在模块顶层 import；
   用 `importlib.util.find_spec('xxx')` 判断是否装了（不触发导入），据此决定是否显示相关菜单项；
   真要用时才 `import xxx`；拿不到就 `print` 一次可操作的提醒，再走回退实现。
2. **顶层 `try/except ImportError` + 整套回退**（范例 `code_edit.py`：没有 QsciScintilla 时退化成
   `QTextEdit`；`solver_selector.py`、`system_state_label.py`、`_parallel.py` 同理）。

⚠️ 不要静默回退：能力和效果变差了，至少要 `print` 一句，并告诉用户怎么补装（`pip install xxx`）。

### `app_data` 的两套存储，别混用

| 用哪一对 | 存在哪 | 重启后还在吗 |
|---|---|---|
| `setenv` / `getenv` | 磁盘 `env/<key>` | **在**（要跨进程保留就用这对） |
| `put` / `get` | 内存 | 不在（只传本次运行的临时状态） |

⚠️ `getenv` **先查 `os.environ`**，所以键名必须独特（`use_xxx` / `xxx_by_yyy` 这种），用
`path`、`emails` 之类通用名会被外部环境变量静默掩盖；`setenv` 的 value **只能是 `str`**
（列表 / 数字自己 `json.dumps`）。现成写法：`_parallel.py` 的 `_parallel_enabled(value=None)`。

### `settings.save/load`：含非 ASCII 的键**必须**显式 `encoding='utf-8'`

`zmlx.ui.settings.save/load` 是控件存自己那份配置的标准做法（落到 app_data 的 temp 目录）。
⚠️ `load` 最终走 `read_text(path, encoding=None)` → 用**系统编码**解码（中文 Windows 上是 GBK）：
文件是 UTF-8 写的，里面只要有中文（注释、标签都算），就会抛 `UnicodeDecodeError`，而 `read_text`
会**吞掉异常返回 `default`** —— 现场看起来就是「明明存了却读不到 / 没落盘」。

- 存与取都写全：`settings.save(key=..., value=..., encoding='utf-8')` /
  `settings.load(key=..., encoding='utf-8')`（没写 encoding 的地方只有读纯 ASCII 才碰巧没事）；
- ⚠️ `write_text` 在 Windows 上把 `\n` 翻成 `\r\n`，所以**文件字节数 ≠ 内存字符数**：别拿
  `os.path.getsize` 判断「内容是不是刚存的那份」，要断言就断言**读回来的字符串**；
- 排查「读不到」时先 `print(repr(settings.load(...)))`：拿到 `None` 说明解码 / 文件失败，拿到
  空串说明文件真的是空的 —— 两者病因完全不同。

### 落盘状态有两份时，要给出「谁说了算」的判据

控件常要同时存两种东西：**界面参数**（下拉框选了什么）和**产物**（生成出来的文本）。两者都可能
被外部改掉（用户手改文件、脚本直接调 GUI API），所以载入时必须有**明确、可解释**的判定规则，
并且**绝不静默覆盖用户的东西**：

- 判据：「产物 == 由参数生成的结果」→ 参数模式（滑块和界面状态对得上）；对不上 → 文本模式
  （用户 / 外部写的内容原样保留）；
- 界面上从文本模式切回参数模式会覆盖文本时，**先弹一句确认**；
- **产物为空**（没在用自定义配置）时，参数也回到默认 —— 否则会留下「参数写着护眼绿、文本框却
  空着」这种自相矛盾的状态，用户点「应用」还以为没生效（实际是把空配置又应用了一遍）。

范例：`style_sheet_menu.py`（`zml_window_style.qss` = 产物，`zml_style_options.json` = 参数）。

### 只在一种 PyQt 下能跑的 API：两种绑定都要写

`zmlx.ui.pyqt` 统一了导入与大多数枚举，但**函数形态**仍有差异，得两边都写。踩过的例子：

```python
try:
    families = QtGui.QFontDatabase.families()      # PyQt6：静态方法
except Exception:
    families = QtGui.QFontDatabase().families()    # PyQt5：成员函数，得先建实例
```

写这类兼容分支时要说清**哪种绑定走哪条**（照上面的注释写），否则下一个人不知道该删哪一条。

### 控件里的颜色：用图标 / 调色板，别在控件里写 `color` / `background`

本程序会加载用户可编辑的 `zml_window_style.qss`，还有暗色模式；控件里一旦写死色值，要么在暗色
下看不清，要么把用户主题盖掉（`system_state_label.py` / `tabs/license_register.py` / `tabs/check_count_view.py`
的模块文档里各记了一遍）。**要在控件里显示一个颜色**（例如取色按钮的色块），用 `QIcon` 画：

```python
pixmap = QtGui.QPixmap(14, 14)
pixmap.fill(color)
self.setIcon(QtGui.QIcon(pixmap))                     # ✅ 不受样式表 / 主题影响
# self.setStyleSheet(f'background-color: {color}')    # ❌ 和用户主题打架
```

范例：`style_sheet_menu.py` 的 `_ColorButton`（色块 + 十六进制文本，「未设置」时显示「默认」）。

### Qt 自带渲染 vs 第三方渲染（以 Markdown 为例）

`md_view.py` 实测 Qt 自带路径的缺陷：`QTextDocument.setMarkdown()` 不认
`document().setDefaultStyleSheet()`（自定义 CSS 全失效）、不给标题建命名锚点
（`scrollToAnchor` 失效）、遇到**未自闭合的空元素**（如 `<img src=x>`）会把其后**整篇文档**
当成 HTML 块吞掉（写成 `<img src=x />` 才正常）。`markdown` 库 → `setHtml()` 三者都能解决，
但多一个依赖。

结论：**默认优先第三方库**，把选择权做成「设置键 + 右键菜单勾选项」，并且**两条路都要显式测过**
（`md_view.py` 的 `_close_void_tags` 就是为 Qt 路径打的补丁）。要显示 md 时不要自己
`setMarkdown`，直接继承 / 使用 `MarkdownView`（`readme_browser.py` 就这样缩成了几行）。

## 4. 自测与验收

1. **能直接跑**：`python zmlx/ui/widgets/xxx.py`，`test_1()` 造出的示例数据要能看出控件的主要能力
   （空白界面等于没测）。⚠️ 只造**示例数据**：不要落盘、不要改用户配置 —— `test_1()` 里调
   `apply(save=True)` 这类「顺手演示一下」，会让用户下次启动时的界面外观莫名变掉。
2. **独立解释器**：本仓库不在 site-packages 里，直接跑需仓库根在 `sys.path`（见 §1），
   或用 `python -m zmlx.ui.widgets.xxx`。
3. **无头环境**：设 `QT_QPA_PLATFORM=offscreen`，断言**文档 / 数据结构**而不是像素 ——
   走 `QTextDocument`（数 `frag.isImageFormat()` / `isAnchor()` / `fontStrikeOut()`，读
   `document().toPlainText()`、`rootFrame().childFrames()` 里的 `QTextTable`），或走控件 API
   （`QTest.mouseClick(view.viewport(), ...)` 真实点击 + 用信号 / 回调记录验证）。
   ⚠️ offscreen 下字体库可能缺失、文字渲染成方块，结构断言不受影响；要**看图**得用真实平台
   （Windows 上可用 `PrintWindow` + `PIL.ImageGrab`）。
4. **别把验证脚本留在仓库里**：临时脚本放系统临时目录；仓库里只保留正式的 demo / 测试。
5. 提交按 `projects/zml/AGENTS.md` 的「1. 提交」走（更新 `zmlx/data/CHANGELOG.md` ——
   这是**唯一**的 CHANGELOG，仓库根目录那份已删除；必要时更新 `zmlx/ui/ReadMe.md` 的控件
   列表）。**永远不要 `git push`。**

## 5. 参考实现

| 想学什么 | 看哪个文件 |
|---|---|
| 最小控件 + 缩放/交互 | `../plugins/builtin/image_browser.py`（`ImageView`，QGraphicsView；2026-10-22 由 `tabs/img.py` 并入「图片浏览」插件） |
| 上下文菜单 + 状态栏提示 + 导出 | `text_browser.py`（本目录多数控件的基类） |
| 可选依赖 + 整套回退 | `code_edit.py`（QsciScintilla → QTextEdit） |
| 后台线程 + 信号回主线程 | `demo_view.py`（`DemoScanThread`）、`tabs/about.py`（`AboutThread`） |
| 原生 `QPainter` 绘图（简单展示图别用 matplotlib） | `gui_iter_edit.py`、`tabs/check_count_view.py` |
| `app_data` 开关 + 复选框 | `_parallel.py`、`env_edit.py` |
| Markdown / 可选库 / 设置键 / 右键勾选项 | `md_view.py` |
| 模块级「干净」的样板（常量与生成器装进私有命名空间类） | `style_sheet_menu.py`（`_Qss`） |
| 参数 + 产物双模式的落盘判据 / 取色按钮（图标画色块） / 转接 gui API 而不动 `MainWindow` | `style_sheet_menu.py`（`StyleSheetEdit`、`_ColorButton`） |
| 按链接文字就地处理（不开浏览器） | `readme_browser.py`（微信 → 本地二维码、注册 → `gui.show_reg_tool()`、`zmlx/demos` → `gui.show_demo()`） |
