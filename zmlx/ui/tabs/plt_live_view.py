"""实时绘图视图（PltLiveView — 基于 matplotlib 的自动刷新绘图控件）.

**一句话**：给它一个线程安全的共享容器 + 一个「把数据画到 figure 上」的回调，它就
在**后台线程**里循环取数据、绘图、刷新画面；界面全程不卡。

公开接口只有一个::

    view = PltLiveView()
    view.set_data(shared, on_figure)

============================  ==================================================
参数                           说明
============================  ==================================================
``shared``                    ``zmlx.ui.utils.shared.SharedValue`` 一类的线程安全容器.
                              只要求有 ``get()`` 与 ``set(value)``（鸭子类型，不限于那一个类）.
``on_figure(fig, data)``      把 ``data`` 画到 ``fig`` 上. ⚠️ **在绘图线程里执行**，
                              只许碰 ``fig`` 与 ``data``，**不许**碰任何 Qt 控件.
============================  ==================================================

⚠️ 除 ``set_data`` 之外的那些方法（``refresh`` / ``cleanup_before_tab_close`` /
``save_file`` / ``need_save``）都是 ``MainWindow`` / ``TabWidget`` 约定的**框架钩子**，
由框架按需调用，不是本控件的数据接口。

三方线程怎么配合
----------------

::

    计算内核（另一个线程）        本控件（绘图线程）                GUI 线程
    ────────────────────        ──────────────────────          ─────────────
    算完一步 →
    共享格子空着吗？
      ├─ 空 → 准备数据（耗时）→ set(data)
      └─ 有 → 跳过（不重复准备）
                                每轮：睡 interval 秒
                                  data = shared.get()
                                    ├─ None → 本轮不画，继续睡
                                    └─ 有值 → 「取走」（置 None）
                                              → on_figure(fig, data)
                                              → Agg 渲染成位图
                                              → 信号 ──────────→ 贴到屏幕上
                                                                  （只做一次拷图）

⚠️ **先取走、再绘图**是刻意的顺序：内核一看到「空了」就能**同时**去准备下一份，于是
「算」与「画」并行。若改成「画完再清空」，绘图那几秒内核只能白等。

⚠️ 这也意味着「本控件忙 / 被隐藏的时候，内核不会准备新数据」—— 它看到格子里有没被
取走的值就一直跳过。所以暂停期间**没有额外计算消耗**；代价是恢复后第一帧可能稍旧，
内核那边「每过一段时间强制刷新一次」的保底策略正好补上这一点。

为什么不在 GUI 线程里画（为什么不直接复用 ``MatplotWidget``）
--------------------------------------------------------------

⚠️ **2026-10-18 更新**：``MatplotWidget`` 现在**已经**是「调用线程渲染 + 位图自绘」
（见 ``widgets/plt.py`` 的模块文档），不再有下面这个问题。本控件仍然保留自己的
绘图线程，理由变了 —— **它需要在没人调用的时候也按间隔自动刷新**（常驻循环），
而 ``MatplotWidget`` 是事件驱动的（有 plot 请求才画）。两者需求不同，不是重复实现。

下面的分析是当时的判断依据，保留备查：``MatplotWidget`` 那时内嵌的是
``FigureCanvasQTAgg``，它把 figure 画到一个 **Qt 的 QPaintDevice** 上，而 Qt 规定
「只能在自己的 GUI 线程里碰 QPaintDevice」。于是只有两条路：

1. **在 GUI 线程里** ``canvas.draw()``：一次几秒的绘图 = 界面卡死几秒（拖动、点按钮
   全部无响应）。本控件的卖点恰恰是「重图也照刷」，所以不能选它。
2. **在后台线程里**用 ``FigureCanvasAgg`` 把图渲染成像素，GUI 线程只负责贴图
   （一次 ``drawPixmap``，微秒级）。**本控件走这条。**

代价：屏幕上看到的是**位图**，不是可交互的画布 —— 没有 matplotlib 工具栏（框选缩放、
平移、改轴范围）。换来的是「绘图再慢也不卡界面」这条硬指标。哪天确实需要交互，正确
做法是「点一下 → 在 GUI 线程里用这份数据重画一次」（用户主动触发，他愿意等那几秒），
而不是让每一帧都阻塞 GUI。

⚠️ 因此 ``on_figure`` 收到的是**绘图线程私有的那个 figure**（Agg 后端），不是
``MatplotWidget`` 里的那个。它就是个普通的 ``matplotlib.figure.Figure``，
``fig.subplots()`` / ``fig.clear()`` / ``fig.suptitle()`` / ``fig.tight_layout()``
都照常用。

⚠️ 渲染分辨率跟着控件走：宽高取绘图区的**逻辑像素**，DPI 取 ``100 × dpr``，所以
高 DPI 屏上文字不会糊（位图尺寸 = 逻辑尺寸 × 缩放比例，DrawPixmap 时正好 1:1）。

⚠️ **回调抛异常不会弄死线程**：捕获、按次数上报（前 3 次发警告）、在状态栏显示原因，
然后丢掉这一帧，下一轮照常。回调里若真出错，别指望界面变成红色 —— 看状态栏那句话。

显示 / 隐藏：不看不画
--------------------

- **标签页被切到本页**（``showEvent``）：立即「催一下」，不等睡眠间隔，马上试取一次数据。
- **标签页被切走**（``hideEvent``）：绘图循环**阻塞式暂停**（``QWaitCondition``，零轮询）。
- **切回本页 / 菜单「操作 → 刷新」**：``refresh()`` 只做一次唤醒，立即返回。
- **点「暂停」按钮**：与隐藏同样效果，但界面上仍保留最后一帧。

⚠️ 暂停时**连 ``shared.get()`` 都不做** —— 隐藏的标签页不该让内核「以为有人在看」，
更不该白占 CPU。

⚠️ ``refresh()`` 之所以只做「催一下」而不直接取数据、直接绘图：它每次切标签都会被调，
项目规范要求它必须快（见 ``zmlx/ui/widgets/AGENTS.md``）。真正干活的永远只有那条
绘图线程。

睡眠间隔
--------

控制条上可设（0.1 ~ 600 s，默认 **1 s**），存在 ``app_data`` 的 ``env`` 里，下次打开
还是这个值。**每一轮结束都睡**（无论这一轮画没画）—— 这是「不占满 CPU」的兜底；
用 ``QWaitCondition.wait(timeout)`` 实现，所以「改间隔 / 暂停 / 换数据源 / 催刷新」
都能立刻打断睡眠，而不是傻等到点。

统计信息（第二行，只读）
------------------------

::

    运行中        绘图 12 次 · 尝试 15 次 · 耗时 1.83 s · 上次 0.09 s · 平均 0.15 s · 空闲 3.2 s

各项口径（数字全部在**绘图线程**里累加，GUI 侧只负责显示 —— 不做两份记账）:

=========================  ===========================================================
项                          口径
=========================  ===========================================================
绘图 N 次                   成功渲染出图像的次数（失败不计；尺寸变化引起的「重排」也不计）
尝试 N 次                   取到数据、进入渲染的次数（**含失败**）
失败 N 次                   回调抛异常 / 渲染出错的次数（只有非零时才显示）
耗时 X s                    所有成功渲染的累计耗时
上次 / 平均                 最近一次渲染耗时 / 平均每次渲染耗时（= 总耗时 ÷ 绘图次数）
空闲 W s                    距上一次成功渲染过去了多久；它就是「没有新数据」的那段时间
已存 N 张                   自动保存成功的张数（只有开启自动保存时才显示）
=========================  ===========================================================

⚠️ 「空闲」是**绘图线程每轮报一次**的（间隔就是刷新间隔），所以它最多滞后一个间隔；
暂停 / 隐藏时这个数字会**停住**（那段时间不再有循环，也就没有人在数）。

⚠️⚠️ **这两行不会把控件顶宽**。两个文字标签都是 :class:`_ElideLabel`：宽度不够就打
省略号，完整文字进 tooltip，``minimumSizeHint()`` 只报一个固定的小宽度。这一条是踩出来
的 —— 普通 ``QLabel`` 在 ``wordWrap=False`` 时 ``minimumSizeHint()`` **等于整段文字的
宽度**，于是「一条 100 字的异常信息」会把这一行的最小宽度从 **527 px 顶到 1290 px**
（实测），统计文字直接被挤出可视区。

⚠️ 因此控件的最小宽度只由**控制行**决定（约 **530 px**：间隔框 96 + 三个按钮各 80 +
复选框 72 + 标号与边距），与文字内容无关。窗口比这更窄时控制行会被裁掉 —— 绘图区本来
也不该窄到那个程度。

自动保存
--------

勾上控制条上的「**自动保存**」后，**每画出一帧就存一张 PNG**：

- 写盘在**绘图线程**里做（一张图几十毫秒，绝不能占 GUI 线程）；
- 目录点「**保存目录…**」改，默认 ``<用户缓存目录>/plt_live_view``；不存在会自动建；
- 两项都经 ``app_data`` 的 ``env`` 持久化，下次打开还是那样；
- 存的文件名是时间戳（``2026-10-18-12-30-05-123456.png``），按名字排序即时间顺序。

⚠️ 间隔设得很小（例如 0.1 s）时，一小时能堆出几万张图 —— 这是「**每帧都存**」的必然
结果，不是缺陷。要长期跑就把间隔调大，或者干脆关掉它。

⚠️ 自动保存**不影响**「文件 → 保存」（那是手动存当前这一帧），两者都存到上面那个目录。

关闭标签页时会发生什么
----------------------

「随时可能被关」是标签页控件的常态，所以收尾分三层（缺任何一层都会出问题）：

1. **清理钩子** ``cleanup_before_tab_close()``：置不可见、通知线程收工、**立刻摘掉对
   线程的引用**，且**绝不 ``wait()``** —— 关标签不许卡（一次渲染可能是几秒）。
   线程之所以能安全回收，靠的是「不设 parent + 类属性强引用」那两条纪律，不是靠等。
2. **迟到的信号**：所有槽都是**绑定方法**（不是 lambda），控件销毁时 Qt 自动断连；
   每个槽开头另有一道 ``self._thread is None`` 的闸门，挡住「清理之后才到」的那一份。
3. **程序退出**：``QApplication.aboutToQuit`` 接到 :meth:`_RenderThread._stop_all`，
   把还活着的线程叫停并**有限等待**（3 s）。不做这一步的话，进程退出时「运行中的
   ``QThread`` 被析构」会让**整个进程** abort（``0xC0000409``，不是 Python 异常，
   ``try/except`` 兜不住）。

⚠️ 关标签时如果正在渲染：那一帧会画完（无法中途取消 matplotlib 的绘制），但它的信号
已经没人接了 —— 被安全丢弃，不会碰已销毁的控件。

共享数据「不是原子的」：会有什么问题
------------------------------------

``SharedValue`` 的 ``get()`` 与 ``set()`` 各自加锁，但**两者之间**不原子，于是
「读 → 判断 → 清空」这段不是一次事务。具体三类后果：

1. **丢一次更新（本控件已缓解，未根治）**
   我们读到 D1，正准备写 None，内核那边因为「数据过期太久」强制刷新写了 D2；
   我们随后写 None，把 D2 抹掉了 —— 这份刚算出来的数据谁也没画。
   本控件用「**校验后再清空**」缩小窗口：``if shared.get() is data: shared.set(None)``。
   于是「读完之后被替换」的情况**不会**误删（格子里是新对象就原样留着），只剩
   「校验之后、写入之前」那一瞬（微秒级，且只可能撞上强制刷新）。
   ⚠️ 真要根治，得在 ``SharedValue`` 上加一个**原子取走**的方法（在同一把锁里
   「读出 + 置 None」返回旧值，即 ``take()``）。那是 ``zmlx/ui/utils/shared.py``
   的事，本控件按「只改一个文件」的约定没有碰它。
2. **同一份数据被画两遍（与共享方式有关）**
   **一个 ``SharedValue`` 只喂给一个 PltLiveView**。若两个视图共用同一个容器，它们
   会各自读到同一份数据（谁先清空看运气），于是画两遍 —— 这是「共享格子」的语义，
   不是本控件的缺陷。
3. **数据在「交接之后」被就地改写（最隐蔽的一类）**
   ``get()`` 返回的是**引用**。内核若复用同一个 numpy 数组（每步原地写），我们正在
   渲染的那一刻它可能已经改到一半 —— 画出来的是「半新半旧」的图，且无从检测。
   **约定：hand-off 的必须是快照**（``arr.copy()`` 或每步新建对象），别复用缓冲区。

另外两条「反向」的竞争，写内核时值得留意：

- 内核「看一眼是空的 → 准备 → 写入」同样不是原子的。两次准备撞在一起时后写者胜，
  先算出来的那份白算（只浪费 CPU，不会画错）。
- 内核的「定期强制刷新」与消费者「取走」会互相覆盖：最坏结果是某一版数据没被看到，
  下一版会补上。都属于**可自愈**的竞争，不是致命问题。

用法示例
--------

内核线程（另一个文件里）::

    shared = SharedValue()

    # 每步算完：
    if shared.get() is None:            # 已经画过了才准备（准备本身很贵）
        shared.set(make_snapshot())     # ⚠️ 新对象 / 深拷贝，别复用缓冲区

界面（GUI 线程）::

    from zmlx.ui.tabs.plt_live_view import PltLiveView

    view = PltLiveView()

    def on_figure(fig, data):
        ax = fig.subplots()
        ax.plot(data['t'], data['p'])
        fig.suptitle('第 {0} 步'.format(data['step']))

    view.set_data(shared, on_figure)

已知取舍
--------

- **位图，不是矢量画布**（见上）；没有 matplotlib 的交互工具栏。
- **matplotlib 不是线程安全的**。本控件只让**唯一**的绘图线程碰它自己的那个 figure，
  并在构造时于主线程把字体与 rcParams 一次性预热好（``set_chinese_font()`` 约 300 ms），
  把「字体缓存初始化」这种一次性全局状态的竞争窗口消掉。剩下的理论风险是「GUI 线程
  同时在给别的 matplotlib 图排版文字」时 FreeType 层面的竞争 —— 实践中极少触发；
  若你的场景里同时开着大量 matplotlib 图并高频重绘，可把 ``_RenderThread._render``
  改回 GUI 线程执行（代价是那些重图会卡界面）。
- **窗口尺寸变化时会「重排」一次**：如果这一轮没有新数据、而显示尺寸变了，本控件会用
  **上一份 data** 按新尺寸再渲染一遍（否则旧位图会被拉伸/留黑边）。所以回调应当
  **幂等**（画什么只由 data 决定）。``clear=False``（叠加模式）时**不会**重排 ——
  那会把同一份数据叠加两遍。
- 隐藏期间不消费数据，所以「恢复可见」的第一帧可能是几十秒前的（取决于内核的强制
  刷新周期）。
- 位图在内存里只留最后一张（十几 MB 以内，取决于窗口尺寸与屏幕缩放），不做帧历史。

Created by DeepSeek, 2026-10-18
"""

