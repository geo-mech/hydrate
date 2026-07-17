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

参考 demo 文件（如 zmlx/demo/flow_1ph/darcy_1d.py）了解更多示例。
"""

from typing import Optional, Tuple, List, Union

from zmlx.system import app_data, is_headless


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
        """
        将函数标记为直接调用，而不是通过gui调用
        Args:
            key: 函数的名称
        Returns:
            函数代理对象
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

        if not disable_gui:
            from zmlx.system import is_headless
            if is_headless():
                disable_gui = True
                print('headless mode, disable gui')

        if self.exists() or disable_gui:
            return fx()

        try:
            from zmlx.ui.main import execute
            return execute(fx, keep_cwd=keep_cwd,
                           close_after_done=close_after_done,
                           add_history=add_history)
        except Exception as execute_err:
            print(f'call gui failed: {execute_err}')
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


def _plot_no_gui(kernel, *args, fname=None, dpi=300, caption=None, tight_layout=None, suptitle=None,
                 on_top=None,  # 兼容gui下的参数
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
            from zmlx.system import is_headless
            if is_headless() and caption is None:
                caption = "default_figure"
            if caption is not None:
                import datetime
                import os
                from zmlx.plt._save import get_plt_save_path
                from zmlx.system import make_parent
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
        import zmlx.alg.sys as warnings
        warnings.warn(f'meet exception <{err}> when run <{kernel}>')
        return None


def plot(kernel, *args, gui_only=False, gui_mode=None,
         fname=None, dpi=300,
         **kwargs):
    """
    调用matplotlib执行绘图操作. 如果需要处于gui_mode下面绘图，但是当前不是gui模式，则打开gui界面绘图(此功能仅供测试使用)
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
        None
    """

    def plot_with_gui():
        try:
            gui.break_point()
            return gui.plot(kernel, *args, fname=fname, dpi=dpi, **kwargs)
        except Exception as plot_err:
            print(f'plot failed: {plot_err}')
            return None

    if gui.exists():
        return plot_with_gui()

    # 此时，没有处在gui中
    if gui_mode:
        from zmlx.system import is_headless
        if is_headless():
            gui_mode = False
            print('headless mode, disable gui')

    if gui_mode:  # 创建窗口来运行
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
        overwritable=True
):
    """
    在gui菜单添加一个操作项
    """
    if gui.exists():
        gui.add_action(
            menu=menu, text=text, name=name, slot=slot,
            icon=icon, tooltip=tooltip, shortcut=shortcut,
            on_toolbar=on_toolbar,
            is_enabled=is_enabled,
            is_visible=is_visible,
            overwritable=overwritable
        )


def proc_argv(argv=None):
    from zmlx.alg import fsys
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


def open_gui_without_setup(argv=None):
    """
    打开gui
    """
    from zmlx.system import app_data
    app_data.put('argv', argv)
    app_data.put('restore_tabs', False)
    app_data.put('run_setup', False)
    gui.execute(func=lambda: proc_argv(argv), keep_cwd=False, close_after_done=False, add_history=False)


def test():
    import sys
    open_gui(sys.argv)


if __name__ == "__main__":
    test()
