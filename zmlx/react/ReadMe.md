# zmlx.react — 化学反应模块

## 概述

`zmlx.react` 提供化学反应的定义、创建和管理功能，用于多孔介质渗流模拟中的地球化学和热化学反应。支持水合物生成/分解、融化/冻结、溶解、燃烧、吸热分解等反应类型，以及抑制剂（催化剂）定义和 TOUGHREACT 反应数据接口。

**核心设计**：所有反应类型最终都基于 `endothermic.create()` 构建，具有统一的数据字典格式，便于在 Seepage 框架内组合和互换。

---

## 快速开始

```python
from zmlx import *

# 添加甲烷水合物分解反应
reactions = [
    create_reaction(
        left={'ch4_hydrate': 1.0},      # 反应物
        right={'ch4': 0.129, 'h2o': 1},  # 生成物（含质量比）
        temp=280, heat=4.37e5,           # 参考温度(K)和反应热(J/kg)
        rate=1e-6,                       # 反应速率系数
        p2t=ch4_hydrate_p2t,             # 压力-平衡温度曲线
        t2q=ch4_hydrate_t2q,             # 温度-反应进度曲线
    )
]
add_reaction(model, data=reactions)

# 添加抑制剂（降低反应速率）
inh = create_inh(
    sol='salt', liq='h2o',              # 抑制剂溶质和溶剂
    c2t=lambda c: c * 2,                 # 浓度→平衡温度偏移
    c2q=lambda c: 1 - c,                 # 浓度→反应速率折减
)
add_inh(reaction, inh)
```

---

## 反应类型

### 内置反应工厂

| 模块 | 函数 | 描述 |
|------|------|------|
| `endothermic.py` | `create()` | **基础反应工厂**：所有反应的底层构建块。反应物→生成物单向转化吸热，温度升高驱动正向反应 |
| `hydrate.py` | `create()` | 水合物反应工厂：气体+液体↔固体水合物可逆反应 |
| `melt.py` | `create()` | 融化/升华/汽化：固体→流体相变 |
| `freeze.py` | `create()` | 冻结/冷凝：流体→固体相变 |
| `dissolution.py` | `create()` | 溶解反应：固体在液体中的可逆溶解 |
| `combustion.py` | `create()` | 燃烧反应（实验性）：超过点火温度后触发 |
| `decomposition.py` | `create()` | 吸热分解（不可逆）：温度超过阈值后分解 |
| `vapor.py` | `create()` | 水汽化：水→蒸汽，使用 Antoine 公式计算饱和蒸气压 |

### 物理常数模块

| 模块 | 描述 |
|------|------|
| `ch4_hydrate.py` | 甲烷水合物：TP 平衡曲线（来自 TOUGH+ Hydrate 手册），水合数 nh=6，离解热 ~437 kJ/kg |
| `co2_hydrate.py` | CO₂ 水合物：平衡曲线来自 Anderson (2003) 和 Zhou (2008)，水合数 nh=5.75 |
| `h2o_ice.py` | 水-冰相变：温度 273.15K，潜热 336 kJ/kg |
| `vapor.py` | 水蒸气：Antoine 公式计算饱和蒸气压 |
| `CaOH2_deshydra.py` | Ca(OH)₂ 脱水 / CaO 水合：热化学储能反应，ΔH = 104.4 kJ/mol |
| `alpha/salinity.py` | 盐度对水合物平衡温度的影响（0-20% 盐度） |
| `alpha/co2_liq_lyx.py` | CO₂ 气-液相变临界曲线（Span & Wagner 1996） |

---

## 抑制剂系统

抑制剂用于调整反应速率和相平衡温度：

```python
# 创建抑制剂
inh = create_inh(
    sol='salt',      # 抑制剂物质名
    liq='h2o',       # 溶剂名
    c2t=...,         # 浓度→平衡温度偏移函数
    c2q=...,         # 浓度→反应速率折减函数
    exp=0.5,         # 浓度指数（可选）
    exp_r=0.8,       # 逆反应浓度指数（可选）
)
```

---

## 核心算法

| 函数 | 位置 | 描述 |
|------|------|------|
| `load_reactions(option, folder)` | `alg.py` | 从 JSON 配置文件加载反应 |
| `add_reaction(model, data)` | `alg.py` | 向 Seepage 模型添加反应 |
| `create_reaction(**opts)` | `alg.py` | 从参数字典创建反应对象 |
| `create_inh(**opts)` | `inh.py` | 创建抑制剂配置字典 |
| `add_inh(reaction, inh)` | `inh.py` | 向反应添加抑制剂 |

---

## TOUGHREACT 集成

`react/tough_react/` 子包提供 TOUGHREACT 热力学数据库解析工具：

| 模块 | 描述 |
|------|------|
| `Single_react.py` | 从 `aqueous.txt` 检索单一反应并拟合 Arrhenius 参数 |
| `Multiple_react.py` | 检索包含指定反应物的所有反应 |
| `Kf_Kr.py` | 计算正向/逆向反应速率常数 |
| `thermo_loader.py` | 读取 `.tdat` 热力学数据文件，进行 Van't Hoff 拟合 |
| `react0611.py` | CaCO₃ 溶解反应构建器 |
| `co2_react.py` | CO₂ 注入和水合物反应建模 |

---

## 反应参数说明

每个反应由以下参数定义：

| 参数 | 说明 |
|------|------|
| `left` / `right` | 反应物/生成物字典 `{流体名: 质量比}` |
| `temp` | 参考温度 (K) |
| `heat` | 反应热 (J/kg)，正值为吸热 |
| `rate` | 反应速率系数 |
| `fa_t` | 温度属性键（默认为 temperature）|
| `fa_c` | 浓度属性键（默认为 conc） |
| `p2t` | 压力→平衡温度插值函数（用于水合物等）|
| `t2q` | 温度→反应进度插值函数 |
| `inhibitors` | 抑制剂列表 |

---

## 模块列表

| 模块 | 说明 |
|------|------|
| `alg.py` | 核心算法：反应加载、创建、添加 |
| `inh.py` | 抑制剂创建工具 |
| `endothermic.py` | 基础吸热反应工厂 |
| `hydrate.py` | 水合物反应工厂 |
| `ch4_hydrate.py` | 甲烷水合物物理常数 |
| `co2_hydrate.py` | CO₂ 水合物物理常数 |
| `melt.py` | 融化反应 |
| `freeze.py` | 冻结反应 |
| `vapor.py` | 汽化反应 |
| `dissolution.py` | 溶解反应 |
| `combustion.py` | 燃烧反应（实验性） |
| `decomposition.py` | 分解反应 |
| `CaOH2_deshydra.py` | Ca(OH)₂ 脱水反应 |
| `tough_react/` | TOUGHREACT 数据接口 |
| `alpha/` | 扩展反应（盐度效应、CO₂ 相变） |
| `h2o_gl_kpa/` / `h2o_ls_kpa/` | 低压水相变 |

---

## 与其他模块的关系

- `zmlx.exts.Seepage.Reaction`：反应对象的底层类型
- `zmlx.fluid`：反应涉及流体的物性定义
- `zmlx.tfc`：在 `tfc.seepage.iterate()` 中自动调用化学反应计算
- `zmlx.scen.hydrate` / `zmlx.scen.icp`：完整应用场景中的反应配置
