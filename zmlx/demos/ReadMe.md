# zmlx Demo 指南

本文件夹包含基于 `zmlx` 的完整建模示例。每个含 `# ** desc = '...'` 的脚本都可在 GUI 或命令行中直接运行。

## 快速开始

```bash
python zmlx/demos/flow_1ph/darcy_1d.py            # GUI 模式（默认）
python zmlx/demos/flow_1ph/darcy_1d.py --no-gui   # headless，图存到文件
```

入口固定写在 `if __name__ == '__main__'` 里的
`gui.execute(main, close_after_done=False)`（`--no-gui` 时 `gui.*` 调用自动变为空操作）。
`gui.execute` 的位置要求、`gui.break_point()` / `gui.progress()` / `gui.plot()` 等函数、
headless 与批量测试的细节见同级 `AGENTS.md`「运行与批量测试」和
`projects/zml/AGENTS.md`「GUI mode」。本文只讲**怎么写一个 demo**：建模 API、边界条件、
时间步进、可视化与常见陷阱。

---

## 目录结构与问题类型

各子目录的领域与常用 API 见同级 `AGENTS.md`「目录组织」——那份表是完整的（还含
`plt/`、`others/`、`tests/`、`gui_input/`、`debugging/`）。本文的例子主要来自
`flow_1ph/`、`flow_2ph/`、`hydrate/`、`thermal/` 四个目录。

---

## 建模方法

zmlx 提供两种建模方法，从底层到高层递进。建议优先使用高层方法，仅在需要精细控制时降至底层。

### 方法一：高层建模 — 使用 `tfc.create` 和专用场景模块

这是推荐的方法。通过定义网格和空间分布函数来创建完整模型。

```python
from zmlx import *

# 1. 创建网格
mesh = create_cube(
    x=linspace(0, 300, 61),      # x 方向 60 个格子
    y=(-0.5, 0.5),               # y 方向 1 层（二维化）
    z=linspace(-500, 0, 101)     # z 方向 100 个格子
)

# 2. 定义空间分布函数（闭包）
def get_k(x, y, z):  return 1.0e-14 if z > -300 else 1.0e-15   # 渗透率
def get_s(x, y, z):  return {'ch4': 0.5, 'h2o': 0.5}           # 初始饱和度

# 3. 调用高层创建函数
model = tfc.create(
    mesh, porosity=0.1, pore_modulus=100e6,
    temperature=280, p=10e6, s=get_s,
    perm=get_k, heat_cond=2.0,
    fludefs=[create_ch4(name='ch4'), create_h2o(name='h2o')],
    gravity=(0, 0, -10),
    dt_max=3600 * 24 * 365
)
```

专用场景模块进一步简化了特定问题（这里只示意调用形状，参数含义见各 demo）：

```python
model = hydrate.create(mesh, gravity=[0, 0, -10], porosity=get_fai, temperature=get_t,
                       p=get_p, s=get_s, perm=get_k, heat_cond=heat_cond,
                       prods=[{'index': ..., 'p': [3e6, 3e6]}],
                       dt_min=1, dt_max=24*3600, cfl=0.1)   # 水合物开发

model = icp.create(mesh, porosity=..., p=..., temperature=...,
                   injectors=[...], prods=[...])            # 原位转化
```

### 方法二：底层建模 — 手动构建 Cell 和 Face

适用于需要完全控制模型结构的场景（教学、简单验证）。

```python
model = Seepage()

# 手动添加 Cell
c = model.add_cell()
c.pos = [x, y, z]
c.set_pore(p=1e6, v=vol, dp=1e6, dv=vol * 0.1)
c.fluid_number = 1
c.get_fluid(0).vol = c.p2v(p)
c.get_fluid(0).vis = 1.0e-3

# 手动添加 Face（连接两个 Cell）
dist = get_distance(c0.pos, c1.pos)
face = model.add_face(i0, i1)
face.cond = area * perm / dist
```

**关键公式**：`face.cond = area * perm / dist`（导流系数），其中 `area` 为横截面积 (m²)，`perm` 为渗透率 (m²)，`dist` 为流动距离 (m)。

### 两种方法的对比

- **代码量**：高层少，底层多；高层由 mesh 自动生成 Face 并自动配置流体属性，边界条件函数式
  定义；底层需手动 `set_pore` / 设置流体 `vis`、`den`，手动建 Face 并手动设 Cell 属性。
