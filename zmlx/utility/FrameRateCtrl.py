# -*- coding: utf-8 -*-


import timeit


class FrameRateCtrl:
    """
    给定界面绘图的内核函数，并控制更新的帧率
    """
    def __init__(self, update=None, rate=20):
        self.__lastShow = None
        self.__thisShow = timeit.default_timer() - 1.0e11  # 确保首次调用成功
        self.__update = update
        self.rate = rate
        self.timesShow = 0
        self.timesCall = 0

    def __call__(self, *args, **kwargs):
        """
        调用内核函数(控制帧率来调用); 返回是否真正执行;
        """
        assert self.rate > 1.0e-10, f'帧率必须大于0. rate = {self.rate}'
        self.timesCall += 1
        if timeit.default_timer() - self.__thisShow < 1.0 / self.rate:
            return False
        else:
            self.__lastShow = self.__thisShow
            self.__thisShow = timeit.default_timer()
            self.timesShow += 1
            if self.__update is not None:
                self.__update(*args, **kwargs)
            return True

    @property
    def realtime_rate(self):
        """
        实时的帧率
        """
        if self.__lastShow is not None and self.__thisShow is not None:
            return 1.0 / max(1.0e-5, self.__thisShow - self.__lastShow)

