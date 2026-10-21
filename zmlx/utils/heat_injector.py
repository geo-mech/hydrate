"""热量注入器，支持恒定功率与恒定温度两种注入模式.

Modified by Claude, 2026-08-12
"""

from zmlx.algs import get_velocity_after_slowdown_by_viscosity


class HeatInjector:
    """热量注入器。

    对指定 Cell 注入热量，支持两种模式：
    - 恒定功率：按功率直接提升温度（``power * dt / (mc)``）。
    - 恒定温度：按传热系数向目标温度靠拢（带粘性减速）。
    当 ``power`` 不为 None 且大于 0 时优先使用恒定功率模式。
    """

    def __init__(self, cell, ca_mc, ca_t, power=None, temp=None, cond=None):
        """初始化热注入器。

        Args:
            cell: 目标 Cell 对象（支持 ``get_attr`` / ``set_attr``）。
            ca_mc: 比热属性 ID（``mc`` = 质量 × 比热）。
            ca_t: 温度属性 ID。
            power: 恒定注入功率 [W]（None 表示不使用恒定功率模式）。
            temp: 恒定目标温度 [K]（仅恒定温度模式使用）。
            cond: 传热系数（仅恒定温度模式使用）。
        """
        self.cell = cell
        self.ca_mc = ca_mc
        self.ca_t = ca_t
        self.power = power
        self.temp = temp
        self.cond = cond

    def work(self, dt):
        """执行指定时间的热量注入。

        Args:
            dt: 工作时间 [s]（<= 0 时直接返回）。

        工作流程：
            1. 若 ``power`` 大于 0，执行恒定功率注入。
            2. 否则若 ``temp`` 和 ``cond`` 均有效且 ``cond > 0``，
               执行恒定温度注入（向目标温度靠拢）。
        """
        if dt <= 0:
            return

        if self.power is not None:
            if self.power > 0:
                # 恒定功率注入：直接将能量转化为温度增量
                t0 = self.cell.get_attr(self.ca_t)
                t1 = t0 + self.power * dt / self.cell.get_attr(self.ca_mc)
                self.cell.set_attr(self.ca_t, t1)
                return

        if self.temp is not None and self.cond is not None:
            if self.cond > 0:
                # 恒定温度注入：按传热系数向目标温度靠拢
                t0 = self.cell.get_attr(self.ca_t)
                mc = self.cell.get_attr(self.ca_mc)
                v0 = t0 - self.temp  # 温度差，相当于速度
                a0 = v0 * self.cond / mc  # 按照当前的温度差，单位时间内温度的改变
                v1 = get_velocity_after_slowdown_by_viscosity(
                    v0, a0, dt)  # 之后的温度差
                t1 = self.temp + v1
                self.cell.set_attr(self.ca_t, t1)
                return