- **适用场景**：一般建模用高层；教学、底层调试用底层。
- **参考 demo**：高层 `gas_mig.py`、`prod_v2.py`；底层 `darcy_1d.py`、`diffusion1.py`。

---

## 空间分布函数 — 核心建模范式

zmlx 的核心建模范式是"空间分布函数"：将渗透率、孔隙度、初始压力/温度/饱和度等定义为 `(x, y, z) → value` 的闭包函数。这些函数在模型创建时会被自动应用到每个 Cell。

### 模式一：分段函数（最常用）

```python
def get_k(x, y, z):
    """高渗储层 + 低渗盖层的组合"""
    if z > -30 or z < -70:        # 盖层和底层 → 低渗屏障
        return 1.0e-15
    else:                          # 储层 → 高渗
        return 1.0e-14

def get_s(x, y, z):
    """储层含水合物，其余区域纯水"""
    if z > -30 or z < -70:
        return {'h2o': 1}          # 纯水
    else:
        return {'h2o': 0.6, 'ch4_hydrate': 0.4}  # 40% 水合物
```

### 模式二：使用 `get_distance` 定义圆形/球形区域

```python
def is_gas_region(x, y, z):
    return get_distance([x, y, z], [center_x, center_y, center_z]) < radius

def get_s(x, y, z):
    if is_gas_region(x, y, z):
        return {'ch4': 1}          # 气源区
    else:
        return {'h2o': 1}          # 水饱和区
```

### 模式三：使用网格边界作为参考

```python
z_min, z_max = mesh.get_pos_range(2)  # 获取 z 方向范围

def is_upper(x, y, z):   return abs(z - z_max) < 0.01   # 顶边界
def is_lower(x, y, z):   return abs(z - z_min) < 0.01   # 底边界

def denc(*pos):
    """边界设为极大热容 → 恒温边界条件"""
    return 1e20 if is_upper(*pos) or is_lower(*pos) else 5e6
```

---

## 边界条件设置

zmlx 通过操作模型属性来设置边界条件，而非传统的"指定边界值"方式。

### 定压边界

**方法一**：把边界 Cell 的体积设为极大值（如 `1e6` m³），大体积意味着流动中压力几乎不变：

```python
c.set_pore(p=1e6, v=1e6, dp=1e6, dv=1e6 * 0.1)
```

**方法二**：把边界 Cell 的孔隙度设为极大值（如 `1e10`），效果相同：

```python
def get_fai(x, y, z):
    return 1.0e10 if is_upper(x, y, z) else 0.3   # 顶面定压
```

### 恒温边界

将边界 Cell 的热容（`denc` = 密度 × 比热）设为极大值（如 `1e20`）——完整写法见上面的
「空间分布函数 / 模式三」。

### 封闭边界

**无流动边界**：不添加任何 Face 连接该 Cell（或渗透率设为 0）。
**绝热边界**：不设置导热 Face（或 `heat_cond` 设为 0）。

### 井（注入/生产）

```python
# 注入井（注入速率 kg/s）
model.add_injector(cell=target_id, fluid_id=1, flu=injection_fluid, value=rate)

# 生产井（在 tfc.create/hydrate.create 中指定）
prods=[{'index': cell_index,
        't': [0, 1e20],          # 时间范围（始终开启）
        'p': [3e6, 3e6]}]        # 井底流压 3 MPa

# 电加热（纯热注入，功率 W）
model.add_injector(cell=target_id, ca_mc=model.get_cell_key('mc'),
                   ca_t=model.get_cell_key('temperature'), value=500)
```

### 虚拟 Cell/Face — 连接井到模型

`add_cell_face` 在指定位置创建一个虚拟的 Cell 和 Face，用于作为生产井或注入井的接口。

```python
# 在位置 (0, 0, -50) 创建虚拟连接，体积 1000 m³，面积 5 m²，长度 1 m
add_cell_face(mesh, pos=[0, 0, -50], offset=[0, 10, 0],
              vol=1000, area=5, length=1)
```

**重要**：虚拟 Cell 和 Face 会影响热传导。必须在虚拟 Face 附近将 `heat_cond` 设为 0，防止热量通过虚拟 Face 异常传导。

```python
def heat_cond(x, y, z):
    return 1.0 if abs(y) < 2 else 0.0   # 仅在井附近导热
```

---

## 时间步进

### 推荐方式：`tfc.solve`

```python
# 基本用法（headless）
tfc.solve(model, time_forward=3*365*24*3600, folder='output')

# 带回调绘图
tfc.solve(model,
    extra_plot=lambda: show(model, jx, jz),
    time_forward=365*24*3600,
    folder='output')
```

