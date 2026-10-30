# ** name = 'Admin 功能'
# ** desc = '一批开发 / 调试与作者相关的辅助入口：播放图片、快捷方式、外部链接、日历、命令列表 / Action 列表 / Setup 日志 / 系统路径（默认不加载）'
# ** enabled = False
"""「Admin 功能」这一批菜单的装配（插件，默认不加载）.

原先是「帮助 → 加载 → Admin功能」：先点一下才生成下面这些条目。作为插件，那一层
「加载」被去掉 —— **插件被执行，菜单就当场出现**（2026-10-18）。

搬过来的条目
------------

============================  ===========================================
菜单位置                       条目
============================  ===========================================
``操作``                       播放图片
``帮助``                       创建快捷方式、时间标签
``帮助 → 打开``                 已发表文章、新建Issue、中科院地质地球所、
                              主页、工作路径、数据目录、AppData
``帮助 → 显示``                 日历、命令列表、Action列表、Setup日志、
                              系统路径
============================  ===========================================

为什么默认不加载
----------------

这批里多数是**开发 / 调试**用的（命令列表、Action 列表、Setup 日志、系统路径、
日历），或者是**作者本人**才关心的（已发表文章、新建 Issue、单位主页）。
它们随包分发，但默认不开 —— 想要就去「设置 → 插件」里勾上，重启后出现。

⚠️ **整体做成插件意味着启用前这些条目一律不出现**，包括「打开工作路径」这类
日常会用到的。这是刻意的取舍：这一批同属一个「加载」入口，拆开会让菜单结构
变得难以解释。

⚠️ 其中 ``AppData`` 一项原本就带 ``is_enabled=lambda: lic.is_admin`` —— 非管理员
看到的是灰掉的条目。**保持原样**：本插件默认不加载，所以勾上它的人大概率就是
要有这些调试能力的人，再按管理员身份隐藏反而无从排查。

⚠️ 作为插件，顶层**必须自己调** ``setup_ui()``（见文件末尾）—— 没有谁会替它调。

搬入的方法（2026-10-22）
-----------------------

``show_calendar`` 原来以 ``MainWindow.show_calendar`` 的形式常驻在界面骨架里：
它只是「开一个 Qt 自带的 ``QCalendarWidget`` 标签页」，而这个功能的**条目**本来就在
本插件里（「帮助 → 显示 → 日历」）。现在方法与条目都在这里，命令
``gui.show_calendar`` 由 :func:`setup_ui` 用 ``gui.add_func`` **显式注册**
（它原来靠 ``MainWindow`` 的「所有公开方法自动注册」）。

⚠️ **代价（刻意接受）**：本插件默认不加载，所以 ``gui.show_calendar`` 默认**不存在**；
历史标签页里的 ``gui.show_calendar()`` 也只在启用本插件后能恢复。日历本来就被
本文件的 ``# ** desc`` 列为 admin / 调试类入口，随插件开关走是合理的。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-18: 由 ``extra_setups/testing.py`` 移入插件；
    去掉「帮助 → 加载 → Admin功能」中间层，并默认不加载
Modified by DeepSeek, 2026-10-22: ``MainWindow.show_calendar`` 方法搬入本文件
    （连同它那条菜单项的 slot），并显式注册 ``gui.show_calendar``
"""

import os

from zmlx.system import execute_once


def show_calendar():
    """显示一个「日历」标签页（就是 Qt 自带的 ``QCalendarWidget``）.

    ⚠️ **命令名不能改**：历史标签页的 ``gui_restore`` 里存着 ``gui.show_calendar()``，
    重启时按原文重放。⚠️ 本插件**默认不加载**，所以这个命令默认**不存在** ——
    启用本插件后才有（历史标签页也只在启用后能恢复）。这是 2026-10-22 搬入时的
    已知取舍：日历本来就被列为 admin / 调试类入口（见文件顶的 ``# ** desc``）。

    ⚠️ 只通过 ``gui.get_widget`` 打开 —— 标签页只会一个，重复调用只是切到前面。
    """
    from zmlx.ui import gui
    from zmlx.ui.pyqt import QtWidgets

    def oper(w):
        w.gui_restore = 'gui.show_calendar()'

    gui.get_widget(
        the_type=QtWidgets.QCalendarWidget, caption='日历', on_top=True, oper=oper)


