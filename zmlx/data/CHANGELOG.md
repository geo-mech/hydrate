# CHANGELOG

## v1.9.23 (2026-11-04)
新增**地热场景插件包** `zmlx/scen/geothermal/`：模拟水平井一个横截面附近的取热（岩石向井筒传热），在菜单栏挂**一级菜单「地热 → 测试 → Case2」**，默认不加载。

- **插件入口**（`zml_plugin.py`，`# ** enabled = False`）：一级菜单 `'地热'`，
  命令 `gui.show_geothermal_case_02()`。求解经 `gui.start` 进控制台线程
  （`tfc.solve` 是分钟级长任务，直接放进 `slot` 会冻住界面，走 `start` 才能用暂停/停止）；
  点菜单前先查 `gui.is_running()`，避免控制台单槽位把请求**静默丢弃**。
- **建模 / 求解**（`_well_cross_section.py`）：`create(...)` 建 x–z 剖面模型，
  井取离 `well_pos` 最近的单元并按井筒直径收缩其与相邻单元的导流面积；
  岩石物性按花岗岩典型值（2650 kg/m³ / 790 J/(kg·K) / 3.0 W/(m·K)），
  密度、比热、热导率、渗透率、最大时间步均可参数化。
  `solve(...)` 求解并实时绘图；`update_power(model)` 每步统计采热功率。
- **网格**（`_mesh.py`）：`mesh_xz(*, jx, jz, xr, yr, zr)` 只负责几何，参数全部为
  仅关键字（避免 `jx` / `jz` 写反却无提示），`xr` / `zr` 支持两元组等分或直接给节点序列；
  另含 `equivalent_area`（两段线性变截面的**对数平均**等效面积）与
  `get_average_area`（两段常量面积的**加权调和平均**），两者数值不等、不可互替。
- **绘图**（`_show.py`）：`show(model, jx, jz, *, circles=None)` 画岩石温度 / 流体温度 /
  密度 / 流体 z0 四张子图，并可叠加任意多个参考圆（元组或字典两种写法，
  字典的额外键原样传给 matplotlib 的 `plot`）。
- **精度**：模型里记录的时间与能量用 `repr()` 存储 —— `f"{x:.10f}"` 是定点格式，
  会把 `1.2e-12` 写成 `0.0000000000` 使精度全失，而 `repr` 保证 `float(s)` 与原值逐位相同。
- **文档**：按发布级标准编写，模块与全部函数（含嵌套）都有 docstring，统一
  `Args:` / `Returns:` / `Raises:` 三段式；并对反直觉处显式标注（`dist` 是流体与固体的
  换热距离而非热扩散率；`h2o.create` 的 `t_min` / `t_max` 是查表**钳制边界**而非算例温度区间）。

## v1.9.22 (2026-11-03)
`open_gui_without_setup()` 改为真正的**安全启动**：启动时的每一项「要不要加载」统一由 `gui_buffer.start_option()` 决定，安全启动下不再恢复控制台输出历史、不加载插件 / 标签页 / 初始检查与界面状态（`setups` 仍默认执行）。

- **统一取值链**：新增 `gui_buffer.start_option(key, default)` —— **显式内存键 > 安全启动 >
  持久化 env > default**。`main.py` 里不再各处直接 `app_data.get(...)` 判断，只有一条链，
  排查「这次为什么没加载」只需看一处。
- **安全启动（`open_gui_without_setup()`）写下的开关**：`safe_start=True` 总开关，外加
  `restore_console_output` / `run_plugins`（旧名 `run_setup` 同步写）/ `restore_tabs` /
  `init_check` / `restore_ui_state` 全为 `False`（清单是 `gui_buffer._Startup.SKIP_IN_SAFE_START`）；
  `run_setups` **默认 `True`**（清单是 `_Startup.KEEP_IN_SAFE_START`）—— 安全启动仍要 setups。
- **不新增文件级全局名**：键名与清单都收进 `gui_buffer._Startup` 这个私有命名空间类
  （`SAFE` / 各键 / `SKIP_IN_SAFE_START` / `KEEP_IN_SAFE_START`），模块级只留
  `is_safe_start()` 与 `start_option()` 两个函数；`main.py` 侧直接用字面量键名
  （`start_option('restore_console_output')`），与设置页里的持久化开关同名、一眼对应。
- **不再恢复控制台历史**：`__restore_history()` 在安全启动下连历史文件都不读（这是 v1.9.21
  那个「卡在启动画面」所在的位置：启动画面还挡着时解析 HTML、解码图片、生成预览缓存）。
- **setups 默认照常执行**（2026-11-03 按用户要求定）：通知、变量浏览器、设置页、插件面板、
  登录页、反馈都在 `setups.setup_ui()` 里，是「用界面把东西修好」的前提。新增 `run_setups`
  开关（与插件开关是两回事），只有显式传 `run_setups=False` 才会跳过。
- **不再恢复界面状态**：`__on_show()` 在安全启动下不读窗口尺寸 / 侧栏宽度 / 可见性 / 样式表；
  `keep_cwd=True` 也不读上次的工作目录。
- **每一项都可单独覆盖**：`open_gui_without_setup(restore_console_output=True, ...)`
  的具名参数与键同名，`None` = 沿用安全启动默认；「安全启动但想看历史」这类诊断场景写得出来。
- **一眼可见**：安全启动时控制台首行多一句灰色提示「=== 安全启动：未加载 插件 / 输出历史 /
  标签页 / 窗口样式 ===」，免得用户以为界面坏了。
- 实测（用户那份带 8 张图的历史数据）：正常启动 `__on_init` 0.12 s、内核 0.47 s、恢复 9 张图；
  安全启动 `__on_init` 0.04 s、内核 0.02 s、0 张图、setups 命令照常注册；真实入口
  `zmlx/scripts/open_ui_safe.py` 4 秒内窗口可用。

## v1.9.21 (2026-11-03)
两个修复：一是「在这台电脑上退出」之后登录页停在「更新信息」形态、不发验证码就没法重新登录（退出后立刻切回登录形态，并补上「服务端明确说本机没登记」这一判定）；二是恢复输出历史时预览缓存写盘失败被反复重试、导致 GUI 线程死循环、启动卡在启动画面（缓存目录改为自己创建并校验可写，失败即放弃）。

### 登录页：退出后切不回登录形态
- **根因**：`_prefill` 只把 `Yes` 开头当成有效答复，服务端回答的
  `Please register with your email first.`（= **确定**本机没登记）被归进了「查不到」，
  于是**刻意不动形态** —— 退出之后形态一直停在「更新信息」，「发送验证码」与验证码那一行
  都不回来；关掉标签再打开才恢复（那时才走到切形态那一步）。
