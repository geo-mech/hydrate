from zml import app_data, create_dict
from zmlx.ui import gui
from zmlx.ui.Qt import QtWidgets, QtCore


class LineEdit(QtWidgets.QLineEdit):

    def __init__(self, parent=None, key=None):
        super().__init__(parent)
        self.key = None
        self.setKey(key)
        self.editingFinished.connect(self.save)

    def setKey(self, key):
        self.key = key
        self.load()

    def load(self):
        if self.key is not None:
            self.setText(app_data.getenv(self.key, encoding='utf-8', default=''))

    def save(self):
        if self.key is not None:
            app_data.setenv(key=self.key, value=self.text(), encoding='utf-8')
            gui.status(f'保存成功. key = {self.key}, value = {self.text()}')


class ComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None, key=None):
        super().__init__(parent)
        self.key = key
        self.currentTextChanged.connect(self.save)

    def setKey(self, key):
        self.key = key
        self.load()

    def load(self):
        if self.key is not None:
            self.setCurrentText(app_data.getenv(self.key, encoding='utf-8', default=''))

    def save(self):
        if self.key is not None:
            app_data.setenv(key=self.key, value=self.currentText(), encoding='utf-8')
            gui.status(f'保存成功. key = {self.key}, value = {self.currentText()}')


class EnvEdit(QtWidgets.QTableWidget):
    sigRefresh = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sigRefresh.connect(self.refresh)
        self.sigRefresh.emit()

    def refresh(self):
        data = [create_dict(label='主界面标签位置', key='TabPosition',
                            items=['', 'North', 'East', 'South', 'West'],
                            note='默认在顶部'),
                create_dict(label='主界面标签形状', key='TabShape',
                            items=['', 'Rounded', 'Triangular'],
                            note='默认:Rounded'),
                create_dict(label='控制台内核优先级', key='console_priority',
                            items=['', 'LowestPriority', 'LowPriority',
                                   'InheritPriority', 'NormalPriority',
                                   'HighPriority', 'HighestPriority'],
                            note='默认为低优先级。提高内核的优先级，可能会提高计算速度，'
                                 '但是可能会影响到界面的稳定性，从而造成卡顿'),
                create_dict(label='是否禁用计时器', key='disable_timer',
                            items=['', 'Yes', 'No'],
                            note='默认为No'),
                create_dict(label='是否禁用启动画面', key='disable_splash',
                            items=['', 'Yes', 'No'],
                            note='默认为No'),
                create_dict(label='使用WebEngine', key='use_web_engine',
                            items=['', 'Yes', 'No'],
                            note='默认为否。如果使用WebEngine，则在需要打开网页的时候，'
                                 '会在此软件的标签页面内直接打开，否则，则会调用系统的浏览器'),
                create_dict(label='恢复关闭时的标签', key='restore_tabs',
                            items=['', 'Yes', 'No'],
                            note='默认为No'),
                create_dict(label='启动时显示ReadMe', key='show_readme',
                            items=['', 'Yes', 'No'],
                            note='默认为Yes'),
                create_dict(label='启动时恢复控制台输出', key='restore_console_output',
                            items=['', 'Yes', 'No'],
                            note='默认为No, 即不恢复'),
                create_dict(label='启动时检查授权', key='check_lic_when_start',
                            items=['', 'Yes', 'No'],
                            note='默认不检查. 检查的操作会耗时较长，影响启动速率'),
                create_dict(label='不向开发者反馈', key='disable_auto_feedback',
                            items=['', 'Yes', 'No'],
                            note='默认开启反馈。向软件开发者发送程序错误的信息，仅用于改进程序。'
                                 '如果打开此选项，则不会向开发者反馈任何信息'),
                create_dict(label='Qt版本', key='Qt_version',
                            items=['', 'PyQt5', 'PyQt6'],
                            note='界面优先使用Qt版本，默认为PyQt6. 请尽量保证系统里PyQt5或者PyQt6，仅安装其中一个。'
                                 '两个同时安装，可能会带来不可预知的错误'),
                ]
        self.setRowCount(len(data))
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['项目', '值', '备注'])
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for i in range(len(data)):
            label = data[i].get('label')
            key = data[i].get('key')
            items = data[i].get('items')
            note = data[i].get('note')
            if label is not None:
                self.setItem(i, 0, QtWidgets.QTableWidgetItem(label))
            assert isinstance(key, str)
            if items is None:
                item = LineEdit()
                item.setKey(key)
            else:
                item = ComboBox()
                item.addItems(items)
                item.setKey(key)
            self.setCellWidget(i, 1, item)
            if isinstance(note, str):
                self.setItem(i, 2, QtWidgets.QTableWidgetItem(note))
            self.resizeRowToContents(i)

    def resizeEvent(self, e):
        for row in range(self.rowCount()):
            self.resizeRowToContents(row)
        super().resizeEvent(e)

    @staticmethod
    def get_start_code():
        return """gui.trigger('env.txtpy')"""