**注意**：`tfc.solve` 内部的 `gui_mode=True` 参数已弃用（将在 2027-07 移除）。如需 GUI，使用：

```python
gui.execute(lambda: tfc.solve(model, ...), close_after_done=False)
```

### 手动时间步进（精细控制）

```python
dt = 1e8
for step in range(100):
    model.iterate(dt=dt)
    dt = model.get_recommended_dt(previous_dt=dt, cfl=0.1)
```

### 时间步长管理

| 参数 | 位置 | 含义 |
|------|------|------|
| `dt_min` / `dt_max` | `tfc.create()` | 时间步长范围限制 |
| `cfl` | `tfc.create()` | CFL 数（自适应步长） |
| `dv_relative` | 已弃用 → 用 `cfl` | 每步最大流动距离 / 网格尺寸 |
| `time_forward` | `tfc.solve()` | 求解总时长 |
| `time_max` | solve options | 最大模拟时间 |
| `check_dt` tag | `model.add_tag("check_dt")` | 启用 CFL 步长检查 |

---

## 多相流与流体定义

### 定义流体

```python
# 内置流体
fludefs = [
    create_ch4(name='ch4'),        # 甲烷
    create_h2o(name='h2o'),        # 水
    create_co2(name='co2'),        # 二氧化碳
]

# 自定义流体
fludefs = [
    FluDef(den=50, vis=1.0e-2, name='oil'),
    FluDef(den=1000, vis=1.0e-3, name='water'),
]

# 从文件读取
oil = from_file('oil_data.txt', t_min=274, t_max=423, name='oil')
```

### 相对渗透率

```python
# 默认曲线
kr = create_kr()

# 自定义（Corey 模型）
kr = create_krf(faic=0.05, n=2.0, k_max=100, count=300)

# 变化相对渗透率（随水合物饱和度变化）
# 参见 prod_v2_vari_kr_inj_hot_water.py
```

### 饱和度表示

用字典 `{流体名: 饱和度}`，各相之和应 ≤ 1：单相 `{'h2o': 1}`；两相
`{'ch4': 0.5, 'h2o': 0.5}`；含 40% 水合物 `{'h2o': 0.6, 'ch4_hydrate': 0.4}`。

---

## 可视化策略

### 策略一：在 `tfc.solve` 中使用 `extra_plot`

每一时间步完成后自动调用绘图函数——完整示例见上文「推荐方式：`tfc.solve`」。

### 策略二：使用 `plot()` 函数

```python
def on_figure(fig):
    ax = add_axes2(fig, xlabel='x', ylabel='p')
    add_curve(ax, x_data, y_data)

plot(on_figure, caption='Pressure', tight_layout=True)
```

### 策略三：使用 `fig` 模块的声明式 API

```python
fig.show(
    fig.axes2(
        fig.contourf(x, y, p, cbar={'label': 'p/Pa', 'shrink': 0.7}),
        title='Pressure', xlabel='x/m', ylabel='y/m', aspect='equal'
    ),
    fig.tight_layout(),
    caption='压力分布'
)
```

### 策略四：使用 GUI 的 `plot_on_figure`

```python
widget.plot_on_figure(on_figure)
```

### 数据提取 API

```python
# 标量场（reshape 为网格形状）
x = tfc.get_x(model, shape=(jx, jz))
p = tfc.get_p(model, shape=(jx, jz))
s = tfc.get_v(model, fid=0, shape=(jx, jz))  # 特定流体体积

# 使用 Numpy 适配器
cells = as_numpy(model).cells
p = cells.pre / 1e6                        # 压力 (MPa)
t = cells.get(model.get_cell_key('temperature'))
```

---

## 特殊物理过程

### 扩散

```python
# 注册 Face 的扩散系数属性
fa_g = model.reg_face_key('g')

# 计算扩散通量: g = area * diffusion_coeff / dist
face.set_attr(fa_g, f1.area * 1.0e-9 / f1.dist)

# 添加扩散设置（组分 1 在流体 0 中扩散）
diffusion.add_setting(model, flu0=[0, 1], flu1=[0], fa_g=fa_g, cfl=0.2)

# 手动调用扩散迭代（使用 tfc.solve 时自动调用）
diffusion.iterate(model, dt=dt, recommend_dt=True)
```

### 毛管力

