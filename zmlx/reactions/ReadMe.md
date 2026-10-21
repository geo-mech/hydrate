# zmlx.reactions — 化学反应模块

## 概述

`zmlx.reactions` 用**一个统一的字典格式**定义反应方程式、平衡温度、反应速率和热量，
再交给 `add_reaction()` 挂到 `Seepage` 模型上。水合物分解/生成、融化/冻结、蒸发/凝结、
溶解、吸热分解、燃烧都是这套格式的实例。

**核心设计**：`endothermic.create()` 是**唯一**的底层构建块 —— 其它反应工厂（`hydrate` /
`melt` / `freeze` / `decomposition` / `combustion` …）都只是把它包装一层，换掉反应物、
生成物和曲线。所以理解了一个字典，就理解了整个包。

⚠️ 本包**不做化学平衡求解**（没有活度、没有物种形态、没有矿物饱和指数）。化学反应只有
一种建模方式：**"平衡温度 + 温度驱动的速率曲线"**，详见下文〈反应速率模型〉。若需要真正的
地球化学平衡 / 动力学（活度、矿物组合、Arrhenius），请看 `zmlx.fluids.rkt`（Reaktoro 绑定）。

---

## 快速开始

```python
from zmlx import *

# 1. 反应列表：每个元素是一个配置 dict（不是 Seepage.Reaction 对象）
reactions = [
    # 甲烷水合物分解/生成：平衡曲线、水合数、离解热都由模块内置
    ch4_hydrate.create(gas='ch4', wat='h2o', hyd='ch4_hydrate'),
    # 水 ↔ 冰：熔点/潜热内置
    h2o_ice.create(flu='h2o', sol='h2o_ice'),
]

# 2. 一条反应也可以手写（字段含义见下文〈反应参数说明〉和〈反应速率模型〉）
custom = {
    'name': 'my_reaction',
    'components': [
        {'kind': 'a', 'weight': -1.0},              # 左侧：反应物，权重取负
        {'kind': 'b', 'weight': 0.8},               # 右侧：生成物，权重取正
        {'kind': 'c', 'weight': 0.2},
    ],
    'temp': 280.0,                                  # 参考温度 K
    'heat': -4.0e5,                                 # ⚠️ 负值 = 吸热（J/kg，见下文）
    'p2t': ([0.01e6, 100e6], [278.0, 285.0]),       # 压力 → 平衡温度
    't2q': ([-10, 0, 10], [-1e-6, 0, 1e-6]),        # 偏离平衡温度 → 反应速率
}

# 3. 建模型时直接用 reactions= 挂上（推荐）
model = tfc.create(
    mesh, porosity=0.3, p=10e6, temperature=280, s={'h2o': 1}, perm=1e-14,
    fludefs=[create_h2o(name='h2o'), create_ch4(name='ch4'),
             create_ch4_hydrate(name='ch4_hydrate'), ...],
    reactions=reactions,
    has_solid=True,
)
```

模型**已经建好**时，用 `add_reaction(model, data)` 逐条追加：

```python
add_reaction(model, ch4_hydrate.create(gas='ch4', wat='h2o', hyd='ch4_hydrate'))
```

> 上面的示例经实测可运行（反应字典 → `tfc.create(reactions=...)` → `model.reaction_number`
> 正确增加）。组分名会在 `add_reaction()` 里按模型已注册的 `fludef` **名字**解析，所以
> `fludefs` 必须先于 `reactions` 给出 —— `tfc.create()` 内部就是这个顺序。

### 常用的现成配方

| 想要 | 用 |
|------|-----|
| 甲烷 / CO₂ 水合物 | `ch4_hydrate.create(...)` / `co2_hydrate.create(...)` |
| 水 ↔ 冰 | `h2o_ice.create(flu='h2o', sol='h2o_ice')` |
| 水 ↔ 汽（真空/亚临界，Antoine 饱和蒸气压） | `vapor.create(vap='steam', wat='h2o')` |
| 气体/盐溶于液相 | `dissolution.create(sol=…, sol_in_liq=…, liq=…, ca_sol=…)` |
| 不可逆吸热分解（裂解） | `decomposition.create(left=…, right=[…], temp=…, heat=…, rate=…)` |
| 盐度对水合物平衡温度的影响 | 抑制剂 `c2t=salinity.data`，见〈抑制剂系统〉 |
| 完整的物理—化学场景 | 直接用 `zmlx.scen.hydrate` / `zmlx.scen.icp`（那里已组装好整套反应） |

---

## 反应类型

### 反应工厂

