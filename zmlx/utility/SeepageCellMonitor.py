import warnings

from zml import is_array


def get_mass_of_fluid(flu):
    """
    返回给定流体各个组分的质量<作为一个list>.
    """
    if flu.component_number == 0:
        return [flu.mass, ]
    else:
        result = []
        for i in range(flu.component_number):
            for m in get_mass_of_fluid(flu.get_component(i)):
                result.append(m)
        return result


def get_mass_in_cell(cell):
    """
    返回一个Cell内各个流体的质量
    """
    result = []
    for i in range(cell.fluid_number):
        for m in get_mass_of_fluid(cell.get_fluid(i)):
            result.append(m)
    return result


def get_mass_in_cells(cells):
    """
    返回多个Cell内所有的流体的质量和
    """
    if len(cells) == 0:
        return 0
    result = get_mass_in_cell(cells[0])
    for i in range(1, len(cells)):
        vm = get_mass_in_cell(cells[i])
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
        self.vm0 = get_mass_in_cells(self.cells)
        # 初始化数组
        self.vt = [self.get_t()]
        self.vm = [[0] for i in range(len(self.vm0))]

    def update(self, dt=1.0e-6):
        """
        更新记录的流体的质量变化. 其中dt为更新数据的最小的时间间隔 <并非计算时候的时间步长>
        """
        try:
            assert dt > 0, 'The time interval should be positive'
            time = self.get_t()
            if time >= self.vt[-1] + dt:
                self.vt.append(time)
                vm = get_mass_in_cells(self.cells)
                assert len(vm) == len(self.vm0)
                vm = [vm[i] - self.vm0[i] for i in range(len(vm))]
                assert len(vm) == len(self.vm)
                for i in range(len(self.vm)):
                    self.vm[i].append(vm[i])
        except Exception as err:
            warnings.warn(f'meet exception when update. err = {err}. function = {self.update}')

    def get_prod(self, index=None, np=None):
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
            warnings.warn(f'meet exception when call function <{self.get_prod}>, err = <{err}>')

    def get_rate(self, index=None, np=None):
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
            warnings.warn(f'meet exception <{err}> when call function <{self.get_rate}>')

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
            warnings.warn(f'meet exception <{err}> when call function <{self.save}>')

    def plot(self, index, **kwargs):
        """
        同时显示累积生产曲线和生产速率曲线：已废弃
        """
        try:
            self.plot_prod(index, **kwargs)
            self.plot_rate(index, **kwargs)
        except Exception as err:
            warnings.warn(f'meet exception <{err}> when call function <{self.plot}>')

    def plot_prod(self, index, **kwargs):
        """
        显示累积生产曲线
        """
        try:
            from zmlx.plt.plotxy import plotxy
            x, y = self.get_prod(index)
            x = [xi / (3600 * 24) for xi in x]
            kw = {}
            kw.update(caption=f'累积<{index}>', xlabel='time/d', ylabel='kg')
            kw.update(kwargs)
            plotxy(x, y, **kw)
        except Exception as err:
            warnings.warn(f'meet exception <{err}> when call function <{self.plot_prod}>')

    def plot_rate(self, index, **kwargs):
        """
        显示生产速率曲线
        """
        try:
            from zmlx.plt.plotxy import plotxy
            x, y = self.get_rate(index)
            x = [xi / (3600 * 24) for xi in x]
            y = [yi * (3600 * 24) for yi in y]
            kw = {}
            kw.update(caption=f'速率<{index}>', xlabel='time/d', ylabel='kg/day')
            kw.update(kwargs)
            plotxy(x, y, **kw)
        except Exception as err:
            warnings.warn(f'meet exception <{err}> when call function <{self.plot_rate}>')
