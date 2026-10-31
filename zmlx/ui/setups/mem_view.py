"""变量浏览器（MemView — app_data.space 变量查看与过滤）+「显示 → 变量」菜单入口.

**本文件自含**：控件 :class:`MemView`、它依赖的**编辑器注册**（``app_data_edits`` /
``default_app_data_edit`` 两个 ``app_data`` 键）、菜单项「显示 → 变量」与命令
``gui.show_memory`` 都在这里。

⚠️ **2026-10-31 由 ``zmlx/ui/tabs/mem_view.py`` 搬到 ``setups/``**（原模块删除、
**不留垫片**），同时把原来挂在 ``MainWindow.show_memory`` 上的「开标签页」逻辑一并收进
本文件。控件本体与 ``setup_ui`` 的逻辑一字未改。

为什么在 ``setups/`` 而不是 ``tabs/`` 或插件
---------------------------------------------------

判据是 ``setups/AGENTS.md`` §1 那条：**关掉它，软件还能不能正常用？**

- **不能** —— 本模块的 ``setup_ui()`` 往 ``app_data`` 里放的是**全局的变量编辑能力**
  （``app_data_edits`` / ``default_app_data_edit``）：别的控件（如插件页、编辑器的双击
  编辑）靠它决定「双击一个变量时用什么编辑器」。做成插件就等于允许用户关掉这套能力，
  界面上会静默少掉一整类交互。
- 也**不该**待在 ``tabs/`` —— ``tabs/`` 收的是「只被装配层打开成页面的顶层控件」，
  而这里连带装着菜单项、命令与全局 ``app_data`` 键。

⚠️ 由 ``setups/__init__.py`` 的 ``setup_ui()`` 统一调用（那里是**唯一**的登记点）。

菜单与命令（**与搬迁前完全一致**）
----------------------------------

=========================  ==================================================
项                          值
=========================  ==================================================
菜单                        显示 → 变量（``name='memory'``、``icon='variables'``）
命令                        ``gui.show_memory()``
标签页                      标题「变量」，``gui_restore = 'gui.show_memory()'``
=========================  ==================================================

⚠️ **``gui.show_memory`` 这个名字不能改**：历史标签页的 ``gui_restore`` 存的就是它，
重启时按原文重放。⚠️ 菜单项原本在 ``main.py`` 的 ``__init_actions`` 里注册（与
「操作 → 刷新」等骨架条目同组），现在**整体搬到本文件**，``main.py`` 里那片注释会指到这里。
菜单的**位置**因此取决于 ``setups`` 与 ``main.py`` 的注册先后：本文件在
``MainWindow`` 构造之后才跑，所以「变量」排在「显示」菜单里骨架条目之后。

Created by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-31: 由 ``zmlx/ui/tabs/mem_view.py`` 搬到
    ``setups/mem_view.py``，并接管 ``MainWindow.show_memory``（开标签页）与
    「显示 → 变量」菜单项；原模块与 ``MainWindow`` 上的方法均删除、**不留垫片**。
"""

import timeit

from zmlx.algs.base import clamp
from zmlx.system import app_data, execute_once
from zmlx.ui import gui
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets

# 类型 → 字体颜色。已知类型预制颜色，未知类型用 hash 分配。
_TYPE_COLORS = {
    int: '#1565C0',  # 蓝
    float: '#2E7D32',  # 绿
    str: '#E65100',  # 橙
    bool: '#6A1B9A',  # 紫
    list: '#00838F',  # 青
    tuple: '#00695C',  # 深青
    dict: '#F9A825',  # 黄
    set: '#558B2F',  # 黄绿
    type(None): '#9E9E9E',  # 灰
    # 函数/方法
    'function': '#D84315',  # 深橙
    'method': '#BF360C',  # 红棕
    'builtin_function_or_method': '#BF360C',
    # 类的颜色（用字符串名来匹配，因为类可能不在当前命名空间）
    'Seepage': '#1B5E20',  # 深绿
    'SeepageMesh': '#0D47A1',  # 深蓝
    'FluDef': '#880E4F',  # 深粉
    'DynSys': '#4A148C',  # 深紫
}


