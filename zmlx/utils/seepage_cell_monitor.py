"""监测一个或一组 Cell 中流体质量的变化，记录累积产量与产率，支持保存与绘图.

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""


from zmlx.system import warn
from zmlx.exts import is_array, Seepage, np


def _get_mass(item):
    """返回给定流体各组分质量的 list（递归遍历 Cell 和 Fluid）。"""
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
    """Cell 流体质量监测器。

    监测指定 Cell（或一组 Cell）中各流体组分质量随时间的变化，
    记录累积产量和产率，支持保存到制表符分隔文件及可视化绘图。
    """

    def __init__(self, get_t, cell):
        """初始化监测器。

        构造时备份各 Cell 的初始流体质量作为基准。

        Args:
            get_t: 返回当前时间的回调函数（返回秒）。
            cell: 单个 Seepage.CellData 或其数组。
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
        """更新流体的质量变化记录。

        Args:
            dt: 记录数据的最小时间间隔 [s]（非计算步长）。
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
            warn(
                f'meet exception when update. err = {err}. function = {self.update}')

    def get_current_rate(self):
        """返回当前各组分产率。

        Returns:
            list[float] | None: 当前产率 (kg/s)，数据不足时返回 None。
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
        """返回累积产量数据。

        Args:
            index: 组分索引（None 时返回所有组分的总和）。

        Returns:
            (时间数组, 累积质量数组 [kg]) | None: 失败时返回 None。
        """
        try:
            if index is not None and index < len(self.vm):
                return self.vt, self.vm[index]
            vm = self.vm[0].copy()
            for i in range(1, len(self.vm)):
                vm += self.vm[i]
            if np is None:
                return self.vt, vm
            else:
                return np.array(self.vt), np.array(vm)
        except Exception as err:
            warn(
                f'meet exception when call function <{self.get_prod}>, err = <{err}>')
            return None

    def get_rate(self, index=None):
        """返回产率数据。

        Args:
            index: 组分索引（None 时返回所有组分的总和）。

        Returns:
            (时间数组, 产率数组 [kg/s]) | None: 失败时返回 None。
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
            warn(
                f'meet exception <{err}> when call function <{self.get_rate}>')
            return None

    def save(self, path):
        """将监测数据保存到文件（制表符分隔）。

        格式：第 1 列为时间 [s]，随后各列为各组分的累积产出质量 [kg]。

        Args:
            path: 文件路径（None 时无操作）。
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
            warn(
                f'meet exception <{err}> when call function <{self.save}>')

    def plot(self, index, caption=None, **kwargs):
        """同时显示累积产量曲线和产率曲线（已废弃）。

        请分别使用 ``plot_prod`` 和 ``plot_rate``。

        Args:
            index: 组分索引。
            caption: 图表标题前缀。
            **kwargs: 透传给 ``zmlx.plt.show_xy``。
        """
        try:
            self.plot_prod(
                index,
                caption=None if caption is None else caption + '_mass',
                **kwargs)
            self.plot_rate(
                index,
                caption=None if caption is None else caption + '_rate',
                **kwargs)
        except Exception as err:
            warn(
                f'meet exception <{err}> when call function <{self.plot}>')

    def plot_prod(self, index, caption=None, **kwargs):
        """显示累积产量曲线（时间单位为天，质量为 kg）。

        Args:
            index: 组分索引。
            caption: 图表标题。
            **kwargs: 透传给 ``zmlx.plt.show_xy``。
        """
        try:
            from zmlx.plt import show_xy
            x, y = self.get_prod(index)
            x = [xi / (3600 * 24) for xi in x]
            kw = {}
            if caption is None:
                caption = f'mass<{index}>'
            kw.update(caption=caption, xlabel='time/d', ylabel='kg')
            kw.update(kwargs)
            show_xy(x, y, **kw)
        except Exception as err:
            warn(
                f'meet exception <{err}> when call function <{self.plot_prod}>')

    def plot_rate(self, index, caption=None, **kwargs):
        """显示产率曲线（时间单位为天，产率为 kg/day）。

        Args:
            index: 组分索引。
            caption: 图表标题。
            **kwargs: 透传给 ``zmlx.plt.show_xy``。
        """
        try:
            from zmlx.plt import show_xy
            x, y = self.get_rate(index)
            x = [xi / (3600 * 24) for xi in x]
            y = [yi * (3600 * 24) for yi in y]
            kw = {}
            if caption is None:
                caption = f'rate<{index}>'
            kw.update(caption=caption, xlabel='time/d', ylabel='kg/day')
            kw.update(kwargs)
            show_xy(x, y, **kw)
        except Exception as err:
            warn(
                f'meet exception <{err}> when call function <{self.plot_rate}>')
