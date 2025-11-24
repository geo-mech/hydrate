import datetime
import os
import sys

import zmlx.alg.sys as warnings
from zmlx.alg.fsys import has_permission, samefile, time_string, print_tag
from zmlx.base.zml import lic, core, app_data, read_text, get_dir, is_chinese
from zmlx.ui import settings
from zmlx.ui.alg import open_url, get_last_exec_history, install_package, set_plt_export_dpi, play_images
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import (
    QtCore, QtWidgets, QtMultimedia, QAction, QtGui,
    is_pyqt6, QWebEngineView, QWebEngineSettings)
from zmlx.ui.utils import TaskProc, GuiApi, FileHandler
from zmlx.ui.widget import (
    CodeEdit, Console, TabWidget, ConsoleStateLabel)


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
        get_text = getattr(self, 'get_text', None)
        if callable(get_text):
            text = get_text()
            if isinstance(text, str):
                self.setText(text)


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

        def _do_nothing(fname):
            pass

        def new_empty_file(fname):
            from zmlx.base.zml import make_parent
            with open(make_parent(fname), 'w') as file:
                pass

        for opt in [
            dict(desc='Python文件', exts=['.py'],
                 func=dict(open_file=self.open_code, new_file=_do_nothing)),
            dict(desc='文本文件', exts=['.txt', '.json', '.xml', '.qss'],
                 func=dict(open_file=self.open_text, new_file=new_empty_file)),
            dict(desc='二维裂缝', exts=['.fn2'], func=self.show_fn2),
            dict(desc='图片', exts=['.png', '.jpg'], func=self.open_image),
            dict(desc='PDF文件', exts=['.pdf'], func=self.open_pdf),
        ]:
            self.add_file_handler(**opt)

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
        self.console_state_label = ConsoleStateLabel(self)
        self.statusBar().addPermanentWidget(self.console_state_label)

        def show_text_on_console_state(text):
            if not self.__console.output_widget.isVisible():
                text = text.strip()[:50]
                if len(text) > 0:
                    self.console_state_label.setText(text)

        self.__console.output_widget.sig_add_text.connect(show_text_on_console_state)  # 同时，尝试在控制台状态标签中显示

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

    def closeEvent(self, event):
        if self.__console.is_running():
            reply = QtWidgets.QMessageBox.question(
                self, '退出UI',
                "内核似乎正在运行，确定要退出吗？"
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

        try:
            from zmlx.ui.alg import reg_file_type, edit_in_tab
            for key, func in [('reg_file_type', reg_file_type),
                              ('edit_in_tab', edit_in_tab)]:
                self.__gui_api.add_func(key, func)
                gui.mark_direct(key)  # 直接调用的函数
        except Exception as err:
            print(err)

        for key in ['window']:
            gui.mark_direct(key)

    def __init_actions(self):
        """
        初始化内置的菜单动作
        """
        from zmlx.alg.sys import create_ui_lnk_on_desktop

        def not_running():
            return not self.is_running()

        self.add_action(
            menu='文件', name='set_cwd', icon='open',
            tooltip='设置工作路径 (在进行各种操作前，务必确保工作路径正确)',
            text='工作路径', shortcut='Ctrl+W',
            slot=self.set_cwd_by_dialog,
            on_toolbar=True,
            is_enabled=not_running,
            is_visible=lambda: True
        )

        self.add_action(
            menu='文件', name='open', icon='open',
            tooltip='打开文件', text='打开',
            slot=self.open_file_by_dlg,
            on_toolbar=True, shortcut=QtGui.QKeySequence.StandardKey.Open,
            is_enabled=not_running, is_visible=lambda: True
        )

        self.add_action(
            menu='文件', name='new_file', icon='new',
            text='新建', shortcut=QtGui.QKeySequence.StandardKey.New,
            slot=self.new_file,
            on_toolbar=True,
            is_enabled=not_running,
        )

        self.add_action(
            menu='文件', name='quit', icon='quit',
            text='退出',
            slot=self.close,
        )

        self.add_action(
            menu='文件', name='view_cwd', icon='cwd',
            text='浏览', shortcut='Ctrl+B',
            slot=self.view_cwd
        )

        def import_data():
            widget = self.get_current_widget()
            f = getattr(widget, 'import_data', None)
            if callable(f):
                try:
                    f()
                    self.refresh_action()
                except Exception as e:
                    print(e)

        self.add_action(
            menu='文件', text='导入', name=None, slot=import_data,
            icon='import',
            on_toolbar=True,
            is_visible=lambda: hasattr(self.get_current_widget(), 'import_data') and not self.is_running(),
        )

        def is_enabled():
            widget = self.get_current_widget()
            if hasattr(widget, 'need_save'):
                try:
                    return widget.need_save()
                except Exception as err:
                    print(err)
                    return True
            else:
                return True

        def save_file():
            widget = self.get_current_widget()
            f = getattr(widget, 'save_file', None)
            if callable(f):
                try:
                    f()
                    self.refresh_action()
                except Exception as e:
                    print(e)

        self.add_action(
            menu='文件', text='保存', name=None, slot=save_file,
            icon='save', shortcut='Ctrl+S',
            on_toolbar=True,
            is_enabled=is_enabled,
            is_visible=lambda: hasattr(self.get_current_widget(), 'save_file') and not self.is_running(),
        )

        def export_data():
            widget = self.get_current_widget()
            f = getattr(widget, 'export_data', None)
            if callable(f):
                try:
                    f()
                    self.refresh_action()
                except Exception as e:
                    print(e)

        self.add_action(
            menu='文件', name='export_data', icon='export',
            text='导出', shortcut='Ctrl+Shift+S',
            slot=export_data,
            on_toolbar=True,
            is_visible=lambda: hasattr(self.get_current_widget(), 'export_data') and not self.is_running(),
        )

        self.add_action(
            menu='显示', name='refresh', icon='refresh',
            text='刷新',
            slot=self.refresh
        )

        self.add_action(
            menu='显示', name='memory', icon='variables',
            text='变量',
            slot=self.show_memory
        )

        self.add_action(
            menu='显示', name='timer', icon='clock',
            tooltip='显示cpu耗时统计的结果', text='耗时',
            slot=self.show_timer
        )

        self.add_action(
            menu='显示', name='console', icon='console',
            text='Python控制台(测试)',
            slot=self.show_pg_console
        )

        self.add_action(
            menu='显示', name='cls', icon='clean',
            text='清屏', shortcut='Ctrl+L',
            slot=self.cls
        )

        def console_exec():
            f = getattr(self.get_current_widget(), 'console_exec', None)
            if callable(f):
                f()
            else:
                self.get_console().exec_file(fname=None)

        self.add_action(
            menu='操作', name='console_exec', icon='begin',
            tooltip='运行当前标签页面显示的脚本 (执行当前标签的console_exec函数)',
            text='运行', shortcut='Ctrl+R',
            slot=console_exec,
            on_toolbar=True,
            is_enabled=not_running,
            is_visible=not_running,
        )

        def pause_enabled():
            c = self.get_console()
            if not c.is_running():
                return False
            return not c.get_pause()

        self.add_action(
            menu='操作', name='console_pause',
            icon='pause',
            tooltip='暂停内核的执行 (需要提前在脚本内设置break_point)',
            text='暂停',
            slot=lambda: self.get_console().set_pause(True),
            on_toolbar=True,
            is_enabled=pause_enabled,
        )

        self.add_action(
            menu='操作', name='console_resume',
            icon='begin',
            tooltip=None, text='继续', shortcut='Ctrl+R',
            slot=lambda: self.get_console().set_pause(False),
            on_toolbar=True,
            is_enabled=lambda: self.is_running() and self.get_console().get_pause(),
        )

        self.add_action(
            menu='操作', name='console_stop', icon='stop',
            tooltip='安全地终止内核的执行 (需要提前在脚本内设置break_point)',
            text='停止', shortcut='Ctrl+Q',
            slot=lambda: self.get_console().stop(),
            on_toolbar=True,
            is_enabled=self.is_running
        )

        self.add_action(
            menu='操作', name='console_kill', icon='kill',
            text='强制结束',
            slot=self.kill_thread,
            is_enabled=self.is_running
        )

        self.add_action(
            menu='操作', name='console_hide',
            icon='console',
            tooltip='隐藏主窗口右侧的控制台', text='隐藏', shortcut='Ctrl+H',
            slot=self.hide_console,
            on_toolbar=True,
            is_enabled=lambda: self.get_console().isVisible()
        )

        self.add_action(
            menu='操作', name='console_show',
            icon='console',
            tooltip='显示主窗口右侧的控制台', text='显示', shortcut='Ctrl+H',
            slot=self.show_console,
            on_toolbar=True,
            is_enabled=lambda: not self.get_console().isVisible()
        )

        self.add_action(
            menu='操作', name='console_start_last',
            text='重新执行', shortcut='Ctrl+Shift+R',
            slot=self.get_console().start_last,
            is_enabled=lambda: not self.is_running() and get_last_exec_history() is not None,
        )

        self.add_action(
            menu='操作', name='close_all_tabs',
            icon='close_all',
            text='关闭所有页面',
            slot=self.close_all_tabs,
            is_enabled=lambda: self.count_tabs() > 0,
        )

        self.add_action(
            menu='操作', name='play_images',
            text='播放图片',
            slot=play_images
        )

        self.add_action(
            menu='设置', name='env', icon='set',
            text='系统变量', shortcut='Ctrl+E',
            slot=self.show_env_edit
        )

        self.add_action(
            menu='设置', name='setup_files',
            text='启动文件',
            slot=self.edit_setup_files
        )

        self.add_action(
            menu='设置', name='search', icon='set',
            text='搜索路径',
            slot=self.show_file_finder
        )

        self.add_action(
            menu='设置', name='edit_window_style',
            text='窗口风格',
            slot=lambda: self.open_text(
                app_data.temp('zml_window_style.qss'), '窗口风格')
        )

        self.add_action(
            menu='设置', name='set_plt_export_dpi',
            text='设置plt输出图的DPI',
            slot=set_plt_export_dpi
        )

        self.add_action(
            menu='帮助', name='readme', icon='info',
            text='ReadMe', shortcut='F1',
            slot=self.show_readme,
            on_toolbar=True)

        def about():
            print(lic.desc)
            self.show_about()

        self.add_action(
            menu='帮助', name='about',
            text='关于', shortcut='Ctrl+Shift+A',
            icon='info',
            slot=about,
            is_enabled=not_running,
        )

        self.add_action(
            menu='帮助', name='demo', icon='demo',
            tooltip=None, text='示例',
            slot=self.show_demo,
            on_toolbar=True, is_enabled=None, is_visible=lambda: True
        )

        self.add_action(
            menu='帮助', name='reg', icon='reg',
            text='注册',
            slot=self.show_reg_tool
        )

        self.add_action(
            menu='帮助',
            text='安装Python包',
            slot=install_package,
        )

        self.add_action(
            menu='帮助', name='feedback',
            text='反馈',
            icon='info',
            slot=self.show_feedback,
            is_enabled=not_running,
        )

        self.add_action(
            menu='帮助', name='create_lnk',
            text='创建快捷方式',
            slot=create_ui_lnk_on_desktop,
        )

        self.add_action(
            menu=['帮助', '打开'], name='papers',
            text='已发表文章',
            slot=lambda: open_url(
                url="https://pan.cstcloud.cn/s/5cKaQrdFSHM",
                use_web_engine=False)
        )

        self.add_action(
            menu=['帮助', '打开'], name='new_issue',
            text='新建Issue',
            icon='issues',
            slot=lambda: open_url(
                url='https://gitee.com/geomech/hydrate/issues/new',
                on_top=True,
                caption='新建Issue',
                icon='issues'),
            is_enabled=not_running,
        )

        self.add_action(
            menu=['帮助', '打开'], name='iggcas',
            text='中科院地质地球所',
            icon='iggcas',
            slot=lambda: open_url(
                url='http://www.igg.cas.cn/',
                on_top=True,
                caption='中科院地质地球所主页',
                icon='iggcas'
            ),
            is_enabled=not_running,
        )

        self.add_action(
            menu=['帮助', '打开'], name='homepage',
            text='主页',
            icon='home',
            slot=lambda: open_url(
                url='https://gitee.com/geomech/hydrate',
                on_top=True,
                caption='IGG-Hydrate',
                icon='home'
            ),
            is_enabled=not_running,
        )

        self.add_action(
            menu=['帮助', '显示'],
            text='日历',
            slot=self.show_calendar,
        )

        self.add_action(
            menu='帮助', name='print_tag',
            text='时间标签',
            slot=print_tag
        )

        def print_funcs():
            self.show_string_table(list(gui.list_all()), '命令列表')

        def print_actions():
            names = gui.list_actions()
            names.sort()
            gui.show_string_table(names, 'Action列表')

        self.add_action(
            menu=['帮助', '显示'],
            text='命令列表',
            slot=lambda: self.start_func(print_funcs),
        )

        self.add_action(
            menu=['帮助', '显示'],
            text='Action列表',
            slot=lambda: self.start_func(print_actions),
        )

        def print_gui_setup_logs():
            logs = app_data.get('gui_setup_logs')
            gui.show_string_table(logs, 'gui_setup_logs', 1)

        self.add_action(
            menu=['帮助', '显示'],
            text='Setup日志',
            slot=print_gui_setup_logs,
        )

        def print_sys_folders():
            from zmlx.alg.sys import listdir
            paths = listdir(app_data.get_paths())
            gui.show_string_table(paths, '系统路径', 1)

        self.add_action(
            menu=['帮助', '显示'],
            text='系统路径',
            slot=print_sys_folders,
        )

        def open_cwd():
            print(f'当前工作路径：\n{os.getcwd()}\n')
            os.startfile(os.getcwd())

        self.add_action(
            menu=['帮助', '打开'], name='open_cwd',
            text='工作路径',
            slot=open_cwd
        )

        self.add_action(
            menu=['帮助', '打开'], name='open_app_data',
            text='AppData',
            slot=lambda: os.startfile(app_data.root()),
            is_enabled=lambda: lic.is_admin
        )

    def list_member_functions(self):
        """
        列出所有成员函数（排除私有方法）
        """
        import inspect
        return [name for name, _ in inspect.getmembers(self.__class__)
                if inspect.isfunction(getattr(self.__class__, name))
                and not name.startswith('__')]

    def parse_value(self, value):
        if callable(value):  # 直接是一个函数，直接运行
            return value()

        if isinstance(value, dict):  # 字典，则尝试作为带有参数的函数
            on_window = value.get('on_window')
            if callable(on_window):
                return on_window(self)

            func = value.get('func')
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

    def add_action(self, menu=None, text=None, name=None, slot=None,
                   icon=None, tooltip=None, shortcut=None,
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
            if isinstance(text, str):
                action.setText(settings.get_text(text))
            else:
                assert callable(text)
                setattr(action, 'get_text', text)
        else:
            action.setText(name)

        if shortcut is not None:
            if isinstance(shortcut, str):
                action.setShortcut(QtGui.QKeySequence(shortcut))
            else:
                action.setShortcut(shortcut)

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

    def list_actions(self):
        names = []
        for action in self.findChildren(QAction):
            name = action.objectName()
            if isinstance(name, str):
                if len(name) > 0:
                    names.append(name)
        return names

    def trigger(self, name):
        """
        出发给定的Action
        """
        action = self.get_action(name)
        if hasattr(action, 'trigger'):
            action.trigger()

    def count_tabs(self):
        """
        返回标签的数量
        """
        return self.__tab_widget.count()

    def close_all_tabs(self):
        """
        关闭所有的标签
        """
        self.__tab_widget.close_all_tabs()

    def close_tab_object(self, widget):
        """
        关闭给定对象的标签页面
        """
        return self.__tab_widget.close_tab_object(widget)

    def get_tab_caption(self, index):
        """
        返回给定位置tab的Caption
        """
        return self.__tab_widget.tabText(index)

    def set_tab_caption(self, index, caption):
        """
        设置tab的文本
        """
        self.__tab_widget.setTabText(index, caption)

    def exec_tab_func(self, name):
        widget = self.get_current_widget()
        if hasattr(widget, name):
            f = getattr(widget, name)
            f()

    def get_tabs(self):
        return self.__tab_widget

    def cls(self):
        self.__console.output_widget.clear()

    def show_status(self, *args, **kwargs):
        self.statusBar().showMessage(*args, **kwargs)

    def console_state(self, text):
        """
        在控制台状态标签中显示文本，
        Args:
            text: 要显示的文本
        """
        if not isinstance(text, str):
            text = str(text)
        if len(text) > 20:
            text = text[:20] + '...'
        self.console_state_label.setText(text)

    def set_title(self, title):
        self.__title = title
        self.refresh()

    @staticmethod
    def toolbar_warning(text=None):
        if isinstance(text, str):
            if len(text) > 0:
                try:
                    gui.add_message(text, color='red')  # 警告
                except:
                    print(text)

    def get_console(self):
        return self.__console

    def is_running(self):
        return self.__console.is_running()

    def click_pause(self):
        """
        在界面上点击暂停按钮
        """
        if self.is_running():
            self.__console.set_pause(True)

    def exec_file(self, filename):
        self.__console.exec_file(filename)

    def start_func(self, *args, **kwargs):
        """
        在控制台执行代码
        """
        self.__console.start_func(*args, **kwargs)

    def exec_current(self):
        widget = self.__tab_widget.currentWidget()
        if isinstance(widget, CodeEdit):
            widget.save()
            self.__console.exec_file(widget.get_fname())
        else:
            self.__console.exec_file()

    def kill_thread(self):
        self.__console.kill_thread()

    def refresh_action(self, name=None):
        """
        刷新给定的Action或者所有的Action
        """
        if name is None:
            for action in self.findChildren(QAction):
                update_view = getattr(action, 'update_view', None)
                if callable(update_view):
                    try:
                        update_view()
                    except Exception as err:
                        print(err)
        else:
            action = self.get_action(name=name, create_empty=False)
            update_view = getattr(action, 'update_view', None)
            if callable(update_view):
                try:
                    update_view()
                except Exception as err:
                    print(err)

    def refresh(self):
        """
        尝试刷新标题以及当前的页面
        """
        if self.__title is not None:
            self.setWindowTitle(f'{self.__title}')
        else:
            self.setWindowTitle(f'WorkDir: {os.getcwd()}')

        try:  # 尝试刷新当前的页面（在定义refresh函数的情况下）
            current = self.get_current_widget()
            if hasattr(current, 'refresh'):
                self.__task_proc.add(lambda: current.refresh())
        except Exception as err:
            print(f'Error: {err}')

        self.refresh_action()

        # 调用刷新
        self.__console.refresh_view()

    def get_widget(
            self, the_type, caption=None, on_top=None, init=None,
            type_kw=None, oper=None, icon=None, caption_color=None,
            set_parent=False, tooltip=None, is_ok=None):
        """
        返回一个控件，其中type为类型，caption为标题，现有的控件，只有类型和标题都满足，才会返回，否则就
        创建新控件。
        Args:
            the_type: 控件的类型
            caption: 标题
            on_top: 是否将控件设置为当前的控件
            init: 首次生成控件，在显示之前所做的操作
            type_kw: 用于创建控件的关键字参数
            oper: 每次调用都会执行，且在控件显示之后执行
            icon: 图标
            caption_color: 标题的颜色
            set_parent: 是否将控件的父对象设置为当前的窗口
            tooltip: 工具提示
            is_ok: 一个函数，用于检查控件对象

        Returns:
            符合条件的Widget对象，否则返回None
        """
        if caption is None:
            caption = 'untitled'
        widget = self.__tab_widget.find_widget(the_type=the_type, text=caption, is_ok=is_ok)
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
            if tooltip is not None:
                self.__tab_widget.setTabToolTip(index, tooltip)
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

    def get_figure_widget(self, **kwargs):
        """
        返回一个用以 matplotlib 绘图的控件
        """
        from zmlx.ui.widget.plt import MatplotWidget
        kwargs.setdefault('icon', 'matplotlib')
        return self.get_widget(the_type=MatplotWidget, **kwargs)

    def plot(
            self, kernel, *args, fname=None, dpi=None,
            caption=None, on_top=None, icon=None,
            clear=None,
            tight_layout=None,
            suptitle=None,
            **kwargs):
        """
        调用matplotlib执行绘图操作 注意，此函数会创建或者返回一个标签，并默认清除标签的绘图，返回使用回调函数
        在figure上绘图。
        Args:
            kernel: 绘图的回调函数，函数的原型为：
                def kernel(figure, *args, **kwargs):
                    ...
            fname: 输出的文件名
            dpi: 输出的分辨率
            *args: 传递给kernel函数的参数
            **kwargs: 传递给kernel函数的关键字参数
            caption: 窗口的标题
            on_top: 是否置顶
            icon: 窗口的图标
            clear: 是否清除之前的内容 (特别注意，默认是要清除之前的内容的，因此，如果要多个视图的时候，就不要使用clear)
            tight_layout: 是否自动调整子图参数，以防止重叠
            suptitle: 图表的标题

        Returns:
            None
        """
        if clear is None:  # 默认清除
            clear = True
        try:
            widget = self.get_figure_widget(caption=caption, on_top=on_top, icon=icon)

            def on_figure(figure):
                if clear:  # 清除
                    figure.clear()
                if callable(kernel):
                    try:
                        kernel(figure, *args, **kwargs)  # 这里，并不会传入clear参数
                    except Exception as kernel_err:
                        print(kernel_err)
                if isinstance(suptitle, str):
                    figure.suptitle(suptitle)
                if tight_layout:
                    figure.tight_layout()

            widget.plot_on_figure(on_figure=on_figure)
            if fname is not None:
                if dpi is None:
                    dpi = 300
                widget.savefig(fname=fname, dpi=dpi)

            return widget.figure  # 返回Figure对象，后续进一步处理
        except Exception as err:
            warnings.warn(f'meet exception <{err}> when run <{kernel}>')
            return None

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

    def view_cwd(self):
        from zmlx.ui.widget.base import CwdView

        def oper(w):
            w.refresh()
            w.gui_restore = f"""gui.view_cwd()"""  # 用于重启

        self.get_widget(
            the_type=CwdView, caption='浏览', on_top=True,
            oper=oper,
            icon='cwd')

    def progress(
            self, label=None, val_range=None, value=None, visible=None,
            duration=None):
        """
        显示进度
        """
        if duration is not None:
            warnings.warn('duration will not be used in future')
        return self.__console.output_widget.progress(
            label=label, val_range=val_range, value=value, visible=visible)

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
                    the_type=CodeEdit, caption=caption, on_top=True, oper=oper, icon='python',
                    tooltip='代码编辑窗口，点击工具栏的运行按钮可以执行'
                )
                if app_data.getenv('show_info_after_code_open',
                                   default='') != 'No':
                    print(
                        f'文件已打开: \n\t{fname}\n\n请点击工具栏上的<运行>按钮以运行!\n\n')

    def open_text(self, fname, caption=None):
        from zmlx.ui.widget.base import TextFileEdit
        if not isinstance(fname, str):
            return
        if len(fname) > 0:
            def oper(x: TextFileEdit):
                x.set_fname(fname)
                kwds = dict(fname=fname, caption=caption)
                x.gui_restore = f"""gui.open_text(**{kwds})"""  # 用于重启

            for i in range(self.__tab_widget.count()):
                widget = self.__tab_widget.widget(i)
                if isinstance(widget, TextFileEdit):
                    if samefile(fname, widget.get_fname()):
                        self.__tab_widget.setCurrentWidget(widget)
                        oper(widget)
                        return

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
            filter='Python File (*.py)')
        self.open_code(fname)

    def new_file(self):
        return self.__file_handler.new_file_by_dlg(
            folder=os.getcwd())

    def add_file_handler(self, desc, exts, func):
        if callable(func):
            open_file = func
            new_file = None
        else:
            open_file = func.get('open_file', None)
            new_file = func.get('new_file', None)
        return self.__file_handler.add(
            desc=desc, exts=exts, open_file=open_file, new_file=new_file)

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
        """
        返回当前的标签对象
        """
        return self.__tab_widget.currentWidget()

    def get_current_tab_index(self):
        """
        返回当前标签的序号
        """
        return self.__tab_widget.currentIndex()

    def get_output_widget(self):
        return self.__console.output_widget

    def add_task(self, task):
        self.__task_proc.add(task)

    def get_gui_api(self):
        return self.__gui_api

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

    def show_demo(self):
        from zmlx.ui.widget import DemoView

        def oper(w):
            w.refresh()
            w.gui_restore = f"""gui.show_demo()"""

        self.get_widget(the_type=DemoView, caption='示例', on_top=True,
                        oper=oper, icon='demo',
                        tooltip='内置在模型中的示例。单击条目可以打开，然后，请点击工具条的运行按钮来执行')

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

        self.get_widget(
            the_type=PgConsole, caption='Python控制台', on_top=True,
            icon='console', oper=oper)

    def show_file_finder(self):
        from zmlx.ui.widget import AppPathEdit
        def oper(w):
            w.gui_restore = f"""gui.show_file_finder()"""

        self.get_widget(
            the_type=AppPathEdit, caption='搜索路径',
            on_top=True,
            icon='set', oper=oper)

    def show_env_edit(self):
        from zmlx.ui.widget import EnvEdit

        def oper(w):
            w.gui_restore = f"""gui.show_env_edit()"""

        self.get_widget(
            the_type=EnvEdit, caption='设置Env', on_top=True,
            icon='set', oper=oper,
            type_kw=dict(items=settings.get_env_items())
        )

    def show_calendar(self):
        def oper(w):
            w.gui_restore = f"""gui.show_calendar()"""

        self.get_widget(
            the_type=QtWidgets.QCalendarWidget,
            caption='日历',
            on_top=True,
            oper=oper
        )

    def show_string_table(self, data, caption=None, data_columns=3):
        from zmlx.ui.widget.string_table import StringTable
        opts = dict(data=data, caption=caption, data_columns=data_columns)

        def oper(w):
            w.gui_restore = f"""gui.show_string_table(**{opts})"""
            w.set_data(data)

        widget = self.get_widget(
            StringTable, caption='文本表格' if caption is None else caption,
            type_kw=dict(data_columns=data_columns),
            set_parent=True, oper=oper)

        return widget

    def edit_setup_files(self):
        from zmlx.ui.widget import SetupFileEdit

        def oper(w):
            w.gui_restore = f"""gui.edit_setup_files()"""

        self.get_widget(
            the_type=SetupFileEdit, caption='启动文件',
            on_top=True,
            icon='set', oper=oper)

    def show_readme(self):
        from zmlx.ui.widget import ReadMeBrowser

        def oper(w):
            w.gui_restore = f"""gui.show_readme()"""

        self.get_widget(
            the_type=ReadMeBrowser, caption='ReadMe', on_top=True,
            icon='info', oper=oper,
            tooltip='显示ReadMe信息，与IGG-Hydrate网站首页的ReadMe保持一致')

    def show_reg_tool(self):
        from zmlx.ui.widget import RegTool

        def oper(w):
            w.gui_restore = f"""gui.show_reg_tool()"""

        self.get_widget(
            the_type=RegTool, caption='注册', on_top=True,
            icon='reg', oper=oper)

    def show_feedback(self):
        from zmlx.ui.widget import FeedbackTool

        def oper(w):
            w.gui_restore = f"""gui.show_feedback()"""

        self.get_widget(
            the_type=FeedbackTool, caption='反馈', on_top=True,
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

    def set_console_visible(self, visible: bool):
        """
        设置控制台是否可见
        """
        self.get_console().setVisible(visible)
        self.refresh()  # 刷新窗口

    def hide_console(self):
        """
        隐藏控制台
        """
        self.set_console_visible(False)

    def show_console(self):
        """
        显示控制台
        """
        self.set_console_visible(True)


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
        return splash
    else:
        return None


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
    """
    设置GUI的额外的选项(会在线程里面执行)
    """
    from zmlx.ui import setup_files
    the_logs = []
    for path in setup_files.get_files():
        try:
            folder = os.path.dirname(os.path.dirname(path))
            if folder not in sys.path:
                sys.path.append(folder)  # 确保包含zml_gui_setup.py的包能够被正确import

            the_logs.append(f'Exec File: {path}')
            space = {'__name__': '__main__', '__file__': path}
            exec(read_text(path, encoding='utf-8'),
                 space)
        except Exception as err:
            the_logs.append(f'Failed: {err}')
            gui.add_message(f'path = {path}, error = {err}')
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

    try:
        from zmlx.ui.widget.message import setup_ui
        setup_ui()
    except Exception as err:
        print(f'Error when setup message: {err}')

    try:
        from zmlx.ui.widget.editors import setup_ui
        setup_ui()
    except Exception as err:
        print(f'Error when setup editors: {err}')

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
    if isinstance(splash, QtWidgets.QSplashScreen):
        splash.finish(win)  # 隐藏启动界面
        splash.deleteLater()

    # 执行显示之后的操作
    __on_show(win)

    # 设置必要的回调函数
    win.on_close = lambda: __on_close(win)

    # 启动核心(但是不阻塞当前线程)
    win.get_console().start_func(
        lambda: __console_kernel(code),  # 这里，会启动包含code在内的其它一些在初始化的代码
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
