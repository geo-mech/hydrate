import os
from queue import Queue, Empty

from zml import read_text
from zmlx.alg.sys import unique
from zmlx.ui.pyqt import QtCore, QtWidgets


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
        if value is None:
            self.value.pop(key, None)
        else:
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

        def call(func, *args, **kwargs):
            return func(*args, **kwargs)

        def channel_n():
            return self.channels.length()

        self.funcs = SharedDict(
            {
                "add_func": self.add_func,
                "get_func": self.get_func,
                "list_all": self.list_all,
                "channel_n": channel_n, "call": call,
            }
        )
        self.channels = SharedList([GuiApi.Channel()])
        for key, val in self.get_standard(parent=parent).items():
            self.add_func(key, val)

    def add_func(self, key, func):
        """
        添加一个函数
        """
        if callable(func) or func is None:
            self.funcs.set(key, func)
        return self

    def get_func(self, key):
        return self.funcs.get(key, None)

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
            return QtWidgets.QFileDialog.getOpenFileName(
                parent, *args, **kwargs)

        def get_save_file_name(*args, **kwargs):
            return QtWidgets.QFileDialog.getSaveFileName(
                parent, *args, **kwargs)

        def information(*args, **kwargs):
            QtWidgets.QMessageBox.information(
                parent, *args, **kwargs)

        def about(*args, **kwargs):
            QtWidgets.QMessageBox.about(
                parent, *args, **kwargs)

        def warning(*args, **kwargs):
            QtWidgets.QMessageBox.warning(
                parent, *args, **kwargs)

        def get_existing_directory(*args, **kwargs):
            return QtWidgets.QFileDialog.getExistingDirectory(
                parent, *args, **kwargs)

        def question(info):
            reply = QtWidgets.QMessageBox.question(
                parent, '请选择',
                info)
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                return False
            else:
                return True

        def get_int(*args, **kwargs):
            return QtWidgets.QInputDialog.getInt(
                parent, *args, **kwargs)

        def get_double(*args, **kwargs):
            return QtWidgets.QInputDialog.getDouble(
                parent, *args, **kwargs)

        def get_text(*args, **kwargs):
            return QtWidgets.QInputDialog.getText(
                parent, *args, **kwargs)

        def get_multi_line_text(*args, **kwargs):
            return QtWidgets.QInputDialog.getMultiLineText(
                parent, *args, **kwargs)

        def get_item(*args, **kwargs):
            return QtWidgets.QInputDialog.getItem(
                parent, *args, **kwargs)

        return {
            'question': question, "information": information,
            "about": about, "warning": warning,
            'get_open_file_name': get_open_file_name,
            'get_save_file_name': get_save_file_name,
            'get_existing_directory': get_existing_directory,
            'get_int': get_int,
            'get_double': get_double,
            'get_text': get_text,
            'get_multi_line_text': get_multi_line_text,
            'get_item': get_item,
        }


class BreakPoint(QtCore.QObject):
    __sig_unlocked = QtCore.pyqtSignal()
    __sig_locked = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(BreakPoint, self).__init__(parent)
        self.__mtx = QtCore.QMutex()
        self.__locked = SharedValue(False)

    def pass_only(self):
        self.__mtx.lock()
        self.__mtx.unlock()

    def locked(self):
        return self.__locked.get()

    def lock(self):
        if not self.__locked.get():
            self.__mtx.lock()
            self.__locked.set(True)
            self.__sig_locked.emit()

    def unlock(self):
        if self.__locked.get():
            self.__mtx.unlock()
            self.__locked.set(False)
            self.__sig_unlocked.emit()


class SharedValue:
    def __init__(self, value=None):
        self.__val = value
        self.__mtx = QtCore.QMutex()

    def get(self):
        self.__mtx.lock()
        buf = self.__val
        self.__mtx.unlock()
        return buf

    def set(self, new_value):
        self.__mtx.lock()
        self.__val = new_value
        self.__mtx.unlock()

    @property
    def value(self):
        return self.get()

    @value.setter
    def value(self, new_value):
        self.set(new_value)


class TaskProc(QtCore.QObject):
    __sig_do_task = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__tasks = Queue()
        self.__mtx = QtCore.QMutex()
        self.__sig_do_task.connect(self.__do_task)

    def _get_task(self):
        """
        弹出一个任务.
        """
        self.__mtx.lock()
        try:  # 尝试从队列中弹出一个任务
            res = self.__tasks.get(block=False)
        except Empty:
            res = None
        except Exception as err:
            print(f'Error: {err}')
            res = None
        self.__mtx.unlock()
        return res

    def __do_task(self):
        while True:
            try:
                task = self._get_task()
                if task is None:
                    break
                else:
                    assert callable(task), 'The task is not a function'
                    task()
            except Exception as err:
                print(f'meet error {err}')

    def add(self, task):
        try:
            if callable(task):
                self.__mtx.lock()
                self.__tasks.put(task, block=False)
                self.__mtx.unlock()
                self.__sig_do_task.emit()
        except Exception as err:
            print(f'meet error {err}')


class CodeFile:
    def __init__(self, fname):
        self.fname = fname

    def __str__(self):
        return f"CodeFile({self.fname})"

    def __repr__(self):
        return str(self)

    def abs_path(self):
        if isinstance(self.fname, str):
            return os.path.abspath(self.fname)
        else:
            return ''

    def get_text(self):
        return read_text(
            self.abs_path(), encoding='utf-8', default='')

    def exists(self):
        return os.path.isfile(self.abs_path())


