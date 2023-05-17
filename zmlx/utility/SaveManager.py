# -*- coding: utf-8 -*-


import os

from zmlx.alg.make_fname import make_fname


class SaveManager:
    """
    用以管理在迭代的过程中以一定的时间间隔来保存数据
    """

    def __init__(self, folder=None, dtime=None, get_time=None, save=None, ext=None, time_unit=None, always_save=False):
        """
        folder为存储的目录;
        其中dtime可以是一个函数<或者一个具体的数值>，来返回不同时刻输出的时间间隔(采用和get_time函数一样的单位)
        get_time返回模型的当前时间
        ext为文件的扩展名<需要包含点>
        time_unit为显示的时间的单位;
        注意：如果folder为None，那么函数仍会运行，但传递给save的path参数将为None
        """
        self.folder = folder
        if hasattr(dtime, '__call__'):
            self.dtime = dtime
        else:
            self.dtime = lambda time: dtime
        self.get_time = get_time
        self.save = save
        self.ext = ext
        self.time_unit = time_unit
        self.time_last_save = -1.0e100
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
            assert len(self.folder) > 0
            if not os.path.exists(self.folder):
                os.makedirs(self.folder, exist_ok=True)
        path = make_fname(time=current_t, folder=self.folder, ext=self.ext,
                          unit=self.time_unit)
        try:
            if path is not None or self.always_save:
                self.save(path)
        except Exception as err:
            print(f'{__file__}: {err}. \npath = {path}')
        self.time_last_save = current_t


if __name__ == '__main__':
    t = 0
    m = SaveManager(folder='.', dtime=lambda t: t * 0.1,
                    get_time=lambda: t,
                    save=lambda s: print(s), ext='.txt')
    while t < 100:
        m()
        t += 0.1
