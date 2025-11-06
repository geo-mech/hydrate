import os

from zmlx import gui
from zmlx.alg.fsys import print_tag
from zmlx.exts.base import app_data, lic


def print_funcs():
    gui.show_string_table(list(gui.list_all()), '所有的gui函数')


def print_actions():
    names = gui.list_actions()
    names.sort()
    gui.show_string_table(names, '所有的Action名字')


def print_gui_setup_logs():
    logs = app_data.get('gui_setup_logs')
    gui.show_string_table(logs, 'gui_setup_logs', 1)


def print_sys_folders():
    from zmlx.alg.sys import listdir
    paths = listdir(app_data.get_paths())
    gui.show_string_table(paths, '系统路径', 1)


def open_cwd():
    print(f'当前工作路径：\n{os.getcwd()}\n')
    os.startfile(os.getcwd())


def show_calendar():
    from zmlx.ui.pyqt import QtWidgets
    def oper(w):
        w.gui_restore = f"""gui.show_calendar()"""

    gui.get_widget(
        the_type=QtWidgets.QCalendarWidget,
        caption='QCalendarWidget',
        on_top=True,
        oper=oper
    )


def setup_ui():
    from zmlx.ui.alg import install_package, set_plt_export_dpi, play_images
    gui.add_func('show_calendar', show_calendar)

    add = gui.add_action

    add(menu='帮助',
        text='安装Python包',
        slot=install_package,
        )
    add(menu='帮助', name='print_tag',
        text='时间标签',
        slot=print_tag
        )

    add(menu='操作', name='play_images',
        text='播放图片',
        slot=play_images
        )

    add(menu=['帮助', '显示'],
        text='gui命令列表',
        slot=lambda: gui.start(print_funcs),
        )

    add(menu=['帮助', '显示'],
        text='action列表',
        slot=print_actions,
        )

    add(menu=['帮助', '显示'],
        text='Setup日志',
        slot=print_gui_setup_logs,
        )

    add(menu=['帮助', '显示'],
        text='系统路径',
        slot=print_sys_folders,
        )

    add(menu=['帮助', '显示'],
        text='日历',
        slot=show_calendar,
        )

    add(menu=['帮助', '打开'], name='open_cwd',
        text='工作路径',
        slot=open_cwd
        )

    add(menu=['帮助', '打开'], name='open_app_data',
        text='AppData',
        slot=lambda: os.startfile(app_data.root()),
        is_enabled=lambda: lic.is_admin
        )

    add(menu='设置', name='set_plt_export_dpi',
        text='设置plt输出图的DPI',
        slot=set_plt_export_dpi
        )


def main():
    from zmlx.alg.sys import first_execute
    if first_execute(__file__):
        gui.execute(func=setup_ui, keep_cwd=False, close_after_done=False)


if __name__ == '__main__':
    main()
