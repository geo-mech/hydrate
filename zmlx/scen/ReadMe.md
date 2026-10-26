# zmlx.scen — 应用场景模块

## 概述

`zmlx.scen` 定义基于 zmlx 中其他基础模块的具体工程和地质应用场景，针对实际问题提供最接近应用的数值模拟功能配置。

**设计原则**：
- 每个子模块对应一个具体的应用场景
- `hydrate` 和 `icp` 两个子包已导入到 zmlx 顶层命名空间（向后兼容）
- 后续子包采用松散组织，不自动导入，可存放不成熟或测试中的代码
- `__init__.py` 不主动导入任何子包

---

## 场景列表

| 子包 | 导入顶层 | 描述 |
|------|---------|------|
| `hydrate/` | 是 | 天然气水合物（可燃冰）开发模拟 |
| `icp/` | 是 | 原位转化（干酪根热解/重油裂解） |
| `frac/` | 否 | 裂缝模拟（兼容旧版 `zmlx.config.frac`） |
| `geothermal_helium/` | 否 | 地热伴生氦气开采 |
| `helium/` | 否 | 氦气流体定义（`create_fludefs`）与体积分数可视化 |
| `mineralization_reactor/` | 否 | CO₂ 矿化封存（Reaktoro 化学耦合） |
| `rkt/` | 否 | Reaktoro 化学热力学基准测试/教程 |
| `quick_look/` | 否 | 2D 单相流压力快速评估 |
| `uv_equilibrium/` | 否 | 气-水固定体积-内能（UV）平衡计算 |
| `easter_eggs/` | 否 | **彩蛋（插件包）**：连连看 + 螺螺是方块，挂在「帮助 → 彩蛋」 |

---

## 各场景详解

### hydrate/ — 天然气水合物开发
- 位置：`zmlx/scen/hydrate/`
- 功能：模拟水合物成藏、降压开发、注热开发、CO₂ 置换等过程
- 主要导出：`create()`、`create_fludefs()`、`create_reactions()`、`create_caps()`、`create_opts()`、`solve()`、`show_2d()`
- 应用案例：`zmlx/demos/hydrate/` 中的多个 demo 脚本

### icp/ — 原位转化（油页岩/重油）
- 位置：`zmlx/scen/icp/`
- 功能：模拟干酪根热解、重油裂解、原位加热开采
- 主要导出：`create()`、`create_fludefs()`、`create_reactions()`、`solve()`、`show_xz()`
- 应用案例：`zmlx/demos/heavy_oil/` 中的 ICP demo

### frac/ — 裂缝模拟
- 位置：`zmlx/scen/frac/`
- 功能：裂缝建模基础代码（拓扑、电阻率、速率、轨迹、最小宽度）
- 子模块：`_base.py`、`_rate.py`、`_resist.py`、`_topo.py`、`_traj.py`、`_wmin.py`、`_layered.py`、`_lay3d.py`、`_net2.py`、`_rc3.py`、`_show.py`

### geothermal_helium/ — 地热伴生氦气
- 位置：`zmlx/scen/geothermal_helium/`
- 功能：模拟地热系统中氦气（He）与氮气（N₂）的伴生开采
- 使用 IAPWS 标准计算亨利常数

### mineralization_reactor/ — CO₂ 矿化封存
- 位置：`zmlx/scen/mineralization_reactor/`
- 功能：将 Reaktoro 化学热力学与渗流传质耦合，模拟 CO₂ 注入后与岩石矿物反应形成碳酸盐矿物
- 特点：完整的配置系统、矿物列表、物种验证

### rkt/ — Reaktoro 基准测试
- 位置：`zmlx/scen/rkt/`
- 功能：Reaktoro 化学热力学功能演示和教程
- 内容：8 个基础教程脚本 + 平衡计算示例

### quick_look/ — 2D 单相流压力快速评估
- 位置：`zmlx/scen/quick_look/`
- 功能：矩形区域内单相 Darcy 渗流压力分布快速计算
- 导出：`evaluate()`（支持控压点、裂缝线段、加速因子）
- GUI：`zml_plugin.py` 集成，`帮助 > 加载 > Quick Look 快速评估` 打开参数输入与结果显示控件
  ⚠️ 该插件声明 `# ** enabled = False`（**默认不加载**）：需在「设置 → 插件」里勾选并重启，菜单入口才会出现

### uv_equilibrium/ — 气-水 UV 平衡
- 位置：`zmlx/scen/uv_equilibrium/`
- 功能：气-水两相系统的固定体积-内能（UV）平衡计算

### easter_eggs/ — 彩蛋游戏（插件包）
- 位置：`zmlx/scen/easter_eggs/`
- 功能：两个彩蛋游戏，作为**一个可关闭的插件**（默认**不启用**）挂在「帮助 → 彩蛋」
- 内容：`zml_plugin.py`（入口）、`lianliankan.py`（连连看）、`tetris.py`（螺螺是方块）、`__init__.py`、`ReadMe.md`
- 命令：`gui.show_lianliankan()` / `gui.show_tetris()`
- ⚠️ **一个子包、一个入口、两个模块**：两个游戏各自完全自含（约 190 / 215 KB），而一个目录
  只能有一个 `zml_plugin.py` —— 所以「设置 → 插件」里一行（彩蛋），菜单里两项
- ⚠️ 2026-10-22 由 `ui/plugins/builtin/tetris.py` + `lianliankan.py` 合并而来；旧名单记录自动改写
- 详见 [`easter_eggs/ReadMe.md`](easter_eggs/ReadMe.md)

---

## 使用示例

```python
# 水合物开发（hydrate 已导入 zmlx 顶层）
from zmlx import *
model = hydrate.create(
    mesh, gravity=[0, 0, -10],
    porosity=get_fai, temperature=get_t,
    p=get_p, s=get_s, perm=get_k,
    heat_cond=heat_cond,
    prods=[{'index': 0, 'p': [3e6, 3e6]}],
    dt_max=24*3600, cfl=0.1
)
hydrate.solve(model, time_forward=365*24*3600)

# ICP（icp 已导入 zmlx 顶层）
model = icp.create(
    mesh, porosity=0.3, p=10e6, temperature=500,
    injectors=[...], prods=[...]
)
icp.solve(model, time_forward=10*365*24*3600)
```

---

## 与其他模块的关系

- `zmlx.tfc`：所有场景模块均基于 TFC 引擎构建
- `zmlx.fluids`：场景使用其中定义的流体物性
- `zmlx.reactions`：场景使用其中定义的化学反应
- `zmlx.exts`：底层 Seepage 等数据结构
- `zmlx.plt` / `zmlx.ui`：结果可视化
