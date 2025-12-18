# ** desc = '两相流，流体注入驱替。这里，创建多个模型，并行地执行'

from zmlx import *
from zmlx.demo.others.liq_inj import show_model, create


def main():
    models = [create() for _ in range(5)]

    pool = ThreadPool()

    # 向前迭代
    for time in np.linspace(0, 3600 * 24 * 365, 5):
        print(f'target time = {time2str(time)}')
        seepage.iterate_until(*models, target_time=time, pool=pool)
        for model in models:
            show_model(model)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
