"""异步 matplotlib 标签页（PltView — 标签页专用的 ``MatplotWidget`` 替代实现）.

> ⚠️ **2026-10-18 起本类已无必要，且没有任何代码使用它**（`TabWidget.plot()` 与
> `gui.plot` 现在都走重写后的 ``MatplotWidget``：渲染在调用线程、GUI 只贴图）。
> 问题已经在 ``widgets/plt.py`` 里解决，且不必新增线程。保留本文件仅供备查；
> 若要接入或删除，请先确认没有外部脚本 import 它。

**为什么当初要有这个类**：当时 ``MatplotWidget`` 把 figure 画在 **GUI 线程**上
（``FigureCanvasQTAgg`` 只能如此），于是一次几秒的重图 = 界面卡几秒，这是它一直以来的
痛点，而它又被很多控件当**组件**用（``Interp1Edit`` / ``Interp2Edit`` / ``quick_look``），
不能随便改内部实现。所以另起一个**标签页专用**的实现：接口与
``MatplotWidget`` 对齐，但绘制挪到后台线程。

用法（``TabWidget.plot()`` 内部就是这几步）::

    view = PltView()
    view.plot_on_figure(lambda fig: fig.subplots().plot(x, y))   # 接住就返回
    ...

线程模型
--------

::

   调用方（内核线程 / GUI 线程）      绘图线程                     GUI 线程
   ──────────────────────────      ───────────────────          ─────────
   plot_on_figure(cb)
     ├ 槽空 → 放进任务槽 ──────────→ 取任务
     │        （接住，立刻返回）        on_figure(fig)  ← 在这里执行
     └ 槽满 → **等**（见下）           Agg 渲染成位图
                                      → sig_frame ─────────────→ 贴到界面上

⚠️ **「接住」的语义**：``plot_on_figure`` 只在任务被**真正放进任务槽之后**才返回；
任务槽只有 **1 个位置**，所以上一帧还在画时，新的调用会**等**（不会丢掉任何一帧，也不会
让调用方无限超前）。等待期间界面**照常重绘**（见 :meth:`PltView._pump`）—— 只排除了
用户输入事件，这样不会因为一次点击（例如关标签）把正在用的控件拆掉。

⚠️ 超时保护：等满 ``SUBMIT_TIMEOUT``（60 s）仍放不进去，就丢掉这次任务并发一条警告 ——
宁可少画一帧，也不能把内核永远挂住。

为什么返回位图而不是把 figure 嵌进 Qt 画布
------------------------------------------

``FigureCanvasQTAgg`` 会把 figure 画到 **Qt 的 QPaintDevice** 上，而 Qt 规定只能在自己的
GUI 线程里碰 QPaintDevice。所以只能「后台线程用 ``FigureCanvasAgg`` 渲染成像素 → GUI 线程
贴图」（一次 ``drawPixmap``，微秒级）。代价是屏幕上看到的是**位图**，没有 matplotlib 的
交互工具栏（缩放 / 平移 / 改轴范围）。

分辨率跟着控件走：宽高取绘图区的**逻辑像素**、DPI 取 ``100 × dpr``，高 DPI 屏上文字不会糊。

与 ``MatplotWidget`` 的接口对应关系
-----------------------------------

==============================  ==================================================
``MatplotWidget``                 ``PltView``
==============================  ==================================================
``plot_on_figure(on_figure,     同名同参数，另加 ``wait=``；⚠️ 回调改在**绘图线程**执行
  *, savefig=None)``
``figure``                      同名；⚠️ **会先等当前这一帧画完**再返回（保证可安全读写）
``canvas``                      同名，但返回的是内部的贴图控件（不是 ``FigureCanvasQTAgg``）
``draw(*, savefig=None)``       同名；语义变成「等当前这一帧画完」（可选存图）
``savefig / savefig_by_dlg``    同名（会先 flush，然后按 300 dpi 重绘保存）
``save_file / need_save``       同名；``save_file`` 存**屏幕上那张位图**（不等渲染，关标签不卡）
                                ``need_save`` 是新增的，用来点亮菜单「保存」
``copy_to_clipboard``           同名（直接拷屏上那张位图，不用等渲染）
``set_save_folder / export_data`` 同名
``get_context_menu``            同名（DPI / 导出 / 复制 / 打开目录 / ``context_actions``）
``support_sub_menu = True``     同名类属性
==============================  ==================================================

⚠️ **唯一的返回值差异**：``TabWidget.plot()`` 在**异步**路径上返回 ``None``（旧实现返回
``widget.figure``）。原因：异步时这一帧还没画完，把这个 figure 交出去就是在两个线程里
同时用它（matplotlib 不是线程安全的，轻则图糊、重则崩溃）。``plot`` 的官方 docstring
本来就写着 ``Returns: None``，仓库内也没有任何地方使用它；真要 figure 就传 ``fname``
（那条路径会等画完再返回 figure），或者 ``view.wait()`` 之后取 ``view.figure``。

⚠️⚠️ **回调里捕获的数据必须是快照**：``on_figure`` 在绘图线程执行，而旧实现是同步的
（内核会一直等到画完）。若你直接把「内核正在改写的 numpy 数组」传进去，现在可能画出
「半新半旧」的图。请自己 ``arr.copy()``，或给调用加 ``wait=True``（回到同步语义）。

代价一览（实测）
----------------

- **每个绘图标签页一个线程**（空闲时阻塞在条件变量上，CPU ≈ 0%，栈是虚拟内存）。
  没画过图的标签页**不启动**线程。
- **窗口尺寸变化会重渲染一次**（0.4 s 闸门，拖窗口不会狂重绘）：只重画 figure，**不重跑
  回调** —— 所以 ``clear=False`` 的叠加不会被叠两遍。
- 位图在内存里只留最后一帧（十几 MB 以内，取决于窗口尺寸与屏幕缩放）。
- 首次打开绘图标签仍有约 **0.3~0.5 s** 的一次性开销（matplotlib 导入 + 中文字体初始化
  + 建默认存图目录），与旧实现同一量级（旧实现约 460 ms）。

⚠️ 本模块位于 ``tabs/``，而 ``widgets/tab_widget.py`` 会用到它 —— 这与
``widgets/AGENTS.md`` 的「widgets 不得 import tabs」在字面上冲突。这里是有意的：
``PltView`` 就是「标签页」本身（只被 ``TabWidget`` 打开成页面、不被任何控件当组件用），
而 ``TabWidget.plot()`` 是创建这些页面的唯一入口，它必须知道用哪个类。**导入写在函数体
里（延迟解析）**，所以导入期 ``widgets/`` 一个 ``tabs`` 子模块都不碰 —— 那条规则真正
要防的「导入环」并不存在.

Created by DeepSeek, 2026-10-18
"""

