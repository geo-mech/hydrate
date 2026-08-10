# CHANGELOG

## v1.8.0 (2026-08-10)

本次发布涵盖求解器体系重构（code 字符串 + 线程安全 + 持久化）、DemoView 增强（HTML 渲染 + 按文件夹着色）、
控制台交互完善（命令输入行 + 历史）、GPU 求解器原型（CuPy）、以及大量 UI 优化和缺陷修复。

### 新增
- **求解器体系**：`set_default_solver_code`/`get_default_solver_code`/`make_solver`，支持 exec/eval 双路径
- **求解器持久化**：求解器选择通过 `app_data.getenv/setenv` 写入磁盘，重启后保留
- `GuiIterator`：全局单例 `get_gui_iter()`，不同迭代过程共享同一对象
- `GuiIteratorEdit`：可视化面板（耗时曲线 + 参数编辑）
- `SolverSelector`：求解器配置面板（8 种求解器 + 参数输入 + 快速测试）
- `SciPySolver`：基于 scipy.sparse.linalg.spsolve 的纯 Python 求解器
- `PARDISOSolver`：Intel MKL 稀疏直接求解器（独立 pardiso.dll，概念验证）
- `CudaSolver`：CuPy GPU 求解器 (direct/cg/bicgstab/gmres/bicg)
- **DemoView**：desc 列支持 HTML 渲染 + 116 个 demo 按 13 文件夹分类高亮 + 作者列
- `OutputWidget` 底部 Python 命令输入行 + 历史持久化 + eval 优先

### 变更
- 默认求解器改为 code 字符串模式（exec 优先, eval 兜底），`DynSys`/`FlowSol`/`ThermalSol` 缓存局部实例
- `GuiApi`：assert → if/raise RuntimeError，`mtx_running` → `mtx_busy`
- `app_data.getenv()`：`ignore_empty` 默认值改为 `True`
- `MemView`：按变量类型显示不同字体颜色 17 种
- 移除 PgConsole、清屏、检查更新等 8 个菜单项
- `.claude/commands` 恢复英文命名

### 修复
- DemoView 排序后运行按钮/点击描述执行错误 demo (Qt setSortingEnabled + cell widget bug)

## v1.7.24 (2026-08-05)

### 新增
- DemoView: 三列布局 + 排序 + 自适应行高 + 列宽约束
- EnvEdit: QScrollArea 表单布局 + 智能控件
- About: 分组表单 + 可点击链接 + 关键依赖检测
- `alg.update_by_git`: 基于 git 的安全更新

### 文档
- 优化 78 个 demo 的 desc 描述
- 完善 16 项环境变量配置说明
- 新增 ROADMAP.md

## v1.7.23 (2026-08-04)

### 新增
- 帮助菜单新增"修改记录"、"未来工作"和"检查更新"入口
- `alg.update_by_git`: 基于 git 的安全更新（CLI + pygit2 双后端）
- `lic.fingerprint` / `lic.match_fingerprints`: 硬件指纹识别

### UI 优化
- DemoView: 三列布局 + 排序 + 自适应行高 + 列宽约束
- EnvEdit: QScrollArea 表单布局 + QCheckBox/QComboBox/QSpinBox 智能控件
- About: 分组表单 + 可点击链接 + 8 个关键依赖检测 + 一键安装

### 文档
- 优化 78 个 demo 的 desc 描述
- 完善 16 项环境变量配置说明
- 新增 ROADMAP.md（7 项中期计划 + 开发原则）

## v1.7.18 (2026-08-02)

### 核心重构
- solver 接口全面重构：C 回调 + 去宏化 + 去模板化
- `cg_solver_ty`：新增 `solve()` + `fn`/`ctx`（替代 `fn_ctx`）
- `CSolver` → `SolAdapter` → 删除（最终 `fn`/`ctx` 直接传递）
- `dynsys`/`seepage_ts`/`thermal`：统一改为 C 回调（`fn`/`ctx`）
- `DynSys`：solver 参数改为 duck typing

### 新增求解器
- `SparseLUSolver`：Eigen SparseLU 直接法（任意矩阵，机器精度）
- `SimplicialLDLTSolver`：Eigen SimplicialLDLT 直接法（对称矩阵，速度更快）
- `bicgstab_solver_ty`：Eigen BiCGSTAB 迭代法（非对称矩阵）
- `iccg_solver_ty`：IC 预条件 + CG 迭代法
- `ILUbicgstab_solver_ty`：ILU 预条件 + BiCGSTAB 迭代法