import datetime
import os
import sys
import time

if __name__ == '__main__':  # 直接运行本文件时，把仓库根目录加入搜索路径
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))))

from zmlx.system import app_data, warn
from zmlx.ui.pyqt import QAction, QtCore, QtGui, QtWidgets


class _RenderThread(QtCore.QThread):
    """后台绘图线程：从共享容器里取一份数据、渲染成位图、把位图发回 GUI 线程.

    ⚠️ **线程不设 parent**（写 ``_RenderThread(...)``，绝不写 ``_RenderThread(self)``）：
    关标签走 ``deleteLater()``，parent 指向控件的线程会被连带析构，而「运行中的 QThread
    被析构」是进程级崩溃（``QThread: Destroyed while thread is still running``，
    不是异常，``try/except`` 兜不住）。强引用放在类属性 ``_RUNNING`` 里。

    Attributes:
        sig_frame: ``(QImage, float)`` —— 一帧好了：图像 + 本次渲染耗时（秒）.
        sig_stats: ``dict`` —— 这一轮的统计快照（见 :meth:`_stats`），**每轮结束发一次**.
        sig_error: ``str`` —— 回调 / 渲染失败的原因（供状态栏显示）.
        _RUNNING: 类级强引用登记表（线程不设 parent，必须有别的东西持着它）.
    """

    sig_frame = QtCore.pyqtSignal(QtGui.QImage, float)
    sig_stats = QtCore.pyqtSignal(object)
    sig_error = QtCore.pyqtSignal(str)

    _RUNNING = set()

    #: 是否已经接过 ``QApplication.aboutToQuit``（进程内只接一次）
    _QUIT_HOOKED = False

    #: 逻辑 DPI：figure 的英寸尺寸按「逻辑像素 / 该值」换算，乘 dpr 后得到设备像素
    LOGICAL_DPI = 100.0

    #: 连续失败时最多报几次警告（之后只更新状态栏，避免每轮刷屏）
    MAX_LOGGED_FAILS = 3

    #: 两次「重排」之间至少隔多少秒（防止拖窗口时反复重绘）
    REFLOW_DELAY = 0.4

    #: 尺寸至少变了多少像素才算「真的变了」（阈值太小会被亚像素抖动反复触发）
    REFLOW_TOLERANCE = 4

    #: 程序退出时最多等绘图线程多久（毫秒）。等是为了避免「运行中的 QThread 被析构」
    #: 这个进程级 abort；但也不许无限等 —— 退出卡住比崩掉更让人困惑。
    QUIT_WAIT_MS = 3000

    def __init__(self, *, bg, clear=True):
        """初始化（**不启动**，由 :meth:`start_quietly` 启动）.

        Args:
            bg: figure 的底色（与界面主题一致，避免闪一下白底）.
            clear: 每帧回调之前是否 ``figure.clear()``.
        """
        super(_RenderThread, self).__init__()  # ⚠️ 不传 parent，见类文档
        self.setObjectName(type(self).__name__)

        self._mutex = QtCore.QMutex()
        self._cond = QtCore.QWaitCondition()

        # ── 受 _mutex 保护的状态（GUI 线程写、绘图线程读）──
        self._stopped = False
        self._active = False            # 可见 且 用户没有暂停
        self._interval = 1.0
        self._shared = None
        self._on_figure = None
        self._size = (800, 600, 1.0)    # (宽, 高, dpr)，宽高为逻辑像素
        self._autosave = False          # 是否每帧自动存图
        self._save_folder = ''          # 自动存图到哪儿

        # ── 只属于绘图线程的状态 ──
        self._clear = bool(clear)
        self._bg = bg
        self._fails = 0                 # 连续失败次数（只用于压制重复警告）
        self._last_error = ''
        self._last_data = None          # 上一份画过的数据（尺寸变化时用来重排）
        self._rendered_size = None      # 上一帧是按哪个尺寸渲染的
        self._last_reflow = 0.0
        self._last_draw = 0.0           # 上一次成功出图的时刻（算「空闲」用）
        self._save_folder_ready = ''    # 已经确保存在的目录（省掉每帧 makedirs）
        self._stats = self._new_stats() # 统计快照（口径见类文档）

    # ============================================================== 控制（GUI 线程调）
    def start_quietly(self):
        """登记强引用后以**低优先级**启动（绘图再重也不跟界面抢 CPU）.

        ⚠️ 槽按连接顺序触发：先摘登记表、再 ``deleteLater``（销毁之后就不能再碰它）.
        """
        _RenderThread._hook_app_quit()
        _RenderThread._RUNNING.add(self)
        self.finished.connect(lambda t=self: _RenderThread._RUNNING.discard(t))
        self.finished.connect(self.deleteLater)
        self.start(QtCore.QThread.Priority.LowPriority)

    @classmethod
    def _hook_app_quit(cls):
        """把「程序退出」接到 :meth:`_stop_all`（进程内只接一次）.

        ⚠️ 为什么非要接这一下：本线程**长命**（不关标签就一直跑），而它又**不设 parent**
        （否则关标签时会被连带析构）。于是「用户直接关掉主窗口」这条路径上，没有任何
        东西会通知它停下 —— 解释器退出时 Python 包装对象被回收，C++ 侧
        ``~QThread()`` 发现线程还在跑，直接 ``qFatal`` → 进程 abort。接上 ``aboutToQuit``
        就能在事件循环真正退出之前把它叫停。
        """
        if cls._QUIT_HOOKED:
            return
        app = QtWidgets.QApplication.instance()
        if app is None:  # 没有 QApplication（只 import 不建界面）：无需接
            return
        cls._QUIT_HOOKED = True
        app.aboutToQuit.connect(cls._stop_all)

    @classmethod
    def _stop_all(cls):
        """叫停所有还活着的绘图线程，并**有限等待**（只在程序退出时调用）.

        ⚠️ 这里的 ``wait`` 是「退出路径」唯一的例外：等是为了避免进程级 abort，
        3 s 是上限（一次慢渲染可能更久，那种情况只能认了 —— 进程本来就在退出）。
        标签页关闭路径**绝不**走这里（那边不允许阻塞）。
        """
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

    def set_source(self, shared, on_figure):
        """换数据源与回调（可在运行中随时换；旧的统计随即清零）."""
        with QtCore.QMutexLocker(self._mutex):
            self._shared = shared
            self._on_figure = on_figure
            self._last_data = None      # 换了源，旧快照就作废了
            self._stats = self._new_stats()
            self._fails = 0
            self._last_error = ''
            self._notify()

    def set_autosave(self, enabled, folder):
        """设置「每帧自动存图」及其目录（随时可改，下一帧生效）."""
        with QtCore.QMutexLocker(self._mutex):
            self._autosave = bool(enabled)
            self._save_folder = str(folder) if folder is not None else ''

    def set_active(self, active):
        """是否允许绘图（可见且用户没暂停才为 True）."""
        with QtCore.QMutexLocker(self._mutex):
            self._active = bool(active)
            self._notify()

    def set_interval(self, seconds):
        """设置每轮结束后的睡眠时长（秒）；正在睡的那一轮会被立刻打断并按新值重睡."""
        with QtCore.QMutexLocker(self._mutex):
            self._interval = max(0.0, float(seconds))
            self._notify()

    def set_size(self, width, height, dpr):
        """设置渲染目标尺寸（逻辑像素 + 设备像素比）.

        ⚠️ **刻意不唤醒**：拖窗口会连发几十个 ``resizeEvent``，逐个唤醒就等于逐个重绘。
        新尺寸在下一轮自然生效；要「马上按新尺寸重排」由 ``poke()`` 负责。
        """
        with QtCore.QMutexLocker(self._mutex):
            self._size = (max(1, int(width)), max(1, int(height)), max(1.0, float(dpr)))

    def poke(self):
        """催一下：唤醒当前等待，立刻进入下一轮（只缩短等待，**不**绕过暂停）.

        ⚠️ 它做的事**仅仅**是 ``wakeAll``：睡眠被提前打断后，循环回到顶部重新判断
        「能不能画 / 有没有数据」。所以「催刷新」不会画出没被更新的数据，也不会
        让被隐藏的标签页偷偷跑起来.
        """
        with QtCore.QMutexLocker(self._mutex):
            self._notify()

    def stop(self):
        """请求收工：置停止位并唤醒. **不阻塞**（规范禁止在清理钩子里 ``wait()``）."""
        self.requestInterruption()
        with QtCore.QMutexLocker(self._mutex):
            self._stopped = True
            self._notify()

    def _notify(self):
        """唤醒等待中的循环.

        ⚠️ 必须**持有 mutex**时调用：否则「判断条件」与「进入等待」之间会丢掉这次唤醒
        （经典丢唤醒）。所有调用处都写在 ``with QMutexLocker(...)`` 里面。
        """
        self._cond.wakeAll()

    # ============================================================== 线程体
    def run(self):
        """线程体：循环「等 → 取数据 → 画 → 睡」，**每轮结束发一次统计**.

        ⚠️ 全程只碰本线程自己的 figure / canvas（matplotlib 不是线程安全的，见模块文档）。
        """
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        figure = Figure()
        canvas = FigureCanvasAgg(figure)
        figure.patch.set_facecolor(self._bg)
        self._last_draw = time.monotonic()

        while True:
            try:
                with QtCore.QMutexLocker(self._mutex):
                    # ① 隐藏 / 暂停 / 已停止：**纯阻塞**等待，既不轮询也不取数据
                    while not self._stopped and not self._active:
                        self._cond.wait(self._mutex)
                    if self._stopped:
                        return
                    shared = self._shared
                    on_figure = self._on_figure
                    size = self._size
                    interval = self._interval
                    autosave = self._autosave
                    folder = self._save_folder

                now = time.monotonic()
                self._stats['cycles'] += 1

                if shared is None or on_figure is None:  # 还没 set_data
                    self._emit_stats(now)
                    self._sleep(interval)
                    continue

                data = self._take(shared)
                if data is None:
                    # ② 没有新数据：这一轮不画。但若显示尺寸变了，用上一份数据重排一次
                    #    （否则旧位图会被拉伸或留黑边；这不是「重复消费」，格子是空的）
                    image, cost = self._reflow(figure, canvas, size)
                    if image is not None:
                        self._stats['reflows'] += 1
                        self._last_draw = time.monotonic()
                        self.sig_frame.emit(image, cost)
                    self._emit_stats(now)
                    self._sleep(interval)
                    continue

                # ③ 真的拿到数据了：算「尝试」一次（失败也算尝试）
                self._stats['attempts'] += 1
                cost, image = self._render(figure, canvas, on_figure, data, size)
                if image is None:
                    self._stats['fails'] += 1
                    self.sig_error.emit(self._last_error)
                else:
                    self._stats['frames'] += 1
                    self._stats['total_cost'] += cost
                    self._stats['last_cost'] = cost
                    self._last_data = data
                    self._last_draw = time.monotonic()
                    if autosave and folder:  # 先存盘再发图：存盘耗时也只算在这条线程里
                        self._save(image, folder)
                    self.sig_frame.emit(image, cost)
                self._emit_stats(now)

                # ④ 无论画没画，这一轮结束都要睡（需求：不许占满 CPU）
                self._sleep(interval)
            except Exception as err:
                # ⚠️ 线程体里任何**没预料到**的异常都不许让线程死掉：死了就再也没人画图，
                #    而且现场只剩下一条「线程悄悄退出」的痕迹。报出来，歇一下，接着跑。
                self._on_fail(err)
                self._sleep(0.5)

    @staticmethod
    def _new_stats():
        """一份全新的统计快照（口径见类文档；数字只在本线程累加）."""
        return dict(
            cycles=0,           # 循环轮数（含空转）
            attempts=0,         # 取到数据、进入渲染的次数（含失败）
            frames=0,           # 成功出图的次数
            fails=0,            # 渲染 / 回调失败的次数
            reflows=0,          # 尺寸变化引起的「重排」次数（不算进绘图 / 尝试）
            saved=0,            # 自动保存成功的张数
            save_fails=0,       # 自动保存失败的次数
            total_cost=0.0,     # 累计渲染耗时
            last_cost=0.0,      # 上一次渲染耗时
            save_cost=0.0,      # 上一次存盘耗时
            idle=0.0,           # 距上一次成功出图多久
            last_saved='',      # 最近一次自动保存的文件路径
        )

    def _emit_stats(self, now):
        """把统计快照发给 GUI 线程（每轮一次）.

        ⚠️ 发的是**副本**：GUI 侧只读，不该和本线程共享同一个 dict（否则它读到的
        可能是一个改到一半的中间状态）。
        """
        self._stats['idle'] = max(0.0, now - self._last_draw)
        self.sig_stats.emit(dict(self._stats))

    def _save(self, image, folder):
        """把这一帧存成 PNG（在**绘图线程**里写盘：一张图几十毫秒，绝不能占 GUI 线程）.

        ⚠️ 失败只计数 + 报一次警告，**不打断循环** —— 磁盘满 / 目录没权限都不该让
        绘图停摆（用户还能在状态栏看到失败原因）.
        """
        start = time.monotonic()
        try:
            if self._save_folder_ready != folder:  # 目录只需确保一次
                os.makedirs(folder, exist_ok=True)
                self._save_folder_ready = folder
            now = datetime.datetime.now()
            name = now.strftime('%Y-%m-%d-%H-%M-%S-') + '{0:06d}'.format(now.microsecond)
            path = os.path.join(folder, '{0}.png'.format(name))
            if not image.save(path, 'PNG'):
                raise RuntimeError('QImage.save() 返回 False（路径不可写？）')
            self._stats['saved'] += 1
            self._stats['last_saved'] = path
        except Exception as err:
            self._stats['save_fails'] += 1
            self._save_folder_ready = ''  # 下次重试「确保目录存在」（目录可能是刚被删了）
            if self._stats['save_fails'] <= self.MAX_LOGGED_FAILS:
                warn('PltLiveView: 自动保存失败 —— {0}'.format(err))
        self._stats['save_cost'] = time.monotonic() - start

    def _take(self, shared):
        """从共享容器里取一份数据；取到就**尽力而为地清空**它.

        Returns:
            object: 这一轮要画的数据；**None 表示没有新数据**.

        ⚠️ ``get()`` 与 ``set(None)`` 是两次独立的加锁操作，中间有窗口，所以这里不是
        「原子取走」，而是「读 → 校验仍是它自己 → 清空」的补丁：格子里若已经换成了
        新对象（内核强制刷新写的），就**原样留着**，不会被我们误删（详见模块文档）。
        """
        try:
            data = shared.get()
        except Exception:
            return None
        if data is None:
            return None
        try:
            if shared.get() is data:  # 只有格子里还是它，才动手清空
                shared.set(None)
        except Exception:
            pass
        return data

    def _render(self, figure, canvas, on_figure, data, size, clear=None):
        """把 ``data`` 画到 ``figure`` 上，并渲染成 QImage.

        Args:
            figure: 本线程私有的 Figure（Agg 后端）.
            canvas: 与它配套的 FigureCanvasAgg.
            on_figure: 用户的绘图回调 ``(fig, data)``.
            data: 这一帧的数据.
            size: ``(宽, 高, dpr)``，宽高是**逻辑像素**.
            clear: 是否先 ``figure.clear()``；None 表示用构造时的设置.

        Returns:
            (float, QtGui.QImage | None): 耗时（秒）与图像；失败时图像为 None
            （原因已通过 ``sig_error`` 发出）.
        """
        width, height, dpr = size
        if clear is None:
            clear = self._clear
        start = time.monotonic()
        try:
            # 英寸尺寸按逻辑像素算、dpi 乘上 dpr ⇒ 位图尺寸 = 逻辑尺寸 × dpr（1:1 贴图）
            figure.set_dpi(self.LOGICAL_DPI * dpr)
            figure.set_size_inches(width / self.LOGICAL_DPI,
                                   height / self.LOGICAL_DPI)
            if clear:
                figure.clear()
            figure.patch.set_facecolor(self._bg)  # clear 之后底色要重设
            on_figure(figure, data)
            canvas.draw()
            image = self._to_image(canvas, figure, dpr)
        except Exception as err:
            self._on_fail(err)
            return time.monotonic() - start, None
        self._fails = 0
        self._last_error = ''
        self._rendered_size = (width, height, dpr)
        return time.monotonic() - start, image

    def _reflow(self, figure, canvas, size):
        """尺寸变了、又恰好没有新数据：用**上一份数据**按新尺寸重排一次.

        Returns:
            (QtGui.QImage | None, float): 新图像与耗时；不需要 / 不能重排时为
            ``(None, 0.0)``（调用方据此保持「无数据」的状态显示）.

        ⚠️ ``clear=False``（叠加模式）时**不做**重排 —— 那会把同一份数据叠加两遍。
        """
        data = self._last_data
        on_figure = self._on_figure
        if data is None or on_figure is None or not self._clear:
            return None, 0.0
        old = self._rendered_size
        if old is None:
            return None, 0.0
        tolerance = self.REFLOW_TOLERANCE
        if (abs(old[0] - size[0]) < tolerance
                and abs(old[1] - size[1]) < tolerance
                and abs(old[2] - size[2]) < 1e-3):
            return None, 0.0
        now = time.monotonic()
        if now - self._last_reflow < self.REFLOW_DELAY:
            return None, 0.0
        self._last_reflow = now
        cost, image = self._render(figure, canvas, on_figure, data, size)
        return image, cost

    def _on_fail(self, err):
        """记录一次失败：前几次发警告（含日志），每次都发到状态栏."""
        self._fails += 1
        text = '{0}: {1}'.format(type(err).__name__, err)
        self._last_error = text
        if self._fails <= self.MAX_LOGGED_FAILS:
            warn('PltLiveView: 绘图回调失败（连续第 {0} 次）—— {1}'.format(
                self._fails, text))
        self.sig_error.emit(text)

    @classmethod
    def _to_image(cls, canvas, figure, dpr):
        """把 Agg 画布的内容转成 QImage（**深拷贝**，不依赖画布缓冲区的寿命）.

        ⚠️ 必须在 ``canvas.draw()`` 之后调用. 不同 matplotlib 版本的
        ``buffer_rgba()`` 形状不同（≥3.6 为 ``(h, w, 4)``，更早是一维字节串），两种都处理.
        """
        import numpy
        buffer = canvas.buffer_rgba()
        array = numpy.asarray(buffer)
        if array.ndim == 3:
            height, width = int(array.shape[0]), int(array.shape[1])
            array = array.reshape(height, width, 4)
        else:  # 老版本：一维字节串，宽度从 bbox 推
            width = int(round(figure.bbox.width))
            array = array.reshape(-1, width, 4)
            height = int(array.shape[0])
        array = numpy.ascontiguousarray(array)
        image = QtGui.QImage(array.tobytes(), width, height, width * 4,
                             QtGui.QImage.Format.Format_RGBA8888)
        image = image.copy()  # ⚠️ 必须 copy：QImage 不持有 Python 缓冲区的所有权
        image.setDevicePixelRatio(max(1.0, float(dpr)))
        return image

    def _sleep(self, seconds):
        """睡 ``seconds`` 秒；期间收到控制信号（暂停 / 停止 / 换数据 / 改间隔 / 催刷新）
        则**立刻**返回，不等满.

        ⚠️ 用 ``QWaitCondition.wait(timeout)`` 而不是 ``time.sleep``：前者能被唤醒，
        后者会让「暂停」和「催刷新」慢上整整一个间隔（间隔设成 60 s 时尤其明显）.
        """
        with QtCore.QMutexLocker(self._mutex):
            if self._stopped:
                return
            milliseconds = int(round(max(0.0, float(seconds)) * 1000.0))
            if milliseconds > 0:
                self._cond.wait(self._mutex, milliseconds)


