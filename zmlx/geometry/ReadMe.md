# zmlx.geometry — 几何计算模块

## 概述

`zmlx.geometry` 提供点、线段、三角形、矩形、离散裂缝网络（DFN）等几何对象的创建、分析和相交检测功能。用于渗流网格、裂缝网络建模和地质力学模拟中的几何计算。

---

## 快速开始

```python
from zmlx import *

# 点与向量
dist = get_distance(p1, p2)       # 两点距离
angle = get_angle(x, y)           # 角度（相对于 x 轴）
norm = get_norm(vector)            # 向量模长

# 线段
center = get_center(p1, p2)       # 中点
seg_angle = get_seg_angle(x0, y0, x1, y1)  # 线段角度
intersection = seg_intersection(ax, ay, bx, by, cx, cy, dx, dy)  # 线段相交
dist = seg_point_distance(seg, point)       # 点到线段距离

# 三角形
area = triangle_area(a, b, c)     # 三角形面积（三边长 → Heron 公式）

# 离散裂缝网络 (2D)
fractures = dfn2(
    xr=(-50, 50), yr=(-150, 50),  # 区域范围
    p21=1.0,                       # 裂缝密度 (m⁻¹)
    angles=[(0, 45), (45, 90)],   # 角度范围（两组）
    lengths=[(10, 30)],            # 长度范围
    l_min=5,                       # 最小裂缝长度
)

# 离散裂缝网络 (3D 垂直裂缝)
v3_fractures = dfn_v3(
    box=(-50, -150, -25, 50, 150, 25),
    p21=1.0, angles=[(0, 1.57)],
    lengths=[(10, 30)], heights=[(10, 50)],
)
```

---

## 主要函数

### 点与向量（`point.py`）

| 函数 | 描述 |
|------|------|
| `get_angle(x, y)` | 点的极角 `atan2(y, x)`，范围 [-π, π] |
| `get_norm(p)` | 欧几里得范数 |
| `get_center(*points)` | 多点质心 |
| `point_distance(p1, p2)` | 两点距离（别名：`get_distance`） |

### 线段（`segment.py`）

| 函数 | 描述 |
|------|------|
| `get_seg_angle(x0, y0, x1, y1)` | 线段方向角 |
| `get_center(p1, p2)` | 线段中点 |
| `seg_intersection(ax, ay, bx, by, cx, cy, dx, dy)` | 2D 线段-线段相交检测，返回交点坐标或 None |
| `seg_point_distance(seg, point)` | 点到线段的最短距离 |

### 三角形（`triangle.py`）

| 函数 | 描述 |
|------|------|
| `get_area(a, b, c)` | 三角形面积（Heron 公式，三边长） |
| `get_area_by_vertices(a, b, c)` | 三角形面积（顶点坐标，任意维度） |

### 3D 矩形（`rect_3d.py` / `rect_v3.py`）

支持两种表示法：
- **rc3（9 浮点数）**：中心 + 两个相邻边中点
- **v3（6 浮点数）**：两个对角顶点（垂直矩形，伪 3D）

| 函数 | 描述 |
|------|------|
| `from_v3(v3)` / `to_v3(rc3)` | rc3 ↔ v3 互转 |
| `get_cent(rc3)` | 矩形中心 |
| `get_area(rc3)` / `get_area(v3)` | 矩形面积 |
| `get_vertexes(rc3)` | 4 个角点坐标 |
| `intersected(a, b)` | v3 矩形相交检测（z 范围重叠 + 2D 投影相交） |
| `calculate_3d_rectangle_intersect(...)` | 3D 矩形-矩形相交检测，返回交线端点 |

### 离散裂缝网络（`dfn2.py` / `dfn_v3.py`）

| 函数 | 描述 |
|------|------|
| `dfn2(data, xr, yr, p21, ...)` | 2D 离散裂缝网络生成器 |
| `dfn_v3(data, box, p21, ...)` | 3D 垂直裂缝网络生成器 |
| `get_length(fracture)` | 裂缝长度 |
| `get_center(fracture)` | 裂缝中点 |
| `get_total_length(fractures)` | 裂缝总长度 |
| `create_links(fractures)` | 查找所有相交裂缝对 |
| `from_segs(segs, z_min, z_max, heights)` | 2D 线段→3D 垂直裂缝 |
| `save_c14(path, fractures)` | 保存为 14 列格式（MATLAB） |

---

## 模块列表

| 模块 | 说明 |
|------|------|
| `base.py` | 核心函数聚合（重新导出所有基本函数） |
| `point.py` | 点与向量运算 |
| `segment.py` | 线段运算与相交检测 |
| `triangle.py` | 三角形面积计算 |
| `rect_3d.py` | 3D 矩形（rc3 表示法）运算 |
| `rect_v3.py` | 垂直矩形（v3 表示法）相交检测 |
| `rect_3d_intersection.py` | 3D 矩形-矩形相交检测算法 |
| `dfn2.py` | 2D 离散裂缝网络生成 |
| `dfn_v3.py` | 3D 垂直裂缝网络生成 |

---

## 与其他模块的关系

- `zmlx.exts`：DFN 生成依赖 `Dfn2`，几何数据用于 `Mesh3`、`Seepage` 等网格结构
- `zmlx.alg`：部分几何函数（如 `dfn_v3`）在 `alg.frac` 中有重定向
- `zmlx.plt`：裂缝网络可视化（`show_dfn2`、`show_fn2`、`show_rc3`）
- `zmlx.demo`：DFN 相关的 demo 案例
