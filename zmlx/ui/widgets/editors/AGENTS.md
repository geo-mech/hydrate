# AGENTS.md

**`zmlx/ui/widgets/editors/`** 的操作规范：**加 / 改一个编辑器时按此做**。

上承 [`../AGENTS.md`](../AGENTS.md)（`widgets/` 总规范 —— 标准骨架、命名、线程契约、右键菜单、
自测**全部继续适用**，本文只写本子包多出来的部分）；冲突时以本文为准。

⚠️ 本文**不列控件清单**（那是 [`../../ReadMe.md`](../../ReadMe.md) §`editors/` 那一行的唯一职责），
也**不重复**公共 API（那是 [`__init__.py`](__init__.py) docstring 的职责）。分工见 §5。

## 0. 判据：什么算「编辑器」

⚠️ **不是「类名以 `Edit` 结尾」，也不是「继承某个基类」** —— 是**成对实现两个方法**：

| 方法 | 语义 |
|---|---|
| `set_data(data)` | 把数据推上控件显示 |
| `get_data()` | 取回编辑后的数据 |

即「**给数据 → 用户编辑 → 取回**」，再加一个可选的 `sig_changed` 信号。这条判据的原文在
[`../float_edit.py`](../float_edit.py) 的弃用说明里 —— 它当初就是用来论证「`Slider` / `Dial`
为什么算编辑器、为什么该搬进来」的。

⚠️ **协议只规定方法名，不规定签名与返回类型** —— 因为 `reg_file_type` 用 `hasattr` 探测、
`edit_in_tab` 直接调方法。于是 `get_data()` 返回**数据本身还是模型引用**取决于它的**形态**
（见 §1，只有两种），读代码时不要假设它返回什么。

⚠️ **归属**：实现该协议的控件一律放本子包；[`../`](../) 根目录只放**纯控件**
（`CodeEdit` / `TextBrowser` / `MatplotWidget` / `Label` …）。2026-10-21 把
`Slider` / `Dial` 与 Seepage 那批搬进来，就是为了把这条边界做实。

⚠️ **2026-10-22 有一次「搬出去又搬回来」**：渗流相关的两个模块（`seepage_edit.py` 的
7 个 Seepage 编辑器 + `field_edit.py` 的 3 个字段行）一度被搬进插件包
`zmlx/scen/editors/`（「只有那个插件在用」），同一天又**搬回本子包** —— 判据错了：
**「只有插件在用」不代表它是插件的东西**，它们是纯控件（`field_edit` 连 `zmlx.exts`
都不 import），而「包自己就是一个插件」的形态应该只装装配代码。现在：控件在本子包，
**装配**（`gui.reg_file_type` 那 7 条 + 「帮助 → 其它 → 生成测试数据」6 条）在
[`../../plugins/builtin/editors.py`](../../plugins/builtin/editors.py) 一个文件里。
下文凡提 `seepage_edit` / `field_edit` 的地方，指的就是**本子包**里的那两个模块。

⚠️ **已知遗留例外**：`../edit_by_text.py` 的 `ObjEditByText` 同样成对实现了
`set_data` / `get_data` + `sig_changed`，却仍留在 `widgets/` 根目录
（`../AGENTS.md` §0 的例子表也把它列在那儿）。按判据它**该搬进来** —— 尚未搬，
动手前先搜外部引用。

## 1. 两种形态 + 一种结构：先决定「数据存在谁身上」

⚠️ **判据只有一条**：`get_data()` 返回的是**数据本身**，还是**被编辑的模型**？

这是**语义**上的划分，只有**两种**；「有没有子编辑器」是另一个维度（**结构**），与语义**正交**。
2026-10-22 修正：原先把「组合容器」列为第三种形态是**错的** —— 实测容器
`set_data(m)` 后 `get_data() is m`（返回模型引用），与绑定字段型**完全一致**，它只是把同一个
模型转给子控件、再原样还回来，**从不聚合子控件的值**。

### 1.1 两种语义（`get_data()` 的返回）

