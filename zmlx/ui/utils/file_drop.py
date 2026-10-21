"""把「拖进窗口的文件」接到文件处理分发上（``FileDropHandler``）.

用户把一个（或多个）文件从资源管理器拖到界面上，松手后按**扩展名**交给
:class:`~zmlx.ui.utils.file_handler.FileHandler` 去分派 —— 于是「哪些类型能打开」
完全等于「谁调过 ``gui.add_file_handler(...)``」，拖放本身不认识任何扩展名。

⚠️ **为什么是「事件过滤器」而不是重写 ``MainWindow.dragEnterEvent``**：

1. 文本类子控件（``QTextEdit`` / ``QPlainTextEdit`` / ``QLineEdit`` 的派生控件，
   例如 ``TextBrowser`` / ``CodeEdit`` / 控制台的输入框）**自己就接受文件拖放**
   （``acceptDrops()`` 为 ``True``，松手后插入路径文本），事件**到不了**主窗口。
   只在主窗口重写事件的结果是「拖空白处能打开、拖编辑器正文上没反应」。
2. :meth:`MainWindow.list_member_functions` 会把类上的**所有公开方法**扫进命令表，
   重写 ``dragEnterEvent`` / ``dropEvent`` 之类等于往 ``gui.xxx`` 里塞 5 条要带
   ``event`` 参数的假命令；做成独立的 ``QObject`` 就没有这个副作用。

判据见 :meth:`FileDropHandler.eventFilter`：**三个条件同时成立才接管**，其余一律
``return False`` 放行（标签页内部拖动、拖选文字片段、往输入框拖文本都照旧）。

Created by DeepSeek, 2026-11-02
"""

from zmlx.ui.pyqt import QtCore, QtWidgets