| 模块 | 函数 | 描述 |
|------|------|------|
| `endothermic.py` | `create(left, right, temp, heat, rate=None, fa_t=None, fa_c=None, l2r=True, r2l=True, p2t=None, t2q=None, inhibitors=None)` | **底层构建块**：左侧 → 右侧吸热。`l2r` / `r2l` 开关正/逆向 |
| `hydrate.py` | `create(gas, liq, hyd, mg, vp, vt, temp, heat, …, dissociation=True, formation=True)` | 水合物：固体 ↔ 气体 + 液体（`left=[(hyd,1)]`，`right=[(gas,mg),(liq,1−mg)]`）|
| `melt.py` | `create(sol, flu, temp, heat, fa_t=None, fa_c=None, vp=None, vt=None, t2q=None, l2r=True, r2l=True)` | 融化 / 升华 / 汽化：固体 → 流体 |
| `freeze.py` | `create(flu, sol, vp, vt, temp, heat, …)` | 冻结 / 凝结：`melt` 的包装，**方向取反**，`t2q` 也取反 |
| `dissolution.py` | `create(*, sol, sol_in_liq, liq, ca_sol, rate=1.0, …)` | 溶解（可逆），溶解度取 Cell 属性 `ca_sol`（质量分数），**与 T、P 无关** |
| `decomposition.py` | `create(left, right, temp, heat, rate, …)` | 不可逆吸热分解（`r2l=False`）|
| `combustion.py` | `create(left, right, temp, heat, rate, …)` | 燃烧：超过燃点才发生（实验性，仅冒烟测试过）|

⚠️ `melt.create()` 内部的 `rate` **写死为 1.0**，不接受调用方传 `rate`；要调速率，
只能自己构造 `t2q` 或直接用 `endothermic.create()`。`hydrate.create()` 的 `rate`
参数只有在 `t2q` 未给时生效（两者同时给时 `t2q` 优先）。

### 物理常数模块（返回配置 dict）

| 模块 | 内容 |
|------|------|
| `ch4_hydrate.py` | 平衡曲线取自 TOUGH+ Hydrate 手册（45 点，148.7 K → 320.2 K）；`nh=6.0`、`mg≈0.129`、离解热 ≈ 437 kJ/kg；附 `get_p(t)` / `get_t(p)` / `create_p2t()` |
| `co2_hydrate.py` | 曲线来自 Anderson (2003) 与 Zhou et al. (2008)；`nh=5.75`、`mg≈0.298`、离解热 ≈ 406.5 kJ/kg |
| `h2o_ice.py` | 水 ↔ 冰：`temp=273.15 K`、`heat=336000 J/kg` |
| `CaOH2_deshydra.py` | Ca(OH)₂ ↔ CaO + H₂O（热化学储能），ΔH = 104.4 kJ/mol |
| `h2o_gl_kpa/` | 低气压（~1 kPa 量级、三相点附近）水汽 ↔ 水，数据表驱动 |
| `h2o_ls_kpa/` | 同上，水 ↔ 冰 |
| `alpha/salinity.py` | 盐度 0–0.2 对甲烷水合物平衡温度的偏移（**只导出 `data = (vs, vt)`**）|
| `alpha/co2_liq_lyx.py` | ⚠️ CO₂ 气液曲线**目前只定义在 `if __name__ == '__main__'` 里**，`import` 什么都拿不到 |

⚠️ `h2o_gl_kpa` / `h2o_ls_kpa` 与 `alpha` **不会**随 `from zmlx.reactions import *` 出现，
必须走完整路径导入：`from zmlx.reactions.h2o_gl_kpa import create`。

---

## 反应速率模型（理解本包的关键）

反应本身不"算"化学平衡，而是把一个 Cell 的**实际温度**和一条**平衡温度曲线**比较，
温差越大反应越快。`Seepage.Reaction` 的 docstring 给出了完整 10 步流程，摘要如下：

```
1. T0 = p2t(压力)                       ← 该压力下的平衡（基准）温度
2. T0 += c2t(抑制剂浓度)                ← 每个 Inhibitor 的平衡温度修正
3. T0 += idt(单元属性) × wdt            ← 按单元逐个修正（如局部盐度、固体占比）
4. dT  = T(cell) − T0
5. q  = t2q(dT)                         ← 正向速率
   qr = t2qr(dT)                        ← 逆向速率（通常不给，等价于 0）
6. q  *= c^exp ;  qr *= c^exp_r         ← 抑制剂的浓度指数修正
7. Q  = q − qr
8. Q += c2q(抑制剂浓度)                 ← 抑制剂对速率的直接加成
9. Q *= irate(单元属性)                 ← 单元级总倍率（如注入井局部强化）
10. 按 Q 消耗左侧、生成右侧，并按 heat 交换热量
```

两个必须记住的语义：

- **速率 `rate` 的单位很特殊**：按 `Seepage.Reaction` 的定义，它是"**每秒**生成/消耗的
  质量，**除以**该 Cell 内参与本反应的组分**质量之和**"，即"每秒反应掉全部相关质量的
  多少"。和常见的 kmol/(m³·s) 动力学速率不是一回事。