| 形态 | 数据在谁身上 | `set_data` 收什么 | `get_data()` 返回 | 什么时候拿得到新值 | 代表 |
|---|---|---|---|---|---|
| **自持值** | 控件自己 | 数据本身 | **数据本身**（`ndarray` / `float` / `str` …） | **只有**调 `get_data()` | `TextEdit`、`ArrayTextEdit`、`ArrayEdit`、`Slider`、`Dial`、`XyEdit`、`XyzEdit` |
| **引用模型** | 被编辑的模型 | **模型对象** | **模型引用**（`is` 传入的那个） | 用户一改就写回模型了，`get_data()` 只是把模型还回去 | `TextFieldEdit`、`IntFieldEdit`、`FloatFieldEdit`、`FludefEdit`、`SeepageFormEdit`、`SeepageTabEdit`、`SeepageSummary`、`SeepageKrEdit`、`SeepageEdit` |

⚠️ **不可互换使用**：自持值型必须调 `get_data()` 才拿得到用户的新输入；引用模型型的
`get_data()` 几乎总是返回**同一个对象**，别指望它体现「改了什么」。

⚠️ **边界情况：`Interp1Edit` / `Interp2Edit`** 返回 `Interp1` / `Interp2`。按「返回的是
数据对象、值不会自动写回别处」算**自持值**；但它返回的是一个**可变的模型对象**，所以看起来
像引用模型。判定时看**归属**：`Interp1Edit` 自己 `new` 了一个 `Interp1` 并持有它
（`self.data`），没人从外面灌进来、也没人从它写回别处 ⇒ 自持值。

### 1.2 一种结构（有没有子编辑器）

结构与语义**正交**，不要拿它当第三种形态：

| 结构 | 判据 | 例子 |
|---|---|---|
| **叶子** | 值由自己的一组 Qt 控件承载 | `TextEdit`、`ArrayEdit`、`Slider`、`TextFieldEdit` |
| **复合 / 容器** | 把数据**转发**给一组子编辑器，再把子控件的 `sig_changed` 汇上来 | `XyEdit`（内含 `ArrayEdit` + `MatplotWidget`）、`SeepageKrEdit`、`SeepageFormEdit`、`SeepageTabEdit`、`SeepageSummary`、`SeepageEdit` |

⚠️ **复合结构落在哪一型，由它 `get_data()` 返回什么决定**，与「它有没有子控件」无关：

- `XyEdit` 是复合结构（内部两个子控件），但返回 `ndarray` ⇒ **自持值型**；
- `SeepageFormEdit` 也是复合结构，但返回 `Seepage` ⇒ **引用模型型**。

**容器的两个实现要点**：

```python
def set_data(self, data):
    self.data = data
    for edit in self.editors:
        edit.set_data(self.data)      # 向下转发同一个对象

def get_data(self):
    return self.data                  # 原样返回，不读子控件
```

⚠️ 转发子信号时要**先探测**：`if hasattr(widget, 'sig_changed')` —— 容器不要求子控件一定是
编辑器（`SeepageFormEdit` 的某些行就是纯只读显示）。

⚠️ **容器的 `self.data` 只是「转手」，不是「持有」**：它不参与 `get_data()` 的结果计算。
这也是它属于**引用模型型**而非自持值型的实证 —— 真正的数据在模型对象上。

### 1.3 写新编辑器时怎么用这三条

先问两句话，答案直接决定代码：

1. **「值存在哪？」** → 自己存 ⇒ 自持值；模型上 ⇒ 引用模型。（语义）
2. **「要不要一组子编辑器？」** → 要 ⇒ 写成容器，照 1.2 的两个实现要点。（结构）

⚠️ 与语义无关的一条：`sig_changed` 只表示「**用户改了这个控件的值**」，`set_data()` **不发**
（见 §4.0 / §4.1a）。容器把子信号转上来，所以一次深层编辑，容器**只发一次**。

### 1.4 新建引用模型编辑器：**先用 `ObjectEdit` 包，别从头手写**（2026-10-22 新增）

引用模型型 = **自持值编辑器 + 一层 `get_value` / `set_value` 中转**。这层中转是通用的，
所以**大多数情况下不需要新写类**：

