"""标签页容器（TabWidget — 标签管理、查找、绘图路由）.

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-09-14

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.system import app_data
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
            # ⚠️ 「列出标签」（``gui.show_tab_details``）2026-10-22 起由插件
            #    ``plugins/builtin/viewers.py`` 提供；插件被禁用时由
            #    ``extra_setups/plugin_placeholders.py`` 的**占位**顶上（只打印提示）。
            #    这里仍按命令存在性决定要不要加这一项 —— 菜单项点了要「开标签页」，
            #    给一条只会打印提示的菜单项没有意义。
            if gui.get_func('show_tab_details') is not None:
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
        """关闭第 ``index`` 个标签页（``tabCloseRequested`` 与右键菜单都走这里）.

        **销毁控件之前，本方法给控件两次「清理」机会**（都是 duck-typing 探测，控件按需实现）：

        1. :meth:`__try_save` —— **持久化**：定义了 ``save_file`` 就调它；定义了
           ``need_save`` 就先问一句「有东西要存吗」，为假则整体跳过。
           ⚠️ 这对接口**不限于关标签**：菜单「文件 → 保存」也用它，所以控件内部
           **不要**假设自己一定是在被关闭。
        2. :meth:`__try_cleanup` —— **其余收尾**：调 ``cleanup_before_tab_close()``，
           让控件放掉后台线程的引用、复位忙碌状态等。

        ⚠️ **第 2 步的名字里带 ``tab_close`` 是有意为之**：它**只在控件作为标签页被关闭时**
        才会被调用。同一个控件若被用在别处（对话框、普通子控件……）就**不会被调用** ——
        那些场合需要自己收尾。

        ⚠️ **本方法用 ``deleteLater()`` 销毁控件，所以 ``closeEvent`` 不会被触发**
        （那是 ``close()`` 才发的）。控件里为「关闭」写的 ``closeEvent`` 在这条路径上是
        **死代码**（``license_register`` / ``check_count_view`` / ``feedback_tool`` 都写了，
        但点标签页的关闭按钮时一次都不会执行）—— 要在关闭前做点什么，只能用上面两个钩子。

        ⚠️ **两个钩子都必须快、都不许阻塞**（尤其别 ``wait()``）：关标签路径上界面正等着，
        而联网请求最长 60 秒。后台线程的存活要靠控件自己那两条纪律保证（见
        :meth:`__try_cleanup`），不能靠在这里等它结束。

        Args:
            index: 标签页下标。

        Returns:
            bool: 关闭成功返回 True；不可关闭或下标越界返回 False。
        """
        if index < self.count():
            widget = self.widget(index)
            if (closeable := getattr(widget, 'tab_closeable', None)) or closeable is None:
                self.__try_save(widget)
                self.__try_cleanup(widget)
                widget.deleteLater()
                self.removeTab(index)
                return True
            else:
                return False
        else:
            return False

    @staticmethod
    def __try_cleanup(widget):
        """销毁前调 ``cleanup_before_tab_close()``：让控件做**非持久化**的收尾.

        它与 :meth:`__try_save` 是同一个概念（「销毁前清理」）的两半：那个管**存数据**，
        这个管**放资源 / 复位状态** —— 例如清掉对后台线程的引用、把 ``_busy`` 复位
        （否则控件若被复显会带着「按钮全禁用」回来）。

        ⚠️ **本钩子不是崩溃防线** —— 这点实测过，写在这里免得误传：

        ``close_tab`` 用 ``deleteLater()`` 销毁控件，控件（连同**子对象**）会在事件循环
        下一轮被真正 ``delete``。**崩溃的真正成因**是控件把 :class:`QtCore.QThread` 的
        **parent 设成了自己**，线程于是跟着被析构；而 Qt 规定「正在运行的 QThread 不能被
        销毁」，线程还没跑完（联网最长 60 秒）时进程直接 abort::

            QThread: Destroyed while thread is still running

        这是**进程级崩溃**，不是异常，Python 侧 try/except 兜不住。**解法是「线程不设
        parent + 用模块级强引用持有它」**：``demo_view.py`` 的 ``_RUNNING`` 就是这么做的，
        它**没有** ``cleanup_before_tab_close`` 也从不崩。实测两种组合：把本钩子改成空操作，
        在慢查询进行中关标签页**依然安全**；反过来把线程 parent 回控件，**即使本钩子存在
        也照样崩**。所以线程的存活必须靠那两条纪律自己保证，别指望这里的收尾。

        ⚠️ **契约是「摘引用」而不是「等待」**：钩子里只清引用，**绝不要 ``wait()``** ——
        同步等 60 秒会把「关标签」这件本该瞬间完成的事变成冻结界面。控件销毁后 Qt 会自动
        断开绑定方法的信号连接，迟到结果被安全丢弃（lambda 连的槽除外，见
        ``check_count_view.py`` 的 ``_is_deleted``）。

        ⚠️ 钩子自身出错也不能阻断关闭流程（否则控件会关不掉），只打印出来。
        没定义这个方法的控件行为不变。

        Args:
            widget: 即将被关闭的标签页控件。
        """
        cleanup = getattr(widget, 'cleanup_before_tab_close', None)
        if not callable(cleanup):
            return
        try:
            cleanup()
        except Exception as e:
            # 收尾失败不该让标签页关不掉：报出来即可（属于控件自身的实现问题，
            # 不该由 TabWidget 兜底成「关不掉」）。
            print(f'Error: {e}')

    @staticmethod
    def __try_save(widget):
        """关闭标签页之前，给控件一次保存的机会.

        只做两件事：控件若定义了 ``save_file`` 就调它；控件若还定义了
        ``need_save``，则**先问一句「有东西要存吗」**，为假就整体跳过。

        ⚠️ **为什么要问 ``need_save``**：关闭标签页是用户想「关掉」，
        不是想「保存」。那些没有未保存内容的控件（例如刚提交完、输入框已清空的
        反馈页）如果照样被调 ``save_file``，就会弹出「保存到哪个文件」的对话框，
        或者写下一个空文件 —— 用户被迫回答一个毫无意义的问题。
        ``need_save`` 正是控件表达「我现在有没有东西要存」的接口（菜单也用它
        决定「保存」项的灰/亮），所以这里复用它，语义一致。

        ⚠️ 没定义 ``need_save`` 的控件**行为不变**（仍然直接调 ``save_file``）：
        那是历史行为，很多控件依赖它来「关闭时落盘」，不能一刀切地改成默认不存。

        Args:
            widget: 即将被关闭的标签页控件。
        """
        save = getattr(widget, 'save_file', None)
        if not callable(save):
            return
        need = getattr(widget, 'need_save', None)
        if callable(need):
            try:
                if not need():
                    return      # 没有要保存的内容：静默跳过
            except Exception as e:
                # 判空自己出错时按「有内容」处理：宁可多问一次，也别悄悄丢数据
                print(e)
        try:
            save()
        except Exception as e:
            print(e)

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
        if not isinstance(caption, str):
            caption = 'untitled'
        if len(caption) == 0:
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
            if on_top is None or on_top:
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
        from zmlx.ui.widgets.plt import MatplotWidget
        kwargs.setdefault('icon', 'matplotlib')

        def init_x(widget):
            if callable(init):
                init(widget)
            if folder_save is not None:
                widget.set_save_folder(folder_save)

        return self.get_widget(the_type=MatplotWidget, init=init_x, **kwargs)

    @staticmethod
    def make_on_figure(kernel, args=(), kwargs=None, *, clear=True,
                       suptitle=None, tight_layout=None):
        """把「清屏 + 回调 + 标题 + tight_layout」包成一个只吃 figure 的函数.

        ⚠️ **纯 Python，不含任何 Qt 调用** —— 它会在**发起绘图的那个线程**里执行
        （``GuiBuffer.plot`` 会把它交给计算内核线程跑），所以这里不许碰任何控件。

        Args:
            kernel: 用户回调 ``kernel(figure, *args, **kwargs)``
            args: 传给 kernel 的位置参数
            kwargs: 传给 kernel 的关键字参数
            clear: 是否先 ``figure.clear()``
            suptitle: 图表的总标题
            tight_layout: 是否 ``figure.tight_layout()``（dict 则作为参数）

        Returns:
            Callable[[Figure], None]: 包装后的回调
        """
        extra = dict(kwargs) if kwargs else {}

        def on_figure(figure):
            if clear:  # 清除
                figure.clear()
            if callable(kernel):
                try:
                    kernel(figure, *args, **extra)  # 这里，并不会传入clear参数
                except Exception as kernel_err:
                    print(kernel_err)
            if isinstance(suptitle, str):
                figure.suptitle(suptitle)
            if tight_layout:
                if isinstance(tight_layout, dict):
                    figure.tight_layout(**tight_layout)
                else:
                    figure.tight_layout()

        return on_figure

    def plot(
            self, kernel, *args, fname=None, dpi=None,
            caption=None, on_top=None, icon=None,
            clear=None,
            tight_layout=None,
            suptitle=None,
            folder_save=None,
            savefig=None,
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
            savefig: 是否自动保存图(bool, 或者文件名)

        Returns:
            None
        """
        if clear is None:  # 默认清除
            clear = True
        try:
            from zmlx.ui.widgets.plt import MatplotWidget
            widget = self.get_figure_widget(
                caption=caption, on_top=on_top, icon=icon, folder_save=folder_save
            )
            assert isinstance(widget, MatplotWidget)

            on_figure = self.make_on_figure(
                kernel, args, kwargs, clear=clear,
                suptitle=suptitle, tight_layout=tight_layout)

            if fname is not None:
                savefig = False  # 不自动保存图
            widget.plot_on_figure(on_figure=on_figure, savefig=savefig)
            if fname is not None:
                if dpi is None:
                    from zmlx.io.env import plt_export_dpi
                    dpi = plt_export_dpi.get_value()
                widget.savefig(fname=fname, dpi=dpi)

            return widget.figure  # 返回Figure对象，后续进一步处理
        except Exception as err:
            import zmlx.algs.sys as warnings
            warn(f'meet exception <{err}> when run <{kernel}>')
            return None
