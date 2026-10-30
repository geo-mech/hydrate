"""插件命令的**占位**：插件没启用时，`gui.xxx` 仍然存在，只打印一句可操作的提示.

⚠️ **为什么要有本模块**（2026-10-22 定，`get_vtk_view` 是第一个）：一批入口 2026-10-22
从 `MainWindow` 搬进了各自的插件，但**命令名不能消失** —— 历史标签页的 `gui_restore`
里存着 `gui.show_style_sheet()` 这类原文，重启时按原文重放；
脚本 / demo / 外部项目也在调它们（例如 `igg-hydrate-works` 的 drill_v3 插件）。没有占位
时，插件被禁用就只剩 `gui function <xxx> not found`。

⚠️⚠️ **为什么放在 `extra_setups/` 而不是 `MainWindow`**（2026-10-22 改）：

1. **执行顺序天然正确**：`extra_setups.setup_ui()` 与 `plugins.load_all()` 在
   `main.py` 的 `__console_kernel` 里**顺序执行**（先 `extra_setups`、后插件，见
   `extra_setups/AGENTS.md` §3），而两者都在 `gui.set(api)` 之后。所以「先挂占位、
   插件再覆盖」是**同一根顺序链**上的一前一后，不依赖「控台线程 vs GUI 线程」这种
   跨线程的时序巧合；
2. **`main.py` 保持骨架**：这些占位一个参数都不读、只打一句话，留在 `MainWindow`
   里纯粹是给插件擦屁股（而且 `MainWindow` 的公开方法会被**自动注册**成命令 ——
   占位写在那儿就得靠「插件后写」才能让出位置，读代码时很难看出这层关系）。

⚠️ **占位的名字与插件名必须与插件一致**：插件启用后由它的 `gui.add_func(名字, ...)`
**覆盖**这里的占位（`GuiApi.funcs` 是普通 `SharedDict`，`set` 就是赋值、后写者胜）。
插件名一改（`# ** name = ...`），这里的提示就会指错地方。

⚠️ **签名一律 `*args, **kwargs`、函数体只有一句提示、不写 `return`**：占位一个参数都
不读，抄插件的参数表只会让它看起来像真实现（插件一改签名，这里就过时）；函数体末尾
隐式返回 `None`，不需要 `return None`。

⚠️ **不要用 `gui.add_func(name, None)` 去「注销」**：那会让 `gui.xxx` 报 `not found`，
而且直接调主窗口方法的路径也会一起失效，什么都没说。

⚠️ **本模块顶层什么都不做**（只有 import 与定义）：注册由 :func:`setup_ui` 发起，再由
`extra_setups/__init__.py` 调用 —— 顶层调用就是「导入即注册」的导入期副作用。

Created by DeepSeek, 2026-10-22: 从 ``main.py`` 的 ``MainWindow`` 搬出（原先那一族
    占位方法），命令名与提示文字保持不变
"""

from zmlx.system import execute_once


def _say(name, plugin):
    """打印「这个命令在插件里，请先启用它」."""
    print(f'要使用 {name}，请先在「设置 → 插件」里启用插件「{plugin}」并重启'
          f'（或点该行的「临时加载」当场生效）。'
          f'未启用时 gui.{name} 只是这个提示，不会打开任何窗口。')


def get_vtk_view(*args, **kwargs):
    """（**占位**）要使用 pyvista 视图，请先启用插件「VtkView」.

    ⚠️ 真正的实现在是插件 ``plugins/builtin/vtk_view.py``（同名的模块级函数
    ``get_vtk_view``）；插件启用后它的 ``gui.add_func`` 会**覆盖**这里。
    """
    _say('get_vtk_view', 'VtkView')


def show_style_sheet(*args, **kwargs):
    """（**占位**）要打开样式表编辑器，请先启用插件「样式表」.

    ⚠️ 真正的实现在插件 ``plugins/builtin/style_sheet_menu.py``。⚠️
    ``gui.set_style_sheet`` / ``gui.get_style_sheet`` **不受影响**（它们直接转接 Qt），
    所以禁用插件时已落盘的样式照常生效，只是没有可视化编辑器。
    """
    _say('show_style_sheet', '样式表')


