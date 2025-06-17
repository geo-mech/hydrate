import os

from zml import app_data, read_text, lic
from zmlx.alg.fsys import print_tag
from zmlx.ui.alg import open_url
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtWidgets, QAction


class Action(QAction):
    def __init__(self, parent):
        super().__init__(parent)
        self.is_enabled = None  # 检查是否是可执行的
        self.is_visible = None  # 检查是否是可见的

    def update_view(self):
        """
        更新视图
        """
        is_enabled = self.is_enabled() if callable(self.is_enabled) else True
        is_visible = self.is_visible() if callable(
            self.is_visible) else is_enabled
        self.setEnabled(is_enabled)
        self.setVisible(is_visible)


def open_cwd():
    print(f'当前工作路径：\n{os.getcwd()}\n')
    os.startfile(os.getcwd())


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


def print_funcs():
    cmds = list(gui.list_all())
    for i in range(len(cmds)):
        print(i, cmds[i])


def add_std_actions(window):
    """
    初始化内置的菜单动作
    """
    from zmlx.alg.sys import create_ui_lnk_on_desktop

    def not_running():
        return not window.is_running()

    def console_exec():
        f = getattr(window.get_current_widget(), 'console_exec', None)
        if callable(f):
            f()

    def pause_enabled():
        c = window.get_console()
        if not c.is_running():
            return False
        return not c.should_pause()

    def about():
        print(lic.desc)
        window.show_about()

    def set_plt_export_dpi():
        from zmlx.io.env import plt_export_dpi
        number, ok = QtWidgets.QInputDialog.getDouble(
            window,
            '设置导出图的DPI',
            'DPI',
            plt_export_dpi.get_value(), 50, 3000)
        if ok:
            plt_export_dpi.set_value(number)

    data = [
        dict(menu='文件', name='set_cwd', icon='open',
             tooltip='设置当前的工作路径', text='工作路径',
             slot=window.set_cwd_by_dialog,
             on_toolbar=True,
             is_enabled=not_running,
             is_visible=lambda: True
             ),

        dict(menu='文件', name='quit', icon='quit',
             text='退出',
             slot=window.close,
             ),

        dict(menu='文件', name='open', icon='open',
             tooltip='设置当前的工作路径', text='打开',
             slot=window.open_file_by_dlg,
             on_toolbar=True,
             is_enabled=not_running, is_visible=lambda: True
             ),

        dict(menu='文件', name='demo', icon='demo',
             tooltip=None, text='示例',
             slot=window.show_demo,
             on_toolbar=True, is_enabled=None, is_visible=lambda: True
             ),

        dict(menu='文件', name='view_cwd', icon='cwd',
             text='文件',
             slot=window.view_cwd,
             on_toolbar=True
             ),

        dict(menu='文件', name='py_new', icon='python',
             text='新建Python脚本',
             slot=window.new_code,
             is_enabled=not_running,
             ),

        dict(menu='文件', name='export_data',
             text='导出数据',
             slot=lambda: getattr(window.get_current_widget(), 'export_data')(),
             is_enabled=lambda: hasattr(
                 window.get_current_widget(),
                 'export_data') and not window.is_running(),
             ),

        dict(menu='文件', name='export_plt_figure',
             text='导出plt图',
             on_toolbar=True,
             slot=lambda: getattr(window.get_current_widget(),
                                  'export_plt_figure')(),
             is_enabled=lambda: hasattr(
                 window.get_current_widget(),
                 'export_plt_figure') and not window.is_running(),
             ),

        dict(menu='显示', name='refresh', icon='refresh',
             text='刷新',
             slot=window.refresh
             ),

        dict(menu='显示', name='memory', icon='variables',
             text='变量',
             slot=window.show_memory
             ),

        dict(menu='显示', name='timer', icon='clock',
             tooltip='显示cpu耗时统计的结果', text='耗时',
             slot=window.show_timer
             ),

        dict(menu='显示', name='console', icon='console',
             text='Python控制台(测试)',
             slot=window.show_pg_console
             ),

        dict(menu='显示', name='cls', icon='clean',
             text='清屏',
             slot=window.cls
             ),

        dict(menu='显示', name='tab_details',
             text='标签列表',
             tooltip='在一个标签页内显示所有标签也的摘要，当标签特别多的时候比较有用',
             slot=window.show_tab_details
             ),

        dict(menu='显示', name='show_code_history',
             text='运行历史',
             slot=lambda: window.show_code_history(
                 folder=app_data.root('console_history'),
                 caption='运行历史')
             ),

        dict(menu='显示', name='show_output_history',
             text='输出历史',
             slot=window.show_output_history,
             ),

        dict(menu='操作', name='console_exec', icon='begin',
             tooltip='运行当前标签页面显示的脚本',
             text='运行',
             slot=console_exec,
             on_toolbar=True,
             is_enabled=lambda: hasattr(
                 window.get_current_widget(),
                 'console_exec') and not window.is_running(),
             is_visible=not_running,
             ),

        dict(menu='操作', name='console_pause',
             icon='pause',
             tooltip='暂停内核的执行 (需要提前在脚本内设置break_point)',
             text='暂停',
             slot=lambda: window.get_console().pause_clicked(),
             on_toolbar=True,
             is_enabled=pause_enabled,
             ),

        dict(menu='操作', name='console_resume',
             icon='begin',
             tooltip=None, text='继续',
             slot=lambda: window.get_console().pause_clicked(),
             on_toolbar=True,
             is_enabled=lambda: window.is_running() and window.get_console().should_pause(),
             ),

        dict(menu='操作', name='console_stop', icon='stop',
             tooltip='安全地终止内核的执行 (需要提前在脚本内设置break_point)',
             text='停止',
             slot=lambda: window.get_console().stop_clicked(),
             on_toolbar=True,
             is_enabled=window.is_running
             ),

        dict(menu='操作', name='console_kill', icon='kill',
             text='强制结束',
             slot=window.kill_thread,
             is_enabled=window.is_running
             ),

        dict(menu='操作', name='console_hide',
             icon='console',
             tooltip='隐藏主窗口右侧的控制台', text='隐藏',
             slot=lambda: window.get_console().setVisible(False),
             on_toolbar=True,
             is_enabled=lambda: window.get_console().isVisible()
             ),

        dict(menu='操作', name='console_show',
             icon='console',
             tooltip='显示主窗口右侧的控制台', text='显示',
             slot=lambda: window.get_console().setVisible(True),
             on_toolbar=True,
             is_enabled=lambda: not window.get_console().isVisible()
             ),

        dict(menu='操作', name='close_all_tabs',
             icon='close_all',
             text='关闭所有页面',
             slot=window.close_all_tabs,
             is_enabled=lambda: window.count_tabs() > 0,
             ),

        dict(menu='操作', name='print_tag',
             text='添加时间标签',
             slot=print_tag
             ),

        dict(menu='操作', name='play_images',
             text='播放图片',
             slot=play_images
             ),

        dict(menu='设置', name='search', icon='set',
             text='搜索路径',
             slot=window.show_file_finder
             ),

        dict(menu='设置', name='env', icon='set',
             text='Env变量',
             slot=window.show_env_edit
             ),

        dict(menu='设置', name='setup_files',
             text='启动文件',
             slot=window.show_setup_files_edit
             ),

        dict(menu='设置', name='install_dep',
             text='第三方包',
             slot=window.show_package_table
             ),

        dict(menu='设置', name='edit_window_style',
             text='窗口风格(qss)',
             slot=lambda: window.open_text(
                 app_data.temp('zml_window_style.qss'), '窗口风格')
             ),

        dict(menu='设置', name='set_plt_export_dpi',
             text='plt图的DPI',
             slot=set_plt_export_dpi
             ),

        dict(menu='帮助', name='readme', icon='info',
             text='ReadMe',
             slot=window.show_readme,
             on_toolbar=True),

        dict(menu='帮助', name='about',
             text='关于',
             icon='info',
             slot=about,
             is_enabled=not_running,
             ),

        dict(menu='帮助', name='reg', icon='reg',
             text='注册',
             slot=window.show_reg_tool
             ),

        dict(menu='帮助', name='feedback',
             text='反馈',
             icon='info',
             slot=window.show_feedback,
             is_enabled=not_running,
             ),

        dict(menu=['帮助', '打开'], name='papers',
             text='已发表文章',
             slot=lambda: open_url(
                 url="https://pan.cstcloud.cn/s/5cKaQrdFSHM",
                 use_web_engine=False)
             ),

        dict(menu=['帮助', '打开'], name='new_issue',
             text='新建Issue',
             icon='issues',
             slot=lambda: open_url(
                 url='https://gitee.com/geomech/hydrate/issues/new',
                 on_top=True,
                 caption='新建Issue',
                 icon='issues'),
             is_enabled=not_running,
             ),

        dict(menu=['帮助', '打开'], name='iggcas',
             text='中科院地质地球所',
             icon='iggcas',
             slot=lambda: open_url(
                 url='http://www.igg.cas.cn/',
                 on_top=True,
                 caption='中科院地质地球所主页',
                 icon='iggcas'
             ),
             is_enabled=not_running,
             ),

        dict(menu=['帮助', '打开'], name='homepage',
             text='主页',
             icon='home',
             slot=lambda: open_url(
                 url='https://gitee.com/geomech/hydrate',
                 on_top=True,
                 caption='IGG-Hydrate',
                 icon='home'
             ),
             is_enabled=not_running,
             ),

        dict(menu=['帮助', '打开'], name='open_cwd',
             text='当前工作路径',
             slot=open_cwd
             ),

        dict(menu=['帮助', '打开'], name='open_app_data',
             text='AppData',
             slot=lambda: os.startfile(app_data.root()),
             is_enabled=lambda: lic.is_admin
             ),

        dict(menu=['帮助', '显示'],
             text='gui命令列表',
             slot=print_funcs,
             ),

        dict(menu='帮助', name='create_lnk',
             text='创建快捷方式',
             slot=create_ui_lnk_on_desktop,
             ),
    ]
    for opt in data:
        window.add_action(**opt)


