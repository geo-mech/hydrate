from zmlx.system import execute_once


@execute_once(file=__file__)
def setup_ui():

    try:
        from zmlx.ui.tabs.message import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup message: {err}")

    try:
        from zmlx.ui.tabs.mem_view import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup mem_view: {err}")

    try:
        # ⚠️ 只注册**文件类型**（``gui.open_numpy_array`` 等），不再挂菜单：
        #    「文件 → 生成测试数据」那五个**示例数据**条目已搬进插件
        #    ``plugins/builtin/editors_menu.py``（默认不加载，见那边说明）。
        #    打开已有文件是常规能力，与插件是否启用无关，所以留在这里。
        from zmlx.ui.widgets.editors import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup editors: {err}")

    try:
        # ⚠️ 只注册**文件类型**（``gui.open_seepage`` / ``gui.open_fludef``），
        #    不再挂菜单：「文件 → 生成测试数据」里那条造 ``Example.fludef`` 的
        #    示例数据已搬进插件 ``plugins/builtin/seepage_menu.py``（默认不加载）。
        #    打开已有 .seepage 文件是常规能力，与插件是否启用无关，所以留在这里。
        from zmlx.ui.widgets.seepage import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup seepage: {err}")

    # ⚠️ 「帮助 → 加载 → Admin功能」那一批已整体移入插件
    #    ``plugins/builtin/admin_menu.py``（默认不加载）—— 里面多数是开发 / 调试用的入口，
    #    见那边的模块文档。这里不再登记。
    #
    # ⚠️ 「设置 → 运行环境」也已移入插件 ``plugins/builtin/runtime_env.py``（默认不加载）。
    #    它整个模块就是「控件 + 注册」，没有别处复用，所以整体搬走即可。

    try:
        # 「帮助 → 用户 → 管理」：授权查询与修改（管理员可用）。
        # ⚠️ 这是**产品功能**，所以留在 extra_setups 而不是 plugins ——
        #    plugins 里的是用户可禁用的扩展。
        # ⚠️ **注册顺序要在 license_query 之前**：同一子菜单下的条目按注册先后排列，
        #    放前面才能让「管理」排在「登录 / 反馈」之后、「查询」那一段之前。
        #    ⚠️ 「用户」「查询」两个子菜单的**位置**由 ``main.py`` 的两行
        #    ``get_menu`` 决定（它们排在 ReadMe / 关于 / 示例之后，即「帮助」的下半段）；
        #    本模块在 ``MainWindow`` 构造**之后**才执行，只负责往子菜单里**填条目**，
        #    不影响子菜单在「帮助」里的位置。
        from zmlx.ui.extra_setups.user_admin import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup user_admin: {err}")

    try:
        from zmlx.ui.extra_setups.license_query import setup_ui

        setup_ui()
    except Exception as err:
        print(f"Error when setup license_query: {err}")

    try:
        # 「帮助 → 架构」：zmlx 代码库的图文入门页（architecture.py）。
        #
        # ⚠️ 这里**不用**上面那种 `setup_ui` 的写法，而是先用 getattr 探测函数名：
        #    architecture.py 在模块顶层就 import Qt 控件，在没有 Qt / 无头环境里它可能
        #    直接导入失败。用类型探测，取不到就安静跳过，不会带崩整个 setup_ui。
        #    详见该文件 `provide_gui_setup` 的 docstring。
        from zmlx.ui.extra_setups import architecture

        provider = getattr(architecture, 'provide_gui_setup', None)
        if callable(provider):
            provider()
    except Exception as err:
        print(f"Error when setup architecture: {err}")