```python
from zmlx.ui.widgets.editors import IntSpin, ObjectEdit

edit = ObjectEdit(IntSpin(),                       # 内层：任何**自持值编辑器**
                  get_value=lambda m: m.n,         # 模型 → 值
                  set_value=lambda m, v: setattr(m, 'n', v))   # 值 → 模型（不给则只读）
edit.set_data(model)      # 内部：inner.set_data(get_value(model))，不写回、不发信号
edit.get_data()           # 返回 model 本身（引用模型型）
```

| 想要 | 用 |
|---|---|
| 单行文本字段 | `ObjectEdit(TextInput(), ...)` |
| 整数字段 | `ObjectEdit(IntSpin(), ...)` |
| 浮点数字段 | `ObjectEdit(FloatSpin(), ...)` |
| 编辑某个 `ndarray` 字段 | `ObjectEdit(ArrayEdit(), ...)` |
| 编辑某个曲线字段 | `ObjectEdit(Interp1Edit(), ...)` |

⚠️ **内层必须是「编辑器」，不能是裸 Qt 控件**：`QSpinBox` / `QLineEdit` 没有
`set_data` / `get_data`，直接传会抛 `ValueError`（带明确提示）。缺少的类型就补一个
**自持值叶子**（照 `object_edit.py` 里 `IntSpin` 的写法，约 10 行）—— 这正是本节的要点：
**新类型只写叶子，不写字段行**。

⚠️ **`TextInput`（单行 `QLineEdit`）≠ `TextEdit`（多行 `QTextEdit`）** —— 名字相近，
用途不同，别混用。

⚠️ **现有三个手写字段行 `TextFieldEdit` / `IntFieldEdit` / `FloatFieldEdit` 暂未迁移**：
它们是 `QTextEdit` / `QSpinBox` / `QDoubleSpinBox` 的**子类**，外部可能 `isinstance` 或直接
调 `setRange()`；改成组合会破坏这些用法。要迁移时**保留类名与构造签名**、内部换成组合即可。

## 2. 加一个新编辑器

1. **新建 `xxx_edit.py`**，文件名与主类一一对应。本子包 2026-10-21 起按此拆分
   （`text_edit` / `array_edit` / `data_edit` / `interp_edit` / `float_edit` /
   `field_edit` / `seepage_edit`），**不要**往已有文件里塞第二个新编辑器。
2. 按 §1 定**形态**（语义：自持值 / 引用模型）与**结构**（叶子 / 容器），实现
   `set_data` / `get_data`，需要通知外界时加 `sig_changed = QtCore.pyqtSignal()`。
   ⚠️ 这两件事是**分开的**：先看 `get_data()` 该返回什么（决定语义），再看要不要一组子编辑器
   （决定结构）。别把「容器」当成第三种语义。
3. **要不要注册文件类型？**
   - **要** → 在 [`../../plugins/builtin/editors.py`](../../plugins/builtin/editors.py) 的
     `setup_file_types()` 里**加一条表项**（`dict(desc=..., exts=..., name=..., init=..., widget_type=本类)`）；
   - **不要** → 什么都不用加（`Slider` / `Dial` 就是这样：它们从不注册文件类型）。

   ⚠️ **本子包只定义控件，不挂界面**（2026-10-22 起）：
   - 类上**没有** `setup_ui`（原来 `ArrayEdit.setup_ui()` 这类静态方法各自注册，7 个类 7 份、
     调用方要逐个拼）；
   - 子包里**没有** `setup_ui.py`（那是 2026-10-22 之前的形态）；
   - **不要再往回加**：`reg_file_type` 会往主窗口挂东西，属于导入期副作用。装配一律走
     **插件** [`plugins/builtin/editors.py`](../../plugins/builtin/editors.py)，
     子包导入必须保持轻量。

   ⚠️ 那个插件的**函数体**才是注册发生的地方；它的**模块顶层什么都不做** ——
   「导入即注册」会让只 `import` 它的人意外触发注册。⚠️ 注册由该文件自己的
   `__name__ == '__zml_plugin__'` 分支调用，**不在** `setups` 里。
