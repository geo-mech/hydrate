from zmlx.ui.console_api import console


class GuiBuffer:
    def __init__(self):
        self.__gui = []

    def command(self, *args, **kwargs):
        """
        执行命令
        """
        if len(self.__gui) > 0:
            return self.__gui[-1].command(*args, **kwargs)
        else:
            return None

    def push(self, the_gui):
        """
        压入gui的实例
        """
        assert hasattr(the_gui, 'command')
        self.__gui.append(the_gui)

    def pop(self):
        """
        弹出最后一个gui的实例
        """
        if len(self.__gui) > 0:
            return self.__gui.pop()
        else:
            return None

    def exists(self):
        """
        是否存在gui的实例
        """
        return len(self.__gui) > 0

    def __bool__(self):
        """
        是否存在gui的实例
        """
        return self.exists()

    def get(self):
        """
        返回最后一个gui实例
        """
        if len(self.__gui) > 0:
            return self.__gui[-1]
        else:
            return None

    def break_point(self):
        """
        添加一个断点，用于暂停以及安全地终止
        """
        self.command(break_point=True)

    # 函数的别名<为了兼容之前的代码>
    breakpoint = break_point

    class Agent:
        def __init__(self, the_gui, name):
            self.gui = the_gui
            self.name = name

        def __call__(self, *args, **kwargs):
            if self.gui is not None:
                return self.gui.command(self.name, *args, **kwargs)
            else:
                return console.command(self.name, *args, **kwargs)

    def __getattr__(self, name):
        return GuiBuffer.Agent(self.get(), name)

    def execute(self, func, keep_cwd=True, close_after_done=True, args=None,
                kwargs=None, disable_gui=False, run_setup=True):
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
            from zmlx.ui.main_window import execute
            return execute(fx, keep_cwd=keep_cwd,
                           close_after_done=close_after_done,
                           run_setup=run_setup)
        except Exception as err:
            print(f'call gui failed: {err}')
            return fx()

    def __call__(self, *args, **kwargs):
        """
        尝试在gui模式下运行给定的函数.
        """
        return self.execute(*args, **kwargs)


gui = GuiBuffer()


def information(*args, **kwargs):
    break_point()
    return gui.information(*args, **kwargs)


def question(info):
    break_point()
    return gui.question(info)


def plot(*args, **kwargs):
    """
    调用matplotlib执行绘图操作
    """
    gui_only = kwargs.pop('gui_only', False)
    if gui_only and not gui.exists():
        return
    break_point()
    gui.plot(*args, **kwargs)


def break_point():
    """
    添加一个gui的断点，从而在gui执行的过程中，可以控制暂停和终止
    """
    gui.break_point()


def gui_exec(*args, **kwargs):
    """
    调用gui来执行一个函数，并返回函数的执行结果
    """
    return gui.execute(*args, **kwargs)