class _ElideLabel(QtWidgets.QLabel):
    """单行文字标签：宽度不够就打省略号，且**绝不会把控件的最小宽度顶大**.

    为什么必须有它（实测过）：``QLabel`` 在 ``wordWrap=False`` 时的
    ``minimumSizeHint()`` **等于整段文字的宽度**。于是「一条 100 字的错误信息」会让
    这一行的最小宽度从 542 px 涨到 **1290 px**（``state_label.minimumSizeHint()`` 实测
    1260）—— 结果是统计文字被挤出可视区，窗口一旦被拖窄，整行就错位。

    这里做三件事：

    1. ``minimumSizeHint()`` 只报一个固定的小宽度（``minimum_width``），布局因此
       可以把它压扁；
    2. ``sizeHint()`` 可设上限（``maximum_hint``），避免「文字很长时要跟旁边的统计
       抢光空间」；
    3. 真正显示的是**按当前宽度省略后**的那一段，完整文字放进 tooltip —— 信息不丢，
       也不会看到半个汉字被切掉的毛边。

    ⚠️ ``setText()`` 收到的永远是**完整**文字（省略只发生在显示层），所以外部
    （:meth:`PltLiveView._sync_labels`）的「文字变了才 setText」那套缓存照常成立。
    """

    def __init__(self, parent=None, *, minimum_width=0, maximum_hint=0):
        """初始化.

        Args:
            parent: Qt 父对象.
            minimum_width: 允许被压到的最小宽度（像素）；0 表示可以压到 0.
            maximum_hint: ``sizeHint()`` 的上限（像素）；0 表示不设上限.
        """
        super(_ElideLabel, self).__init__(parent)
        self._full_text = ''
        self._minimum_width = max(0, int(minimum_width))
        self._maximum_hint = max(0, int(maximum_hint))
        self.setWordWrap(False)
        self.setTextFormat(QtCore.Qt.TextFormat.PlainText)

    def setText(self, text):
        """设置**完整**文字（实际显示的是省略后的那一段）."""
        self._full_text = '' if text is None else str(text)
        self._apply_elide()

    def full_text(self):
        """当前的完整文字（未省略）."""
        return self._full_text

    def minimumSizeHint(self):
        """最小宽度只报固定值 —— 这就是「不顶宽」的关键.

        Returns:
            QtCore.QSize: 宽 = ``minimum_width``，高沿用父类的（一行字的高度）.
        """
        hint = super(_ElideLabel, self).minimumSizeHint()
        return QtCore.QSize(self._minimum_width, hint.height())

    def sizeHint(self):
        """偏好宽度：按**完整文字**算（再受 ``maximum_hint`` 截断）.

        ⚠️ 必须用完整文字重算，不能直接用父类的：父类的 ``sizeHint()`` 基于「当前显示的
        那段（可能已被省略）」，于是窄过一次之后 hint 就变小 —— 窗口再拉宽时布局按
        hint 分配空间，标签**再也长不回来**（实测：长错误信息下宽 1000 px 时仍停在
        110 px）。这里用字宽差把「省略掉的那部分」加回去.
        """
        base = super(_ElideLabel, self).sizeHint()
        metrics = self.fontMetrics()
        delta = (metrics.horizontalAdvance(self._full_text)
                 - metrics.horizontalAdvance(super(_ElideLabel, self).text()))
        hint = QtCore.QSize(base.width() + delta, base.height())
        if self._maximum_hint > 0:
            hint.setWidth(min(hint.width(), self._maximum_hint))
        return hint

    def resizeEvent(self, event):
        """宽度变了：重新省略一次."""
        super(_ElideLabel, self).resizeEvent(event)
        self._apply_elide()

    def changeEvent(self, event):
        """字体变了（换主题 / 改字号）：也要重算，否则断字位置会错."""
        super(_ElideLabel, self).changeEvent(event)
        if event.type() == QtCore.QEvent.Type.FontChange:
            self._apply_elide()

    def _apply_elide(self):
        """按当前宽度重算显示文字（只在真的变了才 ``setText``，避免自我循环）."""
        width = self.width()
        if width <= 0:  # 还没被布局摆好：先显示全文，别急着打省略号
            text = self._full_text
        else:
            text = self.fontMetrics().elidedText(
                self._full_text, QtCore.Qt.TextElideMode.ElideRight, width)
        if text != super(_ElideLabel, self).text():
            super(_ElideLabel, self).setText(text)
        tooltip = self._full_text if text != self._full_text else ''
        if tooltip != self.toolTip():
            self.setToolTip(tooltip)