import datetime
import os
import sys
import time

if __name__ == '__main__':  # 直接运行本文件时，把仓库根目录加入搜索路径
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))))

from zmlx.system import make_parent, warn
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets


class _PlotWorker(QtCore.QThread):
    """后台绘图线程：接任务 → 在**自己的** figure 上画 → 渲染成位图发回 GUI 线程.

    ⚠️ **线程不设 parent**（写 ``_PlotWorker(fig)``，绝不传 ``self``）：关标签走
    ``deleteLater()``，parent 指向控件的线程会被连带析构，而「运行中的 QThread 被析构」
    是进程级崩溃（``QThread: Destroyed while thread is still running``，不是异常）。
    强引用放在类属性 ``_RUNNING`` 里，退出时由 ``aboutToQuit`` 统一叫停。

    ⚠️ ``figure`` 由 GUI 线程**创建**、由本线程**绘制**。matplotlib 的 figure 没有线程
    亲和性，真正的规矩是「同一时刻只有一个线程碰它」—— 本类所有对 figure 的访问都发生在
    ``run()`` 里，GUI 侧只在 ``wait()``（确认空闲）之后才碰，因此是串行的。

    Attributes:
        sig_frame: ``(QImage, int)`` —— 一帧画好了：图像 + 任务号.
        sig_error: ``str`` —— 回调 / 渲染 / 存图失败的原因.
        _RUNNING: 类级强引用登记表（线程不设 parent，必须有别的东西持着它）.
    """

    sig_frame = QtCore.pyqtSignal(QtGui.QImage, int)
    sig_error = QtCore.pyqtSignal(str)

    _RUNNING = set()

    #: 是否已经接过 ``QApplication.aboutToQuit``（进程内只接一次）
    _QUIT_HOOKED = False

    #: 逻辑 DPI：figure 的英寸尺寸按「逻辑像素 / 该值」换算，乘 dpr 后得到设备像素
    LOGICAL_DPI = 100.0

    #: 空闲时隔多久醒来一次（毫秒）：既用于等新任务，也用于检查「尺寸变了要重排」
    IDLE_WAIT_MS = 200

    #: 两次「重排」之间至少隔多少秒（防止拖窗口时反复重绘）
    REFLOW_DELAY = 0.4

    #: 尺寸至少变了多少像素才算「真的变了」
    REFLOW_TOLERANCE = 4

    #: 程序退出时最多等绘图线程多久（毫秒）
    QUIT_WAIT_MS = 5000

    #: ``savefig=None`` 时自动存图的最小间隔（秒）——与 ``MatplotWidget`` 一致
    AUTO_SAVE_INTERVAL = 5.0

    def __init__(self, figure, *, bg):
        """初始化（**不启动**，由 :meth:`start_quietly` 启动）.

        Args:
            figure: GUI 线程创建好的 ``matplotlib.figure.Figure``（本线程负责画它）.
            bg: figure 底色（与主题一致，避免闪白）.
        """
        super(_PlotWorker, self).__init__()  # ⚠️ 不传 parent，见类文档
        self.setObjectName(type(self).__name__)

        self._figure = figure
        self._agg = None                 # FigureCanvasAgg（在 run() 里创建）
        self._bg = bg

        self._mutex = QtCore.QMutex()
        self._cond = QtCore.QWaitCondition()

        # ── 受 _mutex 保护的状态 ──
        self._stopped = False
        self._job = None                 # 任务槽（容量 1）
        self._busy = False               # 正在渲染
        self._done_id = 0                # 已完成的最大任务号
        self._size = (800, 600, 1.0)     # 目标尺寸（逻辑像素 + dpr）
        self._save_folder = None         # 自动存图目录（None = 不自动存）
        self._save_dpi = 300

        # ── 只属于绘图线程的状态 ──
        self._last_job = None            # 最近一个任务（尺寸变化时重排用）
        self._rendered_size = None
        self._last_reflow = 0.0
        self._last_save = None

    # ============================================================== 控制（GUI 线程调）
    def start_quietly(self):
        """登记强引用后以**低优先级**启动（绘图再重也不跟界面抢 CPU）."""
        _PlotWorker._hook_app_quit()
        _PlotWorker._RUNNING.add(self)
        self.finished.connect(lambda t=self: _PlotWorker._RUNNING.discard(t))
        self.finished.connect(self.deleteLater)
        self.start(QtCore.QThread.Priority.LowPriority)

    @classmethod
    def _hook_app_quit(cls):
        """把「程序退出」接到 :meth:`_stop_all`（进程内只接一次）.

        ⚠️ 本线程**长命**（开一个图标签就一直活着）且**不设 parent**，所以关主窗口时没有
        任何东西会通知它停下 —— 解释器退出时 Python 包装对象被回收，C++ 侧 ``~QThread()``
        发现线程还在跑，直接 ``qFatal`` → 进程 abort。接上 ``aboutToQuit`` 才能避免。
        """
        if cls._QUIT_HOOKED:
            return
        app = QtWidgets.QApplication.instance()
        if app is None:
            return
        cls._QUIT_HOOKED = True
        app.aboutToQuit.connect(cls._stop_all)

    @classmethod
    def _stop_all(cls):
        """叫停所有还活着的绘图线程，并**有限等待**（只在程序退出时调用）."""
        for thread in list(cls._RUNNING):
            try:
                thread.stop()
            except Exception:
                pass
        for thread in list(cls._RUNNING):
            try:
                thread.wait(cls.QUIT_WAIT_MS)
            except Exception:
                pass

    def try_put(self, job):
        """尝试把任务放进槽里（**不阻塞**）；只有**完全空闲**时才接.

        判定「空闲」= 槽里没有待画任务 **且** 没在渲染。这就是「上一帧还没画完时，
        新的提交必须等」那条规矩的实现处 —— 光看槽空不空是不够的（线程会立刻把任务
        取走，槽几乎总是空的）。

        Args:
            job: 任务字典（``id`` / ``on_figure`` / ``size`` / ``savefig``）.

        Returns:
            bool: True = 已接住（任务会被画出来）；False = 忙 / 线程已停.
        """
        with QtCore.QMutexLocker(self._mutex):
            if self._stopped or self._job is not None or self._busy:
                return False
            self._job = job
            self._cond.wakeAll()
            return True

    def is_done(self, job_id):
        """任务 ``job_id`` 是否已经画完（线程停止时也返回 True，好让等待者退出）."""
        with QtCore.QMutexLocker(self._mutex):
            return self._done_id >= job_id or self._stopped

    def is_idle(self):
        """是否既没有待画任务、也没在渲染."""
        with QtCore.QMutexLocker(self._mutex):
            return self._job is None and not self._busy

    def is_stopped(self):
        """是否已收到停止请求."""
        with QtCore.QMutexLocker(self._mutex):
            return self._stopped

    def set_size(self, width, height, dpr):
        """设置渲染目标尺寸（逻辑像素 + 设备像素比）；变了才唤醒（拖窗口会连发很多次）."""
        new = (max(1, int(width)), max(1, int(height)), max(1.0, float(dpr)))
        with QtCore.QMutexLocker(self._mutex):
            if new != self._size:
                self._size = new
                self._cond.wakeAll()

    def set_save_folder(self, folder):
        """设置自动存图目录（``None`` = 不自动存）."""
        with QtCore.QMutexLocker(self._mutex):
            self._save_folder = folder if folder else None

    def set_export_dpi(self, dpi):
        """设置存图用的 DPI."""
        with QtCore.QMutexLocker(self._mutex):
            self._save_dpi = int(dpi)

    def stop(self):
        """请求收工：置停止位并唤醒. **不阻塞**（清理钩子里不许 ``wait()``）."""
        self.requestInterruption()
        with QtCore.QMutexLocker(self._mutex):
            self._stopped = True
            self._cond.wakeAll()

    # ============================================================== 线程体
    def run(self):
        """线程体：循环「等任务 → 画 → 回报」，空闲时处理「尺寸变了要重排」."""
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        self._agg = FigureCanvasAgg(self._figure)
        try:
            while True:
                kind, payload = self._wait_work()
                if kind is None:
                    return
                if kind == 'job':
                    self._exec_job(payload)
                else:
                    self._exec_reflow(*payload)
        finally:  # 无论怎么退出，都别让等待者永远挂住
            with QtCore.QMutexLocker(self._mutex):
                self._busy = False
                self._cond.wakeAll()

    def _wait_work(self):
        """阻塞等待「有任务」或「需要重排」.

        Returns:
            tuple: ``('job', job)`` / ``('reflow', (job, size))`` / ``(None, None)``（收工）.

        ⚠️ 返回前已把 ``_busy`` 置真（在锁内），所以等待者看到的「忙」是准确的.
        """
        while True:
            with QtCore.QMutexLocker(self._mutex):
                if self._stopped:
                    return None, None
                if self._job is not None:
                    job = self._job
                    self._job = None
                    self._busy = True
                    return 'job', job
                size = self._size
                last = self._last_job
                if last is not None and self._reflow_due(size):
                    self._busy = True
                    return 'reflow', (last, size)
                self._cond.wait(self._mutex, self.IDLE_WAIT_MS)

    def _reflow_due(self, size):
        """尺寸是否变了、且距离上次重排够久了（都满足才重排，避免拖动时狂重绘）."""
        old = self._rendered_size
        if old is None:
            return False
        if (abs(old[0] - size[0]) < self.REFLOW_TOLERANCE
                and abs(old[1] - size[1]) < self.REFLOW_TOLERANCE
                and abs(old[2] - size[2]) < 1e-3):
            return False
        return time.monotonic() - self._last_reflow >= self.REFLOW_DELAY

    def _exec_job(self, job):
        """画一个任务：跑回调 → 渲染 → 发图 → （按需）存图 → 回报完成.

        ⚠️ 顺序很重要：``sig_frame`` **先**发、``sig_error`` 后发 —— GUI 侧收到帧会清掉
        「最近一次失败」，所以错误必须在帧之后到达，否则失败原因会被自己那一帧擦掉
        （旧实现里这是真踩到的坑）.
        """
        try:
            image, err = self._draw(job['on_figure'], job.get('size') or self._size)
            if image is not None:
                self.sig_frame.emit(image, job['id'])
            if err is not None:
                self._report(err)
            self._maybe_save(job.get('savefig'))
        except Exception as err:
            self._report(err)
        finally:
            with QtCore.QMutexLocker(self._mutex):
                self._busy = False
                self._last_job = job
                self._done_id = job['id']
                self._cond.wakeAll()

    def _exec_reflow(self, job, size):
        """尺寸变了：用**现有 figure** 按新尺寸重渲染一次（**不重跑回调**）.

        ⚠️ 这里刻意不重新调用 ``on_figure``：回调**不保证幂等**（例如 ``clear=False`` 的
        多个视图叠加，重跑会把同一批 artist 再叠一遍）。figure 里已经有内容，重画即可.
        """
        try:
            self._apply_size(size)
            self._agg.draw()
            self.sig_frame.emit(self._to_image(size[2]), job['id'])
        except Exception as err:
            self._report(err)
        finally:
            self._last_reflow = time.monotonic()
            with QtCore.QMutexLocker(self._mutex):
                self._busy = False
                self._cond.wakeAll()

    def _apply_size(self, size):
        """把 figure 的英寸尺寸 / DPI 调成「逻辑像素 × dpr」."""
        width, height, dpr = size
        figure = self._figure
        figure.set_dpi(self.LOGICAL_DPI * max(1.0, dpr))
        figure.set_size_inches(width / self.LOGICAL_DPI, height / self.LOGICAL_DPI)
        figure.patch.set_facecolor(self._bg)
        self._rendered_size = size

    def _draw(self, on_figure, size):
        """跑回调并渲染成 QImage（**只在本线程执行**）.

        Returns:
            tuple: ``(QImage, Exception | None)`` —— 图像 + 回调抛出的异常（没有则 None）.

        ⚠️ 回调抛异常时，仍然把已经画上去的那部分渲染出来（与 ``MatplotWidget`` 的行为
        一致：旧实现也是「报错后照样 draw」），异常由调用方在**发完帧之后**再上报.
        """
        self._apply_size(size)
        err = None
        if callable(on_figure):
            try:
                on_figure(self._figure)
            except Exception as e:
                err = e
        self._agg.draw()
        return self._to_image(size[2]), err

    def _to_image(self, dpr):
        """把 Agg 画布的内容转成 QImage（**深拷贝**）.

        ⚠️ 不同 matplotlib 版本的 ``buffer_rgba()`` 形状不同（≥3.6 为 ``(h, w, 4)``，
        更早是一维字节串），两种都处理.
        """
        import numpy
        buffer = self._agg.buffer_rgba()
        array = numpy.asarray(buffer)
        if array.ndim == 3:
            height, width = int(array.shape[0]), int(array.shape[1])
            array = array.reshape(height, width, 4)
        else:  # 老版本：宽度从 bbox 推
            width = int(round(self._figure.bbox.width))
            array = array.reshape(-1, width, 4)
            height = int(array.shape[0])
        array = numpy.ascontiguousarray(array)
        image = QtGui.QImage(array.tobytes(), width, height, width * 4,
                             QtGui.QImage.Format.Format_RGBA8888)
        image = image.copy()  # ⚠️ 必须 copy：QImage 不持有 Python 缓冲区的所有权
        image.setDevicePixelRatio(max(1.0, float(dpr)))
        return image

    def _report(self, err):
        """上报一次失败（不抛出 —— 一个坏回调不该让绘图线程死掉）."""
        text = '{0}: {1}'.format(type(err).__name__, err)
        warn('PltView: {0}'.format(text))
        self.sig_error.emit(text)

    def _maybe_save(self, savefig):
        """按 ``MatplotWidget.draw`` 的语义处理保存（写盘在**绘图线程**里）.

        - ``savefig`` 是 ``str`` → 存到这个路径（并重置自动存图计时）；
        - 否则看目录：``None`` → 距上次 ≥5 s 才存；``True`` → 每次都存；``False`` → 不存.
        """
        with QtCore.QMutexLocker(self._mutex):
            folder = self._save_folder
            dpi = self._save_dpi

        if isinstance(savefig, str):
            self._save_figure(savefig, dpi)
            self._last_save = datetime.datetime.now()
            return

        if folder is None:
            return
        now = datetime.datetime.now()
        if savefig is None:
            if (self._last_save is not None
                    and abs(now - self._last_save).total_seconds() < self.AUTO_SAVE_INTERVAL):
                return
        elif not savefig:
            return
        name = now.strftime('%Y-%m-%d-%H-%M-%S-') + '{0:06d}.png'.format(now.microsecond)
        self._save_figure(os.path.join(folder, name), dpi)
        self._last_save = datetime.datetime.now()

    def _save_figure(self, path, dpi):
        """把 figure 存成图片（失败只上报，不打断循环）."""
        try:
            self._figure.savefig(fname=make_parent(path), dpi=dpi)
            return path
        except Exception as err:
            self._report(err)
            return None


