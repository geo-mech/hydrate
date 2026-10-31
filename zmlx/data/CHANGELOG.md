# CHANGELOG

## v1.9.8 (2026-10-31)
主窗口瘦身、目录重整，并新增「界面桥」插件、去掉后台改界面的并发上限。

**主窗口瘦身（22 个入口搬出）**

- 「显示 → 变量 / 通知」、「设置 → 系统 / 插件 / 迭代器」、「帮助 → ReadMe / 登录 / 反馈 / 关于」，
  以及 `show_code_history` / `show_output_history` / `show_string_table` / `show_text_in_tab` /
  `open_url` / `check_license` 等入口，连同控件一起搬进 `ui/setups/`。
- 判据只有一条：**关掉它，软件还能不能正常用？** 不能 → `setups/`；能 → 插件。
  「用户管理」三个页面按同一判据重判后归插件。
- **命令名一字未改**，历史标签页照常恢复；控件跟着入口走。

**目录重整**

- `extra_setups/` 改名为 `setups/`：`extra_` 意为「额外」，可它装的是**必加载**的装配，名字与语义相反。
  老路径直接失效、不留垫片。

**新增「界面桥」插件（实验，默认关闭）**

- 「设置 → 界面桥」打开后，本机其它程序（脚本、另一个实例）可以查询界面状态、列出页面、截图、
  打开指定页面；只提供只读操作，写操作不开放。
- 只监听 `127.0.0.1`，端口与口令每次启动随机生成；修掉连续请求时连接错乱的问题
  （鉴权失败等早退响应后，同一条连接上的后续请求全部出错）。

**界面命令通道更稳**

- 后台线程从脚本改界面不再有 20 个并发通道的上限，忙时不会被静默丢弃；
  `gui.channel_n()` 随之弃用（2027-10-30 删除）。
- 通道握手改用信号量，不再依赖「非属主线程解锁」这种未文档化的行为；对外行为不变。

**其它**

- 图片浏览并入「图片浏览」插件；新增「帮助 → AI辅助」（可写脚本、执行脚本并读回控制台输出）。
- 主菜单顺序在最后一个提交里才固定下来（此前「设置」可能排到「帮助」后面）。
- 删除三处从来没有生效过的内部通道，界面代码更简洁。

## v1.9.7 (2026-10-30)
图片浏览器 `ImageBrowser` 由 `ui/tabs/image_browser.py` 整体并入插件 `plugins/builtin/image_browser.py`，原模块删除、不留转发垫片。

- 插件从此**单文件自足**（控件 + 3 个后台线程 + 菜单入口都在一处），关掉「图片浏览」插件时它的代码也一并关掉；
- **命令名与控件的公开接口均未变**：`gui.show_image_browser()`、action name `image_browser`、`set_folder` / `follow_cwd` / `rescan` / `play` / `pause` / `step` 照旧，历史标签页能正常恢复；
- 删除前已核实全仓与外部工作区都没有别处 import 该模块（唯一引用就是本插件）；
- 新路径：`from zmlx.ui.plugins.builtin.image_browser import ImageBrowser`。

## v1.9.6 (2026-10-29)
AI 辅助可写脚本、执行脚本并读回控制台输出（可自己调试代码）；用户气泡底色改为按主题取色；控制台输出可通过 `MainWindow.get_output_text()` 读取。

## v1.9.5 (2026-10-29)
新增场景侧插件包 `scen/ai_assistant`：与 DeepSeek 对话的右侧标签页（「帮助 → AI辅助」）。

## v1.9.4 (2026-10-29)
弃用 `zmlx.version`（LazyImport 改由模块级 `__getattr__` 转发），并新增 `zmlx.version_at_least(version)` 按数字比较版本号。

## v1.9.3 (2026-10-28)
删除从未执行过的「启动即打开欢迎页」分支，并修好标签页重启恢复时带字符串参数会生成坏代码的问题。

- **删除欢迎页**：`MainWindow` 构造期一直在找 `welcome` 图标，而 `zml_icons/` 里从未有过这个文件（git 历史也查不到），该分支永久不执行；整段移除，相关解释移到 `open_image` 的 docstring。
- **修复 `gui_restore` 生成**：`open_image` / `open_code` / `open_text` 保存重启参数时没加 `!r`，`caption` 等字符串被拼成不带引号的裸值（路径里的反斜杠也会被写坏），重启重放时抛 `NameError`。

