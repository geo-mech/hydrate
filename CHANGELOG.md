# CHANGELOG

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
