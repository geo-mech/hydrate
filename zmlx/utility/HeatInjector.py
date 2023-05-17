# -*- coding: utf-8 -*-


from zml import *


class HeatInjector:
    """
    热量注入：可以用恒定功率和恒定温度两种注入的方式
    """

    def __init__(self, cell, ca_mc, ca_t, power=None, temp=None, cond=None):
        """
        初始化
        """
        self.cell = cell
        self.ca_mc = ca_mc
        self.ca_t = ca_t
        self.power = power
        self.temp = temp
        self.cond = cond

    def work(self, dt):
        """
        工作指定的时间
        """
        if dt <= 0:
            return

        if self.power is not None:
            if self.power > 0:
                """
                此时，执行恒定功率的注入
                """
                t0 = self.cell.get_attr(self.ca_t)
                t1 = t0 + self.power * dt / self.cell.get_attr(self.ca_mc)
                self.cell.set_attr(self.ca_t, t1)
                return

        if self.temp is not None and self.cond is not None:
            if self.cond > 0:
                """
                此时，执行恒定温度的注入
                """
                t0 = self.cell.get_attr(self.ca_t)
                mc = self.cell.get_attr(self.ca_mc)
                v0 = t0 - self.temp  # 温度差，相当于速度
                a0 = v0 * self.cond / mc  # 按照当前的温度差，单位时间内温度的改变
                v1 = Alg.get_velocity_after_slowdown_by_viscosity(v0, a0, dt)  # 之后的温度差
                t1 = self.temp + v1
                self.cell.set_attr(self.ca_t, t1)
                return
