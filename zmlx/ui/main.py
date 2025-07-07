import datetime
import os
import sys

import zmlx.alg.sys as warnings
from zml import lic, core, app_data, read_text, get_dir, is_chinese, \
    log as zml_log
from zmlx.alg.fsys import has_permission, samefile, time_string
from zmlx.ui import settings
from zmlx.ui.alg import show_seepage, open_url, get_last_exec_history
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import (QtCore, QtWidgets, QtMultimedia, QAction, QtGui,
                          is_pyqt6, QWebEngineView, QWebEngineSettings)
from zmlx.ui.utils import TaskProc, GuiApi, FileHandler
from zmlx.ui.widget import (
    CodeEdit, Console, Label, TabWidget, VersionLabel)


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


class MainWindow(QtWidgets.QMainWindow):
    sig_cwd_changed = QtCore.pyqtSignal(str)
    sig_do_task = QtCore.pyqtSignal()
    sig_play_sound = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowIcon(settings.load_icon('app'))
        self.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.__task_proc = TaskProc(self)

        self.__file_handler = FileHandler(self)
        for opt in [
            dict(desc='Python文件', exts=['.py'], func=self.open_code),
            dict(desc='文本文件', exts=['.txt', '.json', '.xml', '.qss'],
                 func=self.open_text),
            dict(desc='二维裂缝', exts=['.fn2'], func=self.show_fn2),
            dict(desc='Seepage模型文件', exts=['.seepage'], func=show_seepage),
            dict(desc='图片', exts=['.png', '.jpg'], func=self.open_image),
            dict(desc='PDF文件', exts=['.pdf'], func=self.open_pdf),
        ]:
            self.__file_handler.add(**opt)

        widget = QtWidgets.QWidget(self)
        h_layout = QtWidgets.QVBoxLayout(widget)
        splitter = QtWidgets.QSplitter(widget)
        splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.__tab_widget = TabWidget(splitter)
        self.__tab_widget.currentChanged.connect(self.refresh)
        self.__console = Console(splitter)
        self.__gui_api = GuiApi(
            widget,
            self.__console.get_break_point(),
            self.__console.get_flag_exit())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        h_layout.addWidget(splitter)
        self.setCentralWidget(widget)
        self.__title = None
        self.__init_gui_api()  # 在成员声明了之后，第一时间初始化API
        self.__init_actions()

        self.sig_cwd_changed.connect(self.refresh)
        self.sig_cwd_changed.connect(self.view_cwd)
        self.sig_cwd_changed.connect(self.__console.restore_code)

        self.__console.sig_refresh.connect(self.refresh)

        # 尝试关闭进度条，从而使得进度条总是临时显示一下.
        self.__timer_close_progress = QtCore.QTimer(self)
        self.__timer_close_progress.timeout.connect(
            lambda: self.progress(visible=False))
        self.__timer_close_progress.start(5000)

        self.__progress_label = Label()
        self.__progress_bar = QtWidgets.QProgressBar()
        self.statusBar().addPermanentWidget(self.__progress_label)
        self.statusBar().addPermanentWidget(self.__progress_bar)
        self.statusBar().addPermanentWidget(VersionLabel())
        self.progress(visible=False)

        # 用以显示警告
        self.__warning_toolbar = self.addToolBar('WarningToolbar')
        self.__warning_toolbar.setVisible(False)
        self.__warning_toolbar.setStyleSheet('background-color: yellow;')
        self.__warning_action = Action(self)
        self.__warning_action.setToolTip('警告消息(点击以隐藏)')
        self.__warning_action.triggered.connect(
            lambda: self.toolbar_warning(text=''))
        self.__warning_toolbar.addAction(self.__warning_action)

        # 用以播放声音
        if QtMultimedia is not None:
            self.__sound = QtMultimedia.QSoundEffect()
        else:
            self.__sound = None

        def play(name):
            if self.__sound is not None:
                self.__sound.setSource(QtCore.QUrl.fromLocalFile(name))
                self.__sound.play()

        self.sig_play_sound.connect(play)

        try:
            filename = settings.find_icon_file('welcome')
            if filename is not None:
                if os.path.isfile(filename):
                    self.open_image(filename, caption='Welcome')
        except Exception as err:
            print(f'Error: {err}')

        try:
            if app_data.getenv(key='check_lic_when_start', default='No',
                               ignore_empty=True) == 'Yes':
                self.check_license()
        except Exception as err:
            print(f'Error: {err}')

        self.refresh()

    def __init_gui_api(self):
        # 默认，将所有新的定义的函数都添加到GUI API中
        for key in self.list_member_functions():
            func = getattr(self, key)
            if callable(func):
                self.__gui_api.add_func(key, func)
        self.__gui_api.add_func('close', self.close)
        self.__gui_api.add_func('show_next', self.__tab_widget.show_next)
        self.__gui_api.add_func('show_prev', self.__tab_widget.show_prev)
        self.__gui_api.add_func('status', self.show_status)
        self.__gui_api.add_func('start', self.start_func)
        self.__gui_api.add_func('tab_count', self.count_tabs)
        self.__gui_api.add_func('title', self.set_title)
        self.__gui_api.add_func('window', lambda: self)
        self.__gui_api.add_func('is_maximized', lambda: self.isMaximized())
        self.__gui_api.add_func('show_maximized', lambda: self.showMaximized())
        self.__gui_api.add_func('resize', self.resize)
        self.__gui_api.add_func('device_pixel_ratio', self.devicePixelRatioF)

    def __init_actions(self):
        """
        初始化内置的菜单动作
        """
        from zmlx.alg.sys import create_ui_lnk_on_desktop

        def not_running():
            return not self.is_running()

        def console_exec():
            f = getattr(self.get_current_widget(), 'console_exec', None)
            if callable(f):
                f()

        def pause_enabled():
            c = self.get_console()
            if not c.is_running():
                return False
            return not c.get_pause()

        def about():
            print(lic.desc)
            self.show_about()

        def set_plt_export_dpi():
            from zmlx.io.env import plt_export_dpi
            number, ok = QtWidgets.QInputDialog.getDouble(
                self,
                '设置导出图的DPI',
                'DPI',
                plt_export_dpi.get_value(), 50, 3000)
            if ok:
                plt_export_dpi.set_value(number)

        data = [
            dict(menu='文件', name='set_cwd', icon='open',
                 tooltip='设置工作路径 (在进行各种操作前，务必确保工作路径正确)',
                 text='工作路径',
                 slot=self.set_cwd_by_dialog,
                 on_toolbar=True,
                 is_enabled=not_running,
                 is_visible=lambda: True
                 ),

            dict(menu='文件', name='quit', icon='quit',
                 text='退出',
                 slot=self.close,
                 ),

            dict(menu='文件', name='open', icon='open',
                 tooltip='打开文件', text='打开',
                 slot=self.open_file_by_dlg,
                 on_toolbar=True,
                 is_enabled=not_running, is_visible=lambda: True
                 ),

            dict(menu='文件', name='demo', icon='demo',
                 tooltip=None, text='示例',
                 slot=self.show_demo,
                 on_toolbar=True, is_enabled=None, is_visible=lambda: True
                 ),

            dict(menu='文件', name='view_cwd', icon='cwd',
                 text='文件',
                 slot=self.view_cwd,
                 on_toolbar=True
                 ),

            dict(menu='文件', name='py_new', icon='python',
                 text='新建脚本',
                 slot=self.new_code,
                 is_enabled=not_running,
                 ),

            dict(menu='文件', name='export_data',
                 text='导出数据',
                 slot=lambda: getattr(self.get_current_widget(),
                                      'export_data')(),
                 is_enabled=lambda: hasattr(
                     self.get_current_widget(),
                     'export_data') and not self.is_running(),
                 ),

            dict(menu='文件', name='export_plt_figure',
                 text='导出plt图',
                 on_toolbar=True,
                 slot=lambda: getattr(self.get_current_widget(),
                                      'export_plt_figure')(),
                 is_enabled=lambda: hasattr(
                     self.get_current_widget(),
                     'export_plt_figure') and not self.is_running(),
                 ),

            dict(menu='显示', name='refresh', icon='refresh',
                 text='刷新',
                 slot=self.refresh
                 ),

            dict(menu='显示', name='memory', icon='variables',
                 text='变量',
                 slot=self.show_memory
                 ),

            dict(menu='显示', name='timer', icon='clock',
                 tooltip='显示cpu耗时统计的结果', text='耗时',
                 slot=self.show_timer
                 ),

            dict(menu='显示', name='console', icon='console',
                 text='Python控制台(测试)',
                 slot=self.show_pg_console
                 ),

            dict(menu='显示', name='cls', icon='clean',
                 text='清屏',
                 slot=self.cls
                 ),

            dict(menu='显示', name='tab_details',
                 text='标签列表',
                 tooltip='在一个标签页内显示所有标签也的摘要，当标签特别多的时候比较有用',
                 slot=self.show_tab_details
                 ),

            dict(menu='显示', name='show_code_history',
                 text='运行历史',
                 slot=lambda: self.show_code_history(
                     folder=app_data.root('console_history'),
                     caption='运行历史')
                 ),

            dict(menu='显示', name='show_output_history',
                 text='输出历史',
                 slot=self.show_output_history,
                 ),

            dict(menu='操作', name='console_exec', icon='begin',
                 tooltip='运行当前标签页面显示的脚本',
                 text='运行',
                 slot=console_exec,
                 on_toolbar=True,
                 is_enabled=lambda: hasattr(
                     self.get_current_widget(),
                     'console_exec') and not self.is_running(),
                 is_visible=not_running,
                 ),

            dict(menu='操作', name='console_pause',
                 icon='pause',
                 tooltip='暂停内核的执行 (需要提前在脚本内设置break_point)',
                 text='暂停',
                 slot=lambda: self.get_console().set_pause(True),
                 on_toolbar=True,
                 is_enabled=pause_enabled,
                 ),

            dict(menu='操作', name='console_resume',
                 icon='begin',
                 tooltip=None, text='继续',
                 slot=lambda: self.get_console().set_pause(False),
                 on_toolbar=True,
                 is_enabled=lambda: self.is_running() and self.get_console().get_pause(),
                 ),

            dict(menu='操作', name='console_stop', icon='stop',
                 tooltip='安全地终止内核的执行 (需要提前在脚本内设置break_point)',
                 text='停止',
                 slot=lambda: self.get_console().stop(),
                 on_toolbar=True,
                 is_enabled=self.is_running
                 ),

            dict(menu='操作', name='console_kill', icon='kill',
                 text='强制结束',
                 slot=self.kill_thread,
                 is_enabled=self.is_running
                 ),

            dict(menu='操作', name='console_hide',
                 icon='console',
                 tooltip='隐藏主窗口右侧的控制台', text='隐藏',
                 slot=lambda: self.get_console().setVisible(False),
                 on_toolbar=True,
                 is_enabled=lambda: self.get_console().isVisible()
                 ),

            dict(menu='操作', name='console_show',
                 icon='console',
                 tooltip='显示主窗口右侧的控制台', text='显示',
                 slot=lambda: self.get_console().setVisible(True),
                 on_toolbar=True,
                 is_enabled=lambda: not self.get_console().isVisible()
                 ),

            dict(menu='操作', name='console_start_last',
                 text='重新执行',
                 slot=self.get_console().start_last,
                 is_enabled=lambda: not self.is_running() and get_last_exec_history() is not None,
                 ),

            dict(menu='操作', name='close_all_tabs',
                 icon='close_all',
                 text='关闭所有页面',
                 slot=self.close_all_tabs,
                 is_enabled=lambda: self.count_tabs() > 0,
                 ),

            dict(menu='设置', name='search', icon='set',
                 text='搜索路径',
                 slot=self.show_file_finder
                 ),

            dict(menu='设置', name='env', icon='set',
                 text='Env变量',
                 slot=self.show_env_edit
                 ),

            dict(menu='设置', name='setup_files',
                 text='Setup文件',
                 slot=self.edit_setup_files
                 ),

            dict(menu='设置', name='edit_window_style',
                 text='风格(qss)',
                 slot=lambda: self.open_text(
                     app_data.temp('zml_window_style.qss'), '窗口风格')
                 ),

            dict(menu='设置', name='set_plt_export_dpi',
                 text='plt的DPI',
                 slot=set_plt_export_dpi
                 ),

            dict(menu='帮助', name='readme', icon='info',
                 text='ReadMe',
                 slot=self.show_readme,
                 on_toolbar=True),

            dict(menu='帮助', name='about',
                 text='关于',
                 icon='info',
                 slot=about,
                 is_enabled=not_running,
                 ),

            dict(menu='帮助', name='reg', icon='reg',
                 text='注册',
                 slot=self.show_reg_tool
                 ),

            dict(menu='帮助', name='feedback',
                 text='反馈',
                 icon='info',
                 slot=self.show_feedback,
                 is_enabled=not_running,
                 ),

            dict(menu='帮助', name='create_lnk',
                 text='创建快捷方式',
                 slot=create_ui_lnk_on_desktop,
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
        ]
        for opt in data:
            self.add_action(**opt)

    def add_action(self, menu=None, text=None, name=None, slot=None,
                   icon=None, tooltip=None,
                   on_toolbar=None,
                   is_enabled=None,
                   is_visible=None
                   ):
        """
        添加一个Action. 这是一个新的版本，将替代后续的直接基于File的ActionX的创建方法，
        并且将支持动态地创建Action。
        Since 2026-6-9.
        """
        if self.get_action(name=name, create_empty=False) is not None:
            warnings.warn(
                f'The action already exists: {name}',
                UserWarning, stacklevel=2)
            name = None

        if name is None:
            index = 1
            while self.get_action(name='unnamed_%03d' % index,
                                  create_empty=False) is not None:
                index += 1
            name = 'unnamed_%03d' % index

        action = Action(self)
        action.setObjectName(name)

        if callable(is_enabled):  # 作为一个函数，动态地判断是否可用
            action.is_enabled = is_enabled

        if callable(is_visible):  # 作为一个函数，动态地判断是否可见
            action.is_visible = is_visible

        action.setIcon(settings.load_icon(
            icon if icon is not None else 'python'))

        if tooltip is not None:
            action.setToolTip(settings.get_text(tooltip))

        if text is not None:
            action.setText(settings.get_text(text))
        else:
            action.setText(name)

        def slot_x():
            try:
                self.parse_value(slot)
                app_data.log(f'run <{name}>')
                self.refresh()  # since 2024-10-11
            except Exception as e2:
                info = f'meet error when run <{name}>. \nInfo = \n {e2}'
                print(info)
                app_data.log(info)

        action.triggered.connect(slot_x)

        if menu is None:
            menu = '其它'

        if on_toolbar:
            toolbar_name = menu if isinstance(menu, str) else menu[0]
            self.get_toolbar(toolbar_name).addAction(action)

        self.get_menu(menu).addAction(action)

    def parse_value(self, value):
        if callable(value):  # 直接是一个函数，直接运行
            return value()

        if isinstance(value, dict):  # 字典，则尝试作为带有参数的函数
            on_window = value.get('on_window', None)
            if callable(on_window):
                return on_window(self)

            func = value.get('func', None)
            if callable(func):
                args = value.get('args', [])
                args = [self if item == '@window' else item for item in args]
                return func(*args)

        # 直接返回数值
        return value

    def get_menu(self, name):
        """
        返回给定name的菜单
        """
        assert name is not None, f'Error: name is None when get_menu'
        if isinstance(name, str):
            keys = [name]
        else:
            keys = name
        if len(keys) == 0:
            return None

        keys = [settings.get_text(key) for key in keys]  # 替换字符串

        menu = None
        for action in self.menuBar().actions():
            if isinstance(action.menu(), QtWidgets.QMenu):
                if action.menu().title() == keys[0]:
                    menu = action.menu()
                    break

        if menu is None:
            menu = QtWidgets.QMenu(self.menuBar())
            menu.setTitle(keys[0])
            self.menuBar().addAction(menu.menuAction())

        # 现在，主menu找到了，下面，找次一级的menu
        for idx in range(1, len(keys)):
            key = keys[idx]
            sub_menu = None
            for action in menu.actions():
                if isinstance(action.menu(), QtWidgets.QMenu):
                    if action.menu().title() == key:
                        sub_menu = action.menu()
                        break
            if sub_menu is None:
                sub_menu = QtWidgets.QMenu(menu)
                sub_menu.setTitle(key)
                menu.addAction(sub_menu.menuAction())
            menu = sub_menu  # 设置为当前层级的目录
        # 完成了所有的遍历，找到对应的menu
        return menu

    def get_toolbar(self, name: str):
        """
        返回对应的菜单的工具栏
        """
        for toolbar in self.findChildren(QtWidgets.QToolBar):
            if toolbar.windowTitle() == name:
                return toolbar
        return self.addToolBar(name)

    def list_actions(self):
        names = []
        for action in self.findChildren(QAction):
            name = action.objectName()
            if isinstance(name, str):
                if len(name) > 0:
                    names.append(name)
        return names

    def count_tabs(self):
        return self.__tab_widget.count()

    def close_all_tabs(self):
        self.__tab_widget.close_all_tabs()

    def cls(self):
        self.__console.output_widget.clear()

    def kill_thread(self):
        self.__console.kill_thread()

    def toolbar_warning(self, text=None):
        if isinstance(text, str):
            if len(text) > 0:
                self.__warning_toolbar.setVisible(True)
                self.__warning_action.setText(text)
                zml_log(text)
            else:
                self.__warning_toolbar.setVisible(False)
                self.__warning_action.setText('')

    def refresh(self):
        """
        尝试刷新标题以及当前的页面
        """
        if self.__title is not None:
            self.setWindowTitle(f'{self.__title}')
        else:
            self.setWindowTitle(f'WorkDir: {os.getcwd()}')

        try:
            current = self.get_current_widget()
            if hasattr(current, 'refresh'):
                self.__task_proc.add(lambda: current.refresh())
        except Exception as err:
            print(f'Error: {err}')

        for action in self.findChildren(QAction):
            update_view = getattr(action, 'update_view', None)
            if callable(update_view):
                update_view()

        # 调用刷新
        self.__console.refresh_view()

    def closeEvent(self, event):
        if self.__console.is_running():
            reply = QtWidgets.QMessageBox.question(
                self, '退出UI',
                "内核似乎正在运行，确定要退出吗？",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        on_close = getattr(self, 'on_close', None)
        if callable(on_close):  # 在确定要关闭之前执行的操作
            on_close()

    def showEvent(self, event):
        super(MainWindow, self).showEvent(event)
        self.refresh()

    def get_widget(
            self, the_type, caption=None, on_top=None, init=None,
            type_kw=None, oper=None, icon=None, caption_color=None,
            set_parent=False):
        """
        返回一个控件，其中type为类型，caption为标题，现有的控件，只有类型和标题都满足，才会返回，否则就
        创建新的控件。
        init：首次生成控件，在显示之前所做的操作
        oper：每次调用都会执行，且在控件显示之后执行
        """
        if caption is None:
            caption = 'untitled'
        widget = self.__tab_widget.find_widget(the_type=the_type, text=caption)
        if widget is None:
            if self.__tab_widget.count() >= 200:
                print(f'The current number of tabs has reached '
                      f'the maximum allowed')
                return None  # 为了稳定性，不允许标签页太多
            if type_kw is None:
                type_kw = {}
            if set_parent:
                type_kw['parent'] = self
            try:
                widget = the_type(**type_kw)
                assert isinstance(widget, the_type)
            except Exception as err:
                print(f'Error: {err}')
                return None
            if init is not None:
                try:
                    init(widget)
                except Exception as err:
                    print(f'Error: {err}')
            index = self.__tab_widget.addTab(widget, caption)
            if icon is not None:
                self.__tab_widget.setTabIcon(index, settings.load_icon(icon))
            self.__tab_widget.setCurrentWidget(widget)
            if caption_color is not None:
                self.__tab_widget.tabBar().setTabTextColor(
                    index, QtGui.QColor(caption_color)
                )
            if oper is not None:
                self.add_task(lambda: oper(widget))
            return widget
        else:
            if on_top:
                self.__tab_widget.setCurrentWidget(widget)
            if oper is not None:
                self.add_task(lambda: oper(widget))
            return widget

    def get_figure_widget(self, clear=True, **kwargs):
        """
        返回一个用以 matplotlib 绘图的控件
        """
        from zmlx.ui.widget.plt import MatplotWidget
        if kwargs.get('icon') is None:
            kwargs['icon'] = 'matplotlib'
        widget = self.get_widget(the_type=MatplotWidget, **kwargs)
        assert isinstance(widget, MatplotWidget)
        if clear:
            widget.figure.clear()
        return widget

    def show_fn2(self, filepath, **kwargs):
        warnings.warn('gui.show_fn2 will be removed after 2026-3-5, '
                      'please use zmlx.plt.show_fn2 instead',
                      DeprecationWarning, stacklevel=2)
        from zmlx.ui.widget.fn2 import Fn2Widget
        if kwargs.get('caption') is None:
            kwargs['caption'] = 'Fractures'
        widget = self.get_widget(the_type=Fn2Widget, **kwargs)
        assert widget is not None
        widget.open_fn2_file(filepath)

    def plot(self, kernel=None, fname=None, dpi=300, **kwargs):
        if kernel is not None:
            try:
                widget = self.get_figure_widget(**kwargs)
                widget.plot_on_figure(on_figure=kernel)
                if fname is not None:
                    assert dpi is not None
                    widget.savefig(fname=fname, dpi=dpi)
            except Exception as err:
                warnings.warn(f'meet exception <{err}> when run <{kernel}>')

    def show_status(self, *args, **kwargs):
        self.statusBar().showMessage(*args, **kwargs)

    def trigger(self, name):
        action = self.get_action(name)
        if hasattr(action, 'trigger'):
            action.trigger()

    def get_action(self, name, create_empty=None):
        """
        返回给定name的菜单action
        """
        if isinstance(name, str):
            for action in self.findChildren(QAction):
                if action.objectName() == name or action.objectName() == name + '.py':
                    return action
        if create_empty is None:
            create_empty = True
        if create_empty:
            warnings.warn(f'cannot find the action with name: <{name}>',
                          UserWarning, stacklevel=2)
            action = QAction(parent=self)
            if name is not None:
                action.setText(name)
            else:
                action.setText('unnamed')
            return action
        else:
            return None

    def set_title(self, title):
        self.__title = title
        self.refresh()

    def view_cwd(self):
        from zmlx.ui.widget.base import CwdView

        def oper(w):
            w.refresh()
            w.gui_restore = f"""gui.view_cwd()"""  # 用于重启

        self.get_widget(
            the_type=CwdView, caption='文件', on_top=True,
            oper=oper,
            icon='cwd')

    def progress(
            self, label=None, val_range=None, value=None, visible=None,
            duration=5000):
        """
        显示进度
        """
        if label is not None:
            visible = True
            self.__progress_label.setText(label)
        if val_range is not None:
            visible = True
            assert len(val_range) == 2
            self.__progress_bar.setRange(*val_range)
        if value is not None:
            visible = True
            self.__progress_bar.setValue(value)
        if visible is not None:
            self.__progress_bar.setVisible(visible)
            self.__progress_label.setVisible(visible)
            if visible:
                self.__timer_close_progress.setInterval(duration)
            else:
                self.__timer_close_progress.setInterval(5000000)  # 不再执行

    def open_code(self, fname, caption=None):
        if not isinstance(fname, str):
            return

        def get_widget(name_1):
            for i in range(self.__tab_widget.count()):
                widget_ = self.__tab_widget.widget(i)
                if isinstance(widget_, CodeEdit):
                    if samefile(name_1, widget_.get_fname()):
                        return widget_
                    return None
                return None
            return None

        if len(fname) > 0:
            if samefile(fname, self.__console.get_fname()):
                return
            widget = get_widget(fname)
            if widget is not None:
                self.__tab_widget.setCurrentWidget(widget)
                return
            else:
                def oper(x):
                    x.open(fname)
                    kwds = dict(fname=fname, caption=caption)
                    x.gui_restore = f"""gui.open_code(**{kwds})"""  # 用于重启

                if caption is None:
                    caption = os.path.basename(fname)

                self.get_widget(
                    the_type=CodeEdit,
                    caption=caption,
                    on_top=True,
                    oper=oper, icon='python')
                if app_data.getenv('show_info_after_code_open',
                                   default='') != 'No':
                    print(
                        f'文件已打开: \n\t{fname}\n\n请点击工具栏上的<运行>按钮以运行!\n\n')

    def open_text(self, fname, caption=None):
        from zmlx.ui.widget.base import TextFileEdit
        if not isinstance(fname, str):
            return
        if len(fname) > 0:
            for i in range(self.__tab_widget.count()):
                widget = self.__tab_widget.widget(i)
                if isinstance(widget, TextFileEdit):
                    if samefile(fname, widget.get_fname()):
                        self.__tab_widget.setCurrentWidget(widget)
                        return

            def oper(x):
                x.set_fname(fname)
                kwds = dict(fname=fname, caption=caption)
                x.gui_restore = f"""gui.open_text(**{kwds})"""  # 用于重启

            if caption is None:
                caption = os.path.basename(fname)

            self.get_widget(
                the_type=TextFileEdit,
                caption=caption,
                on_top=True, oper=oper,
            )

    def open_image(self, fname, caption=None, on_top=True):
        """
        打开一个图片
        """
        if isinstance(fname, str):
            if os.path.isfile(fname):
                from zmlx.ui.widget.img import ImageView

                def oper(x):
                    x.set_image(fname)
                    kwds = dict(fname=fname, caption=caption, on_top=on_top)
                    x.gui_restore = f"""gui.open_image(**{kwds})"""  # 用于重启

                if caption is None:
                    caption = os.path.basename(fname)

                self.get_widget(
                    the_type=ImageView,
                    caption=caption,
                    on_top=on_top, oper=oper
                )

    def open_pdf(self, fname, caption=None, on_top=True):
        """
        打开一个pdf
        """
        assert isinstance(fname,
                          str), f'The given fname is not a string: {fname}'
        if not os.path.isfile(fname):
            print(f'File not exist: {fname}')
            return
        if QWebEngineView is None or QWebEngineSettings is None:
            print('QWebEngineView is not installed')
            return

        def oper(w):
            kwds = dict(fname=fname, caption=caption, on_top=on_top)
            w.gui_restore = f"""gui.open_pdf(**{kwds})"""  # 用于重启
            w.settings().setAttribute(
                QWebEngineSettings.WebAttribute.PluginsEnabled, True)
            w.settings().setAttribute(
                QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
            if fname.startswith("file://"):
                w.load(QtCore.QUrl(fname))
            else:
                w.load(QtCore.QUrl(QtCore.QUrl.fromLocalFile(
                    os.path.abspath(fname)).toString()))

        if caption is None:
            caption = os.path.basename(fname)

        self.get_widget(
            the_type=QWebEngineView, caption=caption, on_top=on_top,
            oper=oper,
        )

    def new_code(self):
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            caption='新建.py脚本',
            directory=os.getcwd(),
            filter='Python File (*.py);;')
        self.open_code(fname)

    def exec_current(self):
        widget = self.__tab_widget.currentWidget()
        if isinstance(widget, CodeEdit):
            widget.save()
            self.__console.exec_file(widget.get_fname())
        else:
            self.__console.exec_file()

    def add_file_handler(self, desc, exts, func):
        return self.__file_handler.add(desc=desc, exts=exts, func=func)

    def open_file(self, filepath):
        return self.__file_handler.open_file(filepath)

    def open_file_by_dlg(self, folder=None):
        return self.__file_handler.open_file_by_dlg(folder=folder)

    def set_cwd(self, folder):
        if isinstance(folder, str):
            if os.path.isdir(folder):
                if has_permission(folder):
                    try:
                        os.chdir(folder)
                        settings.save_cwd()
                        self.sig_cwd_changed.emit(os.getcwd())
                    except Exception as err:
                        print(f'Error: {err}')

    def set_cwd_by_dialog(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, settings.get_text('请选择工程文件夹'), os.getcwd())
        self.set_cwd(folder)

    def get_current_widget(self):
        return self.__tab_widget.currentWidget()

    def exec_file(self, filename):
        self.__console.exec_file(filename)

    def start_func(self, *args, **kwargs):
        """
        在控制台执行代码
        """
        self.__console.start_func(*args, **kwargs)

    def get_output_widget(self):
        return self.__console.output_widget

    def add_task(self, task):
        self.__task_proc.add(task)

    def get_gui_api(self):
        return self.__gui_api

    def get_console(self):
        return self.__console

    def exec_tab_func(self, name):
        widget = self.get_current_widget()
        if hasattr(widget, name):
            f = getattr(widget, name)
            f()

    def is_running(self):
        return self.__console.is_running()

    def get_tabs(self):
        return self.__tab_widget

    def check_license(self):
        try:
            while core.has_log():
                core.pop_log()
            if not lic.valid:
                while core.has_log():
                    print(core.pop_log())
                print('\n\n')
                self.toolbar_warning(
                    '此电脑未授权，请确保: 1、使用最新版；2、本机联网!')
        except Exception as err:
            print(f'Error: {err}')

    def show_about(self):
        from zmlx.ui.widget.base import About
        self.check_license()

        def oper(widget):
            widget.gui_restore = f"""gui.show_about()"""

        self.get_widget(
            the_type=About, caption='关于', on_top=True,
            icon='info', type_kw=dict(lic_desc=lic.desc),
            oper=oper
        )

    def play_sound(self, filename):
        """
        播放声音
        """
        if isinstance(filename, str):
            if not os.path.isfile(filename):
                filename = settings.find_sound(filename)
                if filename is None:
                    return
            if os.path.isfile(filename):
                self.sig_play_sound.emit(filename)

    def show_tab_details(self):
        from zmlx.ui.widget.base import TabDetailView
        def oper(w):
            w.gui_restore = f"""gui.show_tab_details()"""

        self.get_widget(
            the_type=TabDetailView, caption='标签列表', on_top=True,
            type_kw={'obj': TabDetailView.TabWrapper(self.__tab_widget)},
            oper=oper,
        )

    def show_code_history(self, folder, caption=None):
        from zmlx.ui.widget.base import CodeHistoryView
        if not isinstance(folder, str):
            return

        if os.path.isdir(folder):
            kwds = dict(folder=folder, caption=caption)

            if caption is None:
                caption = os.path.basename(folder)

            def oper(widget):
                widget.set_folder(folder=folder)
                widget.gui_restore = f"""gui.show_code_history(**{kwds})"""

            self.get_widget(
                the_type=CodeHistoryView,
                caption=caption,
                on_top=True, oper=oper, icon='python'
            )

    def show_output_history(self):
        from zmlx.ui.widget import OutputHistoryView

        def oper(w):
            w.gui_restore = f"""gui.show_output_history()"""
            w.set_folder()

        self.get_widget(
            the_type=OutputHistoryView,
            caption='输出历史',
            on_top=True, oper=oper
        )

    def list_member_functions(self):
        """
        列出所有成员函数（排除私有方法）
        """
        import inspect
        return [name for name, _ in inspect.getmembers(self.__class__)
                if inspect.isfunction(getattr(self.__class__, name))
                and not name.startswith('__')]

    def show_demo(self):
        from zmlx.ui.widget import DemoView

        def oper(w):
            w.refresh()
            w.gui_restore = f"""gui.show_demo()"""

        self.get_widget(the_type=DemoView, caption='示例', on_top=True,
                        oper=oper, icon='demo')

    def show_memory(self):
        from zmlx.ui.widget import MemView
        def oper(w):
            w.refresh()
            w.gui_restore = f"""gui.show_memory()"""

        self.get_widget(the_type=MemView, caption='变量', on_top=True,
                        icon='variables', oper=oper)

    def show_timer(self):
        from zmlx.ui.widget import TimerView

        def oper(w):
            w.refresh()
            w.gui_restore = f"""gui.show_timer()"""

        self.get_widget(the_type=TimerView, caption='耗时', on_top=True,
                        icon='clock', oper=oper)

    def show_pg_console(self):
        from zmlx.ui.widget.base import PgConsole
        if PgConsole is None:
            return

        def oper(w):
            w.gui_restore = f"""gui.show_pg_console()"""

        self.get_widget(the_type=PgConsole, caption='Python控制台', on_top=True,
                        icon='console', oper=oper)

    def show_file_finder(self):
        from zmlx.ui.widget import AppPathEdit
        def oper(w):
            w.gui_restore = f"""gui.show_file_finder()"""

        self.get_widget(the_type=AppPathEdit, caption='搜索路径',
                        on_top=True,
                        icon='set', oper=oper)

    def show_env_edit(self):
        from zmlx.ui.widget import EnvEdit

        def oper(w):
            w.gui_restore = f"""gui.show_env_edit()"""

        self.get_widget(the_type=EnvEdit, caption='设置Env', on_top=True,
                        icon='set', oper=oper,
                        type_kw=dict(items=settings.get_env_items())
                        )

    def edit_setup_files(self):
        from zmlx.ui.widget import SetupFileEdit

        def oper(w):
            w.gui_restore = f"""gui.edit_setup_files()"""

        self.get_widget(the_type=SetupFileEdit, caption='启动文件',
                        on_top=True,
                        icon='set', oper=oper)

    def show_readme(self):
        from zmlx.ui.widget import ReadMeBrowser

        def oper(w):
            w.gui_restore = f"""gui.show_readme()"""

        self.get_widget(the_type=ReadMeBrowser, caption='ReadMe', on_top=True,
                        icon='info', oper=oper)

    def show_reg_tool(self):
        from zmlx.ui.widget import RegTool

        def oper(w):
            w.gui_restore = f"""gui.show_reg_tool()"""

        self.get_widget(the_type=RegTool, caption='注册', on_top=True,
                        icon='reg', oper=oper)

    def show_feedback(self):
        from zmlx.ui.widget import FeedbackTool

        def oper(w):
            w.gui_restore = f"""gui.show_feedback()"""

        self.get_widget(the_type=FeedbackTool, caption='反馈', on_top=True,
                        icon='info', oper=oper)

    def open_url(self, url, caption=None, on_top=None, zoom_factor=None,
                 icon=None):
        """
        显示一个html文件或者网址
        """
        if not isinstance(url, str):
            return

        if QWebEngineView is None:
            if os.path.isfile(url):
                os.startfile(url)
            else:
                from webbrowser import open_new_tab
                open_new_tab(url)
            return

        kwds = dict(
            url=url, caption=caption, on_top=on_top,
            zoom_factor=zoom_factor, icon=icon
        )

        if zoom_factor is None:
            zoom_factor = 1.0 if is_pyqt6 else 1.5

        def oper(widget):
            widget.page().setZoomFactor(zoom_factor)
            if os.path.isfile(url):
                widget.load(QtCore.QUrl.fromLocalFile(url))
            else:
                widget.load(QtCore.QUrl(url))
            widget.gui_restore = f"""gui.open_url(**{kwds})"""

        if icon is None:
            icon = 'web'

        self.get_widget(
            the_type=QWebEngineView, caption=caption, on_top=on_top,
            oper=oper, icon=icon)


class MySplashScreen(QtWidgets.QSplashScreen):
    def mousePressEvent(self, event):
        pass


def __make_splash(app):
    splash_fig = settings.load_pixmap('splash')
    if splash_fig is not None and app_data.getenv(
            'disable_splash',
            default='No',
            ignore_empty=True) != 'Yes':
        splash = MySplashScreen()
        try:
            rect = settings.get_current_screen_geometry(splash)
            splash_fig = splash_fig.scaled(
                round(rect.width() * 0.3),
                round(rect.height() * 0.3),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        except Exception as err:
            print(f'Error: {err}')
        splash.setPixmap(splash_fig)
        splash.show()
        app.processEvents()  # 处理主进程事件
    else:
        splash = None
    return splash


def __exception_hook(the_type, value, tb):
    message = f"""Exception Type: {the_type}
Message : {value}
Object : {tb} We are very sorry for this exception. Please check your data according to the above message. If it's 
still unresolved, please contact the author (email: 'zhangzhaobin@mail.iggcas.ac.cn'), Thank you!"""
    print(message)


def __restore_history(win):
    # 恢复窗口的输出历史
    try:
        if app_data.getenv(
                key='restore_console_output', default='Yes',
                ignore_empty=True) != 'No':
            from zmlx.alg.fsys import get_latest_file, get_size_mb
            filename = get_latest_file(app_data.root('output_history'))
            if filename is not None:
                if 0 < get_size_mb(filename) < 0.5:
                    win.get_output_widget().load_text(filename)
    except Exception as Err:
        print(f'Error: {Err}')

    # 输出历史显示之后，再输出当前时间
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    win.get_output_widget().write(f'====== {now} ====== \n')


def __save_history(win):
    # 保存输出历史
    win.get_output_widget().save_text(
        app_data.root('output_history', f'{time_string()}.txt'))


def __on_init(win):
    # step 1
    app_data.put('sys_excepthook', sys.excepthook)  # 备份原来的异常处理函数
    sys.excepthook = __exception_hook

    # step 2. 设置main_window
    app_data.space['main_window'] = win

    # step 3. gui
    gui.set(win.get_gui_api())

    # step 4. 恢复输出历史
    __restore_history(win)

    # step 5. stdout and stderr
    sys.stdout = win.get_output_widget()
    sys.stderr = win.get_output_widget()


def __on_exit(win):
    # step 5. stdout and stderr (此事，界面不应该再接收print，这是首先要做的)
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    # step 4 保存输出历史
    __save_history(win)

    # step 3. gui
    gui.set(None)

    # step 2. 恢复 main_window
    app_data.space['main_window'] = None

    # step 1.
    sys_excepthook = app_data.get('sys_excepthook', None)
    if callable(sys_excepthook):
        sys.excepthook = sys_excepthook  # 恢复原来的异常处理函数


def __on_show(win):
    """
    在首次显示窗口之后执行的操作
    """
    # 必须在窗口正式显示之后，否则此函数可能会出错
    settings.load_window_size(win)

    # 设置窗口风格
    try:
        if app_data.getenv(
                key='load_window_style', default='Yes',
                ignore_empty=True) != 'No':
            text = settings.load(
                key='zml_window_style.qss',
                default='',
                encoding='utf-8', ignore_empty=True)
            if len(text) > 0:
                win.setStyleSheet(text)
    except Exception as err:
        print(f'Error: {err}')


def __add_code_history():
    try:  # 在尝试调用gui执行的时候，添加代码执行历史
        if len(sys.argv) == 1:
            filepath = sys.argv[0]
            if os.path.isfile(filepath):
                from zmlx.ui.alg import add_code_history
                add_code_history(filepath)
    except Exception as err:
        print(f'Error: {err}')


def __gui_setup():
    from zmlx.ui.settings import get_setup_files
    the_logs = []
    for path in get_setup_files():
        try:
            the_logs.append(f'Exec File: {path}')
            space = {'__name__': '__main__', '__file__': path}
            exec(read_text(path, encoding='utf-8'),
                 space)
        except Exception as err:
            the_logs.append(f'Failed: {err}')
    app_data.put('gui_setup_logs', the_logs)


def __check():
    messages = []

    if not is_pyqt6:
        messages.append(
            '界面将在2026年6月之后停止支持PyQt5，请更新至PyQt6')

    if is_chinese(get_dir()):
        messages.append(
            '程序安装路径包含中文，请务必安装在纯英文路径下. ')

    if len(messages) > 0:
        KEY = 'Init_Warnings_Shown'
        if not app_data.has_tag_today(KEY):
            app_data.add_tag_today(KEY)
            text = ''
            for i in range(len(messages)):
                text += f'{i + 1}. {messages[i]}\n'
            gui.information('注意', text)


def __restore_tabs(filename=None):
    """
    恢复标签状态
    """
    if filename is None:
        filename = app_data.temp('tab_start_code.json')
    if os.path.isfile(filename):
        from zmlx.io.json_ex import read as read_json
        data = read_json(filename)
        try:
            os.remove(filename)
        except Exception as err:
            print(err)
        if isinstance(data, list):
            for text in data:
                try:
                    space = {'gui': gui}
                    exec(text, space)
                except Exception as err:
                    print(err)
    if app_data.getenv('show_readme', default='Yes') != 'No':
        if gui.count_tabs() == 0:
            gui.show_readme()


def __console_kernel(code):
    """
    在控制台线程执行的工作
    """
    # 在尝试调用gui执行的时候，添加代码执行历史
    __add_code_history()

    if app_data.get('run_setup', True):  # 执行额外的配置文件(默认执行)
        __gui_setup()

    if app_data.get('init_check', False):
        __check()

    if app_data.get('restore_tabs', False):  # 尝试载入tab
        __restore_tabs()

    if code is not None:
        return code()  # 执行外部给的代码
    else:
        return None


def __console_done(win, code, close_after_done):
    """
    在控制台线程结束之后执行的操作
    """
    app_data.put('console_result', win.get_console().result)  # 获得结果
    if close_after_done and code is not None:
        win.close()


def __save_tabs(filename=None):
    """
    保存标签状态
    """
    from zmlx.io.json_ex import write as write_json
    tabs = gui.get_tabs()
    data = []
    for idx in range(tabs.count()):
        code = getattr(tabs.widget(idx), 'gui_restore', None)
        if isinstance(code, str):
            data.append(code)
    if filename is None:
        filename = app_data.temp('tab_start_code.json')
    write_json(filename, data)


def __on_close(win):
    # 存储是否显示控制台
    app_data.setenv(
        key='console_visible',
        value='Yes' if win.get_console().isVisible() else 'No'
    )
    settings.save_window_size(win)
    # 尝试保存tab
    if app_data.get('restore_tabs', False):
        __save_tabs()


def execute(code=None, keep_cwd=True, close_after_done=True):
    try:
        app_data.log(f'gui_execute. file={__file__}. argv={sys.argv}')
    except Exception as err:
        print(f'Error: {err}')

    if gui.exists():
        return code() if callable(code) else None

    if not keep_cwd:  # 工作目录
        settings.load_cwd()

    # 启动界面应用程序
    app = QtWidgets.QApplication(sys.argv)
    splash = __make_splash(app)

    # 建立主窗口对象，并进行最基本的数据初始化
    win = MainWindow()
    __on_init(win)

    # 显示主窗口
    win.show()
    if splash is not None:
        splash.finish(win)  # 隐藏启动界面
        splash.deleteLater()

    # 执行显示之后的操作
    __on_show(win)

    # 设置必要的回调函数
    win.on_close = lambda: __on_close(win)

    # 启动核心(但是不阻塞当前线程)
    win.get_console().start_func(
        lambda: __console_kernel(code),
        post_task=lambda: __console_done(win, code, close_after_done)
    )
    win.get_console().start_func(None)  # 清除最后一次调用的信息
    app.exec()
    __on_exit(win)  # 执行最后的清理/恢复操作

    # 返回运行的结果
    return app_data.get('console_result', None)


def get_window():
    window = app_data.get('main_window')
    if window is not None:
        assert isinstance(window, MainWindow)
        return window
    else:
        return None