- **判据收敛成三份、共用一处**：`lic_utils` 新增 `NO_LICENSE_REPLY` 与 `is_unregistered()`；
  登录页的 `_prefill` / `_show_status` 与状态栏 `license_button._classify` 全部用它，
  不再各写一遍（状态栏原先自己有一份常量，现改为别名）。
- **退出要当场切形态**：`_after_logout` 在 `Unbound` 之后立刻
  `_apply_mode(MODE_REGISTER)` + `_show_status(未登录)`，不再等那一趟最长 60 秒的联网复核；
  断网时也不会卡在旧结论上。
- **横幅措辞顺带修正**：「服务端明确说本机没登记」原先显示成「登录无效或查询失败」，
  现在显示「尚未登录：这台电脑还没有登录。」（首次打开一台未登录的机器也看得到）。
- ⚠️ **没有把「断网」也当成未登录**：`SocketException` / 超时 / 已过期仍走「形态不动」，
  免得一次网络抖动就把已登录的界面翻成登录形态。

### 启动卡在启动画面
- **根因（实测复现）**：`load_text()` → `set_html()` → `_rebind_images()` 会对历史里每张
  需要缩小的大图调 `_cached_image_size()`，把预览写到
  `app_data.temp('console_images')`。这个目录**只在该函数被调用时才顺带创建**，而
  `_cached_image_size()` 只算路径、不建目录 ⇒ `QImage.save()` 目标目录不存在而失败，紧接着
  `setCharFormat()` 触发文档重绘、又一次请求同一张图 —— **GUI 线程在 `set_html` 里死循环**，
  启动画面永远不消失（实测：CPU 满核、内存涨到 2.1 GB、只能强杀）。
  数据目录里只要有一份**带图片**的历史（`output_history/20261102T1828*.html` 里 8 张），
  启动就必然卡住；清空该目录即恢复 —— 与现场完全一致。
- **缓存目录自己建、且真的可写**：新增 `_ensure_folder()`（`makedirs` + 写一个探针文件），
  不再依赖「谁先调 `app_data.temp()`」；新增 `_cache_ready()`，0 字节 / 半截文件不再算命中。
- **失败即放弃、本次进程不重试**：`_cached_image_size()` 任何一步失败都记进
  `OutputWidget._CACHE_FAILED` 并返回 `None`，调用方直接沿用原图路径；
  `_CACHE_BUSY` 防重入（同一个路径在计算途中再次被请求时直接返回）—— 两个死循环入口都堵上。
- **只重新绑定「读得出来的图片」**：`_rebind_images()` 先用 `_image_size()` 确认文件头能说出
  宽高；指向 `.exe` 等非图片文件的 `<img>`（历史被改坏）原样不动 —— 实测在编辑块里重新设置
  这类图片的格式会让 `QTextDocument` 无限重排。
- **所有耗时计算移出编辑块**：先收集「位置 + 新格式」，再在一个编辑块里写回，每张图仍只写一次。
- **启动路径加三层保险**：`set_html()` 重绑失败就回滚成刚 `setHtml` 的文档（图片按原图显示）；
  `__restore_history()` 出任何异常都清空面板照常启动；启动画面改由 `__finish_splash()`
  在**事件循环启动后的第一个定时器**里关闭，即使后续显示流程出错也不会一直挡着界面。
- 实测：`load_text` 首次 0.50 s（自动建目录并生成 4 个预览）、二次 0.01 s；真实启动 3 s 内
  窗口可用；`console_images` 被同名文件占住、历史里塞进非图片的 `<img>` 等异常场景均不再卡住。

## v1.9.20 (2026-11-02)
控制台内嵌图片改为「只限文件大小（30 MB）+ 解码尺寸封顶 1000×1000」，大图不再因像素多而整张不显示，而是缩成预览显示、双击打开原图；图片**记录的一律是原图**，预览路径由原图纯函数推导，不依赖任何 json。

- **判据从「像素」改成「文件大小」**：原先超过 3200 万像素就整张丢弃（只留一句「图片过大，
  未显示」），8K 截图、相机原图这些本来完全能看的东西全被挡住。现在 `_ImageFit.MAX_FILE_BYTES
  = 30 MB` 是唯一的「能不能显示」判据：**≤ 30 MB 一律显示**，`MAX_PIXELS` / `MAX_BYTES` 已删除。
- **显示前先缩小**：`QTextImageFormat.name` 指向哪个文件，`QTextDocument` 就按那个文件
  **原分辨率解码** —— 缩小显示并不省内存（一亿像素仍要 400 MB 位图）。所以像素数超过
  1000×1000 的图，先用 `QImageReader.setScaledSize`（**解码时就按目标尺寸解**，不是先解全图
  再缩小）缩到长边 1000，写成缓存文件，渲染时指向缓存。小图**一个字节都不碰**，
  仍然是原来的「超链接」。
- **记录原图、显示才用缓存**：图片字符格式上新增自定义属性 `IMAGE_PROP` 记录**原图绝对路径**，
  「这个位置是哪张图」以它为准；只有渲染用的 `name` 才写预览路径。双击 / 右键「在新标签页中
  打开原图」/「复制图片路径」全部从 `IMAGE_PROP` 取原图，不从缓存文件名反推。
- **不依赖 json**：缓存路径是原图路径的**纯函数**（`sha1(原图绝对路径 + 大小 + 修改时间 +
  目标边长)` 前 16 位）—— 删了能重建、原图改了自动换新哈希，不需要任何失效逻辑。
  ⚠️ 曾实现过一份 `_index.json` 清单 + `_origin_of()` 反查，**已整段删除**：那等于维护第二份
  状态，丢了就还原不出原图。
- **历史 HTML 的两处改写（必须成对）**：`toHtml()` 只写 `name`、自定义属性不落盘（实测），
  所以存的时候 `get_html()` 把 `src` 从缓存路径**改写回原图路径**；读的时候 `set_html()` →
  `_rebind_images()` 再把 `src` 当原图、重算缓存并写回 `name`。删任一个都会出问题：
  前者让历史里只剩哈希文件名，后者让大图按原分辨率解码。旧版历史 HTML（`src` 就是原图、
  无自定义属性）由同一条链路正确接管。
- 预览缓存放在 `app_data.temp('console_images')`，格式取文件头里的真实格式，先写 `.tmp` 再
  `os.replace`；灰色说明行注明「预览：已缩放到长边 1000 像素，双击打开原图」。
- ⚠️ 修 `needs_cache`：不能拿 `decode_size` 的结果去比 `MAX_CACHED_PIXELS` ——
  那个值已被夹到 1000 以内，判断恒为假、分支永远不生效（实现时踩到并改掉）。
