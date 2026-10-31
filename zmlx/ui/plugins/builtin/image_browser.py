# ** name = '图片浏览'
# ** desc = '扫描工作路径下的图片，左侧缩略图相册 + 右侧大图预览，支持连续播放'
"""图片浏览器（ImageBrowser — 浏览 / 预览 / 动画播放工作路径下的图片）+ 菜单入口.

**本文件自含**：控件 :class:`ImageBrowser` 与它挂到界面上的入口（「文件 → 浏览 → 图片」）
都在这里，不再从 ``zmlx.ui.tabs`` 导入任何东西。

**用途**：方便查看计算产生的图片结果。打开即扫描「工作路径」及其下至多
``SCAN_MAX_DEPTH`` 层子目录里的所有图片，左侧是缩略图相册（类似手机相册），
点哪张就在右侧大图区显示；支持上一张 / 下一张 / 按设定帧率连续播放。

⚠️ **2026-10-30 由 ``zmlx/ui/tabs/image_browser.py`` 整体并入本文件**，原文件已删除、
**不留转发垫片**（已核实全仓 + 外部工作区都没有别处 import 它，唯一引用就是本插件；
打开入口走的是命令 ``gui.show_image_browser()``，与控件路径无关）。合并的理由是
[`../AGENTS.md`](../AGENTS.md) §0.2 那条目标：「**关掉功能时，它的代码也应当能一起关掉**」——
控件只服务这一个可关闭的插件，单文件自足才算真的独立完整。

目录是「跟随工作路径」的（默认）
--------------------------------
⚠️ **每次扫描都现取 ``os.getcwd()``，不冻结**。所以用户在别处改了工作路径
（菜单「设置 → 工作路径」，或 ``os.chdir``）再回到本页点「刷新」，
看到的就是**新**目录里的图 —— 这正是「看当前工作路径下的图」应有的语义。
（早期版本把目录冻结在构造那一刻，切了工作路径再刷新还是旧图，已改掉。）

需要固定在某个目录时用 :meth:`ImageBrowser.set_folder`（此后不再跟随工作路径）；
想回到跟随用 :meth:`ImageBrowser.follow_cwd`。

⚠️ 内部把「跟随」与「本次扫的是哪儿」**分成两个概念**，不能合成一个：
``_resolve_folder()`` 现算「该扫哪儿」，``_scan_target`` 记下「本次扫描的目标」。
扫描是异步的，结果回来时要按 ``_scan_target`` 校验 —— 若改用「当前工作路径」去比，
用户在扫描途中切了目录，那份本来有效的结果会被误丢。

界面
----
::

    ┌────────────┬──────────────────────────────────────────┐
    │ 目录 + 计数 │            主显示区（按比例缩放居中）        │
    │ ┌────────┐ ├──────────────────────────────────────────┤
    │ │缩略图 1│ │ 上一张  播放/暂停  下一张  帧率  循环  继续播放 │
    │ │缩略图 2│ ├──────────────────────────────────────────┤
    │ │缩略图 3│ │ 进度条 ───────────────●────── 12 / 240  刷新 │
    │ └────────┘ ├──────────────────────────────────────────┤
    │            │ 文件名 · 尺寸 · 体积 · 所在子目录            │
    └────────────┴──────────────────────────────────────────┘

⚠️ **本控件故意不实现 ``refresh()``**：项目里 ``refresh()`` 是「切到本标签页时被调一次」
的钩子，而图片目录的重新扫描有明显的 IO 代价，不该由「用户切了下标签」触发。
刷新**只**由界面上的「刷新」按钮（以及首次显示时的一次）发起 —— 这正是需求里
「不要用切换标签就会自动刷新的 refresh 方法」的落点。

三个后台线程（全部压低优先级，见 ``_Worker``）
---------------------------------------------

======== ==================  ==========================================
线程      职责                优先级
======== ==================  ==========================================
``_ScanThread``  遍历目录、收集图片路径   ``LOWEST``（纯 IO）
``_ThumbThread`` 生成左侧相册缩略图       ``LOWEST``（数量多，最该让路）
``_LoadThread``  按显示尺寸解码大图       ``BELOW_NORMAL``（要跟上播放节奏）
======== ==================  ==========================================

⚠️ 播放的「换帧」本身由 GUI 线程里的 ``QTimer`` 完成（只是把一张已经解好的图贴上去，
开销极小）；真正吃 CPU 的**解码**在 ``_LoadThread`` 里，所以「播放时也用低优先级」
是在解码线程上兑现的。

线程生命周期（项目铁律，见 ``zmlx/ui/widgets/AGENTS.md``）
--------------------------------------------------------

1. **线程一律不设 parent**（写 ``_ScanThread()``，不写 ``_ScanThread(self)``）：
   关标签走 ``deleteLater()``，parent 指向本控件的 ``QThread`` 会被连带析构，
   而它在运行中被析构会让进程直接崩（``QThread: Destroyed while thread is still
   running``，**不是** Python 异常，``try/except`` 兜不住）。
2. **强引用放在类属性 ``_Worker._RUNNING`` 里**（不放模块级 —— 本包规范要求模块级
   只留 import / 类定义 / ``test_1()``）。跑完由 ``finished`` 摘表并 ``deleteLater()``。
3. ``cleanup_before_tab_close()`` **只通知、不阻塞**（规范：两个清理钩子里都不许
   ``wait()``）。线程能安全回收靠的是上面两条，不靠这个钩子。

标签被隐藏 / 恢复
-----------------

播放中切走标签（``hideEvent``）会**暂停**并记下这件事；切回来时（``showEvent``）
「继续播放」按钮出现，点它接着播。手动暂停不会点亮那个按钮。

按尺寸自适应（响应式）
----------------------

**总原则：宁可少显示一个次要部件，也不把所有部件都挤成看不清。**
窗口变窄时按 ``TINY_WIDTH`` / ``NARROW_WIDTH`` 两级降级（见
:meth:`ImageBrowser._update_responsive`）：

================================  ==========================================
宽度                               显示
================================  ==========================================
>= ``NARROW_WIDTH``（620）          完整：相册 + 大图 + 完整控制条 + 信息行
>= ``TINY_WIDTH``（560）            同上，但「帧率」二字与「循环」让位
<  ``TINY_WIDTH``                   **收起左侧相册**，宽度全给大图
================================  ==========================================

⚠️ 断点必须落在「控件真能到达的宽度」内。本控件的最小宽由控制条决定，实测 **438 px**
（拖到更窄会被这个下限卡住）—— 所以断点小于 438 就是**死代码**（初版写的 420 就犯了这个错）。

⚠️ 两处「文字可能比可用宽度长」的地方（左栏路径 + 右下信息行）都靠
:meth:`ImageBrowser._fit` 兜底：它保证返回值**一定塞得进给定宽度**，
而这两个标签的水平尺寸策略必须是 ``Ignored`` —— 否则 ``QLabel.minimumSizeHint()``
等于整段文字宽度，会把所在分栏"顶"开（实测长路径曾把窗口压成「左 1512 / 右 550」，
连 ``splitter.setSizes()`` 都拦不住）。两者缺一不可，理由详见 :meth:`ImageBrowser._fit`。

已知取舍
--------

- 动图（GIF / APNG）**只显示第一帧**：这里要的是「批量看结果图」，不是动图播放器。
- **默认不收 `pdf`**（``SKIP_EXTS``）：Qt 的图片插件确实能把它当图读，但 pdf 是多页文档，
  塞进单图查看器只会显示第 1 页。想收就清空 ``SKIP_EXTS``。
- 解码按**显示尺寸**而非原始尺寸（``QImageReader.setScaledSize``，并用文件头里的
  原始尺寸判断是否真需要缩）—— 否则一张 8000×8000 的图会让播放卡住。
  目标尺寸量化到 256 的整数倍，避免拖动窗口时反复重解码。
- Windows 上额外用 ``SetThreadPriority`` 把 OS 线程优先级压到 ``LOWEST`` /
  ``BELOW_NORMAL``（Qt 的 ``QThread.Priority`` 只到「低于正常」一档）；其它平台静默跳过。

菜单入口（本文件后半部分）
--------------------------

=======================  ============================================
入口                       调用
=======================  ============================================
菜单「文件 → 浏览 → 图片」    :func:`show_image_browser`
GUI 命令                  ``gui.show_image_browser()``
=======================  ============================================

⚠️ **2026-10-26 起菜单项是「文件 → 浏览」的子菜单项**（原先直接挂在「文件 → 图片浏览」）：
「工作目录」浏览（插件 ``viewers`` 的 ``view_cwd``）与「图片」都是「看文件」的入口，
两者合成一个子菜单，用户不必在两个位置各找一次。

⚠️ 位置由**本插件**（而不是 ``viewers``）决定：子菜单 `['文件', '浏览']` 由
``MainWindow.get_menu`` **按标题、缺则新建**，所以两个插件谁先加载都能并进同一个
「浏览」；而本插件被禁用时，「工作目录」那一项照样出现（``viewers`` 自己建出这个
子菜单）。

为什么是插件（``plugins/``）而不是 ``setups/``
--------------------------------------------------

图片浏览是**工具型、非核心**的功能，不该出现在「必须提供」的菜单里 ——
所以做成插件，用户不需要时可以在「设置 → 插件」里关掉，菜单项随之消失。

⚠️ 2026-10-18 由 ``setups/image_browser.py`` 移到这里（同理还有
``vtk_view.py`` / ``zip_files.py``）。两者的分工见 :mod:`zmlx.ui.plugins`：
**产品功能**（授权查询、用户管理）留 ``setups``，**可关闭的扩展**放这里。

⚠️⚠️ **``open_image`` 与 ``ImageView`` 2026-10-22 一度搬进本文件，同日又还原**：
欢迎页在 ``MainWindow.__init_actions`` 里就要用它，``gui.open_image`` 是**底层能力**，
不该随插件开关而消失。现在它们分别在 ``MainWindow.open_image`` 与
``ui/tabs/img.py``（``ImageView``），``.png/.jpg`` 文件类型也回到 ``main.py`` 的
``__init_actions`` 里注册。

⚠️ 因此别把两者混为一谈：``ImageView``（单图滚轮缩放查看器）仍在 ``tabs/img.py``，
由 ``gui.open_image`` 使用、**不随本插件开关**；本文件里的 ``ImageBrowser`` 是
**相册浏览**（扫描目录 + 缩略图 + 连播），引擎与入口都在本文件内。

⚠️ **``gui.show_image_browser()`` 是给 ``gui_restore`` 用的**：标签页被存进标签
状态后，重启时按这串原文重放，所以命令名一旦发布就**不能再改**（照
``user_admin.py`` 末尾那几条旧名别名的既定纪律）。

⚠️ 命令名**必须与 ``MainWindow`` 已有的方法名不撞车**：``__init_gui_api`` 会把主窗口
的所有公开方法自动注册进命令表，撞名就会把那个方法悄悄顶掉。``show_image_browser``
在 ``main.py`` 里不存在（这正是「不动 ``main.py``」的实现方式），所以安全。

只切页、不重扫
--------------

``get_widget`` 在窗口里**按「类型 + 标题」复用**已有的标签页：反复点菜单只会把
「图片浏览」那一页切到前面，**不会越开越多**。

⚠️ 因此 ``oper`` 里**只**记 ``gui_restore``，不调刷新 —— ``get_widget`` 每次调用都会
跑到 ``oper``（点菜单也不例外），在里面刷新就等于「点一次菜单重扫一次目录」。
本控件也不实现 ``refresh()``（切标签页**不**自动重扫，刷新只由页面上的「刷新」按钮
触发），两处口径一致：**重建视图只发生在真的新建标签页时**。

Created by DeepSeek, 2026-10-16
Modified by DeepSeek, 2026-10-22: ``ImageView`` 与 ``open_image`` 一度并入本文件
Modified by DeepSeek, 2026-10-22: 同日**还原** —— ``open_image`` 是底层能力（欢迎页在
    ``MainWindow`` 构造期就要用），控件回 ``ui/tabs/img.py``、命令回 ``MainWindow``；
    本插件只留「相册浏览」
Modified by DeepSeek, 2026-10-26: 菜单项搬到「文件 → 浏览」子菜单下（文字「图片」）；
    命令名 ``gui.show_image_browser`` 与 action name 均未变
Modified by DeepSeek, 2026-10-30: 控件 ``ImageBrowser`` 由 ``ui/tabs/image_browser.py``
    整体并入本文件（原文件删除、**不留垫片**）；命令名 / action name / 控件的公开接口
    （``set_folder`` / ``follow_cwd`` / ``rescan`` / ``play`` …）均未变
"""

