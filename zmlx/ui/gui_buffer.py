"""
zmlx GUI 执行框架。

== 核心用法 ==

所有 gui.xxx() 函数（break_point、progress、show_attrs 等）只有在通过
gui.execute() 启动主程序时才会生效。在非 GUI 模式下，这些调用自动变为
无害的空操作，不需要手动判断。

**正确的启动方式**（仅在 if __name__ == '__main__' 下调用 gui.execute）：

    if __name__ == '__main__':
        gui.execute(main, close_after_done=False)

**无头模式**（不显示 GUI 窗口）：

    python demo.py --no-gui
    python demo.py --headless

在 gui.execute() 内部会自动检测无头模式，不需要手动处理。

**不要在其它位置调用 gui.execute()**。gui.execute 只应出现在主程序
入口的 if __name__ == '__main__' 块中。如果在函数内部调用 gui.execute，
会导致嵌套执行，产生不可预期的行为。

参考 demo 文件（如 zmlx/demos/flow_1ph/darcy_1d.py）了解更多示例。

== 跨线程动界面：四条通道 ==

**控制台线程 / 任意后台线程里，永远不要直接碰 Qt 控件**，按下面的分工选：

======================  ==========================  =========  ===============
想要什么                 用什么                       同步？      拿得到结果
======================  ==========================  =========  ===============
改界面（有导出函数）      ``gui.xxx(...)``             ✅ 阻塞     ✅
改界面（没有导出函数）    ``gui.call(func, ...)``      ✅ 阻塞     ✅
跑长任务                  ``gui.start(func, ...)``     ❌ 立刻返回  `Console.result`
稍后在 GUI 线程跑一下      ``gui.add_task(func)``       ❌          ❌
======================  ==========================  =========  ===============

⚠️ ``gui.start`` 是**单任务**的：控制台只有一个线程槽位，忙的时候再调会被**静默丢弃**
（只响一声）。调之前必须判 ``gui.is_running()`` —— 完整规则、死锁警告与排查表见
[`AGENTS.md`](AGENTS.md) §6。

⚠️ **``Console`` 仍是长任务唯一槽位。** 上表第 3 行说的「跑长任务」= 要能被暂停/停止的
仿真、批量计算。**多个短/中任务并发**是另一件事，用
``zmlx.ui.utils.thread_runner``（§6.8），别反复调 ``gui.start``（第二个必被丢），
也别自己写 ``QThread`` 子类。判据：需要暂停/继续/停止 ⇒ ``gui.start``；
并行做完再回写界面 ⇒ ``thread_runner``。

== 调用已注册的函数：只写 ``gui.xxx(...)`` ==

外部代码（插件 / 脚本 / 场景 / 后台线程）调用**命令表里的函数**时，只写 ``gui.xxx(...)``，
**不要** ``gui.get().xxx()``：

    gui.list_all()               # ✅  __getattr__ -> Agent -> command('list_all')
    gui.get_func('plot')         # ✅
    gui.get().list_all()         # ❌  绕过派发层，跨线程没有任何保证

``gui.xxx`` 这个**属性访问本身就是契约**（``__getattr__`` 返回 ``Agent``）：于是
「命令不存在」只有一个处理点（``GuiApi.__proc`` 抛 ``RuntimeError``），跨线程调用也由它
自动搬到 GUI 线程。``gui.get()`` 返回的是 ``GuiApi`` 实例，拿它再调方法等于直接读一个
属于 GUI 线程的对象 —— 在 GUI 线程里看不出差别，在后台线程里则丢掉了唯一的线程保证。
``GuiBuffer`` 自己的实现（``command`` 等转发）是唯一例外。

**判据**：名字出现在 ``gui.list_all()`` 里 ⇒ 一律 ``gui.名字(...)``。
本类那几个显式方法（``command`` / ``call`` / ``start`` / ``add_task`` / ``exists`` /
``mark_direct``）**不是**命令表里的命令，照常用。

完整规则与反例见 [`AGENTS.md`](AGENTS.md) §6.2。

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
Modified by DeepSeek, 2026-10-20: 补「四条通道」；``call`` / ``start`` / ``add_task``
    由动态代理改为显式方法（带 docstring，便于检索）
Modified by DeepSeek, 2026-10-20: 补「Console 仍是长任务唯一槽位」，指向 thread_runner 的分工
Modified by DeepSeek, 2026-10-23: ``mark_direct`` 补 docstring —— 它去掉的是「派发到 GUI 线程」，
    默认不要用（判据与踩坑见 ``ui/AGENTS.md`` §6.2）
Modified by DeepSeek, 2026-11-02: 补「调用已注册的函数：只写 ``gui.xxx(...)``」一节 ——
    ``gui.get().xxx()`` 绕过派发层，跨线程没有线程保证（判据见 ``ui/AGENTS.md`` §6.2）
"""