- ⚠️ 修 `_rebind_images` 的两处实测缺陷：① PyQt6 **没有** `QTextImageFormat(QTextCharFormat)`
  这个构造重载（报 `argument 1 has unexpected type`），拷贝格式要先 `.toImageFormat()`；
  ② `IMAGE_PROP` 必须**无条件**写回 —— 小图的预览路径就等于原图，只在「路径不同才写」会让
  恢复后的小图没有原图属性，双击拿到的是渲染路径。
- 实测 37 项断言全过：大图缩到 1000×750 且保持 4:3、缓存远小于原图、小图仍走原路径、
  重复显示不新增缓存、31 MB 文件被拒并提示、原图改动后缓存哈希自动变、历史 HTML 的 `src`
  是原图路径（全文不含缓存目录名）、缓存目录里没有任何 json、缓存全清后恢复仍自动重建、
  恢复后双击打开原图、旧版 HTML 兼容、`w=` 上限仍生效、无图片时 `get_html()` 与原输出一致。

## v1.9.19 (2026-11-02)
控制台图片补齐三种打开方式，并修掉图片菜单把控制台右键菜单整体顶掉的问题；图片浏览改为默认只看当前目录（可调到 2 层）、路径可点击换目录、默认帧率 5。

- **修掉控制台右键菜单整体消失**（v1.9.16 引入）：图片菜单的兜底跳到了 Qt 基类实现，绕过了
  `TextBrowser` 自己的实现。现象是在输出面板文本上右键**菜单不再出现**（实测 6 项 → 0 项）。
  改为「替换前先把原函数存下来、非图片处原样交还给**它**」—— 这也正是同一处更早那版
  「调自身导致 `RecursionError`」的反方向错误所指向的同一个答案。实测恢复 13 项，图片处两者并存。
- **控制台图片的三种打开方式**：新增面板右键「打开图片…」（选图**追加显示**，与已有渲染
  走同一个 `_add_image`）、**双击图片**打开原图、图片右键打开原图。⚠️ 双击**非图片**处必须
  原样交还默认行为（选中一个词）。图片文件已被删除时不调 `gui.open_image`，改为原位补一句
  `[图片] 已不存在：<路径>`。
- **图片浏览的子目录深度可调（默认 0、最大 2）**：路径下方新增「子目录深度」数字框，`0` 只看
  给定目录这一层（**新的默认行为**，原先固定递归 2 层），`1` / `2` 再往下收；改完立即重扫。
  API 侧 `set_depth` / `get_depth`，越界夹到 `[0, 2]`、非法值退回默认且不抛错。深度改为
  **调用时传参**（`_walk(folder, depth, token)`）而非类常量，并与 `_scan_target` 一起记成
  `_scan_depth` 参与校验 —— 扫描是异步的，途中改深度时在途结果仍然有效。
- **图片浏览左上角路径可点击换目录** + 右侧新增「…」按钮，两者走同一个 `_choose_folder`。
  ⚠️ 人工选目录**会退出「跟随工作路径」模式**；API 侧 `follow_cwd()` 不变。取消或目录不可读
  ⇒ 什么都不做。默认播放帧率 `2.0 → 5.0`。
- **长路径不再撑宽窗口**：只靠 `Ignored` 尺寸策略 + `_fit` 截断**挡不住** —— 布局算不可压缩
  下限时看 `minimumSizeHint()`、**不看 sizePolicy**，`QLabel` 拿到长文字后它等于那行文字宽度
  （实测 624 px 把宿主顶宽）。现在 `maximumWidth` + `Ignored` + `_fit` 三条一起生效，右下
  `info_label` 有同样隐患一并补上。另修掉「…」按钮被子布局拉成 640×640、把左栏顶成柱子的问题。
- 文档：`ui/AGENTS.md` §6.5 把「兜底必须调 `QtWidgets.QTextBrowser.contextMenuEvent`」这条
  错误写法改成「调用替换之前存下来的那个原函数」，并列清两种错误写法的不同后果；
  `ui/ReadMe.md` 的 `ImageBrowser` 一行同步（深度 0~2、可点击换目录、5.0 fps、长路径不撑宽）。
- 实测：控制台回归 11/11 与 13/13（选图追加 / 取消不追加 / 双击与右键均调 `open_image` /
  非图片处双击交还默认 / 菜单项与替换前逐项一致）；图片浏览 30 项断言全过（深度 0/1/2 的
  收取范围、隐藏目录与 `__pycache__` 跳过、深度框夹取与回环防护、后缀文案、布局位置），
  长短路径的最短窗口宽度均为 438 px（与路径长度无关）。

## v1.9.18 (2026-11-02)
修掉绘图中文的两处老毛病（Linux/macOS 上控件里的中文一律是方框、「自己建 figure」时报
`Glyph ... missing from font(s) DejaVu Sans`），并让 Linux 的 `build.sh` 在 Boost ≥ 1.90 上能过依赖探测。

- **控件中文方框（Linux / macOS）**：`MatplotWidget._ensure_chinese_font` 自带了一份按平台挑字体的
  副本，用了 `in_macos()` 却没导入 —— `in_windows()` 为假后紧接着就抛 `NameError`，被自己的
  `except` 吞成一句 `Error when ensure chinese font`，字体**从未被设上**。那份副本已删掉，改为转接
  `zmlx.plt.ensure_chinese_font()`（判断逻辑只留一份）。
- **自行建 figure 时中文缺字形**：`zmlx.fig.add_to_figure` / `add_to_axes` 是公开入口，调用者常
  自己 `plt.figure()` 再塞项目，绕开 `zmlx.ui.plot`，`rcParams` 一直是 `DejaVu Sans`；而
  `tight_layout` 属于「排版时刻」，警告就落在它的 `func(...)` 行上。现在两个入口在添加元素前先
  兜一次字体。
- **新增 `zmlx.plt.ensure_chinese_font()`**（附带 `list_chinese_fonts()`）：**幂等**，每次只比较
  `rcParams`，已经对就什么都不改、被 `plt.style.use('default')` 重置过就补回来。`set_chinese_font()`
  带 `@execute_once`、重置后补不回来，这是「设过一次仍报 DejaVu Sans」的根因。
- **字体名改读字体管理器缓存**：原先扫盘逐个字体文件建族名集合，而 `.ttc` 里打包了多个字族，
  `FontProperties(fname=...).get_name()` 只返回最前的一个 —— 实测 `Noto Sans CJK SC` 永远匹配不上，
  Linux 下中文退到楷体 `AR PL UKai CN`。`DejaVu Sans` 也从候选里移出、只作最后兜底。