```python
# 定义毛管压力曲线（饱和度 → 毛管压力）
capillary.add_setting(model, ...)
```

### 流体加热（全储层分布）

```python
# 注意：这是全储层所有 Cell 的流体加热，非点加热
# 点加热请使用 add_injector（不设 fluid_id）
tfc.heating.add_setting(
    model,
    fluid='ch4_hydrate',      # 被加热的流体
    power=power_array,        # 每个 Cell 的功率 (W)
    temp_max=323.15           # 温度上限 (K)
)
```

### 砂运移

```python
sand.add_setting(model, ...)
```

---

## 模型管理

### 保存与恢复

```python
# 保存
model.save('model.seepage')

# 恢复
model = Seepage()
model.load('model.seepage')
```

### 求解选项（存储在模型中）

```python
model.set_text(
    key='solve',
    text={
        'monitor': {'cell_ids': [0, 1, 2]},  # 监控的 Cell
        'time_max': 365 * 24 * 3600,          # 总时间
    }
)
```

### Tags — 控制求解行为

```python
model.add_tag("check_dt")           # 启用 CFL 步长检查
model.not_has_tag("disable_ther")   # 检查是否禁用热计算
```

---

## 常见陷阱与最佳实践

1. **虚拟 Face 的热泄漏** — `add_cell_face` 创建的虚拟 Face 会传导热量，导致异常热流。
   解决：在虚拟 Face 附近将 `heat_cond` 设为 0（写法见「虚拟 Cell/Face」）。
2. **定压边界的设置** — 直接修改边界压力在流动过程中不能保持恒定。解决：用极大的体积
   （`1e6` m³）或极大孔隙度（`1e10`），而非直接固定压力值（见「定压边界」）。
3. **恒温边界的设置** — 直接修改边界温度会被热传导改变。解决：用极大的热容
   `denc = 1e20`（见「恒温边界」）。
4. **时间步长选择** — 步长过大不收敛，步长过小计算时间过长。解决：用 `cfl=0.1` 并添加
   `check_dt` tag 启用自适应步长，设置合理的 `dt_min` / `dt_max`，初始步长取小值（如
   `1e-3`）让模型自动调整（见「时间步长管理」）。
5. **弃用的 `dv_relative`** — 已弃用（将在 2027-06-17 后移除），用 `cfl` 替代。
6. **流体注入时未关闭井的渗透性** — 注热水/加热阶段生产井仍开启会导致流体短路。
   解决：在注入/加热阶段关闭虚拟 Face 的渗透性：

   ```python
   virtual_face = model.get_face(-1)
   perm_backup = virtual_face.get_attr('perm')
   tfc.set_face(virtual_face, perm=0.0, heat_cond=0.0)
   # ... 注入/加热 ...
   tfc.set_face(virtual_face, perm=perm_backup, heat_cond=0.0)
   ```

7. **饱和度和超过 1** — 初始饱和度之和超过 1 会导致求解失败。解决：确保
   `{flu_a: s_a, flu_b: s_b}` 中 `s_a + s_b ≤ 1`。
8. **缺少 `check_dt` tag** — 时间步长可能违反 CFL 条件，导致数值不稳定。解决：创建模型后
   添加 `model.add_tag("check_dt")`。
9. **忘记在注入/加热后重置 dt** — 上一阶段的大时间步长不适合下一阶段。解决：每个阶段结束
   时调用 `tfc.set_dt(model, 1.0e-3)` 重置步长。
10. **多阶段模拟中的状态管理** — 注入井、加热设置、虚拟 Face 属性在阶段切换时需要备份和
    恢复（参考 `inj_hot_water` 函数中的 backup/restore 模式）。

---

## Demo 索引

每个 demo 的说明就是它第一行的 `# ** desc`（见文末规则）。完整且始终最新的清单请打开 GUI 的
Demo 标签页（`gui.show_demo()`），或运行 `python -m zmlx test` —— 本文件不再手工维护一份
必然过期的 demo 表。

---

## 修改 demo 或创建新 demo 的规则

1. 每个可独立运行的 demo 必须在文件第一行设置 `# ** desc = '描述'`
2. 用 `gui.execute(main, close_after_done=False)` 作为 `__main__` 块（无头模式由内部
   `is_headless()` 自动识别，**不必**传 `disable_gui`）
3. 保持代码简单清晰，添加必要的注释
4. 参考现有 demo 的代码风格（agent 指引见同级 `AGENTS.md`；编码风格见 `../../AGENTS.md` 的 Coding style 章节）