from zmlx.system import execute_once

import collections
import os
import sys

from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets


class _Worker(QtCore.QThread):
    """后台线程基类：统一「低优先级」与「可安全停止」两件事。

    一个任务队列 + 一个停止位，是三个具体线程（扫描 / 缩略图 / 解码）共用的骨架。
    线程体里**绝不碰界面**（Qt 的规矩），结果一律经信号回主线程。

    Attributes:
        OS_PRIORITY_LOWEST: ``SetThreadPriority`` 的 ``THREAD_PRIORITY_LOWEST``。
        OS_PRIORITY_BELOW_NORMAL: 同上，``THREAD_PRIORITY_BELOW_NORMAL``。
        _RUNNING: 类级强引用登记表。⚠️ 线程**不设 parent**，必须有别的东西持着它，
            否则运行中被 GC 回收 = 进程崩溃。跑完自动摘表。
    """

    OS_PRIORITY_LOWEST = -2
    OS_PRIORITY_BELOW_NORMAL = -1

    _RUNNING = set()

    def __init__(self, os_priority=OS_PRIORITY_BELOW_NORMAL, qt_priority=None,
                 parent=None):
        """初始化。

        Args:
            os_priority: OS 级优先级（Windows 用；其它平台忽略）。
            qt_priority: ``QThread.Priority``；None 表示「低于正常」。
            parent: ⚠️ **一律留空** —— 理由见模块 docstring 的「线程生命周期」。
        """
        super(_Worker, self).__init__(parent)
        self.setObjectName(type(self).__name__)
        self._os_priority = int(os_priority)
        self._qt_priority = qt_priority
        self._mutex = QtCore.QMutex()
        self._cond = QtCore.QWaitCondition()
        self._jobs = collections.deque()
        self._stopped = False

    # ------------------------------------------------------------------ 启动 / 停止
    def start_quietly(self):
        """登记强引用后以低优先级启动。"""
        _Worker._RUNNING.add(self)
        # 与 demo_view.py 的写法一致：用带默认参数的 lambda 持住线程本体，
        # 跑完先摘登记表、再 deleteLater（槽按连接顺序触发，摘表必须在销毁之前）。
        self.finished.connect(lambda t=self: _Worker._RUNNING.discard(t))
        self.finished.connect(self.deleteLater)
        self.start(self._qt_priority if self._qt_priority is not None
                   else QtCore.QThread.Priority.LowPriority)

    def stop(self):
        """请求收工：清空待办、唤醒等待、置停止位。**不阻塞**（规范要求）。"""
        self.requestInterruption()
        with QtCore.QMutexLocker(self._mutex):
            self._stopped = True
            self._jobs.clear()
        self._cond.wakeAll()

    def is_stopped(self):
        """是否已被要求停止。"""
        return bool(self._stopped) or self.isInterruptionRequested()

    # ------------------------------------------------------------------ 任务队列
    def submit(self, job, *, replace=True):
        """投递任务。

        Args:
            job: 任务对象（各子类自己解释）。
            replace: True 表示「**替换**待办」而不是排队 —— 扫描与播放这类场景
                只关心最新一次请求，排队反而会做无用功。
        """
        with QtCore.QMutexLocker(self._mutex):
            if replace:
                self._jobs.clear()
            self._jobs.append(job)
        self._cond.wakeAll()

    def clear_jobs(self):
        """清空待办（正在处理的那个不受影响）。"""
        with QtCore.QMutexLocker(self._mutex):
            self._jobs.clear()

    def take_job(self, wait_ms=250):
        """取一个任务；没有就最多等 ``wait_ms`` 毫秒。

        Returns:
            任务对象；**None 表示「该退出了」**（收到停止请求）。
        """
        with QtCore.QMutexLocker(self._mutex):
            while True:
                if self._stopped:
                    return None
                if self._jobs:
                    return self._jobs.popleft()
                self._cond.wait(self._mutex, wait_ms)

    # ------------------------------------------------------------------ 优先级
    def lower_os_priority(self):
        """把**当前线程**的 OS 优先级压到 ``self._os_priority``。

        只在真的要干活了才调（由线程体开头调用），非 Windows 平台静默跳过 ——
        那时 Qt 的 ``QThread.Priority.LowPriority`` 仍然生效，只是「低」不到那么低。
        """
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            kernel32.GetCurrentThread.restype = ctypes.c_void_p
            kernel32.SetThreadPriority.argtypes = [ctypes.c_void_p, ctypes.c_int]
            kernel32.SetThreadPriority.restype = ctypes.c_int
            kernel32.SetThreadPriority(kernel32.GetCurrentThread(),
                                       self._os_priority)
        except Exception:
            pass


class _ScanThread(_Worker):
    """在后台遍历目录、收集图片路径（**纯 IO，绝不碰界面**）。

    用「令牌」而不是「打断标志」来取消：每次 ``request_scan`` 都让令牌自增，
    遍历途中一旦发现令牌变了就立刻返回，于是「刷新」按钮连点几下不会叠加出多趟扫描。

    Attributes:
        sig_found: ``(folder, paths)`` —— 扫描完成。
        sig_failed: ``(folder, message)`` —— 目录不存在 / 无权限等。
    """

    sig_found = QtCore.pyqtSignal(str, list)
    sig_failed = QtCore.pyqtSignal(str, str)

    def __init__(self):
        super(_ScanThread, self).__init__(os_priority=_Worker.OS_PRIORITY_LOWEST,
                                          qt_priority=QtCore.QThread.Priority.LowPriority)
        self._token = 0

    def request_scan(self, folder):
        """请求扫描 ``folder``（替换掉之前排队的请求）。"""
        with QtCore.QMutexLocker(self._mutex):
            self._token += 1
            job = (str(folder), self._token)
            self._jobs.clear()
            self._jobs.append(job)
        self._cond.wakeAll()

    def run(self):
        """线程体：不断取「要扫的目录」，扫完把结果发回主线程。"""
        self.lower_os_priority()
        while True:
            job = self.take_job()
            if job is None:
                break
            folder, token = job
            try:
                paths = self._walk(folder, token)
            except Exception as err:  # 防御性：异常绝不允许逃出 run()
                self.sig_failed.emit(folder, '{0}: {1}'.format(type(err).__name__, err))
                continue
            if paths is not None and not self.is_stopped() and token == self._token:
                self.sig_found.emit(folder, paths)

    def _walk(self, folder, token):
        """遍历 ``folder`` 及其下至多 ``ImageBrowser.SCAN_MAX_DEPTH`` 层子目录。

        Returns:
            list: 图片绝对路径；**None 表示这趟遍历已被取消**（期间又发起了新的扫描）。
        """
        root = os.path.abspath(folder)
        if not os.path.isdir(root):
            self.sig_failed.emit(folder, '目录不存在')
            return None

        depth_limit = ImageBrowser.SCAN_MAX_DEPTH
        cap = ImageBrowser.MAX_FILES
        found = []
        stack = [(root, 0)]
        while stack:
            if self.is_stopped() or token != self._token:
                return None
            current, depth = stack.pop()
            try:
                with os.scandir(current) as it:
                    entries = sorted(it, key=lambda e: e.name.lower())
            except OSError:
                continue  # 无权限 / 目录刚被删：跳过，不影响其余
            for entry in entries:
                if self.is_stopped() or token != self._token:
                    return None
                try:
                    if entry.is_dir(follow_symlinks=False):
                        if depth < depth_limit and ImageBrowser.is_visible_dir(entry.name):
                            stack.append((entry.path, depth + 1))
                    elif entry.is_file() and ImageBrowser.is_image(entry.name):
                        found.append(entry.path)
                        if len(found) >= cap:
                            return sorted(found)
                except OSError:
                    continue
        return sorted(found)


