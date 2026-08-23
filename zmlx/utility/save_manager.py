"""周期性自动保存管理器，在迭代过程中按时间间隔保存数据并自动创建目录.

Modified by Claude, 2026-08-12
"""

import os

import zmlx.alg.sys as warnings
from zmlx.alg.fsys import make_fname


class SaveManager:
    """迭代过程中的自动保存管理器。

    在每次调用时检查时间间隔，满足条件则调用 ``save(path)`` 保存模型状态。
    自动创建目标目录，文件名包含时间。

    备注:
        部分函数依赖 SaveManager 执行的 save 函数不需要指定 path，
        这些 save 函数需要在 path 为 None 时也能正常工作。因此参数
        ``always_save`` 的默认值必须为 True。
        （2023-6-13）
    """

    def __init__(self, folder=None, dtime=None, get_time=None, save=None,
                 ext=None, time_unit=None, always_save=True,
                 unit_length=None):
        """初始化保存管理器。

        Args:
            folder: 存储目录（None 时 path 也为 None；空字符串存到当前路径）。
            dtime: 保存间隔函数（接收当前时间并返回间隔）或固定数值。
            get_time: 返回模型当前时间的回调函数。
            save: 保存回调函数（接收 ``path`` 参数，必须可调用）。
            ext: 文件扩展名（需包含点，如 ``".txt"``）。
            time_unit: 显示的时间单位字符串（如 ``"y"``、``"d"``、``"h"``）。
            always_save: 即使 path 为 None 也调用 save 函数。
            unit_length: 每个时间单位对应的秒数；
                          None 时默认为 1.0（保持兼容）；
                          ``'auto'`` 时由 ``time_unit`` 自动推算。
        """

        assert isinstance(folder, str) or folder is None
        self.folder = folder
        if callable(dtime):
            self.dtime = dtime
        else:
            self.dtime = lambda time: dtime
        self.get_time = get_time
        assert callable(
            save), f'save should be a function that receive argument <path>'
        self.save = save
        assert isinstance(ext, str) or ext is None
        self.ext = ext
        if self.ext is not None:
            assert isinstance(self.ext, str)
            if len(self.ext) > 0:
                assert self.ext[0] == '.'
        assert isinstance(time_unit, str) or time_unit is None
        self.time_unit = time_unit
        self.time_last_save = -1.0e100  # 上一次正确存储的时间
        self.always_save = always_save  # 即便path为None也要调用save函数

        # 确定每个时间单位的时间的长度   Since 2025-3-21
        if unit_length is None:
            self.unit_length = 1.0  # 默认不调整，从而保持对之前代码的兼容性
        elif unit_length == 'auto':
            self.unit_length = SaveManager.get_unit_length(time_unit)
        else:
            assert isinstance(unit_length, (int, float))
            assert unit_length > 0.0
            self.unit_length = unit_length  # 时间单位的数值(秒数)，在生成文件名的时候会使用到.

    @staticmethod
    def get_unit_length(time_unit):
        """返回时间单位对应的秒数。

        Args:
            time_unit: ``'y'``（年）、``'d'``（天）、``'h'``（小时）或其他。

        Returns:
            float: 该时间单位的秒数，未知单位返回 1.0。
        """
        if time_unit == 'y':
            return 365.25 * 24.0 * 3600.0
        elif time_unit == 'd':
            return 24.0 * 3600.0
        elif time_unit == 'h':
            return 3600.0
        else:
            return 1.0

    def __call__(self, check_dt=True):
        """尝试执行一次保存操作。

        Args:
            check_dt: False 时不检查时间间隔，强制执行保存。
        """
        if self.save is None or self.get_time is None:
            return
        current_t = self.get_time()
        if check_dt:
            dtime = self.dtime(current_t)
            if current_t - self.time_last_save < dtime:
                return
        if self.folder is not None:
            if len(self.folder) > 0:
                if not os.path.exists(self.folder):
                    os.makedirs(self.folder, exist_ok=True)
        path = make_fname(
            time=current_t / self.unit_length, folder=self.folder,
            ext=self.ext,
            unit=self.time_unit)
        try:
            # 将save函数在保护中运行，确保save函数的异常不会波及全局
            if path is not None or self.always_save:
                self.save(path)
                self.time_last_save = current_t
        except Exception as err:
            warnings.warn(
                f'meet exception when save. function = {self.save}. error = {err}')


if __name__ == '__main__':
    t = 0
    m = SaveManager(folder='.', dtime=lambda x: x * 0.1,
                    get_time=lambda: t,
                    save=lambda s: print(s), ext='.txt', time_unit='s',
                    unit_length=None)
    while t < 100:
        m()
        t += 0.1
