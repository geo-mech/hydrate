# ** name = '小型查看器'
# ** desc = '四个小标签页入口：耗时（TimerView）、浏览→工作目录（CwdView）、标签列表（TabDetailView）、路径（AppPathEdit）'
# ** enabled = True
"""小型查看器插件：四个「show_xxx + 专属控件」组合收进一个文件.

⚠️ **它们是插件（可关闭）**：这四个入口原先都以 ``MainWindow`` 公开方法的形式常驻在
界面骨架里。它们的共同点是 —— **每个方法只做一件事：把某个小控件开成标签页**，
而那个控件**只有它自己用**。按 ``plugins/AGENTS.md`` §0.2 收成「完全自含」：
禁用本插件时连这些控件代码一起不加载。

============================  =================  ========  ==========================
命令                           控件               原行数     原菜单（在 __init_actions）
============================  =================  ========  ==========================
``gui.show_timer``             ``TimerView``        92       显示 → 耗时
``gui.view_cwd``               ``CwdView``          87       文件 → 浏览 → 工作目录
``gui.show_tab_details``       ``TabDetailView``   158       显示 → 标签列表
``gui.show_file_finder``       ``AppPathEdit``      43       设置 → 路径
============================  =================  ========  ==========================

⚠️ 2026-10-26：「浏览」那一项从「文件 → 浏览」下沉到**子菜单**「文件 → 浏览 → 工作目录」，
与「图片」（插件 ``image_browser``）并列 —— 两者都是「看文件」的入口。子菜单由
``MainWindow.get_menu`` 按标题缺则新建，两个插件谁先加载都能合并进**同一个**子菜单，
互不依赖；子菜单**在「文件」里的位置**由 ``get_menu`` 统一决定（插在第一个普通条目
之前），不受插件加载顺序影响。

⚠️⚠️ **下面四个控件的类定义是从原文件原样搬来的，没有改动一个字符**（只去掉了各自
的模块级 docstring —— 内容已汇总到本头部）。改它们请回看本文件的历史，不要以为这是
新写的简化版。

⚠️ **四个命令名都不能改**：历史标签页的 ``gui_restore`` 里存的就是
``gui.show_timer()`` / ``gui.view_cwd()`` / ``gui.show_tab_details()`` /
``gui.show_file_finder()``，重启时按原文重放。它们原先靠 ``MainWindow`` 的
「所有公开方法自动注册」当上 ``gui.xxx``，方法一搬走就得在这里**显式**
``gui.add_func`` 补回来。

⚠️ **为什么四个放一个文件**：它们各自都很小（合计约 440 行），且都是「开一个小标签页」
这一类。分成四个插件文件，用户就要在「设置 → 插件」里管四行 —— 收益不抵麻烦。
这与 ``plugins/AGENTS.md`` §1 的「一个目录只能有一个 ``zml_plugin.py``」同一思路：
**几个自含模块想共享一个开关，就放同一个入口下**。

⚠️ ``show_tab_details`` 有个别的入口没有的依赖：它要 ``MainWindow`` 的两个标签容器
（顶部 / 右侧）才能构造 ``TabDetailView.TabWrapper``。插件**不能**持有 ``MainWindow``，
所以改用 ``gui.get_tab_widgets()`` —— 那是 ``MainWindow`` 的**公开方法**，自动注册成
命令，返回 ``[top_tabs, right_tabs]``。⚠️ 这意味着：**这个入口依赖 ``MainWindow``
仍然提供 ``get_tab_widgets()``**（它是骨架能力，不该被搬走）。

Created by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-22: ``MainWindow`` 的四个 ``show_xxx`` 方法、
    ``ui/tabs/{timer_view,cwd_view,tab_detail_view,app_path_edit}.py`` 与
    ``__init_actions`` 里对应的四条 ``add_action`` 全部并入本插件
Modified by DeepSeek, 2026-10-26: 「浏览」改挂到「文件 → 浏览 → 工作目录」（与
    ``image_browser`` 的「图片」合成子菜单）；命令名 / action name / Ctrl+B 均未变
"""

