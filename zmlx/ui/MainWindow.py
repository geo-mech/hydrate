import os.path
import sys
import warnings

import zml
from zmlx.alg.is_chinese import is_chinese
from zmlx.filesys.has_permission import has_permission
from zmlx.filesys.samefile import samefile
from zmlx.filesys.show_fileinfo import show_fileinfo
from zmlx.ui.ActionX import ActionX, QAction
from zmlx.ui.CodeEdit import CodeEdit
from zmlx.ui.Config import *
from zmlx.ui.ConsoleWidget import ConsoleWidget
from zmlx.ui.GuiApi import GuiApi
from zmlx.ui.GuiBuffer import gui
from zmlx.ui.Label import Label
from zmlx.ui.Qt import QtCore, has_PyQt6, QtWidgets, QtMultimedia
from zmlx.ui.TabWidget import TabWidget
from zmlx.ui.TaskProc import TaskProc
from zmlx.ui.VersionLabel import VersionLabel
from zmlx.ui.Widgets.TextEdit import TextEdit
from zmlx.ui.alg.show_seepage import show_seepage
from zmlx.ui.alg.show_txt import show_txt


class MainWindow(QtWidgets.QMainWindow):
    sig_cwd_changed = QtCore.pyqtSignal(str)
    sig_do_task = QtCore.pyqtSignal()
    sig_play_sound = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowIcon(load_icon('app'))
        self.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.__task_proc = TaskProc(self)

        self.__file_processors = {'.py': [self.open_code, 'Python File To Execute'],
                                  '.fn2': [self.show_fn2, 'Fracture Network 2D'],
                                  '.seepage': [show_seepage, 'Seepage Model File'],
                                  '.txt': [show_txt, 'Text file'],
                                  '.json': [show_txt, 'Json file'],
                                  '.xml': [show_txt, 'Xml file'],
                                  '.png': [self.open_image, 'Png file'],
                                  '.jpg': [self.open_image, 'Jpg file']
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

        self.__actions = {}
        self.__menu_bar = QtWidgets.QMenuBar(self)
        self.setMenuBar(self.__menu_bar)
        self.__menus = {}
        self.__toolbars = {}
        self.__title = None
        self.__init_actions()
        self.__init_gui_api()

        self.sig_cwd_changed.connect(self.refresh)
        self.sig_cwd_changed.connect(self.view_cwd)
        self.sig_cwd_changed.connect(self.__console.restore_code)

        self.__console.sig_refresh.connect(self.refresh)

        # 尝试关闭进度条，从而使得进度条总是临时显示一下.
        self.__timer_close_progress = QtCore.QTimer(self)
        self.__timer_close_progress.timeout.connect(lambda: self.progress(visible=False))
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
        self.__warning_action = QAction(self)
        self.__warning_action.setToolTip('警告消息(点击以隐藏)')
        self.__warning_action.triggered.connect(lambda: self.toolbar_warning(text=''))
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
            if app_data.getenv(key='check_lic_when_start', default='No', ignore_empty=True) == 'Yes':
                self.check_license()
        except Exception as err:
            print(f'Error: {err}')

        self.refresh()

    def __init_actions(self):
        action_files = get_action_files()

        def get_menu(name):
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

        def get_toolbar(name):
            toolbar = self.__toolbars.get(name)
            if toolbar is not None:
                return toolbar
            else:
                toolbar = self.addToolBar(name)
                self.__toolbars[name] = toolbar
                return toolbar

        def add_action(menu, action_name):
            file = action_files.pop(action_name, None)
            if file is not None:
                action = ActionX(self, file=file)
                if menu is None:
                    menu = action.get('menu', '其它')
                if action.get('on_toolbar', False):
                    get_toolbar(menu).addAction(action)
                get_menu(menu).addAction(action)
                self.__actions[action_name] = action

        def add_actions(menu, action_names):
            for s in action_names:
                add_action(menu, s)

        for title, names in get_menus().items():
            add_actions(title, names)

        if len(action_files) > 0:
            add_actions(None, list(action_files.keys()))

    def __init_gui_api(self):
        self.__gui_api.add_func('cls', self.cls)
        self.__gui_api.add_func('close', self.close)
        self.__gui_api.add_func('close_all_tabs', self.__tab_widget.close_all_tabs)
        self.__gui_api.add_func('exec_current', self.exec_current)
        self.__gui_api.add_func('get_widget', self.get_widget)
        self.__gui_api.add_func('get_figure_widget', self.get_figure_widget)
        self.__gui_api.add_func('get_current_widget', self.get_current_widget)
        self.__gui_api.add_func('is_running', self.is_running)
        self.__gui_api.add_func('kill_thread', self.kill_thread)
        self.__gui_api.add_func('plot', self.cmd_plot)
        self.__gui_api.add_func('progress', self.progress)
        self.__gui_api.add_func('play_sound', self.play_sound)
        self.__gui_api.add_func('refresh', self.refresh)
        self.__gui_api.add_func('open_file', self.open_file)
        self.__gui_api.add_func('open_file_by_dlg', self.open_file_by_dlg)
        self.__gui_api.add_func('open_text', self.open_text)
        self.__gui_api.add_func('open_image', self.open_image)
        self.__gui_api.add_func('open_code', self.open_code)
        self.__gui_api.add_func('show_next', self.__tab_widget.show_next)
        self.__gui_api.add_func('show_prev', self.__tab_widget.show_prev)
        self.__gui_api.add_func('show_fn2', self.show_fn2)
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
        if hasattr(self, 'titleText') and self.__title is not None:
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
            reply = QtWidgets.QMessageBox.question(self, '退出HfUI',
                                                   "内核似乎正在运行，确定要退出吗？",
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if reply != QtWidgets.QMessageBox.Yes:
                event.ignore()
                return

    def showEvent(self, event):
        super(MainWindow, self).showEvent(event)
        self.refresh()

    def resizeEvent(self, event):
        super(MainWindow, self).resizeEvent(event)
        name = 'main_window_size_PyQt6' if has_PyQt6 else 'main_window_size'
        save_window_size(self, name)

    def get_widget(self, the_type, caption=None, on_top=None, init=None,
                   type_kw=None, oper=None, icon=None):
        """
        返回一个控件，其中type为类型，caption为标题，现有的控件，只有类型和标题都满足，才会返回，否则就
        创建新的控件。
        init：首次生成控件，在显示之前所做的操作
        oper：每次调用都会执行，且在控件显示之后执行
        """
        widget = self.__tab_widget.find_widget(the_type=the_type, text=caption)
        if widget is None:
            count_max = 100
            assert self.__tab_widget.count() < count_max, f'maximum count of tab_widget is {count_max}'
            if type_kw is None:
                type_kw = {}
            try:
                widget = the_type(self.__tab_widget, **type_kw)
                assert isinstance(widget, the_type)
            except Exception as err:
                print(f'Error: {err}')
                return
            if init is not None:
                try:
                    init(widget)
                except Exception as err:
                    print(f'Error: {err}')
            if caption is None:
                caption = 'untitled'
            index = self.__tab_widget.addTab(widget, caption)
            if icon is not None:
                self.__tab_widget.setTabIcon(index, load_icon(icon))
            self.__tab_widget.setCurrentWidget(widget)
            if oper is not None:
                self.add_task(lambda: oper(widget))
            return widget
        else:
            if on_top:
                self.__tab_widget.setCurrentWidget(widget)
            if oper is not None:
                self.add_task(lambda: oper(widget))
            return widget

    def get_figure_widget(self, clear=None, **kwargs):
        from zmlx.ui.MatplotWidget import MatplotWidget
        if kwargs.get('icon', None) is None:
            kwargs['icon'] = 'matplotlib'
        widget = self.get_widget(the_type=MatplotWidget, **kwargs)
        if clear:
            fig = widget.figure
            for ax in fig.get_axes():
                fig.delaxes(ax)
        return widget

    def show_fn2(self, filepath, **kwargs):
        from zmlx.ui.Widgets.Fn2Widget import Fn2Widget
        if kwargs.get('caption') is None:
            kwargs['caption'] = 'Fractures'
        widget = self.get_widget(the_type=Fn2Widget, **kwargs)
        assert widget is not None
        widget.open_fn2_file(filepath)

    def cmd_plot(self, kernel=None, fname=None, dpi=300, **kwargs):
        if kernel is not None:
            try:
                widget = self.get_figure_widget(**kwargs)
                kernel(widget.figure)
                widget.draw()
                if fname is not None:
                    assert dpi is not None
                    widget.savefig(fname=fname, dpi=dpi)
            except Exception as err:
                warnings.warn(f'meet exception <{err}> when run <{kernel}>')

    def cmd_status(self, *args, **kwargs):
        self.__status_bar.showMessage(*args, **kwargs)

    def trigger(self, name):
        action = self.__actions.get(name)
        assert action is not None, f'Error: action <{name}> not found'
        action.trigger()

    def cmd_title(self, title):
        self.__title = title
        self.refresh()

    def view_cwd(self):
        from zmlx.ui.Widgets.CwdViewer import CwdViewer
        self.get_widget(the_type=CwdViewer, caption='文件', on_top=True, oper=lambda w: w.refresh(), icon='cwd')

    def progress(self, label=None, val_range=None, value=None, visible=None, duration=5000):
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
                w = self.__tab_widget.widget(i)
                if isinstance(w, CodeEdit):
                    if samefile(name_1, w.get_fname()):
                        return w

        if len(fname) > 0:
            if samefile(fname, self.__console.get_fname()):
                return
            widget = get_widget(fname)
            if widget is not None:
                self.__tab_widget.setCurrentWidget(widget)
                return
            else:
                self.get_widget(the_type=CodeEdit,
                                caption=os.path.basename(fname) if caption is None else caption,
                                on_top=True,
                                oper=lambda x: x.open(fname), icon='python')
                print(f'文件已打开: \n\t{fname}\n\n请点击工具栏上的<运行>按钮以运行!\n\n')

    def open_text(self, fname, caption=None):
        if not isinstance(fname, str):
            return
        if len(fname) > 0:
            for i in range(self.__tab_widget.count()):
                w = self.__tab_widget.widget(i)
                if isinstance(w, TextEdit):
                    if samefile(fname, w.get_fname()):
                        self.__tab_widget.setCurrentWidget(w)
                        return
            self.get_widget(the_type=TextEdit,
                            caption=os.path.basename(fname) if caption is None else caption,
                            on_top=True,
                            oper=lambda x: x.set_fname(fname))

    def open_image(self, fname, caption=None, on_top=True):
        """
        打开一个图片
        """
        if isinstance(fname, str):
            if os.path.isfile(fname):
                from zmlx.ui.Widgets.Image import ImageViewer
                self.get_widget(the_type=ImageViewer, caption=os.path.basename(fname) if caption is None else caption,
                                on_top=on_top,
                                oper=lambda x: x.set_image(fname))

    def exec_current(self):
        if isinstance(self.__tab_widget.currentWidget(), CodeEdit):
            self.__tab_widget.currentWidget().save()
            self.__console.exec_file(self.__tab_widget.currentWidget().get_fname())
        else:
            self.__console.exec_file()

    def open_file(self, filepath):
        if not isinstance(filepath, str):
            return

        if not os.path.isfile(filepath):
            if os.path.isdir(filepath):
                self.set_cwd(filepath)
            return

        ext = os.path.splitext(filepath)[-1]
        if ext is None:
            QtWidgets.QMessageBox.warning(self, '警告', f'扩展名不存在: {filepath}')
            return

        assert isinstance(ext, str)
        ext = ext.lower()

        proc = self.__file_processors.get(ext, None)
        if proc is None:
            if os.path.isfile(filepath):
                show_fileinfo(filepath)
            return
        try:
            assert len(proc) == 2
            func, desc = proc
            return func(filepath)
        except Exception as err:
            print(f'Error: filepath = {filepath} \nmessage = {err}')

    def open_file_by_dlg(self, folder=None):
        temp_1 = ''
        for ext, proc in self.__file_processors.items():
            assert len(proc) == 2
            func, desc = proc
            temp_1 = f'{temp_1}{desc} (*{ext});; '

        if folder is None:
            folder = ''

        def get_open_file_name(*args, **kwargs):
            fpath, _ = QtWidgets.QFileDialog.getOpenFileName(self, *get_text(args), **get_text(kwargs))
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
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, get_text('请选择工程文件夹'), os.getcwd())
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
            from zml import lic
            if lic.summary is None:
                self.toolbar_warning('此电脑未授权，请确保: 1、使用最新版；2、本机联网!')
        except Exception as err:
            print(f'Error: {err}')

    def show_about(self):
        from zmlx.ui.Widgets.About import About
        self.check_license()
        self.get_widget(the_type=About, caption='关于', on_top=True, icon='info')

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


def execute(code=None, keep_cwd=True, close_after_done=True):
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
    if splash_fig is not None and app_data.getenv('disable_splash', default='No', ignore_empty=True) != 'Yes':
        splash = MySplashScreen()
        try:
            rect = screen_size()
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

    temp_file = app_data.temp('console_output.txt')

    def f1():
        if app_data.getenv(key='restore_console_output', default='Yes', ignore_empty=True) == 'Yes':
            win.get_output_widget().load_text(temp_file)
        app_data.space['main_window'] = win
        gui.push(win.get_gui_api())
        print(f'Push Gui: {win.get_gui_api()}')
        sys.stdout = win.get_output_widget()
        sys.stderr = win.get_output_widget()

    def f2():
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        print('Pop Gui')
        gui.pop()
        app_data.space['main_window'] = None
        win.get_output_widget().save_text(temp_file)

    f1()

    try:
        name = 'main_window_size_PyQt6' if has_PyQt6 else 'main_window_size'
        load_window_size(win, name)
    except Exception as err:
        print(f'Error: {err}')

    try:
        load_window_style(win, 'zml_main.qss')
    except Exception as err:
        print(f'Error: {err}')

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

    def setup():
        """
        在程序界面启动之后执行的设置
        """
        if is_chinese(zml.get_dir()):
            win.toolbar_warning('提醒：请务必将程序安装在纯英文路径下')

        for path in find_all('zml_gui_setup.py'):
            try:
                print(f'Exec File: {path}')
                exec(read_text(path, encoding='utf-8'), win.get_console().workspace)
            except Exception as e2:
                print(f'Failed: {e2}')

    results = []
    if close_after_done and code is not None:
        win.get_console().sig_kernel_done.connect(win.close)
    win.get_console().sig_kernel_done.connect(lambda: results.append(win.get_console().result))
    if code is not None:
        def codex():
            win.get_console().time_beg = None  # 对于外部的这种调用，不显示cpu耗时
            setup()
            return code()

        win.get_console().start_func(codex)
    else:
        win.get_console().start_func(setup)

    app.exec()
    f2()
    if hasattr(win, 'tabs_should_be_saved'):
        save_tab_start_code(app_data.temp('tab_start_code.json'), win)
    if len(results) > 0:
        return results[0]


def get_window() -> MainWindow:
    window = app_data.get('main_window')
    if window is not None:
        assert isinstance(window, MainWindow)
        return window