4. **在 [`__init__.py`](__init__.py) 补两处**：import 区 + `__all__`（若新增了公开类）。
   ⚠️ 本包是**显式转发**，不做 `import *` 兜底 —— 漏一处，老路径
   `from zmlx.ui.widgets.editors import X` 就断。
5. **更新 [`../../ReadMe.md`](../../ReadMe.md) 里 `editors/` 那一行**（约第 151 行，唯一清单）。
6. 若有外部复用，改动前先搜：`plugins/builtin/editors.py` 是**唯一**的装配包装方
   （2026-10-22 起 `plugins/builtin/editors_menu.py` / `seepage_menu.py`、
   `ui/setups/editors.py` 与 `zmlx/scen/editors/` 都已删除）。

## 3. 本子包特有的硬性规范

（其余见 [`../AGENTS.md`](../AGENTS.md) §2）

| 项 | 要求 |
|---|---|
| Qt 导入 | 一律 `from zmlx.ui.pyqt import ...`，不写 `from PyQt6 import ...` |
| 构造签名 | `def __init__(self, parent=None)`；需要更多参数时全部 **keyword-only**（`*,`） |
| 信号 | `sig_changed = QtCore.pyqtSignal()` 的语义是「**用户改了值**」（不是「值变了」、也不是「编辑完成」）：用户改 → 发；`set_data()` → **不发**。详见 §4.0 / §4.1 / §4.1a |
| 依赖方向 | 可用 [`../plt.py`](../plt.py) 的 `MatplotWidget`；**不得** import `zmlx.ui.tabs.*`；**不得** import `zmlx.ui.setups.*`（装配在上层）；**不得**被 `widgets/` 根目录反向依赖 |
| 模块级内容 | 只有 import / 类 / `test_xxx()` / `if __name__`；常量与工具函数收进类里 |
| 文件头 | docstring 末行 `Modified by <名字>, <YYYY-MM-DD>[: 原因]`；新建写 `Created by ...` |

## 4. 已经踩过的坑

### 4.0 `sig_changed` 到底**干什么用**（2026-10-22 补写 —— 这是本子包最容易误解的一处）

**一句话**：`sig_changed` 回答的是「**用户刚刚改了值**」，不是「值变了」，也不是「编辑完了」。
判据是**谁改的**：

| 触发方 | 发不发 | 本子包内的例子 |
|---|---|---|
| **用户经界面改** | ✅ **发** | 敲键盘、拖 `Slider` / 拨 `Dial`、右键「应用」/「转化为均匀间隔」、按钮增删行 |
| **代码调 `set_data()`** | ❌ **不发** | 打开文件、刷新、构造时初始化、容器向下转发数据 |

**它不是给本子包自己用的**（2026-10-22 全仓审计结论）：

- `editors/` 内部**只有转发、没有消费** —— 唯一的连接是容器把子控件的信号汇到自己的
  `sig_changed`（`SeepageFormEdit` / `SeepageTabEdit` 的 `if hasattr(widget, 'sig_changed')`）；
- 全仓**没有任何**地方 `connect` 本子包的 `sig_changed` 去做业务；外部工作区
  （`igg-hydrate-works`）对它也零引用；
- ⇒ 它是**为外部使用者准备的扩展点**。典型用途只有四种：**预览重绘、把值写回模型、
  置脏标记、联动其它控件**。

⚠️ **唯一的「内部消费」是 `field_edit` 的写回**：三个字段行的 `on_changed` 在 emit 之前
先 `set_value(model, v)`。所以「多发一次」不是多发一次通知，而是**多写一次模型** —— 这正是
§4.1a 那条约定存在的原因。

**计数保证**：一次深层子编辑，容器**只发一次**（实测：`SeepageEdit` → `Summary` → 字段行，
3 层转发仍是 1 次）。不要指望它「每层发一次」去做层级区分。

⚠️ **加了新消费者时**：先读 §4.1（逐次触发、无防抖）与 §4.1a（`set_data` 不发），
再决定要不要防抖 —— 这两个特性合在一起才是它的完整语义。

### 4.1 `sig_changed` 是「值变更」，不是「编辑完成」