class FileDropHandler(QtCore.QObject):
    """窗口级「文件拖放」接收器：识别本地文件，通过信号交回主窗口去打开.

    用法（主窗口构造期）::

        handler = FileDropHandler(self)
        handler.sig_drag_enter.connect(lambda n: self.show_status(f'松开以打开 {n} 个文件'))
        handler.sig_drag_leave.connect(lambda: self.show_status(''))
        handler.sig_dropped.connect(self.drop_files)
        handler.install()

    ⚠️ **它只负责「识别」，不负责「打开」**：``sig_dropped`` 带的是路径列表，
    真正调用 ``file_handler`` 的是主窗口 —— 这样本类不依赖 ``MainWindow``，
    也不会把「怎么提示用户」写死在工具层。
    """

    #: 拖入的本地路径**集合变化**时发一次，参数是路径数。
    #: ⚠️ 只在「变了」时发：``DragMove`` 每帧一次，每帧刷状态栏会让文字抖动。
    sig_drag_enter = QtCore.pyqtSignal(int)

    #: 拖出窗口或拖放被取消（只在确实处于「拖入中」时发）。
    sig_drag_leave = QtCore.pyqtSignal()

    #: 松手了，参数是本地路径列表（已去重、保持拖入顺序）。
    sig_dropped = QtCore.pyqtSignal(list)

    #: 需要接管的事件类型。``DragLeave`` 也在内 —— 只借它清状态，不拦事件。
    _EVENT_TYPES = (
        QtCore.QEvent.Type.DragEnter,
        QtCore.QEvent.Type.DragMove,
        QtCore.QEvent.Type.DragLeave,
        QtCore.QEvent.Type.Drop,
    )

    def __init__(self, window, parent=None):
        """
        Args:
            window: 要接管的窗口（只处理落点在它内部的事件）。传 ``None`` 表示
                接管**所有**窗口 —— 一般不要这么用：模态对话框里的拖放会被抢走。
            parent: Qt 父对象，默认就是 ``window``（于是生命周期跟着窗口走，
                窗口析构时 Qt 会自动把本过滤器摘掉）。
        """
        super().__init__(parent if parent is not None else window)
        self.__window = window
        self.__paths = []

    # ---------------------------------------------------------------- 安装/卸载
    def install(self, app=None):
        """装到 ``QApplication`` 上（进程级，覆盖窗口内的**所有**子控件）.

        Args:
            app: 目标应用对象；``None`` 时取当前 ``QApplication`` 实例。

        Returns:
            self（便于链式调用）。

        ⚠️ 装的是 ``QApplication`` 而不是窗口本身：过滤器只有装在「事件分发链
        更上游」的对象上，才能看到被子控件 ``acceptDrops`` 截走的拖放事件。
        """
        if app is None:
            app = QtCore.QCoreApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        return self

    def uninstall(self, app=None):
        """从 ``QApplication`` 上摘掉（一般不需要：窗口析构时会自动摘）。"""
        if app is None:
            app = QtCore.QCoreApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        return self

    # -------------------------------------------------------------------- 工具
    @staticmethod
    def local_paths(mime):
        """从 MIME 数据里取出**本地文件路径**（去重、保持顺序）.

        Args:
            mime: ``QMimeData``（可能为 ``None``）。

        Returns:
            list[str]: 本地路径；``http(s)`` 链接、邮件附件、压缩包内条目这类
            「虚拟文件」**不在其中**（它们没有本地路径，``isLocalFile()`` 为假）。
        """
        if mime is None or not mime.hasUrls():
            return []
        paths = []
        for url in mime.urls():
            if not url.isLocalFile():
                continue
            fname = url.toLocalFile()
            if fname and fname not in paths:
                paths.append(fname)
        return paths

    def _is_target(self, obj):
        """事件是否发生在「本过滤器负责的窗口」内部。"""
        try:
            if not isinstance(obj, QtWidgets.QWidget):
                return False
            window = self.__window
            if window is None:
                return True
            return obj.window() is window
        except RuntimeError:  # 主窗口已析构（PyQt 里碰它会抛 RuntimeError）
            return False

    def __reset(self):
        if len(self.__paths) > 0:
            self.__paths = []
            self.sig_drag_leave.emit()

    # ---------------------------------------------------------------- 事件入口
    def eventFilter(self, obj, event):
        """接管落在本窗口内的「本地文件」拖放，其余一律放行.

        **接管条件（三条同时成立）**：

        1. 事件类型是 ``DragEnter`` / ``DragMove`` / ``DragLeave`` / ``Drop``；
        2. 落点在本窗口内（``obj.window() is window``）—— 弹出的模态子对话框
           不归这里管；
        3. ``mimeData().hasUrls()`` 且**至少一个**是本地文件。

        ⇒ 标签页内部拖动（``setMovable``）、从编辑器拖选文字到别处、把文本拖进
        输入框，全都**不带本地文件 URL**，因此走 Qt 原生逻辑。
        """
        etype = event.type()
        if etype not in self._EVENT_TYPES:
            return False
        if not self._is_target(obj):
            return False

        if etype == QtCore.QEvent.Type.DragLeave:
            # ⚠️ ``QDragLeaveEvent`` **没有** mimeData()，所以必须放在取路径之前判。
            self.__reset()
            return False  # 只借机清状态，事件本身照旧放行

        paths = self.local_paths(event.mimeData())
        if len(paths) == 0:
            return False

        # 必须**在这里**接受：Qt 只有在 DragEnter 被接受之后才会继续发 Drop，
        # 否则光标一直显示「禁止」，松手也收不到事件。
        event.acceptProposedAction()

        if etype == QtCore.QEvent.Type.Drop:
            # ⚠️ 这里**静默**清状态、不能走 :meth:`__reset`：后者会发
            #    ``sig_drag_leave``，主窗口据此清状态栏 —— 而紧接着 ``sig_dropped``
            #    才要往状态栏写结果，多一次 leave 会让消息闪一下。
            self.__paths = []
            self.sig_dropped.emit(paths)
        elif paths != self.__paths:
            self.__paths = paths
            self.sig_drag_enter.emit(len(paths))

        return True  # 吃掉：不让 ``QTextEdit`` 把路径当文本插进去