- **`build.sh` 去掉 `-lboost_system`**：Boost 1.69 起 Boost.System 已是 header-only，Boost ≥ 1.90 的
  发行版（如 Ubuntu 26.04）不再提供 `libboost_system`，写进 `LIBS` 会直接 `cannot find -lboost_system`；
  源码里也没有任何地方调用它。
- **`build.sh` 缺库探测改为试链接**：原先用 `ldconfig -p | grep libboost_*.so` 判断，而只装了运行时包
  （如 `libboost-filesystem1.83.0` 没有 `-dev`）时它照样列得出来 —— 探测通过，构建到一半才报
  `cannot find -lboost_filesystem`。现在每个库都拿 `int main(){}` 真链一次，缺就是缺。

## v1.9.17 (2026-11-02)
文件可以直接**拖进窗口**打开：按扩展名交给已注册的处理器，与「文件 → 打开」走同一条分派路径。

- **拖放即打开**：从资源管理器把一个或多个文件拖到窗口任意位置松手，等同对每个文件执行
  `gui.open_file(...)` —— 打开方式完全由 `gui.add_file_handler(...)` / `alg.reg_file_type(...)`
  的注册表决定，**插件注册的新类型自动支持拖放**，拖放本身不认识任何扩展名。
  新增命令 `gui.drop_files(paths)`，返回 `{'opened', 'unknown', 'dirs', 'skipped'}`。
- **落点全覆盖**：事件由装在 `QApplication` 上的 `FileDropHandler` 拦截，因此拖到**编辑器正文 /
  控制台输出区 / 命令行输入框**上同样生效（这些控件本来会接受文件拖放并把路径当文本插进去）。
  判据三条同时成立才接管：拖放事件 + 落在主窗口内 + 至少一个本地文件 URL；标签页内部拖动、
  拖选文字、往输入框拖文本一律走 Qt 原生行为。模态子对话框不参与。
- **批量策略**：多义扩展名（同一后缀注册了多种类型）**每类只问一次**；未知扩展名
  **不弹窗**，汇总成一句状态栏提示（`类型未注册: a.xyz 等 5 个`）；单个文件失败不影响其余
  （明细打印在控制台）。重复拖入的同一路径自动去重。
- **目录**：沿用 `gui.open_file` 的既有语义 —— **切换工作目录**（不是打开它），多个目录只切最后一个。
- 拖入过程中状态栏提示「松开以打开 N 个文件」，打开期间显示等待光标，完成后 5 秒内显示结果摘要。
- 内部：`FileHandler` 抽出私有 `_resolve(filepath, cache)` 供单文件/批量共用，新增公开
  `open_files(filepaths, *, set_cwd=True)`；`open_file` 的签名与行为**未变**。

## v1.9.16 (2026-11-02)
控制台输出支持内嵌图片（`print('[[image: path="a.png", w=640]]')`），并把「显示 → 通知」页重排为带常驻工具条的表格控件、修掉长消息只显示一行的问题。

- **控制台内嵌图片**：`print` 里**独占一行**的 `[[image: path="a.png", w=640]]` 被渲染成图片；
  `path` 可省引号（`[[image: a.png]]`），`w` / `width`、`caption` / `title` 为可选键。
  只认整行 —— 行内出现一律按普通文本显示，不误吞用户输出。
- **图片就是一个超链接**：控件只把**绝对路径**填进 `QTextImageFormat.name`，不 `addResource`、
  不编码、不缓存、不复制；图片文件由 `print` 的调用者负责。保存历史仍是 `toHtml()`、恢复仍是
  `setHtml()`，**图片路径零特殊处理**（实测 `toHtml()` 写出的 `src` 就是裸绝对路径，
  `setHtml()` 直接能加载）。
- **显示尺寸**：等比缩放进「面板宽 × 面板高」包围盒，保证**整张可见**（宽图按宽度适配、
  高图收窄）；高的下限 240 px（极端细长图允许滚动，不缩成一条细线）；显式 `w=` 只是上限，
  且**任何情况下都不撑开面板**（最后统一夹到可用宽度）。
- **异常一律退化为文本**：文件不存在 / 不是图片 / 超过 32 MPix 时不插入图片，原位只留一行
  灰字 `[图片] <路径>`；语法错误按普通文本原样显示。不弹窗、不报错、不画裂图。
- **行缓冲**：`print(..., end='')`、`\r` 进度输出会把半行交给输出面板，因此按 `\n` 逐段处理；
  `Console.__kernel_exited` 与 `save_text` 会冲刷残留半行，最后一段不会丢。
- **`_trim()` 零改动**：图片在字符计数里只算 1 个字符，裁剪行为与没有图片时完全一致。
- 输出面板右键新增勾选项「显示图片」（`console_image`，与「ANSI 颜色」同构），关掉后整行标记
  原样显示；图片上右键可「在新标签页中打开原图 / 复制图片路径」。
- **修：控制台右键必抛 `RecursionError`**（同日引入、同日修复）：图片菜单的兜底分支调用了
  `browser.contextMenuEvent(event)`，而实例上的这个方法已被替换成兜底分支自身 ⇒ 无限递归。
  现改为显式调用 `QtWidgets.QTextBrowser.contextMenuEvent(browser, event)`。
- **「显示 → 通知」页重排**（`ui/setups/message.py`）：控件由裸露的 `QTableWidget` 改为组合控件
  （顶部工具条「共 N 条通知 + 复制全部 / 刷新 / 清空」→ 消息表格），新增「复制」能力
  （每行复制按钮 / 复制全部 / 右键复制选中）。⚠️ 类名 `MessageEdit`、命令名 `gui.show_messages`、
  标签页标题「通知」均未变（`gui_restore` 靠它们恢复历史标签页）。
- **修：通知页长消息只显示一行**（原有缺陷）：行高原本锁死在一行，多行通知被截断。现在按消息列
  的真实宽度逐行计算行高，窗口缩放后经 `resizeEvent` + `singleShot` 重算。
- **修：通知页行高被撑到近两倍**：`ResizeToContents` 按自动换行 `QLabel` 的 `sizeHint` 定高，
  与真实换行结果不符（实测 126 px 的内容占 196 px）。改用 `Fixed` + `QFontMetrics.boundingRect` 自行计算。
- **修：通知页时间列宽出三四倍**：`ResizeToContents` 按中文表头 `时间` 算宽度。序号 / 时间改为固定宽度。
- 通知页正文补 `TextSelectableByKeyboard`（单元格文本默认「可选中、不可聚焦」，Ctrl+C 到不了它）；
  序号 / 时间单行文本垂直居中，正文与行内按钮顶对齐。
