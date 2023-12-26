import sys
import warnings

from zmlx.ui.GuiBuffer import gui
from zml import lic
from zmlx.filesys.has_permission import has_permission
from zmlx.filesys.samefile import samefile
from zmlx.filesys.show_fileinfo import show_fileinfo
from zmlx.ui.CodeEdit import CodeEdit
from zmlx.ui.Config import *
from zmlx.ui.ConsoleWidget import ConsoleWidget
from zmlx.ui.GuiApi import GuiApi
from zmlx.ui.Qt import QtCore
from zmlx.ui.Script import Script
from zmlx.ui.TabWidget import TabWidget
from zmlx.ui.TaskProc import TaskProc
from zmlx.ui.Widgets.TextEdit import TextEdit
from zmlx.ui.alg.show_seepage import show_seepage
from zmlx.ui.alg.show_txt import show_txt


class MainWindow(QtWidgets.QMainWindow):
    sig_cwd_changed = QtCore.pyqtSignal(str)
    sig_do_task = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowIcon(load_icon('app.png'))
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.task_proc = TaskProc(self)

        self.file_processors = {'.py': [self.open_code, 'Python File To Execute'],
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
        self.splitter = QtWidgets.QSplitter(widget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.tab_widget = TabWidget(self.splitter)
        self.tab_widget.currentChanged.connect(self.update_widget_actions)
        self.console_widget = ConsoleWidget(self.splitter)
        self.gui_api = GuiApi(widget, self.console_widget.get_break_point(), self.console_widget.get_flag_exit())
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        h_layout.addWidget(self.splitter)
        self.setCentralWidget(widget)

        self.actions = {}
        self.menu_bar = QtWidgets.QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.menus = {}
        self.toolbars = {}
        self.titleText = None
        self.__init_actions()
        self.__init_gui_api()

        self.sig_cwd_changed.connect(self.refresh)
        self.sig_cwd_changed.connect(self.view_cwd)
        self.sig_cwd_changed.connect(self.console_widget.restore_code)

        self.status_bar = QtWidgets.QStatusBar(self)
        self.status_bar.showMessage('正在初始化 ..')  # 在__init_later中显示“就绪”
        self.setStatusBar(self.status_bar)
        self.propress_label = QtWidgets.QLabel()
        self.propress_bar = QtWidgets.QProgressBar()
        self.status_bar.addPermanentWidget(self.propress_label)
        self.status_bar.addPermanentWidget(self.propress_bar)
        self.progress(visible=False)

        self.init_later_timer = QtCore.QTimer(self)
        self.init_later_timer.timeout.connect(self.__init_later)
        self.init_later_timer.start(2000)
        self.update_widget_actions()  # 更新一些和控件相关的action的显示

        try:
            from zmlx.ui.data.get_path import get_path
            fname = get_path('zml_icons', 'welcome.jpg')
            if os.path.isfile(fname):
                self.open_image(fname, caption='Welcome')
        except:
            pass

    def __init_later(self):
        """
        执行一些可能会比较耗时（但是又不那么关键的）的初始化任务
        """
        self.init_later_timer.stop()
        # ----
        try:
            if lic.summary is None:
                toolbar = self.__get_toolbar('NoLicense')
                toolbar.setStyleSheet('background-color:rgb(255, 255, 0)')
                action = QtWidgets.QAction(self)
                action.setText('版本已过期，请更新并联网使用，谢谢！')
                toolbar.addAction(action)
        except:
            pass

        self.status_bar.showMessage('就绪')

    def __init_actions(self):
        scripts = {}
        for name, file in get_action_files().items():
            scripts[name] = Script(file=file)

        def add_action(menu, name):
            script = scripts.pop(name, None)
            if script is not None:
                toolbar = self.__get_toolbar(menu) if script.on_toolbar else None
                action = self.__create_action(text=script.text,
                                              slot=lambda: script(self),
                                              iconname=script.icon,
                                              name=script.name,
                                              toolbar=toolbar,
                                              shortcut=None,
                                              enabled=script.enabled,
                                              tooltip=script.tooltip,
                                              )
                self.__get_menu(menu).addAction(action)
                self.actions[name] = action

        def add_actions(menu, names):
            for s in names:
                add_action(menu, s)

        for title, names in get_menus().items():
            add_actions(title, names)

        for name in list(scripts.keys()):
            menu_name = scripts.get(name).menu
            if menu_name is not None:
                add_action(menu_name, name)

        if len(scripts) > 0:
            add_actions('其它', list(scripts.keys()))

    def __init_gui_api(self):
        self.gui_api.add_func('cls', self.console_widget.output_widget.clear)
        self.gui_api.add_func('show_fn2', self.show_fn2)
        self.gui_api.add_func('get_widget', self.get_widget)
        self.gui_api.add_func('get_figure_widget', self.get_figure_widget)
        self.gui_api.add_func('plot', self.cmd_plot)
        self.gui_api.add_func('status', self.cmd_status)
        self.gui_api.add_func('refresh', self.refresh)
        self.gui_api.add_func('title', self.cmd_title)
        self.gui_api.add_func('window', lambda: self)
        self.gui_api.add_func('trigger', self.trigger)
        self.gui_api.add_func('progress', self.progress)
        self.gui_api.add_func('view_cwd', self.view_cwd)
        self.gui_api.add_func('close', self.close)
        self.gui_api.add_func('open_code', self.open_code)
        self.gui_api.add_func('exec_current', self.exec_current)
        self.gui_api.add_func('open_file', self.open_file)
        self.gui_api.add_func('open_file_by_dlg', self.open_file_by_dlg)
        self.gui_api.add_func('set_cwd', self.set_cwd)
        self.gui_api.add_func('set_cwd_by_dialog', self.set_cwd_by_dialog)
        self.gui_api.add_func('open_text', self.open_text)
        self.gui_api.add_func('open_image', self.open_image)
        self.gui_api.add_func('kill_thread', self.console_widget.kill_thread)
        self.gui_api.add_func('cls', self.console_widget.output_widget.clear)
        self.gui_api.add_func('show_next', self.tab_widget.show_next)
        self.gui_api.add_func('show_prev', self.tab_widget.show_prev)
        self.gui_api.add_func('close_all_tabs', self.tab_widget.close_all_tabs)

    def __get_menu(self, name):
        assert name is not None, f'Error: name is None when get_menu'
        menu = self.menus.get(name)
        if menu is not None:
            return menu
        else:
            menu = QtWidgets.QMenu(self.menu_bar)
            menu.setTitle(get_text(name))
            self.menu_bar.addAction(menu.menuAction())
            self.menus[name] = menu
            return menu

    def __get_toolbar(self, name):
        if name is None:
            return
        toolbar = self.toolbars.get(name)
        if toolbar is not None:
            return toolbar
        else:
            toolbar = self.addToolBar(name)
            self.toolbars[name] = toolbar
            return toolbar

    def __create_action(self, text=None, slot=None, iconname=None, name=None, toolbar=None, shortcut=None,
                        enabled=True, tooltip=None):
        action = QtWidgets.QAction(self)
        if iconname is not None:
            action.setIcon(load_icon(iconname))
        else:
            action.setIcon(load_icon('python.png'))
        action.setEnabled(enabled)
        if tooltip is not None:
            assert isinstance(tooltip, str)
            action.setToolTip(get_text(tooltip))
        if text is not None:
            action.setText(get_text(text))
        if slot is not None:
            action.triggered.connect(slot)
        if name is not None:
            if len(name) > 0:
                setattr(self, name, action)
        if toolbar is not None:
            toolbar.addAction(action)
        if shortcut is not None:
            action.setShortcut(shortcut)
        return action

    def update_widget_actions(self):
        widget = self.tab_widget.currentWidget()

        def set_visible(name, value):
            try:
                ac = getattr(self, name)
                ac.setEnabled(value)
            except:
                pass

        def f(action_name, func_name):
            set_visible(action_name, hasattr(widget, func_name))

        for a, b in [('action_export_data', 'export_data'),
                     ('action_exec_current', 'console_exec')]:
            f(a, b)

        set_visible('action_close_all_tabs', self.tab_widget.count() > 0)

    def refresh(self):
        """
        尝试刷新标题以及当前的页面
        """
        if hasattr(self, 'titleText') and self.titleText is not None:
            self.setWindowTitle(f'{self.titleText}')
        else:
            self.setWindowTitle(f'WorkDir: {os.getcwd()}')

        try:
            current = self.tab_widget.currentWidget()
            if hasattr(current, 'refresh'):
                self.task_proc.add(lambda: current.refresh())
        except:
            pass

    def closeEvent(self, event):
        if self.console_widget.is_running():
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
        save_window_size(self, 'main_window_size')

    def get_widget(self, type, caption=None, on_top=None, init=None, type_kw=None, oper=None, icon=None):
        """
        返回一个控件，其中type为类型，caption为标题，现有的控件，只有类型和标题都满足，才会返回，否则就
        创建新的控件。
        init：首次生成控件，在显示之前所做的操作
        oper：每次调用都会执行，且在控件显示之后执行
        """
        widget = self.tab_widget.find_widget(type=type, text=caption)
        if widget is None:
            count_max = 100
            assert self.tab_widget.count() < count_max, f'maximum count of tab_widget is {count_max}'
            if type_kw is None:
                type_kw = {}
            try:
                widget = type(self.tab_widget, **type_kw)
                assert isinstance(widget, type)
            except:
                return
            if init is not None:
                try:
                    init(widget)
                except:
                    pass
            if caption is None:
                caption = 'untitled'
            index = self.tab_widget.addTab(widget, caption)
            if icon is not None:
                self.tab_widget.setTabIcon(index, load_icon(icon))
            self.tab_widget.setCurrentWidget(widget)
            if oper is not None:
                self.task_proc.add(lambda: oper(widget))
            return widget
        else:
            if on_top:
                self.tab_widget.setCurrentWidget(widget)
            if oper is not None:
                self.task_proc.add(lambda: oper(widget))
            return widget

    def get_figure_widget(self, clear=None, **kwargs):
        from zmlx.ui.MatplotWidget import MatplotWidget
        if kwargs.get('icon', None) is None:
            kwargs['icon'] = 'matplotlib.png'
        widget = self.get_widget(type=MatplotWidget, **kwargs)
        if clear:
            fig = widget.figure
            for ax in fig.get_axes():
                fig.delaxes(ax)
        return widget

    def show_fn2(self, filepath, **kwargs):
        from zmlx.ui.Widgets.Fn2Widget import Fn2Widget
        if kwargs.get('caption') is None:
            kwargs['caption'] = 'Fractures'
        widget = self.get_widget(type=Fn2Widget, **kwargs)
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
        self.status_bar.showMessage(*args, **kwargs)

    def trigger(self, name):
        action = self.actions.get(name, None)
        assert action is not None, f'Error: action <{name}> not found'
        action.trigger()

    def cmd_title(self, title):
        self.titleText = title
        self.refresh()

    def view_cwd(self):
        from zmlx.ui.Widgets.CwdViewer import CwdViewer
        self.get_widget(type=CwdViewer, caption='文件', on_top=True, oper=lambda w: w.refresh(), icon='cwd.png')

    def progress(self, label=None, range=None, value=None, visible=None):
        """
        显示进度
        """
        if label is not None:
            visible = True
            self.propress_label.setText(label)
        if range is not None:
            visible = True
            assert len(range) == 2
            self.propress_bar.setRange(*range)
        if value is not None:
            visible = True
            self.propress_bar.setValue(value)
        if visible is not None:
            self.propress_bar.setVisible(visible)
            self.propress_label.setVisible(visible)

    def open_code(self, fname, caption=None):
        if not isinstance(fname, str):
            return

        def get_widget(fname):
            for i in range(self.tab_widget.count()):
                w = self.tab_widget.widget(i)
                if isinstance(w, CodeEdit):
                    if samefile(fname, w.get_fname()):
                        return w

        if len(fname) > 0:
            if samefile(fname, self.console_widget.get_fname()):
                return
            widget = get_widget(fname)
            if widget is not None:
                self.tab_widget.setCurrentWidget(widget)
                return
            else:
                self.get_widget(type=CodeEdit,
                                caption=os.path.basename(fname) if caption is None else caption,
                                on_top=True,
                                oper=lambda x: x.open(fname), icon='python.png')
                if not app_data.has_tag_today('tip_shown_when_edit_code'):
                    QtWidgets.QMessageBox.about(self, '成功',
                                                '文件已打开，请点击工具栏上的<运行>按钮以运行')
                    app_data.add_tag_today('tip_shown_when_edit_code')

    def open_text(self, fname, caption=None):
        if not isinstance(fname, str):
            return
        if len(fname) > 0:
            for i in range(self.tab_widget.count()):
                w = self.tab_widget.widget(i)
                if isinstance(w, TextEdit):
                    if samefile(fname, w.get_fname()):
                        self.tab_widget.setCurrentWidget(w)
                        return
            self.get_widget(type=TextEdit,
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
                self.get_widget(type=ImageViewer, caption=os.path.basename(fname) if caption is None else caption,
                                on_top=on_top,
                                oper=lambda x: x.setImage(fname))

    def exec_current(self):
        if isinstance(self.tab_widget.currentWidget(), CodeEdit):
            self.tab_widget.currentWidget().save()
            self.console_widget.exec_file(self.tab_widget.currentWidget().get_fname())
        else:
            self.console_widget.exec_file()

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

        proc = self.file_processors.get(ext, None)
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
        temp = ''
        for ext, proc in self.file_processors.items():
            assert len(proc) == 2
            func, desc = proc
            temp = f'{temp}{desc} (*{ext});; '

        if folder is None:
            folder = ''

        def get_open_file_name(*args, **kwargs):
            fpath, _ = QtWidgets.QFileDialog.getOpenFileName(self, *get_text(args), **get_text(kwargs))
            return fpath

        filepath = get_open_file_name('please choose the file to open',
                                      folder, f'All File(*.*);;{temp}')
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
                    except:
                        pass

    def set_cwd_by_dialog(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, get_text('请选择工程文件夹'), os.getcwd())
        self.set_cwd(folder)


class MySplashScreen(QtWidgets.QSplashScreen):
    def mousePressEvent(self, event):
        pass


def execute(code=None, keep_cwd=True, close_after_done=True):
    try:
        app_data.log(f'gui_execute. file={__file__}')
    except:
        pass

    if gui.exists():
        if code is not None:
            return code()
        else:
            return None

    if not keep_cwd:
        load_cwd()

    app = QtWidgets.QApplication(sys.argv)

    splash_fig = load_pixmap('splash.jpg')
    if splash_fig is not None and app_data.getenv('disable_splash', default='False') != 'True':
        splash = MySplashScreen()
        splash.setPixmap(splash_fig)
        splash.show()
        app.processEvents()  # 处理主进程事件
    else:
        splash = None

    win = MainWindow()

    def f1():
        app_data.space['main_window'] = win
        gui.push(win.gui_api)
        print(f'Push Gui: {win.gui_api}')
        sys.stdout = win.console_widget.output_widget
        sys.stderr = win.console_widget.output_widget

    def f2():
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        print('Pop Gui')
        gui.pop()
        app_data.space['main_window'] = None

    f1()

    try:
        load_window_size(win, 'main_window_size')
    except:
        pass

    try:
        load_window_style(win, 'zml_main.qss')
    except:
        pass

    def my_excepthook(type, value, tb):
        message = f"""Exception Type: {type}
Message : {value}
Object : {tb}
We are very sorry for this exception. Please check your data according to the above message. If it's still unresolved, please contact the author (email: 'zhangzhaobin@mail.iggcas.ac.cn'or qq: 542844710), Thank you!
"""
        print(message)
        QtWidgets.QMessageBox.warning(win, "Unresolved Exception", message)

    sys.excepthook = my_excepthook
    win.show()

    if splash is not None:
        splash.finish(win)  # 隐藏启动界面
        splash.deleteLater()

    def setup():
        for path in find_all('zml_gui_setup.py'):
            try:
                print(f'Exec File: {path}')
                exec(read_text(path, encoding='utf-8'), win.console_widget.workspace)
            except Exception as e:
                print(f'Failed: {e}')

    results = []
    if close_after_done and code is not None:
        win.console_widget.sig_kernel_done.connect(win.close)
    win.console_widget.sig_kernel_done.connect(lambda: results.append(win.console_widget.result))
    if code is not None:
        def codex():
            win.console_widget.time_beg = None  # 对于外部的这种调用，不显示cpu耗时
            setup()
            return code()

        win.console_widget.start_func(codex)
    else:
        win.console_widget.start_func(setup)
    app.exec_()
    f2()
    if len(results) > 0:
        return results[0]