def _add_by_file(window, file):
    from zmlx.ui.main_window import MainWindow
    assert isinstance(window, MainWindow)

    text = read_text(path=file, encoding='utf-8',
                     default=None)
    data = {}
    try:
        exec(text, {'__name__': ''}, data)
        has_error = False
    except Exception as err:
        print(f'Error when parse {file}: {err}')
        has_error = True

    icon = data.get('icon')
    tooltip = data.get('tooltip')
    text = data.get('text')
    slot = data.get('slot')
    on_toolbar = data.get('on_toolbar', False)
    menu = data.get('menu', '其它')

    def is_enabled():
        if has_error:  # 解析文件的时候出现错误，直接不可用
            return False

        try:
            exec(data.get('dependency', ''), {})
        except:
            return False  # 依赖项错误，则直接不可用

        value = data.get('enabled')

        if value is None:  # 没有定义，则默认可用
            return True

        try:
            res = window.parse_value(value)
            return False if res is None else res
        except Exception as e:
            print(e)
            return False

    if data.get('is_visible') is None:
        is_visible = None
    else:
        def is_visible():
            try:
                return window.parse_value(data.get('is_visible'))
            except Exception as e:
                print(f'Error when parse is_visible in {file}: {e}')
                return True

    window.add_action(
        menu=menu, name=os.path.basename(file),
        icon=icon,
        tooltip=tooltip, text=text, slot=slot,
        on_toolbar=on_toolbar,
        is_enabled=is_enabled,
        is_visible=is_visible,
    )


def add_zml_actions(window):
    action_files = []
    for path in reversed(app_data.find_all('zml_actions')):
        if path is None:
            continue
        if not os.path.isdir(path):
            continue
        for filename in os.listdir(path):
            name, ext = os.path.splitext(filename)
            if filename == '__init__.py':
                continue
            if ext == '.py':
                action_files.append(os.path.join(path, filename))

    for s in action_files:
        _add_by_file(window, s)