- **`t2q` 是插值曲线**：缺省时 `endothermic` 只给 `[−1e3, 0, 1e3]` 三个点、线性插值，
  所以"温度一旦越过阈值，速率就基本等于 `rate`"，对温度**极不敏感**。
  若要模拟 Arrhenius 型动力学（如裂解、煅烧），必须自己给一条**足够密**的 `t2q` 曲线。

---

## 抑制剂系统

抑制剂（Inhibitor）是实现"盐度降低水合物平衡温度""固体占比过高时抑制继续结晶"
这类**非温度因素**的通用机制 —— 它读一个组分（或固体）的浓度，输出平衡温度偏移
（`c2t`）和速率修正（`c2q` / `exp` / `exp_r`）。

有两条路，**推荐第一条**：

```python
from zmlx.reactions import add_inh
from zmlx.reactions.alpha.salinity import data as salinity_c2t

r = ch4_hydrate.create(gas='ch4', wat='h2o', hyd='ch4_hydrate')
add_inh(r, sol='inh', liq='liq', c2t=salinity_c2t)        # 盐度 → 平衡温度偏移
add_inh(r, sol='sol', liq=None,                           # 固体占比 → 抑制继续生成
        c2t=[[0, 0.8, 1.0], [0, 0.0, -200.0]], use_vol=True)
```

- `sol` / `liq`：溶质与溶剂的组分名（或 ID）。浓度 = `sol 质量 / liq 质量`；
  `use_vol=True` 时按体积分数计算。
- `c2t`、`c2q`：`(x列表, y列表)` 形式的插值曲线。
- `exp` / `exp_r`：正向 / 逆向速率的浓度指数（默认 0 = 不作用）。

第二条路是**在字典里直接写 `inhibitors` 列表**（`add_reaction` 会解析它）：

```python
from zmlx.reactions import create_inh

r['inhibitors'].append(create_inh('inh', 'liq', c2t=salinity_c2t))
```

⚠️ `add_inhibitor(...)` 以及 `create_inh` 的 `c=` / `t=` 参数**已弃用**（导入即
`DeprecationWarning`）：请统一用 `add_inh(...)` 与 `c2t=(c, t)`。

真实的组合方式见 `zmlx/scen/hydrate/_react.py` 与 `zmlx/scen/icp/_react.py`。

---

## 核心 API

| 函数 | 位置 | 描述 |
|------|------|------|
| `add_reaction(model, data, need_id=False)` | `alg.py` | **主入口**：`data` 是配置 dict 或已是 `Seepage.Reaction`；返回反应对象（或 ID）|
| `load_reactions(option, folder)` | `alg.py` | 从 JSON / 文件批量读配置（`option` 可以是文件名、文件名列表、dict）|
| `add_inh(r, sol, liq, *, c2t=None, c2q=None, exp=None, exp_r=None, use_vol=False)` | `inh.py` | 给配置 dict 追加一个抑制剂，直接修改 `r['inhibitors']` |
| `create_inh(sol, liq, …)` | `inh.py` | 只**构造**抑制剂 dict（不追加），需要自己 `append` |
| `create_reaction(model, **opts)` | `alg.py` | ⚠️ **已弃用**（导入即告警）：且要求 `**opts` 用 `components=` 形式，和 `endothermic` 的 `left/right` 调用方式**不同**；请改用 `add_reaction` |

`create_reaction` 与 `add_reaction` 的区别只在组装方式：前者按 `components=` 逐个给出
`{kind, weight, fa_t, fa_c}`（权重左侧负、右侧正），后者吃的是工厂产出的 `left/right` 字典。
**新代码一律用 `add_reaction()`。**

---

## 反应参数说明

每个反应就是一个 dict（`endothermic.create()` 的返回值），字段如下：

| 字段 | 说明 |
|------|------|
| `components` | 组分列表 `[{'kind': 名字或ID, 'weight': 权重, 'fa_t': …, 'fa_c': …}, …]`；**左侧权重为负、右侧为正**，同一侧权重之和的绝对值为 1 |
| `temp` | 参考温度 (K)。`heat` 即在此温度下的值；未给 `p2t` 时也作为所有压力下的平衡温度 |
| `heat` | ⚠️ **发生 1 kg 反应所"释放"的热量 (J/kg)，负值表示吸热**。`endothermic.create()` 内部对输入取负号：工厂接口传 `heat>0` 表示吸热，手写字典时要写 `heat<0` |
| `p2t` | `(压力列表, 温度列表)`，压力 → 平衡温度曲线；未给则退化为常数 `temp` |
| `t2q` | `(dT列表, 速率列表)`，平衡温度偏移 → 正向速率；至少 3 个点。缺省时是 `[−1e3, 0, 1e3]` 的线性斜率 |
| `t2qr` | 同上，逆向速率（通常留空）|
| `inhibitors` | 抑制剂列表，见上节 |
| `idt` / `wdt` / `irate` | 单元级修正：`idt` 为 Cell 属性（名或 ID），参与 `T0 += idt × wdt`；`irate` 为速率倍率 |
| `fa_t` / `fa_c` | 流体的温度 / 比热属性名（默认 `'temperature'` / `'specific_heat'`），一般无需显式给 |

