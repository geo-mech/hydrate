# zmlx.utility — 高层工具集

## 概述

`zmlx.utility` 提供渗流模拟中可复用的高层工具类，包括属性管理、迭代控制、数据输出、物理模型应用等功能。这些工具将常用操作封装为类，便于在模拟脚本中复用。

---

## 主要类一览

### 属性与键管理
| 类 | 说明 |
|------|------|
| `AttrKeys` | 字符串属性名到整数 ID 的映射管理器。支持属性式和字典式访问、批量注册、JSON 保存/加载 |
| `add_keys()` | 批量注册键值对（已弃用） |

### 迭代与绘图控制
| 类 | 说明 |
|------|------|
| `GuiIterator` | 自适应迭代器，协调迭代步进和绘图。自动控制绘图频率（绘图时间不超过总时间的设定比例），支持 GUI/无 GUI 模式切换 |
| `FrameRateCtrl` | 帧率限制器，确保 GUI 更新不超过指定频率 |
| `SaveManager` | 周期性自动保存模型状态。支持定长或时间相关的保存间隔，自动创建目录 |

### 物理模型工具
| 类 | 说明 |
|------|------|
| `CapillaryEffect` | 毛细管压力效应：两流体间饱和度驱动的压力差，导致相邻 Cell 间流体交换 |
| `HeatInjector` | 热注入器：两种模式（恒功率加热 / 恒温控制） |
| `PressureController` | 压力控制器：按预设时间-压力曲线维持目标 Cell 压力，通过调整孔隙体积或流体实现 |
| `CondUpdater` | 导流系数更新器：管理基准孔隙体积、基准导流系数和渗透率折减（已弃用） |
| `Len0Updater` | 热-力耦合：根据温度变化更新弹簧的初始长度（热应变） |

### 数据插值与场
| 类 | 说明 |
|------|------|
| `Field` / `LinearField` | 空间标量场：常数场或线性场 `v(x,y,z) = v0 + (x-x0)*dx + (y-y0)*dy + (z-z0)*dz` |
| `Interp2` / `Interp3` | 2D/3D 散点数据插值器。多级退化：CloughTocher → LinearND → NearestND → 常数 |
| `load_field3(filename)` | 从文本文件加载 (x,y,z,v) 数据并构建 Interp3 对象 |
| `CurveData` | 曲线数据封装（scipy interp1d 包装，边界值钳制）|

### 监测与历史记录
| 类 | 说明 |
|------|------|
| `SeepageCellMonitor` | 监测指定 Cell 的流体质量变化，记录累积产量和产率。支持数据保存（制表符分隔文本文件）和可视化 |

### 兼容性工具
| 类 | 说明 |
|------|------|
| `RuntimeFunc` | 延迟加载函数包装器。在调用时动态导入指定模块和函数，可选发出弃用警告。用于代码迁移过程中的向后兼容 |

---

## 典型用法

### 迭代控制与绘图

```python
from zmlx import *
from zmlx.utility import GuiIterator, FrameRateCtrl

iterator = GuiIterator(
    iterate=lambda: model.iterate(dt=3600),
    plot=lambda: show_contourf(x, z, p),
    max_plot_interval=10,  # 最多每10步绘一次图
    ratio=0.2,             # 绘图时间不超过迭代时间的20%
)

# 在循环中使用
while model.temps['time'] < total_time:
    iterator()
```

### 压力控制

```python
from zmlx.utility import PressureController

# 创建压力控制器，按预设曲线控制生产井压力
ctrl = PressureController(
    cell=prod_cell,
    data=[(0, 10e6), (1e7, 5e6)],  # 时间-压力曲线
)
ctrl.update(current_time)
```

### Cell 监测

```python
from zmlx.utility import SeepageCellMonitor

monitor = SeepageCellMonitor(model, cell_ids=[0, 1, 2])
for step in range(100):
    model.iterate(dt=3600)
    monitor.update(dt=3600)

# 查看产率
print(monitor.get_current_rate())  # 当前产率 (kg/s)
monitor.plot_prod(0)              # 绘制累积产量曲线
monitor.save('prod_data.txt')     # 保存数据
```

### 空间插值

```python
from zmlx.utility import Interp2

# 从散点数据创建插值器
interp = Interp2(
    x=[0, 1, 2, 0, 1, 2],
    y=[0, 0, 0, 1, 1, 1],
    v=[10, 20, 30, 40, 50, 60],
)
value = interp(0.5, 0.5)  # 插值

# 从文件加载 3D 场
from zmlx.utility import load_field3
field = load_field3('field_data.txt')
value = field(x=100, y=200, z=-500)
```

---

## 模块列表

| 模块 | 说明 |
|------|------|
| `attr_keys.py` | 属性键管理器 |
| `capillary_effect.py` | 毛细管压力效应 |
| `cond_updater.py` | 导流系数更新（已弃用） |
| `curve_data.py` | 曲线数据封装 |
| `fields.py` | 空间标量场（常数场、线性场） |
| `frame_rate_ctrl.py` | 帧率限制器 |
| `gui_iterator.py` | GUI 自适应迭代器 |
| `heat_injector.py` | 热注入器 |
| `interp.py` | 2D/3D 散点插值 |
| `len0_updater.py` | 热-力耦合长度更新 |
| `pressure_controller.py` | 压力控制器 |
| `runtime_fn.py` | 延迟加载函数包装器 |
| `save_manager.py` | 自动保存管理器 |
| `seepage_cell_monitor.py` | Cell 生产监测器 |

---

## 与其他模块的关系

- `zmlx.tfc`：大多数工具与 `Seepage` 模型交互，在 TFC 迭代循环中使用
- `zmlx.ui`：`GuiIterator`、`FrameRateCtrl` 与 GUI 系统协同工作
- `zmlx.exts`：底层数据类型（Seepage, Interp1 等）
- `zmlx.plt`：`SeepageCellMonitor` 的绘图方法依赖于 `zmlx.plt`
