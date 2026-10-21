"""Matplotlib 画布（MatplotWidget — matplotlib figure 嵌入 Qt）.

画布是 ``FigureCanvasQTAgg``，**只在 GUI 线程使用**：``plot_on_figure()`` / ``draw()`` /
``savefig()`` 等公开方法**必须在 GUI 线程调用** —— 这是 Qt 控件的契约，本类**不做**跨线程
投递。后台线程要绘图，请把调用交给 ``gui.call(...)``，或放进 ``gui.start`` 的 ``post_task``
（那里本来就是 GUI 线程）。

主题
----
**构造时**判一次（供画布首次自绘用），**每次绘制前**再判一次（跟上用户切换的主题）。
依据是 ``QApplication`` / 主窗口的调色板，以及主窗口**样式表**里的背景色 ——
「设置 → 样式表」走 ``setStyleSheet``，它**不改 palette**，只看控件自己的 ``palette()``
永远判不出暗色。暗色套 ``dark_background``，浅色恢复 ``default``。

⚠️ ``dark_background`` 会改**全局** ``rcParams``；而 ``plt.style.use`` 每次都会把
``font.sans-serif`` 与 ``axes.unicode_minus`` 重置掉，所以 :meth:`_ensure_chinese_font`
在每次 ``style.use`` 之后兜一次（``set_chinese_font()`` 有 ``@execute_once``，补不回来）。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
Modified by DeepSeek, 2026-10-31: 画布改回 ``FigureCanvasQTAgg`` —— 绘制回 GUI 线程
Modified by DeepSeek, 2026-10-31: 暗色主题改为「每次绘制前按应用 / 主窗口调色板与窗口
    样式表判断」—— 原来看控件自己的 ``palette()``，在用户只设了样式表时永远判不出暗色。
Modified by DeepSeek, 2026-11-01: 删掉「首帧覆盖层」整套（``_cover`` / ``_blank_layer`` /
    ``paintEvent`` / ``_fill_first_frame`` / ``_needs_cover`` / ``_frame_ready`` 等）——
    它只为「建页与首绘分属两次 GUI 命令」的那条调用路径服务（那时事件循环会在两者之间
    转一圈，把画布的初始白底送上屏）。调用路径回退成一次命令后不再需要，改为
    **构造时套一次主题**；同时去掉 ``_render`` 里重复的第二次 ``_prepare_frame``。
Modified by DeepSeek, 2026-11-01: 删掉 ``_run_in_gui`` / ``_in_gui_thread`` 跨线程投递 ——
    调用路径回退后，本仓与外部工作区（``igg-hydrate-works`` 24 处）对 ``plot_on_figure`` /
    ``savefig`` 的调用**全部在 GUI 线程**（``post_task`` 也在 GUI 线程），这一层没有真实需求，
    只是掩盖跨线程误用。控件方法恢复成「就地执行」，并把只为投递而拆的
    ``_savefig`` / ``_savefig_by_dlg`` / ``_copy_to_clipboard`` 合并回公开方法。
"""

from zmlx.system import warn
import datetime
import os
import sys

from zmlx.system import make_parent
from zmlx.ui.alg import create_action
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets


