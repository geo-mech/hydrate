# CO₂ 水溶液密度随浓度线性变化的文献依据

---

## 支持"密度随浓度线性变化"的文献

### 1. Garcia (2001)：x≤0.05 时密度增量几乎线性

Garcia 系统整理了 CO₂–H₂O 的密度数据，给出一套偏摩尔体积相关式并指出：

- 对 ≤0.05 的范围，饱和 CO₂–水溶液在 10–100 bar、0–50 °C 条件下，密度比纯水最多高约 **2.5%**
- 原文明确指出：*"As expected according Equation 1, the density variation of the aqueous solutions of CO₂ is nearly linear with CO₂ mole fraction for mole fractions up to about 0.05."*（在 x≈0.05 以内，密度随 CO₂ 摩尔分数的变化几乎是线性的）

用 Garcia 的数据做拟合，得到 **Δρ(%) ≈ 0.5 × x(mol%)**，即：

- x ≈ 5 mol% 时 Δρ ≈ 2.5%
- 斜率 ≈ **0.5%/mol%**

### 2. Song 等（2013）："几乎线性"直接写在实验结论里

Song 等用磁悬浮天平测量了 CO₂+去离子水在温热储层条件下（几十 MPa、较高 T）的密度数据，直接给出结论：

> *"The density of the CO₂ aqueous solution increases with increasing pressure and CO₂ concentration almost linearly, while decreases with increasing temperature. And the slope of the density curves is almost the same for different concentrations at the same temperature within experimental error."*

要点有三：

1. 与 CO₂ 浓度关系 **"almost linearly"**（几乎线性）
2. 给定 T 时，不同浓度下的密度–压力曲线**斜率几乎一样**，说明在实验误差范围内可以用一个常数斜率来描述 ρ 对浓度的敏感性
3. 温度主要改变截距和斜率的数值，不改变"近似线性"的形态

### 3. Nomeli (2014) 对"未饱和溶液"的概括

Nomeli 在构建饱和 CO₂ 溶液密度模型时，总结前人（尤其是 Song 等）的数据，直接写道：

> *"Moreover, the density of the under-saturated solution varies linearly with the mole fraction of dissolved CO₂ (Song et al., 2013)."*

对未饱和 CO₂–水（或 CO₂–盐水）溶液，工程上完全可以把密度看成：

**ρ = ρ_w + k · x_CO₂**

### 4. McBride-Wright (2015)：偏摩尔体积模型 + 实验误差量级

McBride-Wright 等在 274–449 K、P≤100 MPa 下测量了 **x = 0.0086、0.0168、0.0271**（0.86–2.7 mol%）三个浓度的 CO₂(aq) 溶液密度，给出的要点是：

- 通过偏摩尔体积相关式 + IAPWS-95，可以把未饱和溶液的密度重建到 **±0.04%** 的相对误差
- 他们实际上是用"偏摩尔体积只依赖 T、P，不显式依赖 x"的形式来表达的，这等价于在几个 mol% 范围内认为 **ρ 对 x 的依赖一阶线性，二阶项很小**

---

## 什么时候"只用一条直线"就不够了？

### 更高浓度（x > 0.05–0.1）

- 此时 CO₂ 的偏摩尔体积开始随浓度**显著变化**
- ρ–x 曲线会明显弯曲（很多工作用二次或三次多项式拟合）
- 再用"单条直线 + 单个参考点"去拟合，全段误差会升到 1% 甚至更高，这对一些精细问题（比如对流门槛 Ra 的精确判定）就有点大了

### 高盐度盐水：CO₂–brine 体系

- 盐离子会显著改变水的结构，CO₂ 偏摩尔体积和溶解度都会受盐度影响
- 实验表明：在固定盐度下，未饱和溶液的密度–x 关系仍然**近似线性**，但**斜率随盐度变化**，需要为不同 NaCl 质量分数单独拟合一条直线

### 需要"非常高精度"的场合

- 比如用密度差去估算对流开始时间、临界 Rayleigh 数，而其他参数又比较精确，这时候 0.2–0.3% 的误差都可能被写进"误差分析"部分
- 这种情况下，建议直接用 Garcia / McBride-Wright 提供的偏摩尔体积相关式逐点算 ρ，不再走"工程直线近似"

---

*李宇轩，2025年11月25日*
