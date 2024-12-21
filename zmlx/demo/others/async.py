# ** desc = '测试：并行的执行多个任务。注意，此脚本必须作为Python的主程序执行'

from zmlx.alg.apply_async import *


def func(idx):
    """
    用于测试的函数
    """
    print(f'idx = {idx}, now = {datetime.datetime.now()}')
    time.sleep(3)
    return idx ** 2


def test(n):
    tasks = [create_async(func, kwds={'idx': idx}) for idx in range(n)]
    t1 = timeit.default_timer()
    res = apply_async(tasks, processes=n)
    print(f'res = {res}')
    print(f'n = {n}, time = {timeit.default_timer() - t1}')


if __name__ == '__main__':
    test(100)
