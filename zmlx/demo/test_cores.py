# ** desc = '测试计算机的多核性能'


from zmlx.demo.hyd_form import execute
from zmlx.alg.apply_async import *
import timeit
import numpy as np


def execute_t(*args, **kwargs):
    t1 = timeit.default_timer()
    execute(*args, **kwargs)
    t2 = timeit.default_timer()
    return t2 - t1


def run_test(n_task, step_max=500, parallel_enabled=False):
    """
    测试n_task个算例，每个算例计算step_max步骤，返回执行完毕的耗时;
    """
    assert n_task > 0
    tasks = []
    for idx in range(n_task):
        tasks.append(create_async(func=execute_t, kwds={'step_max': step_max,
                                                        'gui_mode': False,
                                                        'parallel_enabled': parallel_enabled}))
    t1 = timeit.default_timer()
    vt = apply_async(tasks, processes=len(tasks), use_thread=True)
    t2 = timeit.default_timer()
    return t2 - t1, sum(vt) / len(vt)


def test(result, vn, step_max=500, parallel_enabled=False):
    for n in vn:
        t1, t2 = run_test(n_task=n, step_max=step_max, parallel_enabled=parallel_enabled)
        with open(result, 'a') as file:
            file.write(f'{n}   {t1}   {t2}\n')
            file.flush()


def main():
    n = list(set([round(x) for x in 2 ** np.linspace(0, 10, 40)]))
    n = sorted(n)
    print(n)
    test('n2t.txt', n, step_max=200, parallel_enabled=False)


if __name__ == '__main__':
    main()