from zmlx.system import warn
import datetime
import os
import sys
from typing import Optional, Tuple, List, Union

from zmlx.system import app_data, is_headless, make_parent


class GuiBuffer:
    def __init__(self):
        self.__api = None

    def command(self, *args, **kwargs):
        """
        执行命令
        Args:
            *args: 位置参数
            **kwargs: 关键词参数
        Returns:
            命令的返回值
        """
        if self.__api is not None:
            return self.__api.command(*args, **kwargs)
        else:
            return None

    def call(self, func, *args, **kwargs):
        """**在 GUI 线程**执行任意可调用对象，并把结果（或异常）带回调用者.

        这是「想动界面，但没有现成的 ``gui.xxx`` 导出函数」时的正道 —— 把要做的
        那一步包成 callable 交给它即可，例如（内核线程里）::

            gui.call(self.btn.setEnabled, False)
            gui.call(lambda: w.setWindowTitle('跑完了'))

        ⚠️ **为什么需要它**：Qt 控件只能在 GUI 线程碰。直接在后台线程
        ``widget.setXxx(...)`` 属未定义行为（轻则不刷新，重则崩）。``GuiApi.command``
        本来就能把「命令名 + 参数」派发过去，``call`` 只是把「命令名」换成「任意
        callable」—— 因此**闭包里的控件访问也在 GUI 线程里发生**。

        ⚠️ 它是**同步**的：调用线程会阻塞到 GUI 线程执行完（异常也会在调用线程重新
        抛出）。所以别在 GUI 线程里调一个「要等内核线程」的东西（会互等死锁），也别
        在持有锁的时候调（GUI 线程可能正等这把锁）。只要「稍后跑一下」、不要结果，
        用 ``add_task`` 而不是它。

        Args:
            func: 要在 GUI 线程执行的可调用对象。
            *args: 传给 ``func`` 的位置参数。
            **kwargs: 传给 ``func`` 的关键词参数。

        Returns:
            ``func`` 的返回值；无界面（headless）时就在当前线程直接执行后返回。
        """
        if self.__api is None:  # 没有界面：不存在「GUI 线程」这件事
            return func(*args, **kwargs)
        return self.command('call', func, *args, **kwargs)

    def start(
            self, func, *, text_beg=None, text_end=None, post_task=None,
            file=None, name=None, add_history=True):
        """在**控制台线程**里执行 ``func`` —— 界面里跑长任务的唯一正规通道.

        转发到 ``Console.start_func``（``main.py`` 里注册为命令 ``start``）。

        ⚠️ **单任务**：控制台只有一个线程槽位，同一时刻只允许一个任务。忙的时候
        再调 ``start`` 会**被直接丢弃**（只响一声 ``play_error()``，没有异常、
        没有返回值区分）。所以调用前请自己判 :meth:`is_running`，并把「忙」如实
        告诉用户 —— 否则用户看到的是「点了没反应」。

        ⚠️ 任务体里操作界面**必须**走 ``gui.xxx`` / :meth:`call` / ``print``
        （``sys.stdout`` 会自己投递到 GUI 线程），不能直接碰控件。

        ⚠️ ``post_task`` 在任务结束后执行，**运行在 GUI 线程**（``Console`` 的
        ``__kernel_exited`` 槽），即使任务抛异常也会执行 —— 适合回写按钮/状态。
        任务的返回值存在 ``Console.result`` 里（``gui.command('get_console')`` 可拿）。

        Args:
            func: 要执行的可调用对象（**不要**传字符串：字符串走 ``exec`` 分支，
                那是给「运行脚本文件」用的）。
            text_beg: 开始提示（蓝色打印到控制台），如 ``'Start: xxx'``。
            text_end: 结束提示。
            post_task: 任务结束后的收尾回调（GUI 线程执行，异常也会执行）。
            file: 记录用的文件名（只影响提示与历史）。
            name: 记录用的 ``__name__``（只影响 ``app_data.space``）。
            add_history: 是否记进「运行历史」（可再点「运行上一次」重跑）。
                临时性任务（例如插件「临时加载」）应当传 ``False``。

        Returns:
            None
        """
        if self.__api is None:  # 无界面：没有控制台线程，直接跑
            try:
                return func()
            finally:
                if callable(post_task):
                    post_task()
        return self.command(
            'start', func, text_beg=text_beg, text_end=text_end,
            post_task=post_task, file=file, name=name,
            add_history=add_history)

    def add_task(self, task):
        """把 ``task`` 投递到 GUI 线程执行（**异步**、不返回结果）.

        与 :meth:`call` 的区别只有两点：不等结果、异常只能靠 ``TaskProc`` 打印。
        高频投递（例如 ``sys.stdout.write``）用它，别用 ``call``。
        """
        api = self.__api
        if api is None:
            return task()
        return api.command('add_task', task)

    def set(self, api):
        """
        设置api
        Args:
            api: 要设置的api对象
        """
        self.__api = api
        print(f'Gui Set: {self.__api}')

    def get(self):
        """
        返回api对象
        Returns:
            api对象
        """
        return self.__api

    def exists(self):
        """
        是否存在api (处于gui模式下)
        Returns:
            是否存在api对象
        """
        return self.__api is not None

    def __bool__(self):
        """
        是否存在api对象 (处于gui模式下)
        Returns:
            是否存在api对象
        """
        return self.exists()

    def break_point(self):
        """
        添加一个断点，用于暂停以及安全地终止gui程序
        """
        self.command(break_point=True)

    # 函数的别名<为了兼容之前的代码>
    breakpoint = break_point

    def pause(self, message=None):
        """
        点击暂停，并添加断点，确保可以被暂停.
        Args:
            message: 要打印的消息
        """
        if message is not None:
            print(message)
        if is_headless():
            disable = True
        else:
            if app_data is not None:
                disable = app_data.get('DISABLE_PAUSE', False)  # 禁止内核的暂停
            else:
                disable = False
        if not disable:
            self.command('click_pause')
        self.break_point()

    class Agent:
        def __init__(self, obj, name, **opts):
            self.obj = obj
            self.name = name
            self.opts = opts  # 预定义的

        def __call__(self, *args, **kwargs):
            opts = self.opts.copy()
            opts.update(kwargs)
            return self.obj.command(self.name, *args, **opts)

    def __getattr__(self, name):
        """
        返回一个函数代理对象

        ⚠️ **``gui.plot`` 走的就是这里**：本类**不再**定义 ``plot`` 方法（2026-11-01 回退），
        所以 ``gui.plot(...)`` 会变成 ``Agent`` → ``command('plot', ...)`` →
        ``MainWindow.plot``。绘图因此**只在 GUI 线程发生一次**：建标签页、跑回调、
        ``canvas.draw()``、按需存图全在那一次命令里顺序做完，调用线程只等一次。

        Args:
            name: 命令名（即 ``gui.<name>`` 的 ``<name>``）
        Returns:
            函数代理对象
        """
        return GuiBuffer.Agent(self, name)

    def set_agent(self, key, **kwargs):
        """
        添加函数关键词的代理(给定默认值)
        Args:
            key: 函数的名称
            **kwargs: 关键词参数，作为默认值
        Returns:
            函数代理对象
        """
        if len(kwargs) == 0:  # 移除代理
            if hasattr(self, key):
                delattr(self, key)
            return self
        else:  # 添加代理
            agent = GuiBuffer.Agent(self, key, **kwargs)
            setattr(self, key, agent)
            return self

    def mark_direct(self, key):
        """把 ``gui.<key>`` 登记成「**在调用者线程里直接执行**」—— 默认**不要**用.

        语义：登记后 ``gui.<key>(...)`` 不再派发到 GUI 线程，而是在**调用者线程**里
        直接运行那个函数（见 :meth:`GuiApi.command` 的 ``is_direct`` 分支）。它去掉的
        正是「派发到 GUI 线程」这一步。

        ⚠️ **它只在「非 GUI 线程调用」时才有差别**：GUI 线程内调用，正常路径本来就是
        AutoConnection 直连、就地执行，登不登记一模一样。所以 ``is_direct`` 的全部
        意义都落在后台线程那条路上 —— 而那正是最危险的一条。

        ⚠️ **判据只有一条：函数体不触碰任何 Qt 对象**。目前全仓**只有 ``window``**
        符合（就是 ``lambda: self``，只返回 ``MainWindow`` 实例本身）。

        它换来的是**确定的延迟上界**（2026-10-30 实测：GUI 线程在槽里阻塞 1.5 s 期间，
        从后台线程调 ``gui.window()``）：

        ======================  ===========
        走法                     耗时
        ======================  ===========
        ``is_direct``（登记后）   **0.023 ms**
        正常派发                 **1200 ms**（一直等到 GUI 回到事件循环）
        ======================  ===========

        ⚠️ 这里的「GUI 忙」指**阻塞了事件循环**（长槽里的计算 / 文件 IO）；模态对话框
        自带事件循环，不会拖住排队的调用。两者都拿到同一个窗口对象 ⇒ **正确性无差别，
        差别只在延迟**。

        ❌ **凡是会建控件、碰窗口、读标签容器的命令都不能登记**，哪怕它只是「转发」：
        一旦登记，后台线程（控制台 / 插件）调 ``gui.xxx()`` 就**当场在后台线程里**
        建控件 —— Qt 控件只能在 GUI 线程碰，轻则不刷新、重则崩，且不可复现。
        2026-10-23 就因为「以为转发类方法多绕了一跳」把 14 条插件命令登记过，当日撤销。

        ⚠️ **2026-10-30 又撤了 ``edit_in_tab`` / ``reg_file_type`` 两条**：前者全部工作就是
        调 ``gui.get_widget(...)``（登记成 direct = 在后台线程里调 GUI 命令，绕一圈没有
        收益），后者只做注册、GUI 线程执行一样快。**它们换不到上表那个延迟收益，只会多
        一份「在后台线程执行」的风险面。**

        ⚠️ **「多绕了一跳」不构成理由**：命令表里放的往往是插件函数本身
        （``gui.add_func`` 后写覆盖），主窗口经 ``gui.xxx`` 是「GUI 线程内直接执行」；
        嫌绕就直接调那个对象（``w.show_timer()``），不要改这里的线程语义。
        通道池取消之后（v1.9.9），连「省一个通道」这条老理由也不成立了。

        Args:
            key: 函数的名称。
        Returns:
            函数代理对象（``self``）。
        """
        return self.set_agent(key, is_direct=True)

    def execute(
            self, func=None, keep_cwd=True, close_after_done=True,
            args=None,
            kwargs=None, disable_gui=False, add_history=True):
        """
        尝试在gui模式下运行给定的函数 func
        Args:
            func: 要运行的函数
            keep_cwd: 是否保持当前目录
            close_after_done: 是否在完成后关闭gui
            args: 要传递给函数的位置参数
            kwargs: 要传递给函数的关键词参数
            disable_gui: 是否禁用gui模式
            add_history: 是否将运行历史添加到历史记录(从而方便再次运行)
        Returns:
            函数的返回值
        """

        def fx():
            if func is not None:
                x = args if args is not None else []
                y = kwargs if kwargs is not None else {}
                return func(*x, **y)
            else:
                return None

        from zmlx.system import is_headless

        if self.exists() or disable_gui or is_headless():  # 此时，不需要新启动GUI界面
            return fx()

        try:
            from zmlx.ui.main import execute
            return execute(fx, keep_cwd=keep_cwd,
                           close_after_done=close_after_done,
                           add_history=add_history)
        except Exception as execute_err:
            print(f'call gui failed: {execute_err}', file=sys.stderr)
            return fx()


