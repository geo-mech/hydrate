"""GUI 命令桥接器（``GuiApi``）：把非 GUI 线程的调用派发到主线程执行.

这是「内核线程想动界面」的唯一正道：后台线程调用 :meth:`GuiApi.command`，
它把请求塞进某个空闲通道并 ``emit`` 一个信号，Qt 的信号/槽机制负责把这次执行
搬到 GUI 线程 —— 后台线程则阻塞等待结果（所以**返回值和异常都能带回原线程**）。

⚠️ 通道池上限 20 个：每个并发调用占一个通道，用满是 ``print`` 一句然后返回
``None``（不排队、不阻塞）。这不是「稍后重试」的语义，调用方要自己看得懂。

Modified by DeepSeek, 2026-10-16: 从 ``zmlx/ui/utils.py`` 拆出（原样搬迁，未改行为）.
"""

from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.utils.shared import SharedDict, SharedList


class GuiApi(QtCore.QObject):
    """GUI 命令桥接器。

    通过信号/槽机制将非 GUI 线程的调用派发到主线程执行。
    支持命令通道池（最多 20 个并发通道）和直接调用模式。
    """

    class Channel:
        """单个命令通道（互斥锁保护）。"""
        def __init__(self):
            self.args = []
            self.kwargs = {}
            self.res = None
            self.err = None
            self.mtx = QtCore.QMutex()
            self.mtx_busy = QtCore.QMutex()

    __sig_proc = QtCore.pyqtSignal(int)

    def __init__(self, parent, break_point=None, flag_exit=None):
        """初始化 GUI API。

        Args:
            parent: 父 QObject。
            break_point: 断点控制器（BreakPoint）。
            flag_exit: 退出标志（SharedValue）。
        """
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
                if not callable(f):
                    raise RuntimeError(f'gui function <{item.args[0]}> not found')
                item.res = f(*item.args[1:], **item.kwargs)
            except Exception as err:
                item.err = err
        item.mtx.unlock()

    def command(self, *args, **kwargs):
        has_bp = kwargs.pop('break_point', False)
        if has_bp:
            # 存在一个断点
            if self.break_point is not None:
                # ⚠️ 这一句会让**内核线程**停在断点上等「继续」（这正是「暂停」
                #    生效的地方）；而它在 **GUI 线程**里会径直返回 —— 界面绝不能被
                #    断点挂住。两种身份的判断都在 BreakPoint.pass_only 里。
                self.break_point.pass_only()
                if self.flag_exit is not None:
                    if self.flag_exit.value:
                        raise KeyboardInterrupt()

        is_direct = kwargs.pop('is_direct', False)
        if is_direct:  # 直接进行调用
            if len(args) > 0:
                f = self.funcs.get(args[0])
                if not callable(f):
                    raise RuntimeError(f'gui function <{args[0]}> not found')
                return f(*args[1:], **kwargs)
            else:
                return None

        if len(args) > 0:
            for idx in range(self.channels.length()):
                item = self.channels.get(idx)
                if item.mtx_busy.tryLock():
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
                    item.mtx_busy.unlock()
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
