# -*- coding: utf-8 -*-


from zml import *


class PressureController(Seepage.CellData):
    """
    压力控制器。给定一个Cell，可以在每一步update的时候，动态调整该Cell内的流体，从而使得该Cell内的压力等于目标压力。
    用以辅助以给定的压力进行生产。
    """

    def __init__(self, cell, t, p):
        """
        设置检测的Cell并且拷贝其中的流体. 需要给定从时间t到压力p的数据.
        后续需要用插值来获得给定时刻的压力。所以这个曲线必须给定足够大的范围
        """
        super(PressureController, self).__init__()
        self.cell = cell
        self.clone(cell)
        assert len(t) == len(p) and len(t) >= 2
        self.t = t
        self.p = p
        self.t2p = Interp1(x=t, y=p)

    def update(self, t):
        """
        给定时间，设置目标Cell的压力(通过调整其内部的流体)
        """
        # 获得当前的目标压力
        if t <= self.t[0]:
            fp = self.p[0]
        elif t >= self.t[-1]:
            fp = self.p[-1]
        else:
            fp = self.t2p(t)
        fv = max(0, self.cell.p2v(fp))

        v0 = 0
        for f in self.cell.fluids:
            v0 += f.vol

        v1 = 0
        for f in self.fluids:
            v1 += f.vol

        fv = min(v0 + v1, fv)
        dv = v0 - fv  # 需要拿走的体积

        buf = Seepage.FluData()

        # 转移流体，达到目标体积
        for i in range(self.fluid_number):
            va = self.cell.get_fluid(i).vol + self.get_fluid(i).vol
            if dv > 0:
                assert dv <= v0
                buf.clone(self.cell.get_fluid(i))
                buf.mass *= (dv / v0)
                self.cell.get_fluid(i).mass *= (1 - dv / v0)
                self.get_fluid(i).add(buf)
            else:
                assert dv >= -v1
                buf.clone(self.get_fluid(i))
                buf.mass *= (-dv / v1)
                self.get_fluid(i).mass *= (1 + dv / v1)
                self.cell.get_fluid(i).add(buf)
            error = self.cell.get_fluid(i).vol + self.get_fluid(i).vol - va
            assert error / max(va, 1) <= 1.0e-10, f'error = {error}, va = {va}'
