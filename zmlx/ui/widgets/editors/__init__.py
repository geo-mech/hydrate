"""数据编辑器子包（numpy 数组、Xy/Xyz 曲线曲面、Interp1/Interp2 插值、Seepage 模型）.

**编辑器的含义**：``set_data(data)`` 把数据交给控件 → 用户编辑 → ``get_data()`` 取回
编辑后的数据。本子包里的类都成对实现这两个方法（并带 ``sig_changed`` 信号）。

**``get_data()`` 返回什么，取决于形态 —— 只有两种**（判据是「数据存在谁身上」）：

| 形态 | `get_data()` 返回 | 例子 |
|---|---|---|
| **自持值** | **数据本身**（`ndarray` / `float` / `str` / `Interp1` …）；只有调 `get_data()` 才拿得到新输入 | `TextEdit`、`ArrayEdit`、`Slider`、`Dial`、`XyEdit`、`Interp1Edit` |
| **引用模型** | **模型引用**（`is` 传入的那个）；用户一改就写回模型了 | `ObjectEdit` 及其包装的内层；`TextFieldEdit` / `IntFieldEdit` / `FloatFieldEdit`；`FludefEdit` / `SeepageEdit` 等 |

⚠️ **「容器」不是第三种形态**（2026-10-22 修正）：``XyEdit`` / ``SeepageFormEdit`` 这类
**有没有子编辑器**属于**结构**维度，与上面的**语义**正交。容器把同一个模型转发给子控件、
再原样还回（`get_data()` 就是 `self.data`），所以它属于**引用模型型**。判据永远只看
`get_data()` 返回的是**数据**还是**模型**。完整讨论见 ``AGENTS.md`` §1。

⚠️ **渗流相关控件的去留**（2026-10-22）：``seepage_edit.py``（``SeepageEdit`` /
``FludefEdit`` / 三个容器 / 三个组合编辑器）与 ``field_edit.py``（三个字段行）曾一度
搬进插件包 ``zmlx/scen/editors/``，同日又**搬回本子包** —— 它们是**纯控件**，不属于
任何「包自己就是一个插件」的形态。只有它们的**文件类型注册**仍是插件的事
（``zmlx/ui/plugins/builtin/editors.py``）。
⚠️ 老路径 ``zmlx.ui.widgets.seepage`` / ``zmlx.ui.widget.seepage`` 仍可用（弃用垫片，
指向本子包）。

⚠️ **``sig_changed`` 是「用户改了值」的信号** —— 三个要点（**判据是「谁改的」，不是「值变没变」**）：

| 触发方 | 发不发 | 例子 |
|---|---|---|
| **用户经界面改** | ✅ **发** | 敲键盘、拖滑块、拨盘、右键菜单里会改数据的动作 |
| **代码调 ``set_data()``** | ❌ **不发** | 打开文件、刷新、程序初始化 |

⚠️ **``set_data()`` 不发**是硬约定（2026-10-22 定稿并逐类验证）：``set_data`` 是「程序把数据
推上控件」，不是「用户改」。它若漏发，下游会把「程序灌进去的数据」误判成「用户改过」——
字段行的改动回调里连着 ``set_value(model, v)``，**打开一次文件就等于改了一次模型**。
实现手法：``set_data`` 里调 ``setText`` / ``setPlainText`` / ``setValue`` 时用
``blockSignals(True) ... finally blockSignals(False)`` 包住（详见
``AGENTS.md`` §4.1a）。

⚠️ **``sig_changed`` 是「值变更」，不是「编辑完成」**（名字是历史遗留，2026-10-21
评估后**决定不改名**，理由见下）：

- 它是**逐次**触发的：``TextEdit`` / ``ArrayTextEdit`` 用 ``textChanged``（**每敲一个键**），
  ``Slider`` / ``Dial`` 用 ``valueChanged``（**每拖一格**）；
- **本子包内没有任何节流 / 防抖**，所以「一个字符一次信号」是常态；
- 例外：``FludefEdit`` 的「名字」「比热」两个输入框接的是 ``editingFinished``
  （回车 / 失焦才发）。

**用途**：给「值一改就要跟着动」的下游用 —— 预览重绘、脏标记、联动控件。容器
（``SeepageFormEdit`` / ``SeepageTabEdit`` / ``SeepageEdit``）把它逐层**汇总转发**成自己的
``sig_changed``，所以一个深层子编辑被改一次，容器**也只发一次**。

⚠️ **当前 ``editors/`` 内部只有「转发」没有「消费」**（2026-10-22 审计）：全仓没有任何地方
``connect`` 本子包的 ``sig_changed`` 去做业务。所以它是**为外部使用者准备的扩展点**，
不是本子包内部机制 —— 改它之前先想清楚「谁在听」。

所以**昂贵响应要自己防抖**：要重算、要大图重绘时，别直接挂在槽里，先攒一攒（``QTimer``
单次触发）或只在 ``get_data()`` 取用时才算。若将来真的需要「编辑完成」这一次性事件，
应当**新增** ``sig_edited`` 与 ``sig_changed`` 并存（公共 API 只增不改），而不是改掉现有名字 ——
``sig_changed`` 是多个类的公开成员，外部代码会 ``connect`` 它。

⚠️ **本包由单文件 ``widgets/editors.py`` 拆分而来（2026-10-21）**，所以老路径
``from zmlx.ui.widgets.editors import ArrayEdit`` **照常可用** —— 下面显式转发了全部
公开名字。⚠️ 之所以必须**显式**转发：模块与同名包并存时 **Python 让包胜出、静默忽略
``.py``**（实测），所以旧的 ``editors.py`` 已被删除（不是留作 shim，留了也不生效）；
老写法能继续用，全靠这里的重新导出。

结构
----

| 模块 | 内容 |
|---|---|
| ``text_edit.py`` | ``TextEdit``（字符串）、``ArrayTextEdit``（文本 ↔ numpy） |
| ``array_edit.py`` | ``ArrayEdit``（ndarray 浏览 / 文本编辑 / 导入）、``NumpyAlgs``（npy/txt 读写） |
| ``data_edit.py`` | ``DataEdit``（绘图预览基类）、``XyEdit``、``XyzEdit`` |
| ``interp_edit.py`` | ``Interp1Edit``、``Interp2Edit`` |
| ``object_edit.py`` | **通用包装器** ``ObjectEdit``：把任意**自持值编辑器**包成引用模型编辑器；另有自持值叶子 ``TextInput``（单行）/ ``IntSpin`` / ``FloatSpin`` |
| ``float_edit.py`` | ``Slider`` / ``Dial``：**自己持有**一个浮点数的滑块 / 拨盘 |
| ``field_edit.py`` | **单字段行**：``TextFieldEdit`` / ``IntFieldEdit`` / ``FloatFieldEdit``（绑定 get/set 回调；只被 ``seepage_edit`` 用） |
| ``seepage_edit.py`` | **渗流控件**：``SeepageEdit`` / ``FludefEdit``、容器 ``SeepageFormEdit`` / ``SeepageTabEdit``、组合编辑器 ``SeepageSummary`` / ``SeepageKrEdit`` / ``SeepageInterp1Edit`` |

⚠️ ``seepage_edit.py`` / ``field_edit.py`` 2026-10-22 曾搬到插件包 ``zmlx/scen/editors/``，
同日又搬回本子包（那个插件包整体取消）。**从本子包导出的名字一个都没少**，只有
``widgets/seepage.py`` 那个老垫片改回了本子包。

⚠️ **本子包只定义控件，不挂界面**（2026-10-22 起）：文件类型的注册（``gui.open_xxx``）
**不在本子包**，也不在 ``ui/`` 的装配层 —— 它是插件
``zmlx/ui/plugins/builtin/editors.py`` 的 ``setup_file_types()`` 完成的。类上**没有**
``setup_ui``，模块里也**没有** ``setup_ui.py``。

依赖方向：本子包可以 import 上层的 ``widgets/plt.py``（``MatplotWidget``）、
``widgets/code_edit.py``；反过来**不允许** —— 与 ``widgets/`` 不得 import ``tabs/``
是同一条纪律（见 ``widgets/AGENTS.md``）。⚠️ 也**不得** import
``zmlx.ui.extra_setups`` / ``zmlx.ui.plugins`` / ``zmlx.scen``（那是装配层 / 更上层的插件）。

⚠️ **已知例外（唯一一处）**：``seepage_edit.py`` import ``zmlx.tfc``（第 4 层），而本子包
在第 3 层 —— 那是从 ``widgets/seepage.py`` 时代就有的越界，记录在 ``AGENTS.md`` §4.6。
用到的只是 ``list_fludefs`` / ``get_dt`` 等 getter/setter，本属模型侧。

⚠️ 已有多个名字被其它控件复用：插件 ``plugins/builtin/editors.py`` 用 ``NumpyAlgs`` 与
``ArrayEdit`` / ``XyEdit`` / ``XyzEdit`` / ``Interp1Edit`` / ``Interp2Edit`` / ``SeepageEdit`` /
``FludefEdit``。改本包的公开名字时先搜那里。

⚠️ **``Slider`` / ``Dial`` 2026-10-21 从 ``widgets/float_edit.py`` 并入**（同样留弃用垫片）。
至此 ``widgets/`` 根目录只剩**纯控件**（``CodeEdit`` / ``TextBrowser`` / ``MatplotWidget`` /
``Label`` ……），编辑器全部集中在本子包。

⚠️ **不转发 ``setup_ui``**（2026-10-22 起）：注册文件类型属于「把控件挂到界面上」的
装配动作，已整体搬进插件 ``zmlx/ui/plugins/builtin/editors.py``。本包只定义控件 ——
装配层在上、控件层在下，反向 import 会倒置分层。

Modified by DeepSeek, 2026-10-21: 由单文件 ``editors.py`` 拆成子包（文件名与类一一对应）
Modified by DeepSeek, 2026-10-21: 并入 ``widgets/seepage.py`` 的全部编辑器控件
Modified by DeepSeek, 2026-10-21: 并入 ``widgets/float_edit.py``（``Slider`` / ``Dial``）
Modified by DeepSeek, 2026-10-22: 类上的静态 ``setup_ui`` 全部删除
Modified by DeepSeek, 2026-10-22: ``setup_ui.py`` 整体搬进装配层，本包不再转发
    ``setup_ui`` / ``reg_file_types``
Modified by DeepSeek, 2026-10-22: 新增 ``object_edit``（``ObjectEdit`` 通用包装器 +
    ``TextInput`` / ``IntSpin`` / ``FloatSpin`` 三个自持值叶子）
Modified by DeepSeek, 2026-10-22: ``seepage_edit`` / ``field_edit`` 一度搬到
    ``zmlx.scen.editors``（`__all__` 27 → 18），同日搬回本子包（`__all__` 18 → 28）
"""