class _ThumbThread(_Worker):
    """在后台生成左侧相册的缩略图（**纯计算，绝不碰界面**）。

    计划是「替换式」的：``submit_plan`` 一次性给出「还有哪些图要缩略图」，
    刷新时清空即可，不需要单独的实现来取消。

    Attributes:
        sig_thumb: ``(index, path, image)`` —— 某一张的缩略图好了。
    """

    sig_thumb = QtCore.pyqtSignal(int, str, QtGui.QImage)

    #: 每处理这么多张就主动让一下（低优先级线程也别把 GIL 攥死）
    YIELD_EVERY = 8

    def __init__(self):
        super(_ThumbThread, self).__init__(os_priority=_Worker.OS_PRIORITY_LOWEST,
                                           qt_priority=QtCore.QThread.Priority.LowPriority)
        self._done = 0

    def submit_plan(self, plan, size):
        """给出「要缩略图的完整清单」。

        Args:
            plan: ``[(index, path), ...]``。
            size: 缩略图的最长边（像素）。
        """
        with QtCore.QMutexLocker(self._mutex):
            self._jobs.clear()
            for index, path in plan:
                self._jobs.append((int(index), str(path), int(size)))
        self._cond.wakeAll()

    def run(self):
        """线程体：不断取缩略图任务，做好一张发一张。"""
        self.lower_os_priority()
        while True:
            job = self.take_job()
            if job is None:
                break
            index, path, size = job
            try:
                image = ImageBrowser.read_image(path, size)
            except Exception:
                continue
            if self.is_stopped():
                break
            if image is not None and not image.isNull():
                self.sig_thumb.emit(index, path, image)
            self._done += 1
            if self._done % self.YIELD_EVERY == 0:
                self.msleep(1)  # 让一下：相册缩略图不着急


class _LoadThread(_Worker):
    """在后台按「显示尺寸」解码大图（**纯计算，绝不碰界面**）。

    计划同样是「替换式」的：控件每次只需要「当前这张 + 邻近几张」，
    给一批新的就等于放弃了旧的一批 —— 播放时不会积压出一长串过期解码。

    Attributes:
        sig_loaded: ``(index, path, image)`` —— 某一张解好了。
    """

    sig_loaded = QtCore.pyqtSignal(int, str, QtGui.QImage)

    def __init__(self):
        super(_LoadThread, self).__init__(
            os_priority=_Worker.OS_PRIORITY_BELOW_NORMAL,
            qt_priority=QtCore.QThread.Priority.LowPriority)

    def submit_plan(self, plan):
        """给出「要解码的清单」：``[(index, path, max_side), ...]``。"""
        with QtCore.QMutexLocker(self._mutex):
            self._jobs.clear()
            for index, path, max_side in plan:
                self._jobs.append((int(index), str(path), int(max_side)))
        self._cond.wakeAll()

    def run(self):
        """线程体：不断取解码任务，解好一张发一张。"""
        self.lower_os_priority()
        while True:
            job = self.take_job()
            if job is None:
                break
            index, path, max_side = job
            try:
                image = ImageBrowser.read_image(path, max_side)
            except Exception:
                continue
            if self.is_stopped():
                break
            if image is not None and not image.isNull():
                self.sig_loaded.emit(index, path, image)


class _Button(QtWidgets.QPushButton):
    """可压缩的按钮：``minimumSizeHint()`` 只报一个很小的宽度。

    为什么要这么做：``QPushButton`` 默认把 ``minimumSizeHint()`` 报成
    “文字 + 图标 + 内边距”（约 80 px），而布局绝不会把控件压到它之下 ——
    于是一排按钮就把整个控件的最小宽度锁死（实测本控件曾是 662 px）。
    锁死以后用户根本拖不窄，“窄窗口就收起相册”这类响应式逻辑永远触发不了。

    ⚠️ ``setMinimumWidth(0)`` **做不到**这件事（实测只能从 662 降到 622）：
    布局看的是 ``minimumSizeHint()``，不是 ``minimumWidth()``。必须重写前者。
    按钮上的文字在窄窗口下会被 Qt 自己用省略号处理（QPushButton 内置）。
    """

    #: 允许被压到的最小宽度（像素）。再小就只剩一个图标，没意义了。
    MIN_COMPRESSED = 34

    def minimumSizeHint(self):
        """只要求一个很小的宽度（高度还按正常来）。"""
        hint = super(_Button, self).minimumSizeHint()
        return QtCore.QSize(self.MIN_COMPRESSED, hint.height())


