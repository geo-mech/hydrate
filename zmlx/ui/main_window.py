import datetime
import os.path
import sys

import zml
import zmlx.alg.sys as warnings
from zml import is_chinese, lic, core
from zmlx.alg.fsys import has_permission, samefile, show_fileinfo, time_string
from zmlx.ui.actions import Action
from zmlx.ui.alg import show_seepage
from zmlx.ui.cfg import *
from zmlx.ui.gui_api import GuiApi
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtWidgets, QtMultimedia
from zmlx.ui.task_proc import TaskProc
from zmlx.ui.widget.code_edit import CodeEdit
from zmlx.ui.widget.console import ConsoleWidget
from zmlx.ui.widget.my_label import Label
from zmlx.ui.widget.tab_widget import TabWidget
from zmlx.ui.widget.version_label import VersionLabel
from zmlx.ui.window_functions import show_txt


class MainWindow(QtWidgets.QMainWindow):
    sig_cwd_changed = QtCore.pyqtSignal(str)
    sig_do_task = QtCore.pyqtSignal()
    sig_play_sound = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowIcon(load_icon('app'))
        self.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.__task_proc = TaskProc(self)

        self.__file_processors = {
            '.py': [self.open_code, 'Python File To Execute'],
            '.fn2': [self.show_fn2, 'Fracture Network 2D'],
            '.seepage': [show_seepage, 'Seepage Model File'],
            '.txt': [show_txt, 'Text file'],
            '.json': [show_txt, 'Json file'],
            '.xml': [show_txt, 'Xml file'],
            '.qss': [show_txt, 'QSS file'],
            '.png': [self.open_image, 'Png file'],
            '.jpg': [self.open_image, 'Jpg file'],
            '.pdf': [self.open_pdf, 'PDF file']
        }

        widget = QtWidgets.QWidget(self)
        h_layout = QtWidgets.QVBoxLayout(widget)
        splitter = QtWidgets.QSplitter(widget)
        splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.__tab_widget = TabWidget(splitter)
        self.__tab_widget.currentChanged.connect(self.refresh)
        self.__console = ConsoleWidget(splitter)
        self.__gui_api = GuiApi(widget,
                                self.__console.get_break_point(),
                                self.__console.get_flag_exit())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        h_layout.addWidget(splitter)
        self.setCentralWidget(widget)

        self.__menu_bar = QtWidgets.QMenuBar(self)
        self.setMenuBar(self.__menu_bar)
        self.__actions = {}
        self.__menus = {}
        self.__toolbars = {}
        self.__title = None
        if True:
            from zmlx.ui.actions import add_std_actions, add_zml_actions
            add_std_actions(self)
            add_zml_actions(self)
        self.__init_gui_api()

        self.sig_cwd_changed.connect(self.refresh)
        self.sig_cwd_changed.connect(self.view_cwd)
        self.sig_cwd_changed.connect(self.__console.restore_code)

        self.__console.sig_refresh.connect(self.refresh)

        # 尝试关闭进度条，从而使得进度条总是临时显示一下.
        self.__timer_close_progress = QtCore.QTimer(self)
        self.__timer_close_progress.timeout.connect(
            lambda: self.progress(visible=False))
        self.__timer_close_progress.start(5000)

        self.__status_bar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.__status_bar)
        self.__progress_label = Label()
        self.__progress_bar = QtWidgets.QProgressBar()
        self.__status_bar.addPermanentWidget(self.__progress_label)
        self.__status_bar.addPermanentWidget(self.__progress_bar)
        self.__status_bar.addPermanentWidget(VersionLabel())
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
            filename = find_icon_file('welcome')
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
        self.__gui_api.add_func('add_action', self.add_action)
        self.__gui_api.add_func('cls', self.cls)
        self.__gui_api.add_func('close', self.close)
        self.__gui_api.add_func('close_all_tabs',
                                self.__tab_widget.close_all_tabs)
        self.__gui_api.add_func('exec_current', self.exec_current)
        self.__gui_api.add_func('get_widget', self.get_widget)
        self.__gui_api.add_func('get_figure_widget', self.get_figure_widget)
        self.__gui_api.add_func('get_current_widget', self.get_current_widget)
        self.__gui_api.add_func('is_running', self.is_running)
        self.__gui_api.add_func('kill_thread', self.kill_thread)
        self.__gui_api.add_func('plot', self.plot)
        self.__gui_api.add_func('progress', self.progress)
        self.__gui_api.add_func('play_sound', self.play_sound)
        self.__gui_api.add_func('refresh', self.refresh)
        self.__gui_api.add_func('open_file', self.open_file)
        self.__gui_api.add_func('open_file_by_dlg', self.open_file_by_dlg)
        self.__gui_api.add_func('open_text', self.open_text)
        self.__gui_api.add_func('open_image', self.open_image)
        self.__gui_api.add_func('open_pdf', self.open_pdf)
        self.__gui_api.add_func('open_code', self.open_code)
        self.__gui_api.add_func('show_next', self.__tab_widget.show_next)
        self.__gui_api.add_func('show_prev', self.__tab_widget.show_prev)
        self.__gui_api.add_func('show_fn2', self.show_fn2)
        self.__gui_api.add_func('show_code_history', self.show_code_history)
        self.__gui_api.add_func('set_cwd', self.set_cwd)
        self.__gui_api.add_func('set_cwd_by_dialog', self.set_cwd_by_dialog)
        self.__gui_api.add_func('status', self.cmd_status)
        self.__gui_api.add_func('start_func', self.start_func)
        self.__gui_api.add_func('show_about', self.show_about)
        self.__gui_api.add_func('toolbar_warning', self.toolbar_warning)
        self.__gui_api.add_func('tab_count', self.count_tabs)
        self.__gui_api.add_func('title', self.cmd_title)
        self.__gui_api.add_func('trigger', self.trigger)
        self.__gui_api.add_func('view_cwd', self.view_cwd)
        self.__gui_api.add_func('window', lambda: self)
        self.__gui_api.add_func('is_maximized', lambda: self.isMaximized())
        self.__gui_api.add_func('show_maximized', lambda: self.showMaximized())
        self.__gui_api.add_func('resize', lambda *args: self.resize(*args))
        self.__gui_api.add_func('device_pixel_ratio', self.devicePixelRatioF)
        self.__gui_api.add_func('tab_details', self.tab_details)


    def add_action(self, menu=None, name=None, icon=None,
                   tooltip=None, text=None, slot=None,
                   on_toolbar=None,
                   is_enabled=None,
                   is_visible=None
                   ):
        """
        添加一个Action. 这是一个新的版本，将替代后续的直接基于File的ActionX的创建方法，
        并且将支持动态地创建Action。
        Since 2026-6-9.
        """
        if name in self.__actions:
            warnings.warn(
                f'The action already exists: {name}',
                UserWarning, stacklevel=2)
            name = None

        if name is None:
            index = 0
            while f'unnamed_{index}' in self.__actions:
                index += 1
            name = f'unnamed_{index}'

        action = Action(self)

        if callable(is_enabled):  # 作为一个函数，动态地判断是否可用
            action.is_enabled = is_enabled

        if callable(is_visible):  # 作为一个函数，动态地判断是否可见
            action.is_visible = is_visible

        action.setIcon(load_icon(
            icon if icon is not None else 'python'))

        if tooltip is not None:
            action.setToolTip(get_text(tooltip))

        if text is not None:
            action.setText(get_text(text))
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
            self.get_toolbar(menu).addAction(action)

        self.get_menu(menu).addAction(action)

        # 添加Action
        self.__actions[name] = action

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
        assert name is not None, f'Error: name is None when get_menu'
        menu = self.__menus.get(name)
        if menu is not None:
            return menu
        else:
            menu = QtWidgets.QMenu(self.__menu_bar)
            menu.setTitle(get_text(name))
            self.__menu_bar.addAction(menu.menuAction())
            self.__menus[name] = menu
            return menu

    def get_toolbar(self, name):
        toolbar = self.__toolbars.get(name)
        if toolbar is not None:
            return toolbar
        else:
            toolbar = self.addToolBar(name)
            self.__toolbars[name] = toolbar
            return toolbar

    def list_actions(self):
        return list(self.__actions.keys())

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
                zml.log(text)
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

        for _, ac in self.__actions.items():
            ac.update_view()

        # 调用刷新
        self.__console.refresh_buttons()

    def closeEvent(self, event):
        if self.__console.is_running():
            reply = QtWidgets.QMessageBox.question(
                self, '退出HfUI',
                "内核似乎正在运行，确定要退出吗？",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                event.ignore()
                return

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
                self.__tab_widget.setTabIcon(index, load_icon(icon))
            self.__tab_widget.setCurrentWidget(widget)
            if caption_color is not None:
                self.__tab_widget.tabBar().setTabTextColor(index, QtGui.QColor(
                    caption_color))
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
            widget.del_all_axes()
        return widget

    def show_fn2(self, filepath, **kwargs):
        warnings.warn('gui.show_fn2 will be removed after 2026-3-5, '
                      'please use zmlx.plt.show_fn2 instead',
                      DeprecationWarning, stacklevel=2)
        from zmlx.ui.widget.fn2_widget import Fn2Widget
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

    def cmd_status(self, *args, **kwargs):
        self.__status_bar.showMessage(*args, **kwargs)

    def trigger(self, name):
        action = self.get_action(name)
        assert action is not None, f'Error: action <{name}> not found'
        action.trigger()

    def get_action(self, name):
        """返回给定name的菜单action"""
        action = self.__actions.get(name, None)
        if action is None:
            action = self.__actions.get(name + '.py', None)
        return action

    def cmd_title(self, title):
        self.__title = title
        self.refresh()

    def view_cwd(self):
        from zmlx.ui.widget.cwd_viewer import CwdViewer
        self.get_widget(the_type=CwdViewer, caption='文件', on_top=True,
                        oper=lambda w: w.refresh(), icon='cwd')

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
                self.get_widget(the_type=CodeEdit,
                                caption=os.path.basename(
                                    fname) if caption is None else caption,
                                on_top=True,
                                oper=lambda x: x.open(fname), icon='python')
                print(
                    f'文件已打开: \n\t{fname}\n\n请点击工具栏上的<运行>按钮以运行!\n\n')

    def open_text(self, fname, caption=None):
        from zmlx.ui.widget.text import TextEdit
        if not isinstance(fname, str):
            return
        if len(fname) > 0:
            for i in range(self.__tab_widget.count()):
                widget = self.__tab_widget.widget(i)
                if isinstance(widget, TextEdit):
                    if samefile(fname, widget.get_fname()):
                        self.__tab_widget.setCurrentWidget(widget)
                        return
            self.get_widget(the_type=TextEdit,
                            caption=os.path.basename(
                                fname) if caption is None else caption,
                            on_top=True,
                            oper=lambda x: x.set_fname(fname))

    def open_image(self, fname, caption=None, on_top=True):
        """
        打开一个图片
        """
        if isinstance(fname, str):
            if os.path.isfile(fname):
                from zmlx.ui.widget.image_widget import ImageViewer
                self.get_widget(the_type=ImageViewer, caption=os.path.basename(
                    fname) if caption is None else caption,
                                on_top=on_top,
                                oper=lambda x: x.set_image(fname))

    def open_pdf(self, fname, caption=None, on_top=True):
        """
        打开一个pdf
        """
        if isinstance(fname, str):
            if os.path.isfile(fname):
                from zmlx.ui.widget.pdf import PDFViewer
                self.get_widget(the_type=PDFViewer, caption=os.path.basename(
                    fname) if caption is None else caption,
                                on_top=on_top,
                                oper=lambda x: x.load_pdf(fname))

    def exec_current(self):
        widget = self.__tab_widget.currentWidget()
        if isinstance(widget, CodeEdit):
            widget.save()
            self.__console.exec_file(widget.get_fname())
        else:
            self.__console.exec_file()

    def open_file(self, filepath):
        if not isinstance(filepath, str):
            return None

        if not os.path.isfile(filepath):
            if os.path.isdir(filepath):
                self.set_cwd(filepath)
            return None

        ext = os.path.splitext(filepath)[-1]
        if ext is None:
            QtWidgets.QMessageBox.warning(self, '警告',
                                          f'扩展名不存在: {filepath}')
            return None

        assert isinstance(ext, str)
        ext = ext.lower()

        proc = self.__file_processors.get(ext)
        if proc is None:
            if os.path.isfile(filepath):
                show_fileinfo(filepath)
            return None
        try:
            assert len(proc) == 2
            func, desc = proc
            return func(filepath)
        except Exception as err:
            print(f'Error: filepath = {filepath} \nmessage = {err}')
            return None

    def open_file_by_dlg(self, folder=None):
        temp_1 = ''
        for ext, proc in self.__file_processors.items():
            assert len(proc) == 2
            func, desc = proc
            temp_1 = f'{temp_1}{desc} (*{ext});; '

        if folder is None:
            folder = ''

        def get_open_file_name(*args, **kwargs):
            fpath, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                             *get_text(args),
                                                             **get_text(kwargs))
            return fpath

        filepath = get_open_file_name('please choose the file to open',
                                      folder, f'All File(*.*);;{temp_1}')
        if os.path.isfile(filepath):
            self.open_file(filepath)

    def set_cwd(self, folder):
        if isinstance(folder, str):
            if os.path.isdir(folder):
                if has_permission(folder):
                    try:
                        os.chdir(folder)
                        save_cwd()
                        self.sig_cwd_changed.emit(os.getcwd())
                    except Exception as err:
                        print(f'Error: {err}')

    def set_cwd_by_dialog(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, get_text(
            '请选择工程文件夹'), os.getcwd())
        self.set_cwd(folder)

    def get_current_widget(self):
        return self.__tab_widget.currentWidget()

    def exec_file(self, filename):
        self.__console.exec_file(filename)

    def start_func(self, code):
        """
        在控制台执行代码
        """
        self.__console.start_func(code)

    def get_workspace(self):
        return self.__console.workspace

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
        from zmlx.ui.widget.about_widget import About
        self.check_license()
        self.get_widget(
            the_type=About, caption='关于', on_top=True,
            icon='info', type_kw=dict(lic_desc=lic.desc)
        )

    def play_sound(self, filename):
        """
        播放声音
        """
        if isinstance(filename, str):
            if not os.path.isfile(filename):
                filename = find_sound(filename)
                if filename is None:
                    return
            if os.path.isfile(filename):
                self.sig_play_sound.emit(filename)

    def tab_details(self):
        from zmlx.ui.widget.tab_details import TabWp, TabDetails
        self.get_widget(the_type=TabDetails, caption='标签列表', on_top=True,
                        type_kw={'obj': TabWp(self.__tab_widget)})

    def show_code_history(self, folder, caption=None):
        from zmlx.ui.widget.code_history_viewer import CodeHistoryViewer
        if not isinstance(folder, str):
            return
        if os.path.isdir(folder):
            self.get_widget(
                the_type=CodeHistoryViewer,
                caption=os.path.basename(
                    folder) if caption is None else caption,
                on_top=True,
                oper=lambda widget: widget.set_folder(folder=folder),
                icon='python'
            )


