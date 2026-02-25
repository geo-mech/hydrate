from zml import app_data
from zmlx.ui import settings
from zmlx.ui.alg import create_action
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets
from zmlx.ui.utils import TaskProc


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(TabWidget, self).__init__(parent)
        self.task_proc = TaskProc(self)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.setMovable(True)
        self.context_actions = []  # 附加的命令

    def contextMenuEvent(self, event):
        tab_index = None
        for i in range(self.count()):
            if self.tabBar().tabRect(i).contains(event.pos()):
                tab_index = i

        menu = QtWidgets.QMenu(self)
        if self.count() >= 1:
            menu.addAction(
                create_action(self, '关闭所有', slot=self.close_all_tabs))
            menu.addAction(
                create_action(self, '列出标签', slot=gui.show_tab_details))
            if tab_index is not None:
                menu.addSeparator()
                menu.addAction(create_action(
                    self, text='重命名',
                    slot=lambda: self._rename_tab(tab_index))
                )
                menu.addAction(create_action(
                    self, text='关闭',
                    slot=lambda: self.close_tab(tab_index))
                )
                menu.addAction(create_action(
                    self, text='关闭其它',
                    slot=lambda: self._close_all_except(tab_index))
                )

        if len(self.context_actions) > 0:
            menu.addSeparator()
            for action in self.context_actions:
                menu.addAction(action)

        menu.exec(event.globalPos())

    def close_tab(self, index):
        if index < self.count():
            widget = self.widget(index)
            closeable = getattr(widget, 'tab_closeable', None)
            if closeable or closeable is None:
                f = getattr(widget, 'save_file', None)  # 尝试调用save_file
                if callable(f):
                    try:
                        f()
                    except Exception as e:
                        print(e)
                widget.deleteLater()
                self.removeTab(index)
                return True
            else:
                return False
        else:
            return False

    def close_tab_object(self, widget):
        index = self.get_tab_index(widget)
        if index is not None:
            return self.close_tab(index)
        else:
            return False

    def add_task(self, task):
        self.task_proc.add(task)

    def find_widgets(self, the_type=None, text=None, is_ok=None):
        """
        返回给定条件的所有Widget对象。给定的所有条件需要同时满足
        Args:
            the_type: 控件的类型
            text: 标题
            is_ok: 一个函数，用于检查控件对象

        Returns:
            符合条件的所有Widget对象
            符合条件的所有Widget对象，否则返回None
        """
        assert the_type is not None or text is not None or is_ok is not None
        widgets = []
        for i in range(self.count()):
            widget = self.widget(i)
            if the_type is not None:
                if not isinstance(widget, the_type):
                    continue
            if text is not None:
                if text != self.tabText(i):
                    continue
            if callable(is_ok):
                if not is_ok(widget):
                    continue
            widgets.append(widget)
        return widgets

    def find_widget(self, the_type=None, text=None, is_ok=None):
        """
        返回给定条件的Widget。给定的所有条件需要同时满足
        Args:
            the_type: 控件的类型
            text: 标题
            is_ok: 一个函数，用于检查控件对象

        Returns:
            符合条件的Widget对象，否则返回None
        """
        assert the_type is not None or text is not None or is_ok is not None
        for i in range(self.count()):
            widget = self.widget(i)
            if the_type is not None:
                if not isinstance(widget, the_type):
                    continue
            if text is not None:
                if text != self.tabText(i):
                    continue
            if callable(is_ok):
                if not is_ok(widget):
                    continue
            return widget
        return None

    def get_widget(
            self, the_type, caption=None, on_top=None, init=None,
            type_kw=None, oper=None, icon=None, caption_color=None,
            set_parent=False, tooltip=None, is_ok=None, closeable=None):
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
            closeable: 是否允许关闭

        Returns:
            符合条件的Widget对象，否则返回None
        """
        if caption is None:
            caption = 'untitled'
        widget = self.find_widget(the_type=the_type, text=caption, is_ok=is_ok)
        if widget is None:
            if self.count() >= 200:
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
                if closeable is not None:
                    widget.tab_closeable = closeable
            except Exception as err:
                print(f'Error: {err}')
                return None
            if init is not None:
                try:
                    init(widget)
                except Exception as err:
                    print(f'Error: {err}')
            index = self.addTab(widget, caption)
            if icon is None:
                icon = app_data.getenv(key='default_tab_icon', default='python')
            if icon is not None:
                self.setTabIcon(index, settings.load_icon(icon))
            self.setCurrentWidget(widget)
            if tooltip is not None:
                self.setTabToolTip(index, tooltip)
            if caption_color is not None:
                self.tabBar().setTabTextColor(
                    index, QtGui.QColor(caption_color)
                )
            if oper is not None:
                self.add_task(lambda: oper(widget))
            return widget
        else:
            if on_top:
                self.setCurrentWidget(widget)
            if oper is not None:
                self.add_task(lambda: oper(widget))
            return widget

    def get_tab_index(self, widget):
        for idx in range(self.count()):
            if id(self.widget(idx)) == id(widget):
                return idx
        return None

    def show_next(self):
        if self.count() > 1:
            index = self.currentIndex()
            if index + 1 < self.count():
                self.setCurrentIndex(index + 1)

    def show_prev(self):
        if self.count() > 1:
            index = self.currentIndex()
            if index > 0:
                self.setCurrentIndex(index - 1)

    def close_all_tabs(self):
        """
        关闭所有可以被关闭的标签页
        """
        idx = self.count() - 1
        while idx >= 0:
            succeed = self.close_tab(idx)
            if not succeed:
                print(f'failed to close tab {idx}')
            idx -= 1

    def _close_all_except(self, index):
        if 0 <= index < self.count():
            while self.count() > 1:
                if index > 0:
                    self.close_tab(0)
                    index -= 1
                else:
                    self.close_tab(1)
        else:
            self.close_all_tabs()

    def _rename_tab(self, index):
        if index < self.count():
            text, ok = QtWidgets.QInputDialog.getText(
                self, '重命名',
                '请输入新的名称:',
                text=self.tabText(index))
            if ok:
                self.setTabText(index, text)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.MiddleButton:  # 中间按钮关闭选项卡
            for i in range(self.count()):
                if self.tabBar().tabRect(i).contains(event.pos()):
                    self.close_tab(i)
        super().mousePressEvent(event)

    def get_figure_widget(self, init=None, folder_save=None, **kwargs):
        """
        返回一个用以 matplotlib 绘图的控件
        """
        from zmlx.ui.widget.plt import MatplotWidget
        kwargs.setdefault('icon', 'matplotlib')

        def init_x(widget):
            if callable(init):
                init(widget)
            if folder_save is not None:
                widget.set_save_folder(folder_save)

        return self.get_widget(the_type=MatplotWidget, init=init_x, **kwargs)

    def plot(
            self, kernel, *args, fname=None, dpi=None,
            caption=None, on_top=None, icon=None,
            clear=None,
            tight_layout=None,
            suptitle=None, folder_save=None,
            **kwargs
    ):
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
            folder_save: 自动保存图的文件夹

        Returns:
            None
        """
        if clear is None:  # 默认清除
            clear = True
        try:
            widget = self.get_figure_widget(
                caption=caption, on_top=on_top, icon=icon, folder_save=folder_save
            )

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
                    from zmlx.io.env import plt_export_dpi
                    dpi = plt_export_dpi.get_value()
                widget.savefig(fname=fname, dpi=dpi)

            return widget.figure  # 返回Figure对象，后续进一步处理
        except Exception as err:
            import zmlx.alg.sys as warnings
            warnings.warn(f'meet exception <{err}> when run <{kernel}>')
            return None
