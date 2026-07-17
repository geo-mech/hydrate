# zmlx.tfc — Thermal-Flow-Chemical 耦合引擎

## 概述

`zmlx.tfc`（Thermal-Flow-Chemical）是基于 `Seepage` 类的多物理场耦合模拟引擎，提供渗流（流动）、传热和化学反应的联合求解。核心设计目标是通过单一的 `tfc.seepage.iterate()` 调用完成所有物理场的状态更新。

**设计理念**：iterate 函数中所需的全部参数应定义在 Seepage 模型中并长期保存。所有配置应尽可能写入 Seepage 对象，而非通过函数参数传递。

---

## 核心入口

### `seepage.iterate()` — 主迭代循环
- 位置：`_main.py`
- 功能：推进一个时间步，自动按顺序调用以下子过程：
  1. 时间步管理（dt 更新）
  2. 流体属性更新（密度、粘度）
  3. 注入器执行
  4. 固体相备份/恢复
  5. 导流系数更新
  6. 流场迭代（达西流动求解）
  7. 扩散计算
  8. 毛管力计算
  9. 传热计算
  10. 热交换（流体-固体）
  11. 化学反应
  12. 步进/时间触发器调用

### `seepage.iterate_until()` — 按条件迭代
- 功能：持续迭代直到满足指定条件（如达到总时间）。

### `set_cell_ini()` / `make_grid()` — 模型配置
- 功能：设置 Cell 初始状态、创建结构化网格。

---

## 子模块详解

### `_main.py` — 核心迭代引擎（~68KB）
- 包含 `iterate()`、`iterate_until()` 等主循环函数
- 模型属性关键字：
  - `dt`：时间步长（秒）
  - `time`：当前模拟时间（秒）
  - `step`：当前迭代步数
  - `dt_min` / `dt_max`：时间步长范围
- 模型标签：
  - `disable_update_den`：禁止更新密度
  - `disable_update_vis`：禁止更新粘度
  - `disable_flow`：禁止流动计算
  - `disable_ther`：禁止传热计算
  - `has_solid`：存在固体相
  - `check_dt`：启用 CFL 检查
- `create()`：创建完整 Seepage 模型，支持网格、流体、初始条件一次性配置

### `_base.py` — 基础工具层（~82KB）
- `SeepageNumpy`：Seepage ↔ NumPy 数据适配器
- 常用函数：`get_step()`、`get_time()`、`get_dt()`、`set_dt()`、`get_cell_key()`、`get_face_key()`、`as_numpy()`
- `get_face_sum()` / `get_face_diff()`：Face 属性计算
- `get_cfl()` / `calc_recommended_dt()`：CFL 条件与推荐时间步长
- `get_configs()` / `put_configs()` / `add_config()`：配置存取

### `_cap.py` — 毛管力模块
- 功能：管理相邻 Cell 间由毛管压力驱动的流体组分交换
- 特点：交换不改变各 Cell 流体总体积
- 关键函数：`get_settings()`、`add_setting()`

### `_cond.py` — 导流系数更新
- 功能：根据 Cell 孔隙体积变化动态更新 Face 的导流系数（`cond`）
- 支持自定义 `cond_updaters` 注册在 `model.temps` 中

### `_diff.py` — 扩散模块
- 功能：计算溶质在浓度梯度驱动下的扩散过程
- 支持多组分多扩散设置
- 关键函数：`add_setting(flu0, flu1, fa_g, cfl)`

### `_fluid.py` — 流体属性更新
- 功能：更新所有流体的密度（`update_den`）和粘度（`update_vis`）
- 受标签 `disable_update_den` 和 `disable_update_vis` 控制

### `_heating.py` — 流体加热
- 功能：对全储层所有 Cell 中的指定流体施加分布式热源
- 关键函数：`add_setting(fluid, power, temp_max)`
- **注意**：此处为分布式加热，点加热应使用 `Injector`

### `_inj.py` — 注入模块
- 功能：执行流体注入操作（调用 `model.apply_injectors`）

### `_keys.py` — 动态属性键管理
- `DynKeys` 类：管理动态属性 ID（Cell、Face、Fluid 属性键）
- 函数：`model_keys()`、`cell_keys()`、`face_keys()`、`flu_keys()`

### `_plt.py` — 可视化
- `show_cells()`：使用 matplotlib `tricontourf` 绘制压力、温度、饱和度场

### `_prod.py` — 生产控制
- 功能：按预设压力-时间曲线控制生产井 Cell 的压力
- 关键函数：`add_setting()`、压力控制通过调整孔隙体积实现

### `_sand.py` — 砂运移（实验性）
- 功能：模拟砂的沉降及脱离
- 注意：存在梯度计算不准确的已知问题

### `_solid.py` — 固体相处理
- `backup()`：弹出标记 `has_solid` 模型的最后一种流体（固体相）
- `restore()`：流场计算后恢复固体相

### `_step.py` — 步进触发器
- 功能：按迭代步数触发回调函数（通过 slot 机制）
- 关键函数：`add_setting(start, step, stop, slot)`

### `_time.py` — 时间触发器
- 功能：按模拟时间触发回调函数
- 关键函数：`add_setting()`

### `_traj.py` — 轨迹追踪
- `get_cells_along(seg, model)`：追踪线段穿过所有 Cell 的索引
- `get_cells_along_seg(p0, p1, model)`：同上，基于起点/终点

### `_vis.py` — 粘度调整
- 功能：在流动计算中临时调整流体粘度并恢复备份

### `_check.py` — 模型检查
- `check_seepage()`：验证模型完整性（单元数、面数、重力设置）

### subdomain/ — 子域分解
- 功能：将大模型拆分为多个子域，支持并行求解和虚拟模型
- 关键函数：`create()`、`iterate()`、`split()`、`create_virtual_groups()`

---

## 快速使用

```python
from zmlx import *

# 创建模型
mesh = create_cube(x=linspace(0, 100, 21), y=(-0.5, 0.5), z=linspace(0, 50, 11))
model = tfc.create(mesh, porosity=0.3, p=10e6, temperature=280,
                   s={'h2o': 1}, perm=1e-14,
                   fludefs=[create_h2o(name='h2o')],
                   dt_max=3600*24)

# 迭代求解
tfc.solve(model, time_forward=365*24*3600, folder='output')

# 或手动控制
for step in range(100):
    model.iterate(dt=3600*24)
```

---

## 与其他模块的关系

- **输入**：依赖 `zmlx.exts`（Seepage 等核心类型）
- **流体定义**：调用 `zmlx.fluid` 获取 `FluDef` 对象
- **化学反应**：调用 `zmlx.react` 添加 `Reaction` 到模型
- **可视化**：通过 `zmlx.plt` 或内建 `show_cells()` 绘图
- **高层场景**：`zmlx.scen.hydrate`、`zmlx.scen.icp` 等基于 tfc 构建
