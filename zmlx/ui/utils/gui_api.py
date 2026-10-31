"""GUI 命令桥接器（``GuiApi``）：把非 GUI 线程的调用派发到主线程执行.

这是「内核线程想动界面」的唯一正道：后台线程调用 :meth:`GuiApi.command`，
它就地为这次调用新建一个 :class:`GuiApi.Channel`，把参数写进去，``emit`` 一个
**携带该通道对象**的信号；Qt 的信号/槽机制负责把执行搬到 GUI 线程 —— 后台线程
则阻塞等待结果（所以**返回值和异常都能带回原线程**）。

⚠️ **每次调用一个通道，用完即弃，不存储、不复用**（2026-10-30 起）：
所以既没有「通道池」，也没有「是否被占用」的检查 —— 新建出来的通道必然是空闲的，
并发数也因此不再有上限（旧实现的池上限 20，用满时 ``print`` 一句并返回 ``None``）。
附带的好处是**嵌套天然安全**：外层调用与内层调用是两个不同对象，互不干扰，
不需要「GUI 线程就地执行」之类的特判。

Modified by DeepSeek, 2026-10-16: 从 ``zmlx/ui/utils.py`` 拆出（原样搬迁，未改行为）.
Modified by DeepSeek, 2026-10-30: 去掉通道池（``channels`` / ``mtx_busy`` / 上限 20），
    改为每次调用就地新建 Channel 并由信号直接携带；``channel_n`` 弃用（恒返回 0）.
Modified by DeepSeek, 2026-10-30: 握手原语由 ``QMutex``（非属主线程 unlock，属文档违规）
    改为 ``QSemaphore(0)``，``acquire`` / ``release`` 本就允许跨线程.
"""

from zmlx.system import warn
from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.utils.shared import SharedDict


class GuiApi(QtCore.QObject):
    """GUI 命令桥接器。

    通过信号/槽机制将非 GUI 线程的调用派发到主线程执行。
    每次调用新建一个通道（用完即弃），因此没有并发上限，也不需要占用检查。
    """

    class Channel:
        """单个命令通道 —— 一次调用一份，用完即弃。

        ``sem`` 是一个**二值信号量**（初始计数 0）：调用者在 ``emit`` 之后
        ``acquire`` 等待，由 GUI 线程的 :meth:`GuiApi.__proc` 执行完毕后
        ``release`` 放行。选它而不是 ``QMutex`` 的原因：

        1. ``acquire`` / ``release`` 本来就**允许跨线程**，不存在「非属主线程
           unlock」这种文档违规（``QMutex::unlock`` 文档明说换线程是 error）；
        2. ``release`` 先于 ``acquire`` 发生时只是把计数置 1，``acquire`` 立即
           返回 —— 不需要「先 lock 占位、再 lock 等待」那两步；
        3. 计数是幂等的，``__proc`` 的 ``finally`` 里无论执行几次都不会解错。

        ⚠️ 它**不是**用来保护 ``args`` / ``res`` 的互斥锁：通道不共享，无需保护。
        """
        def __init__(self):
            self.args = []
            self.kwargs = {}
            self.res = None
            self.err = None
            self.sem = QtCore.QSemaphore(0)

    __sig_proc = QtCore.pyqtSignal(object)

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
            """已弃用：通道池已移除，恒返回 0。"""
            warn('``gui.channel_n()`` 已弃用（2026-10-30）：通道池已移除，'
                 '恒返回 0；本命令将于 2027-10-30 删除',
                 DeprecationWarning)
            return 0

        self.funcs = SharedDict(
            {
                "add_func": self.add_func,
                "get_func": self.get_func,
                "list_all": self.list_all,
                "channel_n": channel_n, "call": call,
            }
        )
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

    def __proc(self, item):
        """在 **GUI 线程** 执行 ``item`` 里的那条命令，然后放行调用者。"""
        try:
            f = self.funcs.get(item.args[0])
            if not callable(f):
                raise RuntimeError(f'gui function <{item.args[0]}> not found')
            item.res = f(*item.args[1:], **item.kwargs)
        except Exception as err:
            item.err = err
        finally:
            # ⚠️ 必须放行：槽里万一抛出非 Exception（如 KeyboardInterrupt），
            #    也不能把调用者永久挂在 sem 上。
            item.sem.release()

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
            item = GuiApi.Channel()
            item.args = args
            item.kwargs = kwargs
            self.__sig_proc.emit(item)
            # 若当前就在 GUI 线程，上面的 emit 是**直连**，__proc 已就地执行并
            # release（计数先变 1），这一句立即返回；跨线程时则在此阻塞等待。
            item.sem.acquire()
            if item.err is not None:
                raise item.err
            return item.res
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