import timeit

from zmlx.system import execute_once
from zmlx.algs.base import time2str, clamp
from zmlx.exts import make_parent, timer
from zmlx.ui.pyqt import QtCore, QtWidgets
import os
import time
from zmlx.algs.base import fsize2str, clamp
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtWidgets


class TimerView(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

        self._sort_col = 0       # 当前排序的列
        self._sort_asc = True    # True=升序，False=降序

        # ⚠️ 计时器要把 parent 设为本控件（见 zmlx/ui/widget/AGENTS.md）：
        #    不设 parent 时控件销毁后计时器仍处于 active 状态、还在往已断开的
        #    连接上发信号，要等循环 GC 拆掉 timer→绑定方法→self 的环才被回收，
        #    等于每个关掉的标签页都留一个 500ms 的空转唤醒。
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(500)
        self.refresh()

    def _on_header_clicked(self, col):
        """点击列标题时切换排序方式。"""
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc  # 同列 → 切换升降序
        else:
            self._sort_col = col
            self._sort_asc = True  # 换列 → 默认升序
        self.refresh()

    def export_data(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, '导出Timer',
            '',
            f'Text File(*.txt)')
        with open(make_parent(fpath), 'w', encoding='utf-8') as file:
            for key, val in timer.key2nt.items():
                n, t = val
                file.write(f'{key}\t{n}\t{t}\n')

    def refresh(self):
        """
        更新
        """
        if not self.isVisible():
            return

        cpu_t = timeit.default_timer()

        data = []
        for key, nt in timer.key2nt.items():
            n, t = nt
            data.append([f'{key}', n, t, t / n])

        # 按当前排序列排序
        reverse = not self._sort_asc
        data.sort(key=lambda row: row[self._sort_col], reverse=reverse)

        # 格式化显示（排序在原始值上进行，此处转为字符串）
        for row in data:
            row[1] = f'{row[1]}'             # 调用次数
            row[2] = time2str(row[2])        # 总耗时
            row[3] = time2str(row[3])        # 单次耗时

        self.setRowCount(len(data))
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(
            ['名称', '调用次数', '总耗时', '单次耗时'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for i_row in range(len(data)):
            for i_col in range(4):
                self.setItem(
                    i_row, i_col,
                    QtWidgets.QTableWidgetItem(data[i_row][i_col]))

        cpu_t = timeit.default_timer() - cpu_t
        msec = clamp(int(cpu_t * 200 / 0.001), 200, 8000)
        self.timer.setInterval(msec)

# ===========================================================================
class CwdView(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super(CwdView, self).__init__(parent)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        self.clicked.connect(self.item_clicked)
        self.doubleClicked.connect(self.item_double_clicked)
        # ⚠️ parent 必须设为本控件：否则控件销毁后计时器仍 active，
        #    见 zmlx/ui/widget/AGENTS.md 的「计时器要设 parent」。
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(500)
        self.refresh()

    def __refresh(self):
        folder = os.getcwd()
        data = [['..', '文件夹', '', ''], ]
        try:
            names = os.listdir(folder)
        except Exception as err:
            print(err)
            names = []
        for name in names:
            path = os.path.join(folder, name)
            try:
                if os.path.isfile(path):
                    data.append([name, '文件', fsize2str(os.path.getsize(path)),
                                 f'{time.ctime(os.path.getmtime(path))}'])
                    continue

                if os.path.isdir(path):
                    data.append([name, '文件夹', '', ''])
                    continue
            except Exception as err:
                print(err)
        self.setRowCount(len(data))
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(['名称', '类型', '大小', '修改时间'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        for i_row in range(len(data)):
            for i_col in range(4):
                self.setItem(i_row, i_col,
                             QtWidgets.QTableWidgetItem(data[i_row][i_col]))

    def refresh(self):
        cpu_t = timeit.default_timer()
        #
        try:
            self.__refresh()
        except Exception as err:
            print(err)
            self.clear()
        #
        cpu_t = timeit.default_timer() - cpu_t
        msec = clamp(int(cpu_t * 200 / 0.001), 200, 8000)
        self.timer.setInterval(msec)

    def item_clicked(self, index):
        if index.column() != 0:
            return
        item = self.item(index.row(), index.column())
        text = item.text()
        if text == '..':
            fpath = os.path.dirname(os.getcwd())
        else:
            fpath = os.path.join(os.getcwd(), text)

        if os.path.isfile(fpath):
            ext = os.path.splitext(fpath)[-1]
            if ext is not None:
                if ext.lower() == '.py' or ext.lower() == '.pyw':
                    gui.open_code(fpath)

    def item_double_clicked(self, index):
        if index.column() != 0:
            return
        item = self.item(index.row(), index.column())
        text = item.text()
        if text == '..':
            fpath = os.path.dirname(os.getcwd())
        else:
            fpath = os.path.join(os.getcwd(), text)
        gui.open_file(fpath)

# ===========================================================================
class TabDetailView(QtWidgets.QTableWidget):
    #: 可见时的自动刷新间隔（毫秒）。1 秒足够「跟得上」，而一次刷新的成本只是
    #: 遍历几个标签（标签数通常个位数），不会成为负担。
    REFRESH_INTERVAL_MS = 1000

    class TabWrapper:
        def __init__(self, *tab_widgets):
            self.tab_widgets = tab_widgets

        def count(self):
            return sum([w.count() for w in self.tab_widgets])

        def get(self, index):
            for widget_idx in range(len(self.tab_widgets)):
                widget = self.tab_widgets[widget_idx]
                if index < widget.count():
                    return widget.tabText(index), type(widget.widget(index)).__name__
                else:
                    index -= widget.count()
            return "", ""

        def remove(self, index):
            for widget_idx in range(len(self.tab_widgets)):
                widget = self.tab_widgets[widget_idx]
                if index < widget.count():
                    widget.close_tab(index)
                    break
                else:
                    index -= widget.count()

        def show(self, index):
            for widget_idx in range(len(self.tab_widgets)):
                widget = self.tab_widgets[widget_idx]
                if index < widget.count():
                    if not widget.isVisible():
                        widget.setVisible(True)
                    widget.setCurrentIndex(index)
                    break
                else:
                    index -= widget.count()

    def __init__(self, parent=None, obj=None, header_labels=None):
        super().__init__(parent)
        self.header_labels = header_labels
        self.obj = obj
        #: 定时刷新用的计时器（**只在控件可见时运行**，见 :meth:`showEvent`）
        self._timer = None
        self._init_ui()
        self._connect_signals()
        self.refresh()

    def _init_ui(self):
        self.setColumnCount(3)
        if self.header_labels is not None:
            assert len(self.header_labels) == 3
            self.setHorizontalHeaderLabels(
                self.header_labels)
        else:
            self.setHorizontalHeaderLabels(['标题', '类型', '操作'])
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(True)
        self.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu)  # 启用右键菜单
        # ⚠️ **整张表禁止就地编辑**（这里只是「已打开标签页」的清单，没有可编辑项）。
        #    Qt 的默认触发器是 ``DoubleClicked|EditKeyPressed|AnyKeyPressed``，
        #    于是双击任一单元格会当场弹出**行内编辑器**；而在 WSLg 下，编辑器还
        #    开着时再双击**另一个**单元格会让 Qt 在 C++ 层直接**段错误**
        #    （不是异常，Python 侧兜不住，表现就是「整个软件卡死」）。
        #    这一处比「关于」页更危险：它本来是双击就该「切到那个标签页」的，
        #    双击反而弹出编辑器已经不对，再双击一次就直接崩。
        #    ``setEditTriggers`` 是总闸；:meth:`refresh` 里建单元格时还会清掉
        #    ``ItemIsEditable`` 标志（双保险）。
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

    def _connect_signals(self):
        self.cellClicked.connect(self._on_cell_clicked)
        self.customContextMenuRequested.connect(
            self._show_context_menu)  # 右键菜单信号

    def showEvent(self, event):
        """显示时：立刻刷新一次，并**开始每秒定时刷新**（主线程调用）.

        ⚠️ **为什么要自己定时刷**：主窗口那条刷新链到不了本控件 ——
        ``MainWindow.refresh`` 只刷新 ``get_current_widget()``（**顶部**栏的当前页），
        而本控件是 ``show_tab_details`` 用 ``position="right"`` 开在**右侧**栏的；
        所以切标签页 / 菜单「操作 → 刷新」都不会调到 :meth:`refresh`，
        列表会一直停在打开那一刻的内容（实测：在别处新开标签页，行数纹丝不动）。

        本控件是「已打开标签页」的总览，**内容随时会被别处改掉**，所以用定时器
        每秒对齐一次 —— 比去接各个 ``TabWidget`` 的增删信号简单得多，也不会漏掉
        「重命名 / 换位置」这类不增删的变化。

        ⚠️ **只在可见时跑**（``hideEvent`` 里停）：切走后还在刷就是白烧 CPU，
        而且用户看不见。

        ⚠️ 计时器的 parent 是本控件，所以它随控件一起销毁 —— 不会像线程那样
        在关标签页时把进程带崩（见 ``widget/AGENTS.md`` 的线程生命周期那节）。
        """
        super().showEvent(event)
        self.refresh()
        self._start_timer()

    def hideEvent(self, event):
        """隐藏时停掉定时刷新（控件不可见就没必要刷了）."""
        self._stop_timer()
        super().hideEvent(event)

    def _start_timer(self):
        """开始每秒刷新（重复调用无副作用）"""
        if self._timer is None:
            self._timer = QtCore.QTimer(self)
            self._timer.setInterval(TabDetailView.REFRESH_INTERVAL_MS)
            self._timer.timeout.connect(self.refresh)
        self._timer.start()

    def _stop_timer(self):
        """停止定时刷新（没有计时器时什么都不做）"""
        if self._timer is not None:
            self._timer.stop()

    def refresh(self):
        if (not hasattr(self.obj, 'count')
                or not hasattr(self.obj, 'get')
                or not hasattr(self.obj, 'remove')
                or not hasattr(self.obj, 'show')):
            return
        row_count = self.obj.count()
        self.setRowCount(row_count)

        for row in range(row_count):
            value, name = self.obj.get(row)
            # 数值列（直接显示值）；⚠️ 用只读单元格，见 _init_ui 的说明
            self.setItem(row, 0, self._make_item(str(value)))
            # 类型列（使用type获取类型）
            self.setItem(row, 1, self._make_item(name))
            # 删除按钮
            btn = QtWidgets.QToolButton(self)
            btn.setText('x')
            btn.clicked.connect(lambda _, r=row: self._handle_delete(r))
            self.setCellWidget(row, 2, btn)

    @staticmethod
    def _make_item(text):
        """造一个**只读**单元格（清掉 Qt 默认给的 ``ItemIsEditable`` 标志）.

        ``QTableWidgetItem`` 默认带 ``ItemIsEditable``，这正是「双击单元格会弹出
        编辑器」的直接原因（触发器见 :meth:`_init_ui` 的 ``setEditTriggers``）。
        本表全是只读信息，所以逐项清掉这个标志 —— 与 ``NoEditTriggers`` 互为
        双保险。保留其它标志（可选中 / 启用），只去掉可编辑。

        Args:
            text: 单元格文本。

        Returns:
            QtWidgets.QTableWidgetItem: 只读单元格。
        """
        item = QtWidgets.QTableWidgetItem(text)
        item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        return item

    def _handle_delete(self, row):
        self.obj.remove(row)
        self.refresh()

    def _on_cell_clicked(self, row, column):
        if column in (0, 1):
            self.obj.show(row)

    def _show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        refresh_action = menu.addAction("刷新表格")
        refresh_action.triggered.connect(self.refresh)
        menu.exec(self.viewport().mapToGlobal(pos))

# ===========================================================================
class AppPathEdit(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel(self)
        label.setText('请在此输入文件名: ')
        layout.addWidget(label)

        self.fname_edit = QtWidgets.QLineEdit(self)
        self.fname_edit.textChanged.connect(self.update_files)
        layout.addWidget(self.fname_edit)

        label = QtWidgets.QLabel(self)
        label.setText('完整路径如下: ')
        layout.addWidget(label)

        self.output = QtWidgets.QTextBrowser(self)
        layout.addWidget(self.output)

        button = QtWidgets.QPushButton(self)
        button.setText('添加搜索路径')
        button.clicked.connect(self.add_path)
        layout.addWidget(button)

        self.update_files()

    def update_files(self):
        from zmlx.system import app_data
        filename = self.fname_edit.text()
        if len(filename) == 0:
            text = ''
            for path in app_data.get_paths():
                text = text + path + '\n'
            self.output.setPlainText(text)
            return
        results = app_data.find_all(filename)
        if len(results) == 0:
            self.output.setPlainText('未找到')
            return
        else:
            self.output.setPlainText('\n'.join(results))

    @staticmethod
    def add_path():
        from zmlx.algs.search_paths import choose_path
        choose_path()


# ===========================================================================
# 四个入口
# ===========================================================================

def show_timer():
    """显示（或切到）「耗时」标签页 —— 各函数的 CPU 耗时统计.

    ⚠️ **命令名不能改**（历史标签页存的就是 ``gui.show_timer()``）。
    """
    from zmlx.ui import gui

    def oper(w):
        w.refresh()
        w.gui_restore = 'gui.show_timer()'

    gui.get_widget(
        the_type=TimerView, caption='耗时', on_top=True, icon='clock', oper=oper)


def view_cwd():
    """显示（或切到）「浏览」标签页 —— 当前工作目录的文件列表.

    菜单入口是「文件 → 浏览 → 工作目录」（2026-10-26 起收进子菜单），但标签页标题
    **仍是「浏览」**：``get_widget`` 按「类型 + 标题」复用，标题一改就会多出一页；
    标签列表 / ``gui_restore`` 里记着的也是这一页。

    ⚠️ **命令名不能改**（历史标签页存的就是 ``gui.view_cwd()``）。
    """
    from zmlx.ui import gui

    def oper(w):
        w.refresh()
        w.gui_restore = 'gui.view_cwd()'

    gui.get_widget(
        the_type=CwdView, caption='浏览', on_top=True, oper=oper, icon='cwd')


def show_tab_details():
    """显示（或切到）「标签列表」标签页 —— 开在**右侧栏**.

    ⚠️ 标签容器要问 ``gui`` 拿（``MainWindow.get_tab_widgets()`` 自动注册成的命令，
    返回 ``[top_tabs, right_tabs]``）—— 插件**不能**持有 ``MainWindow``。
    """
    from zmlx.ui import gui

    tab_widgets = gui.get_tab_widgets()

    def oper(w):
        w.gui_restore = 'gui.show_tab_details()'

    # ⚠️ 参数名 `obj`（真件的 `__init__(self, parent=None, obj=None,
    #    header_labels=None)`）—— 与原 main.py 里那行**逐字一致**：
    #    外面用 `TabDetailView.TabWrapper(*标签容器)` 包好再传进去。
    gui.get_widget(
        the_type=TabDetailView,
        caption='标签列表',
        on_top=True,
        type_kw={'obj': TabDetailView.TabWrapper(*tab_widgets)},
        oper=oper,
        position='right',
    )


def show_file_finder():
    """显示（或切到）「路径」标签页 —— 按文件名查找完整路径.

    ⚠️ **命令名不能改**（历史标签页存的就是 ``gui.show_file_finder()``）。
    """
    from zmlx.ui import gui

    # ⚠️ `AppPathEdit` 是「输入文件名 → 显示完整路径」的查找器，
    #    **没有** `set_path()`；原来（main.py 里）的 oper 也只设 `gui_restore`。
    def oper(w):
        w.gui_restore = 'gui.show_file_finder()' 

    gui.get_widget(
        the_type=AppPathEdit, caption='路径', on_top=True, icon='set', oper=oper)


@execute_once(file=__file__)
def setup_ui():
    """注册四个命令与四条菜单项（插件被执行时调一次）.

    ⚠️ 菜单标题与 ``main.py`` 里那几处**逐字一致**（``'文件'`` / ``'显示'`` / ``'设置'``），
    否则 ``get_menu`` 会另建一个同名的新顶层菜单，界面上出现两个同名菜单。
    ⚠️ ``name=`` 沿用 ``main.py`` 时期的原文（``view_cwd`` / ``timer`` /
    ``tab_details`` / ``search``）—— 它们是 action 的内部名，改了可能影响别处的查找。
    """
    from zmlx.ui import gui

    gui.add_func('show_timer', show_timer)
    gui.add_func('view_cwd', view_cwd)
    gui.add_func('show_tab_details', show_tab_details)
    gui.add_func('show_file_finder', show_file_finder)

    # ⚠️ 参数与原 main.py __init_actions 里那四条**逐字一致**（含 shortcut / tooltip）：
    #    `Ctrl+B` 是「浏览」的历史快捷键，丢了就是用户肌肉记忆失效。
    # ⚠️ 2026-10-26：菜单路径 ``'文件'`` → ``['文件', '浏览']``（与「图片」合成子菜单），
    #    菜单文字 ``'浏览'`` → ``'工作目录'``；``name='view_cwd'``、命令名与快捷键
    #    ``Ctrl+B`` **都不变**。
    #
    # ⚠️ **子菜单建在「文件」的哪个位置不用本插件管**：``MainWindow.get_menu`` 把新子菜单
    #    插在**第一个普通条目之前**（即紧跟「文件」已有的固有条目），所以子菜单落在哪里
    #    只由「文件」自身决定，与两个插件谁先加载无关。
    # ⚠️ 但**子菜单里的条目顺序**仍取决于登记先后：``builtin/`` 按**文件名**排，
    #    ``image_browser.py``（i）先于本文件（v）⇒ 默认界面里「图片」在「工作目录」之前。
    gui.add_action(
        menu=['文件', '浏览'], name='view_cwd',
        icon='cwd',
        text='工作目录',
        shortcut='Ctrl+B',
        slot=view_cwd,
    )
    gui.add_action(
        menu='显示', name='timer',
        icon='clock',
        tooltip='显示cpu耗时统计的结果',
        text='耗时',
        slot=show_timer,
    )
    gui.add_action(
        menu='显示', name='tab_details',
        tooltip='列出已经打开的标签页（可以切过去或关掉），等同于标签栏右键的「列出标签」',
        text='标签列表',
        slot=show_tab_details,
    )
    gui.add_action(
        menu='设置', name='search',
        icon='set',
        text='路径',
        slot=show_file_finder,
    )


# ⚠️ 插件路径：由 load_all exec 执行，**没人会替我们调 setup_ui()**，所以本文件
#    把调用写在**模块顶层**的这个分支里（``setups/*.py`` 则由
#    ``setups/__init__.py`` 统一调用 —— 这是两者唯一的区别）。
#    插件机制执行时 ``__name__`` 是 ``'__zml_plugin__'``；直接 ``python viewers.py``
#    时才是 ``'__main__'``（见 plugins/__init__.py 的说明）。
if __name__ == '__zml_plugin__':
    setup_ui()
