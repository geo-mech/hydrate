from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.settings import get_text


class SharedList:
    """
    线程安全的列表
    """

    def __init__(self, value=None):
        self.value = value if isinstance(value, list) else []
        self.mtx = QtCore.QMutex()

    def get(self, idx):
        self.mtx.lock()
        res = self.value[idx]
        self.mtx.unlock()
        return res

    def set(self, idx, value):
        self.mtx.lock()
        self.value[idx] = value
        self.mtx.unlock()

    def append(self, value):
        self.mtx.lock()
        self.value.append(value)
        self.mtx.unlock()

    def length(self):
        self.mtx.lock()
        res = len(self.value)
        self.mtx.unlock()
        return res


class SharedDict:
    def __init__(self, value=None):
        self.value = value if isinstance(value, dict) else {}
        self.mtx = QtCore.QMutex()

    def get(self, key, default=None):
        self.mtx.lock()
        res = self.value.get(key, default)
        self.mtx.unlock()
        return res

    def set(self, key, value):
        self.mtx.lock()
        self.value[key] = value
        self.mtx.unlock()

    def list_keys(self, sort=True):
        self.mtx.lock()
        keys = list(self.value.keys())
        self.mtx.unlock()
        if sort:
            keys.sort()
        return keys


class GuiApi(QtCore.QObject):
    class Channel:
        def __init__(self):
            self.args = []
            self.kwargs = {}
            self.res = None
            self.err = None
            self.mtx = QtCore.QMutex()
            self.mtx_running = QtCore.QMutex()

    __sig_proc = QtCore.pyqtSignal(int)

    def __init__(self, parent, break_point=None, flag_exit=None):
        super(GuiApi, self).__init__(parent)
        self.__sig_proc.connect(self.__proc)
        self.break_point = break_point
        self.flag_exit = flag_exit
        self.funcs = SharedDict(
            {"add_func": self.add_func, "list_all": self.list_all,
             "channel_n": lambda: self.channels.length(),
             })
        self.channels = SharedList([GuiApi.Channel()])
        for key, val in self.get_standard(parent=parent).items():
            self.add_func(key, val)

    def add_func(self, key, func):
        """
        添加一个函数
        """
        self.funcs.set(key, func)
        return self

    def list_all(self, sort=True):
        """
        列出所有的函数
        """
        return self.funcs.list_keys(sort=sort)

    def __proc(self, idx):
        assert idx < self.channels.length()
        item = self.channels.get(idx)
        if len(item.args) > 0:
            try:
                f = self.funcs.get(item.args[0])
                assert f is not None, f'gui function <{item.args[0]}> not found'
                item.res = f(*item.args[1:], **item.kwargs)
            except Exception as err:
                item.err = err
        item.mtx.unlock()

    def command(self, *args, **kwargs):
        has_bp = kwargs.pop('break_point', False)
        if has_bp:
            # 存在一个断点
            if self.break_point is not None:
                self.break_point.pass_only()
                if self.flag_exit is not None:
                    if self.flag_exit.value:
                        raise KeyboardInterrupt()
        if len(args) > 0:
            for idx in range(self.channels.length()):
                item = self.channels.get(idx)
                if item.mtx_running.tryLock():
                    item.mtx.lock()
                    item.res = None
                    item.err = None
                    item.args = args
                    item.kwargs = kwargs
                    self.__sig_proc.emit(idx)
                    item.mtx.lock()
                    item.mtx.unlock()
                    res = item.res
                    err = item.err
                    item.mtx_running.unlock()
                    if err is not None:
                        raise err
                    return res
            if self.channels.length() < 20:
                self.channels.append(GuiApi.Channel())
                return self.command(*args, **kwargs)
            else:
                print(f'Gui Command Ignored: {args}, {kwargs}')
                return None
        else:
            return None

    @staticmethod
    def get_standard(parent):
        def get_open_file_name(*args, **kwargs):
            fpath, _ = QtWidgets.QFileDialog.getOpenFileName(
                parent,
                *get_text(args),
                **get_text(kwargs))
            return fpath

        def get_save_file_name(*args, **kwargs):
            fpath, _ = QtWidgets.QFileDialog.getSaveFileName(
                parent,
                *get_text(args),
                **get_text(kwargs))
            return fpath

        def information(*args, **kwargs):
            QtWidgets.QMessageBox.information(
                parent, *get_text(args),
                **get_text(kwargs))

        def about(*args, **kwargs):
            QtWidgets.QMessageBox.about(
                parent, *get_text(args),
                **get_text(kwargs))

        def warning(*args, **kwargs):
            QtWidgets.QMessageBox.warning(
                parent, *get_text(args),
                **get_text(kwargs))

        def get_existing_directory(*args, **kwargs):
            folder = QtWidgets.QFileDialog.getExistingDirectory(
                None,
                *get_text(args),
                **get_text(
                    kwargs))
            return folder

        def question(info):
            reply = QtWidgets.QMessageBox.question(
                parent, get_text('请选择'),
                get_text(info),
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                return False
            else:
                return True

        return {'question': question, "information": information,
                "about": about, "warning": warning,
                'get_open_file_name': get_open_file_name,
                'get_save_file_name': get_save_file_name,
                'get_existing_directory': get_existing_directory,
                }
