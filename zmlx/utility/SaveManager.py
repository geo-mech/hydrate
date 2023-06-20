# -*- coding: utf-8 -*-


import os
from zmlx.alg.make_fname import make_fname
import warnings


class SaveManager:
    """
    用以管理在迭代的过程中以一定的时间间隔来保存数据
    """

    def __init__(self, folder=None, dtime=None, get_time=None, save=None, ext=None, time_unit=None, always_save=True):
        """
        folder: 存储的目录 (当folder为None的时候，则传入save函数的路径也为None。当folder为空字符串时，将保存到当前路径)
        dtime: 可以是一个函数<或者一个具体的数值>，来返回不同时刻输出的时间间隔(采用和get_time函数一样的单位)
        get_time: 返回模型的当前时间
        ext: 为文件的扩展名<需要包含点>
        time_unit: 为显示的时间的单位（一个字符串）;
        always_save: 即便在路径为None的时候，也尝试运行save函数 (传递给save的path参数将为None)

        备注：
            部分函数依赖SaveManager执行的save函数不需要指定path，这些save函数需要在path为None的时候调用。因此，参数
            always_save的默认值必须为True，否则这些语句将无法正确执行。
            2023-6-13
        """

        assert isinstance(folder, str) or folder is None
        self.folder = folder
        if hasattr(dtime, '__call__'):
            self.dtime = dtime
        else:
            self.dtime = lambda time: dtime
        self.get_time = get_time
        assert hasattr(save, '__call__'), f'save should be a function that receive argument <path>'
        self.save = save
        assert isinstance(ext, str) or ext is None
        self.ext = ext
        assert isinstance(time_unit, str) or time_unit is None
        self.time_unit = time_unit
        self.time_last_save = -1.0e100  # 上一次正确存储的时间
        self.always_save = always_save  # 即便path为None也要调用save函数

    def __call__(self, check_dt=True):
        """
        尝试执行一次保存操作。当check_dt为False的时候，则不检查时间间隔
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
        path = make_fname(time=current_t, folder=self.folder, ext=self.ext,
                          unit=self.time_unit)
        try:
            # 将save函数在保护中运行，确保save函数的异常不会波及全局
            if path is not None or self.always_save:
                self.save(path)
                self.time_last_save = current_t
        except Exception as err:
            warnings.warn(f'meet exception when save. function = {self.save}. error = {err}')


if __name__ == '__main__':
    t = 0
    m = SaveManager(folder='.', dtime=lambda x: x * 0.1,
                    get_time=lambda: t,
                    save=lambda s: print(s), ext='.txt')
    while t < 100:
        m()
        t += 0.1
