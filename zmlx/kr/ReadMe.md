# zmlx.kr — 相对渗透率模块

## 概述

`zmlx.kr` 提供多孔介质多相流模拟中的相对渗透率（Relative Permeability）曲线生成函数。支持气-水两相和油-气-水三相的相对渗透率模型，以及裂缝相对渗透率和水合物占据孔隙空间时的渗透率折减计算。

**核心模型**：
- **Corey/Stone 模型**：气-水两相相对渗透率
- **Stone 模型 I**：油-气-水三相相对渗透率（Aziz & Settari, 1979）
- **立方定律**：裂缝相对渗透率
- **临界饱和度模型**：水合物占据孔隙时的渗透率折减

---

## 快速开始

```python
from zmlx import *

# 方法1：创建两相相对渗透率曲线（推荐）
kr = create_kr()                        # 默认参数
kr = create_kr(srg=0.02, srw=0.2,       # 自定义残余饱和度
               ag=3.5, aw=4.5)          # Corey 指数

# 方法2：创建折减系数（水合物占据孔隙）
krf = create_krf(faic=0.2, n=2.0)      # 临界饱和度比 + 指数

# 方法3：裂缝相对渗透率（立方定律）
fracture_kr = create_fracture_kr()     # 开度³

# 方法4：三相 Stone 模型 I
from zmlx.kr.stone_model_I import stone_model_I
sw, krw, sg, krg, so, kro = stone_model_I(
    swir=0.2, sorg=0.2, sorw=0.2, sgc=0.05,
    krwro=0.6, kroiw=0.8, krgro=0.6,
    nw=4.0, nsorw=2.0, ng=3.0, nog=2.0
)
```

---

## 主要函数

### `base.py` — 核心函数

| 函数 | 描述 | 返回 |
|------|------|------|
| `create_kr(srg, srw, ag, aw, count)` | Stone 模型气-水两相相对渗透率 | `(vs, kg, kw)` 饱和度、气相 kr、水相 kr |
| `create_krf(faic, n, as_interp, k_max, s_max, count)` | 水合物折减系数（临界饱和度模型） | `(x, y)` 或 `Interp1` 插值器 |
| `create_fracture_kr()` | 裂缝相对渗透率（立方定律） | `(vs, kr)` 开度、相对渗透率 |

**create_kr 参数说明**：
- `srg`：残余气相饱和度（默认 0.02）
- `srw`：残余水相饱和度（默认 0.2）
- `ag`：气相 Corey 指数 [1.0, 6.0]（默认 3.5）
- `aw`：水相 Corey 指数 [1.0, 6.0]（默认 4.5）

**create_krf 参数说明**：
- `faic`：临界孔隙度比 [0, 0.98)（默认 0.2）
- `n`：折减指数 [1, 10]（默认 2.0）

### `stone_model_I.py` — 三相 Stone 模型

| 函数 | 描述 |
|------|------|
| `stone_model_I(swir, sorg, sorw, sgc, krwro, kroiw, krgro, nw, nsorw, ng, nog)` | 归一化 Stone 模型 I（Aziz & Settari, 1979），含 Fayers & Matthews (1984) 残余油处理 |

### `Stone_model.py` — 简单两相模型

| 函数 | 描述 |
|------|------|
| `stone(sirg, sirw)` | 气-水两相 kr，NumPy 数组输出（形状 N×3） |

---

## 曲线参数说明

### Stone 模型（Corey 型指数函数）

```
krg = ((s - srg) / (1 - srw))^ag     （当 s > srg）
krw = ((s - srw) / (1 - srw))^aw     （当 s > srw）
```

### 水合物折减模型

当水合物占据部分孔隙空间时，流体的有效渗透率降低：
- 饱和度低于临界值（`faic`）：渗透率为 0
- 高于临界值：按指数规律恢复

---

## 模块列表

| 模块 | 描述 |
|------|------|
| `base.py` | 核心：`create_kr`、`create_krf`、`create_fracture_kr` |
| `stone_model_I.py` | 油-气-水三相 Stone 模型 I |
| `Stone_model.py` | 简单的两相 kr 生成 |

---

## 与其他模块的关系

- `zmlx.exts.Interp1`：相对渗透率曲线以 Interp1 插值器形式使用
- `zmlx.tfc`：在 `tfc.create()` 中通过 `kr` 参数设置相对渗透率
- `zmlx.demo`：多相流 demo（如 `oil_prod.py`、`gas_mig.py`）中使用 create_kr
