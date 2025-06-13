from importlib import import_module

import zml
from zmlx.alg.fsys import print_tag
from zmlx.ui.alg import open_url
from zmlx.ui.cfg import *
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
        is_visible = self.is_visible() if callable(self.is_visible) else is_enabled
        self.setEnabled(is_enabled)
        self.setVisible(is_visible)


def add_std_actions(window):
    """
    初始化内置的菜单动作
    """
    from zmlx.ui.widget.demo_widget import DemoWidget
    from zmlx.ui.main_window import MainWindow
    from zmlx.alg.sys import create_ui_lnk_on_desktop
    assert isinstance(window, MainWindow)

    def open_cwd():
        print(f'当前工作路径：\n{os.getcwd()}\n')
        os.startfile(os.getcwd())

    def new_code():
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            window,
            caption='新建.py脚本',
            directory=os.getcwd(),
            filter='Python File (*.py);;')
        window.open_code(fname)

    def show_txt(filepath):
        try:
            from zmlx.alg.fsys import get_size_mb, show_fileinfo
            if get_size_mb(filepath) < 0.5:
                window.open_text(filepath)
            else:
                show_fileinfo(filepath)
        except:
            pass

    def show_widget(
            module_name, widget_name,
            caption=None, on_top=None,
            oper=None, icon=None):
        try:
            the_type = getattr(import_module(module_name), widget_name, None)
        except:
            the_type = None
        if the_type is not None:
            window.get_widget(
                the_type=the_type, caption=caption, on_top=on_top,
                oper=oper, icon=icon)

    def not_running():
        return not window.is_running()

    def exec_current():
        f = getattr(window.get_current_widget(), 'console_exec', None)
        if callable(f):
            f()

    def pause_enabled():
        c = window.get_console()
        if not c.is_running():
            return False
        return not c.should_pause()

    def install_dep():
        from zmlx.ui.widget.package_table import PackageTable
        from zmlx.ui.pyqt import is_pyqt6

        packages = [
            dict(package_name='numpy', import_name='numpy'),
            dict(package_name='scipy', import_name='scipy'),
            dict(package_name='matplotlib',
                 import_name='matplotlib'),
            dict(package_name='PyOpenGL', import_name='OpenGL'),
            dict(package_name='pyqtgraph', import_name='pyqtgraph'),
            dict(package_name='pypiwin32', import_name='win32com'),
            dict(package_name='pywin32', import_name='pywintypes'),
            dict(package_name='chemicals', import_name='chemicals'),
        ]
        if is_pyqt6:
            packages.append(dict(
                package_name='PyQt6-WebEngine',
                import_name='PyQt6.QtWebEngineWidgets'))
        else:
            packages.append(dict(
                package_name='PyQtWebEngine',
                import_name='PyQt5.QtWebEngineWidgets'))
        window.get_widget(
            the_type=PackageTable, caption='Python包管理', on_top=True,
            type_kw=dict(packages=packages))

    def about():
        from zml import lic
        print(lic.desc)
        window.show_about()

    def set_demo_opath():
        from zmlx.demo.opath import set_output, opath
        root = opath()
        name = QtWidgets.QFileDialog.getExistingDirectory(
            window, 'Choose Demo Output Folder', root)
        if len(name) > 0:
            set_output(name)
        else:
            print(f'Current folder: {root}')

    def set_plt_export_dpi():
        from zmlx.io.env import plt_export_dpi
        number, ok = QtWidgets.QInputDialog.getDouble(
            window,
            '设置导出图的DPI',
            'DPI',
            plt_export_dpi.get_value(), 50, 3000)
        if ok:
            plt_export_dpi.set_value(number)

    def play_images():
        from zmlx.alg.fsys import list_files
        from zmlx.ui.gui_buffer import gui

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
             slot=lambda: show_widget(
                 module_name='zmlx.ui.widget.demo_widget',
                 widget_name='DemoWidget',
                 caption='示例', on_top=True,
                 oper=lambda w: w.refresh,
                 icon='demo'),
             on_toolbar=True, is_enabled=None, is_visible=lambda: True
             ),

        dict(menu='文件', name='open_cwd',
             text='打开工作路径',
             slot=open_cwd
             ),

        dict(menu='文件', name='view_cwd', icon='cwd',
             text='文件',
             slot=window.view_cwd,
             on_toolbar=True
             ),

        dict(menu='文件', name='py_new', icon='python',
             text='新建Python脚本',
             slot=new_code,
             is_enabled=not_running,
             ),

        dict(menu='文件', name='export_data',
             text='导出',
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

        dict(menu='文件', name='set_demo_opath',
             text='设置示例的数据输出',
             slot=set_demo_opath,
             is_enabled=lambda: isinstance(
                 window.get_current_widget(),
                 DemoWidget) and not window.is_running(),
             ),

        dict(menu='显示', name='refresh', icon='refresh',
             text='刷新',
             slot=window.refresh
             ),

        dict(menu='显示', name='memory', icon='variables',
             text='变量',
             slot=lambda: show_widget(
                 module_name='zmlx.ui.widget.mem_viewer',
                 widget_name='MemViewer',
                 caption='变量', on_top=True,
                 oper=lambda w: w.refresh,
                 icon='variables')
             ),

        dict(menu='显示', name='timer', icon='clock',
             tooltip='显示cpu耗时统计的结果', text='耗时',
             slot=lambda: show_widget(
                 module_name='zmlx.ui.widget.timer_viewer',
                 widget_name='TimerViewer',
                 caption='耗时', on_top=True,
                 oper=lambda w: w.refresh,
                 icon='clock')
             ),

        dict(menu='显示', name='console', icon='console',
             text='Python控制台(测试)',
             slot=lambda: show_widget(
                 module_name='zmlx.ui.widget.pg_console',
                 widget_name='PgConsole',
                 caption='Python控制台', on_top=True,
                 icon='console')
             ),

        dict(menu='显示', name='cls', icon='clean',
             text='清屏',
             slot=window.cls
             ),

        dict(menu='操作', name='console_exec', icon='begin',
             tooltip='运行当前标签页面显示的脚本',
             text='运行',
             slot=exec_current,
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
             slot=lambda: show_widget(
                 module_name='zmlx.ui.widget.file_find',
                 widget_name='FileFind',
                 caption='搜索路径', on_top=True,
                 icon='set')
             ),

        dict(menu='设置', name='env', icon='set',
             text='设置env',
             slot=lambda: show_widget(
                 module_name='zmlx.ui.widget.env_edit',
                 widget_name='EnvEdit',
                 caption='设置Env', on_top=True,
                 icon='set')
             ),

        dict(menu='设置', name='setup_files',
             text='启动文件',
             slot=lambda: show_widget(
                 module_name='zmlx.ui.widget.setup_files_editor',
                 widget_name='SetupFilesEditor',
                 caption='启动文件',
                 on_top=True)
             ),

        dict(menu='设置', name='install_dep',
             text='Python包设置',
             slot=install_dep
             ),

        dict(menu='设置', name='edit_window_style',
             text='窗口风格(qss文件)',
             slot=lambda: show_txt(temp('zml_window_style.qss'))
             ),

        dict(menu='设置', name='set_plt_export_dpi',
             text='设置导出plt图的DPI',
             slot=set_plt_export_dpi
             ),

        dict(menu='帮助', name='readme', icon='info',
             text='ReadMe',
             slot=lambda: show_widget(
                 module_name='zmlx.ui.widget.read_me',
                 widget_name='ReadMeBrowser',
                 caption='ReadMe', on_top=True,
                 icon='info'),
             on_toolbar=True),

        dict(menu='帮助', name='reg', icon='reg',
             text='注册',
             slot=lambda: show_widget(
                 module_name='zmlx.ui.widget.reg_tool',
                 widget_name='RegTool',
                 caption='注册', on_top=True,
                 icon='reg')
             ),

        dict(menu='帮助', name='tab_details',
             text='标签列表',
             tooltip='在一个标签页内显示所有标签也的摘要，当标签特别多的时候比较有用',
             slot=window.tab_details
             ),

        dict(menu='帮助', name='show_code_history',
             text='代码运行历史',
             slot=lambda: window.show_code_history(
                 folder=app_data.root('console_history'),
                 caption='代码运行历史')
             ),

        dict(menu='帮助', name='show_output_history',
             text='输出历史',
             slot=lambda: show_widget(
                 module_name='zmlx.ui.widget.output_history_viewer',
                 widget_name='OutputHistoryViewer',
                 caption='输出历史',
                 on_top=True,
                 oper=lambda w: w.set_folder())
             ),

        dict(menu='帮助', name='papers',
             text='已发表文章',
             slot=lambda: open_url(
                 url="https://pan.cstcloud.cn/s/5cKaQrdFSHM",
                 use_web_engine=False)
             ),

        dict(menu='帮助', name='new_issue',
             text='新建Issue',
             icon='issues',
             slot=lambda: open_url(
                 url='https://gitee.com/geomech/hydrate/issues/new',
                 on_top=True,
                 caption='新建Issue',
                 icon='issues'),
             is_enabled=not_running,
             ),

        dict(menu='帮助', name='iggcas',
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

        dict(menu='帮助', name='feedback',
             text='反馈',
             icon='info',
             slot=lambda: show_widget(
                 module_name='zmlx.ui.widget.feedback',
                 widget_name='FeedbackWidget',
                 caption='反馈'),
             is_enabled=not_running,
             ),

        dict(menu='帮助', name='open_app_data',
             text='打开AppData目录',
             slot=lambda: os.startfile(app_data.root()),
             is_enabled=lambda: zml.lic.is_admin
             ),

        dict(menu='帮助', name='homepage',
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

        dict(menu='帮助', name='about',
             text='关于',
             icon='info',
             slot=about,
             is_enabled=not_running,
             ),

        dict(menu='帮助', name='create_lnk',
             text='创建桌面快捷方式',
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
    except:
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
        except Exception as err:
            print(err)
            return False

    if data.get('is_visible') is None:
        is_visible = None
    else:
        def is_visible():
            try:
                return window.parse_value(data.get('is_visible'))
            except:
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
    for path in reversed(find_all('zml_actions')):
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