class _Canvas(QtWidgets.QWidget):
    """右侧主显示区：把一张 ``QImage`` 按比例缩放、居中画出来。

    刻意只是一个「画图的板子」——不含翻页 / 缩放 / 业务逻辑。用 ``paintEvent``
    而不是 ``QLabel`` + ``setPixmap``：窗口每变一次尺寸就重建一张缩放后的
    ``QPixmap`` 是浪费，而 ``drawPixmap`` 可以在绘制时直接缩放。
    """

    def __init__(self, parent=None):
        super(_Canvas, self).__init__(parent)
        self._pixmap = None
        self._message = ''
        self.setMinimumSize(260, 200)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Expanding)

    def set_image(self, image):
        """显示一张图（``None`` 等于清空）。"""
        if image is None or image.isNull():
            self._pixmap = None
        else:
            # ⚠️ QPixmap 只能在 GUI 线程构造 —— 本方法只由主线程调用
            self._pixmap = QtGui.QPixmap.fromImage(image)
        self._message = ''
        self.update()

    def set_message(self, text):
        """显示一行提示文字（不显示图片）。"""
        self._pixmap = None
        self._message = str(text)
        self.update()

    def has_image(self):
        """当前是否正在显示图片。"""
        return self._pixmap is not None and not self._pixmap.isNull()

    def paintEvent(self, event):
        """把图按比例缩放居中画出来；没有图时画提示文字。"""
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(),
                         self.palette().color(QtGui.QPalette.ColorRole.Base))
        if self.has_image():
            painter.setRenderHint(
                QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.drawPixmap(self._fit_rect(self._pixmap.size()), self._pixmap)
        elif self._message:
            painter.setPen(
                self.palette().color(QtGui.QPalette.ColorRole.PlaceholderText))
            painter.drawText(self.rect(),
                             QtCore.Qt.AlignmentFlag.AlignCenter, self._message)
        painter.end()

    def _fit_rect(self, size):
        """算出「等比缩放并居中」后，图片该占的那个矩形。"""
        w, h = int(size.width()), int(size.height())
        if w <= 0 or h <= 0:
            return QtCore.QRect()
        scale = min(self.width() / float(w), self.height() / float(h))
        tw = max(1, int(w * scale))
        th = max(1, int(h * scale))
        return QtCore.QRect((self.width() - tw) // 2, (self.height() - th) // 2,
                            tw, th)


class ImageBrowser(QtWidgets.QWidget):
    """浏览 / 预览 / 动画播放工作路径下的图片（详见模块 docstring）。

    ⚠️ **故意不实现 ``refresh()``**：切标签页不会重新扫描目录；刷新只由界面上的
    「刷新」按钮触发。想从代码里刷新就调 :meth:`rescan`。
    """

    #: 目录递归深度（「工作路径」算第 0 层，此值表示再往下几层）
    SCAN_MAX_DEPTH = 2

    #: 单次扫描最多收多少张（防御：工作路径里有几万张图时不至于把列表塞爆）
    MAX_FILES = 2000

    #: 生成缩略图时的最长边（像素）
    THUMB_SIZE = 128

    #: 相册里一格图标的边长（像素）
    THUMB_ICON = 112

    #: 主显示区解码的最长边上限（像素）
    LOAD_MAX_SIDE = 2400

    #: 解码目标尺寸的量化步长：按此取整可避免拖窗口时反复重解码
    LOAD_STEP = 256

    #: 主显示区最多缓存几张解好的图
    CACHE_LIMIT = 16

    #: 播放时向后 / 向前预取几张
    PREFETCH_AHEAD = 3
    PREFETCH_BACK = 1

    #: 默认 / 允许的播放帧率
    DEFAULT_FPS = 2.0
    MIN_FPS = 0.2
    MAX_FPS = 30.0

    #: 支持解码的扩展名（惰性缓存；由 Qt 的图片插件能力反推）
    _IMAGE_EXTS = None

    #: 文本适配时的兜底宽度（像素）：标签还没被布局摆好（``width()`` 为 0）时用它。
    #: ⚠️ 只决定**截断到多少像素**，不决定控件占多宽（那是尺寸策略的事）。
    ELIDE_MIN_WIDTH = 60

    #: 左侧相册的**下限**宽度（像素）：约一张缩略图 + 滚动条，是「还能看出是相册」的底线。
    #: ⚠️ 不给下限的话，窄窗口下 QSplitter 会把空间全让给右侧，把相册压成一条缝
    #: （实测 520 px 宽的窗口把左栏压成 70 px）。
    MIN_LIST_WIDTH = 120

    #: 左侧相册的**默认**宽度（像素）：初次显示时给这么多，之后由用户拖动决定。
    DEFAULT_LIST_WIDTH = 340

    #: 响应式断点（整体宽度，像素）。见 :meth:`_update_responsive`。
    #:
    #: ⚠️ 断点必须落在“控件能真正到达的宽度区间”内。本控件的最小宽由
    #: 控制条与分隔条决定，实测为 **438 px**（拖到更窄会被这个下限卡住）。
    #: 所以断点若小于 438 就是**死代码**（永远触发不了）—— 初版写的 420 就犯了这个错。
    #:
    #: - 低于 ``TINY_WIDTH``：**收起左侧相册**（它已经只剩不到一张缩略图的宽度，
    #:   留着也看不清），把宽度全给大图。
    #: - 低于 ``NARROW_WIDTH``：让出控制条上的次要文字（「帧率」两字与「循环」）。
    TINY_WIDTH = 560
    NARROW_WIDTH = 620

    #: 从「Qt 能解码的格式」里剔掉这些：它们虽然能被 QImageReader 读出来，
    #: 但不是「一张图」—— 例如 pdf 是多页文档，塞进单图查看器只会显示第 1 页。
    #: 想把它们收进来，把这个集合清空即可。
    SKIP_EXTS = {'pdf'}

    def __init__(self, parent=None, folder=None):
        """初始化并**开始扫描** ``folder``。

        Args:
            parent: Qt 父对象。
            folder: 要浏览的目录。**None（默认）表示「跟随工作路径」** ——
                每次扫描都现取 ``os.getcwd()``，所以用户改了工作路径再点刷新，
                看到的就是新目录。给了具体路径则**固定**在该目录（见 :meth:`set_folder`）。
        """
        super(ImageBrowser, self).__init__(parent)
        self.context_actions = []

        # ── 目录：“跟随工作路径”还是“固定目录” ──
        # ⚠️ 不能把目录冻结成一个字符串：本控件的语义是“看**当前**
        #    工作路径下的图”，用户改了工作路径（菜单“设置 → 工作路径”）
        #    再点刷新，就该看到新目录里的图 —— 以前冻结在构造那一刻，
        #    切了工作路径再刷新还是旧目录，实测确认过这个行为。
        #    但也要保留“显式指定一个固定目录”的能力（set_folder），
        #    否则装配层就无法把它定到某个特定目录上。
        self._folder_fixed = None    # 仅 'fixed' 模式有效
        self._scan_target = None     # 本次扫描实际用的绝对路径
        if isinstance(folder, str) and folder:
            self._folder_mode = 'fixed'
            self._folder_fixed = os.path.abspath(folder)
        else:
            self._folder_mode = 'cwd'
        self._paths = []            # 当前清单（扫描结果）
        self._index = -1            # 当前显示第几张
        self._shown = -1            # 画布上**实际**显示的是第几张（落后于 _index 即「解码中」）
        self._cache = {}            # index -> QImage（OrderedDict 语义，按距离淘汰）
        self._load_plan = []        # 已投给解码线程、还没回来的 index
        self._cache_side = 0        # 缓存是按哪个目标尺寸解的
        self._cap_hit = False       # 上次扫描是否撞到 MAX_FILES
        self._playing = False
        self._paused_by_hide = False  # 「因为标签被隐藏而暂停」——决定「继续播放」是否出现
        self._syncing = False       # 程序化改列表选中项时，抑制「选中 = 人手选」的处理
        self._placeholder = None

        self.image_extensions()     # 预热扩展名表（别留给后台线程去初始化）

        self._build_ui()

        # ⚠️ 定时器设 parent 是**安全**的（Qt 对象随控件销毁没问题）；
        #    与「后台线程一律不设 parent」那条规矩正好相反，别写混。
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._on_tick)

        self._scan_thread = _ScanThread()
        self._scan_thread.sig_found.connect(self._on_scan_found)
        self._scan_thread.sig_failed.connect(self._on_scan_failed)
        self._scan_thread.start_quietly()

        self._thumb_thread = _ThumbThread()
        self._thumb_thread.sig_thumb.connect(self._on_thumb)
        self._thumb_thread.start_quietly()

        self._load_thread = _LoadThread()
        self._load_thread.sig_loaded.connect(self._on_loaded)
        self._load_thread.start_quietly()

        self._apply_fps()
        self._sync_controls()

        # 首次扫描推迟到事件循环里做：让装配层先把标签页挂好。
        # ⚠️ 用「带 parent 的一次性 QTimer」而不是 QTimer.singleShot(0, 绑定方法)：
        #    后者没有接收者对象，控件若在计时器到点前就被销毁，槽仍会被调到
        #    （碰已删除的成员即 RuntimeError）；带 parent 的计时器会随控件一起销毁，
        #    连接随之消失。
        self._first_scan = QtCore.QTimer(self)
        self._first_scan.setSingleShot(True)
        self._first_scan.timeout.connect(self.rescan)
        self._first_scan.start(0)

    # ================================================================== 图片格式
    @classmethod
    def image_extensions(cls):
        """支持解码的扩展名集合（小写、不含点）。

        以 Qt 编译进来的图片插件为准（``QImageReader.supportedImageFormats()``），
        再并上一批常见格式兜底 —— 于是「支持哪些格式」不用我们维护一张会过期的表。
        """
        if cls._IMAGE_EXTS is None:
            exts = set()
            try:
                for fmt in QtGui.QImageReader.supportedImageFormats():
                    exts.add(bytes(fmt).decode('ascii', 'ignore').strip().lower())
            except Exception:
                pass
            exts |= {'png', 'jpg', 'jpeg', 'bmp', 'gif', 'tif', 'tiff', 'webp',
                     'ico', 'pnm', 'ppm', 'pgm', 'pbm', 'xpm', 'xbm', 'svg'}
            exts.discard('')
            exts -= set(cls.SKIP_EXTS)
            cls._IMAGE_EXTS = exts
        return cls._IMAGE_EXTS

    @classmethod
    def is_image(cls, filename):
        """``filename`` 的扩展名是否在支持列表里。"""
        ext = os.path.splitext(filename)[1][1:].lower()
        return bool(ext) and ext in cls.image_extensions()

    @staticmethod
    def is_visible_dir(name):
        """这个子目录要不要往下走（跳过隐藏目录与 ``__pycache__``）。"""
        return not name.startswith('.') and name != '__pycache__'

    @staticmethod
    def read_image(path, max_side):
        """按需缩放解码一张图（**纯计算，不碰界面**，可在任意线程调用）。

        先读文件头拿到原始尺寸，只有原图真的超过 ``max_side`` 时才让解码器
        **直接按比例缩小解码** —— 既省内存也快得多（一张 8000×8000 的图若全解，
        光内存就 250 MB，播放立刻卡死）。

        Args:
            path: 图片路径。
            max_side: 目标最长边（像素）；非正数表示不缩放。

        Returns:
            QtGui.QImage（可能为 null，调用方需自行判空）。
        """
        reader = QtGui.QImageReader(str(path))
        reader.setAutoTransform(True)  # 尊重 EXIF 方向
        target = int(max_side)
        if target > 0:
            size = reader.size()       # 文件头里的原始尺寸
            if size.isValid() and size.width() > 0 and size.height() > 0:
                if size.width() > target or size.height() > target:
                    box = QtCore.QSize(target, target)
                    reader.setScaledSize(size.scaled(
                        box, QtCore.Qt.AspectRatioMode.KeepAspectRatio))
        return reader.read()

    # ================================================================== 界面
    def _build_ui(self):
        """搭界面（左侧相册 + 右侧主显示 + 控制条 + 进度条 + 信息行）。"""
        self.folder_label = QtWidgets.QLabel('')
        self.folder_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.folder_label.setWordWrap(False)
        # ⚠️ 这一行是必需的，不是装饰：QLabel 关掉换行后，它的 minimumSizeHint()
        #    就等于**整段文字的宽度**。长路径（很常见）于是把左侧栏顶到上千像素，
        #    右侧主显示被挤到几乎看不见 —— 实测 1512 px 的路径把 1000+ 宽的窗口
        #    压成「左 1512 / 右 550」，连 splitter.setSizes([340, 900]) 都拦不住
        #    （splitter 不会把子控件压到它的 minimumSizeHint 之下）。
        #    改用 Ignored 水平策略 = 「我的宽度建议请忽略，随布局给多少算多少」，
        #    再由 _fit() 按**实际**宽度截断文字。两者缺一不可：
        #    只改策略不截断，文字会被硬裁（看不到右半截）；只截断不改策略，
        #    则 label.width() 本身就被文字撑大，_fit 拿到的是个假宽度（循环依赖）。
        self.folder_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Preferred)
        self.folder_label.setMinimumWidth(0)

        self.list = QtWidgets.QListWidget()
        self.list.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
        self.list.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.list.setMovement(QtWidgets.QListView.Movement.Static)
        self.list.setIconSize(QtCore.QSize(self.THUMB_ICON, self.THUMB_ICON))
        self.list.setGridSize(QtCore.QSize(self.THUMB_ICON + 26, self.THUMB_ICON + 42))
        self.list.setUniformItemSizes(True)
        self.list.setWordWrap(True)
        self.list.setTextElideMode(QtCore.Qt.TextElideMode.ElideMiddle)
        self.list.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.NoDragDrop)
        # 只读展示：关掉就地编辑（本项目在 WSL 下踩过「编辑器开着再双击」段错误）
        self.list.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.list.currentRowChanged.connect(self._on_row_changed)

        left = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.folder_label)
        left_layout.addWidget(self.list, 1)

        self.canvas = _Canvas()
        self.canvas.set_message('正在扫描目录…')

        self.prev_button = self._make_button('上一张', 'SP_MediaSkipBackward')
        self.play_button = self._make_button('播放', 'SP_MediaPlay')
        self.next_button = self._make_button('下一张', 'SP_MediaSkipForward')
        self.resume_button = self._make_button('继续播放', 'SP_MediaPlay')
        self.resume_button.setVisible(False)
        self.refresh_button = self._make_button('刷新', 'SP_BrowserReload')

        self.fps_box = QtWidgets.QDoubleSpinBox()
        self.fps_box.setRange(self.MIN_FPS, self.MAX_FPS)
        self.fps_box.setSingleStep(0.5)
        self.fps_box.setDecimals(1)
        self.fps_box.setValue(self.DEFAULT_FPS)
        self.fps_box.setSuffix(' fps')
        self.fps_box.setToolTip('播放帧率')
        self.fps_box.setMaximumWidth(110)
        # 宽度不够时允许被压缩（否则它会把控件的最小宽度锁死）
        self.fps_box.setMinimumWidth(70)

        self.loop_box = QtWidgets.QCheckBox('循环')
        self.loop_box.setToolTip('播到最后一张时是否回到第一张继续')

        self.progress = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.progress.setRange(0, 0)
        self.progress.setToolTip('拖动可跳到任意一张（播放中拖动不会停止播放）')

        self.counter_label = QtWidgets.QLabel('0 / 0')
        self.counter_label.setMinimumWidth(60)
        self.counter_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        # 计数只是「第几张 / 共几张」，窄窗口下允许它被压缩（不然它和进度条抢空间）
        self.counter_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Preferred)

        self.info_label = QtWidgets.QLabel('')
        self.info_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.info_label.setWordWrap(False)
        # ⚠️ 与 folder_label 同一个坑（理由见 _build_ui 里那段注释）：普通 QLabel 的
        #    minimumSizeHint() 等于整段文字宽度，而本行会带上**相对路径** ——
        #    实测一个长文件名的图把它顶到 2760 px，右侧被撑到 2760、左侧相册被压成
        #    70 px（整个界面全毁），连 splitter.setSizes([340, 900]) 都拦不住。
        #    同样用 Ignored + _fit() 按实际宽度截断。
        self.info_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Preferred)
        self.info_label.setMinimumWidth(0)

        bar = QtWidgets.QHBoxLayout()
        bar.setContentsMargins(0, 0, 0, 0)
        bar.setSpacing(4)
        bar.addWidget(self.prev_button)
        bar.addWidget(self.play_button)
        bar.addWidget(self.next_button)
        # ⚠️ 「帧率」这两个字是**可选**的（下拉框自己有 ' fps' 后缀、也有 tooltip），
        #    窗口窄时先把它让出去 —— 见 _update_responsive。
        self.fps_caption = QtWidgets.QLabel('帧率')
        bar.addWidget(self.fps_caption)
        bar.addWidget(self.fps_box)
        bar.addWidget(self.loop_box)
        bar.addWidget(self.resume_button)
        bar.addStretch(1)
        bar.addWidget(self.refresh_button)

        bar2 = QtWidgets.QHBoxLayout()
        bar2.setContentsMargins(0, 0, 0, 0)
        bar2.setSpacing(4)
        bar2.addWidget(self.progress, 1)
        bar2.addWidget(self.counter_label)

        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)
        right_layout.addWidget(self.canvas, 1)
        right_layout.addLayout(bar)
        right_layout.addLayout(bar2)
        right_layout.addWidget(self.info_label)

        #: 响应式布局要按需显隐的部件（见 _update_responsive）
        self._left = left
        self._right = right

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        # ⚠️ **不能**让子控件可拖成 0 宽：那样用户一不小心就把相册拖没了。
        #    收起相册改由 _update_responsive 用 setVisible 做（窄窗口下自动）。
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        # ⚠️ 左侧相册给一个**下限**：不给的话，窗口一窄，QSplitter 会把空间优先
        #    满足右侧（按钮条的 minimumSizeHint 之和比相册大得多），实测 520 px 的
        #    窗口把左栏压成 **70 px** —— 缩略图挤成一条缝，等于废掉。
        #    120 px 约等于一张 112 px 缩略图 + 滚动条，是「还能看出是相册」的底线。
        left.setMinimumWidth(self.MIN_LIST_WIDTH)
        splitter.setSizes([self.DEFAULT_LIST_WIDTH, 900])
        self.splitter = splitter

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(splitter, 1)

        # 用户是否手动收起过相册（收起过就尊重他的选择，见 _update_responsive）
        self._left_user_hidden = False
        splitter.splitterMoved.connect(self._on_splitter_moved)

        self.prev_button.clicked.connect(lambda: self.step(-1))
        self.play_button.clicked.connect(self.toggle_play)
        self.next_button.clicked.connect(lambda: self.step(1))
        self.resume_button.clicked.connect(self.play)
        self.refresh_button.clicked.connect(self.rescan)
        self.fps_box.valueChanged.connect(self._on_fps_changed)
        self.progress.valueChanged.connect(self._on_progress)

    def _on_splitter_moved(self, pos, index):
        """用户拖过分隔条：记住「左栏现在是不是被收起了」."""
        if not hasattr(self, '_left'):
            return
        sizes = self.splitter.sizes()
        self._left_user_hidden = (not sizes) or sizes[0] <= 0

    def _update_responsive(self):
        """按当前宽度决定「显示哪些东西」（响应式降级）。

        原则：**宁可少显示一个次要部件，也不把所有部件都挤成看不清**。
        分档看的是**整体宽度**，不是给每个控件各自设最小值 ——
        后者会互相打架，最后谁也得不到够用的宽度（QSplitter 满足不了所有
        minimumSizeHint 时就按比例硬压，实测把左栏压成 70 px）。

        ====================  ==============================================
        可用宽度                 显示
        ====================  ==============================================
        >= ``NARROW_WIDTH``    完整：相册 + 大图 + 完整控制条 + 信息行
        >= ``TINY_WIDTH``      同上，但「帧率」两字与「循环」让位
        <  ``TINY_WIDTH``      **收起左侧相册**，把宽度全给大图
        ====================  ==============================================

        ⚠️ 收起相册时**不动** ``list`` 的任何状态（当前选中、缩略图缓存都在），
        所以窗口再拉宽时展开即可，不会重扫、也不会跳回第一张。
        """
        if not hasattr(self, '_left'):
            return
        width = self.width()
        self._left.setVisible(width >= self.TINY_WIDTH and not self._left_user_hidden)
        self.fps_caption.setVisible(width >= self.TINY_WIDTH)
        self.loop_box.setVisible(width >= self.TINY_WIDTH)
        # 窄窗口下把 fps 框收短，省出的宽度给按钮。
        # ⚠️ 不能小于它自己的 minimumSizeHint（实测 84 px，含 ' fps' 后缀与上下箭头）——
        #    设成 78 会把文字裁成「2.0 fp:」（少半截字符）。要么给足，要么干脆收起它。
        self.fps_box.setMaximumWidth(110 if width >= self.NARROW_WIDTH else 88)

    def _make_button(self, text, standard_icon):
        """做一个带标准图标的按钮（图标取自当前主题，不写死颜色）。

        ⚠️ 用 :class:`_Button`（可压缩）而不是裸的 ``QPushButton``：后者会把自己锁在
        约 80 px，四个按钮就是 320 px，成为“整个控件最小宽度”的主要来源
        （实测曾是 662 px）—— 于是用户拖不窄，响应式断点永远触发不了。
        """
        button = _Button(text)
        button.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Fixed)
        try:
            pixmap = getattr(QtWidgets.QStyle.StandardPixmap, standard_icon)
            button.setIcon(self.style().standardIcon(pixmap))
        except Exception:
            pass
        return button

    # ================================================================== 公开接口
    def set_folder(self, folder, *, rescan=True):
        """把本控件**固定**在某个目录上（不再跟随工作路径）。

        Args:
            folder: 新目录；非法值直接忽略（不做「抛错」——它多半是被装配层调用的）。
            rescan: 是否立刻重新扫描。

        ⚠️ 调过它之后本控件就不再跟随工作路径了（切工作路径 + 刷新也不会换）；
        想回到“跟随工作路径”，用 :meth:`follow_cwd`。
        """
        if not isinstance(folder, str) or not folder:
            return
        self._folder_mode = 'fixed'
        self._folder_fixed = os.path.abspath(folder)
        if rescan:
            self.rescan()

    def follow_cwd(self, *, rescan=True):
        """恢复“跟随**工作路径**”的行为（每次扫描都现取 ``os.getcwd()``）。

        Args:
            rescan: 是否立刻重新扫描。
        """
        self._folder_mode = 'cwd'
        self._folder_fixed = None
        if rescan:
            self.rescan()

    def _resolve_folder(self):
        """现算出“本次该扫哪儿”（**每次扫描都要重新算**）。

        跟随模式下取 ``os.getcwd()``；工作路径不存在（目录被删）时退回上一个可用值，
        而不是把控件弄成无效状态。

        Returns:
            str: 绝对路径。
        """
        if self._folder_mode == 'fixed' and self._folder_fixed:
            return self._folder_fixed
        try:
            return os.path.abspath(os.getcwd())
        except OSError:
            # 工作目录已被删掉（Linux 上 getcwd 会抛）：用上次的目标顶一下。
            return self._scan_target or os.path.abspath(os.path.expanduser('~'))

    def get_folder(self):
        """当前浏览的目录（跟随模式下 = 当前工作路径）。"""
        return self._resolve_folder()

    def _display_folder(self):
        """界面上要显示的目录（标题栏、相对路径都用它）。

        ⚠️ 用 ``_scan_target``（**当前清单是哪个目录扫出来的**），而不是现取工作路径：
        两者在“刚切完路径、新扫描还没回来”那一瞬是**不一致**的 ——
        那时列表里还是旧图，标题若先跳到新路径，就会出现“标题说 B、
        列表全是 A 的图”这种自相矛盾。新结果一到（``_on_scan_found``）就会同步。

        尚未扫描过（``_scan_target`` 还是 None）时回退到现取值。
        """
        return self._scan_target or self._resolve_folder()

    def rescan(self):
        """重新扫描目录（只由「刷新」按钮与首次显示触发，**不是** ``refresh()`` 钩子）。

        ⚠️ **每次都现取目录**（见 :meth:`_resolve_folder`）：跟随模式下就是
        当前 ``os.getcwd()`` —— 所以用户切了工作路径再点刷新，看到的是**新**目录。
        以前冻结在构造那一刻，切了路径刷新还是旧图（实测确认过）。
        """
        if self._scan_thread is None:
            return  # 已经被 cleanup_before_tab_close() 收工了
        self._scan_target = self._resolve_folder()
        self._thumb_thread.clear_jobs()
        self._thumb_thread.submit_plan([], self.THUMB_SIZE)
        self._load_thread.submit_plan([])
        self._load_plan = []
        self._cache.clear()
        self._paths = []
        self._index = -1
        self._shown = -1
        self._cap_hit = False
        self._syncing = True
        try:
            self.list.clear()
        finally:
            self._syncing = False
        self.canvas.set_message('正在扫描目录…\n{0}'.format(self._scan_target))
        self._sync_controls()
        self._scan_thread.request_scan(self._scan_target)

    def play(self):
        """开始（或继续）播放。"""
        if len(self._paths) == 0:
            return
        if self._index < 0:
            self._set_index(0, stop_playback=False)
        self._playing = True
        self._paused_by_hide = False
        self._apply_fps()
        self._sync_controls()

    def pause(self):
        """暂停播放（不会点亮「继续播放」按钮）。"""
        self._pause(by_hide=False)

    def toggle_play(self):
        """播放 / 暂停。"""
        if self._playing:
            self._pause(by_hide=False)
        else:
            self.play()

    def step(self, delta):
        """上一张 / 下一张（到头就停住，不循环 —— 循环只发生在播放时）。

        Args:
            delta: +1 下一张，-1 上一张。
        """
        count = len(self._paths)
        if count == 0:
            return
        target = self._index + int(delta)
        if target < 0 or target >= count:
            return
        self._set_index(target, stop_playback=True)

    def is_playing(self):
        """当前是否在播放。"""
        return self._playing

    # ================================================================== 列表 / 索引
    def _on_row_changed(self, row):
        """相册里选中项变了（**人手点**或键盘移动）。"""
        if self._syncing or row < 0:
            return
        self._set_index(row, stop_playback=True)

    def _set_index(self, index, *, stop_playback):
        """切到第 ``index`` 张（唯一的入口：列表、翻页、播放、进度条都走这里）。

        Args:
            index: 目标序号（会被夹到合法范围）。
            stop_playback: 人手切换时 True —— 需求「选中哪张就停止播放」；
                播放自身推进时 False。
        """
        count = len(self._paths)
        if count == 0:
            self._index = -1
            self._sync_controls()
            return
        index = max(0, min(int(index), count - 1))
        if stop_playback and self._playing:
            self._pause(by_hide=False)
        self._index = index
        self._sync_list()
        self._show_index(index)
        self._plan_loads()
        self._sync_controls()

    def _sync_list(self):
        """让相册的选中项跟上 ``self._index``（不触发「人手切换」的处理）。"""
        if not (0 <= self._index < self.list.count()):
            return
        item = self.list.item(self._index)
        if item is None or self.list.currentItem() is item:
            return
        self._syncing = True
        try:
            self.list.setCurrentItem(item)
            self.list.scrollToItem(
                item, QtWidgets.QAbstractItemView.ScrollHint.EnsureVisible)
        finally:
            self._syncing = False

    def _show_index(self, index):
        """把第 ``index`` 张贴到画布上（命中缓存就立即贴，否则交给后台解码）。"""
        image = self._cache.get(index)
        if image is not None:
            self._touch_cache(index)
            self.canvas.set_image(image)
            self._shown = index
            return
        # 不在缓存里：保持当前画面（播放时比闪一下占位图舒服得多），
        # 并立刻把这一张插到解码队列最前面（见 _plan_loads 的顺序）
        self._plan_loads(urgent=index)

    def _plan_loads(self, urgent=None):
        """把「当前 + 邻近若干张」交给解码线程（替换式计划，可反复调用）。"""
        if not self._paths or self._load_thread is None:
            return
        order = []
        if urgent is not None:
            order.append(urgent)
        order.append(self._index)
        for k in range(1, self.PREFETCH_AHEAD + 1):
            order.append(self._index + k)
        for k in range(1, self.PREFETCH_BACK + 1):
            order.append(self._index - k)

        side = self._target_side()
        plan, seen = [], set()
        for i in order:
            if i in seen or not (0 <= i < len(self._paths)):
                continue
            seen.add(i)
            if self._cache.get(i) is not None:
                continue
            plan.append((i, self._paths[i], side))
        self._load_plan = [i for i, _, _ in plan]
        self._load_thread.submit_plan(plan)

    def _target_side(self):
        """当前解码目标边长：按画布尺寸量化到 ``LOAD_STEP`` 的整数倍。

        量化是为了「拖一下窗口就把缓存全作废重解」这件事不要发生。
        """
        side = max(self.canvas.width(), self.canvas.height(), 512)
        stepped = int(side * 1.2 / self.LOAD_STEP + 1) * self.LOAD_STEP
        return max(self.LOAD_STEP, min(self.LOAD_MAX_SIDE, stepped))

    def _touch_cache(self, index):
        """把 ``index`` 挪到缓存末尾（LRU），并把离当前太远的挤出去。"""
        image = self._cache.pop(index)
        self._cache[index] = image
        while len(self._cache) > self.CACHE_LIMIT:
            away = max(self._cache, key=lambda k: abs(k - self._index))
            del self._cache[away]

    # ================================================================== 线程回调
    def _on_scan_found(self, folder, paths):
        """扫描回来了（主线程调用）。"""
        if self._scan_thread is None or self._thumb_thread is None:
            # ⚠️ 标签页已经关掉了（cleanup_before_tab_close 把三个线程引用置 None）。
            #    扫描是异步的，关标签时「结果已经在路上」是常态 —— 真踩过：
            #    AttributeError: 'NoneType' object has no attribute 'submit_plan'。
            return
        if os.path.abspath(folder) != self._scan_target:
            # ⚠️ 比的是 **_​scan_target**（发起扫描那一刻定下的目标），不是“当前工作路径”：
            #    扫描是异步的，若用“当前路径”去比，用户在扫描途中切了目录，
            #    这份本来有效的结果会被误丢。
            return  # 目录已经被换掉，结果作废
        self._paths = list(paths)
        self._cap_hit = len(self._paths) >= self.MAX_FILES
        self._cache.clear()
        self._load_plan = []
        self._cache_side = self._target_side()
        self._fill_list()
        self._thumb_thread.submit_plan(
            [(i, path) for i, path in enumerate(self._paths)], self.THUMB_SIZE)
        if self._paths:
            self._set_index(0, stop_playback=True)
        else:
            self._index = -1
            self._shown = -1
            self.canvas.set_message(
                '没有找到图片\n{0}\n\n支持: {1}'.format(
                    self._scan_target,
                    ' / '.join(sorted(self.image_extensions()))))
        self._sync_controls()

    def _on_scan_failed(self, folder, message):
        """扫描失败（主线程调用）。"""
        if os.path.abspath(folder) != self._scan_target:
            return
        self.canvas.set_message('扫描失败: {0}\n{1}'.format(message, self._scan_target))
        self._sync_controls()

    def _on_thumb(self, index, path, image):
        """某张缩略图好了（主线程调用）。"""
        if self._thumb_thread is None:
            return  # 标签页已关（见 _on_scan_found 的说明）
        if not (0 <= index < self.list.count()):
            return
        item = self.list.item(index)
        if item is None or item.data(QtCore.Qt.ItemDataRole.UserRole) != path:
            return  # 列表已经被刷新过，这个结果过期了
        item.setIcon(QtGui.QIcon(QtGui.QPixmap.fromImage(image)))

    def _on_loaded(self, index, path, image):
        """某张大图解好了（主线程调用）。"""
        if self._load_thread is None:
            return  # 标签页已关（见 _on_scan_found 的说明）
        if not (0 <= index < len(self._paths)) or self._paths[index] != path:
            return  # 结果过期（期间刷新过或换了目录）
        if index in self._load_plan:
            self._load_plan.remove(index)
        self._cache[index] = image
        self._touch_cache(index)
        if index == self._index:
            self.canvas.set_image(image)
            self._shown = index
            self._sync_controls()

    # ================================================================== 播放
    def _on_fps_changed(self, value):
        """帧率被改：立刻按新帧率走（正在播放时立即生效）。"""
        self._apply_fps()

    def _apply_fps(self):
        """把帧率落到定时器上；只在播放中才真的起表。"""
        fps = max(self.MIN_FPS, float(self.fps_box.value()))
        self._timer.setInterval(max(30, int(round(1000.0 / fps))))
        if self._playing:
            self._timer.start()

    def _on_tick(self):
        """播放定时器到点：推进一张。"""
        count = len(self._paths)
        if count == 0:
            self._pause(by_hide=False)
            return
        target = self._index + 1
        if target >= count:
            if self.loop_box.isChecked():
                target = 0
            else:
                self._pause(by_hide=False)
                return
        self._set_index(target, stop_playback=False)

    def _pause(self, *, by_hide):
        """停止播放。

        Args:
            by_hide: True 表示「因为标签被隐藏而暂停」——这时切回来会亮出
                「继续播放」按钮；False（人手暂停）不会。
        """
        self._playing = False
        self._timer.stop()
        self._paused_by_hide = bool(by_hide)
        self._sync_controls()

    def _on_progress(self, value):
        """进度条被拖动：跳过去，但**不打断播放**（像播放器拖进度那样）。"""
        if self._syncing or not self._paths:
            return
        index = max(0, min(int(value), len(self._paths) - 1))
        if index != self._index:
            self._set_index(index, stop_playback=False)

    # ================================================================== 状态同步
    def _sync_controls(self):
        """把「状态」映射到界面（按钮文字 / 进度条 / 计数 / 信息行）。"""
        count = len(self._paths)
        # ⚠️ 张数走 ``reserve`` 交给 _fit —— 它会**先**给后缀留位、再截路径。
        #    不能自己再拼一遍（``_fit(...) + suffix`` 会拼两遍，
        #    _fit 的返回值里已经含 reserve）；也不能“先截路径、再拼后缀”——
        #    截断后的路径会正好占满整行，后缀被切掉（实测长路径下「(4 张)」
        #    只露出半个括号）。张数是这一行里最该看清的信息，
        #    宁可路径少显示几个字符。
        suffix = '  ({0} 张{1})'.format(
            count, '，已达上限' if self._cap_hit else '')
        self.folder_label.setText(
            self._fit(self.folder_label, self._display_folder(), reserve=suffix))
        self.folder_label.setToolTip(self._display_folder())

        self.play_button.setText('暂停' if self._playing else '播放')
        self.resume_button.setVisible(
            self._paused_by_hide and not self._playing and count > 0)

        self._syncing = True
        try:
            self.progress.setRange(0, max(0, count - 1))
            self.progress.setValue(max(0, self._index))
        finally:
            self._syncing = False
        # 计数也走同一套适配（极窄窗口下连「i / n」也会放不下）。
        # ⚠️ reserve 留空：计数本身就是最该看清的，被截了就没意义了。
        self.counter_label.setText(self._fit(
            self.counter_label,
            '{0} / {1}'.format(self._index + 1 if count else 0, count)))

        # ⚠️ 把标签的**实际**宽度传进去让它截断：只看 minimumSizeHint 不够，
        #    这一行会带上子目录名，长起来照样把右侧撑开（见 info_label 的尺寸策略）。
        self.info_label.setText(
            self._describe_current(width=self.info_label.width() - 8))

    # ================================================================== 文字适配
    #
    # 本控件有三处「文字可能比可用宽度长」的地方，且都必须**在任何窗口尺寸下都不溢出**：
    #   folder_label（左栏顶：路径 + 张数）、info_label（右下：文件名 · 尺寸 · 体积 · 子目录）、
    #   相册条目（list 里的文件名，由 QListWidget 自己省略）。
    #
    # 它们共用同一套办法，核心是**两条硬规则**：
    #
    #   ① 标签的水平尺寸策略必须是 ``Ignored`` —— 否则 ``QLabel`` 的
    #      ``minimumSizeHint()`` 等于整段文字宽度，会把所在分栏"顶"开
    #      （实测长路径把窗口压成「左 1512 / 右 550」，连 ``splitter.setSizes()``
    #      都拦不住：QSplitter 不会把子控件压到其 minimumSizeHint 之下）。
    #   ② 拿到宽度后，一律走 :meth:`_fit` —— 它保证**返回值一定塞得进给定宽度**，
    #      放不下就按 ``省略号`` 截断，绝不再往外"要"空间。
    #
    # ⚠️ ①② 缺一不可、且互相依赖：只做①不做②，文字被硬裁（右半截看不见）；
    #    只做②不做①，``label.width()`` 本身已被文字撑大，量出来的宽度是假的。
    #
    # ⚠️ 宽度要在 ``_sync_controls()`` 里**现取**（``label.width()``），不能缓存 ——
    #    窗口每次变尺寸都要重新算，``resizeEvent`` 已经接好了这条链。


    def _fit(self, label, text, reserve=''):
        """把 ``text`` 适配进 ``label`` 的当前宽度，返回**保证不溢出**的文字。

        策略（按"信息重要性"从高到低）：整段放得下 → 原样；放不下 → 中间省略；
        连 ``reserve`` 都挤不下 → 只保 ``reserve``（它是最该看清的部分）。

        Args:
            label: 提供宽度与字体度量的标签。
            text: 主体文字（如路径、文件名）。
            reserve: 必须一起显示的**后缀**（如 ``  (12 张)``）。它优先于主体：
                空间不够时先牺牲主体，而不是把后缀切掉。

        Returns:
            str: 适配后的文字（宽度以像素计，含 8 px 的右边距余量）。
        """
        metrics = label.fontMetrics()
        avail = label.width() - 8
        if avail < self.ELIDE_MIN_WIDTH:
            # 标签还没被摆好（width 可能是 0）：按兜底宽度截，
            # 这样至少得到一个带省略号的短串，而不是一整段长文字。
            avail = self.ELIDE_MIN_WIDTH
        reserve = str(reserve or '')
        body_avail = avail - metrics.horizontalAdvance(reserve)
        if body_avail <= 0:
            # 连后缀都放不下：只留后缀（必要时连它也截），主体全让位。
            if metrics.horizontalAdvance(reserve) <= avail:
                return reserve
            return metrics.elidedText(reserve, QtCore.Qt.TextElideMode.ElideRight,
                                      avail)
        text = str(text)
        if metrics.horizontalAdvance(text) > body_avail:
            text = metrics.elidedText(text, QtCore.Qt.TextElideMode.ElideMiddle,
                                      body_avail)
        return text + reserve

    def _describe_current(self, width=None):
        """信息行：文件名 · 尺寸 · 体积 ·（所在子目录）。

        ⚠️ **刻意不再重复「相对路径」**：原先这一行是「文件名 · 尺寸 · 体积 · 相对路径」，
        而相对路径的**末段就是文件名本身** —— 长名字的图会在同一行里把同一个名字显示
        两遍（实测 2760 px，把左侧相册压成 70 px）。现在只补「所在子目录」
        （已经在根目录就不补），信息量不减、长度却短得多。

        截断策略（从高到低保留）：「文件名 · 尺寸 · 体积」这几个短字段**整体优先**，
        放不下时先丢**子目录**（它是可推导的、也最长），再放不下才截前几个字段。
        ⚠️ 不能把整行交给 Qt 一起截：``ElideLeft`` 会把体积甚至尺寸切掉，
        实测变成「… KB · a_very_long_subdirectory…」，连文件多大都看不见了。

        Args:
            width: 可用宽度（像素）。None / <=0 表示不截断（返回完整文字）。

        Returns:
            str: 这一行要显示的文字。
        """
        if not (0 <= self._index < len(self._paths)):
            return '共 {0} 张'.format(len(self._paths))
        path = self._paths[self._index]
        parts = [os.path.basename(path)]
        image = self._cache.get(self._index)
        if image is not None:
            parts.append('{0}×{1}'.format(image.width(), image.height()))
        try:
            parts.append('{0:.1f} KB'.format(os.path.getsize(path) / 1024.0))
        except OSError:
            pass
        if self._shown != self._index:
            parts.append('解码中…')
        head = '  ·  '.join(parts)

        # 只在**子目录里**才补目录名：文件就在根目录时补上只会是废话。
        folder = os.path.dirname(path)
        sub = ''
        if folder and os.path.abspath(folder) != self._display_folder():
            try:
                sub = os.path.relpath(folder, self._display_folder())
            except ValueError:
                sub = folder
            if sub == '.':
                sub = ''

        if width is None or width <= 0:
            return head + ('  ·  ' + sub if sub else '')

        metrics = self.info_label.fontMetrics()
        sep = '  ·  '
        if not sub:
            # 没有子目录：整行按普通中间省略即可。
            if metrics.horizontalAdvance(head) > width:
                head = metrics.elidedText(head, QtCore.Qt.TextElideMode.ElideMiddle,
                                          width)
            return head
        room = width - metrics.horizontalAdvance(head + sep)
        if room <= 0:
            # 子目录放不下 —— 直接丢掉它（可推导的冗余信息），头部整体保留；
            # 头部自己也超宽时才截它。
            if metrics.horizontalAdvance(head) > width:
                head = metrics.elidedText(head, QtCore.Qt.TextElideMode.ElideMiddle,
                                          width)
            return head
        # 子目录有地方：从**左侧**省略它（省掉的正是重复的目录前缀）。
        if metrics.horizontalAdvance(sub) > room:
            sub = metrics.elidedText(sub, QtCore.Qt.TextElideMode.ElideLeft, room)
        return head + sep + sub

    # ================================================================== 列表填充
    def _fill_list(self):
        """按扫描结果重建相册（缩略图先占位，由后台线程一张张补上）。"""
        self._syncing = True
        try:
            self.list.clear()
            icon = self._placeholder_icon()
            for path in self._paths:
                name = os.path.relpath(path, self._display_folder())
                item = QtWidgets.QListWidgetItem(icon, name)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                item.setData(QtCore.Qt.ItemDataRole.UserRole, path)
                item.setToolTip(path)
                item.setTextAlignment(
                    QtCore.Qt.AlignmentFlag.AlignHCenter
                    | QtCore.Qt.AlignmentFlag.AlignTop)
                self.list.addItem(item)
        finally:
            self._syncing = False

    def _placeholder_icon(self):
        """缩略图还没生成时用的占位图标（颜色取自调色板，跟随主题）。"""
        if self._placeholder is None:
            pixmap = QtGui.QPixmap(self.THUMB_ICON, self.THUMB_ICON)
            pixmap.fill(self.palette().color(QtGui.QPalette.ColorRole.Mid))
            self._placeholder = QtGui.QIcon(pixmap)
        return self._placeholder

    # ================================================================== 生命周期
    def showEvent(self, event):
        """标签页被显示：重算响应式布局 + 更新按钮状态（**不重扫**）。"""
        super(ImageBrowser, self).showEvent(event)
        # 首次显示时宽度才真正定下来，这里补一次响应式计算。
        self._update_responsive()
        self._sync_controls()

    def hideEvent(self, event):
        """标签页被切走：正在播放就暂停，并记下「可以继续」。"""
        super(ImageBrowser, self).hideEvent(event)
        if self._playing:
            self._pause(by_hide=True)

    def resizeEvent(self, event):
        """尺寸变了：重算响应式布局、重新截断文字；解码目标尺寸变了就丢掉缓存。"""
        super(ImageBrowser, self).resizeEvent(event)
        # 先定“显示哪些”，再同步文字（_sync_controls 里会按最新宽度截断）。
        # ⚠️ 顺序不能反：先同步文字的话，用的是“相册还没收起”时的旧宽度。
        self._update_responsive()
        side = self._target_side()
        if side != self._cache_side and self._cache_side:
            self._cache.clear()
            self._load_plan = []
        self._cache_side = side
        self._sync_controls()

    def cleanup_before_tab_close(self):
        """关标签前的收尾：停表、通知线程收工、放掉引用。

        ⚠️ 这里**不 ``wait()``** —— 规范要求两个清理钩子都不许阻塞（同步等一会儿
        就是冻结界面）。线程能被安全回收靠的是「不设 parent + 类级强引用」那两条纪律
        （见 ``_Worker``），本方法只负责「通知它们可以走了」。
        """
        self._playing = False
        self._paused_by_hide = False
        self._timer.stop()
        for thread in (self._scan_thread, self._thumb_thread, self._load_thread):
            self._stop_thread(thread)
        self._scan_thread = None
        self._thumb_thread = None
        self._load_thread = None
        self._cache.clear()
        self._load_plan = []

    @staticmethod
    def _stop_thread(thread):
        """通知一个后台线程收工（线程若已被销毁就静默跳过）。

        线程不设 parent，理论上不会被提前销毁；但 ``finished`` 之后会走
        ``deleteLater()``，那一刻 Python 这侧的包装对象就失效了 —— 收尾路径上
        多一层容错比抛 ``RuntimeError`` 好。
        """
        if thread is None:
            return
        try:
            thread.stop()
        except Exception:
            pass

    def closeEvent(self, event):
        """控件被单独 ``close()``（例如直接跑 ``test_1()``）时也做同样的收尾。

        ⚠️ 这条路径**不是**关标签页那条（那边走 ``deleteLater()``，不发 ``closeEvent``），
        所以它只是对 :meth:`cleanup_before_tab_close` 的补充，不能替代后者。
        """
        self.cleanup_before_tab_close()
        super(ImageBrowser, self).closeEvent(event)