## v1.9.2 (2026-10-26)
菜单项的注册体系一次收敛：`add_action` 不再受 `name` 摆布 —— 名字缺省时按「菜单路径 + 文字」自动生成，`overwrite` 撞名时真正**就地覆盖**，分隔线改用 `text='---'` 声明；`get_action` 不再凭空造空 action，且只认 `add_action` 创建的菜单项。

- **自动命名与判重**：`name` 缺省时按「菜单路径 + 文字」生成（文字是函数则按其身份，不调用它），「同菜单 + 同文字」的重复注册会得到同一个名字，判重对所有调用方式一致生效；文字传函数时标识里带上定义行号与绑定实例，不再把不同的函数认成同一个（此前后注册的会静默覆盖前一条）。
- **`overwrite`**（原 `overwritable`，旧名保留为弃用别名、2027-10-27 删除）：`True`（默认）撞名时就地覆盖已有那条并留在原位置，菜单里始终只有一条；`False` 只注册一次，撞了发警告并跳过。覆盖时没给 `icon` / `tooltip` / `shortcut` / 动态回调就保持原值。
- **`text`**：必填（`str` 或返回 `str` 的 callable），类型不符抛 `TypeError`；多级 `menu`（`list` / `tuple`）可省略它，直接弹最后一级当文字；分隔线用 `text='---'` 声明，没给 `menu` 时不再凭空建「其它」菜单。
- **`get_action` / `list_actions`**：只查 `add_action` 创建的菜单项；`get_action` 的 `create_empty` 已弃用（2027-10-26 删除），找不到一律返回 `None`，`trigger` 找不到时明确告警。
- **菜单分组**：「操作」菜单按内核控制 / 控制台栏 / 历史与页面分成三段，「文件」菜单按打开新建 / 数据操作 / 退出分成三段，分别加了分隔线 —— 11 项平铺在一栏里太乱，误点的后果也完全不同。
- 重复注册不再让一次点击跑多个历史槽（点击改为转发到 `Action.slot_func`，覆盖时整体替换）；新建条目后立即刷新一次视图，文字传函数时首帧不再为空。
- 顺带清理：删除从未被调用的 `MainWindow._push_sub_menus_to_end`，几处多余的嵌套 `if` 合并，`add_action` 签名改为紧凑排版。

## v1.9.1 (2026-10-26)
界面、菜单与控制台的一组改进。

**界面**

- 状态栏新增「运行状态灯」（○ 空闲 / ● 运行中 / ⏸ 已暂停），点它即可显示控制台。
- 右侧栏（控制台）宽度可拖动调整，并记住位置与是否显示；「显示 → 重置布局」可一键恢复默认，不影响窗口大小和样式表。
- 版本号按钮只显示版本号（`版本: 1.9.1`），内核编译时间移到提示里。
- 工具栏图标全部重绘为扁平风格，透明底、更清晰。
- 「帮助 → 架构」：配图改内嵌、排版自动适配，打开速度约快十倍。
- 「关于」页新增「架构」按钮；「文件 → 浏览」下新增「工作目录」与「图片」。

**菜单与快捷键**

- 菜单顺序重新梳理：文件、帮助两个菜单按原来的习惯排列；「刷新」归入「操作」。
- 修复快捷键冲突（运行 / 暂停 / 继续 / 停止 / 再次运行各占一个）。
- 「设置 → 插件」第一列改名「默认加载」；插件新增依赖声明，可随依赖自动加载。

**控制台**

- 输出历史改存 HTML，重启后颜色与粗体不再丢失；旧历史仍可打开。

**编辑器控件**

- 全部编辑器控件集中到 `zmlx.ui.widgets.editors`（旧路径仍可用，2027-10 前不删）。
- 修好 `MatplotWidget` 缩放变形、`zmlx.plt` 旧路径垫片的若干调用错误。
- 编辑器的 `sig_changed` 只在用户改值时发出，代码赋值不再误触发。

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
