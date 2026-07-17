# zmlx.plt — Matplotlib 可视化工具集

## 概述

`zmlx.plt` 提供基于 matplotlib 的可视化绘图功能，组织为**三层架构**：

1. **`on_axes/`（底层）**：在 `Axes` 对象上绘制图元的 `add_xxx` 函数
2. **`on_figure/`（中层）**：Figure 级别操作（子图创建、布局计算）和 GUI 桥接
3. **`on_ui/`（高层）**：一键绘制并显示在 GUI 标签页的 `show_xxx` 函数

---

## 快速开始

```python
from zmlx import *

# 方法1：高层 show_xxx（直接显示在 GUI 中）
show_contourf(x, y, z, caption='压力分布')
show_xy(x_data, y_data, caption='生产曲线')
show_tricontourf(x, y, z, caption='不规则数据')

# 方法2：中层 plot_on_axes（控制 Axes 绘制）
def on_axes(ax):
    add_curve(ax, x, y, label='压力')
    add_legend(ax)
plot_on_axes(on_axes, caption='我的图表')

# 方法3：底层 add_xxx（完全控制）
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
add_contourf(ax, x, y, z, cbar={'label': '压力/Pa'})
add_curve(ax, x_data, y_data, 'r-')
plt.show()
```

---

## 底层绘图函数（on_axes）

所有函数以 `ax`（matplotlib Axes 对象）作为第一参数：

| 函数 | 描述 |
|------|------|
| `add_curve(ax, x, y, ...)` | 曲线图（别名：`add_curve2`、`curve`） |
| `add_contourf(ax, x, y, z, cbar, ...)` | 填充等值线图 |
| `add_tricontourf(ax, x, y, z, cbar, ...)` | 不规则数据三角等值线 |
| `add_trisurf(ax, x, y, z, cbar, ...)` | 3D 三角表面图 |
| `add_surf(ax, x, y, z, c, ...)` | 3D 曲面图（颜色映射） |
| `add_scatter(ax, ...)` | 散点图 |
| `add_legend(ax, ...)` | 图例 |
| `add_cbar(ax, title, cmap, clim, ...)` | 颜色条 |
| `add_dfn2(ax, dfn2, ...)` | 2D 离散裂缝网络 |
| `add_fn2(ax, pos, w, c, ...)` | 2D 裂缝网络（宽度+颜色映射） |
| `add_seepage_mesh(ax, mesh, ...)` | 3D 渗流网格可视化 |
| `add_rc3(ax, rc3, ...)` | 3D 矩形集合（裂缝可视化） |
| `add_field2(ax, f, xr, yr, ...)` | 2D 标量场（采样函数 f） |

---

## 中层绘图函数（on_figure）

| 函数/类 | 描述 |
|---------|------|
| `plot_on_figure(kernel, ...)` | 在 figure 上执行回调，自动显示在 GUI 中 |
| `plot_on_axes(on_axes, dim=2, ...)` | 创建 Axes 并执行回调 |
| `add_subplot(figure, on_axes, ...)` | 创建或复用子图 |
| `add_axes2(fig, ...)` | 创建 2D 子图（快捷方式） |
| `add_axes3(fig, ...)` | 创建 3D 子图（快捷方式） |
| `AutoLayout` | 自动子图布局管理器 |
| `calc_best_layout(num_plots, ...)` | 计算最佳子图布局 |
| `add_axes_img(fig, file_path)` | 显示图片（保持原始宽高比） |

---

## 高层绘图函数（on_ui）

一键创建标签页并显示图形：

| 函数 | 别名 | 描述 |
|------|------|------|
| `show_contourf(x, y, z, ...)` | `contourf` | 填充等值线图 |
| `show_tricontourf(x, y, z, ...)` | `tricontourf` | 不规则三角等值线 |
| `show_xy(x, y, ...)` | `plot_xy`, `plotxy` | 2D 线图（支持从文件加载） |
| `show_trisurf(...)` | `plot_trisurf` | 3D 三角表面 |
| `show_trimesh(...)` | `trimesh` | 2D 三角网格边线 |
| `show_scatter(...)` | | 2D/3D 散点图 |
| `show_dfn2(dfn2, ...)` | | 2D 离散裂缝网络 |
| `show_fn2(pos, w, c, ...)` | | 2D 裂缝网络 |
| `show_field2(f, xr, yr, ...)` | | 2D 标量场（网格采样） |
| `show_rc3(rc3, ...)` | | 3D 矩形集合（裂缝） |
| `show_flu_def(flu, pr, tr, ...)` | | 流体属性双面板展示 |

---

## 辅助工具

| 函数 | 位置 | 描述 |
|------|------|------|
| `get_cm(name, levels)` | `cmap.py` | 获取颜色映射表（默认 'coolwarm'） |
| `get_color(cmap, lr, rr, val)` | `cmap.py` | 将数值映射为 RGBA 颜色 |
| `set_chinese_font()` | `_font.py` | 配置 matplotlib 中文字体 |
| `plot_no_gui(kernel, fname, ...)` | `_plot.py` | 无 GUI 模式绘图（保存为文件） |
| `get_plt_save_path(*subdirs)` | `_save.py` | 获取图形保存路径 |

---

## 典型用法示例

### 在迭代过程中绘图

```python
def show(model):
    x = tfc.get_x(model, shape=(nx, nz))
    z = tfc.get_z(model, shape=(nx, nz))
    p = tfc.get_p(model, shape=(nx, nz))
    show_contourf(x, z, p, caption=f'压力 @ t={model.temps["time"]:.0f}s')

tfc.solve(model, extra_plot=show, time_forward=365*24*3600)
```

### 声明式绘图（使用 zmlx.fig）

```python
fig.show(
    fig.axes2(
        fig.contourf(x, y, p, cbar={'label': 'p/Pa'}),
        title='压力', xlabel='x/m', ylabel='y/m'
    ),
    caption='压力分布'
)
```

---

## 模块列表

| 模块 | 说明 |
|------|------|
| `on_axes/` | 底层 Axes 绘制函数（add_xxx） |
| `on_figure/` | 中层 Figure 操作和 GUI 桥接 |
| `on_ui/` | 高层一键绘图（show_xxx） |
| `cmap.py` | 颜色映射管理 |
| `_font.py` | 中文字体配置 |
| `_plot.py` | 无 GUI 模式绘图工具 |
| `_save.py` | 图形路径管理 |

---

## 与其他模块的关系

- `zmlx.ui`：`plot_on_figure` 和 `show_xxx` 函数通过 `zmlx.ui.plot` 在 GUI 标签页中显示
- `zmlx.tfc._plt`：内建 `show_cells()` 函数用于快速模型可视化
- `zmlx.fig`：更高层声明式绘图 API（`fig.axes2`、`fig.contourf` 等），plt 中部分函数已弃用并迁移至 fig
- `zmlx.exts`：绘图所需的 Mesh3、Seepage 等数据结构
