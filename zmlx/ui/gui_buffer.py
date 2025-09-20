class GuiBuffer:
    def __init__(self):
        self.__api = None

    def command(self, *args, **kwargs):
        """
        执行命令
        """
        if self.__api is not None:
            return self.__api.command(*args, **kwargs)
        else:
            print(f'gui.command while api is None. args={args}, kwargs={kwargs}')
            return None

    def set(self, api):
        """
        设置api
        """
        self.__api = api
        print(f'Gui Set: {self.__api}')

    def get(self):
        """
        返回api
        """
        return self.__api

    def exists(self):
        """
        是否存在api (处于gui模式下)
        """
        return self.__api is not None

    def __bool__(self):
        """
        是否存在api (处于gui模式下)
        """
        return self.exists()

    def break_point(self):
        """
        添加一个断点，用于暂停以及安全地终止
        """
        self.command(break_point=True)

    # 函数的别名<为了兼容之前的代码>
    breakpoint = break_point

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
        返回一个函数代理
        """
        return GuiBuffer.Agent(self, name)

    def set_agent(self, key, **kwargs):
        """
        添加函数关键词的代理(给定默认值)
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
        将函数标记为直接调用
        """
        return self.set_agent(key, is_direct=True)

    def execute(
            self, func=None, keep_cwd=True, close_after_done=True,
            args=None,
            kwargs=None, disable_gui=False):
        """
        尝试在gui模式下运行给定的函数 func
        """

        def fx():
            if func is not None:
                x = args if args is not None else []
                y = kwargs if kwargs is not None else {}
                return func(*x, **y)
            else:
                return None

        if self.exists() or disable_gui:
            return fx()

        try:
            from zmlx.ui.main import execute
            return execute(fx, keep_cwd=keep_cwd,
                           close_after_done=close_after_done)
        except Exception as execute_err:
            print(f'call gui failed: {execute_err}')
            return fx()


gui = GuiBuffer()

try:
    from zmlx.exts.base import app_data

    app_data.put('gui', gui)
except Exception as err:
    print(err)


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


def plot_no_gui(kernel, *args, fname=None, dpi=300, caption=None, **kwargs):
    """
    在非GUI模式下绘图(或者显示并阻塞程序执行，或者输出文件但不显示).
    """
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        from zmlx.exts.base import log
        log(text=f'{e}', tag='matplotlib_import_error')
        plt = None

    if kernel is None or plt is None:
        return None
    try:
        fig = plt.figure()
        kernel(fig, *args, **kwargs)
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

    if gui_mode:  # 创建窗口来运行
        return gui.execute(plot_with_gui, close_after_done=False)

    if gui_only:
        return None
    else:
        return plot_no_gui(kernel, *args, fname=fname, dpi=dpi, **kwargs)


def gui_exec(*args, **kwargs):
    """
    调用gui来执行一个函数，并返回函数的执行结果
    """
    return gui.execute(*args, **kwargs)


def open_gui(argv=None):
    """
    打开gui
    """
    from zmlx.exts.base import app_data
    app_data.put('argv', argv)
    # 是否需要恢复标签
    app_data.put('restore_tabs',
                 app_data.getenv('restore_tabs', default='Yes') != 'No')
    # 是否初始检查
    app_data.put('init_check',
                 app_data.getenv('init_check', default='Yes') != 'No')

    gui.execute(keep_cwd=False, close_after_done=False)


def open_gui_without_setup(argv=None):
    """
    打开gui
    """
    from zmlx.exts.base import app_data
    app_data.put('argv', argv)
    app_data.put('restore_tabs', False)
    app_data.put('run_setup', False)
    gui.execute(keep_cwd=False, close_after_done=False)


def test():
    import sys
    open_gui(sys.argv)


if __name__ == "__main__":
    test()
