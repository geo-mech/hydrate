import timeit


class Timer:
    """
    用以辅助统计函数的执行耗时。对于每一个函数，都应该有一个key，来表示这个函数在内存存储的名字.
    -
        张召彬  2023-7-7
    """

    def __init__(self):
        """
        用一个空表（字典）来进行初始化. 字典的key是待统计的函数的名字，值为运行的次数和总耗时.
        """
        self.enabled = True
        self.key2nt = {}
        self.__key2t = {}

    def __str__(self):
        """
        将数据转化为字符串输出.
        """
        return f'{self.key2nt}'

    def __call__(self, key, func, *args, **kwargs):
        """
        调用一个函数，并且记录调用的cpu耗时，以及调用的次数. 返回函数的执行结果.
            注意，这个函数将抛出func运行的异常.
            func后面的参数将传递给func.
        """
        if self.enabled:
            cpu_t = timeit.default_timer()
            r = func(*args, **kwargs)
            cpu_t = timeit.default_timer() - cpu_t
            nt = self.key2nt.get(key, None)
            if nt is None:
                self.key2nt[key] = [1, cpu_t]
            else:
                nt[0] += 1
                nt[1] += cpu_t
            return r
        else:
            return func(*args, **kwargs)

    def beg(self, key):
        """
        开始一段测试
        """
        if self.enabled:
            self.__key2t[key] = timeit.default_timer()

    def end(self, key):
        """
        结束一段测试(并且记录)
        """
        if self.enabled:
            t0 = self.__key2t.get(key, None)
            if t0 is not None:
                cpu_t = timeit.default_timer() - t0
                nt = self.key2nt.get(key, None)
                if nt is None:
                    self.key2nt[key] = [1, cpu_t]
                else:
                    nt[0] += 1
                    nt[1] += cpu_t

    def clear(self):
        """
        清除所有的统计结果. （临时数据保留）
        """
        self.key2nt = {}


timer = Timer()


def test():
    """
    用以展示timer的使用方法
    """
    from time import sleep

    for i in range(3):
        print(i)

        timer('0', sleep, 0.01)
        timer(1, sleep, 0.02)

        timer.beg(2)
        sleep(0.1)
        timer.end(2)

        timer.beg('3')
        sleep(0.1)
        timer.end('3')

    print(timer)


if __name__ == '__main__':
    test()
