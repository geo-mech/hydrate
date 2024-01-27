import warnings

from zml import create_dict

try:
    import matplotlib.pyplot as plt
except Exception as _err:
    plt = None
    warnings.warn(f'cannot import matplotlib in zml. error = {_err}')


class ConsoleApi:
    def __init__(self):
        self.__commands = create_dict(about=self.show_all, information=self.show_all,
                                      question=self.question, plot=self.plot, progress=self.do_nothing)

    @staticmethod
    def do_nothing(*args, **kwargs):
        pass

    @staticmethod
    def question(info):
        """
        询问信息。返回是否True
        """
        y = input(f"{info} input 'y' or 'Y' to continue: ")
        return y == 'y' or y == 'Y'

    @staticmethod
    def show_all(*args, **kwargs):
        """
        显示所有的参数
        """
        print(f'args={args}, kwargs={kwargs}')

    @staticmethod
    def plot(kernel, **kwargs):
        """
        在非GUI模式下绘图(或者显示并阻塞程序执行，或者输出文件但不显示)
        """
        if kernel is None or plt is None:
            return
        try:
            fig = plt.figure()
            kernel(fig)
            fname = kwargs.get('fname', None)
            if fname is not None:
                dpi = kwargs.get('dpi', 300)
                fig.savefig(fname=fname, dpi=dpi)
                plt.close()
            else:
                plt.show()
        except Exception as err:
            warnings.warn(f'meet exception <{err}> when run <{kernel}>')

    def command(self, name, *args, **kwargs):
        """
        当GUI不存在的时候来执行默认的命令
        """
        cmd = self.__commands.get(name, None)
        if cmd is not None:
            return cmd(*args, **kwargs)
        else:
            print(f'function: {name}(args={args}, kwargs={kwargs})')


console = ConsoleApi()


class GuiBuffer:
    def __init__(self):
        self.__gui = []

    def command(self, *args, **kwargs):
        if len(self.__gui) > 0:
            return self.__gui[-1].command(*args, **kwargs)

    def push(self, gui):
        assert hasattr(gui, 'command')
        self.__gui.append(gui)

    def pop(self):
        if len(self.__gui) > 0:
            return self.__gui.pop()

    def exists(self):
        return len(self.__gui) > 0

    def get(self):
        if len(self.__gui) > 0:
            return self.__gui[-1]

    def break_point(self):
        """
        添加一个断点，用于暂停以及安全地终止
        """
        self.command(break_point=True)

    # 函数的别名<为了兼容之前的代码>
    breakpoint = break_point

    class Agent:
        def __init__(self, gui, name):
            self.gui = gui
            self.name = name

        def __call__(self, *args, **kwargs):
            if self.gui is not None:
                return self.gui.command(self.name, *args, **kwargs)
            else:
                return console.command(self.name, *args, **kwargs)

    def __getattr__(self, name):
        return GuiBuffer.Agent(self.get(), name)

    def execute(self, func, keep_cwd=True, close_after_done=True, args=None, kwargs=None, disable_gui=False):
        """
        尝试在gui模式下运行给定的函数 func
        """

        def fx():
            if func is not None:
                x = args if args is not None else []
                y = kwargs if kwargs is not None else {}
                return func(*x, **y)

        if self.exists() or disable_gui:
            return fx()
        try:
            from zmlx.ui.MainWindow import execute
            return execute(fx, keep_cwd=keep_cwd, close_after_done=close_after_done)
        except Exception as e:
            print(f'call gui failed: {e}')
            return fx()

    def __call__(self, *args, **kwargs):
        """
        尝试在gui模式下运行给定的函数.
        """
        return self.execute(*args, **kwargs)


gui = GuiBuffer()


def information(*args, **kwargs):
    return gui.information(*args, **kwargs)


def question(info):
    return gui.question(info)


def plot(*args, **kwargs):
    """
    调用matplotlib执行绘图操作
    """
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