gui = GuiBuffer()

app_data.put('gui', gui)


def break_point():
    """
    添加一个gui的断点，从而在gui执行的过程中，可以控制暂停和终止
    """
    gui.break_point()


def information(*args, **kwargs):
    break_point()
    return gui.information(*args, **kwargs)


def question(info):
    if gui.exists():
        break_point()
        return gui.question(info)
    else:
        y = input(f"{info} input 'y' or 'Y' to continue: ")
        return y == 'y' or y == 'Y'


def _plot_no_gui(kernel, *args, fname=None, dpi=300, caption=None, clear=None, tight_layout=None, suptitle=None,
                 on_top=None,  # 兼容gui下的参数
                 savefig=None,  # 兼容gui下的参数
                 folder_save=None,  # 兼容gui下的参数
                 **kwargs):
    """在非 GUI 模式下绘图（保存到文件）。

    内部函数，用户不应直接调用。请使用 gui.plot() 或 zmlx.ui.plot()，
    它们会自动根据环境选择 GUI 绘图或非 GUI 保存。
    """
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        from zmlx.system import log
        log(text=f'{e}', tag='matplotlib_import_error')
        plt = None

    if kernel is None or plt is None:
        return None
    try:
        from zmlx.plt import set_chinese_font
        set_chinese_font()

        if fname is None:
            if folder_save is not None:
                now = datetime.datetime.now()
                name = now.strftime("%Y-%m-%d-%H-%M-%S-") + f"{now.microsecond:06d}.png"
                fname = make_parent(os.path.join(folder_save, name))
            else:
                if is_headless() and caption is None:
                    caption = "default_figure"
                if caption is not None:
                    from zmlx.plt import get_plt_save_path
                    now = datetime.datetime.now()
                    name = now.strftime("%Y-%m-%d-%H-%M-%S-") + f"{now.microsecond:06d}.png"
                    fname = make_parent(os.path.join(get_plt_save_path(caption), name))
        fig = plt.figure()
        kernel(fig, *args, **kwargs)
        if isinstance(suptitle, str):
            fig.suptitle(suptitle)
        if tight_layout:
            if isinstance(tight_layout, dict):
                fig.tight_layout(**tight_layout)
            else:
                fig.tight_layout()
        if fname is not None:
            fig.savefig(fname=fname, dpi=dpi)
            plt.close()
            return None
        else:
            plt.show()
            return fig
    except Exception as err:
        warn(f'meet exception <{err}> when run <{kernel}>')
        return None