class FileHandler(QtCore.QObject):
    """
    管理文件处理函数
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__handlers = {}  # key = desc, value = [exts, open, new_file]
        self.parent = parent

    def add(self, desc, exts, open_file=None, new_file=None):
        """
        添加文件类型
        """
        if not isinstance(exts, (list, tuple)):
            assert isinstance(exts, str)
            exts = [exts]

        exts = [e.lower() for e in exts]
        for i in range(len(exts)):
            assert len(exts[i]) > 0, f'The file extension should not be empty'
            if exts[i][0] != '.':
                exts[i] = '.' + exts[i]

        value = self.__handlers.get(desc, None)

        if value is None:
            self.__handlers[desc] = [exts, open_file, new_file]
        else:  # 对于同样的描述，只能适用于某一个函数
            self.__handlers[desc] = [unique(value[0] + exts), open_file, new_file]

    def get(self, desc):
        """
        根据文件类型描述找文件处理函数
        """
        value = self.__handlers.get(desc, None)
        if value is None:
            return [desc, None, None, None]
        else:
            return [desc, value[0], value[1], value[2]]

    def find(self, ext):
        """
        根据文件扩展名找处理函数
        """
        ext = ext.lower()
        if len(ext) > 0:
            if ext[0] != '.':
                ext = '.' + ext
        results = []
        for desc, value in self.__handlers.items():
            if ext in value[0]:
                results.append([desc, value[0], value[1], value[2]])
        return results

    def open_file(self, filepath):
        """
        打开文件
        """
        if not isinstance(filepath, str):
            return None

        if not os.path.isfile(filepath):
            if os.path.isdir(filepath):
                from zmlx.ui.gui_buffer import gui
                gui.set_cwd(filepath)  # 浏览文件夹
            return None

        ext = os.path.splitext(filepath)[-1]
        if ext is None:
            return None

        funcs = self.find(ext)

        if len(funcs) == 0:
            open_file = None
        elif len(funcs) == 1:
            open_file = funcs[0][2]
        else:
            items = [x[0] for x in funcs]
            desc, ok = QtWidgets.QInputDialog.getItem(
                self.parent, '此扩展名可能是多种文件类型', '请选择',
                items, editable=False)
            open_file = None
            if ok:
                for x in funcs:
                    if desc == x[0]:
                        open_file = x[2]
                        break

        if not callable(open_file):
            self.show_info(filepath)
            return None

        try:
            return open_file(filepath)
        except Exception as err:
            print(f'Error: filepath = {filepath} \nmessage = {err}')
            return None

    @staticmethod
    def show_info(filepath):
        if os.path.isfile(filepath):
            from zmlx.alg.fsys import show_fileinfo
            show_fileinfo(filepath)

    def open_file_by_dlg(self, folder=None):
        """
        打开对话框，并基于选中的类型打开文件
        """
        if len(self.__handlers) == 0:
            return
        filter_text = '所有文件(*.*)'
        data = {}
        for desc, value in self.__handlers.items():
            exts, open_file, new_file = value
            if callable(open_file):
                desc += ' ('
                for ext in exts:
                    desc += f'*{ext}; '
                desc += ')'
                data[desc] = open_file
                filter_text += ';;'
                filter_text += desc
        if not isinstance(folder, str):
            folder = ''

        filepath, desc = QtWidgets.QFileDialog.getOpenFileName(
            self.parent, '请选择要打开的文件', folder, filter_text)

        if os.path.isfile(filepath):
            open_file = data.get(desc, None)
            if callable(open_file):
                open_file(filepath)
            else:  # 使用扩展名来查找
                self.open_file(filepath)

    def new_file_by_dlg(self, folder=None):
        """
        打开对话框，创建文件，并打开文件
        """
        if len(self.__handlers) == 0:
            print('没有设置任何的文件处理函数')
            return
        filter_text = None
        data = {}
        for desc, value in self.__handlers.items():
            exts, open_file, new_file = value
            if callable(new_file):
                desc += ' ('
                for i, ext in enumerate(exts):
                    if i+1==len(exts):
                        desc += f'*{ext}'
                    else:
                        desc += f'*{ext}; '
                desc += ')'
                data[desc] = [open_file, new_file]
                if filter_text is None:
                    filter_text = desc
                else:
                    filter_text += ';;'
                    filter_text += desc

        if len(data) == 0:
            print('没有用于新建文件的处理函数')
            return

        if not isinstance(folder, str):
            folder = ''

        filepath, desc = QtWidgets.QFileDialog.getSaveFileName(
            self.parent, '新建文件', folder, filter_text)

        print(f'filepath = {filepath}')
        print(f'desc = {desc}')

        value = data.get(desc, None)
        if value is None:
            print(f'对于给定类型，没有找到文件处理函数: {desc}')
            return

        assert isinstance(value, list)
        open_file = value[0]
        new_file = value[1]

        if callable(new_file):
            try:
                new_file(filepath)
                if callable(open_file):
                    open_file(filepath)
            except Exception as err:
                print(f'Error: filepath = {filepath} \nmessage = {err}')
                return