def show_demo(*args, **kwargs):
    """（**占位**）要打开示例浏览器，请先启用插件「示例浏览」.

    ⚠️ 真正的实现在插件 ``plugins/builtin/demo_menu.py``（连同 ``DemoView``）。
    """
    _say('show_demo', '示例浏览')


def show_fn2(*args, **kwargs):
    """（**占位**）要查看二维裂缝（``.fn2``），请先启用插件「二维裂缝查看」.

    ⚠️ 真正的实现在插件 ``plugins/builtin/fn2_view.py``。⚠️ 那里仍会发
    ``DeprecationWarning``（针对拿 ``gui.show_fn2`` 当绘图函数用的旧脚本，原样保留自
    ``MainWindow`` 时期）；占位本身**不发**。
    """
    _say('show_fn2', '二维裂缝查看')


def show_pg_console(*args, **kwargs):
    """（**占位**）要打开 Python 控制台，请先启用插件「Python 控制台」.

    ⚠️ 真正的实现在插件 ``plugins/builtin/pg_console.py``（需要 ``pyqtgraph``）。

    ⚠️ **本模块只管 ``gui.xxx`` 命令，不挂菜单项**（2026-10-25 定，原本这里还挂过一条
    「显示 → 控制台(pg)」占位）。⚠️ 当时附带的另一个理由「``add_action`` 换不掉已经连到
    ``QAction`` 上的槽」**已于 2026-10-26 失效**，别再拿它当依据：点击改为转发到
    ``Action.slot_func``，而 ``overwrite=True`` 撞名时是**就地覆盖**（重设槽 / 图标 /
    文字，留在原位置），所以「先挂占位、插件启用后再挂一次」在技术上已经可行。
    规则**仍然不变**，理由换成更根本的一条：**菜单项由插件自己挂，插件关掉时它就该消失**
    —— 占位挂在这里，插件被禁用时菜单里照样多出一行，点下去只得到一句提示，而用户并没有
    开启这个功能。收益只有一行提示，代价是「关掉的插件还在菜单里占位」，不值。
    """
    _say('show_pg_console', 'Python 控制台')


def open_pdf(*args, **kwargs):
    """（**占位**）要打开 PDF，请先启用插件「PDF 查看」.

    ⚠️ 真正的实现在插件 ``plugins/builtin/pdf_view.py``（需要
    ``PyQt6-WebEngine``）。⚠️ 历史标签页的 ``gui_restore`` 里存着
    ``gui.open_pdf(...)``，所以这条命令不能消失 —— 与其它 ``show_*`` 同理。
    """
    _say('open_pdf', 'PDF 查看')


def show_timer(*args, **kwargs):
    """（**占位**）要查看耗时统计，请先启用插件「小型查看器」.

    ⚠️ 真正的实现在插件 ``plugins/builtin/viewers.py``（连同 ``TimerView``）。
    """
    _say('show_timer', '小型查看器')


def view_cwd(*args, **kwargs):
    """（**占位**）要浏览当前工作路径，请先启用插件「小型查看器」.

    ⚠️ 真正的实现在插件 ``plugins/builtin/viewers.py``（连同 ``CwdView``），菜单入口是
    **「文件 → 浏览 → 工作目录」**（2026-10-26 起收进「浏览」子菜单）。
    """
    _say('view_cwd', '小型查看器')


def show_image_browser(*args, **kwargs):
    """（**占位**）要浏览工作路径下的图片，请先启用插件「图片浏览」.

    ⚠️ 真正的实现在插件 ``plugins/builtin/image_browser.py``（**控件 ``ImageBrowser``
    与入口都在那一个文件里**，2026-10-30 起；原先控件在 ``ui/tabs/image_browser.py``），
    菜单入口是 **「文件 → 浏览 → 图片」**（2026-10-26 起与「工作目录」同一个子菜单）。
    ⚠️ **2026-10-26 起新增本条占位**：原先「图片浏览」是默认启用的，所以这条命令
    从没有过"插件被禁用"的情形；菜单合并之后它与「工作目录」并列，用户更可能直接把
    这个插件关掉 —— 那时历史标签页的 ``gui_restore``（``gui.show_image_browser()``）
    得有地方可落地，不能只剩 ``gui function <xxx> not found``。
    """
    _say('show_image_browser', '图片浏览')