class _Canvas(QtWidgets.QWidget):
    """绘图区：把一张 ``QPixmap`` 等比缩放、居中画出来.

    刻意只是一个「画板」：不含缩放漫游、不含业务逻辑。用 ``paintEvent`` 而不是
    ``QLabel.setPixmap``，是为了「缩放只在绘制时做」—— 窗口尺寸变了不用重建
    ``QPixmap``（``QLabel`` 在 ``scaledContents`` 下会自己缩放，但会把控件的最小
    尺寸锁在图片尺寸上，长图会把整个标签页顶开）。
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
        """算出「等比缩放并居中」后图片该占的那个矩形.

        ⚠️ 用 **device-independent** 尺寸（``width() / devicePixelRatio()``）来算：
        位图是按「逻辑尺寸 × dpr」渲染的，若直接拿设备像素去比，高 DPI 屏上会算成
        「放大到 2 倍」而糊掉.
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


class PltLiveView(QtWidgets.QWidget):
    """基于 matplotlib 的实时绘图视图（详见模块文档）.

    ⚠️ 数据接口**只有一个**：:meth:`set_data`。其余公开方法都是框架钩子.
    """

    #: 默认睡眠间隔（秒）
    DEFAULT_INTERVAL = 1.0

    #: 允许的最小 / 最大睡眠间隔（秒）
    MIN_INTERVAL = 0.1
    MAX_INTERVAL = 600.0

    #: 睡眠间隔的持久化键（``app_data.getenv`` / ``setenv``）
    SETTING_KEY = 'plt_live_view_interval'

    #: 「每帧自动存图」开关的持久化键（``'Yes'`` / ``'No'``）
    AUTOSAVE_KEY = 'plt_live_view_autosave'

    #: 自动存图目录的持久化键（绝对路径）
    FOLDER_KEY = 'plt_live_view_save_folder'

    #: matplotlib 的一次性初始化（字体 / 主题）是否已经做过
    _MPL_READY = False

    def __init__(self, parent=None, *, clear=True):
        """初始化.

        Args:
            parent: Qt 父对象.
            clear: 每次回调之前是否 ``figure.clear()``。默认 True —— 每帧重画，这是
                live view 的常态。若你的回调是「在已有图上继续叠加」（例如每帧追加
                一条曲线），传 False；⚠️ 那时窗口尺寸变化**不会**触发重排（否则会把
                同一份数据叠加两遍）。
        """
        super(PltLiveView, self).__init__(parent)
        self.context_actions = []  # 右键菜单扩展点（与 MatplotWidget 同一套约定）

        self._thread = None        # 绘图线程（不设 parent，见 _RenderThread）
        self._shared = None        # 共享数据容器
        self._on_figure = None     # 绘图回调
        self._visible = False      # Qt 层面的显隐（showEvent / hideEvent 维护）
        self._user_paused = False  # 用户点了「暂停」
        self._clear = bool(clear)

        self._autosave = False     # 是否每帧自动存图
        self._save_folder = ''     # 存图目录
        self._stats = {}           # 绘图线程报上来的统计（口径见模块文档）
        self._error = ''           # 最近一次失败原因
        self._last_image = None    # 最近一帧（保存 / 复制用）
        self._state_cache = ''     # 状态文字的缓存（只在变了才 setText）
        self._stats_cache = ''     # 统计文字的缓存
        self._bg = '#ffffff'

        self._prepare_matplotlib()  # 字体 / 主题：进程内只在主线程做一次
        self._autosave = self._load_autosave()
        self._save_folder = self._load_folder()
        self._build_ui()
        self._sync_labels()

    # ============================================================== matplotlib 预热
    def _prepare_matplotlib(self):
        """初始化 matplotlib 的字体与主题（**进程内只做一次**，且只在主线程做）.

        ⚠️ 必须在这里做、不能留给绘图线程：``set_chinese_font()`` 要遍历系统字体、
        触发字体管理器初始化（实测约 300 ms），那是典型的「一次性全局状态」—— 两个
        线程同时初始化它才是真正的风险。在主线程一次到位，绘图线程就只管画。

        ⚠️ 这里**不**调 ``matplotlib.use(...)``：本控件用 ``FigureCanvasAgg`` 直接渲染，
        不经过 pyplot，没有「当前后端」的概念。故意不去动它，免得与 ``MatplotWidget``
        在无头模式下的后端选择打架。
        """
        if PltLiveView._MPL_READY:
            return
        PltLiveView._MPL_READY = True  # 先置位：初始化失败也不再重试（否则每次都慢一次）
        try:
            import matplotlib
            from matplotlib import style
            if self._is_dark():
                # 与 MatplotWidget 的暗色处理一致：整套暗色 rcParams
                matplotlib.rcParams.update(style.library['dark_background'])
        except Exception as err:
            print('PltLiveView: 设置 matplotlib 主题失败 —— {0}'.format(err))
        try:
            from zmlx.plt import set_chinese_font
            set_chinese_font()
        except Exception as err:
            print('PltLiveView: 设置中文字体失败 —— {0}'.format(err))

    def _is_dark(self):
        """当前是否是暗色主题（判据与 ``MatplotWidget`` 一致：窗口底色的亮度）."""
        color = self.palette().color(QtGui.QPalette.ColorRole.Window)
        return color.lightness() < 128

    # ============================================================== 界面
    def _build_ui(self):
        """搭界面：上面绘图区（占满），下面两行 —— 控制行 + 统计行."""
        self._bg = '#1e1e1e' if self._is_dark() else '#ffffff'

        self.canvas = _Canvas(self)
        self.canvas.set_background(self._bg)
        self.canvas.set_message('等待数据…\n\n（还没调用 set_data，或内核还没算出第一批数据）')

        self.interval_box = QtWidgets.QDoubleSpinBox(self)
        self.interval_box.setRange(self.MIN_INTERVAL, self.MAX_INTERVAL)
        self.interval_box.setDecimals(1)
        self.interval_box.setSingleStep(0.5)
        self.interval_box.setSuffix(' s')
        self.interval_box.setKeyboardTracking(False)  # 别每敲一个字符就写一次设置
        self.interval_box.setMaximumWidth(110)
        self.interval_box.setToolTip(
            '每一轮（取数据 → 绘图 → 睡）结束之后睡多久.\n'
            '画得快就调小（更跟手）；想让内核少等、界面少占 CPU 就调大.')
        self.interval_box.setValue(self._load_interval())

        self.pause_button = QtWidgets.QPushButton('暂停', self)
        self.pause_button.setCheckable(True)
        self.pause_button.setToolTip(
            '暂停 / 继续刷新.\n（标签页被切走时本来就会自动暂停，不用手动点）')

        self.refresh_button = QtWidgets.QPushButton('立即刷新', self)
        self.refresh_button.setToolTip('立刻试取一次数据，不等睡眠间隔')

        self.autosave_box = QtWidgets.QCheckBox('自动保存', self)
        self.autosave_box.setChecked(self._autosave)
        self.autosave_box.setToolTip(
            '每画出一帧就存一张 PNG 到右边的目录.\n'
            '写盘在绘图线程里做，不会让界面卡顿；间隔调到 0.1 s 时图片会堆得很快.')

        self.folder_button = QtWidgets.QPushButton('保存目录…', self)
        self.folder_button.setToolTip('自动保存到：{0}'.format(self._save_folder))

        # ── 统计行（只读）──
        # ⚠️ 两个标签都必须用 _ElideLabel：普通 QLabel 在长文本（例如 100 字的异常信息）
        #    会把整行最小宽度顶到一千多像素（实测 1290），统计文字就被挤出可视区。
        #    state 给 110 px 下限（「已暂停」「运行中」总看得见）、偏好宽度封顶 360 px
        #    （别让它把统计挤光）；stats 保 100 px 下限（数字总还能看到几个），
        #    宽度不够时自己省略，全文进 tooltip。
        self.state_label = _ElideLabel(self, minimum_width=110, maximum_hint=360)
        self.stats_label = _ElideLabel(self, minimum_width=100)
        self.stats_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        # stats 用 Ignored：宽度富余时把剩下的都给它（文字右对齐），不够时任其压缩。
        # ⚠️ 策略是 Ignored 时 Qt **不看** minimumSizeHint（qSmartMinSize 直接跳过），
        #    所以「至少留 100 px」还得显式 setMinimumWidth 一次，否则它会被压到 0。
        self.stats_label.setMinimumWidth(100)
        self.stats_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Preferred)
        # 统计是次要信息：取调色板里的「提示文字」色 —— 别写死灰色（暗色主题下看不见）
        palette = self.stats_label.palette()
        palette.setColor(
            QtGui.QPalette.ColorRole.WindowText,
            palette.color(QtGui.QPalette.ColorRole.PlaceholderText))
        self.stats_label.setPalette(palette)

        bar = QtWidgets.QHBoxLayout()
        bar.setContentsMargins(8, 4, 10, 2)
        bar.setSpacing(8)
        bar.addWidget(QtWidgets.QLabel('刷新间隔', self))
        bar.addWidget(self.interval_box)
        bar.addWidget(self.pause_button)
        bar.addWidget(self.refresh_button)
        bar.addSpacing(14)
        bar.addWidget(self.autosave_box)
        bar.addWidget(self.folder_button)
        bar.addStretch(1)

        info = QtWidgets.QHBoxLayout()
        info.setContentsMargins(8, 0, 10, 4)
        info.setSpacing(12)
        info.addWidget(self.state_label)
        info.addWidget(self.stats_label, 1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.canvas, 1)
        layout.addLayout(bar)
        layout.addLayout(info)

        # ⚠️ 先把控件状态设好再 connect：否则构造时那几处赋值会顺手写一遍设置文件
        self.interval_box.valueChanged.connect(self._on_interval_changed)
        self.pause_button.toggled.connect(self._on_pause_toggled)
        self.refresh_button.clicked.connect(self.refresh)
        self.autosave_box.toggled.connect(self._on_autosave_toggled)
        self.folder_button.clicked.connect(self._choose_folder)

    # ============================================================== 唯一的数据接口
    def set_data(self, shared_value, on_figure):
        """设置数据源与绘图回调（**本控件唯一的数据接口**）.

        Args:
            shared_value: 线程安全的共享容器（如 ``zmlx.ui.utils.shared.SharedValue``）.
                只要求有 ``get()`` 与 ``set(value)``：本控件每轮 ``get()`` 一次，取到值
                后立刻把它清成 ``None``（内核据此知道你画过了）。
            on_figure: ``on_figure(fig, data)`` —— 把 ``data`` 画到 ``fig`` 上.
                ⚠️ **在绘图线程里执行**：只能碰 ``fig`` 与 ``data``，不许碰 Qt 控件.
                ⚠️ 应当**幂等**（画什么只由 data 决定）：窗口尺寸变化时，本控件会用
                上一份 data 再调一次，让它按新尺寸重新排版.

        Raises:
            ValueError: ``shared_value`` 不是一个有 ``get`` / ``set`` 的容器，或回调不可调用.

        Note:
            可以在运行中随时再调一次（换数据源 / 换回调），旧的那份快照随即作废.
            隐藏状态下调用**不会**启动线程 —— 等标签页显示时才开始跑（不看不画）.
        """
        if not (callable(getattr(shared_value, 'get', None))
                and callable(getattr(shared_value, 'set', None))):
            raise ValueError('shared_value must provide get() and set(value)')
        if not callable(on_figure):
            raise ValueError('on_figure must be callable: on_figure(fig, data)')

        self._shared = shared_value
        self._on_figure = on_figure
        self._error = ''
        self._stats = {}  # 统计由线程重置，这里先清空显示

        thread = self._ensure_thread()
        thread.set_source(shared_value, on_figure)
        self._push_autosave()
        if self._visible:  # 隐藏着就别白跑：等 showEvent 再说
            self._start_thread()
            thread.set_active(not self._user_paused)
            thread.poke()
        self._sync_labels()

    # ============================================================== 框架钩子
    def refresh(self):
        """框架钩子：切回本标签页 / 菜单「操作 → 刷新」时被调用.

        ⚠️ 规范要求 ``refresh()`` 必须快（每次切标签都会调）。这里只做一次唤醒，
        **不**同步取数据、**不**同步绘图 —— 真正的活全在绘图线程里，事件循环立刻返回。
        """
        thread = self._thread
        if thread is not None:
            thread.poke()

    def save_file(self):
        """把**当前画面**存成 PNG，返回路径（框架钩子：菜单「文件 → 保存」）.

        ⚠️ **不弹对话框**（与 ``MatplotWidget.save_file`` 的语义一致）：存到控制条上
        那个「保存目录」（与自动保存同一个目录），文件名用当前时间.

        ⚠️ 关标签时 ``TabWidget`` 也会调它（只要 :meth:`need_save` 为真）—— 正因为它
        不弹对话框，关标签才不会被一个「另存为」卡住.
        """
        image = self._last_image
        if image is None:
            return None
        try:
            folder = self._save_folder or self._default_folder()
            os.makedirs(folder, exist_ok=True)
            now = datetime.datetime.now()
            name = now.strftime('%Y-%m-%d-%H-%M-%S-') + '{0:06d}'.format(now.microsecond)
            path = os.path.join(folder, '{0}.png'.format(name))
            if not image.save(path, 'PNG'):
                print('PltLiveView: 保存图片失败 —— {0}'.format(path))
                return None
            return path
        except Exception as err:
            print('PltLiveView: 保存图片失败 —— {0}'.format(err))
            return None

    def need_save(self):
        """框架钩子：有没有「值得保存」的内容（决定菜单「保存」的灰 / 亮）."""
        return self._last_image is not None

    def cleanup_before_tab_close(self):
        """关标签前的收尾：通知绘图线程收工、放掉引用.

        ⚠️ 这里**不** ``wait()``（规范：清理钩子不许阻塞）。线程能被安全回收靠的是
        「不设 parent + 类级强引用」那两条纪律；本方法只负责「通知它该走了」，并立刻
        摘掉引用 —— 之后迟到的信号由 Qt 自动断开（槽都是绑定方法），槽里另有一道
        ``self._thread is None`` 的闸门兜底.
        """
        self._visible = False
        self._user_paused = False
        thread, self._thread = self._thread, None
        self._shared = None
        self._on_figure = None
        self._last_image = None
        self._stats = {}
        self._error = ''
        if thread is not None:
            try:
                thread.stop()
            except Exception:
                pass  # 线程已 finished / 已被销毁：静默跳过
        self._sync_labels()  # 让「已关闭」这个状态在界面上立即可见（控件还没销毁）

    # ============================================================== 生命周期
    def showEvent(self, event):
        """标签页被切到本页：启动（或恢复）绘图线程，并**立即**试取一次数据."""
        super(PltLiveView, self).showEvent(event)
        self._visible = True
        self._push_size()
        if self._shared is not None:
            self._start_thread()
            thread = self._thread
            if thread is not None:
                thread.set_active(not self._user_paused)
                thread.poke()
        self._sync_labels()

    def hideEvent(self, event):
        """标签页被切走：绘图循环进入**阻塞式暂停**（连 ``get()`` 都不做）."""
        super(PltLiveView, self).hideEvent(event)
        self._visible = False
        thread = self._thread
        if thread is not None:
            thread.set_active(False)
        self._sync_labels()

    def resizeEvent(self, event):
        """尺寸变了：把新的渲染目标尺寸推给绘图线程（**不唤醒**，免得拖动时反复重绘）."""
        super(PltLiveView, self).resizeEvent(event)
        self._push_size()

    def changeEvent(self, event):
        """窗口被拖到另一块「缩放比例不同」的屏幕上时，重推一次渲染尺寸.

        ⚠️ 不处理的话，位图会按旧的 dpr 渲染、再被 Qt 按新 dpr 缩放 —— 字就糊了。
        ``DevicePixelRatioChange`` 是 Qt 6.6 才有的枚举，取不到就静默跳过（老版本
        本来也不会发这个事件）.
        """
        super(PltLiveView, self).changeEvent(event)
        kind = getattr(QtCore.QEvent.Type, 'DevicePixelRatioChange', None)
        if kind is not None and event.type() == kind:
            self._push_size()

    def closeEvent(self, event):
        """控件被单独 ``close()`` 时也做同样的收尾（直接跑 ``test_1()`` 走这条路）.

        ⚠️ 关标签页**不走**这里（那边是 ``deleteLater()``，不发 ``closeEvent``）。
        """
        self.cleanup_before_tab_close()
        super(PltLiveView, self).closeEvent(event)

    # ============================================================== 右键菜单
    def get_context_menu(self):
        """右键菜单（与 ``MatplotWidget`` 的能力对齐：刷新 / 暂停 / 导出 / 复制）."""
        from zmlx.ui.alg import create_action

        menu = QtWidgets.QMenu(self)
        menu.addAction(create_action(self, '立即刷新', icon='refresh', slot=self.refresh))

        # ⚠️ QAction 在 PyQt6 里属于 QtGui、PyQt5 里属于 QtWidgets —— 一律用
        #    ``zmlx.ui.pyqt`` 统一导出的那个名字，别直接写 ``QtWidgets.QAction``
        pause_action = QAction('暂停刷新', menu)
        pause_action.setCheckable(True)
        pause_action.setChecked(self._user_paused)
        # 菜单项与按钮共用一份状态：点这个就等于点那个按钮
        pause_action.triggered.connect(self.pause_button.toggle)
        menu.addAction(pause_action)

        menu.addSeparator()
        menu.addAction(create_action(self, '保存到默认目录', icon='save',
                                     slot=self.save_file))
        menu.addAction(create_action(self, '另存为…', icon='export', slot=self._save_as))
        menu.addAction(create_action(self, '复制到剪贴板', icon='export',
                                     slot=self._copy_to_clipboard))

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

    def _save_as(self):
        """弹框选择路径保存当前画面."""
        image = self._last_image
        if image is None:
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, caption='请选择保存路径', directory=os.getcwd(),
            filter='Png图片(*.png);;Jpg图片(*.jpg);;所有文件(*.*)')
        if path is not None and len(path) > 0:
            if not image.save(path):
                print('PltLiveView: 保存图片失败 —— {0}'.format(path))

    def _copy_to_clipboard(self):
        """把当前画面放到剪贴板."""
        image = self._last_image
        if image is not None:
            QtWidgets.QApplication.clipboard().setImage(image)

    # ============================================================== 线程联动
    def _ensure_thread(self):
        """创建绘图线程（**不启动**）并接好信号."""
        if self._thread is None:
            thread = _RenderThread(bg=self._bg, clear=self._clear)
            thread.sig_frame.connect(self._on_frame)
            thread.sig_stats.connect(self._on_stats)
            thread.sig_error.connect(self._on_error)
            thread.set_interval(self.interval_box.value())
            self._thread = thread
            self._push_size()
            self._push_autosave()
        return self._thread

    def _start_thread(self):
        """启动绘图线程（已在跑就不重复启动）."""
        thread = self._ensure_thread()
        if not thread.isRunning():
            thread.start_quietly()

    def _push_size(self):
        """把绘图区当前的（逻辑）尺寸与 dpr 推给绘图线程."""
        thread = self._thread
        if thread is None:
            return
        canvas = self.canvas
        try:
            dpr = float(canvas.devicePixelRatioF())
        except Exception:
            dpr = 1.0
        thread.set_size(max(240, canvas.width()), max(180, canvas.height()), dpr)

    def _push_autosave(self):
        """把「自动保存」的两项设置推给绘图线程."""
        thread = self._thread
        if thread is not None:
            thread.set_autosave(self._autosave, self._save_folder)

    def _on_frame(self, image, cost):
        """绘图线程送来一帧（主线程执行）."""
        if self._thread is None:
            return  # 已经收工（关标签了）
        self._error = ''
        self._last_image = image
        self.canvas.set_image(image)
        self._sync_labels()

    def _on_stats(self, stats):
        """绘图线程送来一轮统计（主线程执行）."""
        if self._thread is None:
            return
        self._stats = stats
        self._sync_labels()

    def _on_error(self, text):
        """绘图回调 / 渲染失败（主线程执行）."""
        if self._thread is None:
            return
        self._error = str(text)
        self._sync_labels()

    # ============================================================== 控制条
    def _load_interval(self):
        """读上次用的睡眠间隔（读不到 / 非法就回默认值）."""
        try:
            value = float(app_data.getenv(self.SETTING_KEY,
                                          default=self.DEFAULT_INTERVAL))
        except (TypeError, ValueError):
            value = self.DEFAULT_INTERVAL
        if not (value > 0):
            value = self.DEFAULT_INTERVAL
        return min(self.MAX_INTERVAL, max(self.MIN_INTERVAL, value))

    @staticmethod
    def _default_folder():
        """默认的存图目录：<用户缓存目录>/plt_live_view（稳定，不随进程变）."""
        try:
            return app_data.root('plt_live_view')
        except Exception:
            return os.path.join(os.path.expanduser('~'), 'plt_live_view')

    def _load_autosave(self):
        """读「自动保存」开关（默认关：不主动往磁盘写东西）."""
        try:
            text = app_data.getenv(self.AUTOSAVE_KEY, default='') or ''
        except Exception:
            text = ''
        return str(text).strip().lower() in ('yes', 'true', '1', 'on')

    def _load_folder(self):
        """读存图目录；没配过就用默认目录.

        ⚠️ 这里**不**检查「目录是否还存在」：用户选的是外接盘 / 网络盘时，盘暂时不在
        就「悄悄改存到缓存目录」比「存失败并报出来」更糟 —— 图片会散落在两个地方。
        目录由 :meth:`_RenderThread._save` 负责创建，真建不出来就在统计里显示失败次数.
        """
        try:
            folder = str(app_data.getenv(self.FOLDER_KEY, default='') or '').strip()
        except Exception:
            folder = ''
        return folder if folder else self._default_folder()

    def _on_interval_changed(self, value):
        """睡眠间隔被改：立刻生效，并记到设置里（下次打开还是这个值）."""
        value = min(self.MAX_INTERVAL, max(self.MIN_INTERVAL, float(value)))
        thread = self._thread
        if thread is not None:
            thread.set_interval(value)
        try:
            app_data.setenv(self.SETTING_KEY, '{0:g}'.format(value))
        except Exception:
            pass

    def _on_pause_toggled(self, checked):
        """「暂停 / 继续」按钮被切换."""
        self._user_paused = bool(checked)
        self.pause_button.setText('继续' if self._user_paused else '暂停')
        thread = self._thread
        if thread is not None:
            thread.set_active(self._visible and not self._user_paused)
            if not self._user_paused:
                thread.poke()
        self._sync_labels()

    def _on_autosave_toggled(self, checked):
        """「自动保存」被勾选 / 取消（立刻生效，并记到设置里）."""
        self._autosave = bool(checked)
        try:
            app_data.setenv(self.AUTOSAVE_KEY, 'Yes' if self._autosave else 'No')
        except Exception:
            pass
        self._push_autosave()
        if self._autosave:
            self.refresh()  # 勾上之后马上存一张，别让用户干等一个间隔
        self._sync_labels()

    def _choose_folder(self):
        """选自动存图的目录（选完立刻生效，并记到设置里）."""
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, '选择自动保存目录', self._save_folder or os.getcwd())
        if folder:
            self._set_save_folder(folder)

    def _set_save_folder(self, folder):
        """设置自动存图目录（空值 → 回默认目录）."""
        folder = str(folder).strip() if folder is not None else ''
        self._save_folder = os.path.abspath(folder) if folder else self._default_folder()
        try:
            app_data.setenv(self.FOLDER_KEY, self._save_folder)
        except Exception:
            pass
        self.folder_button.setToolTip('自动保存到：{0}'.format(self._save_folder))
        self._push_autosave()
        self._sync_labels()

    # ============================================================== 状态与统计文字
    def _sync_labels(self):
        """刷新状态行与统计行（**只在文字变了才 setText**）.

        ⚠️ 为什么要在意「变了才写」：绘图线程**每一轮**都会发一次统计，间隔设成 0.1 s
        就是每秒 10 次 —— 每次都 ``setText`` 会让整个标签页不停地重排布局.
        """
        state = self._state_text()
        if state != self._state_cache:
            self._state_cache = state
            self.state_label.setText(state)
        stats = self._stats_text()
        if stats != self._stats_cache:
            self._stats_cache = stats
            self.stats_label.setText(stats)

    def _state_text(self):
        """左边那格：当前在干什么（一行，过长会被截断）."""
        if self._thread is None:
            return '已关闭'
        if self._user_paused:
            return '已暂停（点「继续」恢复）'
        if not self._visible:
            return '标签页未显示 —— 绘图循环暂停'
        if self._shared is None or self._on_figure is None:
            return '未设置数据源（set_data）'
        if self._error:
            return '绘图失败：{0}'.format(self._error[:100])
        if not self._stats or self._stats.get('frames', 0) <= 0:
            return '等待数据…'
        return '运行中'

    def _stats_text(self):
        """右边那格：绘图次数 / 尝试次数 / 耗时 / 空闲（口径见模块文档）."""
        stats = self._stats
        if not stats:
            return '绘图 0 次 · 尝试 0 次 · 空闲 0.0 s'
        frames = int(stats.get('frames', 0))
        total = float(stats.get('total_cost', 0.0))
        parts = [
            '绘图 {0} 次'.format(frames),
            '尝试 {0} 次'.format(int(stats.get('attempts', 0))),
        ]
        fails = int(stats.get('fails', 0))
        if fails > 0:
            parts.append('失败 {0} 次'.format(fails))
        parts.append('耗时 {0:.2f} s'.format(total))
        if frames > 0:
            parts.append('上次 {0:.2f} s'.format(float(stats.get('last_cost', 0.0))))
            parts.append('平均 {0:.2f} s'.format(total / frames))
        parts.append('空闲 {0:.1f} s'.format(float(stats.get('idle', 0.0))))
        saved = int(stats.get('saved', 0))
        if saved > 0:
            parts.append('已存 {0} 张'.format(saved))
        save_fails = int(stats.get('save_fails', 0))
        if save_fails > 0:
            parts.append('存图失败 {0} 次'.format(save_fails))
        return ' · '.join(parts)