def plot(kernel, *args, gui_only=False, gui_mode=None,
         fname=None, dpi=300,
         **kwargs):
    """
    调用matplotlib执行绘图操作. 如果需要处于gui_mode下面绘图，但是当前不是gui模式，则打开gui界面绘图(此功能仅供测试使用)

    ⚠️ **绘图全部在 GUI 线程完成，且只跨界一次**：``gui.plot`` 经 :meth:`GuiBuffer.__getattr__`
    代理成 ``command('plot', ...)``，由 :class:`GuiApi` 派发到 ``MainWindow.plot``。建标签页、
    跑 ``kernel``、``canvas.draw()``、按需存图都在那一次命令里顺序执行，本函数阻塞到画完才返回。
    所以回调里**不必**再 ``copy()`` 数据（它就在 GUI 线程跑）；代价是重图期间界面会停住。

    Args:
        kernel: 绘图的回调函数，函数的原型为：
            def kernel(figure, *args, **kwargs):
                ...
        gui_only: 是否只在GUI模式下执行
        fname: 输出的文件名
        dpi: 输出的分辨率
        *args: 传递给kernel函数的参数
        **kwargs: 传递给kernel函数的关键字参数
        gui_mode: 是否强制使用GUI模式

    Returns:
        Figure | None: GUI 下返回画好的 figure；无界面且未给 fname 时为 None
    """

    def plot_with_gui():
        try:
            gui.break_point()
            return gui.plot(kernel, *args, fname=fname, dpi=dpi, **kwargs)
        except Exception as plot_err:
            print(f'plot failed: {plot_err}', file=sys.stderr)
            return None

    if gui.exists():
        return plot_with_gui()

    # 此时，没有处在gui中
    if gui_mode:
        from zmlx.system import is_headless
        if is_headless():
            gui_mode = False

    if gui_mode:  # 创建窗口来运行(并在绘图后保持窗口打开状态)
        return gui.execute(plot_with_gui, close_after_done=False)

    if gui_only:
        return None
    else:
        return _plot_no_gui(kernel, *args, fname=fname, dpi=dpi, **kwargs)


