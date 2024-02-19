import multiprocessing
import time


def apply_async(tasks, processes=None, sleep=None):
    """
    并行地执行多个任务.
        其中tasks存储需要执行的多个任务(其中每一个task都是一个dict，并需要定义func, args和kwds).
            特别需要注意，这个func需要是一个全局函数，否则会报错;
        processes为线程的数量，默认为cpu的数量.
        sleep为调用一个休眠的时间，主要用来确保所有的进程不会被同时调用，给出一定的时间差.
    ---
        since 2024-2-19
    """
    if processes is None:
        processes = multiprocessing.cpu_count()

    # 创建pool来进行并行计算.
    with multiprocessing.Pool(processes=processes) as pool:
        results = []
        for task in tasks:
            # 读取函数和参数
            func = task.get('func', None)
            assert func is not None
            args = task.get('args', [])
            kwds = task.get('kwds', {})
            # 使用 apply_async() 异步执行
            results.append(pool.apply_async(func=func, args=args, kwds=kwds,
                                            error_callback=lambda x: print(f'Error: {x}')))
            if sleep is not None:
                assert sleep >= 0
                time.sleep(sleep)
        # 返回计算的结果.
        return [res.get() for res in results]


def create_async(func, args=None, kwds=None):
    """
    创建一个任务. 注意函数func需要是全局函数(不能是函数内部定义的函数或者一个lambda)
    """
    task = {'func': func}
    if args is not None:
        task['args'] = args
    if kwds is not None:
        task['kwds'] = kwds
    return task


def _func(x, n):
    """
    用于测试的函数
    """
    time.sleep(0.2)
    return x ** n


def _test():
    res = apply_async([create_async(_func, args=[x], kwds={'n': 2}) for x in range(10)])
    print(res)


if __name__ == '__main__':
    _test()

