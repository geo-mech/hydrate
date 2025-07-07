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
        def __init__(self, api, name):
            self.api = api
            self.name = name

        def __call__(self, *args, **kwargs):
            if self.api is not None:
                return self.api.command(self.name, *args, **kwargs)
            else:
                print(f'args={args}, kwargs={kwargs}')
                return None

    def __getattr__(self, name):
        return GuiBuffer.Agent(self.get(), name)

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
        except Exception as err:
            print(f'call gui failed: {err}')
            return fx()


gui = GuiBuffer()


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


def plot_no_gui(kernel, **kwargs):
    """
    在非GUI模式下绘图(或者显示并阻塞程序执行，或者输出文件但不显示)
    """
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        from zml import log
        log(text=f'{e}', tag='matplotlib_import_error')
        plt = None

    if kernel is None or plt is None:
        return
    try:
        fig = plt.figure()
        kernel(fig)
        fname = kwargs.get('fname')
        if fname is not None:
            dpi = kwargs.get('dpi', 300)
            fig.savefig(fname=fname, dpi=dpi)
            plt.close()
        else:
            plt.show()
    except Exception as err:
        import zmlx.alg.sys as warnings
        warnings.warn(f'meet exception <{err}> when run <{kernel}>')


def plot(*args, **kwargs):
    """
    调用matplotlib执行绘图操作
    """
    gui_only = kwargs.pop('gui_only', False)
    if gui.exists():
        break_point()
        gui.plot(*args, **kwargs)
    else:
        if not gui_only:
            plot_no_gui(*args, **kwargs)


def gui_exec(*args, **kwargs):
    """
    调用gui来执行一个函数，并返回函数的执行结果
    """
    return gui.execute(*args, **kwargs)


def open_gui(argv=None):
    """
    打开gui
    """
    from zml import app_data
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
    from zml import app_data
    app_data.put('argv', argv)
    app_data.put('restore_tabs', False)
    app_data.put('run_setup', False)
    gui.execute(keep_cwd=False, close_after_done=False)


def test():
    import sys
    open_gui(sys.argv)


if __name__ == "__main__":
    test()
