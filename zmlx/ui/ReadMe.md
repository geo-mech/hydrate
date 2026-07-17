# zmlx.ui — 图形用户界面

## 概述

`zmlx.ui` 提供基于 PyQt6（自动降级至 PyQt5）的完整图形用户界面系统，包括多标签页编辑器、代码编辑器、文件浏览器、控制台（后台线程执行脚本）、matplotlib 绘图、图像/PDF 查看、环境变量管理等功能。

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

**不要在函数内部调用 `gui.execute()`**，否则会导致嵌套执行，产生不可预期的行为。参考 demo 文件（如 `zmlx/demo/flow_1ph/darcy_1d.py`）。

### 导入 PyQt

**不要直接 `from PyQt6 import ...`**，应通过 `zmlx.ui.pyqt` 导入，确保 Qt 版本与 zmlx 一致：

```python
from zmlx.ui.pyqt import QtWidgets, QtGui, QtCore
from zmlx.ui.pyqt import QAction, QWebEngineView
```

`pyqt.py` 会自动选择 PyQt6（优先）或 PyQt5 降级，并在无头模式下跳过加载。

### 无头模式

```bash
python demo.py --no-gui       # 命令行模式
python demo.py --headless     # 等效
```

`gui.execute()` 内部会自动检测无头模式（`is_headless()`），不需要手动处理。

### gui.xxx() 系列函数

在 `gui.execute()` 启动的程序中，可以直接使用以下函数。**在非 GUI 模式下，这些调用自动变为空操作**，不需要 `if gui.exists()` 判断。

> **建议**：在 GUI 中运行的代码，尤其是在长循环、大量迭代的求解过程中，应多放置 `gui.break_point()`，让界面有机会响应用户的暂停/终止操作。否则界面会卡死，直到计算结束。

| 函数 | 用途 |
|------|------|
| `gui.break_point()` | 添加暂停/终止断点。**建议在长循环中多放置**，否则界面无法响应用户的暂停操作 |
| `gui.progress(label, val_range, value)` | 显示进度条 |
| `gui.show_attrs(**attrs)` | 在控制台动态显示变量 |
| `gui.information(text)` | 弹出信息对话框 |
| `gui.question(text)` | 弹出是/否对话框 |
| `gui.plot(on_figure, caption)` | 自动检测环境：有 GUI 则在标签页绘图，无 GUI 则保存到文件 |

---

## 公共 API

仅以下函数/对象为外部可用的公共接口（来自 `gui_buffer.py`）：

| 接口 | 类型 | 描述 |
|------|------|------|
| `gui` | `GuiBuffer` | 全局 GUI API 单例 |
| `information(msg, title)` | 函数 | 显示信息对话框 |
| `question(msg, title)` | 函数 | 显示问题对话框（是/否） |
| `plot(on_figure, caption, ...)` | 函数 | 在 GUI 标签页中执行绘图 |
| `break_point()` | 函数 | 插入断点（支持暂停/继续/终止） |
| `gui_exec(func)` | 函数 | 在 GUI 线程中执行代码 |
| `progress(value, text)` | 函数 | 显示进度条 |
| `show_attrs(obj)` | 函数 | 显示对象的动态属性 |
| `add_action(text, slot, ...)` | 函数 | 添加菜单动作 |

---

## 典型使用场景

```python
from zmlx import *

def main():
    """主程序：定义业务逻辑，通过 gui.execute 启动"""
    for step in range(100):
        gui.break_point()               # 断点：允许暂停/终止
        gui.progress('计算中', [0, 100], step)  # 进度条

    def on_figure(fig):
        ax = fig.add_subplot(111)
        ax.plot([1, 2, 3], [4, 5, 6])
    gui.plot(on_figure, caption='结果')

    information('模拟完成', '提示')

if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
```

---

## 控件列表（widget/）

| 控件 | 描述 |
|------|------|
| `CodeEdit` | Python 代码编辑器（QsciScintilla） |
| `MatplotWidget` | matplotlib 嵌入式显示 |
| `TabWidget` | 可关闭标签页管理器 |
| `OutputWidget` | 输出面板（文本 + 属性 + 进度条） |
| `CwdView` | 当前目录文件浏览器 |
| `DemoView` | Demo 脚本浏览器 |
| `ImageView` | 图片查看器 |
| `TextFileEdit` | 可编辑文本文件视图 |
| `CodeHistoryView` | 历史代码浏览 |
| `OutputHistoryView` | 历史输出浏览 |
| `AttrView` | 属性键值表格查看器 |
| `MemView` | 内存变量查看/编辑器 |
| `EnvEdit` | 环境变量编辑器 |
| `Fn2Widget` | 2D 裂缝网络可视化 |
| `PgConsole` | 交互式 Python 控制台 |
| `ConsoleStateLabel` | 状态栏版本号显示 |
| ... | 更多控件详见 `widget/` 目录 |

---

## 架构层次

```
zmlx.ui/
├── pyqt.py               Qt 绑定层（PyQt6 → PyQt5 自动降级）
├── utils.py              API 桥接层（跨线程安全调用）
│   └── GuiApi           通道池模式，跨线程函数调用
│   └── BreakPoint       暂停/恢复机制
│   └── TaskProc          GUI 线程任务队列
├── gui_buffer.py         API 代理层（全局 gui 单例）
├── main.py               应用层（MainWindow 主窗口）
│   └── MainWindow        QMainWindow 子类（~100 方法）
│   └── execute()         GUI 入口点
├── console.py            控制台管理器
│   └── ConsoleThread     后台脚本执行线程
│   └── Console           线程生命周期管理
├── settings.py           配置管理
├── alg.py                辅助函数（动作创建、历史记录、文件注册）
├── widget/               自定义控件集合（~35 个控件）
├── action/               额外菜单动作
├── exts/                 启动脚本管理
└── data/                 默认配置数据
```

---

## 模块列表

| 模块 | 说明 |
|------|------|
| `gui_buffer.py` | 全局 GUI API 代理 |
| `main.py` | 主窗口实现（QMainWindow） |
| `console.py` | 后台脚本执行控制台 |
| `pyqt.py` | Qt 绑定选择层 |
| `settings.py` | 配置管理（图标、声音、窗口位置） |
| `alg.py` | 辅助函数（动作、历史、文件注册） |
| `utils.py` | 跨线程安全工具（GuiApi, BreakPoint, TaskProc） |
| `setup_files.py` | 启动文件管理（已弃用） |
| `widget/` | ~35 个自定义 PyQt6 控件 |
| `action/` | 额外菜单动作 |
| `exts/` | 启动脚本管理 |
| `data/` | 默认配置数据 |

---

## 与其他模块的关系

- 公共 API（`information`、`plot`、`gui_exec` 等）通过 `zmlx.exts.LazyImport` 在顶层命名空间中可用
- `zmlx.plt`：通过 `plot_on_figure` / `plot_on_axes` 在 GUI 中显示图形
- `zmlx.utility`：`GuiIterator`、`FrameRateCtrl` 与 GUI 系统协同
- 设计上追求独立：未来将减少对 `zmlx` 其他模块的依赖
