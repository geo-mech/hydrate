"""通用字符串表格控件（``StringTable``）+ 命令 ``gui.show_string_table``.

**本文件自含**：控件 :class:`StringTable` 与「开标签页」的入口 :func:`show_string_table`
都在这里。

⚠️ **2026-10-31 由 ``zmlx/ui/tabs/string_table.py`` 搬到 ``setups/``**（原模块删除、
**不留垫片**），同时把 `MainWindow.show_string_table` 的方法体原样搬成模块级函数。
控件本体一字未改。

为什么在 ``setups/`` 而不是 ``tabs/``
------------------------------------

判据是 ``setups/AGENTS.md`` §1 那条：**关掉它，软件还能不能正常用？**

- ``gui.show_string_table`` 是一个**通用的「把一堆字符串丢进表格窗口看」的出口**，
  被**插件**与 **scen** 直接调用：``plugins/builtin/admin_menu.py``（4 处：命令列表 /
  Action 列表 / 运行日志 / 系统路径）与 ``scen/ai_assistant/action.py``。
  做成插件的话，关掉它这些调用方就会报「找不到命令」。
- 它也不只是「被装配层打开成页面的顶层控件」：入口带**参数**（``data`` / ``caption`` /
  ``data_columns``）、要写 ``gui_restore``、**还返回那个 widget**，属装配层的工具。

⚠️ 由 ``setups/__init__.py`` 的 ``setup_ui()`` 统一调用（那里是**唯一**的登记点）。

命令与参数（**与搬迁前完全一致**）
----------------------------------

=========================  ==================================================
项                          值
=========================  ==================================================
命令                        ``gui.show_string_table(data, caption=None, data_columns=3)``
标签页标题                  ``caption``；不给时用「文本表格」
``gui_restore``             ``gui.show_string_table(**{'data': …, 'caption': …, 'data_columns': …})``
返回值                      **那个 widget**（``get_widget`` 的返回值，调用方会用到）
=========================  ==================================================

⚠️ **命令名与签名都不能改**：历史标签页的 ``gui_restore`` 存的就是那串原文；
``admin_menu`` / ``ai_assistant`` 按名字调它。

⚠️⚠️ **两处容易被改坏的地方**（搬过来时原样保留了，别"顺手优化"掉）：

1. **返回值** —— 原方法 ``return widget``。虽然多数调用方忽略返回值，但它是**签名的一部分**，
   外部脚本可能在用（例如拿到 widget 后 ``set_data`` 再刷一次）。
   所以这里的模块级函数同样返回。
2. **``set_parent=True``** —— 原调用传给 ``get_widget`` 的正是它。
   它与 ``string_table`` 这个控件本身的性质绑在一起（见 ``MainWindow.get_widget`` 的说明），
   搬过来必须原样带上，否则标签页的父子关系会变。

Created by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-31: 由 ``zmlx/ui/tabs/string_table.py`` 搬到 ``setups/``
    （原模块删除、**不留垫片**），并接管 ``MainWindow.show_string_table``；
    命令名、签名、返回值与 ``set_parent=True`` 均未变。
"""

import math

from zmlx.system import execute_once
from zmlx.ui import gui
from zmlx.ui.pyqt import QtWidgets, QtCore


class StringTable(QtWidgets.QTableWidget):
    def __init__(self, parent=None, data_columns=3):
        """
        创建字符串列表表格控件

        Args:
            parent: 父控件
            data_columns: 数据列数 (默认3列)
        """
        super().__init__(parent)
        # 保存列数参数
        self.data_columns = max(1, data_columns)  # 确保至少1列
        self.setColumnCount(1 + self.data_columns)  # 序号列 + 数据列
        self.setHorizontalHeaderLabels(
            ['序号'] + [f'数据 {i + 1}' for i in range(self.data_columns)])

        # 设置列宽：序号列尽可能窄
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(0, 40)  # 40像素宽度的序号列
        for i in range(1, self.columnCount()):
            self.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.Stretch)

        # 表格样式设置
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)

    def set_data(self, data):
        """设置要显示的数据

        Args:
            data (list): 字符串列表
        """
        # 计算需要多少行（ceil(数据个数/列数)）
        row_count = math.ceil(len(data) / self.data_columns) if data else 0
        self.setRowCount(row_count)

        # 清除现有数据
        self.clearContents()

        # 填充表格
        for i in range(len(data)):
            row = i // self.data_columns
            col = (i % self.data_columns) + 1  # 数据列从第2列开始（0列是序号）

            # 序号列（0列）
            if self.item(row, 0) is None:
                index_item = QtWidgets.QTableWidgetItem(
                    str(row * self.data_columns + 1))
                index_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.setItem(row, 0, index_item)

            # 数据列
            data_item = QtWidgets.QTableWidgetItem(data[i])
            self.setItem(row, col, data_item)

        # 为空白单元格添加占位符保持表格整洁
        if row_count > 0:
            for row in range(row_count):
                # 处理第一列（序号）
                if self.item(row, 0) is None:
                    index = row * self.data_columns + 1
                    index_item = QtWidgets.QTableWidgetItem(str(index))
                    index_item.setTextAlignment(
                        QtCore.Qt.AlignmentFlag.AlignCenter)
                    self.setItem(row, 0, index_item)

                # 处理数据列
                for col in range(1, self.columnCount()):
                    if self.item(row, col) is None:
                        empty_item = QtWidgets.QTableWidgetItem("")
                        self.setItem(row, col, empty_item)


def show_string_table(data, caption=None, data_columns=3):
    """把一列字符串丢进表格标签页显示；同时也是 GUI 命令 ``gui.show_string_table``.

    Args:
        data: 要显示的字符串列表。
        caption: 标签页标题；不给时用「文本表格」。
        data_columns: 数据列数（不含最左的序号列），默认 3。

    Returns:
        刚打开（或切到）的那个 :class:`StringTable` 控件。⚠️ **返回值是签名的一部分**，
        不要改成返回 ``None``（见模块文档「两处容易被改坏的地方」）。

    ⚠️ 由 ``MainWindow.show_string_table`` **原样搬来**（2026-10-31）：那段代码靠「主窗口的
    公开方法被自动注册成 ``gui.xxx``」提供命令；方法搬走后那条链断了，所以本文件的
    :func:`setup_ui` 用 ``gui.add_func('show_string_table', show_string_table)`` **显式补上**。

    ⚠️ ``set_parent=True`` **不是可选项**：原调用就是这样传的，见模块文档。

    ⚠️ **标签页按「控件类型 + 标题」复用**：同标题再调一次只是切过去并重填数据；
    想让两次数据各占一页，就得给不同的 ``caption``。这正是 ``admin_menu`` 那几处
    各传各的标题的原因。
    """
    opts = dict(data=data, caption=caption, data_columns=data_columns)

    def oper(w):
        w.gui_restore = f"""gui.show_string_table(**{opts})"""
        w.set_data(data)

    widget = gui.get_widget(
        StringTable,
        caption="文本表格" if caption is None else caption,
        type_kw=dict(data_columns=data_columns),
        set_parent=True,
        oper=oper,
    )

    return widget


@execute_once(file=__file__)
def setup_ui():
    """注册命令 ``gui.show_string_table``（由 ``setups/__init__.py`` 调用）.

    ⚠️ 本文件**不挂菜单项**：它是给插件 / scen / 脚本用的**通用出口**，
    由调用方自己决定什么时候弹这个表格（``admin_menu`` 就是一个典型调用方）。
    """
    gui.add_func('show_string_table', show_string_table)