def progress(
        label: Optional[str] = None, val_range: Optional[Union[List[int], Tuple[int, int]]] = None,
        value: Optional[int] = None, visible: Optional[bool] = None
):
    """
    显示(或者隐藏进度条(如果gui模式下)
    Args:
        label: 进度条的标签
        val_range: 进度条的范围
        value: 当前进度
        visible: 是否可见
    Returns:
        None
    """
    if gui.exists():
        gui.progress(label=label, val_range=val_range, value=value, visible=visible)


def show_attrs(clear: bool = False, **attrs):
    """
    在控制台内核运行的过程中，在控制台的输出窗口显示的一些动态的属性值（在控制台运行结束之后隐藏）
    Args:
        clear: 是否清除已有的参数
        **attrs: 要显示的参数
    Returns:
        None
    """
    if gui.exists():
        gui.show_attrs(clear=clear, **attrs)


def gui_exec(*args, **kwargs):
    """
    调用gui来执行一个函数，并返回函数的执行结果
    """
    return gui.execute(*args, **kwargs)


def add_action(
        menu=None, text=None, name=None, slot=None,
        icon=None, tooltip=None, shortcut=None,
        on_toolbar=None,
        is_enabled=None,
        is_visible=None,
        overwritable=None,
        overwrite=None
):
    """
    在gui菜单添加一个操作项

    参数原样转给 ``MainWindow.add_action``（同步派发到 GUI 线程执行），**这里不加逻辑**；
    完整的参数说明见那个方法的 docstring。两个要点在这里重复一次，因为最常踩：

    - ``menu`` 可以是 ``str``（一级）或 ``list``（多级路径），每级标题必须与别处**逐字一致**；
    - ``overwrite`` 管的是「**``name`` 已被占用时怎么办**」：
      ``True``（默认）→ **就地覆盖**：用本次参数重设那个已有 action（菜单里始终只有一条）；
      ``False`` → 发一条 ``UserWarning`` 并**跳过**，已有那条保持原样。

    ⚠️ ``overwritable`` 是 ``overwrite`` 的**弃用别名**（2026-10-27 改名，2027-10-27 删除）：
    传它会发一条 ``DeprecationWarning``，行为与 ``overwrite`` 完全等价。新代码请用 ``overwrite``。

    ⚠️ ``text='---'`` 是**分隔符**（2026-10-26 加；判据是 ``text`` 而非 ``name``）：
    只在菜单末尾插一条分隔线，不建 action —— 其余参数一个都不用给::

        gui.add_action(menu='操作', text='---')

    它**不判重**（连插两条就是两条线），也**不会**让分隔线出现在工具栏上
    （``on_toolbar`` 对它不生效；工具栏的分隔符仍要自己 ``insertSeparator``）。
    """
    if gui.exists():
        gui.add_action(
            menu=menu, text=text, name=name, slot=slot,
            icon=icon, tooltip=tooltip, shortcut=shortcut,
            on_toolbar=on_toolbar,
            is_enabled=is_enabled,
            is_visible=is_visible,
            overwritable=overwritable,
            overwrite=overwrite
        )