- **示例浏览按「最近运行」分组**（`ui/plugins/builtin/demo_menu.py`）。

## v1.9.15 (2026-11-02)
`zmlx/ui/` 代码整理、`gui` 调用出口统一，以及**命令表文档补全**（**不升版本号**）。

- `ui/pyqt.py`：Qt 探测的两个 `if qt_name is None: if "PyQtX" in sys.modules:` 嵌套合并成
  `if qt_name is None and ...:`；裸 `except Exception` 标注 `# noqa: BLE001`。
- `ui/GuiBuffer.py`：`__all__` 改为一个名字一行的排序形式。
- `ui/alg.py`：函数内局部 import 按字母序排列、补空行。
- `ui/main.py`：补一处空行。
- **`gui` 调用一律走 `gui.xxx(...)`**：`plugins/builtin/api_doc.py` 里的
  `gui.get().list_all()` / `gui.get().get_func(name)` 改为 `gui.list_all()` /
  `gui.get_func(name)` —— 这两条命令经 `GuiBuffer.__getattr__` → `Agent` →
  `command(...)` 派发到 GUI 线程执行，先 `gui.get()` 取 `GuiApi` 再调方法是绕过派发层，
  跨线程时没有线程保证。同款写法一并改掉：`plugins/builtin/architecture.py`、
  `ui/setups/readme_browser.py`、`scen/ai_assistant/script.py`，含 `architecture.py` 里
  教用户这么写的一句文档。无界面时 `GuiBuffer.command` 返回 `None`（不抛异常），
  `api_doc` 的降级提示据此把「没有界面」与「命令表是空的」分开报。
- **`api_doc.py` 不再依赖 `zmlx.ui.alg.create_action`**：新增本文件的 `_make_action`
  （`QAction` + `load_icon`，图标取不到就退化成纯文字）。`create_action` 执行完会
  `gui.refresh()` 整窗刷新并写一条 `log`，而本页的动作全是本地的（复制命令名、回首页、
  刷新列表）；工具栏与右键菜单因此合并成一份实现。
- **修 `api_doc.py` 右键菜单丢项**：`view.context_actions` 由赋值改为 `extend`。
  `TextBrowser.__init__` 自带一条「清除内容」（绑它自己的 `clear`），赋值会把它顶掉，
  而状态栏文案还写着「右键「清除内容」清空正文」。
- `api_doc.py` 模块文档新增「除 `gui.xxx` 之外，本文件还调用了什么」清单：`execute_once`
  （插件入口）、Qt 三个模块（自建控件）、`TextBrowser`（统一正文控件）、`load_icon`
  （图标资源，命令表里没有图标命令）、`app_data`（记录上次看的条目）、`inspect` 与
  `html`/`re`/`json`/`textwrap`（读签名、拼 HTML）—— 没有一条是在碰主窗口。
- **给全部 `gui` 命令补 docstring**（144 条命令，含插件注册的那些）：改前 52 条没有说明、
  `Args:` 段只有 14 条、`Returns:` 8 条、带用例 0 条；改后 **无 docstring 的为 0**，
  `Args:` 84 条、返回值 71 条、用例 81 条。「帮助 → GUI 接口」页因此从「名字 + 签名」
  变成了能读懂的说明书 —— 那页的说明文字全部运行时从 docstring 现读，不补文档它就只剩骨架。
- **`window` / `is_maximized` / `show_maximized` 由 lambda 改为公开方法**（`main.py`）：
  lambda 挂不了 docstring；改后走「公开方法自动注册」，来源标记也从「闭包」变成「主窗口」。
  ⚠️ `gui.mark_direct("window")` 登记的是**命令名**，不受影响。
- **`close` / `resize` / `device_pixel_ratio` / `set_style_sheet` / `get_style_sheet`**
  （`gui_api.py`）：这五个是 Qt 的 C++ 内建方法（`__doc__` 只读），在注册处**包一层命名闭包**
  并写文档，签名与行为不变。
- **7 个 `open_*` 的说明按类型生成**（`alg.py`）：`reg_file_type` 里它们本是同一个闭包，
  改为在注册前赋值 `open_file.__doc__`，各自带上描述 / 扩展名 / 命令名。
- **`api_doc._first_line` 剥离行内标记**：列表摘要那一列是纯文本（只有正文走 RST→HTML），
  不剥离就会显示 `` ``MainWindow`` ``、`**重点**` 这种字面符号。
- 已有详细文档的方法（`add_action` / `plot` / `get_widget` / `find_widget` / `reset_layout` /
  `set_side_tabs_visible` / `console_state` / `update_system_state` …）**保留原文**，只做增补。

## v1.9.15 (2026-11-01)
新增内置插件「GUI 接口」（菜单 → 帮助 → GUI 接口），把 `gui` 命令表做成可搜索的图形化说明书。

- **`plugins/builtin/api_doc.py`**（默认启用，完全自含）：三栏说明页 —— 左侧按用途分组
  （显示窗口 / 标签页 / 对话框 / 绘图 / 运行控制 / 打开文件 / 插件 / 自省 / 基础），
  中间是命令列表（名字 · 签名摘要 · 来源），右侧是详情（签名 / 参数表 / 返回值 / 说明 /
  用例 / 注意事项）。顶部可搜索（空格分词全部命中）、按用途与来源筛选、只显示带示例的。
- **命令 `gui.show_api_doc(name=None)`**：`name` 给具体命令名时直接定位到那一条。
- **信息全部运行时读取**：名字来自 `gui.list_all()`、函数来自 `gui.get_func()`、签名与
  说明用 `inspect` 现读；别名（如 `status` ↔ `show_status`）按函数身份自动识别，
  来源标记（主窗口 / gui_api / 内建 / 插件 / 外部）也运行时判定。文件内自带的
  `_PREBUILT_CATALOG_TEXT` 只存「名字 → 分组」，供名字规则没覆盖到的新命令兜底分组，
  不存任何说明文字 —— 所以库怎么变都不会丢命令。
- **刷新时机只有两处**：打开标签页、点顶部「刷新」。刻意不接 `refresh()` 钩子 ——
  `MainWindow.refresh` 会在每个菜单动作之后被调，说明页没必要跟着重扫。
- 双击一行把 `gui.名字(` **复制到剪贴板**，参数表里也有「复制」；本页只写剪贴板，
  **不执行**任何命令。带源码位置的命令可一键用代码编辑器打开。

## v1.9.14 (2026-11-01)
依赖表的列宽交给优先级分配（依赖包按名字取宽、空间不够就藏备注），安装输出改走界面控制台。

