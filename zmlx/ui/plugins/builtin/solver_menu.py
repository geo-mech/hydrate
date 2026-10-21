# ** name = '求解器'
# ** desc = '「设置 → 求解器」：选择并配置本机使用的求解器后端（默认不加载）'
# ** enabled = False
"""把「设置 → 求解器」这个入口挂成插件（默认不加载）.

⚠️ **只挪菜单，不挪控件**：菜单项原来在 ``main.py`` 的 ``__init_actions`` 里，紧挨着
``show_solver_selector`` 方法。那个方法是 ``MainWindow`` 的**公开方法**，
``__init_gui_api`` 会自动把它的名字注册成 ``gui.show_solver_selector`` 命令 ——
**已保存的标签页**（``gui_restore = "gui.show_solver_selector()"``）重启时要靠它恢复。
所以方法本身**必须留在 ``main.py``**，这里只负责那一行 ``add_action``。

为什么默认不加载
----------------

求解器选择是**装好一次就不用再动**的设置；多数用户从不让它出现在界面上。
它仍然随包分发 —— 需要在「设置 → 插件」里勾上，重启后「设置 → 求解器」才出现。

⚠️ 本插件被禁用时，``gui.show_solver_selector()`` **命令依然可用**（它来自
``MainWindow`` 的方法，与插件无关）。只是菜单里没有入口了。

⚠️ 作为插件，顶层**必须自己调** ``setup_ui()``（见文件末尾）—— 没有谁会替它调。

Created by DeepSeek, 2026-10-18
"""

from zmlx.system import execute_once


@execute_once(file=__file__)
def setup_ui():
    """在「设置」下挂「求解器」（插件被执行时调一次）.

    ⚠️ 菜单标题与 ``main.py`` 里那几处**逐字一致**（都写 ``'设置'``），否则
    ``get_menu`` 会另建一个同名的新顶层菜单，界面上出现两个「设置」。
    """
    from zmlx.ui import gui

    gui.add_action(
        menu='设置', name='solver',
        text='求解器',
        slot=gui.show_solver_selector,
        overwritable=False,
    )


# ⚠️ 插件路径：由 run_setup exec 执行，**没人会替我们调 setup_ui()**，所以本文件
#    把调用写在**模块顶层**（``extra_setups/*.py`` 则由 ``extra_setups/__init__.py``
#    统一调用 —— 这是两者唯一的区别）。插件机制执行时 ``__name__`` 是
#    ``'__zml_plugin__'``；直接 ``python solver_menu.py`` 时才是 ``'__main__'``
#    （见 plugins/__init__.py 的说明）。
if __name__ == '__zml_plugin__':
    setup_ui()