### 变更
- `_seepage.py`、`_dyn.py`：solver 参数改为 duck typing
- `tests/`：新增 `lu_sol.py`、`ldlt_sol.py`、`bicgstab_sol.py`、`preconditioned_sol.py`
- `build.bat`：Boost/Eigen 路径增加 fallback

## v1.7.13 (2026-08-01)

### 新增
- `MatplotWidget.save_file(open_dir, open_fig)`：自动保存图片（时间戳文件名），支持打开目录/图片
- `MatplotWidget.copy_to_clipboard()`：复制图片到剪切板（保存到临时文件），可直接粘贴到 PPT 等
- 右键菜单新增"复制到剪切板"

### 变更
- `.claude/settings.local.json`：放宽 Bash 命令限制（移除 rm -rf/rm -r 禁用），设置默认权限模式为 dontAsk

### 文档
- `README.md`：在作者后添加"关键词"部分（天然气水合物、多场耦合、THMC 等）

## v1.7.10 (2026-07-29)

### 新增
- `tools/launcher.py`：Windows 桌面启动器
  - 自动发现 Python（EXE 旁 → 系统 PATH → 手动选择）
  - 直接启动 + 后台监控启动错误（≤500ms 检测崩溃）
  - 配置持久化到 `launcher_config.json`（支持相对路径）
- `tools/build_launcher.py`：一键编译启动器为 EXE
- `tools/app.ico`：应用图标
- `lic.fingerprint`：获取硬件指纹
- `lic.match_fingerprints(fp1, fp2)`：比较两个硬件指纹的匹配度

### 变更
- `.gitignore` 合并至仓库根目录，忽略 `IGG-Hydrate.exe`

## v1.7.7 (2026-07-20)

### 修复
- `_compare_rkt_and_cp.py`: `__main__` 移至文件末尾，修复 `_visualize` 未定义

## v1.7.6 (2026-07-19)

### 新增
- `scen/helium/`：氦气提取场景（`create_fludefs` + `plot_seepage_volume_fractions`）

### 变更
- 优化 demo 描述：plt/8 + thermal/5 + diffusion/3

---

## v1.7.5 (2026-07-19)

### 新增
- `fluid/cp/_create_fludef.py`：`create_fludef(fluid, ...)` 基于 CoolProp 自动创建 FluDef

### 移除
- `scen/helium/`：已迁移至 `zmlx/fluid/cp/` + `zmlx/fluid/rkt/`

---

## v1.7.4 (2026-07-19)

### 新增
- `fluid/rkt/aq/`：气体溶解度 `h2o_xxx_solubility(P, T)` + `create_gas_aqueous(gas, ...)`
  - 6 种气体 CH₄/CO₂/N₂/O₂/He/H₂，水相质量法计算饱和质量分数
  - 自动创建 FluDef 水溶液，线性缩放至 c=0.05
  - `plot_density_ratio` 支持 `fn_solubility`，标题显示溶解度

### 变更
- `fluid/cp/`、`fluid/rkt/`、`fluid/rkt/aq/`：导入守卫，库缺失时提示安装方式

### 文档
- CLAUDE.md 精简 + GUI 模式 + `zmlx.ui.plot` 绘图规范
- `ui/ReadMe.md` / `plt/ReadMe.md`：强调 `plot(on_figure)` 标准方式

---

## v1.7.3 (2026-07-18)

### 新增
- `fluid/rkt/aq/`：基于 Reaktoro 的气体-水溶液密度计算
  - 6 种气体水溶液：CH₄/CO₂/N₂/O₂/He/H₂
  - 统一签名 `fn(w, P=10e6, T=300)`，密度比值 ρ/ρ₀ 绘图
  - 溶解度饱和拐点自动识别

### 变更
- 所有 `_plot.py`（cp/rkt/aq）统一使用 `zmlx.ui.plot(on_figure, caption)` 模式
- 所有 `__main__` 统一 `gui.execute()` 入口
- 等值线暗色模式适配（`gui.in_dark_mode()` → 白线/浅灰）

### 文档
- `fluid/ReadMe.md`：新增 cp/rkt 双引擎章节（API + 流体表 + 对比）
- `__init__.py` ×3：完整模块文档 + 流体列表
- `_plot.py` ×3：详细参数说明 + 暗色模式
- 代表性流体文件：增强模块级文档

---

## v1.7.2 (2026-07-18)