def proc_argv(argv=None):
    from zmlx.algs import fsys
    if not isinstance(argv, (list, tuple)):
        return
    if len(argv) < 2:
        return
    key = argv[1]
    if fsys.isfile(key):
        gui.open_file(key)
        return
    gui.command(*argv[1:])


def open_gui(argv=None):
    """
    打开gui
    """
    from zmlx.system import app_data
    app_data.put('argv', argv)
    # 是否需要恢复标签
    app_data.put('restore_tabs',
                 app_data.getenv('restore_tabs', default='Yes') != 'No')
    # 是否初始检查
    app_data.put('init_check',
                 app_data.getenv('init_check', default='Yes') != 'No')
    gui.execute(func=lambda: proc_argv(argv), keep_cwd=False, close_after_done=False,
                add_history=False)


class _Startup:
    """「启动时要不要加载某项」的全部约定 —— 不实例化，纯粹当**命名空间**用.

    ⚠️ 为什么全收进一个类、而不是平铺成模块级常量（2026-11-03）：文件级别的全局名会被
    别处 import 走，之后就再也改不动了；这类「只服务启动流程」的约定本来就不该出现在
    模块的公共命名空间里。对外只留 :func:`is_safe_start` 与 :func:`start_option` 两个函数，
    键名本身属于实现细节（见 ``zmlx/ui/widgets/AGENTS.md`` §2「模块级内容」）。

    ⚠️ 所有开关都放在 ``app_data`` 的**内存**里（``put``）：只活在本次运行、不落盘，
    也不会改变用户在「设置 → 系统」里存的任何开关 —— 「这次先别加载」不会变成
    「以后都不加载」。
    """

    #: 「安全启动」的总开关：本次运行尽量少加载。由 :func:`open_gui_without_setup` 写入。
    SAFE = 'safe_start'

    #: 「安全启动」下**每一项**加载的键（细分，便于单独诊断 / 单独覆盖）。
    HISTORY = 'restore_console_output'    # 恢复控制台输出历史（main.__restore_history）
    TABS = 'restore_tabs'                 # 重放上次的标签页（main.__console_kernel）
    PLUGINS = 'run_plugins'               # plugins.load_all()（旧名 run_setup 仍写）
    SETUPS = 'run_setups'                 # setups.setup_ui()（⚠️ 与插件开关是两回事）
    INIT_CHECK = 'init_check'             # 启动自检弹框（main.__check）
    UI_STATE = 'restore_ui_state'         # 窗口尺寸 / 侧栏宽度 / 样式表（main.__on_show）

    #: 「安全启动」下会被置为 ``False`` 的键（:func:`open_gui_without_setup` 用它）。
    #: ⚠️ 新增一个启动开关时**只改这一处**：安全启动自动跳过它，不必再动那个函数。
    #:
    #: ⚠️⚠️ **``SETUPS`` 不在这份清单里**（2026-11-03 按用户要求改）：``setups.setup_ui()``
    #: 虽然属于「装配」，但对安全启动**同样需要** —— 通知、变量浏览器、设置页、插件面板、
    #: 登录页、反馈、读取 ReadMe 这一整块都在里面，关掉之后界面会是一副「残废」的样子，
    #: 用户也就失去了「用界面修好东西」的入口（而这正是安全启动的用途）。所以安全启动下
    #: **照常执行 setups**，只跳过那些「读用户数据 / 可能出问题」的项（输出历史、标签页、
    #: 界面状态、插件、自检）。要让 setups 也跳过，显式传 ``run_setups=False``。
    SKIP_IN_SAFE_START = (HISTORY, TABS, PLUGINS, INIT_CHECK, UI_STATE)

    #: 安全启动下**显式放行**（仍会执行）的键 —— 与上面那份清单一起写进 ``app_data``，
    #: 让 :func:`start_option` 的「显式内存键优先」给出正确结论。
    #: ⚠️ 这是**显式**写成 ``True``，而不是「不写、靠默认」：不写的话，用户在「设置」里存的
    #: ``run_setups='No'`` 之类会把它关掉，而安全启动的本意是「用默认的、别碰用户数据」。
    KEEP_IN_SAFE_START = (SETUPS,)


