import timeit

from zml import app_data
from zmlx.alg.base import clamp
from zmlx.ui.pyqt import QtCore, QtWidgets


class MemView(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        self.timer = QtCore.QTimer()
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
                    edit = app_data_edits.get(type(value))
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
            data.append([key, f'{value}', f'{type(value)}'])

        self.setRowCount(len(data))
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['名称', '值', '类型'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for i_row in range(len(data)):
            for i_col in range(3):
                self.setItem(
                    i_row, i_col,
                    QtWidgets.QTableWidgetItem(data[i_row][i_col]))

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


def setup_ui():
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

    # 注册编辑方法
    app_data_edits = app_data.get('app_data_edits')
    if not isinstance(app_data_edits, dict):
        app_data_edits = {}
    # 添加编辑方法
    app_data_edits[int] = edit_int
    app_data_edits[float] = edit_float
    app_data_edits[str] = edit_str
    # 保存编辑方法字典
    app_data.put('app_data_edits', app_data_edits)

    def default_app_data_edit(key):
        from zmlx.ui.alg import edit_in_tab
        from zmlx.ui.widget.edit_by_text import ObjEditByText
        def set_data(value):
            app_data.put(key, value)

        def get_data():
            return app_data.get(key)

        edit_in_tab(ObjEditByText, set_data=set_data, get_data=get_data, caption=f'编辑变量{key}',
                    support_refresh=False)

    # 添加默认的编辑器
    app_data.put('default_app_data_edit', default_app_data_edit)