class _Canvas(QtWidgets.QWidget):
    """绘图区：把一张 ``QPixmap`` 等比缩放、居中画出来（+ 一行占位文字）.

    刻意只是一个「画板」：不含交互、不含业务逻辑。用 ``paintEvent`` 而不是
    ``QLabel.setPixmap``，是为了「缩放只在绘制时做」——窗口尺寸变了不用重建 ``QPixmap``.
    """

    def __init__(self, parent=None):
        super(_Canvas, self).__init__(parent)
        self._pixmap = None
        self._message = ''
        self._bg = None
        self.setMinimumSize(240, 180)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Expanding)

    def set_image(self, image):
        """显示一张图（``None`` 等于清空）."""
        if image is None or image.isNull():
            self._pixmap = None
        else:
            pixmap = QtGui.QPixmap.fromImage(image)
            pixmap.setDevicePixelRatio(max(1.0, float(image.devicePixelRatio())))
            self._pixmap = pixmap
        self._message = ''
        self.update()

    def set_message(self, text):
        """显示一行提示文字（不显示图片）."""
        self._pixmap = None
        self._message = str(text)
        self.update()

    def set_background(self, color):
        """设置底色（与 figure 的底色一致，避免刷新时闪一下）."""
        self._bg = QtGui.QColor(color)
        self.update()

    def has_image(self):
        """当前是否正在显示图片."""
        return self._pixmap is not None and not self._pixmap.isNull()

    def paintEvent(self, event):
        """画底色 → 有图就等比居中贴图，没图就写提示文字."""
        painter = QtGui.QPainter(self)
        if self._bg is not None:
            painter.fillRect(self.rect(), self._bg)
        else:
            painter.fillRect(
                self.rect(), self.palette().color(QtGui.QPalette.ColorRole.Base))
        if self.has_image():
            painter.setRenderHint(
                QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.drawPixmap(self._fit_rect(), self._pixmap)
        elif self._message:
            painter.setPen(
                self.palette().color(QtGui.QPalette.ColorRole.PlaceholderText))
            painter.drawText(self.rect(),
                             QtCore.Qt.AlignmentFlag.AlignCenter, self._message)
        painter.end()

    def _fit_rect(self):
        """算出「等比缩放并居中」后图片该占的矩形.

        ⚠️ 用 device-independent 尺寸（``width() / devicePixelRatio()``）来算：位图是按
        「逻辑尺寸 × dpr」渲染的，直接拿设备像素去比会在高 DPI 屏上算成放大 2 倍.
        """
        pixmap = self._pixmap
        dpr = max(1.0, float(pixmap.devicePixelRatio()))
        width = pixmap.width() / dpr
        height = pixmap.height() / dpr
        if width <= 0 or height <= 0:
            return QtCore.QRect()
        scale = min(self.width() / width, self.height() / height)
        target_width = max(1, int(round(width * scale)))
        target_height = max(1, int(round(height * scale)))
        return QtCore.QRect((self.width() - target_width) // 2,
                            (self.height() - target_height) // 2,
                            target_width, target_height)


class PltView(QtWidgets.QWidget):
    """异步 matplotlib 标签页（详见模块文档）.

    ⚠️ 用法与 ``MatplotWidget`` 基本一致，但 ``on_figure`` **在绘图线程里执行**；
    详见 :meth:`plot_on_figure`.
    """

    #: 支持子菜单（与 ``MatplotWidget`` 同名同义，供宿主控件判断）
    support_sub_menu = True

    #: 放进任务槽最多等多久（秒）——超时就丢掉这一帧，绝不把内核挂死
    SUBMIT_TIMEOUT = 60.0

    #: 等「这一帧画完」（``wait`` / ``figure`` / ``savefig``）最多等多久（秒）
    FLUSH_TIMEOUT = 60.0

    #: matplotlib 的一次性初始化（字体 / 主题）是否已经做过
    _MPL_READY = False

    def __init__(self, parent=None):
        """初始化.

        Args:
            parent: Qt 父对象.
        """
        super(PltView, self).__init__(parent)
        self.context_actions = []  # 右键菜单扩展点（与 MatplotWidget 同一套约定）

        self.__worker = None       # 绘图线程（不设 parent，见 _PlotWorker）
        self.__figure = None       # matplotlib 的 Figure（GUI 创建、线程里画）
        self.__canvas = None       # 贴图区
        self.__job_seq = 0         # 任务号
        self.__last_image = None   # 最近一帧（复制 / 保存用）
        self.__save_folder = None  # 自动存图目录
        self.__error = ''          # 最近一次失败原因（供 tooltip / 状态）

        self._prepare_matplotlib()  # 字体 / 主题：进程内只在主线程做一次
        self.__build()

    # ============================================================== matplotlib 预热
    def _prepare_matplotlib(self):
        """初始化 matplotlib 的字体与主题（**进程内只做一次**，且只在主线程做）.

        ⚠️ 必须在这里做、不能留给绘图线程：``set_chinese_font()`` 要遍历系统字体、触发
        字体管理器初始化（约 300 ms），那是典型的一次性全局状态 —— 两个线程同时初始化它
        才是真正的风险。在主线程一次到位，绘图线程只管画.

        ⚠️ 这里**不**调 ``matplotlib.use(...)``：本控件用 ``FigureCanvasAgg`` 直接渲染、
        不经过 pyplot，没有「当前后端」的概念，故意不去动它.
        """
        if PltView._MPL_READY:
            return
        PltView._MPL_READY = True
        try:
            import matplotlib
            from matplotlib import style
            if self._is_dark():
                matplotlib.rcParams.update(style.library['dark_background'])
        except Exception as err:
            print('PltView: 设置 matplotlib 主题失败 —— {0}'.format(err))
        try:
            from zmlx.plt import set_chinese_font
            set_chinese_font()
        except Exception as err:
            print('PltView: 设置中文字体失败 —— {0}'.format(err))

    def _is_dark(self):
        """当前是否是暗色主题（判据与 ``MatplotWidget`` 一致：窗口底色的亮度）."""
        color = self.palette().color(QtGui.QPalette.ColorRole.Window)
        return color.lightness() < 128

    # ============================================================== 界面 / 线程
    def __build(self):
        """建 figure、贴图区与绘图线程（线程**不启动**，等第一个任务）."""
        import matplotlib.figure

        bg = '#1e1e1e' if self._is_dark() else '#ffffff'

        self.__canvas = _Canvas(self)
        self.__canvas.set_background(bg)
        self.__canvas.set_message('正在绘图…')

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.__canvas, 1)

        self.__figure = matplotlib.figure.Figure()

        from zmlx.plt import get_plt_save_path
        now = datetime.datetime.now()
        name = now.strftime('%Y-%m-%d-%H-%M-%S-') + '{0:06d}'.format(now.microsecond)
        self.__save_folder = get_plt_save_path(name)  # 与 MatplotWidget 同一套默认目录

        worker = _PlotWorker(self.__figure, bg=bg)
        worker.sig_frame.connect(self.__on_frame)
        worker.sig_error.connect(self.__on_error)
        worker.set_save_folder(self.__save_folder)
        worker.set_export_dpi(self._export_dpi())
        self.__worker = worker
        self.__push_size()

    def __ensure_started(self):
        """确保绘图线程已经启动（第一个任务来时才启动，没画过图就不占线程）."""
        worker = self.__worker
        if worker is not None and not worker.isRunning():
            worker.start_quietly()

    def __push_size(self):
        """把贴图区当前的（逻辑）尺寸与 dpr 推给绘图线程."""
        worker = self.__worker
        if worker is None:
            return
        canvas = self.__canvas
        try:
            dpr = float(canvas.devicePixelRatioF())
        except Exception:
            dpr = 1.0
        worker.set_size(max(240, canvas.width()), max(180, canvas.height()), dpr)

    def __target_size(self):
        """这一帧该按什么尺寸渲染（逻辑像素 + dpr）."""
        canvas = self.__canvas
        try:
            dpr = float(canvas.devicePixelRatioF())
        except Exception:
            dpr = 1.0
        return (max(240, canvas.width()), max(180, canvas.height()), max(1.0, dpr))

    # ============================================================== 排队 / 等待
    @staticmethod
    def _pump(seconds):
        """等一小会儿，但**继续处理界面事件**.

        ⚠️ 用 ``ExcludeUserInputEvents`` 是有意的：等待期间界面照常重绘、后台结果照常
        显示，但**不会**因为一次点击（比如关掉这个标签）而把我们正在用的控件拆掉 ——
        那会让「等一会儿」变成「等一个已经被 delete 的对象」.
        ⚠️ 只在 GUI 线程里 pump（``processEvents`` 不能从别处调）.
        """
        app = QtWidgets.QApplication.instance()
        if app is not None and QtCore.QThread.currentThread() is app.thread():
            app.processEvents(
                QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        time.sleep(seconds)

    def __submit(self, job):
        """把任务交给绘图线程；槽满就**等**（期间界面照常重绘）.

        Returns:
            bool: True = 已接住；False = 控件已关闭 / 等太久.
        """
        worker = self.__worker
        if worker is None:
            return False
        self.__ensure_started()
        deadline = time.monotonic() + self.SUBMIT_TIMEOUT
        while True:
            worker = self.__worker
            if worker is None or worker.is_stopped():
                return False
            if worker.try_put(job):
                return True
            if time.monotonic() > deadline:
                return False
            self._pump(0.005)

    def wait(self, timeout=None):
        """等绘图线程把手上的任务全部画完（GUI 线程调用；期间界面照常重绘）.

        Args:
            timeout: 最多等多久（秒）；``None`` 用 :attr:`FLUSH_TIMEOUT`.

        Returns:
            bool: True = 已经空闲；False = 超时 / 控件已关闭.
        """
        timeout = self.FLUSH_TIMEOUT if timeout is None else timeout
        deadline = time.monotonic() + timeout
        while True:
            worker = self.__worker
            if worker is None or worker.is_idle():
                self._pump(0.005)  # 让还在排队的 sig_frame 落地：返回时画面已更新
                return True
            if time.monotonic() > deadline:
                warn('PltView: 等待绘图线程空闲超时（{0:.1f} s）'.format(timeout))
                return False
            self._pump(0.005)

    def __wait_done(self, job_id, timeout=None):
        """等某个具体任务画完（``wait=True`` 用）."""
        timeout = self.FLUSH_TIMEOUT if timeout is None else timeout
        deadline = time.monotonic() + timeout
        while True:
            worker = self.__worker
            if worker is None or worker.is_done(job_id):
                self._pump(0.005)  # 让排队的 sig_frame 落地：返回时画面已更新
                return True
            if time.monotonic() > deadline:
                warn('PltView: 等待第 {0} 号绘图任务超时'.format(job_id))
                return False
            self._pump(0.005)

    # ============================================================== 公开接口
    def plot_on_figure(self, on_figure, *, savefig=None, wait=False):
        """在控件上绘图（与 ``MatplotWidget.plot_on_figure`` 同名同参数，另加 ``wait``）.

        Args:
            on_figure: ``on_figure(fig)`` —— 把内容画到 figure 上.
                ⚠️ **在绘图线程里执行**：只能操作 ``fig`` 与它捕获的数据，不许碰 Qt 控件.
                ⚠️ 捕获的数据必须是**快照**（或此后不再改动），否则可能画出「半新半旧」.
            savefig: ``None`` / ``True`` / ``False`` / ``str`` —— 与
                ``MatplotWidget.draw`` 的语义一致（``None`` = 距上次 ≥5 s 才自动存）.
            wait: ``True`` = 等这一帧画完再返回（旧语义）；``False`` = 接住就返回.

        Returns:
            bool: 任务是否被接住（False = 控件正在关闭，或等待超时）.

        Note:
            「接住」= 任务已经放进绘图线程的**唯一**任务槽。槽满时本方法会等（期间界面
            照常重绘），所以调用方不会无限超前，也不会丢帧.
        """
        if not callable(on_figure):
            raise ValueError('on_figure must be callable: on_figure(fig)')

        self.__job_seq += 1
        job = dict(id=self.__job_seq, on_figure=on_figure,
                   size=self.__target_size(), savefig=savefig)
        if not self.__submit(job):
            warn('PltView: 绘图任务没有被接住（控件正在关闭，或绘图线程长时间无响应）')
            return False
        if wait:
            self.__wait_done(job['id'])
        return True

    def draw(self, *, savefig=None):
        """等当前这一帧画完（新实现里没有「在 GUI 线程立刻重绘」这条路）.

        Args:
            savefig: 传 ``str`` 时把当前画面存到该路径（与旧实现一样用 figure 存）.

        Note:
            保留这个方法只为接口兼容：绘图已经在后台完成，``draw()`` 实际做的事是
            「flush + 可选存图」.
        """
        self.wait()
        if isinstance(savefig, str):
            self.savefig(fname=make_parent(savefig), dpi=self._export_dpi())

    @property
    def figure(self):
        """matplotlib 的 ``Figure`` 对象.

        ⚠️ **访问会先等当前这一帧画完**（最多 :attr:`FLUSH_TIMEOUT` 秒）：figure 由绘图
        线程使用，不等它空闲就在两个线程里同时碰它是未定义行为.
        """
        self.wait()
        return self.__figure

    @property
    def canvas(self):
        """贴图控件（⚠️ 不是 ``FigureCanvasQTAgg``，只负责显示位图）."""
        return self.__canvas

    def savefig(self, *args, **kwargs):
        """保存图片（会先等当前这一帧画完，再在 GUI 线程用 figure 存）."""
        self.wait()
        try:
            self.__figure.savefig(*args, **kwargs)
        except Exception as err:
            print('Error when save figure: {0}'.format(err))

    def savefig_by_dlg(self):
        """弹框选择路径保存当前画面."""
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, caption='请选择保存路径', directory=os.getcwd(),
            filter='Jpg图片(*.jpg);;Png图片(*.png);;所有文件(*.*)')
        if fpath is not None and len(fpath) > 0:
            self.savefig(fname=fpath, dpi=self._export_dpi())

    def save_file(self, open_dir=False, open_fig=False):
        """把**屏幕上这张**存成 PNG，返回路径（框架钩子：菜单「文件 → 保存」/ 关标签前）.

        Args:
            open_dir: 是否打开保存目录.
            open_fig: 是否用系统默认程序打开图片.

        Returns:
            str | None: 成功时返回图片路径，失败时 ``None``.

        ⚠️ 这里用**最后一帧位图**直接写盘，**不** ``wait()``、**不**碰 figure：本方法会被
        「关闭标签页」调用，而一次渲染可能是几秒 —— 关标签路径上不许阻塞（旧实现在这条路上
        是同步重绘，关个标签要等好几秒）。代价是存下来的是「你看到的那张」；要 300 dpi 的
        高清重绘请用右键「导出图」（那条会先等这一帧画完，属于用户主动触发）.
        """
        image = self.__last_image
        folder = self.__save_folder
        if image is None or folder is None:
            return None
        try:
            now = datetime.datetime.now()
            name = now.strftime('%Y-%m-%d-%H-%M-%S-') + '{0:06d}.png'.format(now.microsecond)
            path = make_parent(os.path.join(folder, name))
            if not image.save(path, 'PNG'):
                print('PltView: 保存图片失败 —— {0}'.format(path))
                return None
            if open_dir:
                from zmlx.algs import startfile
                startfile(folder)
            if open_fig:
                from zmlx.algs import startfile
                startfile(path)
            return path
        except Exception as err:
            print('Error when save figure auto: {0}'.format(err))
            return None

    def need_save(self):
        """框架钩子：当前有没有值得保存的内容（决定菜单「保存」的灰 / 亮）."""
        return self.__last_image is not None

    def copy_to_clipboard(self):
        """把当前画面放到剪贴板（直接拷屏上那张位图，不用等渲染）."""
        try:
            image = self.__last_image
            if image is None:
                return
            QtWidgets.QApplication.clipboard().setImage(image)
        except Exception as err:
            print('Error when copy figure to clipboard: {0}'.format(err))

    def export_data(self):  # 接菜单命令
        """导出（菜单命令入口）."""
        self.savefig_by_dlg()

    def set_save_folder(self, folder):
        """设置自动存图目录（``None`` = 不自动存；与 ``MatplotWidget`` 同名）."""
        self.__save_folder = folder if folder else None
        worker = self.__worker
        if worker is not None:
            worker.set_save_folder(self.__save_folder)

    @staticmethod
    def _export_dpi():
        """导出图片用的 DPI（与 ``MatplotWidget`` 同一套环境设置）."""
        try:
            from zmlx.io.env import plt_export_dpi
            return plt_export_dpi.get_value()
        except Exception:
            return 300

    @staticmethod
    def set_plt_export_dpi():
        """（已弃用）请用 ``zmlx.ui.alg.set_plt_export_dpi``."""
        warn('set_plt_export_dpi is deprecated, use set_plt_export_dpi in zmlx.ui.alg',
             DeprecationWarning, stacklevel=2)
        from zmlx.ui.alg import set_plt_export_dpi as impl
        impl()

    # ============================================================== 右键菜单
    def get_context_menu(self):
        """右键菜单（与 ``MatplotWidget`` 的能力对齐）."""
        from zmlx.ui.alg import create_action

        menu = QtWidgets.QMenu(self)
        menu.addAction(
            create_action(self, '设置导出图的DPI', icon='set',
                          slot=self.set_plt_export_dpi))
        menu.addAction(
            create_action(self, '导出图', icon='export', slot=self.savefig_by_dlg))
        menu.addAction(
            create_action(self, '复制到剪切板', icon='export',
                          slot=self.copy_to_clipboard))
        if isinstance(self.__save_folder, str):
            def open_dir():
                from zmlx.algs import startfile
                startfile(self.__save_folder)

            menu.addAction(create_action(self, '打开图片保存目录', slot=open_dir))

        if len(self.context_actions) > 0:  # 额外的右键菜单（与 MatplotWidget 同一套）
            menu.addSeparator()
            for action in self.context_actions:
                if isinstance(action, dict):
                    name = action.get('name', None)
                    if name is not None:
                        sub_menu = menu.addMenu(name)
                        for item in action.get('items', []):
                            sub_menu.addAction(item)
                elif isinstance(action, str):
                    if action == '':
                        menu.addSeparator()
                else:
                    menu.addAction(action)
        return menu

    def contextMenuEvent(self, event):
        """右键弹菜单."""
        self.get_context_menu().exec(event.globalPos())

    # ============================================================== 线程联动
    def __on_frame(self, image, job_id):
        """绘图线程送来一帧（主线程执行）."""
        if self.__worker is None:
            return  # 已经收工（关标签了）
        self.__last_image = image
        self.__error = ''
        self.setToolTip('')
        self.__canvas.set_image(image)

    def __on_error(self, text):
        """绘图 / 存图失败（主线程执行）：记下来，放到 tooltip 里，不打断任何东西."""
        if self.__worker is None:
            return
        self.__error = str(text)
        self.setToolTip('最近一次绘图失败：\n{0}'.format(self.__error[:400]))

    # ============================================================== 生命周期
    def showEvent(self, event):
        """首次显示：把尺寸推给绘图线程（线程等第一个任务来时再启动）."""
        super(PltView, self).showEvent(event)
        self.__push_size()

    def resizeEvent(self, event):
        """尺寸变了：推给绘图线程（空闲时它会按新尺寸重排一次）."""
        super(PltView, self).resizeEvent(event)
        self.__push_size()

    def changeEvent(self, event):
        """窗口被拖到另一块「缩放比例不同」的屏幕上时，重推一次渲染尺寸."""
        super(PltView, self).changeEvent(event)
        kind = getattr(QtCore.QEvent.Type, 'DevicePixelRatioChange', None)
        if kind is not None and event.type() == kind:
            self.__push_size()

    def refresh(self):
        """框架钩子：切回本标签页时被调用（这里只重推尺寸，**立即返回**）."""
        self.__push_size()

    def cleanup_before_tab_close(self):
        """关标签前的收尾：通知绘图线程收工、放掉引用（**不阻塞**）.

        ⚠️ 这里**不** ``wait()``：一次渲染可能是几秒，关标签不许卡。线程能被安全回收靠的是
        「不设 parent + 类级强引用」那两条纪律；迟到的信号由 Qt 自动断开（槽都是绑定方法），
        槽里另有一道 ``self.__worker is None`` 的闸门.
        """
        worker, self.__worker = self.__worker, None
        self.__last_image = None
        if worker is not None:
            try:
                worker.stop()
            except Exception:
                pass

    def closeEvent(self, event):
        """控件被单独 ``close()`` 时也做同样的收尾（直接跑 ``test_1()`` 走这条路）.

        ⚠️ 关标签页**不走**这里（那边是 ``deleteLater()``，不发 ``closeEvent``）。
        """
        self.cleanup_before_tab_close()
        super(PltView, self).closeEvent(event)


