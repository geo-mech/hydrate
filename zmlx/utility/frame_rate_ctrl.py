import timeit


class FrameRateCtrl:
    """
    给定界面绘图的内核函数，并控制更新的帧率
    """

    def __init__(self, update=None, rate=20):
        """
        初始化，其中update为更新界面时执行的函数，rate为帧率(注意帧率必须大于0)
        """
        self.last_time = timeit.default_timer() - 2.0e11
        self.this_time = self.last_time + 1.0e11  # 确保首次调用成功
        self.update = update
        self.rate = rate
        self.times_show = 0
        self.times_call = 0

    def __call__(self, *args, **kwargs):
        """
        调用内核函数(控制帧率来调用); 返回是否真正尝试执行;
        """
        assert self.rate > 1.0e-10, f'帧率必须大于0. rate = {self.rate}'
        self.times_call += 1
        if timeit.default_timer() - self.this_time < 1.0 / self.rate:
            return False
        else:
            self.last_time = self.this_time
            self.this_time = timeit.default_timer()
            self.times_show += 1
            if self.update is not None:
                self.update(*args, **kwargs)
            return True

    @property
    def realtime_rate(self):
        """
        实时的帧率
        """
        if self.last_time is not None and self.this_time is not None:
            return 1.0 / max(1.0e-5, self.this_time - self.last_time)
