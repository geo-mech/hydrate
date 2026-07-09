# Planar Stress CST 平面应力三角形单元

平面应力常应变三角形单元 (Constant Strain Triangle, Plane Stress)。

## 基本信息

- **节点数**: 3
- **自由度**: 6（每个节点2个平动自由度 u, v）
- **应变状态**: 常应变（单元内应变为常量）
- **适用场景**: 薄板结构的面内应力分析（如薄壁容器、板壳结构）

## 文件说明

| 文件 | 功能 |
|------|------|
| `_stiffness.py` | 计算单元刚度矩阵（6×6） |
| `_strain.py` | 计算单元应变向量 (3,)：[ε_xx, ε_yy, γ_xy] |
| `_stress.py` | 计算单元应力向量 (3,)：[σ_xx, σ_yy, τ_xy] |


## 平面应力 D 矩阵

$$D = \frac{E}{1-\mu^2} \begin{bmatrix} 1 & \mu & 0 \\ \mu & 1 & 0 \\ 0 & 0 & \frac{1-\mu}{2} \end{bmatrix}$$