- `TextEdit` / `ArrayTextEdit` 接 `textChanged` —— **每敲一个键**发一次；
- `Slider` / `Dial` 接 `valueChanged` —— **每拖一格**发一次；
- 本子包内**没有任何节流 / 防抖**，所以「一个字符一次信号」是常态；
- 唯一例外：`FludefEdit` 的「名字」「比热」两个输入框接 `editingFinished`（回车 / 失焦才发）。

⇒ **昂贵响应必须自己防抖**（`QTimer` 单次触发，或只在 `get_data()` 取用时才算）。

⚠️ **不要改它的名字**。名字是历史遗留，2026-10-21 评估后明确决定保留：它是本子包**全部编辑器**
的公开成员（15 处显式声明，其余经继承），外部代码会 `connect`。真需要「编辑完成」事件时，
**新增** `sig_edited` 与它并存（公共 API 只增不改）。

### 4.1a `set_data()` **不发** `sig_changed`（2026-10-22 定稿并修完）

**约定**：`sig_changed` 只在**用户经界面改值**时发；`set_data()` 是「程序把数据推上控件」，
**一律不发**。判据很好记 —— 「谁改的」：用户改 → 发；代码调 `set_data` → 不发。

为什么重要：发多了不只是「多一次通知」，而是会**误导下游**。`field_edit` 的 `on_changed`
里连着 `set_value(model, v)`，不屏蔽信号的话 `set_data` 会把**刚读出来的值又写回模型**，
外部据此判定「模型被用户改过」——**打开一次文件就等于改了一次模型**。

**做法**：`set_data` 里凡是要调 `setText` / `setPlainText` / `setValue` 的，一律用
`blockSignals` 包住，且**必须 `try/finally`**：

```python
self.blockSignals(True)
try:
    self.setText(...)
finally:
    self.blockSignals(False)
```

⚠️ **`try/finally` 不是可选项**。`blockSignals` 改的是**控件自身**的标志位，不会被异常
自动复位；中途抛异常（`get_value` 是外部回调，返回类型不归控件管 —— 实测返回 int 时
`setPlainText` 直接 `TypeError`）而没复位，控件就**永久哑掉**：此后用户怎么改都不再发
`sig_changed`，**且没有任何报错**。这比直接抛异常难查得多。

- 不需要 `except` —— 只负责复位，异常照常往上抛，由调用方决定是否处理；
- 若要「恢复原状」更严格，可 `old = self.blockSignals(True)` 再 `blockSignals(old)`，
  别一律写 `False`（会误开原本就屏蔽的对象）。本子包内都用同一对象的瞬时开关，写 `False` 即可。
- 现成范例：`../env_edit.py` 的 `_set_raw`、`../plugin_list_edit.py`、`../../plugins/builtin/user_admin.py`。

⚠️ **声明了 `sig_changed` 不等于会发**。2026-10-22 审计发现 `Interp1Edit` 右键
「转化为均匀间隔的数据」改了数据却**既不重绘也不发信号**（lambda 直接调
`self.data.to_evenly_spaced()`），已改为具名方法 `_to_evenly_spaced()`：
`to_evenly_spaced()` → `set_data()` 重绘 → `sig_changed.emit()`。**加新的右键菜单动作时，
凡是会改 `self.data` 的，都要照这个三步走。**

⚠️ **归属变更（2026-10-22 又改了一次）**：`field_edit.py` 先随 `seepage_edit.py` 搬到
`zmlx/scen/editors/`，同一天又搬回**本子包**（插件包取消）。本节讲的约定与位置无关：
`field_edit.py` 就在本目录。

### 4.2 `field_edit` 与模型类型无关 —— 判据是**回调可调**，不是 `isinstance(Seepage)`（2026-10-22 定案）

**曾经的毛病**：`field_edit.py` 的模块文档写「与 Seepage 类型无关，任何对象都能用」，但三个类
的 `set_data()` 与改动回调里都硬判 `if isinstance(self.data, Seepage)`。⇒ 传入**任何非
`Seepage` 对象**时既不显示值、也不回写 —— **完全静默**（无异常、无警告），用户只看到
「控件是空的、改了没反应」。