# ====================================================================== 菜单入口
def show_image_browser():
    """打开（或切到）「图片浏览」标签页；同时也是 GUI 命令 ``gui.show_image_browser()``.

    目录由 :class:`ImageBrowser` 自己决定：**默认跟随工作路径**
    （每次刷新都现取 ``os.getcwd()``），所以用户改了工作路径再点刷新，看到的就是新目录。

    ⚠️ 这里走 ``gui.command`` 而不是直接开标签页：菜单项是从 GUI 线程调的，但
    ``gui.show_image_browser()`` 也可能被**脚本 / 后台线程**调用 —— 走命令表才能保证
    「无论谁调，开标签页这件事都发生在 GUI 线程里」。

    ⚠️ 标签页按「类型 + 标题」复用：重复点菜单只会切到那一页。也正因为复用，
    **不能**在 ``type_kw`` 里传 ``folder``（那会把目录固定在第一次打开时的值上）。
    """
    from zmlx.ui import gui

    gui.command('show_image_browser')


def _open():
    """真正打开标签页（注册成命令 ``show_image_browser``，故只在 GUI 线程里执行）."""
    from zmlx.ui import gui

    def _oper(w):
        # ⚠️ 只做「记住怎么重放我」这一件事，不要在这里刷新（见模块文档）。
        w.gui_restore = 'gui.show_image_browser()'

    gui.get_widget(
        the_type=ImageBrowser,
        caption='图片浏览',
        on_top=True,
        oper=_oper,
        tooltip='浏览工作路径下的图片：左侧缩略图相册，点选后在右侧查看大图，'
                '支持上一张/下一张、按帧率连续播放与循环',
        # ⚠️ **刻意不传 folder**：不传 = 控件跟随工作路径，每次刷新都现取
        #    ``os.getcwd()``。传了 ``folder=os.getcwd()`` 反而会把它**固定**在
        #    打开菜单那一刻的目录上 —— 之后用户改了工作路径、再点刷新，
        #    看到的还是老目录（这正是要避免的行为）。
        #    标签页被复用（get_widget 按「类型+标题」）时也不会残留旧目录。
    )