def is_safe_start():
    """本次是不是「安全启动」（:func:`open_gui_without_setup` 打开的那种）."""
    from zmlx.system import app_data
    return app_data.get(_Startup.SAFE, False) is True


def start_option(key, default=True):
    """读取一个「启动时要不要加载」的开关：**显式内存键 > 安全启动 > 持久化 env > default**.

    所有 startup 开关都从这里取，``main.py`` 里不许再直接 ``app_data.get(...)`` 判断 ——
    只有一条取值链，才说得清「这次为什么没加载」。

    Args:
        key: ``app_data`` 里的键名，直接写字面量即可（如 ``'restore_console_output'`` /
            ``'run_plugins'``），与设置页里那份持久化开关同名。
        default: 什么都没设置过时返回的值（正常启动的默认行为：**加载**）。

    Returns:
        bool: 是否执行该项。

    ⚠️ 顺带兼容**持久化设置**：用户「设置 → 系统」里的 ``restore_console_output`` /
    ``restore_tabs`` 这类开关（``app_data.getenv``）仍然生效 —— 只看内存键会漏掉它们，
    而这两项过去本来就由它们控制。所以内存键取不到时再查一次 ``getenv``（``'No'`` 视为关），
    查不到才用 ``default``。
    """
    from zmlx.system import app_data
    value = app_data.get(key, None)
    if value is not None:
        return bool(value)
    if is_safe_start():
        return False
    try:
        env = app_data.getenv(key, default=None, ignore_empty=True)
    except Exception:
        env = None
    if env is not None:
        return str(env).strip().lower() not in ('no', 'false', '0', 'off')
    return default


def _put_start_options(**options):
    """把 ``options`` 里**不为 None** 的项写进 ``app_data``（``None`` = 不覆盖）."""
    from zmlx.system import app_data
    for key, value in options.items():
        if value is not None:
            app_data.put(key, value)