- **列宽按优先级分配**（`_layout_columns` / `COLUMN_WIDTHS` / `COLUMN_PRIORITY`，挂在
  自己的 `resizeEvent` 上）：不再用 Qt 的 `Stretch` —— 那会让第一列把富余全吃掉。
  「依赖包」用 `QFontMetrics` 实测最长包名来定宽（只求「够显示名字」，本机 206 px，
  换字体 / 改 DPI 会跟着变）；「操作」恒保 64 px；富余只给「备注」，**空间不够时备注
  整列隐藏**（实测 760 px 尚显示、640 px 起隐藏，宽回来自动恢复）。
- **安装输出改走 `print` 进界面控制台**：删掉控件底部的「安装日志」`QPlainTextEdit`，
  `InstallThread` 去掉 `sig_output`，改为逐行 `print` —— 控制台本来就支持 ANSI 颜色，
  且有滚动历史与右键复制。pip / conda 自己的彩色输出**原样透传**（不 strip）；线程边界
  的几行自己上色（青=开始 / 绿=成功 / 黄=回退 / 红=失败），用 SGR 基础色以便控件按
  明暗主题换算。好处之一：安装几分钟期间用户可以同时看别的页面。
  右键菜单相应去掉「清空日志」。

## v1.9.13 (2026-11-01)
「运行环境」插件改为默认加载、依赖清单按扫描补齐，表格支持点标题排序且不再撑宽上级控件。

- **「运行环境」改为默认启用**（`plugins/builtin/runtime_env.py`：`# ** enabled = False`
  → `True`）：这是「装完软件就该看得见」的入口 —— 依赖缺失时它是用户的第一落点，
  藏在「设置 → 插件」里等于让最需要它的人找不到它。取消勾选「默认加载」仍可关掉。
- **可选依赖 12 → 14 项**：新增 `requests`（`scen/ai_assistant/chat.py`，AI 辅助插件的
  必需项）与 `torch`（`scen/uv_equilibrium` 的训练脚本）—— 它们此前只被 `scen/ai_assistant`
  自己的 `env_check` 知道，运行环境页看不见。
- **新增 `IMPORT_TO_PACKAGE`**（导入名 → 发行包名的映射：`cv2 → opencv-python`、
  `PIL → pillow`、`sklearn → scikit-learn` 等）。扫描只能拿到导入名，而「装没装 / 怎么装」
  问的是发行包名，直接拿导入名去 pip 装有时能撞对、有时会装错（`sklearn` 装到的是个空的
  占位包）。
- **`check_dependency` 加固**：`package` 缺省时不再 `KeyError`，而是走 `package_of(name)`
  从导入名反推发行包名；`dependency_list()` 的去重键也一并规范化。
- 清单口径写进了 `OPTIONAL_DEPENDENCIES` 上方的注释（不列核心依赖、不列 `_Trash/`、
  不列 `zmlx` 自己的模块、不列 PyQt5 兼容分支），以后加第三方 import 时照着同步。

**依赖表：点标题排序 + 不再撑宽上级控件**

- **新增「备注」列**（2026-11-01，按用户要求）：一句话说清这个包在 zmlx 里干什么。
  文字来自依赖条目自己的 `note` 字段 —— 可选依赖写在 `OPTIONAL_DEPENDENCIES`，必需依赖
  新增 `zmlx/data/dep.py` 的 `package_notes`（**唯一来源**，16 个核心包各一句，查不到时
  退回「zmlx 的核心依赖」）。「操作」列随之后移到第 7 列；`_copy_list` 原来写死「第 5 列
  是按钮」，改为按 `COLUMN_KINDS` 找「操作」列，以后再加列不会错位。
- **七列都能点标题排序**。排序键与显示文字**分开存**：新增 `_SortItem`
  （`QTableWidgetItem` 子类，自己覆写 `__lt__`）。⚠️ 不覆写不行 —— PyQt6 的默认实现对
  **自定义角色**不比较，会把值转成字符串（实测版本号退化成字符串序，`0.4.10` 排在
  `0.46.4` 后面）；而塞进 `DisplayRole` 又会顶掉显示文字。
- **按语义排，不按字形排**：「状态」列未安装 → 已安装（不是按汉字编码），「分组」列
  必需 → 可选，版本号按**数值**（`2.3.3 < 2.14.1`、`3.1.5 < 3.1.10 < 3.11`）。版本号
  补零到定长再比 —— Python 元组是「逐项先比、长度只在前缀相同时才生效」，不补零时
  `(3, 11)` 会排到 `(3, 1, 10)` 后面。无版本号的 `-` 排在最前（那通常就是没装的包）。
- **铺表时先关排序再开**（`_fill_table`）：开启排序时每 `setItem` / `setCellWidget`
  都可能触发重排，行号铺到一半就变，按钮会挂到别的行上（重排后验收：未安装的行有按钮、
  已安装的没有）。同时显式 `removeCellWidget`，避免重建时残留旧按钮。
- **宽度不再撑大上一级控件**：去掉了 220 px 的固定首列；各列可被压到 40 px
  （`setMinimumSectionSize(40)`）；竖向滚动条常驻（否则它出现 / 消失会让整页最小宽度
  抖动）；状态标签允许被压窄（完整文字进 tooltip，列被截断时靠 tooltip 看全文）。
  实测控件最小宽 **396 → 262 px**。工具栏文案同时缩短（「只显示未安装」→「只看未安装」，
  「一键安装缺失(必需)」→「安装缺失项」），按钮加 `setMinimumWidth(56)`。
- **列宽按优先级分配**（新增 `_layout_columns` / `COLUMN_WIDTHS` / `COLUMN_PRIORITY`，
  挂在自己的 `resizeEvent` 上）：不再用 Qt 的 `Stretch` —— 那会让第一列把富余全吃掉。
  - **依赖包**只为「显示名字」取宽度：用 `QFontMetrics` 实测最长的包名（本机 206 px），
    换字体 / 改 DPI 会跟着变，而不是写死一个偏大的像素值；
  - **操作**列恒保 64 px，与依赖包一起构成「优先保证」的两列；
  - 富余空间**只给备注**；**空间不够时备注整列隐藏**（实测 760 px 尚显示、640 px 起
    隐藏，宽回来自动恢复），而不是被压成一条看不懂的窄缝。
  - 顺带修正：整页最小宽从 262 px 降到 **~200 px**（因为依赖包的最小宽度按名字放宽到
    110 px 之外不再多占），窄窗口下溢出交给横向滚动条。
