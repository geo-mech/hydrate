"""Matplotlib 画布（MatplotWidget —— 在**调用线程**渲染，只把贴图交给 GUI 线程）.

为什么重写（2026-10-18）
------------------------
旧实现用 ``FigureCanvasQTAgg``：它的 ``draw()`` 必须在 **GUI 线程**执行，而一次
重图（contourf 600x600 / 4 万三角面片）实测要 **数秒** —— 那几秒里整个界面是死的。

``gui.plot()`` 的调用链上，渲染其实**不必**发生在 GUI 线程：

    GUI 线程   ① 建 / 找标签页，拿到控件（这一步非 GUI 线程做不了）
    调用线程   ② 跑回调 + Agg 渲染成 QImage      ← 耗时全在这里，留在调用线程
    GUI 线程   ③ QPixmap.fromImage + drawPixmap   ≈ 6 ms

所以这里把画布换成「Agg 渲染 + 位图自绘」：``plot_on_figure()`` 变成**线程无关**
的方法 —— 谁调用就在谁的线程里画完，然后 ``sig_image.emit(QImage)``；GUI 线程只
负责把这张图贴上去（AutoConnection：跨线程自动排队，同线程则直连，与旧实现完全
同步）。于是计算内核照旧「画完才往下走」，既不丢帧，也不占 GUI 线程。

⚠️ 两条必须遵守的契约：

1. **回调里捕获的数据必须是快照**。回调现在在计算内核线程执行，旧实现是同步的
   （内核会等到画完），所以「传一个内核正在改写的数组」在旧实现下碰巧安全，
   现在会画出「半新半旧」的图。请 ``arr.copy()`` 再传。
2. **回调里只用面向对象的 API**（``figure.subplots()`` / ``ax.plot()`` ……），
   不要用 ``plt.plot()`` / ``plt.gca()`` —— 那些依赖 pyplot 的全局状态机，
   在多线程 / 多标签页下本来就不可靠。

不做重排（2026-10-18 的决定）
------------------------------
位图是定尺的：窗口被拉大后，屏幕上出现的是**拉伸过的旧图**（看着发虚），不会
自动重渲染 —— 这正是「拖动全程跟手」的代价。两个例外：

* **首次显示**补一次（``showEvent`` → ``_fit_once``）。否则「只画一次」的调用
  （建标签页时控件还没被布局，用的是 ``FALLBACK_SIZE``）会永远糊着。
* ``savefig()`` 先把 figure 的**英寸**对齐到控件当前尺寸（只改属性、不渲染），
  再由它自己按该尺寸重新渲染 —— 所以**导出的图永远清晰、宽高比永远正确**，
  与屏幕上糊不糊无关。

线程安全
--------
``figure`` / Agg canvas / 尺寸 / 自动保存的时间戳都归 ``__mutex`` 管：多个内核
线程同时画同一个控件会被串行化（旧实现靠「只在 GUI 线程执行」天然串行，现在必须
显式加锁）。``QPixmap`` 只在 GUI 线程生成，跨线程传递的载体是 ``QImage``。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
Modified by DeepSeek, 2026-10-18: 画布由 FigureCanvasQTAgg 改为「Agg + 位图自绘」，
    绘制挪到调用线程；公开接口保持不变。
"""

from zmlx.system import warn
import datetime
import os
import sys

from zmlx.system import make_parent
from zmlx.ui.alg import create_action
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets


class _BitmapCanvas(QtWidgets.QWidget):
    """只负责「把一张位图贴上去」的画布 —— 替代 ``FigureCanvasQTAgg``.

    ⚠️ 为什么不能再用 ``FigureCanvasQTAgg``：它继承 ``QPaintDevice``，Qt 规定这种
    对象**只能在 GUI 线程**被绘制；把 ``draw()`` 挪到内核线程会直接崩。所以拆成
    「别处渲染成 QImage」+「这里在 ``paintEvent`` 里贴一张 QPixmap」。

    ⚠️ ``resizeEvent`` **只记尺寸、不重排**（见模块文档「不做重排」）。没贴过图的
    时候什么都不画（首次绘制前是空白，与旧实现一致）。
    """

    #: 没有内容时的兜底尺寸（逻辑像素）
    DEFAULT_SIZE = (640, 480)

    #: 最小尺寸：够显示一点东西，又不至于把标签页的最小宽度顶大
    MIN_SIZE = (120, 80)

    def __init__(self, owner=None):
        super(_BitmapCanvas, self).__init__(owner)
        self._owner = owner
        self._pixmap = None
        self.setMinimumSize(self.MIN_SIZE[0], self.MIN_SIZE[1])
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding)

    def sizeHint(self):
        return QtCore.QSize(self.DEFAULT_SIZE[0], self.DEFAULT_SIZE[1])

    def pixmap(self):
        """当前贴着的位图（可能为 None）."""
        return self._pixmap

    def set_pixmap(self, pixmap):
        """换一张位图（**只能在 GUI 线程调用**）."""
        self._pixmap = pixmap
        self.update()

    def draw(self):
        """兼容旧 ``FigureCanvasQTAgg.draw()``：按当前尺寸重渲染（**不跑回调**）."""
        owner = self._owner
        if owner is not None:
            owner.draw()

    def paintEvent(self, event):
        pixmap = self._pixmap
        if pixmap is None or pixmap.isNull():
            return
        painter = QtGui.QPainter(self)
        try:
            dpr = pixmap.devicePixelRatio() or 1.0
            matched = (round(pixmap.width() / dpr) == self.width()
                       and round(pixmap.height() / dpr) == self.height())
            if matched:  # 尺寸正好：1:1 贴，不经插值
                painter.drawPixmap(0, 0, pixmap)
            else:  # 控件缩放后的拉伸（会发虚 —— 这是 2026-10-18 接受的代价）
                painter.setRenderHint(
                    QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
                painter.drawPixmap(self.rect(), pixmap)
        finally:
            painter.end()

    def resizeEvent(self, event):
        super(_BitmapCanvas, self).resizeEvent(event)
        owner = self._owner
        if owner is not None:
            owner._on_canvas_resized(
                self.width(), self.height(), self.devicePixelRatioF())


class MatplotWidget(QtWidgets.QWidget):
    support_sub_menu = True  # 支持子菜单(since 2026-1-5)

    #: 逻辑 DPI：figure 的英寸 = 逻辑像素 / 该值；实际渲染时 dpi 再乘设备像素比
    LOGICAL_DPI = 100.0

    #: 控件还没被布局摆好时的兜底尺寸（逻辑像素）
    FALLBACK_SIZE = (640, 480)

    #: 自动保存的最小间隔（秒）—— 沿用旧实现的 5 s
    SAVE_INTERVAL = 5.0

    #: 首次贴合时，若渲染锁被占（内核线程正在画）最多重试几次
    FIT_RETRY = 3

    #: 一帧画好了：``QImage``。渲染线程 emit，GUI 线程接收（仅用于贴图）
    sig_image = QtCore.pyqtSignal(QtGui.QImage)

    def __init__(self, parent=None):
        """
        初始化
        """
        super(MatplotWidget, self).__init__(parent)
        self.context_actions = []  # 额外的右键菜单

        # 受 __mutex 保护：figure / 渲染尺寸 / 自动保存时间戳
        self.__mutex = QtCore.QMutex()
        self.__size = (self.FALLBACK_SIZE[0], self.FALLBACK_SIZE[1], 1.0)
        self.__rendered = None      # 上一次渲染用的逻辑尺寸 (w, h)
        self.__time_save = None
        # 以下三个只在 GUI 线程读写
        self.__fitted = False       # 是否已按「真实的控件尺寸」渲染过一次
        self.__fit_scheduled = False

        self._prepare_matplotlib()

        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        # ⚠️ 直接建 Figure（不经 pyplot）：pyplot 的 current-figure 是**全局状态**，
        #    渲染发生在内核线程，再用它就等于让两个线程抢同一个全局变量。
        self.__figure = Figure()
        self.__agg = FigureCanvasAgg(self.__figure)
        if self.__dark:
            self.__figure.patch.set_facecolor('#1e1e1e')  # 与暗色主题一致

        self.__canvas = _BitmapCanvas(self)
        self.sig_image.connect(self._on_image)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 2025-7-5
        self.setLayout(layout)
        layout.addWidget(self.__canvas)

        now = datetime.datetime.now()
        name = now.strftime('%Y-%m-%d-%H-%M-%S-') + '{0:06d}'.format(now.microsecond)
        from zmlx.plt import get_plt_save_path
        self.__folder_save = get_plt_save_path(name)

    def _prepare_matplotlib(self):
        """一次性初始化：后端 / 暗色主题 / 中文字体（进程内可重复调用）."""
        import matplotlib
        for backend in ['QtAgg', 'Qt5Agg']:
            try:
                matplotlib.use(backend)
                break
            except Exception as err:
                print('Error (when use backend {0}): {1}'.format(backend, err))
        import matplotlib.pyplot as plt

        # 设置主题
        bg_color = self.palette().color(QtGui.QPalette.ColorRole.Window)
        self.__dark = bg_color.lightness() < 128
        if self.__dark:
            plt.style.use('dark_background')
        # 字体设置在主题之后，避免被主题覆盖
        try:
            from zmlx.plt import set_chinese_font
            set_chinese_font()
        except Exception:
            pass

    # ============================================================ 渲染（任意线程）
    def plot_on_figure(self, on_figure, *, savefig=None):
        """
        在控件上面绘图。其中on_figure是回调函数，接受一个Figure类型的参数。

        Args:
            on_figure: 回调函数（**在调用者自己的线程里执行**）
            savefig: 是否将图片保存为文件
        注意：
            如果多次绘图，建议在绘图之前先调用 figure.clear()

        ⚠️ 与旧实现的区别只有「在哪个线程画」：渲染留在调用线程，只有最后
        「贴图」那一步经信号交给 GUI 线程。返回时机仍是**画完之后**，所以
        调用方（计算内核）不会漏帧。
        """
        self._render(on_figure=on_figure, savefig=savefig)

    def draw(self, *, savefig=None):
        """
        按当前尺寸重画一遍（**不跑回调**），并按需保存.
        """
        self._render(on_figure=None, savefig=savefig)

    def _render(self, on_figure=None, savefig=None):
        """跑回调 → 渲染 → 贴图 → 按需保存（**调用者线程序列化，靠 __mutex**）."""
        if self._is_deleted(self):
            return
        self.__mutex.lock()
        try:
            image = self._render_locked(on_figure)
            if image is not None:
                # ⚠️ 持锁 emit 是安全的：跨线程是排队（不碰锁），同线程直连时槽里
                #    也只做 QPixmap 转换 —— 千万别在 _on_image 里调本类任何持锁方法。
                self.sig_image.emit(image)
            self._autosave_locked(savefig)
        finally:
            self.__mutex.unlock()

    def _render_locked(self, on_figure=None):
        """跑回调并渲染成 QImage（**调用方必须已持锁**）.

        Args:
            on_figure: 回调；None 表示只重画当前 figure.

        Returns:
            QImage | None: 渲染失败时为 None.
        """
        figure = self.__figure
        if callable(on_figure):
            try:
                on_figure(figure)
            except Exception as err:
                warn('meet exception <{0}> when run <{1}>'.format(err, on_figure))
        try:
            width, height, dpr = self.__size
            # ⚠️ 尺寸在这里才落定：控件缩放不触发重排，所以每一帧都按「当前尺寸」
            #    重设一遍 —— 于是「下一次绘图」天然就是新尺寸、清晰的。
            figure.set_dpi(self.LOGICAL_DPI * dpr)
            figure.set_size_inches(width / self.LOGICAL_DPI,
                                   height / self.LOGICAL_DPI)
            self.__agg.draw()
            self.__rendered = (width, height)
            return self._to_image(dpr)
        except Exception as err:
            warn('meet exception <{0}> when draw figure'.format(err))
            return None

    def _to_image(self, dpr):
        """把 Agg 的 RGBA 缓冲转成 QImage（**调用方必须已持锁**）."""
        import numpy as np
        buffer = self.__agg.buffer_rgba()
        array = np.asarray(buffer)
        height, width = array.shape[0], array.shape[1]
        # ⚠️ 必须 copy：QImage 只是「借用」这段内存，而 Agg 的缓冲下一帧就被覆盖。
        image = QtGui.QImage(
            bytes(buffer), width, height, array.strides[0],
            QtGui.QImage.Format.Format_RGBA8888).copy()
        image.setDevicePixelRatio(dpr)
        return image

    def _on_image(self, image):
        """收到一帧（**GUI 线程**）—— 转成 QPixmap 贴上去."""
        try:
            pixmap = QtGui.QPixmap.fromImage(image)
        except Exception as err:
            warn('meet exception <{0}> when convert image'.format(err))
            return
        if not pixmap.isNull():
            self.__canvas.set_pixmap(pixmap)

    # ============================================================ 尺寸 / 首次贴合
    def _on_canvas_resized(self, width, height, dpr):
        """绘图区尺寸变了（GUI 线程）—— **只记下来，不重排**."""
        self.__mutex.lock()
        try:
            self.__size = (max(1, int(width)), max(1, int(height)),
                           float(dpr) if dpr and dpr > 0 else 1.0)
        finally:
            self.__mutex.unlock()

    def showEvent(self, event):
        super(MatplotWidget, self).showEvent(event)
        # 首次显示后补一次：建标签页时控件还没被布局，第一帧用的是 FALLBACK_SIZE，
        # 「只画一次」的调用会一直糊着。只做一次，之后的缩放不再重排。
        if self.__fitted or self.__fit_scheduled:
            return
        self.__fit_scheduled = True
        QtCore.QTimer.singleShot(0, self._fit_once)

    def _fit_once(self, attempt=0):
        """按控件的真实尺寸补渲染一次（**不跑回调**，只做一次）.

        ⚠️ 三条纪律缺一不可：

        1. **`tryLock` 而不是 `lock`**：内核线程可能正在渲染（要几秒），在 GUI 线程
           等这把锁等于把整条事件循环停住 —— 实测就是「1.37 s 一次 tick 都没有」。
        2. 已经按**正确尺寸**渲染过就什么都不做（``__rendered`` 比对）。
        3. 拿不到锁就**稍后重试**（最多 ``FIT_RETRY`` 次），绝不在这里等。
        """
        self.__fit_scheduled = False
        if self.__fitted or self._is_deleted(self):
            return
        canvas = self.__canvas
        width, height = canvas.width(), canvas.height()
        if width < 2 or height < 2:
            return  # 还没布局好：放弃（下次 show 会再试）
        if not self.__mutex.tryLock():
            if attempt < self.FIT_RETRY:  # 有渲染在做：等它画完再试，但**不阻塞**
                self.__fit_scheduled = True
                QtCore.QTimer.singleShot(
                    120, lambda: self._fit_once(attempt + 1))
            return
        try:
            if self.__rendered == (width, height):  # 第一帧就是对的样子
                self.__fitted = True
                return
            self.__fitted = True
            image = self._render_locked(None)
            if image is not None:
                self.sig_image.emit(image)
        finally:
            self.__mutex.unlock()

    # ============================================================ 保存
    def set_save_folder(self, folder):
        self.__mutex.lock()
        try:
            self.__folder_save = folder
        finally:
            self.__mutex.unlock()

    @staticmethod
    def _export_dpi():
        try:
            from zmlx.io.env import plt_export_dpi
            return plt_export_dpi.get_value()
        except Exception:
            return 300

    def savefig(self, *args, **kwargs):
        """
        保存图片（**可以在任意线程调用**，内部按锁串行）
        """
        self.__mutex.lock()
        try:
            self._savefig_locked(*args, **kwargs)
        finally:
            self.__mutex.unlock()

    def _savefig_locked(self, *args, **kwargs):
        """保存图片（**调用方必须已持锁**）."""
        try:
            self._sync_size_locked()
            self.__figure.savefig(*args, **kwargs)
        except Exception as e:
            print('Error when save figure: {0}'.format(e))

    def _sync_size_locked(self):
        """把 figure 的英寸对齐到控件当前尺寸（**只改属性、不渲染**）.

        ⚠️ 为什么需要：位图不做重排，所以缩过窗口之后 figure 的英寸还停在旧值。
        ``savefig`` 会按英寸自己渲染，先把英寸对齐 —— 导出的宽高比就永远是对的，
        而这一步几乎零成本。
        """
        width, height, _ = self.__size
        self.__figure.set_size_inches(width / self.LOGICAL_DPI,
                                      height / self.LOGICAL_DPI)

    def _autosave_locked(self, savefig):
        """按 ``savefig`` 的语义决定要不要顺手存图（**调用方必须已持锁**）.

        Args:
            savefig: ``None`` = 按 ``SAVE_INTERVAL`` 节流自动存；``True`` / ``False``
                = 强制存 / 不存；``str`` = 存到指定路径。
        """
        if isinstance(savefig, str):
            self._savefig_locked(fname=make_parent(savefig), dpi=self._export_dpi())
            self.__time_save = datetime.datetime.now()
            return

        folder = self.__folder_save
        if folder is None:
            return

        now = datetime.datetime.now()
        if savefig is None:  # 之前保存过，则检查间隔
            if self.__time_save is not None:
                savefig = (now - self.__time_save).total_seconds() >= self.SAVE_INTERVAL
            else:  # 之前尚未保存过，则直接保存
                savefig = True
        if not savefig:
            return

        name = now.strftime('%Y-%m-%d-%H-%M-%S-') + '{0:06d}.png'.format(now.microsecond)
        path = make_parent(os.path.join(folder, name))
        self._savefig_locked(fname=path, dpi=self._export_dpi())
        self.__time_save = now  # 记录时间

    def savefig_by_dlg(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            caption="请选择保存路径",
            directory=os.getcwd(),
            filter='Jpg图片(*.jpg);;Png图片(*.png);;所有文件(*.*)')
        if fpath is not None and len(fpath) > 0:
            self.savefig(fname=fpath, dpi=self._export_dpi())

    def save_file(self, open_dir=False, open_fig=False):
        """
        自动保存图片到默认路径（以当前时间生成文件名）. 注意，此函数会被系统菜单自动调用

        Args:
            open_dir: 是否打开保存目录
            open_fig: 是否用系统默认程序打开图片
        Returns:
            成功时返回图片文件路径，失败时返回 None
        """
        try:
            self.__mutex.lock()
            try:
                folder = self.__folder_save
                now = datetime.datetime.now()
                name = now.strftime('%Y-%m-%d-%H-%M-%S-') + '{0:06d}.png'.format(now.microsecond)
                path = make_parent(os.path.join(folder, name))
                self._savefig_locked(fname=path, dpi=self._export_dpi())
            finally:
                self.__mutex.unlock()
            if open_dir:
                from zmlx.algs import startfile
                startfile(folder)
            if open_fig:
                from zmlx.algs import startfile
                startfile(path)
            return path
        except Exception as e:
            print('Error when save figure auto: {0}'.format(e))
            return None

    def copy_to_clipboard(self):
        """
        将图片复制到剪切板（保存到临时文件）
        """
        try:
            from zmlx.system import app_data
            now = datetime.datetime.now()
            name = now.strftime('%Y-%m-%d-%H-%M-%S-') + '{0:06d}.png'.format(now.microsecond)
            path = app_data.temp(name)
            self.savefig(fname=path, dpi=self._export_dpi())
            pixmap = QtGui.QPixmap(path)
            QtWidgets.QApplication.clipboard().setPixmap(pixmap)
        except Exception as e:
            print('Error when copy figure to clipboard: {0}'.format(e))

    def export_data(self):  # 接菜单命令
        self.savefig_by_dlg()

    # ============================================================ 属性
    @property
    def figure(self):
        """matplotlib 的 Figure.

        ⚠️ 它可能同时在别的线程被渲染（见模块文档）。要在外部读写它，请走
        :meth:`plot_on_figure` / :meth:`savefig`（内部持锁），不要单独拿着它
        跨线程拼装 artist。
        """
        return self.__figure

    @property
    def canvas(self):
        """绘图区控件（``_BitmapCanvas``）.

        ⚠️ 2026-10-18 起它不再是 ``FigureCanvasQTAgg``：仍提供 ``draw()``
        （= 按当前尺寸重渲染，不跑回调），但**没有** ``buffer_rgba()`` /
        ``get_renderer()`` 这类 matplotlib 画布接口。
        """
        return self.__canvas

    @staticmethod
    def _is_deleted(obj):
        """Qt 对象背后的 C++ 对象是否已被销毁（销毁后再碰会抛 RuntimeError）."""
        try:
            import sip
        except Exception:
            try:
                from PyQt6 import sip
            except Exception:
                try:
                    from PyQt5 import sip
                except Exception:
                    return False
        try:
            return bool(sip.isdeleted(obj))
        except Exception:
            return False

    @staticmethod
    def set_plt_export_dpi():
        warn(
            'set_plt_export_dpi is deprecated, use set_plt_export_dpi in zmlx.ui.alg',
            DeprecationWarning, stacklevel=2
        )
        from zmlx.ui.alg import set_plt_export_dpi as impl
        impl()

    # ============================================================ 右键菜单
    def get_context_menu(self):
        from zmlx.ui.alg import set_plt_export_dpi
        menu = QtWidgets.QMenu(self)
        menu.addAction(
            create_action(
                self, '设置导出图的DPI', icon='set',
                slot=set_plt_export_dpi))
        menu.addAction(
            create_action(
                self, '导出图', icon='export',
                slot=self.savefig_by_dlg))
        menu.addAction(
            create_action(
                self, '复制到剪切板', icon='export',
                slot=lambda: self.copy_to_clipboard()))

        folder = self.__folder_save
        if folder is not None:  # 打开自动保存目录
            if isinstance(folder, str):
                def open_dir():
                    from zmlx.algs import startfile
                    startfile(folder)

                menu.addAction(
                    create_action(
                        self, '打开图片保存目录',
                        slot=open_dir))

        # 尝试获得提前存储的额外的Action
        if len(self.context_actions) > 0:
            menu.addSeparator()
            for action in self.context_actions:
                if isinstance(action, dict):
                    name = action.get('name', None)
                    if name is not None:
                        sub_menu = menu.addMenu(name)
                        assert isinstance(sub_menu, QtWidgets.QMenu)
                        for item in action.get('items', []):
                            sub_menu.addAction(item)
                elif isinstance(action, str):
                    if action == '':
                        menu.addSeparator()
                else:
                    menu.addAction(action)

        return menu

    def contextMenuEvent(self, event):  # 右键菜单
        self.get_context_menu().exec(event.globalPos())


def test_1():
    """直接运行本文件时的自测：后台线程 + 慢绘图，验证界面不卡.

    直接跑::

        python zmlx/ui/widgets/plt.py          # 每帧约 0.05 s
        python zmlx/ui/widgets/plt.py --slow   # 每帧故意多花 1.2 s

    看什么：① 图在更新；② ``--slow`` 下照样能拖动窗口、点右键菜单 —— 说明渲染
    确实不在 GUI 线程里跑。
    """
    import threading
    import time

    import numpy

    app = QtWidgets.QApplication(sys.argv)
    widget = MatplotWidget()
    widget.resize(1000, 740)
    slow = '--slow' in sys.argv
    widget.setWindowTitle(
        'MatplotWidget — 渲染在调用线程' + ('（--slow）' if slow else ''))
    widget.set_save_folder(None)  # 自测不落盘，别改用户的图片目录

    def kernel(fig, step):
        axes = fig.subplots(2, 1)
        t = numpy.linspace(0.0, 1.0, 4000)
        axes[0].plot(t, numpy.sin(2 * numpy.pi * (0.8 * t + 0.05 * step)))
        axes[0].set_title('第 {0} 步'.format(step))
        axes[0].set_xlabel('t')
        x = numpy.linspace(-1.0, 1.0, 200)
        xx, yy = numpy.meshgrid(x, x)
        axes[1].imshow(numpy.sin(3 * xx + 0.3 * step) * numpy.cos(2.5 * yy),
                       origin='lower', aspect='auto', cmap='viridis')
        fig.tight_layout()
        if slow:
            time.sleep(1.2)  # 模拟「重图」

    stop = threading.Event()

    def worker():
        for step in range(100000):
            if stop.is_set():
                return
            widget.plot_on_figure(lambda fig, s=step: kernel(fig, s))
            if stop.wait(1.0):
                return

    widget.show()
    threading.Thread(target=worker, name='DemoKernel', daemon=True).start()
    app.aboutToQuit.connect(stop.set)
    try:
        code = app.exec()
    finally:
        stop.set()
    sys.exit(code)


if __name__ == "__main__":
    test_1()