def open_gui_without_setup(argv=None, restore_console_output=None,
                           run_setups=True, run_plugins=None, restore_tabs=None,
                           init_check=None, restore_ui_state=None, keep_cwd=True):
    """**安全启动**：打开界面，但本次尽量少加载（跳过输出历史 / 插件 / 标签页 / …）.

    与 :func:`open_gui` 的差别只有「加载多少」，界面本身完全一样，所以任何一项出问题
    （历史读坏、插件报错）都不会再影响「能不能打开界面」。

    ⚠️ ``setups`` **照常执行**（2026-11-03 按用户要求定）：通知、变量浏览器、设置页、
    插件面板、登录页、反馈……整块界面装配都在 ``setups.setup_ui()`` 里，它是「用界面
    把东西修好」的前提，安全启动**需要**它。要连它一起跳过，显式传 ``run_setups=False``。

    ⚠️ 这里写的是**运行时**状态（``app_data.put``，只活在内存里），不会写盘、也不会
    改变用户在「设置 → 系统 / 插件」里存的任何持久设置 —— 下一次 :func:`open_gui`
    照常全部加载。想永久不跑某个插件，请用「设置 → 插件」里那一行
    （``plugins.set_disabled``）。

    本次写下的开关（含义见 :func:`start_option`）:

    ===========================  ============================================
    键                           值 / 后果
    ===========================  ============================================
    ``safe_start``               ``True`` —— 总开关
    ``restore_console_output``   ``False`` —— **不恢复控制台输出历史**
    ``run_setups``               ``True``  —— **照常执行 ``setups.setup_ui()``**
    ``run_plugins``              ``False`` —— 不执行 ``plugins.load_all()``
    ``restore_tabs``             ``False`` —— 不重放上次的标签页
    ``init_check``               ``False`` —— 不弹「安装路径含中文」这类初始检查
    ``restore_ui_state``         ``False`` —— 不恢复窗口尺寸 / 侧栏宽度 / 样式表
    ===========================  ============================================

    逐项覆盖：除了 ``argv``，其余参数与上表里的键**同名**，传 ``None`` 表示沿用安全启动
    的默认值，例如「安全启动，但把输出历史也恢复」::

        open_gui_without_setup(restore_console_output=True)

    Args:
        argv: 传给界面的命令行参数（与原行为一致）。
        restore_console_output: 是否恢复控制台输出历史（安全启动默认 ``False``）。
        run_setups: 是否执行 ``setups.setup_ui()``（安全启动默认 **``True``**）。
        run_plugins: 是否执行 ``plugins.load_all()``（安全启动默认 ``False``）。
            新旧键名 ``run_plugins`` / ``run_setup`` 会写成同一个值。
        restore_tabs: 是否重放上次的标签页（安全启动默认 ``False``）。
        init_check: 是否做初始检查（安全启动默认 ``False``）。
        restore_ui_state: 是否恢复窗口尺寸 / 侧栏宽度 / 样式表（安全启动默认 ``False``）。
        keep_cwd: 是否保持调用方当前的工作目录（安全启动默认 ``True``，不读
            上次存的工作目录 —— 那是 ``main.execute`` 在 ``keep_cwd=False`` 时做的事）。
    """
    from zmlx.system import app_data
    app_data.put('argv', argv)
    app_data.put(_Startup.SAFE, True)
    # ① 安全启动下**仍要执行**的项（:attr:`_Startup.KEEP_IN_SAFE_START`）：默认值就是 True，
    #    显式传 False 仍然可以把它关掉（用于排查「是不是某个 setup 拖慢 / 出错」）
    for key in _Startup.KEEP_IN_SAFE_START:
        value = run_setups if key == _Startup.SETUPS else True
        app_data.put(key, True if value is None else bool(value))
    # ② 安全启动下**不执行**的项（:attr:`_Startup.SKIP_IN_SAFE_START`）：`None` → False
    for key, value in zip(_Startup.SKIP_IN_SAFE_START,
                          (restore_console_output, restore_tabs, run_plugins,
                           init_check, restore_ui_state)):
        app_data.put(key, False if value is None else bool(value))
    # ⚠️ ``run_plugins`` / ``run_setup`` 是**同一个开关**的新旧两个名字（2026-10-22 改名；
    #    旧名是 ``zml_gui_setup.py`` 那个文件名的残留）：两个都写，是因为还可能有别处的
    #    旧版 ``main.py`` 只读旧名，旧名保留到 2027-10-22 删。值已在 ② 里定好。
    app_data.put('run_setup', bool(app_data.get(_Startup.PLUGINS, False)))  # 旧名（兼容）
    # ⚠️ **只有安全启动才保持当前工作目录**：``keep_cwd=False`` 会让 ``main.execute``
    #    去读 ``env/current_work_directory``（上一次的工作目录），安全启动不该碰它；
    #    正常启动（``open_gui``）仍是原来的 ``False``。
    gui.execute(func=lambda: proc_argv(argv), keep_cwd=keep_cwd,
                close_after_done=False, add_history=False)


def test():
    import sys
    open_gui(sys.argv)


if __name__ == "__main__":
    test()
