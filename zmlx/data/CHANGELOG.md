# CHANGELOG

## v1.9.0 (2026-10-21)
插件体系定稿、包名统一为复数、界面层集中修缮、登录 / 反馈链路收敛、日志与警告体系统一；以下要点汇总本次发布周期内的全部改动。

- **插件体系定稿**：用「名单 + high/normal/low 三档优先级 + 禁用」取代浮点 rank；插件一律在独立命名空间执行（`__name__` 为 `'__zml_plugin__'`，兼容老写法并有警告），内置插件下沉 `plugins/builtin/`，文件名主推 `zml_plugin.py`；一批可选功能（图片浏览、样式表、VtkView、求解器、运行环境、彩蛋等 13 个）改为插件；`zmlx.ui.exts` → `zmlx.ui.plugins`。「设置 → 插件」重做为七列表格，名称 / 描述由插件头部 `# ** name` / `# ** desc` 自报，扫描移到后台线程，刷新只更新状态、不再整表重建。
- **包名统一改为复数（11 个包）**：`ui/widget`→`widgets`、`utility`→`utils`、`alg`→`algs`、`fluid`→`fluids`、`react`→`reactions`、`geometry`→`geometries`、`mesh`→`meshes`、`seepage_mesh`→`seepage_meshes`、`script`→`scripts`、`kr`→`krs`、`demo`→`demos`，除 `demo` 外均留兼容垫片（导入即发 `DeprecationWarning`，2027-10-16 删除）；`ui/widget` 下的顶层控件迁入 `ui/tabs/`。
- **界面层修缮**：状态栏拆成独立控件、修掉暂停点自死锁导致界面卡死、后台线程被连带析构导致的进程 abort、双击单元格在 WSLg 下段错误；新增图片浏览器、「帮助 → 架构」入门页、「标签列表」入口与自动刷新、用户管理页、运行环境检测；「设置 → 系统变量」按代码实际默认值重做；线程 / 控制台规则成文并新增 `ui.utils.thread_runner`，绘图（`MatplotWidget`）改为与线程无关、重图不再卡界面。
- **登录 / 反馈链路收敛**：通信统一到一个出口，机器码字段改用 `machine_id`、登录答复解析加固；新增登录记录 / 反馈记录页（姓名在上、邮箱在下）与「帮助 → 用户 / 查询」菜单；邮件改走服务端代发，反馈记录与备注改存服务端。
- **日志与警告体系**：警告统一走 `zmlx.system.warn`（多记一条日志并留当天 tag，可查弃用项是否仍被使用），日志统一走 `zmlx.system.log`，自动反馈搬到包入口且只发最近两个月。

## v1.8.0 (2026-08-10)
install_dep 支持 conda 优先回退 pip，About 用 Markdown 显示 CHANGELOG，Memory 显示标准文档。
- 帮助菜单新增「修改记录」「未来工作」「检查更新」三个入口，并新增基于 git 的安全更新（CLI + pygit2 双后端）。
- UI 优化：DemoView 改为三列布局 + 排序 + 自适应行高 + 列宽约束，desc 列支持 HTML 渲染并按 13 个文件夹分类高亮、补上作者列；环境变量页改为滚动区表单布局 + 复选框 / 下拉框 / 数字框等智能控件；About 改为分组表单 + 可点击链接 + 8 个关键依赖检测与一键安装，版本号行的「日志」按钮用 Markdown 显示 CHANGELOG，同时移除硬件码显示及按钮；Memory 支持在 GUI 里显示 Markdown 标准模式文档。
- `install_dep` 统一 conda / pip 接口：优先 `conda install`，失败回退 pip；并新增 Windows 桌面启动器与一键编译脚本。
- 文档：优化 78 个 demo 的 desc 描述，完善 16 项环境变量配置说明，新增 `ROADMAP.md`（7 项中期计划 + 开发原则）。
- 求解器体系重构：默认改为 code 字符串模式（exec 优先、eval 兜底）并支持持久化，求解器选择写入磁盘、重启保留；新增多个求解器，含 SciPy 稀疏求解器、Intel MKL 稀疏直接求解器（概念验证）与基于 CuPy 的 GPU 求解器原型。
- 求解器配置界面：新增全局单例 GUI 迭代器与可视化面板（耗时曲线 + 参数编辑），以及求解器配置面板（8 种求解器 + 参数输入 + 快速测试）。
- 控制台与内存视图：输出面板底部新增 Python 命令输入行（历史持久化 + eval 优先），内存视图按变量类型显示 17 种字体颜色。
- 其他变更与修复：`GuiApi` 由 assert 改为 if/raise RuntimeError；环境变量取值的 `ignore_empty` 默认值改为 `True`；移除 8 个菜单项。修复 DemoView 排序后运行按钮 / 点击描述执行错误 demo（Qt `setSortingEnabled` 与 cell widget 冲突），以及 DemoView 多行 HTML 换行问题。
- 新增 `python -m zmlx test` 命令（无头模式跑全部 demo 测试）；demo 批量测试脚本改用跨平台的文件打开方式，绘图工具补上参数消除警告，并移除 13 个 demo 里多余的守卫。

## v1.7.0 (2026-07-17)
发布文档体系重构、无头模式、matplotlib 工具、水合物 demo 与 Windows 编译脚本等改进。
- **无头模式**：新增 `is_headless()`（支持 `--no-gui` / `--headless` / 环境变量），
  `gui.execute()` 内置自动检测，64 个 demo 的入口因此简化；`pyqt.py` 在无头模式下跳过 Qt 加载。
- **matplotlib 工具**：新增 `set_chinese_font()`、`get_plt_save_path()`、`plot_no_gui()`；
  `plot_no_gui` 移至 `gui_buffer._plot_no_gui`，用户应改用 `gui.plot()` 或 `zmlx.ui.plot()`。
- 新增工具与 demo：AI 训练工具 `zmlx/scen/rkt/ai/`（Logit/Composition/Phase/Temp/Pres 五种变换）、
  溶解平衡 `zmlx/scen/rkt/solubility/`（GasAqueousUVEquilibrium + 数据生成/训练流程）、
  网格工具包 `zmlx/meshes/`（`create_rect_mesh` / `create_cube_mesh` / `filter_mesh`）、
  水合物 demo（注热水+降压、电加热+降压）、`test_all_demos.py` 多线程并行测试、
  Windows 编译脚本 `zmlx/exts/build.bat`（MSVC），以及 Claude Code 命令 `/commit` `/release` `/squash` `/test`。
- 变更与弃用：`dv_relative` → `cfl`（所有 demo 统一用 `cfl`），`tfc.solve(gui_mode=True)`
  与 `plt.plot_no_gui` 标记弃用（改用 `gui.execute(lambda: tfc.solve(...), ...)` 与 `zmlx.ui.plot()`）。
- 文档与修复：`CLAUDE.md`（架构/规范/API 合约）、`zmlx/ReadMe.md`、`demo/ReadMe.md`、
  `ui/ReadMe.md` 与 14 个子包 ReadMe 全面重写；修掉 `oil_disp_wat.py` 缺失 `import sys`、
  `_show.py` 误删代码，并新增 `zmlx/plt/` 包（matplotlib 可视化模块，原 v1.6.8）。

## v1.5.x 及更早
项目基础架构建立，含 THMC 多场耦合核心、PyQt6 GUI 与应用场景。
