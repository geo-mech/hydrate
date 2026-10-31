# ** name = 'Python 控制台'
# ** desc = '打开一个交互式 Python 控制台标签页（基于 pyqtgraph 的 ConsoleWidget，需要安装 pyqtgraph）；入口在「显示 → 控制台(pg)」'
# ** enabled = True
# ** inner_name = 'pg_console'
"""Python 控制台插件：``PgConsole`` 控件 + ``gui.show_pg_console`` 命令 + 「显示 → 控制台(pg)」菜单项.

⚠️ **``inner_name = 'pg_console'`` 不是装饰**（2026-10-25 补）：它让
``plugins.load_now('pg_console')`` / ``is_loaded('pg_console')`` / ``get_load_error('pg_console')``
这几个**按名字**的调用真的找得到本插件。不写 ``inner_name`` 时 ``_alg._resolve`` 会把
``'pg_console'`` 判成「既不是文件、也不像路径」⇒ 返回 ``None`` ⇒ ``load_now`` 直接报
「找不到插件」、``is_loaded`` 一律 ``False``。⚠️ **``inner_name`` 不回落到文件名**
（与 ``name`` 的规则不同），所以必须显式写。

⚠️ **它是插件（可关闭）**：这个能力原先以 ``MainWindow.show_pg_console`` 的形式常驻在
界面骨架里，控件本体住在 ``ui/tabs/pg.py``。两者**只有本插件在用**（全仓与
``igg-hydrate-works`` 均核实过），所以按 ``plugins/AGENTS.md`` §0.2 收成「完全自含」：
禁用本插件时连控件代码一起不加载。

**默认启用**：它是个常用工具，只是依赖可选库，而可选依赖**不该**成为「默认关掉」的理由
—— 见下面那条降级设计。

⚠️ **依赖可选库 ``pyqtgraph``**（``from pyqtgraph.console import ConsoleWidget``）。
缺它时本模块**照样能被插件机制执行、注册照常完成**：

- :data:`PgConsole` 为 ``None``；
- ``gui.show_pg_console`` 命令**仍然注册**，调用它只打印一句可操作的提示（``pip install
  pyqtgraph``）并返回 ``None`` —— **不会抛异常**、不会让整个插件记为 ``Failed``；
- 「显示 → 控制台(pg)」菜单项**照样挂上**：缺库时点它只会打印那句提示（而不是留一个
  点了没反应的菜单项）。

⚠️ 这条降级是刻意与旧代码区分的：原 ``MainWindow.show_pg_console`` 在 ``PgConsole is None``
时**静默 return**（用户点了没有任何反馈，只有菜单项「没反应」）。现在至少会打印一句
说明，便于排查。

⚠️ **命令名 ``show_pg_console`` 不能改**：历史标签页的 ``gui_restore`` 存的就是
``gui.show_pg_console()``，重启时按原文重放。⚠️ 但**只有在 pyqtgraph 装好、且本插件
启用时**那条标签页才恢复得回来。

⚠️ ``app_data.space`` 是**运行空间**（与脚本、命令行共用），``PgConsole`` 直接在里面
执行用户输入 —— 所以它看到的变量和脚本里的一样。``PgConsoleText`` / ``PgConsoleInit``
两个环境变量可分别自定义「欢迎文本」与「初始化代码」。

Created by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-22: ``MainWindow.show_pg_console`` 与 ``ui/tabs/pg.py``
    整体并入本插件；缺 pyqtgraph 时改为打印提示（原来是静默 return）
Modified by DeepSeek, 2026-10-25: 新增菜单项「显示 → 控制台(pg)」（此前只注册命令、
    没有入口）；缺 pyqtgraph 时菜单项照样挂上、点击只打印提示
"""

from zmlx.system import execute_once

#: pyqtgraph 的控制台控件；**没装 pyqtgraph 时这里是 ``None``**.
#:
#: ⚠️ 用 ``try/except ImportError`` 而不是在函数体里导入：需要在**模块导入期**就确定
#: 到底有没有它，好让 :func:`show_pg_console` 能给出「没装」的提示，而 :func:`setup_ui`
#: 也不必推迟注册。
try:
    from pyqtgraph.console import ConsoleWidget as _ConsoleWidget
except ImportError:  # 可选依赖：没装就退化为 None
    _ConsoleWidget = None


if _ConsoleWidget is not None:

    class PgConsole(_ConsoleWidget):
        """基于 pyqtgraph ``ConsoleWidget`` 的交互式控制台。

        ⚠️ **代码在 GUI 主线程里执行**：输入一段耗时较长的代码会让界面卡死。
        这与「控制台标签页」（``Console``，跑在独立的内核线程、可暂停/停止）**不是一回事**
        —— 需要长时间运行的代码请用工具栏的「运行」，不要敲在这里。

        ⚠️ 命名空间就是 ``app_data.space``（与脚本、命令行共用）：这里能拿到脚本刚定义的
        变量，反向亦然。
        """

        def __init__(self, parent=None):
            from zmlx.system import app_data

            text = app_data.getenv(
                key='PgConsoleText',
                encoding='utf-8',
                default='''
这是一个交互的Python控制台。请在输入框输入Python命令并开始。特别注意，输入的代码将直接在主线程中执行，因此，请不要输入耗时较长的代码，否则会导致界面响应卡死。

---\n\n''')
            code = app_data.getenv(
                key='PgConsoleInit',
                encoding='utf-8',
                default='from zmlx import *'
            )
            super().__init__(parent, namespace=app_data.space, text=text)
            try:
                exec(code, app_data.space)
            except Exception as err:
                print(err)

