# zmlx.fluids — 流体属性定义

## 概述

`zmlx.fluids` 提供各种流体（水、甲烷、二氧化碳、水合物等）的定义和创建函数。每个流体以 `FluDef` 对象封装，包含密度（`den`）、粘度（`vis`）和比热（`specific_heat`）等属性，支持以压力 × 温度的二维插值表形式存储。

---

## 快速开始

```python
from zmlx import *                                      # create_h2o / create_ch4 / from_data / FluDef …
from zmlx.fluids import create_mixture                  # ⚠️ 不在 zmlx 顶层，须单独导入

# 标准流体
h2o = create_h2o(name='h2o')       # 液态水
ch4 = create_ch4(name='ch4')       # 甲烷气体
co2 = create_co2(name='co2')       # 二氧化碳
hydrate = create_ch4_hydrate()     # 甲烷水合物（固体）
ice = create_h2o_ice()             # 冰（固体）

# 水溶液：solutes 每项是 [名字, c, den_times, vis_times]
brine = create_aqueous(name='brine', h2o=create_h2o(),
                       solutes=[['nacl', 0.1, 1.1, 1.2]])

# 混合物
mix = create_mixture('mix', ch4=create_ch4(), co2=create_co2())

# 从数据 / 文件创建
flu = from_data(data=[(T, P, den, vis), ...],
                get_t=lambda x: x[0], get_p=lambda x: x[1],
                get_den=lambda x: x[2], get_vis=lambda x: x[3])
flu = from_file('fluid_data.txt', name='oil')

# 常数流体（最快，不查表）
water = FluDef(den=1000.0, vis=1.0e-3, specific_heat=4200.0, name='water')
```

---

## 建立流体

四条路径，按「工作量」递增排列。先判断你属于哪一种：

| # | 路径 | 适用场景 | 入口 |
|---|------|---------|------|
| 1 | 常数属性 | 快速试算、固体、教学 demo | `FluDef(den=…, vis=…)` |
| 2 | 内置函数 | 已收录的常见物种 | `create_h2o()` / `create_ch4()` … |
| 3 | 数据表 | 手上有 P-T-ρ-μ 实测或 NIST 数据 | `from_data()` / `from_file()` |
| 4 | 自写关联式 | 新物种，有文献公式 | 仿 `h2o.py` / `oil.py` |

溶液、混合物是对已有 `FluDef` 的**组合**，不属于新物种，见下文单独小节。

### 路径 1：常数属性（最快）

```python
from zmlx import FluDef

water = FluDef(den=1000.0, vis=1.0e-3, specific_heat=4200.0, name='water')
rock = FluDef(den=2590.0, vis=1.0e30, specific_heat=829.0, name='kerogen')
```

传数会被 `Interp2.create_const()` 包成常数插值场 —— **任何 P、T 下都返回同一个值**。
固体相用 `vis=1e30` 表示不可流动，这是全仓惯例（`h2o_ice.py`、`ch4_hydrate.py`、
`kerogen.py` 都这么写）。

### 路径 2：内置函数（最常用）

```python
from zmlx import create_h2o

h2o = create_h2o(name='h2o', t_min=272, t_max=300, p_min=1e6, p_max=40e6)
```

返回带 P×T 插值表的 `FluDef`。完整清单见下面「流体种类」：7 个由 `zmlx` 顶层直接导出
（`create_h2o` / `create_h2o_gas` / `create_h2o_ice` / `create_ch4` / `create_ch4_hydrate` /
`create_co2` / `create_co2_hydrate`），另有 `oil` / `c11h24` / `kerogen` / `char`
需要从对应子模块取。

⚠️ `create_h2o` 的采样域受断言限制：`269 < t_min < t_max < 350` K、
`10 kPa < p_min < p_max < 50 MPa`，越界直接 `AssertionError`。其它 `create_*`
的默认域各不相同，用前看一眼函数签名。

### 路径 3：从数据表（实测 / NIST）

**直接给列表** —— `from_data`（`zmlx/fluids/alg.py:153`）

```python
from zmlx import from_data

# 每行： (T[K], P[Pa], den[kg/m³], vis[Pa·s])
data = [(300.0, 10e6, 1000.0, 1.00e-3),
        (300.0, 20e6, 1001.0, 1.10e-3),
        (320.0, 10e6,  995.0, 0.80e-3),
        (320.0, 20e6,  996.0, 0.90e-3)]

flu = from_data(
    data=data,
    get_t=lambda x: x[0], get_p=lambda x: x[1],
    get_den=lambda x: x[2], get_vis=lambda x: x[3],
    t_min=300, t_max=320, p_min=10e6, p_max=20e6,   # 可选，缺省取数据的最值
    name='tab', specific_heat=2000.0,
)
```

**从文本文件** —— `from_file`（`alg.py:208`），空白分隔的四列，顺序固定：