### 新增
- **`zmlx/fluid/cp/`**：基于 CoolProp 8.0.0 的纯流体物性子包
  - 8 种流体：H₂O/H₂/He/CH₄/C₂H₆/N₂/O₂/CO₂
  - 每种提供 `xxx_density(P,T)` + `xxx_viscosity(P,T)` + `xxx_specific_heat(P,T)`
  - `_plot.py`：共享绘图函数，支持密度+粘度+比热 3x2 云图
  - 接口规范化：`fn(P, T)` 先压力后温度，SI 单位，`ValueError` 替代 `assert`
- **`zmlx/fluid/rkt/`**：基于 Reaktoro + Supcrt98 的纯流体物性子包
  - 7 种流体：H₂O/H₂/He/CH₄/N₂/O₂/CO₂
  - 每种提供 `xxx_density(P,T)` + `xxx_specific_heat(P,T)`
  - `_compare_rkt_and_cp.py`：rkt vs cp 系统对比脚本
- **`scen/helium/`**：氦气提取化学计算模块
  - `reaktoro_tutorials/`：23 个 Reaktoro 官方教程
  - `fluid/`：基于 Reaktoro 的气体/液体/水溶液密度计算（含 CO₂/N₂/O₂/He/CH₄ 溶液）

### 移除
- `fetch_tutorials.py`（一次性工具）
- `scen/helium/fluid_cp/`（迁移至 `zmlx/fluid/cp/`）

---

## v1.7.1 (2026-07-17)

### 新增
- `python -m zmlx test` 命令：无头模式运行所有 demo 测试

### 修复
- test_all_demos.py: `os.startfile` → `zmlx.alg.startfile` 跨平台兼容
- 移除 13 个 demo 中的 `if not gui.exists(): return` 守卫
- _plot_no_gui 添加 clear/savefig/folder_save 参数消除警告

---

## v1.7.0 (2026-07-17)

本次发布涵盖了项目文档体系重构、无头模式支持、matplotlib 工具模块、
AI 训练辅助工具、水合物开发 demo、Windows 编译脚本等大量改进。

### 新增
- **无头模式**：`is_headless()` 函数，支持 `--no-gui`/`--headless`/环境变量
- **matplotlib 工具**：`set_chinese_font()`、`get_plt_save_path()`、`plot_no_gui()`
- **AI 训练工具**：`zmlx/scen/rkt/ai/` — Logit/Composition/Phase/Temp/Pres 五种变换
- **溶解平衡**：`zmlx/scen/rkt/solubility/` — GasAqueousUVEquilibrium + 数据生成/训练流程
- **网格工具包**：`zmlx/mesh/` — `create_rect_mesh`、`create_cube_mesh`、`filter_mesh`
- **水合物 demo**：注热水+降压、电加热+降压两个完整示例
- **批量测试**：`test_all_demos.py` 多线程并行测试
- **Claude Code 命令**：`/commit`、`/release`、`/squash`、`/test`
- **Windows 编译**：`zmlx/exts/build.bat` MSVC 编译脚本

### 变更
- `gui.execute()` 内置 `is_headless()` 自动检测，64 个 demo 入口简化
- `dv_relative` → `cfl`，所有 demo 统一使用 `cfl` 参数
- `plot_no_gui` 移至 `gui_buffer._plot_no_gui`，用户应使用 `gui.plot()`
- `tfc.solve(gui_mode=True)` 添加弃用警告
- `pyqt.py`：无头模式跳过 Qt 加载

### 弃用
- `tfc.solve(gui_mode=True)` → 使用 `gui.execute(lambda: tfc.solve(...), ...)`
- `plt.plot_no_gui` → 使用 `gui.plot()` 或 `zmlx.ui.plot()`

### 修复
- `oil_disp_wat.py` 缺失 `import sys`
- `_show.py` 误删代码恢复

### 文档
- `CLAUDE.md`：完整项目指引（架构/规范/API 合约）
- `zmlx/ReadMe.md`：面向使用者的完整指南
- `demo/ReadMe.md`：全面建模指南
- `ui/ReadMe.md`：GUI 执行方式/PyQt 导入/无头模式
- 14 个子包 ReadMe
- `CHANGELOG.md`：版本更新日志

---

## v1.6.8 (2026-06-02)

### 新增
- `zmlx/plt/` 包：matplotlib 可视化模块

---

## v1.5.x 及更早

- 项目基础架构建立、THMC 多场耦合核心、PyQt6 GUI、应用场景