# 文本类
from zmlx.ui.widgets.editors.text_edit import ArrayTextEdit, TextEdit

# numpy 数组
from zmlx.ui.widgets.editors.array_edit import ArrayEdit, NumpyAlgs

# 带绘图预览的曲线 / 曲面
from zmlx.ui.widgets.editors.data_edit import DataEdit, XyEdit, XyzEdit

# 插值
from zmlx.ui.widgets.editors.interp_edit import Interp1Edit, Interp2Edit

# 通用包装器：自持值编辑器 → 引用模型编辑器（另含三个自持值叶子）
from zmlx.ui.widgets.editors.object_edit import (
    FloatSpin, IntSpin, ObjectEdit, TextInput)

# 单浮点数编辑器（自己持有值）
from zmlx.ui.widgets.editors.float_edit import Dial, Slider

# 渗流相关的控件（2026-10-22 起回到本子包；只被插件 plugins/builtin/editors.py 注册）
from zmlx.ui.widgets.editors.field_edit import (
    FloatFieldEdit, IntFieldEdit, TextFieldEdit)
from zmlx.ui.widgets.editors.seepage_edit import (
    FludefEdit,
    SeepageEdit,
    SeepageFormEdit,
    SeepageInterp1Edit,
    SeepageKrEdit,
    SeepageSummary,
    SeepageTabEdit,
)

