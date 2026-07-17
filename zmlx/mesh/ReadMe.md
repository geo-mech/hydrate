# zmlx.mesh — 三角网格生成与处理

## 概述

`zmlx.mesh` 提供三角形网格的创建、加载和处理功能。支持 Delaunay 三角剖分、结构化分层网格、极坐标环形网格、圆形区域网格生成，以及网格文件的加载和保存。

---

## 快速开始

```python
from zmlx import *

# 方法1：结构化分层网格（矩形区域）
mesh = layered_triangles(
    x_min=0, x_max=100, nx=20,   # x 方向 20 份
    y_min=0, y_max=50, ny=10,    # y 方向 10 份
    as_mesh=True,                # 返回 Mesh3 对象
)

# 方法2：Delaunay 三角剖分（从点集）
from zmlx.mesh.triangle import get_triangles
nodes = [(0, 0), (1, 0), (0, 1), (1, 1), (0.5, 0.5)]
triangles = get_triangles(nodes)

# 方法3：从文件加载网格
from zmlx.mesh.io import load_trimesh
mesh = load_trimesh('nodes.txt', 'triangles.txt')

# 方法4：圆形区域网格
from zmlx.mesh.triangle_mesh_in_circle import generate_circle_mesh_improved
verts, tris = generate_circle_mesh_improved(r=10, l=2)
analyze_mesh_quality(verts, tris)  # 网格质量分析
```

---

## 主要模块

### `triangle.py` — 核心三角剖分

| 函数 | 描述 |
|------|------|
| `get_triangles(nodes)` | Delaunay 三角剖分（scipy.spatial），返回三角形索引列表，自动过滤退化三角形 |
| `layered_triangles(x_min, x_max, nx, y_min, y_max, ny, as_mesh)` | 矩形区域结构化三角网格。支持 y 方向拉伸使网格更均匀。可选返回 `Mesh3` 对象 |
| `mesh3_from_triangles(faces, nodes, i_beg)` | 将三角形数据和节点坐标转换为 `Mesh3` 对象 |

### `polar.py` — 极坐标环形网格

| 函数 | 描述 |
|------|------|
| `create_ring(vr, angle_step, z)` | 创建极坐标环形网格。`vr` 为径向节点位置列表，`angle_step` 为角度步长 |

### `triangle_mesh_in_circle.py` — 圆形区域网格

| 函数 | 描述 |
|------|------|
| `generate_circle_mesh_improved(r, l, center, use_kdtree)` | 改进型圆形网格生成器。边界均匀布点 + 内部随机布点 + Lloyd 松弛优化 |
| `generate_circle_mesh_hexagonal(r, l, center)` | 六边形晶格圆形网格（更均匀的布点） |
| `analyze_mesh_quality(vertexes, triangles)` | 网格质量分析：边长统计、长宽比、角度分布、面积 |
| `generate_mesh_quality_report(...)` | 打印结构化质量报告（含警告） |
| `plot_mesh_with_quality(...)` | 网格可视化 + 边长直方图 |

### `io.py` — 文件加载

| 函数 | 描述 |
|------|------|
| `load_trimesh(node_file, triangle_file, i_beg, encoding)` | 从两个文本文件加载三角网格：节点文件和三角形索引文件 |

---

### 结构化网格（`_rect.py`, `_cube.py`）

| 函数 | 描述 |
|------|------|
| `create_rect_mesh(xs, ys, z)` | 二维矩形网格（Node/Link/Face，无 Body）。支持 list/tuple/numpy |
| `create_cube_mesh(xs, ys, zs)` | 三维长方体网格（Node/Link/Face/Body）。相邻单元共享面自动去重 |

### 网格过滤与清理（`_filter.py`, `_clean.py`）

| 函数 | 描述 |
|------|------|
| `filter_mesh(mesh, keep)` | 按 keep(x,y,z) 保留元素，返回新 Mesh3 |
| `remove_orphan_faces(mesh)` | 去除不隶属于任何 Body 的 Face |
| `remove_orphan_links(mesh)` | 去除不隶属于任何 Face 的 Link |
| `remove_orphan_nodes(mesh)` | 去除不隶属于任何 Link 的 Node |

---

## 模块列表

| 模块 | 描述 |
|------|------|
| `_rect.py` | 二维矩形结构化网格（Node/Link/Face） |
| `_cube.py` | 三维长方体结构化网格（Node/Link/Face/Body） |
| `_filter.py` | 按位置函数过滤网格 |
| `_clean.py` | 清理孤立元素（Face/Link/Node） |
| `triangle.py` | 核心三角剖分算法：Delaunay 和结构化分层网格 |
| `io.py` | 网格文件加载 |
| `polar.py` | 极坐标环形网格生成 |
| `triangle_mesh_in_circle.py` | 圆形区域网格生成与质量分析 |

---

## 与其他模块的关系

- `zmlx.exts.Mesh3`：本模块生成的网格以 `Mesh3` 形式输出
- `zmlx.seepage_mesh`：Seepage 计算网格（立方体/圆柱体）与此处的三角网格不同
- `zmlx.plt`：三角网格可视化（`show_trimesh`）
- `zmlx.geometry`：几何计算（三角形面积、交点等）与本模块互补
