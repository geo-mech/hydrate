# ** desc = 'matplotlib绘图示例'

from zmlx import *


def heavy_work(count=1000):
    from time import sleep
    x = np.linspace(0, 15, 100)
    for idx in range(count):
        gui.progress(label='执行进度', val_range=[0, count], value=idx,
                     visible=True)
        gui.break_point()
        sleep(0.02)
        print(f'step = {idx}/{count}')

        x += 1
        y = np.sin(x)

        def on_figure(fig):
            ax = fig.add_subplot()
            ax.plot(x, y)

        plot(on_figure, clear=True, caption='sin(x)')
    gui.progress(visible=False)


if __name__ == '__main__':
    gui.execute(heavy_work, close_after_done=False)
