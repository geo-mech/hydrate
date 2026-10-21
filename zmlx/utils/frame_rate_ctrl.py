"""帧率限制器，确保界面更新不超过指定频率.

Modified by Claude, 2026-08-12
"""

import timeit


class FrameRateCtrl:
    """帧率限制器。

    包装界面绘图的回调函数，控制两次更新之间的最小时间间隔，
    从而限制帧率不超过设定值。统计总调用次数与实际执行次数。
    """

    def __init__(self, update=None, rate=20):
        """初始化帧率控制器。

        Args:
            update: 更新界面时执行的回调函数（接收 ``*args, **kwargs``）。
            rate: 目标帧率（必须大于 0）。
        """
        self.last_time = timeit.default_timer() - 2.0e11
        self.this_time = self.last_time + 1.0e11  # 确保首次调用成功
        self.update = update
        self.rate = rate
        self.times_show = 0
        self.times_call = 0

    def __call__(self, *args, **kwargs):
        """按帧率限制调用内核函数。

        Args:
            *args: 传递给 ``update`` 的位置参数。
            **kwargs: 传递给 ``update`` 的关键词参数。

        Returns:
            bool: 本次是否真正执行了更新。
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
        """实时的帧率。

        Returns:
            float | None: 基于最后一次调用间隔计算的帧率，首次调用后有效。
        """
        if self.last_time is not None and self.this_time is not None:
            return 1.0 / max(1.0e-5, self.this_time - self.last_time)
        return None
