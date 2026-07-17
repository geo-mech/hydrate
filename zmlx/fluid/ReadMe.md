# zmlx.fluid — 流体属性定义

## 概述

`zmlx.fluid` 提供各种流体（水、甲烷、二氧化碳、水合物等）的定义和创建函数。每个流体以 `FluDef` 对象封装，包含密度（`den`）、粘度（`vis`）和比热（`specific_heat`）等属性，支持以压力 × 温度的二维插值表形式存储。

---

## 快速开始

```python
from zmlx import *

# 创建标准流体
h2o = create_h2o(name='h2o')       # 液态水
ch4 = create_ch4(name='ch4')       # 甲烷气体
co2 = create_co2(name='co2')       # 二氧化碳
hydrate = create_ch4_hydrate()     # 甲烷水合物（固体）
ice = create_h2o_ice()             # 冰（固体）

# 创建水溶液
brine = create_aqueous(
    name='brine',
    h2o=create_h2o(),
    solutes=[create_solute(den=2200, vis=1e-3, name='nacl')]
)

# 创建混合物
mix = create_mixture(name='mix', ch4=create_ch4(), co2=create_co2())

# 从数据/文件创建
flu = from_data(data=[(T, P, den, vis), ...], get_t=..., get_p=...)
flu = from_file('fluid_data.txt', name='oil')
```

---

## 流体种类

### 标准流体

| 函数 | 描述 | 状态 | 密度 (kg/m³) | 粘度 (Pa·s) | 数据来源 |
|------|------|------|-------------|------------|---------|
| `create_h2o()` | 液态水 | 液相 | 经验公式 | `2e-6·exp(1808.5/T)` | 经验公式 |
| `create_h2o_gas()` | 水蒸气 | 气相 | 插值表 | 插值表 | NIST |
| `create_h2o_ice()` | 冰 | 固相 | 917 | 1e30 | 固定值 |
| `create_ch4()` | 甲烷 | 气相 | 理想气体+压缩性修正 | 经验公式 | 经验公式 |
| `create_ch4_hydrate()` | 甲烷水合物 | 固相 | 919.7 | 1e30 | 固定值 |
| `create_co2()` | 二氧化碳 | 气相 | NIST 插值表 | NIST 插值表 | NIST |
| `create_co2_hydrate()` | CO₂水合物 | 固相 | 1112（可配置） | 1e30 | 固定值 |
| `create_h2o_gas()` | 水蒸气 | 气相 | 插值表 | 插值表 | 文件读取 |

### 重油与有机物

| 函数 | 描述 | 温度范围 | 数据来源 |
|------|------|----------|---------|
| `oil.create()` | 重油 | 270-1000 K | Nourozieh 密度公式 + Mehrotra & Svrcek 粘度公式 |
| `c11h24.create()` | 正十一烷 | 插值表 | 经验公式 |
| `kerogen.create()` | 干酪根（固体） | 固定 | 龙马溪组参数（den=2590, cp=829） |
| `char.create()` | 泥岩/粘土（固体） | 固定 | 可配置密度 |

### 水溶液与混合物

| 函数 | 描述 |
|------|------|
| `create_aqueous(h2o, solutes, name)` | 通过向纯水添加溶质创建水溶液（线性缩放密度/粘度） |
| `create_mixture(name, **components)` | 组合多个单组分 `FluDef` 创建混合物 |
| `create_solute(solvent, den, vis, ...)` | 创建溶质（二分法求解密度/粘度缩放因子，适用于低浓度 ≤0.2） |

---

## 数据来源与精度

流体属性来自以下途径：

1. **经验公式**：直接在 Python 中编码的解析公式（如水、甲烷、重油）
2. **NIST REFPROP**：来自 NIST Chemistry WebBook 的高保真数据，以插值表存储
3. **Tough+Hydrate 手册**：用于水合物密度计算（`ch4_hydrate_th.py`，未验证）
4. **文件读取**：从自定义格式的文本文件读取插值数据

**NIST 数据格式**（位置：`zmlx/fluid/nist/*/`）：
```
第1列: 温度 (K)
第2列: 压力 (Pa)
第3列: 密度 (kg/m³)
第4列: 粘度 (Pa·s)
第5列: 相标志 (0=蒸汽, 1=液体, 2=超临界)
```

**数据生成**：`zmlx/fluid/archive/` 目录存储序列化的流体定义，避免在不同的运行环境中重复依赖第三方库生成数据。

---

## 模块列表

| 模块 | 说明 |
|------|------|
| `h2o.py` | 液态水（经验公式） |
| `h2o_ice.py` | 冰（固态水，固定属性） |
| `ch4.py` | 甲烷气体（经验公式） |
| `ch4_hydrate.py` | 甲烷水合物（固定属性） |
| `ch4_hydrate_th.py` | 甲烷水合物（Tough+Hydrate 公式，未验证） |
| `co2/` | CO₂ 气体（NIST 插值表） |
| `co2_hydrate.py` | CO₂ 水合物（可配置密度） |
| `co2_liq.py` | 液态 CO₂（委托给 nist.co2） |
| `oil.py` | 重油（经验公式） |
| `kerogen.py` | 干酪根（固体） |
| `char.py` | 泥岩/粘土（固体） |
| `CaO.py` / `CaOH.py` | 氧化钙/氢氧化钙（固体） |
| `_aqueous.py` | 水溶液创建 |
| `_mixture.py` | 混合物创建 |
| `solution.py` | 溶质创建 |
| `alg.py` | 核心算法（from_data, from_file, load_fludefs） |
| `nist/` | NIST REFPROP 数据封装（ch4, co2, h2o） |
| `conf/` | 经验公式配置库（各种气体/液体的密度和粘度公式） |
| `archive/` | 序列化流体数据存档 |

---

## 与其他模块的关系

- `zmlx.exts.FluDef`：本模块创建的核心对象类型
- `zmlx.tfc`：在 `tfc.create()` 中通过 `fludefs` 参数使用流体定义
- `zmlx.react`：化学反应涉及流体组分（气体、液体、固体水合物等）
- `zmlx.demo`：demo 案例中大量使用 `create_h2o()`、`create_ch4()` 等
