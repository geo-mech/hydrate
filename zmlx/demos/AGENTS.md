# AGENTS.md

**`zmlx/demos/`** 的唯一规范来源。上承 `projects/zml/AGENTS.md` 与仓库根 `AGENTS.md`；冲突时
以本文件为准。

本 agent **只在 `zmlx/demos/` 内工作**，不改本目录以外的文件。demo 把 `zmlx` 当库用；需要改
`zmlx` 的 API 时把需求写清楚，交给 Python 侧 agent（见 `projects/zml/AGENTS.md`）。
C++ 内核（`zml/`）见仓库根 `AGENTS.md`。

## `desc` 是硬要求

GUI 的 `DemoView`（`zmlx/ui/plugins/builtin/demo_menu.py`，2026-10-22 由
`zmlx/ui/tabs/demo_view.py` 并入）靠 `zmlx.demos.list_demo_files()`
（`demo/__init__.py`）列出 demo：

1. 用 `zmlx.algs.list_files` 扫本目录下所有 `.py`（含 `__Trash`/`debugging`，共 173 个）；
2. **跳过**路径含 `__Trash` 或 `debugging` 的文件；
3. 取出所有 `# **` 注释行，**拼接成一段代码后整体 `exec()` 一次**
   （`code_config` 的 `line_by_line` 默认为 `False`，`list_demo_files` 也没传它）；
4. 看得到的命名空间里 `desc` 是否是非空字符串；
5. 返回 `[(绝对路径, 描述), ...]` —— 当前 110 条。

**每个可运行的 demo 都必须有 `# ** desc = '...'`。** 没有 `desc` 的文件在 GUI 里**不可见**
—— 辅助模块（`__init__.py`、`path.py`、`opath.py`）和 `test_all_demos.py` 正是靠这一点不被当成
demo 列出来。因为所有 `# **` 行是**拼接**后一次 exec（不是逐行 exec），多行描述可以直接用
**隐式字符串拼接**：

```python
# ** desc = 'line1\n' 'line2\n' 'line3'
```

## 运行与批量测试

```bash
python zmlx/demos/flow_1ph/darcy_1d.py            # GUI 模式（默认）
python zmlx/demos/flow_1ph/darcy_1d.py --no-gui   # 无头模式，图存到文件
python zmlx/demos/test_all_demos.py [--jobs N] [--timeout N] [--verbose]
```

入口一律 `gui.execute(main, close_after_done=False)`，且**只在 `if __name__ == '__main__'`**
里调用（`gui.execute` 内部自己处理 GUI / 无头，不要写进函数里）。

⚠️ 批量测试**长耗时**（十几分钟起），**只在用户明确要求「测试」/「跑 demo」时跑**
（同 `projects/zml/AGENTS.md` 的「4. 批量测试」）。它把每个 demo 以 `--no-gui` 起子进程，
收集 stdout/stderr 并生成报告（超时与失败分开统计），输出到 `test_output_<时间戳>/`。

## 目录组织

| 目录 | 领域 | 常用 API |
|---|---|---|
| `flow_1ph/` | 单相达西流、扩散 | `Seepage`（手写）、`tfc.create` |
| `flow_2ph/` | 两相驱替、重力分异 | `tfc.create`、`FluDef`、`create_kr` |
| `thermal/` | 纯热传导、EGS | `model.iterate_thermal()` |
| `hydrate/` | 水合物生成与开采 | `hydrate.create`、`hydrate.solve` |
| `heavy_oil/` | 原位转化（ICP） | `icp.create` |
| `mech/` | 固体力学（FEM） | FEM 模块 |
| `spring/` | 弹簧-质量动力学 | FEM 动力学 |
| `flow_dy/` | 流体惯性 / 压力波 | `tfc.create(dt_max=...)` |
| `flow_thermal/` | 流动 + 传热耦合 | `tfc.create(heat_cond=...)` |
| `aqueous/` | 水溶液对流扩散 | `tfc.create`、多组分 |
| `plt/` | matplotlib 绘图 demo | `fig`、`plot` |
| `others/` | 杂项（DFN、IP、sand 等） | 各式 |
| `tests/` | 底层 DLL / 函数测试 | 直接调 `zml` |
| `gui_input/` | GUI 交互控件示例（pyqtgraph ParameterTree） | `pyqtgraph` |
| `debugging/` | 调试中的草稿（**不计入 demo 列表**） | — |

