import threading


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


def test():
    tasks = []
    for idx in range(20):
        tasks.append(create_task(func=lambda x: x**2, args=[idx]))
    res = apply_threads(tasks)
    print(res)


if __name__ == "__main__":
    test()