**为什么那个判断是错的**：这三个类真正需要的只是**两个回调**：

| 要做的事 | 真正的前提 |
|---|---|
| `set_data` 把模型的值显示出来 | `callable(self.get_value)` |
| 用户改后写回模型 | `callable(set_value)`（**构造时**就已判定，决定可编辑还是只读） |

`self.data` 只是**被交给回调的参数**。「能不能用」取决于回调在不在，与模型**是什么类**没有
因果关系；`Seepage` 只是第一个使用者。用类型判断等于给「能用」加了个**无关且隐蔽**的条件。

**现在的写法**（不要再改回 `isinstance`）：

```python
def set_data(self, data):
    self.data = data
    if not callable(self.get_value):
        return                       # 没有取值回调 → 什么都不做
    self.blockSignals(True)
    try:
        self.setPlainText(self.get_value(self.data))
    finally:
        self.blockSignals(False)

def on_changed():                    # 仅当 set_value 可调时才会被连上
    if self.data is not None:        # 只防「模型还没设进来」
        set_value(self.data, self.toPlainText())
        self.sig_changed.emit()
```

`SeepageInterp1Edit`（`seepage_edit.py`）里的同类判断也已换成
`callable(self.get_value) and self.data is not None`。

⇒ **副产品**：`field_edit.py` 不再 import `zmlx.exts`，是**纯控件**。

⚠️ 实测已覆盖：非 `Seepage` 模型能正确显示与写回、`Seepage` 模型行为不变、只读行（未传
`set_value`）仍只读且 `set_data` 不发信号、`set_data` 不写回模型（§4.1a 的契约不受影响）。

⚠️ **`SeepageKrEdit` 仍有 `isinstance(data, Seepage)`**：它判的是**整个模型**（增删相渗行
要可写），与本节不是一回事，暂未动。

### 4.3 不要给编辑器抽基类（2026-10-21 实测，PyQt6）

「20 个编辑器类都实现同一协议，抽个基类统一 `sig_changed`」听着自然，**实测不可行**。
逐个形态验证（不只测自定义属性，还实际调用 `setPlainText()` / `toPlainText()` 并发信号）：

| 基类形态 | `sig_changed` | Qt 专有方法 | 结论 |
|---|---|---|---|
| 纯 `object` mixin（前置 / 后置） | ✅ | ✅ | 唯一可用，但**不能**带 `__init__` 参数、不能有 layout |
| `QWidget` 子类 **前置** | ✅ | ❌ `could not convert ... to QTextEdit` | 排除 |
| `QWidget` 子类 **后置** | ❌ `TypeError` | ✅ | 排除 |
| `abc.ABC` + `abstractmethod` | — | — | ❌ `metaclass conflict`（`sip.wrappertype` vs `ABCMeta`） |

三条关键结论：

1. **`abstractmethod` 用不了** ⇒ 基类**根本无法强制**子类实现 `set_data` / `get_data`，
   只能写 `raise NotImplementedError`（运行时报错，不是实例化时报错）。
2. `QWidget` 基类**前置**时 **`isinstance()` 会骗人**：返回 `True`，但 C++ 对象实际只是
   `QWidget` —— 多重继承的第一个基类决定 sip 的 primary type，这类错位极难排查。
3. 真正值得统一的不是方法名，而是 `get_data()` 的**语义**（§1）—— 基类统一不了它，
   反而制造「两类编辑器可以互换」的错觉。

⇒ **维持鸭子类型**。要静态契约就用 `typing.Protocol`（纯类型层、零继承要求）；
要运行时校验就写 `is_editor(obj)` 之类的函数。**不要引入继承。**

### 4.4 模块与同名包并存时，**包胜出、`.py` 被静默忽略**

2026-10-21 拆包时实测：`editors.py` 与 `editors/` 同时存在时，
`import zmlx.ui.widgets.editors` **一定**拿到包，`.py` 里的东西全部消失，且**没有任何警告**。

⇒ 旧 `editors.py` 必须**删除**（留作 shim 也没用，它根本不会被加载）。老路径能用，
全靠 `__init__.py` 的显式转发。

