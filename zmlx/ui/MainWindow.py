# -*- coding: utf-8 -*-


import sys

from zml import gui
from zmlx.ui.CodeAlg import edit_code
from zmlx.ui.Config import *
from zmlx.ui.ConsoleWidget import ConsoleWidget
from zmlx.ui.FileAlg import open_file
from zmlx.ui.GuiApi import GuiApi
from zmlx.ui.Script import Script
from zmlx.ui.TabWidget import TabWidget


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowIcon(load_icon('app.png'))
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        widget = QtWidgets.QWidget(self)
        h_layout = QtWidgets.QVBoxLayout(widget)

        self.splitter = QtWidgets.QSplitter(widget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.tab_widget = TabWidget(self.splitter)
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
        self.console_widget.sig_cwd_changed.connect(self.refresh)
        self.console_widget.sig_cwd_changed.connect(self.show_files)

        self.status_bar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.propress_label = QtWidgets.QLabel()
        self.propress_bar = QtWidgets.QProgressBar()
        self.status_bar.addPermanentWidget(self.propress_label)
        self.status_bar.addPermanentWidget(self.propress_bar)
        self.progress(visible=False)

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

        for m in get_menus():
            add_actions(m.get('title', '未命名'), m.get('actions', []))

        for name in list(scripts.keys()):
            menu_name = scripts.get(name).config.get('menu', None)
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
        self.gui_api.add_func('show_files', self.show_files)
        self.gui_api.add_func('set_cwd_by_dialog', self.console_widget.set_cwd_by_dialog)

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

    def refresh(self):
        if hasattr(self, 'titleText') and self.titleText is not None:
            self.setWindowTitle(f'{self.titleText}')
        else:
            self.setWindowTitle(f'WorkDir: {os.getcwd()}')

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

    def get_widget(self, type, caption=None, on_top=None, init=None, type_kw=None, oper=None):
        """
        返回一个控件，其中type为类型，caption为标题，现有的控件，只有类型和标题都满足，才会返回，否则就
        创建新的控件。
        init：首次生成控件，在显示之前所做的操作
        oper：每次调用都会执行，且在控件显示之后执行
        """
        widget = self.tab_widget.find_widget(type=type, text=caption)
        if widget is None:
            count_max = 50
            assert self.tab_widget.count() < count_max, f'maximum count of tab_widget is {count_max}'
            if type_kw is None:
                type_kw = {}
            widget = type(self.tab_widget, **type_kw)
            if init is not None:
                init(widget)
            if caption is None:
                caption = 'untitled'
            self.tab_widget.addTab(widget, caption)
            if widget is not None:
                self.tab_widget.setCurrentWidget(widget)
            if oper is not None:
                oper(widget)
            return widget
        else:
            if on_top:
                self.tab_widget.setCurrentWidget(widget)
            if oper is not None:
                oper(widget)
            return widget

    def get_figure_widget(self, clear=None, **kwargs):
        from .MatplotWidget import MatplotWidget
        widget = self.get_widget(type=MatplotWidget, **kwargs)
        if clear:
            fig = widget.figure
            for ax in fig.get_axes():
                fig.delaxes(ax)
        return widget

    def show_fn2(self, filepath, **kwargs):
        from .Fn2Widget import Fn2Widget
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
                print(f'Error run kernel in .plot: {err}')

    def cmd_status(self, *args, **kwargs):
        self.status_bar.showMessage(*args, **kwargs)

    def trigger(self, name):
        action = self.actions.get(name, None)
        assert action is not None, f'Error: action <{name}> not found'
        action.trigger()

    def cmd_title(self, title):
        self.titleText = title
        self.refresh()

    def show_files(self):
        from zmlx.ui.FileWidget import FileWidget

        def try_edit(ipath):
            if os.path.isfile(ipath):
                ext = os.path.splitext(ipath)[-1]
                if ext is not None:
                    if ext.lower() == '.py' or ext.lower() == '.pyw':
                        edit_code(ipath, False)

        def init(w):
            w.sig_file_clicked.connect(try_edit)
            w.sig_file_double_clicked.connect(lambda ipath: open_file(ipath))

        widget = self.get_widget(type=FileWidget, caption='文件', on_top=True,
                                 init=init)
        widget.set_dir()

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


def execute(code=None, keep_cwd=True, close_after_done=True):
    try:
        from zml import data
        data.log(f'gui_execute. code={code}, file={__file__}')
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
    win = MainWindow()

    def f1():
        gui.push(win.gui_api)
        print(f'Push Gui: {win.gui_api}')
        sys.stdout = win.console_widget.output_widget

    def f2():
        sys.stdout = sys.__stdout__
        print('Pop Gui')
        gui.pop()

    f1()

    load_window_size(win, 'main_window_size')
    load_window_style(win, 'zml_main.qss')

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