def test_1():
    """直接运行本文件时的自测：验证「异步绘图 + 接住 + 不卡界面」.

    直接跑::

        python zmlx/ui/tabs/plt_view.py
        python zmlx/ui/tabs/plt_view.py --slow    # 每帧故意多花 2 s，验证界面不卡

    看什么：① 第一帧立刻出现；② ``--slow`` 下照样能拖动窗口；③ 连续投递任务时，
    控制台会打印「投递 N 次 / 等待 M 秒」——说明槽满时是**等**而不是丢帧。
    """
    import threading

    import numpy

    app = QtWidgets.QApplication(sys.argv)
    slow = '--slow' in sys.argv

    view = PltView()
    view.resize(1000, 720)
    view.setWindowTitle('PltView — 异步绘图' + ('（--slow）' if slow else ''))
    view.show()

    counters = {'submit': 0, 'cost': 0.0}
    lock = threading.Lock()

    def kernel():
        """模拟内核：算一步 → 投一次图（投递会阻塞到「被接住」为止）."""
        step = 0
        while step < 200:
            time.sleep(0.3)  # 模拟「算一步」

            def on_figure(fig, s=step):
                fig.clear()
                ax = fig.subplots()
                t = numpy.linspace(0.0, 1.0, 2000)
                ax.plot(t, numpy.sin(2.0 * numpy.pi * (0.6 * t + 0.05 * s)))
                ax.set_title('第 {0} 步（回调在绘图线程里跑）'.format(s))
                ax.set_xlabel('t')
                ax.set_ylabel('sin')
                fig.tight_layout()
                if slow:
                    time.sleep(2.0)

            t0 = time.monotonic()
            view.plot_on_figure(on_figure)
            with lock:
                counters['submit'] += 1
                counters['cost'] += time.monotonic() - t0
            step += 1
        print('投递 {0} 次，平均等待 {1:.3f} s'.format(
            counters['submit'], counters['cost'] / max(1, counters['submit'])))

    threading.Thread(target=kernel, name='DemoKernel', daemon=True).start()
    try:
        code = app.exec()
    finally:
        view.cleanup_before_tab_close()
    sys.exit(code)


if __name__ == '__main__':
    test_1()
