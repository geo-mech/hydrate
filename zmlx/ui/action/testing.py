import os

from zmlx.system import execute_once
from zmlx.ui.alg import (
    play_images,
    open_gitee_geomech_hydrate, open_iggcas, open_new_issue, open_my_publications
)
from zmlx.ui.gui_buffer import add_action, gui


@execute_once(file=__file__)
def setup_ui_impl():
    from zmlx.system import app_data
    from zmlx.exts import lic
    from zmlx.alg.sys import create_ui_lnk_on_desktop

    def not_running():
        return not gui.is_running()

    add_action(
        menu='操作', name='play_images',
        text='播放图片',
        slot=play_images,
        overwritable=False
    )

    add_action(
        menu='设置', name='edit_window_style',
        text='窗口风格',
        slot=lambda: gui.open_text(
            app_data.temp('zml_window_style.qss'), '窗口风格'),
        overwritable=False
    )

    add_action(
        menu='帮助', name='create_lnk',
        text='创建快捷方式',
        slot=create_ui_lnk_on_desktop,
        overwritable=False
    )

    add_action(
        menu=['帮助', '打开'], name='papers',
        text='已发表文章',
        slot=open_my_publications,
        overwritable=False
    )

    add_action(
        menu=['帮助', '打开'], name='new_issue',
        text='新建Issue',
        icon='issues',
        slot=open_new_issue,
        is_enabled=not_running,
        overwritable=False
    )

    add_action(
        menu=['帮助', '打开'], name='iggcas',
        text='中科院地质地球所',
        icon='iggcas',
        slot=open_iggcas,
        is_enabled=not_running,
        overwritable=False,
    )

    add_action(
        menu=['帮助', '打开'], name='homepage',
        text='主页',
        icon='home',
        slot=open_gitee_geomech_hydrate,
        is_enabled=not_running,
        overwritable=False,
    )

    add_action(
        menu=['帮助', '显示'],
        text='日历',
        slot=gui.show_calendar,
        overwritable=False,
    )

    from zmlx.exts import print_tag

    add_action(
        menu='帮助', name='print_tag',
        text='时间标签',
        slot=print_tag,
        overwritable=False,
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
        overwritable=False,
    )

    add_action(
        menu=['帮助', '显示'],
        text='Action列表',
        slot=lambda: gui.start_func(print_actions),
        overwritable=False,
    )

    def print_gui_setup_logs():
        logs = app_data.get('gui_setup_logs')
        gui.show_string_table(logs, 'gui_setup_logs', 1)

    add_action(
        menu=['帮助', '显示'],
        text='Setup日志',
        slot=print_gui_setup_logs,
        overwritable=False,
    )

    def print_sys_folders():
        from zmlx.alg.sys import listdir
        paths = listdir(app_data.get_paths())
        gui.show_string_table(paths, '系统路径', 1)

    add_action(
        menu=['帮助', '显示'],
        text='系统路径',
        slot=print_sys_folders,
        overwritable=False,
    )

    def open_cwd():
        print(f'当前工作路径：\n{os.getcwd()}\n')
        from zmlx.alg import startfile
        startfile(os.getcwd())

    add_action(
        menu=['帮助', '打开'], name='open_cwd',
        text='工作路径',
        slot=open_cwd,
        overwritable=False,
    )

    def open_opath():
        from zmlx.io import opath
        from zmlx.alg import startfile
        print(f'数据目录：\n{opath()}\n')
        startfile(opath())

    add_action(
        menu=['帮助', '打开'], name='open_opath',
        text='数据目录(zmlx.io.opath)',
        slot=open_opath,
        overwritable=False,
    )

    from zmlx.alg import startfile

    add_action(
        menu=['帮助', '打开'], name='open_app_data',
        text='AppData',
        slot=lambda: startfile(app_data.root()),
        is_enabled=lambda: lic.is_admin,
        overwritable=False,
    )


@execute_once(file=__file__)
def setup_ui():
    add_action(
        menu=['帮助', '加载'],
        text='Admin功能',
        slot=setup_ui_impl,
        overwritable=False,
    )