@execute_once(file=__file__)
def setup_ui():
    """把这批菜单条目挂上（插件被执行时调一次）."""
    from zmlx.algs.sys import create_ui_lnk_on_desktop
    from zmlx.exts import lic, print_tag
    from zmlx.system import app_data
    from zmlx.ui.alg import (
        open_gitee_geomech_hydrate, open_iggcas, open_new_issue,
        open_my_publications, play_images)
    from zmlx.ui.gui_buffer import add_action, gui

    # ⚠️ ``show_calendar`` 原来是 ``MainWindow`` 的公开方法，靠
    #    「所有公开方法自动注册」当上 ``gui.show_calendar``。方法搬到这里后，
    #    那串命令名**必须显式注册**，否则下面那条「日历」菜单项点了会报
    #    ``gui function <show_calendar> not found``。
    gui.add_func('show_calendar', show_calendar)

    def not_running():
        return not gui.is_running()

    add_action(
        menu='操作', name='play_images',
        text='播放图片',
        slot=play_images,
        overwrite=False
    )

    add_action(
        menu='帮助', name='create_lnk',
        text='创建快捷方式',
        slot=create_ui_lnk_on_desktop,
        overwrite=False
    )

    add_action(
        menu=['帮助', '打开'], name='papers',
        text='已发表文章',
        slot=open_my_publications,
        overwrite=False
    )

    add_action(
        menu=['帮助', '打开'], name='new_issue',
        text='新建Issue',
        icon='issues',
        slot=open_new_issue,
        is_enabled=not_running,
        overwrite=False
    )

    add_action(
        menu=['帮助', '打开'], name='iggcas',
        text='中科院地质地球所',
        icon='iggcas',
        slot=open_iggcas,
        is_enabled=not_running,
        overwrite=False,
    )

    add_action(
        menu=['帮助', '打开'], name='homepage',
        text='主页',
        icon='home',
        slot=open_gitee_geomech_hydrate,
        is_enabled=not_running,
        overwrite=False,
    )

    add_action(
        menu=['帮助', '显示'],
        text='日历',
        slot=show_calendar,
        overwrite=False,
    )

    add_action(
        menu='帮助', name='print_tag',
        text='时间标签',
        slot=print_tag,
        overwrite=False,
    )

    def print_funcs():
        gui.show_string_table(list(gui.list_all()), '命令列表')

    def print_actions():
        names = gui.list_actions()
        names.sort()
        gui.show_string_table(names, 'Action列表')

    add_action(
        menu=['帮助', '显示'],
        text='命令列表',
        slot=lambda: gui.start_func(print_funcs),
        overwrite=False,
    )

    add_action(
        menu=['帮助', '显示'],
        text='Action列表',
        slot=lambda: gui.start_func(print_actions),
        overwrite=False,
    )

    def print_gui_setup_logs():
        logs = app_data.get('gui_setup_logs')
        gui.show_string_table(logs, 'gui_setup_logs', 1)

    add_action(
        menu=['帮助', '显示'],
        text='Setup日志',
        slot=print_gui_setup_logs,
        overwrite=False,
    )

    def print_sys_folders():
        from zmlx.algs.sys import listdir
        paths = listdir(app_data.get_paths())
        gui.show_string_table(paths, '系统路径', 1)

    add_action(
        menu=['帮助', '显示'],
        text='系统路径',
        slot=print_sys_folders,
        overwrite=False,
    )

    def open_cwd():
        print(f'当前工作路径：\n{os.getcwd()}\n')
        from zmlx.algs import startfile
        startfile(os.getcwd())

    add_action(
        menu=['帮助', '打开'], name='open_cwd',
        text='工作路径',
        slot=open_cwd,
        overwrite=False,
    )

    def open_opath():
        from zmlx.io import opath
        from zmlx.algs import startfile
        print(f'数据目录：\n{opath()}\n')
        startfile(opath())

    add_action(
        menu=['帮助', '打开'], name='open_opath',
        text='数据目录(zmlx.io.opath)',
        slot=open_opath,
        overwrite=False,
    )

    from zmlx.algs import startfile

    add_action(
        menu=['帮助', '打开'], name='open_app_data',
        text='AppData',
        slot=lambda: startfile(app_data.root()),
        is_enabled=lambda: lic.is_admin,
        overwrite=False,
    )


# ⚠️ 插件路径：由 load_all exec 执行，**没人会替我们调 setup_ui()**，所以本文件
#    把调用写在**模块顶层**（``extra_setups/*.py`` 则由 ``extra_setups/__init__.py``
#    统一调用 —— 这是两者唯一的区别）。插件机制执行时 ``__name__`` 是
#    ``'__zml_plugin__'``；直接 ``python admin_menu.py`` 时才是 ``'__main__'``
#    （见 plugins/__init__.py 的说明）。
if __name__ == '__zml_plugin__':
    setup_ui()