```
# T[K]   P[Pa]       den[kg/m^3]  vis[Pa.s]
300.0    10000000    1000.0       0.001
300.0    20000000    1001.0       0.0011
```

```python
oil = from_file('oil_data.txt', t_min=274, t_max=423, name='oil', specific_heat=1800)
```

两个容易踩的点：

- `t_min/t_max/p_min/p_max` 是**采样域**，不是数据过滤条件。采样域之外的查询点会被插值器
  夹紧到边界值。
- 密度或粘度 ≤ `1e-20` 的样本会被**直接丢弃**（视作缺测点）。这是 `from_data` 内部的
  `v_min=1.0e-20`，不是 bug。

### 路径 4：自己写关联式（新建物种的标准做法）

`zmlx/fluids/h2o.py`、`oil.py` 是范式，四步：

```python
import math
from zmlx.exts import Interp2, FluDef


def create(t_min=280.0, t_max=400.0, p_min=1e6, p_max=40e6, name=None):
    # ① 写 P、T 的函数：SI 单位，Pa / K -> kg/m³ 或 Pa·s
    def get_density(P, T):
        return 1000.0 * (1.0 + 4.0e-10 * P) * (1.0 - 5.0e-4 * (T - 280.0))

    def get_viscosity(P, T):
        return 1.0e-3 * math.exp(1500.0 * (1.0 / T - 1.0 / 300.0))

    # ② 预采样成二维表（x 轴 = 压力，y 轴 = 温度）
    def build(fn):
        itp = Interp2()
        itp.create(p_min, 0.5e6, p_max, t_min, 2.0, t_max, fn)
        return itp

    # ③ 组装
    return FluDef(den=build(get_density), vis=build(get_viscosity),
                  specific_heat=2000.0, name=name)
```

④ **核对**：模块里加一个 `show_all()`，`python -m zmlx.fluids.<模块名>` 即可出图：

```python
def show_all():
    from zmlx.plt import show_flu_def
    show_flu_def(create(name='demo'), [1e6, 40e6], [280, 400])
```

`Interp2.create(xmin, dx, xmax, ymin, dy, ymax, fn)` 里的 `dx` / `dy` 只是**期望采样步长**，
内核会取整、并保证两端都被采到，实际步长**略小于**传入值。陡函数（例如粘度随温度指数变化）
必须用小步长，否则表会削掉峰值 —— `oil.py` 的温度步长就是 `10 K`，`h2o.py` 是 `1 K`。

### 溶液与混合物

```python
from zmlx.fluids import create_aqueous, create_mixture, create_h2o, create_ch4, create_co2

# 水溶液：solutes 每项是 [名字, 浓度c, 密度倍数, 粘度倍数]
brine = create_aqueous(name='brine', h2o=create_h2o(),
                       solutes=[['nacl', 0.1, 1.1, 1.2]])

# 等价的关键字写法（key 即溶质名，value 是 [c, den_times, vis_times]）
brine = create_aqueous(name='brine', nacl=[0.1, 1.1, 1.2])

# 混合物
mix = create_mixture('mix', ch4=create_ch4(), co2=create_co2())
```

⚠️ `solutes` 里必须放**列表或元组**，不能放 `create_solute()` 的返回值 —— 后者是 `FluDef`，
传进去会在 `len(solute)` 上抛 `TypeError`。`create_solute` 用于单独构造一个溶质定义，
其 `c` 被断言限制在 `(0, 0.2]`，线性密度/粘度假设只在这个浓度区间成立
（依据见 `aqueous_density_linearity.md`）。

### FluDef 参数语义

`FluDef(den, vis, specific_heat, name, path)` —— 定义在 `zmlx/exts/_seepage.py:856`。
类文档明确的前提：**密度与粘度都是 P、T 的二维函数，用插值表存储；比热被视为常数。**

| 参数 | 类型 | 默认 | 断言范围 | 说明 |
|------|------|------|---------|------|
| `den` | `float` 或 `Interp2` | `1000.0` | `1e-3 < den ≤ 1e7` | 密度 kg/m³；传数则包成常数场 |
| `vis` | `float` 或 `Interp2` | `1.0e-3` | `1e-7 < vis < 1e40` | 粘度 Pa·s；固体填 `1e30` |
| `specific_heat` | `float` | `4200.0` | `0.1 ≤ cp ≤ 1e8` | **常数**，J/(kg·K)，不随 P/T 变化 |
| `name` | `str` | `None` | — | 仅用于区分，不参与计算 |
| `path` | `str` | `None` | — | 从序列化文件加载（此时忽略 den/vis） |

**读取物性**：`flu.den(P, T)` / `flu.vis(P, T)`，等价于 `flu.get_den(P, T)` / `flu.get_vis(P, T)`。
`flu.den` 本身返回 `Interp2` 对象，可以直接当函数调用。

