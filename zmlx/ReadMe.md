# zmlx — 使用指南

`zmlx` 是 `IggHydrate` 的核心 Python 库（`import zmlx`），为下游应用提供 THMC 多场耦合计算能力。
本文档面向 **zmlx 的使用者**，帮助你快速了解架构、掌握建模方法、避开常见陷阱。

---

## 架构层次

```
Layer 5  应用场景          zmlx/scen/          hydrate, icp, frac, ...
Layer 4  耦合物理引擎       zmlx/tfc/           iterate → solve
Layer 3  工具与 GUI         zmlx/utility/, ui/  Field, GuiIterator, PyQt6
Layer 2  物理定义           zmlx/fluid/, react/, kr/
Layer 1  Python→C++ 绑定    zmlx/exts/          zml.dll / zml.so
Layer 0  C++ 内核           ../../zml/          C++17 header-only
```

**依赖方向**：`system/` → `exts/` → 所有上层。**C++ 文件不可修改**（作者单独维护）。

---

## 子包速览

| 包 | 定位 | 核心 |
|------|------|------|
| `zmlx/system/` | 基础服务（无内部依赖） | `app_data`, `is_headless`, `execute_once`, `deprecated` |
| `zmlx/exts/` | C++ 绑定层 | `Seepage`, `FluDef`, `Cell`, `Face`, `Vector`, `Tensor3` |
| `zmlx/tfc/` | 耦合引擎 | `seepage.iterate()`, `tfc.create()`, `tfc.solve()` |
| `zmlx/fluid/` | 流体物性 | `create_ch4`, `create_h2o`, `create_aqueous`, NIST REFPROP |
| `zmlx/react/` | 化学反应速率 | `create_reaction`, `add_inh` |
| `zmlx/kr/` | 相对渗透率 | `create_kr`, `create_krf` |
| `zmlx/plt/` | matplotlib 可视化 | `plot_on_figure`, `add_contourf`, `show_field2` |
| `zmlx/fig/` | Figure 构建抽象 | `axes2`, `auto_layout`, `contourf`, `tricontourf` |
| `zmlx/ui/` | PyQt6 GUI | `gui.execute()`, `MainWindow`, `MatplotWidget` |
| `zmlx/scen/` | 应用场景 | `hydrate.create/solve`, `icp.create` |
| `zmlx/utility/` | 高层工具 | `Field`, `GuiIterator`, `SaveManager` |
| `zmlx/alg/` | 通用算法 | `linspace`, `join_paths`, `create_async` |
| `zmlx/geometry/` | 几何计算 | `get_distance`, `get_angle`, `dfn2` |
| `zmlx/io/` | 输入输出 | `opath`, `json_ex`, `read_py` |
| `zmlx/filesys/` | 文件系统 | `list_files`, `make_dirs` |
| `zmlx/mesh/`, `seepage_mesh/` | 网格生成 | `create_cube`, `create_xz` |
| `zmlx/fem/` | 有限元 | 有限元求解（开发中） |

---

## GUI 执行模式

### 正确启动

```python
if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
```

**不要在函数内部调用 `gui.execute()`**，只在 `__main__` 入口处调用一次。

### 无头模式

```bash
python script.py --no-gui       # 命令行模式
python script.py --headless     # 等效
```

`gui.execute()` 内部通过 `is_headless()` 自动检测。`gui.xxx()` 函数在无头模式下自动变为空操作。

### 调试建议

在长循环中多放 `gui.break_point()`，让界面有机会暂停/终止。

```python
for step in range(1000):
    gui.break_point()
    model.iterate(dt=dt)
```

---

## 核心数据流

```
模型创建 → tfc.create() / hydrate.create()
         ↓
         Seepage 对象（cell, face, fluid, reaction）
         ↓
时间推进 → seepage.iterate()  或  tfc.solve()
         ↓
         iterate_flow → iterate_thermal → reactions → ...
         ↓
      时间步长自适应（cfl, check_dt）
         ↓
可视化 → show_2d_v2(), plot_on_figure(), extra_plot
```

---

## 常用开发模式

### 空间分布函数

```python
def get_k(x, y, z):      # 函数闭包定义渗透率分布
    return 1e-14 if z > -30 else 1e-15

model = tfc.create(mesh, perm=get_k, ...)
```

### 边界条件

- 定压 → 极大体积 / 极大孔隙度
- 恒温 → 极大热容（denc = 1e20）
- 生产井 → `prods=[{index, p, t}]`
- 虚拟 cell/face → `add_cell_face(mesh, ...)`

### 保存与恢复

```python
model.save('path.seepage')
model.load('path.seepage')
```

---

## 测试

```bash
# 批量测试所有 demo（多线程并行）
python zmlx/demo/test_all_demos.py

# 快速测试
python zmlx/demo/test_all_demos.py --timeout 30

# 单个 demo
python zmlx/demo/flow_1ph/darcy_1d.py --no-gui
```

---

## 常见陷阱

1. **虚拟 Face 热泄漏**：`add_cell_face` 后确保 `heat_cond=0` 在附近
2. **定压边界**：用极大体积/孔隙度，别直接改压力
3. **恒温边界**：用极大热容 `denc=1e20`
4. **步长管理**：加 `check_dt` tag + 合理 `cfl`
5. **注入/加热后**：调用 `tfc.set_dt(model, 1e-3)` 重置步长
6. **饱和度之和** ≤ 1
7. **循环导入**：高依赖模块在函数内部 import

---

## 更多

- 建模指南 → `zmlx/demo/ReadMe.md`
- 版本日志 → `CHANGELOG.md`
- 项目级指引 → `CLAUDE.md`
- 各子包详情 → 子包目录下的 `ReadMe.md`
