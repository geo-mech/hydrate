# zmlx.exts — C++ 核心绑定层

## 概述

`zmlx.exts` 是 `zmlx` 的 **C++ 扩展绑定层**，通过 `ctypes` 封装 `zml.dll`（Windows）或 `zml.so`（Linux）中导出的 C++ 函数和类。本模块是 zmlx 所有功能的基石——上层的渗流、传热、化学、力学计算全部依赖于此。

**核心理念**：一个 DLL 导出函数对应一个 Python 函数。`exts` 中不定义任何复杂操作，仅提供透明的、最小的接口封装。所有操作细节在 Python 层面应可见，以保证可维护性。

**作者**：张召彬 <zhangzhaobin@mail.iggcas.ac.cn>，中国科学院地质与地球物理研究所。

---

## 核心数据结构

### `Seepage` — 多相渗流模型
- 位置：`_seepage.py`
- 描述：zmlx 中最核心的数据结构，存储所有 Cell（网格单元）、Face（面连接）、流体数据和迭代状态。
- 关联类型：`Cell` / `CellData`、`Face` / `FaceData`、`FluData`、`FluDef`、`Injector`、`Reaction`、`FlowSol`、`ThermalSol`
- 辅助函数：`calc_recommended_dt` — 基于 CFL 条件推荐时间步长

### `Mesh3` / `SeepageMesh` — 网格
- 位置：`_mesh.py`
- 描述：`Mesh3` 是通用 3D 网格（节点、连接、面、体），`SeepageMesh` 是面向渗流计算的优化网格（Cell + Face）。
- 关联类型：`Groups`（索引分组）、`ElementMap`（网格间数据映射）

### `DynSys` — 动力学系统
- 位置：`_dyn.py`
- 描述：弹簧-质点-阻尼器动力学系统，用于固体变形和应力波传播模拟。基于稀疏矩阵和共轭梯度求解。

### `Dfn2` / `Lattice3` / `FractureNetwork` — 裂缝网络
- 位置：`_frac.py`
- 描述：`Dfn2` 生成 2D 离散裂缝网络，`Lattice3` 为 3D 空间网格，`FractureNetwork` 管理裂缝网络，`DDMSolution2` 实现 2D 位移间断法。

### `InvasionPercolation` — 侵入逾渗
- 位置：`_ip.py`
- 描述：孔隙尺度的多相驱替模拟，包含 `NodeData`、`BondData`、`Injector`、`InvadeOperation`。

### `Thermal` — 纯热传导模型
- 位置：`_seepage.py`
- 描述：独立的纯热传导求解器，与 Seepage 中的流-热耦合区分。

---

## 基础类型

### 向量与数组
| 类型 | 位置 | 描述 |
|------|------|------|
| `Vector` | `_vec.py` | `std::vector<double>`，支持序列化、numpy 互操作、切片 |
| `IntVector` | `_vec.py` | `std::vector<int>` |
| `UintVector` | `_vec.py` | `std::vector<unsigned int>` |
| `StrVector` | `_vec.py` | `std::vector<std::string>` |
| `Array2` ~ `Array6` | `_ary.py` | 固定大小数组（2~6 维），用于坐标、颜色等 |

### 张量与矩阵
| 类型 | 位置 | 描述 |
|------|------|------|
| `Tensor2` | `_tensor.py` | 2D 二阶张量（xx, yy, xy） |
| `Tensor3` | `_tensor.py` | 3D 二阶张量（xx, yy, zz, xy, xz, yz），支持特征值计算 |
| `Matrix2` / `Matrix3` | `_mat.py` | 2x2 / 3x3 矩阵 |
| `MatrixMN` | `_mat.py` | MxN 稀疏/稠密矩阵 |

### 插值与坐标
| 类型 | 位置 | 描述 |
|------|------|------|
| `Interp1` | `_interp.py` | 1D 分段线性插值 |
| `Interp2` | `_interp.py` | 2D 双线性插值 |
| `Interp3` | `_interp.py` | 3D 三线性插值 |
| `Coord2` / `Coord3` | `_coord.py` | 2D/3D 局部坐标系（原点 + 轴向量） |
| `Map` | `_map.py` | `std::map<string, double>` 封装 |

### 工具类
| 类型 | 位置 | 描述 |
|------|------|------|
| `LinearExpr` | `_lexpr.py` | 线性表达式求值器 |
| `ConjugateGradientSolver` | `_sol.py` | 共轭梯度法线性求解器（Eigen 后端） |
| `HasKeys` | `_hk.py` | 动态键-值属性存储（被 Cell/Face 用于用户定义属性） |
| `ThreadPool` | `_pool.py` | C++ 线程池封装，支持并行任务提交 |
| `Timer` / `clock` | `_timer.py` | 性能计时和函数计时装饰器 |
| `FileMap` | `_fmap.py` | 文件夹→单文件映射（无压缩） |
| `String` | `_str.py` | C++ 字符串封装 |

---

## 全局函数

### 信息与授权
| 函数 | 描述 |
|------|------|
| `about()` | 返回模块版本、编译器信息和授权状态 |
| `reg(code)` | 注册或查询机器序列号/授权数据 |
| `set_srand(seed)` / `get_rand()` | C++ 随机数生成器控制 |
| `get_time_compile()` | 返回 C++ 库编译时间戳 |
| `test_loop(count, parallel)` | 测试 C++ 循环性能 |
| `feedback(text, subject)` | 向作者发送诊断信息 |

### 文件与字符串
| 函数 | 描述 |
|------|------|
| `confuse_file(ipath, opath, password, is_encrypt)` | 文件混淆加密/解密 |
| `contain_chinese(string)` | 检查字符串是否含中文字符 |
| `get_average_perm(p0, p1, get_perm)` | 计算两点间平均渗透率（串联效应） |
| `run(fn)` | 在 DLL 内存检查上下文中执行函数 |

### 模板方法
```python
from zmlx.exts import about
print(about())
```

---

## 授权与许可

本软件的 C++ 核心需要授权文件方可使用。

- 学术用途：免费，需联系作者获取授权
- 商业用途：需联系作者
- 联系方式：zhangzhaobin@mail.iggcas.ac.cn

可通过 `reg()` 查询硬件序列号，发送给作者获取授权数据。

---

## 与其他模块的关系

```
zmlx/exts/          ← C++ DLL 绑定层（本模块）
    ↓
zmlx/tfc/           ← TFC 耦合引擎（基于 Seepage 构建）
zmlx/fluid/         ← 流体属性（基于 FluDef）
zmlx/react/         ← 化学反应（基于 Reaction）
zmlx/kr/            ← 相对渗透率（基于 Interp1）
zmlx/mesh/          ← 网格（基于 Mesh3 / SeepageMesh）
zmlx/geometry/      ← 几何计算（基于 Dfn2 等）
zmlx/alg/           ← 通用算法（独立）
```

**重要**：`exts` 是唯一与 C++ DLL 直接交互的模块。上层的所有物理、化学、可视化模块均通过本模块间接调用 C++ 功能。