def show_tab_details(*args, **kwargs):
    """（**占位**）要列出已打开的标签页，请先启用插件「小型查看器」.

    ⚠️ 真正的实现在插件 ``plugins/builtin/viewers.py``（连同 ``TabDetailView``）。
    """
    _say('show_tab_details', '小型查看器')


def show_file_finder(*args, **kwargs):
    """（**占位**）要编辑「程序路径」，请先启用插件「小型查看器」.

    ⚠️ 真正的实现在插件 ``plugins/builtin/viewers.py``（连同 ``AppPathEdit``）。
    """
    _say('show_file_finder', '小型查看器')


def show_calendar(*args, **kwargs):
    """（**占位**）要打开日历，请先启用插件「Admin 功能」.

    ⚠️ 真正的实现在插件 ``plugins/builtin/admin_menu.py``。⚠️ 那个插件默认
    **不加载**（``# ** enabled = False``），所以默认只有这句提示。
    """
    _say('show_calendar', 'Admin 功能')


def show_solver_selector(*args, **kwargs):
    """（**占位**）要配置求解器，请先启用插件「求解器」.

    ⚠️ 真正的实现在插件 ``plugins/builtin/solver_menu.py``（连同控件 ``SolverSelector``）。
    ⚠️ 那个插件默认**不加载**（``# ** enabled = False``），所以默认只有这句提示；
    历史标签页里存着 ``gui.show_solver_selector()``，重启时会重放到这里。
    """
    _say('show_solver_selector', '求解器')


def show_changelog(*args, **kwargs):
    """（**占位**）要查看修改记录，请先启用插件「文档查看」.

    ⚠️ 真正的实现在插件 ``plugins/builtin/doc_view.py``（默认**启用**）。
    ⚠️ ``ui/tabs/about.py`` 的「日志」按钮与历史标签页都调 ``gui.show_changelog()``。
    """
    _say('show_changelog', '文档查看')


def show_roadmap(*args, **kwargs):
    """（**占位**）要查看未来工作，请先启用插件「文档查看」.

    ⚠️ 真正的实现在插件 ``plugins/builtin/doc_view.py``（默认**启用**）。
    ``ui/tabs/about.py`` 的「路线图」按钮调 ``gui.show_roadmap()``。
    """
    _say('show_roadmap', '文档查看')


#: 占位命令：``[(命令名, 函数), ...]``。
#: ⚠️ 这是**内容集合**型的复数名字（同 `editors` / `utils` 的判据），不是分层名。
PLACEHOLDERS = [
    ('get_vtk_view', get_vtk_view),
    ('show_style_sheet', show_style_sheet),
    ('show_demo', show_demo),
    ('show_fn2', show_fn2),
    ('show_pg_console', show_pg_console),
    ('open_pdf', open_pdf),
    ('show_solver_selector', show_solver_selector),
    ('show_changelog', show_changelog),
    ('show_roadmap', show_roadmap),
    ('show_timer', show_timer),
    ('view_cwd', view_cwd),
    ('show_image_browser', show_image_browser),
    ('show_tab_details', show_tab_details),
    ('show_file_finder', show_file_finder),
    ('show_calendar', show_calendar),
]


@execute_once(file=__file__)
def setup_ui():
    """把上面 15 条**命令**挂到 ``gui`` 上（**只挂命令，不挂任何菜单项**）.

    ⚠️ **必须在插件之前执行**：插件启用后会用同名 ``gui.add_func`` 覆盖它们。两者都在
    `main.py` 的 `__console_kernel` 里顺序执行，`extra_setups` 在前（见
    `extra_setups/AGENTS.md` §3）—— 改那个顺序会让占位**顶掉**插件。

    ⚠️ **本模块永远不调 ``gui.add_action``**（2026-10-25 定，见
    :func:`show_pg_console` 的说明）：``add_action`` 把 slot 绑死在 action 上，命令表的
    覆盖对它无效，占不出有意义的东西。菜单项由插件自己挂。

    ⚠️ **逐个 ``try``**：一条挂不上（名字被占、gui 不可用）不该连累其它条。
    """
    from zmlx.ui import gui

    for name, func in PLACEHOLDERS:
        try:
            gui.add_func(name, func)
        except Exception as err:
            print(f'Error when add placeholder {name}: {err}')