def _get_type_fg(type_obj):
    """根据类型对象返回字体颜色 QColor，未知类型返回 None（默认颜色）。"""
    # 1. 精确类型匹配
    if type_obj in _TYPE_COLORS:
        return QtGui.QColor(_TYPE_COLORS[type_obj])

    type_name = type_obj.__name__

    # 2. 类名字符串匹配（预制的 Seepage 等）
    if type_name in _TYPE_COLORS:
        return QtGui.QColor(_TYPE_COLORS[type_name])

    # 3. 函数/方法类
    name_lower = type_name.lower()
    if 'function' in name_lower or 'method' in name_lower:
        return QtGui.QColor('#D84315')

    # 4. 未知类型：不设颜色，使用默认
    return None


class MemView(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        # ⚠️ parent 必须设为本控件：否则控件销毁后计时器仍 active，
        #    见 zmlx/ui/widget/AGENTS.md 的「计时器要设 parent」。
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(500)
        self.refresh()

        # 连接双击信号
        self.doubleClicked.connect(self.on_double_click)

        # 启用右键菜单
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        """
        显示右键菜单
        """
        index = self.indexAt(position)
        has_selection = index.isValid()

        menu = QtWidgets.QMenu(self)
        menu.addAction('刷新', self.refresh)
        if has_selection and index.column() == 1:
            menu.addAction('编辑', lambda: self.on_double_click(self.model().index(index.row(), 1)))
        if has_selection and index.column() == 0:
            menu.addAction('删除', lambda: self.delete_item(index))
        # 显示菜单
        menu.exec(self.mapToGlobal(position))

    def delete_item(self, index):
        if index.isValid():
            key = self.item(index.row(), 0).text()
            if key in app_data.space:
                reply = QtWidgets.QMessageBox.question(
                    self, '确认删除', f'是否删除变量 {key}？',
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
                if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                    del app_data.space[key]
                    self.refresh()

    def on_double_click(self, index):
        """
        双击单元格时执行的操作
        """
        if not index.isValid():
            return

        row = index.row()
        col = index.column()

        # 获取单元格内容
        item = self.item(row, col)
        if item is None:
            return

        if col == 1:  # 此时，尝试调用类型的编辑方法.
            key = self.item(row, 0).text()
            try:
                app_data_edits = app_data.get('app_data_edits')  # 获取编辑方法字典
                if isinstance(app_data_edits, dict):
                    value = app_data.get(key)
                    edit = app_data_edits.get(type(value).__name__)
                    if callable(edit):  # 找到了针对性的编辑器
                        try:
                            edit(key)
                        except Exception as e:
                            print(f"调用编辑方法(key={key}, edit={edit})时出错: {e}")
                    else:  # 没有针对性的编辑器，调用默认编辑器
                        default_app_data_edit = app_data.get('default_app_data_edit')
                        if callable(default_app_data_edit):
                            try:
                                default_app_data_edit(key)
                            except Exception as e:
                                print(f"调用编辑方法(key={key}, edit={default_app_data_edit})时出错: {e}")
            except Exception as err:
                print(err)

    def __refresh(self):
        names_ignored = app_data.get('names_ignored', None)
        if names_ignored is None:  # 初始化忽略列表
            space = {}
            exec('from zmlx import *', space)
            names_ignored = set(space.keys())
            for k in [
                'app_data_edits', 'names_ignored', 'console_result', 'setup_ui', 'ui_text', 'init_check', 'argv',
                'restore_tabs', 'env_items', 'sys_excepthook', 'console_exec_history', 'first_executed',
                'zipfile', 'dataname', 'execute_zip', 'execute_unzip', 'files_executed', 'get_vtk_view',
                'main_window', 'QtInteractor', 'gui_setup_logs'
            ]:
                names_ignored.add(k)
            app_data.put('names_ignored', names_ignored)
        data = []
        for key, value in app_data.space.items():
            if len(key) > 2:
                if key[0:2] == '__':
                    continue
            if key in names_ignored:
                continue
            data.append([key, f'{value}', type(value)])

        self.setRowCount(len(data))
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['名称', '值', '类型'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for i_row in range(len(data)):
            type_obj = data[i_row][2]
            fg = _get_type_fg(type_obj)
            for i_col in range(3):
                text = data[i_row][i_col] if i_col < 2 else type_obj.__name__
                item = QtWidgets.QTableWidgetItem(text)
                if fg is not None:
                    item.setForeground(fg)
                self.setItem(i_row, i_col, item)

    def refresh(self):
        """
        更新
        """
        if not self.isVisible():
            return
        cpu_t = timeit.default_timer()
        try:
            self.__refresh()
        except Exception as err:
            print(err)
            self.clear()
        cpu_t = timeit.default_timer() - cpu_t
        msec = clamp(int(cpu_t * 200 / 0.001), 200, 8000)
        self.timer.setInterval(msec)


def _register_app_data_edits():
    """把变量的编辑方法写进 ``app_data``（全局键，见模块文档）。

    ⚠️ 这些键是**全局能力**：别的控件靠 ``app_data.get('app_data_edits')`` 决定
    「双击一个变量时用什么编辑器」。本函数只做登记，不挂菜单。
    """
    def edit_int(key):
        from zmlx.ui import gui
        result, ok = gui.get_int(
            f"编辑变量{key}",
            "请输入整数:",
            app_data.get(key),  # 默认值
        )
        if ok:
            app_data.put(key, result)

    def edit_float(key):
        from zmlx.ui import gui
        result, ok = gui.get_double(
            f"编辑变量{key}",
            "请输入浮点数:",
            app_data.get(key),  # 默认值
        )
        if ok:
            app_data.put(key, result)

    def edit_str(key):
        from zmlx.ui import gui
        result, ok = gui.get_multi_line_text(
            f"编辑变量{key}",
            "请输入字符串:",
            app_data.get(key),  # 默认值
        )
        if ok:
            app_data.put(key, result)

    def edit_func(key):
        from zmlx.ui import gui
        gui.information('提示', f'变量 {key} 是函数，暂不支持编辑')

    # 注册编辑方法
    app_data_edits = app_data.get('app_data_edits')
    if not isinstance(app_data_edits, dict):
        app_data_edits = {}
    # 添加编辑方法
    app_data_edits['int'] = edit_int
    app_data_edits['float'] = edit_float
    app_data_edits['str'] = edit_str
    app_data_edits['function'] = edit_func
    app_data_edits['builtin_function_or_method'] = edit_func
    # 保存编辑方法字典
    app_data.put('app_data_edits', app_data_edits)

    def default_app_data_edit(key):
        from zmlx.ui.alg import edit_in_tab
        from zmlx.ui.widgets.edit_by_text import ObjEditByText
        def set_data(value):
            app_data.put(key, value)

        def get_data():
            return app_data.get(key)

        edit_in_tab(ObjEditByText, set_data=set_data, get_data=get_data, caption=f'编辑变量{key}',
                    support_refresh=False)

    # 添加默认的编辑器
    app_data.put('default_app_data_edit', default_app_data_edit)


def show_memory():
    """打开（或切到）「变量」标签页；同时也是 GUI 命令 ``gui.show_memory()``.

    ⚠️ 由 ``MainWindow.show_memory`` **原样搬来**（2026-10-31）：那时它靠「主窗口的公开
    方法被自动注册成 ``gui.xxx``」来提供命令；方法搬走后那条链断了，所以本文件的
    :func:`setup_ui` 用 ``gui.add_func('show_memory', show_memory)`` 显式补上。

    ⚠️ 走 ``gui.get_widget``（按「类型 + 标题」复用）：重复点击只是把已有页面切到前面，
    不会越开越多。``oper`` 里同时 ``refresh()``（切过去就能看到最新变量）并记下
    ``gui_restore``（重启后按原文恢复标签页）。
    """
    def oper(w):
        w.refresh()
        w.gui_restore = 'gui.show_memory()'

    gui.get_widget(
        the_type=MemView, caption="变量", on_top=True, icon="variables", oper=oper
    )


@execute_once(file=__file__)
def setup_ui():
    """注册编辑器 + 「显示 → 变量」菜单项 + ``gui.show_memory``.

    由 ``setups/__init__.py`` 的 ``setup_ui()`` 调用（唯一登记点）；
    ``@execute_once`` 保证重复调用也不会挂出第二条菜单。
    """
    # 1. 变量的编辑方法（全局 app_data 键，别的控件也靠它）
    _register_app_data_edits()

    # 2. 命令：菜单项与 gui.show_memory() 指向**同一个**函数
    #    ⚠️ 必须显式注册：原先靠 MainWindow 的「公开方法自动注册」，方法搬走后那条链断了。
    gui.add_func('show_memory', show_memory)

    # 3. 菜单「显示 → 变量」。⚠️ name 仍是 'memory'、图标仍是 'variables'、文字仍是「变量」
    #    —— 它们是 ribbon 配置与已保存界面布局的定位依据，一个字都不能改。
    gui.add_action(
        menu="显示",
        name="memory",
        icon="variables",
        text="变量",
        slot=show_memory,
        overwrite=False,
    )
