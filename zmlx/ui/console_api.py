import zmlx.alg.sys as warnings

from zml import log

try:
    import matplotlib.pyplot as plt
except Exception as e:
    log(text=f'{e}', tag='matplotlib_import_error')
    plt = None


class ConsoleApi:
    def __init__(self):
        self.__commands = dict(about=self.show_all, information=self.show_all,
                               question=self.question, plot=self.plot,
                               progress=self.do_nothing)

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
            fname = kwargs.get('fname')
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
        cmd = self.__commands.get(name)
        if cmd is not None:
            return cmd(*args, **kwargs)
        else:
            print(f'function: {name}(args={args}, kwargs={kwargs})')
            return None


console = ConsoleApi()
