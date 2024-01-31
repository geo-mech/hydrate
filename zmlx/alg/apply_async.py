import datetime
import multiprocessing
import threading
import time
import timeit

processes_max = 60


def create_task(func, args=None, kwds=None):
    """
    创建一个任务
    """
    task = {'func': func}
    if args is not None:
        task['args'] = args
    if kwds is not None:
        task['kwds'] = kwds
    return task


def exec_task(task):
    # 读取函数和参数
    func = task.get('func', None)
    assert func is not None
    args = task.get('args', [])
    kwds = task.get('kwds', {})
    return func(*args, **kwds)


def exec_task_and_set_res(task, res, idx):
    res[idx] = exec_task(task)


def apply_threads(tasks):
    """
    利用多线程来并行地执行任务，返回执行的结果。
    需要注意的是，
        由于Python的全局解释器锁（GIL），即使使用多线程，Python的CPU密集型任务也不会实现真正的并行，
        只会交替执行。但对于I/O密集型任务或者进行外部系统调用（如调用C扩展函数释放GIL），
        多线程仍然可以提高性能
    """
    if len(tasks) == 0:
        return []

    results = [None, ] * len(tasks)
    threads = []

    for idx in range(len(tasks)):
        t = threading.Thread(target=exec_task_and_set_res, args=(tasks[idx], results, idx))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return results


def divide_list_into_parts(lst, n):
    # 计算列表长度
    total_elements = len(lst)
    # 使用整除得到每个子列表的基本元素数量
    base_size = total_elements // n
    # 使用取余得到剩余的元素数量
    remainder = total_elements % n

    # 初始化结果列表
    result = []
    # 初始化当前索引
    start_index = 0

    # 循环创建子列表
    for i in range(n):
        # 确定当前子列表的大小，前remainder个子列表会多一个元素
        if i < remainder:
            end_index = start_index + base_size + 1
        else:
            end_index = start_index + base_size
            # 切片操作获取子列表
        sub_list = lst[start_index:end_index]
        # 将子列表添加到结果列表中
        result.append(sub_list)
        # 更新下一个子列表的起始索引
        start_index = end_index

    return result


def apply_async(tasks, processes=None, sleep=None, use_thread=True):
    """
    并行地执行多个任务.
        其中tasks存储需要执行的多个任务(其中每一个task都是一个dict，并需要定义func, args和kwds).
            特别需要注意，这个func需要是一个全局函数，否则会报错;
            另外，传入的参数，也应该可以在不同的进程之间传输。在zml中定义的依赖handle的类，因为handle作为
            指针，不可以在不同的进程之间共享，因此，这些类的示例，都不能作为参数.
        processes为线程的数量，默认为cpu的数量.
        sleep为调用一个休眠的时间，主要用来确保所有的进程不会被同时调用，给出一定的时间差.
    ---
        since 2024-2-19
    """
    if len(tasks) == 0:
        return []

    if processes is None:
        processes = multiprocessing.cpu_count()

    # 超过任务的数量是没有必要的
    processes = min(processes, len(tasks))

    if processes > processes_max:
        if use_thread:
            n_threads = round(processes / processes_max) + 1
            parts = divide_list_into_parts(tasks, n_threads)
            assert len(parts) == n_threads
            for part in parts:
                assert len(part) <= processes_max
            # 使用多个线程来创建进程
            vr = apply_threads([create_task(func=apply_async, kwds={'tasks': part,
                                                                    'processes': processes_max,
                                                                    'sleep': sleep,
                                                                    'use_thread': False}) for part in parts])
            assert len(vr) == n_threads
            # 最后，收集结果
            result = []
            for r in vr:
                assert isinstance(r, list)
                result = result + r
            return result
        else:
            processes = min(processes_max, processes)

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


def _func(idx, s=None):
    """
    用于测试的函数
    """
    print(f'idx = {idx}, now = {datetime.datetime.now()}')
    time.sleep(0.5 if s is None else s)
    return idx ** 2


def _test(n):
    tasks = [create_async(_func, kwds={'idx': idx, 's': 30}) for idx in range(n)]
    t1 = timeit.default_timer()
    res = apply_async(tasks, processes=n, use_thread=True)
    print(f'res = {res}')
    print(f'n = {n}, time = {timeit.default_timer() - t1}')


if __name__ == '__main__':
    _test(200)