def test_1():
    """直接运行本文件时的自测：模拟「内核线程 + 慢绘图 + 自动保存」的完整链路.

    直接跑::

        python zmlx/ui/tabs/plt_live_view.py          # 正常速度
        python zmlx/ui/tabs/plt_live_view.py --slow   # 每帧故意多花 2 s，验证界面不卡
        python zmlx/ui/tabs/plt_live_view.py --save   # 顺便打开「自动保存」看看统计

    看什么：① 图每隔一秒左右自己刷新；② 下面两行文字在动（状态 + 统计：绘图次数、
    尝试次数、耗时、空闲）；③ ``--slow`` 下照样能拖动窗口、拖控制条、点按钮（说明
    绘图线程没有把 GUI 线程堵住）；④ 切到别的标签再切回来，会立刻刷新一次；
    ⑤ ``--save`` 时「已存 N 张」会涨，图片落在「保存目录…」指定的位置。
    """
    import threading

    import numpy

    app = QtWidgets.QApplication(sys.argv)
    from zmlx.ui.utils.shared import SharedValue

    shared = SharedValue()
    stop = threading.Event()
    slow = '--slow' in sys.argv

    def kernel():
        """模拟计算内核：**只在共享格子空着时**才准备数据（准备本身有耗时）."""
        step = 0
        forced_at = time.monotonic()
        while not stop.is_set():
            forced = (time.monotonic() - forced_at) >= 4.0  # 过期太久就强制刷一版
            if shared.get() is None or forced:
                time.sleep(0.4)  # ← 模拟「准备数据」的计算开销
                if stop.is_set():
                    return
                t = numpy.linspace(0.0, 1.0, 5000)
                x = numpy.linspace(-1.0, 1.0, 260)
                y = numpy.linspace(-1.0, 1.0, 260)
                xx, yy = numpy.meshgrid(x, y)
                # ⚠️ 每次都造**新对象**（不复用缓冲区），这是线程间交接的基本要求
                shared.set(dict(
                    step=step,
                    t=t,
                    curve=numpy.sin(2.0 * numpy.pi * (0.8 * t + 0.05 * step)),
                    field=numpy.sin(3.0 * xx + 0.15 * step) * numpy.cos(2.5 * yy),
                ))
                step += 1
                forced_at = time.monotonic()
                continue
            time.sleep(0.05)  # ← 已经画过了：这一步什么都不准备

    def on_figure(fig, data):
        """绘图回调：**在绘图线程里执行**，只碰 fig 与 data."""
        axes = fig.subplots(2, 1)
        axes[0].plot(data['t'], data['curve'], lw=1.2)
        axes[0].set_title('模拟内核数据 · 第 {0} 步'.format(data['step']))
        axes[0].set_xlabel('t')
        axes[0].set_ylabel('sin')
        axes[1].imshow(data['field'], origin='lower', extent=[-1, 1, -1, 1],
                       aspect='auto', cmap='viridis')
        axes[1].set_xlabel('x')
        axes[1].set_ylabel('y')
        fig.tight_layout()
        if slow:
            time.sleep(2.0)  # ← 就是这里：绘图本身很慢，但界面不该卡

    view = PltLiveView()
    view.set_data(shared, on_figure)
    view.resize(1000, 760)
    view.setWindowTitle('PltLiveView — 模拟内核线程 + 慢绘图' +
                        ('（--slow）' if slow else ''))
    if '--save' in sys.argv:
        # 演示「每帧自动存图」。⚠️ 刻意**绕开** _on_autosave_toggled 的持久化：自测不该
        # 顺手改掉用户真正的设置（否则哪天真开界面时会发现「自动保存」莫名其妙是开的）。
        view._save_folder = view._default_folder()
        view._autosave = True
        view.autosave_box.blockSignals(True)
        view.autosave_box.setChecked(True)
        view.autosave_box.blockSignals(False)
        view.folder_button.setToolTip('自动保存到：{0}'.format(view._save_folder))
        view._push_autosave()
    view.show()

    threading.Thread(target=kernel, name='DemoKernel', daemon=True).start()
    try:
        code = app.exec()
    finally:
        stop.set()
        view.cleanup_before_tab_close()  # 直接跑时的收尾（关标签路径由框架负责）
    sys.exit(code)


if __name__ == '__main__':
    test_1()