⚠️ `frac/` 目前只有一个空的 `__init__.py`（没有任何 demo），别照它建新目录。
`__Trash/` 是废弃代码，不要引用或复活。

## Demo 写法约定

**高层 demo**（多数）用 `tfc.create()` 或场景级 helper（`hydrate.create()`、`icp.create()`）：

```python
model = tfc.create(mesh, porosity=..., p=..., s=..., perm=...,
                   fludefs=[...], gravity=(0,0,-10), dt_max=...)
tfc.solve(model, time_forward=..., folder='output')
```

**底层 demo**（教学 / 调试）手搭 `Seepage`：

```python
model = Seepage()
c = model.add_cell(); c.pos = [x, y, z]; c.set_pore(...)
face = model.add_face(i0, i1); face.cond = area * perm / dist
model.iterate(dt=...)
```

关键公式：`face.cond = area * perm / dist` —— 两个 cell 之间流动的传导系数。

### 空间函数模式

核心建模范式：把物性写成 `(x, y, z) → 值` 的闭包，再传给 `tfc.create(porosity=..., perm=...,
s=..., p=..., temperature=...)`：

```python
def get_k(x, y, z):
    return 1e-14 if -70 < z < -30 else 1e-15   # 储层 vs 盖层

def get_s(x, y, z):
    return {'ch4': 0.5, 'h2o': 0.5}
```

### 边界条件（写在代码里，不是配置）

- **定压**：把 cell 体积设成 `1e6`（巨大）→ 流动中压力几乎不变
- **定温**：把 `denc` 设成 `1e20`（巨大热容）
- **封闭**：不连 face（或 `perm=0`）
- **井**：`model.add_injector(cell=..., flu=..., value=rate)`，或场景创建器里的
  `prods=[{'index': ..., 'p': [...]}]`

### 可视化

```python
def show(model, jx, jz):
    x = tfc.get_x(model, shape=(jx, jz))
    p = tfc.get_p(model, shape=(jx, jz))
    # ... 用 fig 或 plot 模块画

tfc.solve(model, extra_plot=lambda: show(model, jx, jz), ...)
plot(on_figure, caption='Results')     # 自动适配 GUI / 无头
```

### 路径 helper

- **`from zmlx.demos import get_path`** —— 取 demo 根目录。这是**当前正确**的用法
  （`demo/__init__.py` 里的 `SelfPath(__file__)`，`plugins/builtin/demo_menu.py` 就是这么 import 的）。
- `demo/opath.py` —— 输出路径：`opath`（= `get_path`）、`set_output`（= `set_path`），
  转出自 `zmlx.io.path`。
- ⚠️ `demo/path.py` 与 `demo/get_path.py` **都是废弃的转发 shim**（各自带 `DeprecationWarning`，
  分别声明 2027-05-25 / **2026-04-15** 后移除，后者**已过期**）—— 新代码不要 import 它们。

## 新建 / 修改 demo 时

1. 第一行写 `# ** desc = '简洁的中文描述'`
2. 入口用 `gui.execute(main, close_after_done=False)`
3. 按现有 demo 惯例 `from zmlx import *`
4. 代码自包含，中文注释
5. 优先 `tfc.create()`（除非该 demo 就是要教底层机制）
6. 放进与物理领域匹配的子目录
7. 不引用、不修改 `zmlx/demos/` 以外的文件