### 4.5 `reg_file_type`：缺 `set_data` **或** `get_data` 都是静默降级

`zmlx/ui/alg.py` 里是两个**独立**的 `hasattr`：

```python
if set_data is None and hasattr(widget_type, 'set_data'): ...
if get_data is None and hasattr(widget_type, 'get_data'): ...
```

缺任一个 ⇒ `open_file` 里 `callable(set_data)` 为假 ⇒ **打开后是空标签页**，而且
`save_file` / `export_data` / `import_data` 三个能力**一个都不挂**
（它们要求 `get_data` + `save` 同时可调）。没有异常、没有警告，用户只看到「文件打开了但是空的」。

⇒ 新编辑器注册后**务必真正打开一个文件验一遍**，别只确认「能弹出标签页」。

### 4.6 已知越界：`seepage_edit.py` 依赖 `zmlx.tfc`

⚠️ 2026-10-22 曾因此把 `seepage_edit.py` 搬进 `zmlx/scen/editors/`（`scen` 是第 5 层，
import `tfc` 合法）；同一天那个插件包取消，**它又回到本子包**，于是这条越界**重新成立**：

`seepage_edit.py` 有 `from zmlx.tfc import seepage`，用它的 `list_fludefs` /
`get_dt` / `set_dt` / `get_time` / `set_time` / `get_step` / `set_step` / `get_cfl` / `set_cfl`。

按分层表 `ui`(3) **不得**依赖 `tfc`(4) —— 这是目前本子包**唯一**一处越界，别再加第二处。这些
getter/setter 本属模型侧；将来若收敛到 `exts` / `fluids`，这里就能去掉。

## 5. 文档分工（三份互不复制）

⚠️ 这条纪律来自 `plugins/AGENTS.md` —— 同一个主题写两份，必然漂移。

| 文档 | **只**写这些 |
|---|---|
| 本文件 | **怎么加 / 改编辑器** + 踩过的坑 |
| [`__init__.py`](__init__.py) docstring | **公共 API**：协议定义、`sig_changed` 语义、模块结构表、转发与重导出规则 |
| [`../../ReadMe.md`](../../ReadMe.md) `editors/` 行 | **唯一清单**：每个类是干什么的 |
| [`../AGENTS.md`](../AGENTS.md) | 标准骨架、命名、线程契约、右键菜单、自测 —— **对本子包同样有效** |

改动时只改该负责的那一处。

## 6. 自测与验收

每个模块底部写 `def test_xxx()` + `if __name__ == '__main__':`（照 `../AGENTS.md` §1 骨架）。

⚠️ 那些 `test_xxx()` 会**弹窗并 `app.exec()` 阻塞**，别在自动化里直接跑。批量冒烟用这条
（无头、不弹窗、只验导入与公开名字；在**仓库根** `projects/zml/` 下执行，必须用系统 WinPython ——
托管 venv 里没有 PyQt6）：

```bash
QT_QPA_PLATFORM=offscreen D:/WinPython/WPy64-31320/python/python.exe -c "
import zmlx.ui.widgets.editors as m
print(len(m.__all__), [n for n in m.__all__ if not hasattr(m, n)])"
# 2026-10-22 实测输出：28 []      ← 「名字数 / 缺失项」，第二项非空就是漏了转发
# （渗流控件一度搬走 27 → 18，同日搬回后 18 → 28）
```

⚠️ 涉 `gui.reg_file_type` / 标签页的自测，**不要**用 `gui.execute(...)` 在
`QT_QPA_PLATFORM=offscreen` 下起窗口 —— 它会卡住。自己造 `QApplication` + `MainWindow`，
再用 `gui.set(w.get_gui_api())` 注入。

验收底线（改完至少过一遍）：

1. `from zmlx.ui.widgets.editors import *` 里的名字**一个不少**（含 `__all__` 新增项）；
2. 老路径 `from zmlx.ui.widget import editors` 仍可用（只多一条 `DeprecationWarning`）；
3. 若注册了文件类型：**真的打开一个文件**，确认数据进去了、`保存 / 导出 / 导入` 三项都在。
