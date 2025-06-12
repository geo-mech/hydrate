import os

from zml import app_data, lic
from zmlx import gui
from zmlx.alg.fsys import print_tag


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


def play_images():
    from zmlx.alg.fsys import list_files

    def task():
        files = list_files(exts=['.jpg', '.png'])
        for idx in range(len(files)):
            print(files[idx])
            gui.open_image(files[idx], caption='播放图片',
                           on_top=False)
            gui.break_point()
            gui.progress(
                val_range=[0, len(files)], value=idx,
                visible=True, label="Playing Figures ")
        gui.progress(visible=False)

    gui.start_func(task)


def open_cwd():
    print(f'当前工作路径：\n{os.getcwd()}\n')
    os.startfile(os.getcwd())


def install_package():
    from zmlx.alg.sys import pip_install
    text, ok = gui.get_item(
        '安装第三包包', '输入或者选择你所需要的Python包名，并执行pip安装\n',
        ['', 'numpy', 'scipy', 'matplotlib', 'pyqtgraph', 'PyQt5', 'PyQt6',
         'PyQt6-WebEngine', 'pyqt6-qscintilla',
         'PyOpenGL', 'pypiwin32', 'pywin32', 'dulwich',
         ],
        editable=True, current=0)
    if ok:
        pip_install(text)


def heavy_work():
    import numpy as np
    from time import sleep
    from zmlx import plot_xy
    x = np.linspace(0, 20, 100)
    for idx in range(1000):
        gui.progress(label='Heavy Work执行进度', val_range=[0, 1000], value=idx,
                     visible=True)
        gui.break_point()
        sleep(0.02)
        print(f'step = {idx}/1000')
        x += 1
        y = np.sin(x)
        plot_xy(x, y)
    gui.progress(visible=False)


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


def set_plt_export_dpi():
    from zmlx.io.env import plt_export_dpi
    from zmlx.ui.pyqt import QtWidgets
    number, ok = QtWidgets.QInputDialog.getDouble(
        gui.window(),
        '设置导出图的DPI',
        'DPI',
        plt_export_dpi.get_value(), 50, 3000)
    if ok:
        plt_export_dpi.set_value(number)


def setup_ui():
    gui.add_func('show_calendar', show_calendar)

    data = [
        dict(
            menu='帮助',
            text='安装Python包',
            slot=lambda: gui.start_func(install_package),
        ),
        dict(menu='帮助', name='print_tag',
             text='时间标签',
             slot=print_tag
             ),

        dict(menu='操作', name='play_images',
             text='播放图片',
             slot=play_images
             ),

        dict(menu=['帮助', '显示'],
             text='gui命令列表',
             slot=lambda: gui.start(print_funcs),
             ),

        dict(menu=['帮助', '显示'],
             text='action列表',
             slot=print_actions,
             ),

        dict(menu=['帮助', '显示'],
             text='Setup日志',
             slot=print_gui_setup_logs,
             ),

        dict(menu=['帮助', '显示'],
             text='系统路径',
             slot=print_sys_folders,
             ),

        dict(menu=['帮助', '显示'],
             text='日历',
             slot=show_calendar,
             ),

        dict(menu=['帮助', '打开'], name='open_cwd',
             text='工作路径',
             slot=open_cwd
             ),

        dict(menu=['帮助', '打开'], name='open_app_data',
             text='AppData',
             slot=lambda: os.startfile(app_data.root()),
             is_enabled=lambda: lic.is_admin
             ),

        dict(menu=['帮助', '测试'],
             text='Heavy Task',
             slot=lambda: gui.start(heavy_work),
             ),

        dict(menu='设置', name='set_plt_export_dpi',
             text='设置plt输出图的DPI',
             slot=set_plt_export_dpi
             ),
    ]
    for opt in data:
        gui.add_action(**opt)


def main():
    from zmlx.alg.sys import first_execute
    if first_execute(__file__):
        gui.execute(func=setup_ui, keep_cwd=False, close_after_done=False)


if __name__ == '__main__':
    main()