**序列化**：`flu.save('x.txt')` 存盘、`FluDef(path='x.txt')` 读回。扩展名决定格式 ——
`.txt`（跨平台，基本不可读）、`.xml`（可读但体积最大、最慢）、其它（二进制，最快最小，
但 Windows 与 Linux 生成的文件互不通用）。

#### 四个坑

1. **`FluDef(name='h2o')` 不是 `create_h2o()`**。前者是 den=1000、vis=1e-3 的**常数**
   流体，只借用了这个名字；后者才是带 P×T 表的真水。demo 里
   `FluDef(name='h2o', den=1000, vis=1e-3)` 是刻意的简化，别当成物性库来用。
2. **多组分流体没有 `den` / `vis`**。`create_aqueous`、`create_mixture` 返回的 `FluDef`
   满足 `component_number > 0`，此时读写 `den`、`vis`、`specific_heat` 都会抛
   `AssertionError`；要看物性请走 `FluData` 或遍历 `flu.components`。
3. **`specific_heat` 不随温度变化**。需要真实 `cp(T)` 时，只能按温度分段建多个 `FluDef`，
   或改用 `cp/` 引擎的 `*_specific_heat(P, T)`。
4. **常数 `den` 的上限是 `1e7`，`vis` 的下限是 `1e-7`**。极稀薄气体（ρ < 1e-3）和无粘流体
   无法用常数形式表达，必须给 `Interp2`。

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

**NIST 数据格式**（位置：`zmlx/fluids/nist/*/`）：
```
第1列: 温度 (K)
第2列: 压力 (Pa)
第3列: 密度 (kg/m³)
第4列: 粘度 (Pa·s)
第5列: 相标志 (0=蒸汽, 1=液体, 2=超临界)
```

**数据生成**：`zmlx/fluids/archive/` 目录存储序列化的流体定义，避免在不同的运行环境中重复依赖第三方库生成数据。

---

## 高精度物性引擎（CoolProp / Reaktoro）

v1.7 新增两个基于第三方库的纯流体物性子包，精度远高于上面的经验公式。两者的
流体清单、函数签名、绘图与对比脚本都写在各自子包的模块 docstring 里
（`import` 后 `help()` 或直接看源文件），下面只给指针与差异。

### `cp/` — CoolProp（工程精度）

基于 Helmholtz 能量状态方程，对标 NIST REFPROP，误差 < 0.1%。覆盖 8 种流体
（H₂O/H₂/He/CH₄/C₂H₆/N₂/O₂/CO₂，对应 CoolProp 名称 `Water`/`Hydrogen`/`Helium`/
`Methane`/`Ethane`/`Nitrogen`/`Oxygen`/`CO2`，函数前缀依次为 `h2o_`/`h2_`/`he_`/
`ch4_`/`c2h6_`/`n2_`/`o2_`/`co2_`）。每种提供 `_density`、`_viscosity`、
`_specific_heat` 三个函数，签名均为 `fn(P, T)`，SI 单位。

```python
from zmlx.fluids.cp import h2o_density, h2o_viscosity, h2o_specific_heat
```

### `rkt/` — Reaktoro（地质化学）

基于 Supcrt98 数据库，适用于高温高压地质化学场景。提供 7 种流体（无 C₂H₆），
不含粘度（Reaktoro 不支持输运属性）。

### `rkt/aq/` — 水溶液密度

Reaktoro 独有：气-液平衡分配下的水溶液密度计算，6 种气体水溶液
（CH₄/CO₂/N₂/O₂/He/H₂），自动捕获溶解度饱和拐点，函数形如
`h2o_ch4_density(w=0.001, P=10e6, T=300)` / `h2o_co2_density(w=0.02, P=10e6, T=300)`
（另有同名的 `_solubility` 系列）。

**绘图**：`python -m zmlx.fluids.cp._ch4`、`python -m zmlx.fluids.rkt._ch4`、
`python -m zmlx.fluids.rkt.aq._ch4`，或 `from zmlx.fluids.cp._plot import plot_contours`。
**对比**：`python -m zmlx.fluids.rkt._compare_rkt_and_cp`。

### 引擎对比

| 特性 | `cp/` (CoolProp) | `rkt/` (Reaktoro) |
|------|-----------------|-------------------|
| 精度 | 工程级 (< 0.1%) | 地质化学级 |
| 粘度 | ✅ | ❌ |
| 比热 | ✅ | ✅ |
| 水溶液 | ❌ | ✅ (`rkt/aq/`) |
| 数据库 | 内置 Helmholtz EOS | Supcrt98 (HKF) |
| 速度 | 快 | 较慢（平衡求解） |

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
- `zmlx.reactions`：化学反应涉及流体组分（气体、液体、固体水合物等）
- `zmlx.demos`：demo 案例中大量使用 `create_h2o()`、`create_ch4()` 等
