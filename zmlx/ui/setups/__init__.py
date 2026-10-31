from zmlx.system import execute_once


@execute_once(file=__file__)
def setup_ui():

    try:
        # ⚠️ 2026-10-31 起：通知消息中心本身就在**本目录**（``setups/message.py``），
        #    不再是 ``tabs/`` 里的控件 —— 原 ``zmlx.ui.tabs.message`` 已删除、不留垫片。
        #    它带来的是「消息落盘 API + 「显示 → 通知」菜单」这整块装配，属**必加载**。
        from zmlx.ui.setups.message import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup message: {err}")

    try:
        # ⚠️ 2026-10-31 起：变量浏览器也在**本目录**（``setups/mem_view.py``），
        #    不再是 ``tabs/`` 里的控件 —— 原 ``zmlx.ui.tabs.mem_view`` 已删除、不留垫片。
        #    它连带维护 ``app_data`` 的两个编辑器键（全局能力），并挂「显示 → 变量」菜单项
        #    与命令 ``gui.show_memory``（原先由 ``MainWindow.show_memory`` 提供）。
        from zmlx.ui.setups.mem_view import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup mem_view: {err}")

    try:
        # ⚠️ 2026-10-31 起：脚本执行历史也在**本目录**（``setups/code_history_view.py``），
        #    不再是 ``tabs/`` 里的控件 —— 原 ``zmlx.ui.tabs.code_history_view`` 已删除、
        #    不留垫片。它注册命令 ``gui.show_code_history``（原先由
        #    ``MainWindow.show_code_history`` 提供），供控制台与代码编辑器的右键菜单调用。
        from zmlx.ui.setups.code_history_view import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup code_history_view: {err}")

    try:
        # ⚠️ 2026-10-31 起：控制台输出历史也在**本目录**（``setups/output_history_view.py``），
        #    与上面那条是**同一条链** —— 控制台右键菜单里「脚本运行历史 / 输出历史」两项并列。
        #    原 ``zmlx.ui.tabs.output_history_view`` 已删除、不留垫片。
        #    它注册命令 ``gui.show_output_history``（原先由 ``MainWindow.show_output_history``
        #    提供），并开「输出历史」标签页（目录取 ``app_data.root('output_history')``）。
        from zmlx.ui.setups.output_history_view import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup output_history_view: {err}")

    try:
        # ⚠️ 2026-10-31 起：「设置 → 系统」也在**本目录**（``setups/env_edit.py``），
        #    不再是 ``tabs/`` 里的控件 —— 原 ``zmlx.ui.tabs.env_edit`` 已删除、不留垫片。
        #    它改的是**全局配置**、属产品功能（不该被用户在「设置 → 插件」里关掉），
        #    并带着菜单项与快捷键 ``Ctrl+E`` —— 所以归本目录而不是插件 / tabs。
        #    注册命令 ``gui.show_env_edit``（原先由 ``MainWindow.show_env_edit`` 提供；
        #    那个名字被历史标签页、ReadMe 链接与界面桥的示例命令按名字引用）。
        from zmlx.ui.setups.env_edit import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup env_edit: {err}")

    try:
        # ⚠️ 2026-10-31 起：通用字符串表格也在**本目录**（``setups/string_table.py``），
        #    不再是 ``tabs/`` 里的控件 —— 原 ``zmlx.ui.tabs.string_table`` 已删除、不留垫片。
        #    它注册命令 ``gui.show_string_table``（原先由 ``MainWindow.show_string_table``
        #    提供），是给插件 / scen / 脚本用的**通用出口**：
        #    ``plugins/builtin/admin_menu.py``（4 处）与 ``scen/ai_assistant/action.py``
        #    都按命令名调它 —— 做成插件的话，那些调用方在插件关掉时就会「找不到命令」。
        from zmlx.ui.setups.string_table import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup string_table: {err}")

    try:
        # ⚠️ 2026-10-31 起：「设置 → 插件」也在**本目录**（``setups/plugin_list_edit.py``），
        #    不再是 ``tabs/`` 里的控件 —— 原 ``zmlx.ui.tabs.plugin_list_edit`` 已删除、
        #    不留垫片。它是**插件机制的开关面板本身**：做成插件就成了「关掉『开关』」的循环
        #    （用户一取消勾选，就再也找不回「启用 / 禁用插件」这个入口），所以**必加载**。
        #    注册命令 ``gui.edit_setup_files``（原先由 ``MainWindow.edit_setup_files`` 提供；
        #    名字是「命名遗留」，被 ReadMe 链接、标签页存档串与外部脚本引用）。
        from zmlx.ui.setups.plugin_list_edit import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup plugin_list_edit: {err}")

    try:
        # ⚠️ 2026-10-31 起：「帮助 → ReadMe」（欢迎页）也在**本目录**
        #    （``setups/readme_browser.py``），不再是 ``tabs/`` 里的控件 ——
        #    原 ``zmlx.ui.tabs.readme_browser`` 已删除、不留垫片。
        #    它是**欢迎页**（``main.py`` 的 ``__on_show`` 启动时按 ``show_readme`` 设置自动
        #    打开），且带菜单项 / ``F1`` / 工具栏按钮 —— 做成插件会与「启动时显示欢迎页」
        #    这个设置互相打架，所以**必加载**。
        #    注册命令 ``gui.show_readme``（原先由 ``MainWindow.show_readme`` 提供）。
        from zmlx.ui.setups.readme_browser import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup readme_browser: {err}")

    try:
        # ⚠️ 2026-10-31 起：「帮助 → 登录」也在**本目录**（``setups/license_register.py``），
        #    不再是 ``tabs/`` 里的控件 —— 原 ``zmlx.ui.tabs.license_register`` 已删除、
        #    不留垫片。登录与授权检查是**软件本身**的一部分（状态栏按钮 / ``exts/_lic.py``
        #    的失败引导都指向它），做成插件没有意义，所以**必加载**。
        #    注册命令 ``gui.show_reg_tool``（原先由 ``MainWindow.show_reg_tool`` 提供）。
        #    ⚠️ 名字是历史叫法：它开的是 ``LicenseRegister``，不是 ``RegTool``。
        from zmlx.ui.setups.license_register import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup license_register: {err}")

    try:
        # ⚠️ 2026-10-31 起：「帮助 → 反馈」也在**本目录**（``setups/feedback_tool.py``），
        #    不再是 ``tabs/`` 里的控件 —— 原 ``zmlx.ui.tabs.feedback_tool`` 已删除、
        #    不留垫片。它是**出问题时的唯一出口**（ReadMe 的「新建Issue」链接指向它，
        #    别处也用它预填现场信息），做成插件正好在最需要它时把它关掉，所以**必加载**。
        #    注册命令 ``gui.show_feedback``（原先由 ``MainWindow.show_feedback`` 提供）。
        from zmlx.ui.setups.feedback_tool import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup feedback_tool: {err}")

    try:
        # ⚠️ 2026-10-31 起：``gui.open_url``（用内嵌网页开标签页）也归本目录
        #    （``setups/open_url.py``）。⚠️ 它与 ``zmlx.ui.alg.open_url`` **同名但两回事**：
        #    后者是对外统一入口（判断 use_web_engine / 有无界面，决定开标签页还是降级到
        #    系统浏览器），需要开标签页时正是调本命令；所以命令名**不能改**。
        from zmlx.ui.setups.open_url import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup open_url: {err}")

    try:
        # ⚠️ 2026-10-31 起：``gui.show_text_in_tab`` 也归本目录（``setups/text_in_tab.py``）。
        #    它与 ``setups/string_table.py`` 是**同一类东西**：把一段内容丢进窗口看的通用出口，
        #    被插件与 scen 按**命令名**调用（``scen/ai_assistant/action.py`` 用它显示回答正文）。
        #    ⚠️ 控件本体（``widgets/TextBrowser``）**不在这里**，装配层只做「开页面」。
        from zmlx.ui.setups.text_in_tab import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup text_in_tab: {err}")

    try:
        # ⚠️ 2026-10-31 起：「设置 → 迭代器」也在**本目录**（``setups/gui_iter_edit.py``），
        #    不再是 ``tabs/`` 里的控件 —— 原 ``zmlx.ui.tabs.gui_iter_edit`` 已删除、不留垫片。
        #    ⚠️ 关键：这一页**不是用户点开的** —— ``GuiIterator._plot_timing()`` 在第一次绘图时
        #    会自动调用 ``gui.show_gui_iter()`` 建它。做成插件的话，用户关掉插件后那个自动化
        #    调用方根本不知道自己被关了 ⇒ 必加载。
        from zmlx.ui.setups.gui_iter_edit import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup gui_iter_edit: {err}")

    try:
        # ⚠️ 2026-10-31 起：「帮助 → 关于」也在**本目录**（``setups/about.py``），
        #    不再是 ``tabs/`` 里的控件 —— 原 ``zmlx.ui.tabs.about`` 已删除、不留垫片。
        #    它是软件自身的版本 / 路径 / 登录状态这一页：状态栏的版本按钮
        #    （``widgets/version_button.py``）与 ReadMe 右键菜单都指向它 ⇒ **必加载**。
        from zmlx.ui.setups.about import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup about: {err}")

    try:
        # ⚠️ 2026-10-31 起：``gui.check_license``（**已弃用**的旧授权检查）也归本目录
        #    （``setups/check_license.py``）。它没有任何调用方，但原先是公开方法、
        #    自动注册成 ``gui.check_license`` —— 外部脚本可能在调，搬走时必须显式补
        #    ``gui.add_func``，否则外部调用会从「一条弃用警告」变成「找不到命令」。
        #    ⚠️ **不挂菜单、不加自动触发点**：弃用期到 2027-10-05，届时整体删除。
        from zmlx.ui.setups.check_license import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup check_license: {err}")

    # ⚠️ 数据编辑器的「文件类型 / 打开 / 新建」与「帮助 → 其它 → 生成测试数据」**在插件里**
    #    ``zmlx/ui/plugins/builtin/editors.py``（2026-10-22，默认启用）：编辑器是一个可
    #    关闭的单元，它的装配代码也一起搬走了（原 ``setups/editors.py`` 已删，
    #    中途那个 ``zmlx/scen/editors/`` 插件包也已取消、控件退回 ``ui/widgets/editors/``）。
    #    于是「文件 → 打开 / 新建」里那 7 种类型由**插件**注册，而不是这里的常驻调用。
    #
    # ⚠️ 顺序：本函数在 ``main.py`` 的 ``__console_kernel`` 里**先于**
    #    ``plugins.load_all()`` 执行，而 ``__restore_tabs()`` 在它俩之后 —— 所以重启
    #    恢复标签页时，插件注册的 ``gui.open_xxx`` 一定已经在了。

    try:
        # ⚠️ **必须排在本函数最前面**（比下面那些 setup 都早，更在插件之前）：
        #    它挂的是**插件命令的占位**（``get_vtk_view`` / ``show_style_sheet`` …），
        #    插件启用后要用同名 ``gui.add_func`` 覆盖它们 —— 顺序反了，占位就会顶掉插件。
        #    顺序契约见 ``setups/AGENTS.md`` §3；理由见该模块文档。
        from zmlx.ui.setups.plugin_placeholders import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup plugin_placeholders: {err}")

    # ⚠️ 「帮助 → 加载 → Admin功能」那一批已整体移入插件
    #    ``plugins/builtin/admin_menu.py``（默认不加载）—— 里面多数是开发 / 调试用的入口，
    #    见那边的模块文档。这里不再登记。
    #
    # ⚠️ 「设置 → 运行环境」也已移入插件 ``plugins/builtin/runtime_env.py``（默认不加载）。
    #    它整个模块就是「控件 + 注册」，没有别处复用，所以整体搬走即可。

    # ⚠️ 「帮助 → 用户」整个子菜单 2026-10-31 **已全部搬进插件**
    #    ``plugins/builtin/user_admin.py``（默认加载）——现在是**一个文件管三条菜单项**：
    #
    #      - 管理        gui.show_user_admin
    #      - 登录记录     gui.show_check_count_view
    #      - 反馈记录     gui.show_feedbacks_view
    #
    #    判据：关掉它软件照样能建模 / 求解 / 绘图 ⇒ 按 §1 判据属于「可关闭的扩展」。
    #    搬迁时 ``tabs/user_admin_view.py`` 与 ``license_query.py`` 的内容都整体并进了
    #    那个插件，两个原模块删除、**不留垫片**（已核实全仓与外部工作区都没有别处
    #    import 它们）。四条命令名（含两个旧名别名）与三个 action name 均未变，
    #    历史标签页照常恢复。
    #
    # ⚠️ 因此本目录不再有任何「帮助 → 用户」相关的登记 —— 只剩下面两条通用装配。

    # ⚠️ 「帮助 → 架构」2026-10-31 **已搬进插件** ``plugins/builtin/architecture.py``
    #    （默认加载）：它是纯文档页，关掉它软件照常可用 ⇒ 按 §1 判据属于「可关闭的
    #    扩展」，不该占着「必加载」的位置。那里用标准的 ``setup_ui`` + ``@execute_once``，
    #    不再需要这里原来那段 ``getattr(..., 'provide_gui_setup')`` 类型探测。
    #    命令名 ``gui.show_architecture`` 与菜单项 ``name='architecture'`` 均未变，
    #    历史标签页（``gui_restore``）照常恢复。