- **安装输出改走 `print` 进界面控制台**（2026-11-01，按用户要求）：删掉控件底部的
  「安装日志」`QPlainTextEdit`，`InstallThread` 去掉 `sig_output` 信号，改为逐行 `print`
  —— 控制台（`OutputWidget`）本来就支持 **ANSI 颜色**且有滚动历史 / 右键复制，单开一个
  只读文本框是重复造轮子。细节：
  - pip / conda 自己的彩色输出**原样透传**（不 strip ANSI，实测子进程的 `\033[32m` 在
    控制台里渲染成绿色）；
  - 线程边界那几行自己上色：青色=开始安装 / 命令回显（亮黑），绿=成功，黄=回退，红=失败
    （`ANSI_INFO` / `ANSI_DIM` / `ANSI_OK` / `ANSI_WARN` / `ANSI_ERROR`）。用 SGR **基础色**
    而不是 256 色 / 真彩，控件会按明暗主题自动换算成合适色值；
  - 好处之一：安装可能几分钟，用户可以同时看别的页面，输出也不会随控件关掉而消失。
  - 右键菜单去掉「清空日志」（控件没有自己的日志了，清控制台用控制台自己的入口）。
- 每一格都补了 tooltip（窄窗口下是看全文的唯一出路）。

## v1.9.12 (2026-11-01)
绘图链收敛到「一次 GUI 命令」并清掉由此失去前提的两层防御；新增插件「实时绘图」，把绘图从计算线程里挪出去。

**`gui.plot` 回退：删掉三段式派发**

- 10-18（v1.11.4）为配合「渲染搬到调用者线程」的 `MatplotWidget`，新增了 `GuiBuffer.plot`：
  先 `command('get_plot_widget')` 建页、再在调用线程 `make_on_figure` + `plot_on_figure`
  渲染、最后 `savefig` 导出。10-31（v1.9.10）画布改回 `FigureCanvasQTAgg`、绘制回到 GUI
  线程之后，这三段全落在 GUI 线程里，跨界变成纯粹的多余往返（`plot_on_figure` 的
  `_run_in_gui` 还会再派发一次）。
- 现在**删除 `GuiBuffer.plot`**（`gui_buffer.py` −73 行）：`gui.plot(...)` 恢复成命令代理
  —— `GuiBuffer.__getattr__` → `Agent` → `command('plot')` → `MainWindow.plot`。建页、
  跑 `kernel`、`canvas.draw()`、按需存图都在**一次** GUI 命令里顺序执行，调用线程只阻塞一次。
- 对外行为不变：`zmlx.ui.plot` / `plot_on_figure` 的签名、返回值（`Figure`）以及
  `clear` / `suptitle` / `tight_layout` / `fname` / `dpi` / `savefig` / `position` 的语义都照旧。
  唯一差别是**无界面时直接调 `gui.plot`** 不再退化成写文件（命令没有接收方，返回 `None`）；
  `zmlx.ui.plot` 与 `plot_on_figure` 仍按原逻辑走 `_plot_no_gui`，不受影响。
- 同步修正四处过时说明（都还写着「渲染在调用者线程」）：模块级 `plot()`、
  `MainWindow.get_plot_widget`、`TabWidget.make_on_figure`、`scen/ai_assistant/chart.py`。

**`MatplotWidget` 精简：删首帧覆盖层**

- 删掉只服务「建页与首绘分属两次 GUI 命令」的整套覆盖层（`_cover` / `_blank_layer` /
  `paintEvent` / `showEvent` / `resizeEvent` / `_needs_cover` / `_frame_ready` /
  `_fill_first_frame` / `_has_white_area` / `_is_white`）。上面那条回退之后这个前提已不存在
  （实测：一次 `gui.plot` 期间 **0 次**事件循环轮转，`QTimer.singleShot(0, ...)` 要等返回
  之后才触发），覆盖层因此是纯冗余。
- 改为**构造时套一次主题**（`__init__` 里 `_apply_theme()`）：`FigureCanvasQTAgg` 首次自绘时
  `rcParams` 已是目标主题，画面不会再先白一下；之后每次绘制前仍重判一次，暗色自适应完整保留。
  并去掉 `_render` 里重复的第二次 `_prepare_frame`（`style.use` 在回调前已生效，
  回调里 `add_subplot` 新建的 axes 会直接继承当前 `axes.facecolor`）。
- 连带修两处：① `_in_dark_mode` 原来遍历 `app.topLevelWidgets()` 猜主窗口 —— matplotlib 的
  `FigureManagerQT` 内部也有一个**同样叫 MainWindow** 的 QMainWindow（构造一个
  `MatplotWidget` 就多出一个），会挑错窗口把暗色判成 `#ffffff`，改为向 `gui.window()` 要；
  ② `plt.style.use(...)` 会把 `set_chinese_font()` 设的 `axes.labelsize` / `legend.fontsize`
  重置回 `medium`（该函数只有 `@execute_once`，补不回来），`_ensure_chinese_font` 一并恢复。

**`MatplotWidget` 去掉跨线程投递层**

- 删除 `_run_in_gui` / `_in_gui_thread`（v1.9.10 为「渲染可能在调用者线程」加的防御层），
  以及只为投递而拆的 `_savefig` / `_savefig_by_dlg` / `_copy_to_clipboard`（三者合并回公开方法）。
  判据是穷举而非"觉得"：本仓 `plot_on_figure` 的 4 处调用点全在 GUI 线程；外部
  `igg-hydrate-works` 的 24 处里，**同时出现 `MatplotWidget` 与线程 API 的文件数 = 0**。
- **行为变化**：从非 GUI 线程直接调控件方法不再被自动投递，而是就地执行（Qt 控件离开 GUI
  线程属未定义行为，应当报错暴露而不是被悄悄兜住）。跨线程绘图请用
  `gui.call(lambda: widget.plot_on_figure(...))` 或 `gui.start` 的 `post_task`；
  「后台线程绘图」这条能力由 `gui.plot`（`GuiApi.command` 派发）提供，控件不必重复一遍。
- `test_1()` 的示例从「后台线程推帧」改为「`QTimer` 定时推帧」（定时器本来就在 GUI 线程）。

**新增插件「实时绘图」**

- 新增 `plugins/builtin/realtime_plot.py`（默认加载，单文件自含）。模型：**`caption`
  （= 队列名 = 标签页标题）→ 独立 `queue.Queue` → 一个常驻 daemon 泵线程**；泵线程从各队列
  弹帧，再走**一条** `gui.plot(kernel, data, caption=…, clear=…)` 命令在 GUI 线程画完。
