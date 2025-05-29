import zmlx.alg.sys as warnings

from zml import is_array, Seepage, np


def _get_mass(item):
    """
    返回给定流体各个组分的质量<将所有的流体作为一个list>.
    """
    if isinstance(item, Seepage.CellData):  # 返回单个cell
        result = []
        for flu in item.fluids:
            result += _get_mass(flu)
        return result
    elif isinstance(item, Seepage.FluData):  # 返回单个流体的各个组分
        if item.component_number == 0:
            return [item.mass, ]
        else:
            result = []
            for i in range(item.component_number):
                result += _get_mass(item.get_component(i))
            return result
    else:  # 此时，获取多个cell内的流体之和
        if len(item) == 0:
            return 0
        result = _get_mass(item[0])
        for i in range(1, len(item)):
            vm = _get_mass(item[i])
            assert len(vm) == len(result)
            for j in range(len(vm)):
                result[j] += vm[j]
        return result


class SeepageCellMonitor:
    """
    用以监视给定的一个Cell或者一组Cell中流体质量的变化
    """

    def __init__(self, get_t, cell):
        """
        初始化：给定的<get_t>应为一个函数，用以返回时间(时间的单位应该是秒)；cell为Seepage的一个Cell对象(或者多个Cell对象);
        """
        self.get_t = get_t
        if is_array(cell):
            self.cells = cell
            assert len(self.cells) > 0
        else:
            self.cells = [cell]
        # 备份初始的质量
        self.vm0 = _get_mass(self.cells)
        # 初始化数组
        self.vt = [self.get_t()]
        self.vm = [[0.0] for i in range(len(self.vm0))]

    def update(self, dt=1.0e-6):
        """
        更新记录的流体的质量变化. 其中dt为更新数据的最小的时间间隔 <并非计算时候的时间步长>
        """
        try:
            assert dt > 0, 'The time interval should be positive'
            time = self.get_t()
            if time >= self.vt[-1] + dt:
                self.vt.append(time)
                vm = _get_mass(self.cells)
                assert len(vm) == len(self.vm0)
                vm = [vm[i] - self.vm0[i] for i in
                      range(len(vm))]  # 当前的质量和初始的差异
                assert len(vm) == len(self.vm)
                for i in range(len(self.vm)):
                    self.vm[i].append(vm[i])  # 附加到list
        except Exception as err:
            warnings.warn(
                f'meet exception when update. err = {err}. function = {self.update}')

    def get_current_rate(self):
        """
        返回当前时刻，各个组分的产出的速率(质量速率)
        """
        if len(self.vm) == 0:
            return None

        count = len(self.vm[0])
        if count < 2:
            return None

        # 最后一步记录的产出量
        dm = [max(self.vm[i][-1] - self.vm[i][-2], 0.0) for i in
              range(len(self.vm))]

        # 时间步长
        assert len(self.vt) == count
        dt = max(self.vt[-1] - self.vt[-2], 1.0e-20)

        # 返回质量rate
        return [m / dt for m in dm]

    def get_prod(self, index=None):
        """
        返回一组<时间>; 与时间对应的累积生产的<质量>
        """
        try:
            if index is not None and index < len(self.vm):
                return self.vt, self.vm[index]
            vm = self.vm[0]
            for i in range(1, len(self.vm)):
                vm += self.vm[i]
            if np is None:
                return self.vt, vm
            else:
                return np.array(self.vt), np.array(vm)
        except Exception as err:
            warnings.warn(
                f'meet exception when call function <{self.get_prod}>, err = <{err}>')
            return None

    def get_rate(self, index=None):
        """
        返回一组<时间>; 与时间对应的单位时间的生产<质量>
        """
        try:
            x, y = self.get_prod(index)
            dx = [x[i] - x[i - 1] for i in range(1, len(x))]
            dy = [y[i] - y[i - 1] for i in range(1, len(y))]
            q = [dy[i] / dx[i] for i in range(len(dx))]
            if np is None:
                return x[1:], q
            else:
                return np.array(x[1:]), np.array(q)
        except Exception as err:
            warnings.warn(
                f'meet exception <{err}> when call function <{self.get_rate}>')
            return None

    def save(self, path):
        """
        将记录的结果保存到文件。
        格式：
            第1列为时间，随后各列为各个流体产出的质量<给定时刻的质量减去初始时刻的质量>
        """
        try:
            if path is None:
                return
            with open(path, 'w') as file:
                for step in range(len(self.vt)):
                    file.write(f'{self.vt[step]}\t')
                    for ind in range(len(self.vm)):
                        file.write(f'{self.vm[ind][step]}\t')
                    file.write('\n')
        except Exception as err:
            warnings.warn(
                f'meet exception <{err}> when call function <{self.save}>')

    def plot(self, index, caption=None, **kwargs):
        """
        同时显示累积生产曲线和生产速率曲线：已废弃
        """
        try:
            self.plot_prod(index,
                           caption=None if caption is None else caption + '_mass',
                           **kwargs)
            self.plot_rate(index,
                           caption=None if caption is None else caption + '_rate',
                           **kwargs)
        except Exception as err:
            warnings.warn(
                f'meet exception <{err}> when call function <{self.plot}>')

    def plot_prod(self, index, caption=None, **kwargs):
        """
        显示累积生产曲线
        """
        try:
            from zmlx.plt.fig2 import plot_xy
            x, y = self.get_prod(index)
            x = [xi / (3600 * 24) for xi in x]
            kw = {}
            if caption is None:
                caption = f'mass<{index}>'
            kw.update(caption=caption, xlabel='time/d', ylabel='kg')
            kw.update(kwargs)
            plot_xy(x, y, **kw)
        except Exception as err:
            warnings.warn(
                f'meet exception <{err}> when call function <{self.plot_prod}>')

    def plot_rate(self, index, caption=None, **kwargs):
        """
        显示生产速率曲线
        """
        try:
            from zmlx.plt.fig2 import plot_xy
            x, y = self.get_rate(index)
            x = [xi / (3600 * 24) for xi in x]
            y = [yi * (3600 * 24) for yi in y]
            kw = {}
            if caption is None:
                caption = f'rate<{index}>'
            kw.update(caption=caption, xlabel='time/d', ylabel='kg/day')
            kw.update(kwargs)
            plot_xy(x, y, **kw)
        except Exception as err:
            warnings.warn(
                f'meet exception <{err}> when call function <{self.plot_rate}>')
