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

    ⚠️ **不要把这个对象交给外部代码直接用**：外部调命令表里的函数一律写
    ``gui.xxx(...)``（``GuiBuffer.__getattr__`` → ``Agent`` → ``command``），
    本对象只应由 ``GuiBuffer`` 持有并转发。``gui.get().xxx()`` 在 GUI 线程里
    看不出差别，在后台线程里则绕过了唯一的派发层 —— 理由与判据见
    ``ui/AGENTS.md`` §6.2 与 ``gui_buffer.py`` 的模块文档。
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
            """在 **GUI 线程**执行任意可调用对象（``gui.call(func, ...)`` 的落地命令）.

            Args:
                func: 要执行的可调用对象。
                *args: 传给它的位置参数。
                **kwargs: 传给它的关键词参数。

            Returns:
                ``func`` 的返回值；异常会原样带回调用线程重新抛出。

            ⚠️ **不要直接调这条命令**：用 ``gui.call(func, ...)`` —— 它会先派发到 GUI
            线程再执行；而本函数只是「派发之后实际执行的那一步」，本身不管线程。
            ⚠️ 同步语义：调用线程会阻塞到执行完，所以别在持有锁时调它。

            Example:
                >>> gui.call(btn.setEnabled, False)          # 改控件（GUI 线程里执行）
                >>> gui.call(lambda: w.setWindowTitle('跑完了'))
            """
            return func(*args, **kwargs)

        def channel_n():
            """已弃用：通道池已移除，恒返回 0。

            Returns:
                int: 恒为 ``0``。

            ⚠️ **2026-10-30 弃用、2027-10-30 删除**：它原本返回「命令通道池」的大小，
            而通道池已经取消（现在每次调用就地新建一个、用完即弃），于是它没有意义了。
            调用它会发一条 ``DeprecationWarning``。

            Example:
                >>> gui.channel_n()      # 0（仅用于兼容老代码）
            """
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
        把一个函数注册进命令表（之后外部可用 ``gui.<key>(...)`` 调它）

        Args:
            key: 命令名（外部将用 ``gui.<key>(...)`` 调它）。**一旦发布不能改名**：
                标签页状态里存的是 ``gui.<key>(...)`` 的原文，重启时按原文重放。
            func: 要注册的函数；传 ``None`` 表示「只占位、调用时报错」（占位符用法）。

        Returns:
            GuiApi: ``self``（便于链式调用）。

        ⚠️ **同名会静默覆盖**：后注册者赢。所以通用名字（如 ``push_plot``）容易与
        主窗口的公开方法撞名 —— 插件命令请加自己的前缀（例如 ``rtp_``）。
        ⚠️ 它本身是 GUI 线程命令；插件在**加载期**调用它是安全的（只写命令表，不碰控件）。

        Example:
            >>> gui.add_func('do_something', do_something)
            >>> gui.add_func('my_prefix_do_it', lambda: print('hi'))
        """
        if callable(func) or func is None:
            self.funcs.set(key, func)
        return self

    def get_func(self, key):
        """按名字取命令表里的函数（**外部请直接用 ``gui.get_func(key)``**）.

        Args:
            key: 命令名（不带 ``gui.`` 前缀）。

        Returns:
            注册的函数；名字不存在时返回 ``None``（**不抛异常**）。

        Example:
            >>> f = gui.get_func('plot')
            >>> if callable(f):
            ...     print(inspect.signature(f))
        """
        return self.funcs.get(key, None)

    def list_all(self, sort=True):
        """
        列出所有的函数

        Args:
            sort: 是否按名字排序（默认 ``True``）。

        Returns:
            list[str]: 全部命令名（不带 ``gui.``）。

        Example:
            >>> names = gui.list_all()
            >>> [name for name in names if name.startswith('show_')]
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
            """弹「打开文件」对话框，返回用户选中的文件与所用过滤器.

            除 ``parent``（已固定为主窗口）外，参数与
            ``QFileDialog.getOpenFileName`` 完全一致：

            Args:
                caption: 对话框标题。
                dir: 初始目录（不传则用当前工作目录）。
                filter: 过滤器，例如 ``'Python 文件 (*.py);;所有文件 (*)'``
                    （``;;`` 分隔多组）。
                **kwargs: 其余透传给 Qt（``initialFilter`` / ``options`` 等）。

            Returns:
                tuple: ``(文件名, 选中的过滤器)``。**用户取消时文件名是空串** ——
                判断「有没有选」只看第一个元素是否非空。

            ⚠️ 无界面（headless）时返回 ``None``，调用方要能处理 ``None``。

            Example:
                >>> fname, _ = gui.get_open_file_name(
                ...     caption='选择脚本', filter='Python 文件 (*.py)')
                >>> if fname:
                ...     gui.exec_file(fname)
            """
            return QtWidgets.QFileDialog.getOpenFileName(
                parent, *args, **kwargs)

        def get_save_file_name(*args, **kwargs):
            """弹「保存文件」对话框，返回用户填写的路径与所用过滤器.

            参数与 ``QFileDialog.getSaveFileName`` 一致（``parent`` 已固定）：

            Args:
                caption: 对话框标题。
                dir: 初始目录 / 建议文件名。
                filter: 过滤器，例如 ``'文本文件 (*.txt)'``。
                **kwargs: 其余透传给 Qt。

            Returns:
                tuple: ``(文件名, 选中的过滤器)``；用户取消时文件名为空串。

            ⚠️ 它**不会**替你创建文件，只返回路径；真要写文件请自己 ``open(...)``。
            ⚠️ 无界面时返回 ``None``。

            Example:
                >>> fname, _ = gui.get_save_file_name(
                ...     caption='导出', dir='result.txt', filter='文本文件 (*.txt)')
                >>> if fname:
                ...     with open(fname, 'w', encoding='utf-8') as f:
                ...         f.write('hello')
            """
            return QtWidgets.QFileDialog.getSaveFileName(
                parent, *args, **kwargs)

        def information(*args, **kwargs):
            """弹**信息**提示框（一个「确定」按钮），不返回任何值.

            参数与 ``QMessageBox.information`` 一致（``parent`` 已固定）：

            Args:
                title: 对话框标题。
                text: 正文。
                **kwargs: 其余透传给 Qt（``buttons`` / ``defaultButton`` 等）。

            Returns:
                None: 用户点了哪个按钮**不返回**（要拿用户的选择请用 ``gui.question``
                或 ``gui.warning``）。

            Example:
                >>> gui.information('完成', '全部数据已写入 result.txt')
            """
            QtWidgets.QMessageBox.information(
                parent, *args, **kwargs)

        def about(*args, **kwargs):
            """弹**关于**对话框（标题栏是程序名，正文是传入的文本）.

            参数与 ``QMessageBox.about`` 一致（``parent`` 已固定）：

            Args:
                title: 标题（一般写程序名）。
                text: 正文，支持简单 HTML。

            Returns:
                None。

            Example:
                >>> gui.about('IGG-Hydrate', '版本 1.9.15')
            """
            QtWidgets.QMessageBox.about(
                parent, *args, **kwargs)

        def warning(*args, **kwargs):
            """弹**警告**提示框（黄色感叹号），返回用户点的按钮.

            参数与 ``QMessageBox.warning`` 一致（``parent`` 已固定）：

            Args:
                title: 对话框标题。
                text: 警告正文。
                **kwargs: 其余透传给 Qt（``buttons`` / ``defaultButton`` 等）。

            Returns:
                ``QMessageBox.StandardButton``: 用户点的那个按钮（默认只有「确定」）。
                想拿「是/否」请用 ``gui.question(text)``，它已经把结果转成 ``bool``。

            Example:
                >>> gui.warning('注意', '目录不可写，结果没有保存')
            """
            QtWidgets.QMessageBox.warning(
                parent, *args, **kwargs)

        def get_existing_directory(*args, **kwargs):
            """弹「选择目录」对话框，返回用户选中的**目录路径**.

            参数与 ``QFileDialog.getExistingDirectory`` 一致（``parent`` 已固定）：

            Args:
                caption: 对话框标题。
                dir: 初始目录。
                **kwargs: 其余透传给 Qt（``options`` 等）。

            Returns:
                str: 目录路径；**用户取消时是空串**。

            Example:
                >>> folder = gui.get_existing_directory('选择算例目录', 'D:/cases')
                >>> if folder:
                ...     gui.set_cwd(folder)
            """
            return QtWidgets.QFileDialog.getExistingDirectory(
                parent, *args, **kwargs)

        def question(info):
            """弹一个**是 / 否**确认框，返回 ``True`` / ``False``.

            Args:
                info: 要问的内容（正文）。标题固定是「请选择」，只有一个参数。

            Returns:
                bool: 点「是」返回 ``True``，其它（否 / 关闭）一律 ``False``。

            ⚠️ 它是**模态**的：会阻塞到用户做出选择。无界面时直接返回 ``None``
            （假值），所以 ``if gui.question(...)`` 在 headless 下等于走「否」分支。

            Example:
                >>> if gui.question('结果文件已存在，是否覆盖？'):
                ...     save()
            """
            reply = QtWidgets.QMessageBox.question(
                parent, '请选择',
                info)
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                return False
            else:
                return True

        def get_int(*args, **kwargs):
            """弹「输入整数」对话框，返回用户输入的整数与是否确认.

            参数与 ``QInputDialog.getInt`` 一致（``parent`` 已固定）：

            Args:
                title: 对话框标题。
                label: 输入框上方的说明文字。
                value: 初始值（默认 ``0``）。
                min: 最小值（默认 ``-2147483647``）。
                max: 最大值（默认 ``2147483647``）。
                step: 步长（默认 ``1``）。

            Returns:
                tuple: ``(数值, 是否点了确定)`` —— **取消时数值是原值**，不是 ``None``，
                所以一定要看第二个元素。

            Example:
                >>> n, ok = gui.get_int('步数', '请输入步数：', 100, 1, 100000)
                >>> if ok:
                ...     run(n)
            """
            return QtWidgets.QInputDialog.getInt(
                parent, *args, **kwargs)

        def get_double(*args, **kwargs):
            """弹「输入浮点数」对话框，返回用户输入的数值与是否确认.

            参数与 ``QInputDialog.getDouble`` 一致（``parent`` 已固定）：

            Args:
                title: 对话框标题。
                label: 说明文字。
                value: 初始值（默认 ``0``）。
                min: 最小值。
                max: 最大值。
                decimals: 小数位数（默认 ``1``）。

            Returns:
                tuple: ``(数值, 是否点了确定)``；取消时数值是原值。

            Example:
                >>> v, ok = gui.get_double('压力', '初始压力 (MPa)：', 10.0, 0.0, 100.0, 3)
                >>> if ok:
                ...     p = v
            """
            return QtWidgets.QInputDialog.getDouble(
                parent, *args, **kwargs)

        def get_text(*args, **kwargs):
            """弹「输入单行文本」对话框，返回文本与是否确认.

            参数与 ``QInputDialog.getText`` 一致（``parent`` 已固定）：

            Args:
                title: 对话框标题。
                label: 说明文字。
                echo: 回显模式（``QLineEdit.EchoMode``）；密码输入传 ``Password``。
                text: 初始文本。

            Returns:
                tuple: ``(文本, 是否点了确定)``；取消时文本是初始文本。

            Example:
                >>> name, ok = gui.get_text('命名', '算例名称：', text='case_1')
                >>> if ok:
                ...     print(name)
            """
            return QtWidgets.QInputDialog.getText(
                parent, *args, **kwargs)

        def get_multi_line_text(*args, **kwargs):
            """弹「输入多行文本」对话框，返回文本与是否确认.

            参数与 ``QInputDialog.getMultiLineText`` 一致（``parent`` 已固定）：

            Args:
                title: 对话框标题。
                label: 说明文字。
                text: 初始文本。

            Returns:
                tuple: ``(文本, 是否点了确定)``；取消时文本是初始文本。

            Example:
                >>> desc, ok = gui.get_multi_line_text('说明', '请输入备注：')
            """
            return QtWidgets.QInputDialog.getMultiLineText(
                parent, *args, **kwargs)

        def get_item(*args, **kwargs):
            """弹「下拉选择」对话框，返回选中项与是否确认.

            参数与 ``QInputDialog.getItem`` 一致（``parent`` 已固定）：

            Args:
                title: 对话框标题。
                label: 说明文字。
                items: 候选项列表（字符串列表）。
                current: 默认选中第几项（从 ``0`` 开始）。
                editable: 是否允许用户手输列表外的值（默认 ``True``）。

            Returns:
                tuple: ``(选中项文本, 是否点了确定)``；取消时是当前项。

            Example:
                >>> kind, ok = gui.get_item('选择', '方案：', ['一维', '二维'], 1, False)
                >>> if ok:
                ...     print(kind)
            """
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