class MySplashScreen(QtWidgets.QSplashScreen):
    def mousePressEvent(self, event):
        pass


def save_tab_start_code(filename, window: MainWindow):
    data = []
    tabs = window.get_tabs()
    for idx in range(tabs.count()):
        widget = tabs.widget(idx)
        if hasattr(widget, 'get_start_code'):
            try:
                code = widget.get_start_code()
                if isinstance(code, str):
                    data.append(code)
            except:
                pass

    from zmlx.io.json_ex import write
    write(filename, data)


def execute(code=None, keep_cwd=True, close_after_done=True, run_setup=True):
    try:
        app_data.log(f'gui_execute. file={__file__}')
    except Exception as err:
        print(f'Error: {err}')

    if gui.exists():
        if code is not None:
            return code()
        else:
            return None

    if not keep_cwd:
        load_cwd()

    app = QtWidgets.QApplication(sys.argv)

    splash_fig = load_pixmap('splash')
    if splash_fig is not None and app_data.getenv('disable_splash',
                                                  default='No',
                                                  ignore_empty=True) != 'Yes':
        splash = MySplashScreen()
        try:
            rect = get_current_screen_geometry(splash)
            splash_fig = splash_fig.scaled(round(rect.width() * 0.3),
                                           round(rect.height() * 0.3),
                                           QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        except Exception as err:
            print(f'Error: {err}')
        splash.setPixmap(splash_fig)
        splash.show()
        app.processEvents()  # 处理主进程事件
    else:
        splash = None

    win = MainWindow()

    try:  # 在尝试调用gui执行的时候，添加代码执行历史
        if len(sys.argv) == 1:
            filepath = sys.argv[0]
            if os.path.isfile(filepath):
                from zmlx.ui.alg import add_code_history
                add_code_history(filepath)
    except:
        pass

    def f1():
        try:
            if app_data.getenv(key='restore_console_output', default='Yes',
                               ignore_empty=True) != 'No':
                from zmlx.alg.fsys import get_latest_file, get_size_mb
                filename = get_latest_file(app_data.root('output_history'))
                if filename is not None:
                    if 0 < get_size_mb(filename) < 0.5:
                        win.get_output_widget().load_text(filename)
        except Exception as Err:
            print(f'Error: {Err}')

        app_data.space['main_window'] = win
        gui.push(win.get_gui_api())
        print(f'Push Gui: {win.get_gui_api()}')
        sys.stdout = win.get_output_widget()
        sys.stderr = win.get_output_widget()

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        print(f'====== {now} ====== \n')

        try:
            if app_data.getenv(key='load_window_style', default='Yes',
                               ignore_empty=True) != 'No':
                text = load(key='zml_window_style.qss', default='',
                            encoding='utf-8')
                if len(text) > 0:
                    win.setStyleSheet(text)
        except Exception as styleErr:
            print(f'Error: {styleErr}')

    def f2():
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        print('Pop Gui')
        gui.pop()
        app_data.space['main_window'] = None
        win.get_output_widget().save_text(
            app_data.root('output_history', f'{time_string()}.txt'))  # 保存输出历史

    f1()

    def my_exception_hook(the_type, value, tb):
        message = f"""Exception Type: {the_type}
Message : {value}
Object : {tb} We are very sorry for this exception. Please check your data according to the above message. If it's 
still unresolved, please contact the author (email: 'zhangzhaobin@mail.iggcas.ac.cn'), Thank you!"""
        print(message)

    sys.excepthook = my_exception_hook
    win.show()

    if splash is not None:
        splash.finish(win)  # 隐藏启动界面
        splash.deleteLater()

    # 必须在窗口正式显示之后，否则此函数可能会出错
    load_window_size(win)

    if run_setup:  # 执行额外的配置文件
        files_data = app_data.getenv(
            key='zml_gui_setup_files',
            encoding='utf-8',
            default=''
        )
        if files_data:
            files = [f.strip() for f in files_data.split(';') if f.strip()]
        else:
            files = []

        all_files = []
        for path in files + find_all('zml_gui_setup.py'):
            full_path = os.path.abspath(path)
            if full_path not in all_files:
                all_files.append(full_path)

        for path in all_files:
            try:
                print(f'Exec File: {path}')
                space = {'__name__': '__main__', '__file__': path}
                exec(read_text(path, encoding='utf-8'),
                     space)
                setup = space.get('zml_gui_setup')
                if callable(setup):
                    setup(win)
                else:
                    print(f'zml_gui_setup is not callable: {path}')
            except Exception as e2:
                print(f'Failed: {e2}')

    def setup():
        """
        在程序界面启动之后执行的设置
        """
        if is_chinese(zml.get_dir()):
            win.toolbar_warning('提醒：请务必将程序安装在纯英文路径下')

    results = []
    if close_after_done and code is not None:
        win.get_console().sig_kernel_done.connect(win.close)
    win.get_console().sig_kernel_done.connect(
        lambda: results.append(win.get_console().result))
    if code is not None:
        def codex():
            win.get_console().time_beg = None  # 对于外部的这种调用，不显示cpu耗时
            setup()
            return code()

        win.get_console().start_func(codex)
    else:
        win.get_console().start_func(setup)

    app.exec()

    save_window_size(win)
    f2()

    if hasattr(win, 'tabs_should_be_saved'):
        save_tab_start_code(app_data.temp('tab_start_code.json'), win)
    if len(results) > 0:
        return results[0]
    else:
        return None


def get_window():
    window = app_data.get('main_window')
    if window is not None:
        assert isinstance(window, MainWindow)
        return window
    else:
        return None


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