> `name` 不是工厂函数的参数；需要命名时在 `add_reaction()` 之后设置，或直接构造
> `Seepage.Reaction` 再添加。

---

## TOUGHREACT 集成

⚠️ **TOUGHREACT 集成尚未完成。** `tough_react/` 里是**研究脚本的集合，不是可直接调用的
接口**，多数脚本在 `import` 时就会失败或需要本地数据文件：

| 模块 | 现状 |
|------|------|
| `thermo_loader.py` | ❌ **导入即失败**：模块顶层直接 `open('thermo_data.tdat')`，没有函数封装 |
| `Single_react.py` / `Multiple_react.py` / `Kf_Kr.py` / `Kf_Kr_interpolation.py` | ⚠️ 解析 `.tdat` 块后做 Arrhenius / lnK–1/T 拟合，但需要本地数据文件路径；四者代码高度重复（同一套 `extract_reaction_blocks`）|
| `react0611.py` | ⚠️ 仅有一个 `build_reaction()` 式的实验脚本入口 |
| `co2_react.py` | ⚠️ 面向场景的脚本：建网格 + CO₂ 注入模型 + 调 `create_reaction` 塞入 CaCO₃ 反应；依赖 `"reaction data/"` 下的数据文件，失败时只打印一条告警 |
| `reaction.py` / `__init__.py` | 空模块（只有 docstring）|

**结论**：目前**没有任何**经过测试的、把 TOUGHREACT 热力学数据库接进 zmlx 反应系统的通路。
需要地球化学建模时，优先考虑 `zmlx.fluids.rkt`（Reaktoro）；等 `tough_react/` 整理成
"加载数据库 → 输出标准反应 dict"的正式接口后，再回到本节更新说明。

⚠️ 旧路径 `zmlx.react.tough_react.*` 只是改名兼容垫片（导入即 `DeprecationWarning`，
2027-10-16 删除）。

---

## 模块列表

| 模块 | 说明 |
|------|------|
| `alg.py` | `load_reactions` / `add_reaction` /（弃用）`create_reaction` / 内部 `__add_inhibitor` |
| `inh.py` | `create_inh` / `add_inh` |
| `endothermic.py` | 底层吸热反应工厂 |
| `hydrate.py` | 水合物反应工厂 |
| `melt.py` / `freeze.py` | 融化 / 冻结（互为反向）|
| `vapor.py` | 水 ↔ 汽（Antoine 曲线；另有 `get_heat_need(water_t, steam_t)` 估算总能耗）|
| `dissolution.py` | 溶解 |
| `decomposition.py` | 不可逆吸热分解 |
| `combustion.py` | 燃烧（实验性）|
| `ch4_hydrate.py` / `co2_hydrate.py` | 甲烷 / CO₂ 水合物常数与工厂 |
| `h2o_ice.py` | 水 ↔ 冰 |
| `CaOH2_deshydra.py` | Ca(OH)₂ 脱水 / CaO 水合 |
| `h2o_gl_kpa/` / `h2o_ls_kpa/` | 低气压（三相点附近）的水汽/水、水/冰相变 |
| `alpha/` | 盐度效应、CO₂ 气液曲线（`co2_liq_lyx` 暂不可用）|
| `tough_react/` | TOUGHREACT **研究脚本**（未完成，见上节）|
| `__Trash/` | 归档的旧 CO₂ 水合物数据（`co2_phase_data.py`，同样是"只有 `__main__` 里有东西"），不要引用 |

---

## 与其他模块的关系

- `zmlx.exts.Seepage.Reaction`：底层反应对象，字段与 docstring 定义速率语义
- `zmlx.fluids`：反应涉及流体的物性（组分以**名字**或 ID 在反应里引用）
- `zmlx.tfc`：`tfc.create(reactions=…)` 建模型时挂反应；`iterate()` 中执行反应计算
- `zmlx.scen.hydrate` / `zmlx.scen.icp`：已经组装好的完整反应集合（水合物、冰、蒸汽、溶解…）
- `zmlx.fluids.rkt`：需要活度 / 矿物平衡 / Arrhenius 动力学时使用（与本源反应系统相互独立）
- 旧包名 `zmlx.react`：兼容垫片，导入即 `DeprecationWarning`，**2027-10-16 删除**
