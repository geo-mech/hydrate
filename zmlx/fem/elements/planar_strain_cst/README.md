# Planar Strain CST 平面应变三角形单元

平面应变常应变三角形单元 (Constant Strain Triangle, Plane Strain)。

## 基本信息

- **节点数**: 3
- **自由度**: 6（每个节点2个平动自由度 u, v）
- **应变状态**: 常应变（单元内应变为常量）
- **适用场景**: 厚度方向尺寸远大于面内尺寸的结构（如大坝、隧道截面）

## 文件说明

| 文件 | 功能 |
|------|------|
| `_stiffness.py` | 计算单元刚度矩阵（6×6） |
| `_strain.py` | 计算单元应变向量 (3,)：[ε_xx, ε_yy, γ_xy] |
| `_stress.py` | 计算单元应力向量 (3,)：[σ_xx, σ_yy, τ_xy] |


## 平面应变 D 矩阵

$$D = \frac{E}{(1+\mu)(1-2\mu)} \begin{bmatrix} 1-\mu & \mu & 0 \\ \mu & 1-\mu & 0 \\ 0 & 0 & \frac{1-2\mu}{2} \end{bmatrix}$$