@execute_once(file=__file__)
def setup_ui():
    """注册 GUI 命令与菜单项（由 ``plugins.load_all`` 执行本文件时触发）."""
    from zmlx.ui import gui

    # 先注册命令：gui.show_image_browser() 与菜单项指向**同一个**函数，
    # 保证「菜单」与「命令」不会各写一套。
    gui.add_func('show_image_browser', _open)

    gui.add_action(
        # ⚠️ 2026-10-26：菜单路径由 ``'文件'`` 改为 ``['文件', '浏览']``（子菜单合并，
        #    见模块文档）。``name='image_browser'`` 与 ``gui.show_image_browser()``
        #    **都不变** —— 那是 ribbon 配置 / 已保存的界面布局 / 历史标签页的定位依据。
        menu=['文件', '浏览'],
        name='image_browser',
        text='图片',
        slot=show_image_browser,
        overwrite=False,
    )


def test_1():
    """直接运行本文件时的自测：浏览 ``sys.argv[1]`` 或当前工作路径下的图片。

    直接跑：``python zmlx/ui/plugins/builtin/image_browser.py [目录]``

    ⚠️ 这里**只**造控件来测「相册浏览」本身，不调 ``setup_ui()``（那样会把菜单挂进
    一个没有主窗口的进程里）。要验「菜单 / 命令」那一侧，按 ``../AGENTS.md`` 的验收
    清单走：重启 GUI →「设置 → 插件」→ 该行「临时加载」。
    """
    app = QtWidgets.QApplication(sys.argv)
    folder = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    w = ImageBrowser(folder=folder)
    w.resize(1280, 820)
    w.setWindowTitle('ImageBrowser — {0}'.format(folder))
    w.show()
    sys.exit(app.exec())


# ⚠️ 插件的标准形式：**注册写在这个分支里**。
#    插件机制用 ``exec`` 执行本文件时，命名空间里的 ``__name__`` 被设成
#    ``'__zml_plugin__'``，于是这里成立 —— 只注册，不开窗口。
#    ⚠️ **不要**在顶层裸写 ``setup_ui()``：那样「插件加载」与「直接运行本文件」
#    走同一段代码，既无法区分两种意图，也无法在 ``python image_browser.py`` 时自测。
if __name__ == '__zml_plugin__':
    setup_ui()

# ⚠️ 两支用**两个独立的 if**，不要写成 if / elif（见 `../AGENTS.md` §2 第 4 步）。
if __name__ == '__main__':
    test_1()