- 新命令（都带 `rtp_` 前缀，且登记 `mark_direct`）：`gui.rtp_push(kernel, data, caption=None,
  *, clear=True, suptitle=None, tight_layout=None, max_pending=None)`（压一帧，返回待绘帧数）、
  `gui.rtp_queue_n` / `gui.rtp_queue_clear` / `gui.rtp_queue_stat`；另有 `gui.show_rtp_panel()`
  （不直连：它建控件）。⚠️ 前缀不是审美：`gui` 命令表是全局命名空间，`MainWindow` 公开方法会
  自动注册进来，**重名时后注册者静默顶掉先注册者**。
- 节流**按标签各算**：同一标签两次绘制间隔 ≥ 0.1 s（可调）、队列空则轮询 0.02→0.5 s 翻倍退避、
  **新数据压入当场唤醒**、每标签积压上限默认 8 帧、超出**丢最旧**（实时要最新，不要完整）。
  实测单次 push 0.03–0.19 ms（最坏 2.1 ms，GIL 争用）。
- `mark_direct` 的判据：这四个函数**一行 Qt 代码都没有**（只碰 `queue.Queue` 与一把
  `threading.Lock`）。走派发的话，界面正在画重图那 200 ms 里每次 push 都要等着，
  正好抵消本插件存在的意义。
- 入口：菜单**「显示 → 实时绘图控制面板」**——右侧标签页里的 `RtpPanel`：状态行（线程 /
  目标与实测帧率 / 待绘·累计·丢弃）、三个旋钮（目标帧率、空闲休眠、积压上限，**直接写
  `_pump` 字段**，泵线程每轮现读）、三个按钮（重启线程 / 清空队列 / 演示）、每标签统计表、
  「最近绘制了哪些帧」（帧序号 + 耗时 + 时刻，**跳号即被丢掉**）。面板 200 ms 刷新，
  只在可见时刷。`_PlotPump.restart()` 每代线程带自己的 `Event` 且**不 join**（按钮在 GUI
  线程，泵线程可能正阻塞在 `gui.plot`，一 join 就死锁）。
- 演示（`show_demo`）走 `gui.start`（长任务占 `Console` 槽位），循环里 `gui.break_point()`、
  每 20 帧 print 一行进度；它是面板上的按钮，**不单独占菜单项**。

## v1.9.11 (2026-10-31)
修复 v1.9.10 引入的绘图字体回归：中文标签变方框（`Glyph ... missing from font(s)
DejaVu Sans`）、坐标轴刻度上的负号变方框。

- 二者同一根因：`plt.style.use(...)`（`MatplotWidget` 每次绘制前按主题调一次）会把
  `font.sans-serif` 整个重置成 DejaVu Sans 打头、把 `axes.unicode_minus` 重置回 `True`；
  而 `set_chinese_font()` 被 `@execute_once` 包着，进程内只真正执行一次，之后补不回来。
- 负号：`axes.unicode_minus=True` 时负号写成 `U+2212`，而 **SimHei 没有这个字形**
  （实测字形覆盖：SimHei 缺 `U+2212` 与 `³`，YaHei 齐备，DejaVu 缺中文）。
  故每次绘制前统一把负号切回 ASCII `-`。
- 新增 `MatplotWidget._ensure_chinese_font()`：在 `style.use` 之后、以及 `_prepare_frame`
  开头各调一次，把中文字体名排到 `font.sans-serif` 队首并关掉 Unicode 减号。
  字体是否存在用 `fm.get_font_names()` 读缓存判断（实测 0.041 ms/次，不扫盘）；
  已经正确时什么都不改，也不覆盖用户自己设的其余选项。
- 字体恢复与主题判断**分开兜底**：主题判断抛异常时不会连带跳过字体设置。

## v1.9.10 (2026-10-31)
`MatplotWidget` 的绘制退回 **GUI 线程**（`FigureCanvasQTAgg`），修好暗色主题自适应，
并让暗色下新建绘图标签页不再先闪一下白。

- 画布由「Agg 渲染 + 位图自绘」改回 `FigureCanvasQTAgg`：`plot_on_figure` 把「回调 + 绘制」
  投递到 GUI 线程执行并**等它画完**才返回（已在 GUI 线程则直接调用）。于是 figure 只在
  GUI 线程被碰，不需要加锁、也不要求调用方先 `copy()` 数据；代价是重图期间界面会停住。
  `figure` / `canvas` 现在返回真正的 matplotlib 画布；公开签名一字未改，
  `Interp1Edit` / `Interp2Edit` / `DataEdit` / `quick_look` 不受影响。
- 暗色主题：原来按**控件自己的** `palette()` 判断，而样式表（「设置 → 样式表」写的
  `zml_window_style.qss`）**不改 palette** —— 实测无论先建控件还是先套样式表，读到的都是
  浅色（亮度 239），暗色永远判不出来。改为看 `QApplication` 调色板 / 主窗口调色板 /
  主窗口样式表里的背景色，任一为暗即用暗色，并且**每次绘制前**重判一次：换主题后下一次
  绘图自动跟上，切回浅色时把 figure 与各轴底色显式还原成白（不会残留深色）。
- 新建标签页闪白：`FigureCanvasQTAgg` 一建好，matplotlib 就把**一整幅白底**画进了它的
  像素缓冲，而它带 `WA_OpaquePaintEvent` —— Qt 一要显示它就直接把这块缓冲送屏；
  `draw()` 只是把同一块屏幕像素重涂一遍，所以屏幕仍是「先白后暗」。改为**第一次绘制成功
  之前**用一层与主题同色的覆盖层挡在画布上方（无系统背景、不参与布局、不接鼠标事件，
  `showEvent` 里先判主题再上色），`draw()` 成功后收起，此后完全走 matplotlib 原来的
  贴图路径；另加两道兜底（绘制前把 Agg 缓冲也填成暗色、`paintEvent` 在尚未 ready 时
  自己垫同色底），窗口放大触发的重排与重绘同样不会露白。
- 顺带修掉 `FigureCanvasQTAgg(figure, parent=...)` 在本仓 matplotlib 3.10 下抛
  `unexpected keyword argument 'parent'`（父子关系改由布局接管）。

## v1.9.9 (2026-10-31)
示例浏览（`DemoView`）的说明列宽度变化时重算行高，窗口缩小后描述文字不再显示不全。

- 原来只在「打开那一刻」量一次行高：宽窗口打开、再缩小窗口时，缩窄的说明列里文字被截掉
  （反而是「先缩小再打开」正常）；
- 改为盯住**说明列的宽度**（`sectionResized` + 自身 `resizeEvent`），宽度真的变了才让各行
  重新测量；宽度没变时什么都不做，避免拖动窗口时为 110 行重建「运行」按钮；
- `HtmlDelegate.sizeHint` 改用说明列的**真实列宽**测量（原来整行测量时拿到的是默认 100 px），
  量出来的行高与实际绘制宽度一致。

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