class MatplotWidget(QtWidgets.QWidget):
    support_sub_menu = True  # 支持子菜单(since 2026-1-5)

    #: 自动保存的最小间隔（秒）
    SAVE_INTERVAL = 5.0

    def __init__(self, parent=None):
        """
        初始化
        """
        super(MatplotWidget, self).__init__(parent)
        self.context_actions = []  # 额外的右键菜单

        self._figure, self._canvas = self._create_canvas(self)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 2025-7-5
        self.setLayout(layout)
        layout.addWidget(self._canvas)

        # ⚠️ 构造时就套一次主题：``FigureCanvasQTAgg`` 首次显示会调自己的 ``draw()``，
        #    那一刻若 rcParams 还是默认的浅色，画出来就是白底 —— 暗色窗口下于是「先白
        #    后暗」。这里先判一次；构造时样式表可能还没加载、判成浅色也没关系，
        #    ``_render`` 每次绘制前会按当时状态重判并纠正。
        try:
            self._apply_theme()
        except Exception as err:
            warn('meet exception <{0}> when apply theme'.format(err))

        now = datetime.datetime.now()
        name = now.strftime('%Y-%m-%d-%H-%M-%S-') + '{0:06d}'.format(now.microsecond)
        from zmlx.plt import get_plt_save_path
        self.__folder_save = get_plt_save_path(name)
        self.__time_save = None

    @staticmethod
    def _create_canvas(parent):
        """建一个 ``FigureCanvasQTAgg``，返回 ``(figure, canvas)``.

        ⚠️ 必须在 **GUI 线程**里调用 —— 它创建的是 Qt 控件（同时也是 matplotlib
        的 ``FigureCanvasQTAgg``，只能在自己的 GUI 线程里被绘制）。

        Args:
            parent: 画布控件的父控件。

        Returns:
            Tuple[Figure, FigureCanvasQTAgg]: figure 与它的 Qt 画布。
        """
        for backend in ['QtAgg', 'Qt5Agg']:
            try:
                import matplotlib
                matplotlib.use(backend)
                break
            except Exception as err:
                print('Error (when use backend {0}): {1}'.format(backend, err))
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        import matplotlib.pyplot as plt

        figure = plt.figure()
        # ⚠️ 不是 ``FigureCanvasQTAgg(figure, parent=parent)``：本仓现用的
        #    matplotlib 3.10 里 ``__init__`` 只收 ``figure``，传 parent 会抛
        #    ``unexpected keyword argument 'parent'``。改由布局接管父子关系
        #    （画布在构造后立刻被 addWidget 进本控件）。
        canvas = FigureCanvasQTAgg(figure)

        # 字体设置在主题之前（主题只改颜色，字体保持中文设置）
        try:
            from zmlx.plt import set_chinese_font
            set_chinese_font()
        except Exception:
            pass
        # 暗色主题在**每次绘制前**再套一次（见 :meth:`_apply_theme`）：构造这一刻
        # 用户的样式表可能还没加载，只看这里会判错，所以这里不是唯一的判断点。
        return figure, canvas

    # ============================================================ 主题（暗色自适应）
    @staticmethod
    def _in_dark_mode(widget):
        """当前界面是不是暗色主题（读**应用级**调色板，不是控件自己的）.

        依次看三处，**任意一处**判定为暗就返回 True：

        1. ``QApplication`` 的调色板（整体主题，例如 ``QApplication.setPalette``）；
        2. **主窗口**的调色板（窗口底色的亮度）；
        3. **窗口样式表**里的背景色 —— 这是「设置 → 样式表」实际生效的那条路：它走的是
           ``win.setStyleSheet(...)``，而样式表**不改 palette**。

        ⚠️ **不能只看控件自己的 ``palette()``**：实测无论先建控件还是先套样式表，
           拿到的都是默认浅色（window 亮度 239）—— 用户存的 ``zml_window_style.qss``
           是在**标签页全部建完之后**才 ``setStyleSheet`` 到窗口上的。那种写法下本控件
           永远判不出暗色，图会一直是白底。

        Args:
            widget: 调用者所在控件（用于向上找主窗口）。

        Returns:
            bool: True 表示应当使用暗色主题。
        """
        try:
            app = QtWidgets.QApplication.instance()
            if app is not None and app.palette().color(
                    QtGui.QPalette.ColorRole.Window).lightness() < 128:
                return True
        except Exception as err:
            print('Error when read app palette: {0}'.format(err))

        try:
            window = widget.window()
        except Exception:
            window = None
        if not isinstance(window, QtWidgets.QMainWindow):
            # 控件还没 ``addTab`` 时 ``window()`` 返回它自己 —— 向 ``gui`` 要主窗口。
            # ⚠️ **不要遍历 ``app.topLevelWidgets()`` 猜主窗口**：matplotlib 的
            #    ``FigureManagerQT`` 内部也建了一个**同样叫 MainWindow** 的 QMainWindow，
            #    会排在候选里（实测：构造一个 MatplotWidget 就多出一个），
            #    于是构造时可能挑错窗口、把暗色判成浅色。
            try:
                from zmlx.ui.gui_buffer import gui
                candidate = gui.window()
                if isinstance(candidate, QtWidgets.QMainWindow):
                    window = candidate
            except Exception as err:
                print('Error when ask gui for main window: {0}'.format(err))
        if window is None:
            return False

        try:
            if window.palette().color(
                    QtGui.QPalette.ColorRole.Window).lightness() < 128:
                return True
        except Exception as err:
            print('Error when read window palette: {0}'.format(err))

        try:  # 「设置 → 样式表」那一份：样式表里写下的背景色
            color = MatplotWidget._qss_background(window.styleSheet())
        except Exception as err:
            print('Error when parse window style sheet: {0}'.format(err))
            return False
        return color is not None and color.lightness() < 128

    @staticmethod
    def _qss_background(text):
        """从样式表文本里取窗口的背景色.

        只认 ``background [-]color``（以及简写 ``background``），取**最后一条**规则里
        那条声明 —— 样式表后面的规则优先级更高，与 Qt 的行为一致。

        Args:
            text: 样式表文本。

        Returns:
            QtGui.QColor | None: 找不到时为 None。
        """
        import re
        if not isinstance(text, str) or len(text) == 0:
            return None
        color = None
        for group in re.finditer(r'\{([^}]*)\}', text):
            # ⚠️ 不能要求声明前有 ``;``：每条规则的**第一条**声明前面什么都没有。
            for value in re.findall(
                    r'background(?:-color)?\s*:\s*([^;}]+)', group.group(1)):
                parsed = MatplotWidget._parse_color(value)
                if parsed is not None:
                    color = parsed  # 后面的覆盖前面的
        return color

    @staticmethod
    def _parse_color(value):
        """把 ``#abc`` / ``#aabbcc`` / ``rgb(...)`` / ``颜色名`` 解析成 ``QColor``.

        Args:
            value: 样式表里那段颜色文字。

        Returns:
            QtGui.QColor | None: 解析不出来时为 None（例如 ``background: none``）。
        """
        import re
        text = value.split('!important')[0].strip()
        match = re.search(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})', text)
        if match is not None:
            code = match.group(1)
            if len(code) == 3:
                code = ''.join(c * 2 for c in code)
            return QtGui.QColor('#' + code)
        match = re.search(r'rgba?\(([^)]*)\)', text, re.IGNORECASE)
        if match is not None:
            parts = [p for p in re.split(r'[,\s/]+', match.group(1)) if len(p) > 0]
            if len(parts) >= 3:
                try:
                    return QtGui.QColor(int(float(parts[0])), int(float(parts[1])),
                                        int(float(parts[2])))
                except Exception:
                    return None
        name = text.strip().lower()
        if len(name) > 0 and name not in ('none', 'transparent', 'inherit'):
            color = QtGui.QColor(name)
            if color.isValid():
                return color
        return None

    @staticmethod
    def _ensure_chinese_font():
        """确保中文字体排在 ``font.sans-serif`` 最前面，并让负号用 ASCII ``-``.

        ⚠️ **为什么每次绘制前都要调**：``plt.style.use(...)``（本类的
        :meth:`_apply_theme` 每次绘制都会按主题调一次）会把 ``font.sans-serif``
        **整个重置**成 matplotlib 的默认值（``DejaVu Sans`` 打头），并把
        ``axes.unicode_minus`` 重置回 ``True``；而
        :func:`zmlx.plt.set_chinese_font` 被 ``@execute_once`` 包着，只在进程里
        执行一次，之后不会再补回来。于是出现两类问题：

        1. 中文标题 / 刻度变成 ``Glyph ... missing from font(s) DejaVu Sans``；
        2. **刻度上的负号变成小方框**：``axes.unicode_minus=True`` 时负号写成
           ``U+2212``（数学减号），而 **SimHei 恰好没有这个字形**（实测；DejaVu
           与 YaHei 有）。换成 ASCII 的 ``-`` 则所有中文字体都覆盖。

        ⚠️ 具体实现（按平台挑候选字体、读字体缓存、幂等判断）只在
        :func:`zmlx.plt.ensure_chinese_font` 里有一份 —— **这里只做转接**。原先本方法
        自带一份副本、还要 ``in_macos``，而那个名字并未导入：在 Linux / macOS 上
        ``in_windows()`` 为假、紧接着求值 ``in_macos()`` 就抛 ``NameError``，被下面
        的 ``except`` 吞成一句 ``Error when ensure chinese font``，字体于是**永远没被
        设上**（界面里的中文全是方框）。
        """
        try:
            from zmlx.plt import ensure_chinese_font
            return ensure_chinese_font()
        except Exception as err:
            print('Error when ensure chinese font: {0}'.format(err))
            return []

    def _apply_theme(self):
        """按当前界面是否暗色，把主题套到 figure 上（**GUI 线程**）.

        * **暗色**：套整套 ``dark_background``（深底 + 浅色文字 / 刻度 / 网格）；
        * **浅色**：恢复 ``default`` 主题，并把 ``patch`` 清回 ``none``。⚠️ 必须清，
          因为 ``dark_background`` 与手工设的 ``set_facecolor`` 都留在 figure 上，
          只换风格会把白底覆盖成深色（就是「切回浅色后图还是黑的」那个毛病）。

        之后统一把 figure 底色对齐窗口底色。

        调用点两处：**构造时**一次（供画布首次自绘），以及**每次绘制前**
        （:meth:`_prepare_frame`，用于跟上用户切换的主题）。
        """
        import matplotlib as mpl
        import matplotlib.pyplot as plt
        if self._in_dark_mode(self):
            plt.style.use('dark_background')
            figure_color = '#1e1e1e'  # 与暗色窗口一致
        else:
            plt.style.use('default')
            mpl.rcParams['figure.facecolor'] = 'white'
            figure_color = mpl.rcParams['figure.facecolor']
        self._figure.patch.set_facecolor('none')
        for ax in self._figure.axes:
            # ⚠️ 逐轴重设底色：``add_subplot()`` 那一刻就把当时的 ``axes.facecolor``
            #    记到了轴对象上，只改 rcParams 看不到效果。
            ax.set_facecolor(mpl.rcParams['axes.facecolor'])
        self._figure.patch.set_facecolor(figure_color)
        # ⚠️ 必须紧跟在 style.use 之后：`style.use`（上面刚调过）会把
        #    ``font.sans-serif`` 整个重置回 DejaVu Sans，中文会变成方框。
        self._ensure_chinese_font()

    # ============================================================ 绘图（GUI 线程）
    # ============================================================ 绘图（GUI 线程）
    def plot_on_figure(self, on_figure, *, savefig=None):
        """
        在控件上面绘图。其中on_figure是回调函数，接受一个Figure类型的参数。

        ⚠️ **必须在 GUI 线程调用**（Qt 控件的契约）：本方法不做跨线程投递。后台线程
        要绘图，请用 ``gui.call(lambda: widget.plot_on_figure(...))``，或把绘制放进
        ``gui.start`` 的 ``post_task``（那是 GUI 线程）。回调本身也在 GUI 线程执行，
        因此**不必**为它准备数据快照；代价是重图期间界面停住。

        Args:
            on_figure: 回调函数
            savefig: 是否将图片保存为文件（``None`` = 按 ``SAVE_INTERVAL`` 节流自动存；
                ``True`` / ``False`` = 强制存 / 不存；``str`` = 存到指定路径）
        注意：
            如果多次绘图，建议在绘图之前先调用 figure.clear()
        """
        self._render(on_figure, savefig)

    def draw(self, *, savefig=None):
        """
        按当前 figure 重画一遍（**不跑回调**），并按需保存.

        Args:
            savefig: 保存语义同 :meth:`plot_on_figure`。
        """
        self._render(None, savefig)

    def _render(self, on_figure=None, savefig=None):
        """跑回调 → 绘制 → 按需保存（**必须在 GUI 线程执行**）."""
        self._prepare_frame()  # 按当前主题调好 figure（字体 / 底色）
        if on_figure is not None:
            try:
                on_figure(self._figure)
            except Exception as err:
                warn('meet exception <{0}> when run <{1}>'.format(err, on_figure))
        try:
            self._canvas.draw()
        except Exception as err:
            warn('meet exception <{0}> when draw figure'.format(err))
        self._autosave(savefig)

    def _prepare_frame(self):
        """绘制前：先确保中文字体，再按当前界面主题调 figure.

        任何异常都不该打断绘图，故这里分开兜住 —— **字体那一句不能因为主题出错而被跳过**。
        """
        try:
            self._ensure_chinese_font()
        except Exception as err:
            warn('meet exception <{0}> when ensure font'.format(err))
        try:
            self._apply_theme()
        except Exception as err:
            warn('meet exception <{0}> when prepare frame'.format(err))

    # ============================================================ 保存
    def set_save_folder(self, folder):
        """设置自动保存目录（``None`` = 不自动保存）."""
        self.__folder_save = folder

    @staticmethod
    def _export_dpi():
        try:
            from zmlx.io.env import plt_export_dpi
            return plt_export_dpi.get_value()
        except Exception:
            return 300

    def savefig(self, *args, **kwargs):
        """保存图片（**GUI 线程**；出错只打印，不抛）."""
        try:
            self._figure.savefig(*args, **kwargs)
        except Exception as err:
            print('Error when save figure: {0}'.format(err))

    def _autosave(self, savefig):
        """按 ``savefig`` 的语义决定要不要顺手存图（**GUI 线程**）.

        Args:
            savefig: ``None`` = 按 ``SAVE_INTERVAL`` 节流自动存；``True`` / ``False``
                = 强制存 / 不存；``str`` = 存到指定路径。
        """
        if isinstance(savefig, str):
            self.savefig(fname=make_parent(savefig), dpi=self._export_dpi())
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
        self.savefig(fname=path, dpi=self._export_dpi())
        self.__time_save = now  # 记录时间

    def savefig_by_dlg(self):
        """弹框选路径并导出图片（**GUI 线程**）."""
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
            folder = self.__folder_save
            now = datetime.datetime.now()
            name = now.strftime('%Y-%m-%d-%H-%M-%S-') + '{0:06d}.png'.format(now.microsecond)
            path = make_parent(os.path.join(folder, name))
            self.savefig(fname=path, dpi=self._export_dpi())
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

    def copy_to_clipboard(self):
        """将图片复制到剪切板（保存到临时文件；**GUI 线程**）."""
        try:
            from zmlx.system import app_data
            now = datetime.datetime.now()
            name = now.strftime('%Y-%m-%d-%H-%M-%S-') + '{0:06d}.png'.format(now.microsecond)
            path = app_data.temp(name)
            self.savefig(fname=path, dpi=self._export_dpi())
            pixmap = QtGui.QPixmap(path)
            QtWidgets.QApplication.clipboard().setPixmap(pixmap)
        except Exception as err:
            print('Error when copy figure to clipboard: {0}'.format(err))

    def export_data(self):  # 接菜单命令
        self.savefig_by_dlg()

    # ============================================================ 属性
    @property
    def figure(self):
        """matplotlib 的 Figure.

        ⚠️ 它属于 **GUI 线程**（figure 只在该线程被绘制）。要在外部读写它，请把操作
        交给 :meth:`plot_on_figure` / :meth:`savefig`（两者都必须在 GUI 线程调用）。
        """
        return self._figure

    @property
    def canvas(self):
        """绘图区控件（``FigureCanvasQTAgg``）."""
        return self._canvas

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
    """直接运行本文件时的自测：在 GUI 线程里定时推帧."""
    import numpy

    app = QtWidgets.QApplication(sys.argv)
    widget = MatplotWidget()
    widget.resize(1000, 740)
    widget.setWindowTitle('MatplotWidget — 在 GUI 线程绘制')
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

    state = {'step': 0}

    def tick():
        state['step'] += 1
        widget.plot_on_figure(lambda fig: kernel(fig, state['step']))

    timer = QtCore.QTimer(widget)
    timer.timeout.connect(tick)
    timer.start(1000)  # 每秒推一帧；定时器本来就在 GUI 线程触发
    widget.show()
    tick()  # 先画一帧，别让窗口空着
    sys.exit(app.exec())


if __name__ == "__main__":
    test_1()