else:
    #: 没装 pyqtgraph 时占位为 ``None``（与旧 ``ui/tabs/pg.py`` 的对外约定一致）.
    PgConsole = None


def show_pg_console():
    """打开（或切到）「Python控制台」标签页 —— 基于 pyqtgraph 的交互式控制台.

    ⚠️ **命令名不能改**：历史标签页存的就是 ``gui.show_pg_console()``。

    ⚠️ 缺 ``pyqtgraph`` 时打印一句提示并返回 ``None``（**不抛异常**）；旧代码是静默
    return，用户点了看不见任何反馈，所以这里改成说话。

    ⚠️ 只通过 ``gui.get_widget`` 打开 —— 标签页只会一个，重复调用只是切到前面。

    Returns:
        PgConsole | None: 打开（或切到）的那个标签页控件；缺 ``pyqtgraph`` 时返回
        ``None``（此时只打印一句 ``pip install`` 的提示）。⚠️ 菜单项「显示 → 控制台(pg)」
        与命令 ``gui.show_pg_console()`` 都调用本函数。
    """
    from zmlx.ui import gui

    if PgConsole is None:
        print('PgConsole 不可用：请先执行 `pip install pyqtgraph` 并重启本程序。')
        return None

    def oper(w):
        w.gui_restore = 'gui.show_pg_console()'

    return gui.get_widget(
        the_type=PgConsole,
        caption='Python控制台',
        on_top=True,
        icon='console',
        oper=oper,
    )


@execute_once(file=__file__)
def setup_ui():
    """注册 ``gui.show_pg_console`` 命令 + 「显示 → 控制台(pg)」菜单项.

    ⚠️ **无论有没有 pyqtgraph 都注册**：没装时命令照样存在，调用时给出 `pip install`
    提示。这样「命令不存在」和「库没装」两种失败模式不会混在一起。菜单项同理 ——
    缺库时点它只会**打印提示**（而不是一项点了没反应的灰条），与命令的行为一致。

    ⚠️ 菜单标题 ``'显示'`` 与 ``main.py`` 里那处**逐字一致**，否则 ``get_menu`` 会另建
    一个同名的新顶层菜单（见 ``plugins/builtin/viewers.py`` 的同一条注意事项）。
    ``name='pg_console'`` 是 action 的内部名（现状见 ``ui/ReadMe.md`` 的命名遗留）。

    ⚠️ 「显示 → 控制台(pg)」2026-10-25 新增：此前本插件**只注册命令、不挂菜单**，
    用户只能靠脚本调 ``gui.show_pg_console()`` 才能打开它 —— 一个默认启用的插件却
    没有入口，等于装了看不见。菜单项与命令指向**同一个** :func:`show_pg_console`，
    所以 ``gui_restore`` 恢复标签页的路径不受影响。

    ⚠️ **``overwrite=False`` 在这里的含义**（别按字面理解，见 ``MainWindow.add_action``
    的 docstring）：不是「不许被覆盖」，而是「**同名 action 已存在就直接跳过**」。这条条目
    只由本插件挂、``setup_ui`` 又有 ``@execute_once``，所以正常情况下同名不存在、
    **照常挂上**；只有当另一个插件 / ``setups`` 抢先注册了同名 ``pg_console`` 时
    才会被跳过（那时也**不应该**再多出一条来顶替它）。

    ⚠️ **菜单项不要做占位**（2026-10-25 定）：``gui.add_action`` 在调用那一刻就把 slot
    绑到 ``QAction`` 上了，后来 ``gui.add_func`` 换不掉它；占位条目会让真正的条目进不来
    （见 ``plugins/AGENTS.md`` 的「占位只占命令，不占菜单项」）。
    """
    from zmlx.ui import gui

    gui.add_func('show_pg_console', show_pg_console)

    try:
        gui.add_action(
            menu='显示', name='pg_console',
            icon='python',
            tooltip='打开交互式 Python 控制台（基于 pyqtgraph；代码在主线程执行，'
                    '耗时的代码请用工具栏的「运行」）',
            text='控制台(pg)',
            slot=show_pg_console,
            overwrite=False,
        )
    except Exception as err:
        print(f'Error when add_action(pg_console): {err}')


# ⚠️ 插件路径：由 load_all exec 执行，**没人会替我们调 setup_ui()**，所以本文件
#    把调用写在**模块顶层**的这个分支里（``setups/*.py`` 则由
#    ``setups/__init__.py`` 统一调用 —— 这是两者唯一的区别）。
#    插件机制执行时 ``__name__`` 是 ``'__zml_plugin__'``；直接 ``python pg_console.py``
#    时才是 ``'__main__'``（见 plugins/__init__.py 的说明）。
if __name__ == '__zml_plugin__':
    setup_ui()
