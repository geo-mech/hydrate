# ** name = '样式表'
# ** desc = '「设置 → 样式表」：可视化选择字体 / 配色 / 圆角生成 QSS，或直接编辑样式表文本；落盘后下次启动自动生效'
"""把「设置 → 样式表」这个入口挂成插件（**默认启用**）.

⚠️ **只挪菜单，不挪控件**：菜单项原来在 ``main.py`` 的 ``__init_actions`` 里，紧挨着
``show_style_sheet`` 方法。那个方法是 ``MainWindow`` 的**公开方法**，
``__init_gui_api`` 会自动把它的名字注册成 ``gui.show_style_sheet`` 命令 ——
**已保存的标签页**（``gui_restore = "gui.show_style_sheet()"``）重启时要靠它恢复。
所以方法本身**必须留在 ``main.py``**，这里只负责那一行 ``add_action``。

为什么**默认启用**
------------------

与「求解器」「运行环境」不同：样式表是**用户随时会调**的外观设置（换字体、调字号、
改配色），藏起来会让人以为软件不能改外观。做成插件只是为了让它**可被禁用**
（例如管理员统一部署时锁掉外观），而不是为了默认收起它。

⚠️ 因此本插件**不写** ``# ** enabled = ...``（缺省即启用）。

⚠️ 本插件被禁用时，``gui.show_style_sheet()`` **命令依然可用**（它来自
``MainWindow`` 的方法，与插件无关），只是菜单里没有入口了。

⚠️ 作为插件，顶层**必须自己调** ``setup_ui()``（见文件末尾）—— 没有谁会替它调。

Created by DeepSeek, 2026-10-18
"""

from zmlx.system import execute_once


@execute_once(file=__file__)
def setup_ui():
    """在「设置」下挂「样式表」（插件被执行时调一次）.

    ⚠️ 菜单标题与 ``main.py`` 里那几处**逐字一致**（都写 ``'设置'``），否则
    ``get_menu`` 会另建一个同名的新顶层菜单，界面上出现两个「设置」。
    """
    from zmlx.ui import gui

    gui.add_action(
        menu='设置', name='edit_window_style',
        text='样式表',
        icon='set',
        tooltip='设置窗口样式表：可视化选择字体/配色/圆角，也可以直接编辑 QSS 文本',
        slot=gui.show_style_sheet,
        overwritable=False,
    )


# ⚠️ 插件路径：由 run_setup exec 执行，**没人会替我们调 setup_ui()**，所以本文件
#    把调用写在**模块顶层**（``extra_setups/*.py`` 则由 ``extra_setups/__init__.py``
#    统一调用 —— 这是两者唯一的区别）。插件机制执行时 ``__name__`` 是
#    ``'__zml_plugin__'``；直接 ``python style_sheet_menu.py`` 时才是 ``'__main__'``
#    （见 plugins/__init__.py 的说明）。
if __name__ == '__zml_plugin__':
    setup_ui()
