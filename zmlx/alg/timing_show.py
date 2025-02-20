import time
import timeit


def timing_show(key, func, *args, **kwargs):
    """
    执行函数，并且显示执行的耗时. 主要用于模型初始化过程中，显示那些耗时的操作
    """
    print(f'{key} ... ', end='')
    t_beg = timeit.default_timer()
    res = func(*args, **kwargs)
    t_end = timeit.default_timer()
    print(' succeed. time used = %.2f s' % (t_end - t_beg))
    return res


def test():
    timing_show('test1', time.sleep, 1)
    timing_show('test2', time.sleep, 2)


if __name__ == '__main__':
    test()