# ⚠️ 本包**不**转发 ``setup_ui``（2026-10-22 起）：注册文件类型属于「把控件挂到界面上」的
#    装配动作，在插件 ``zmlx/ui/plugins/builtin/editors.py`` 里。本包只定义控件 ——
#    装配层在上、控件层在下，反向 import 会倒置分层。

# ⚠️ 以下三个名字**不是**本子包的控件，但旧 ``editors.py`` 里 ``import *`` 会一并导出它们，
#    而 ``widgets/seepage.py`` 正是靠 ``from ...editors import *`` 拿到 ``gui`` 的。
#    为了让老写法与老 ``import *`` 的行为一致，这里显式重导出（改动前先搜 ``import *``）。
from zmlx.exts import Interp1, Interp2  # noqa: F401
from zmlx.ui.gui_buffer import gui  # noqa: F401
import numpy as np  # noqa: F401

__all__ = [
    'TextEdit', 'ArrayTextEdit',
    'ArrayEdit', 'NumpyAlgs',
    'DataEdit', 'XyEdit', 'XyzEdit',
    'Interp1Edit', 'Interp2Edit',
    'ObjectEdit', 'TextInput', 'IntSpin', 'FloatSpin',
    'Slider', 'Dial',
    'TextFieldEdit', 'IntFieldEdit', 'FloatFieldEdit',
    'FludefEdit', 'SeepageEdit', 'SeepageFormEdit', 'SeepageTabEdit',
    'SeepageSummary', 'SeepageKrEdit', 'SeepageInterp1Edit',
    'Interp1', 'Interp2',
    'gui',
]
