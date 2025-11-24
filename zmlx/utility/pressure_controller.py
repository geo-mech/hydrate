from zmlx.base.zml import Seepage, Interp1


class PressureController(Seepage.CellData):
    """
    压力控制器。给定一个Cell，可以在每一步update的时候，动态调整该Cell内的流体(或者修改pore)，从而使得该Cell内的压力等于目标压力。
    用以辅助以给定的压力进行生产。
    """

    def __init__(self, cell, t, p, modify_pore=False):
        """
        设置检测的Cell并且拷贝其中的流体.
            需要给定从时间t到压力p的数据. 后续需要用插值来获得给定时刻的压力，所以这个曲线必须给定足够大的范围
            当modify_pore为True的时候，将尝试通过修改pore来达到维持压力的效果(不能保证成功).
        """
        super(PressureController, self).__init__()
        self.cell = cell
        self.clone(cell)  # 存储拷贝
        assert len(t) == len(p) and len(t) >= 2
        self.t = t
        self.p = p
        self.t2p = Interp1(x=t, y=p)
        self.modify_pore = modify_pore

    def _get_p(self, t):
        """
        返回给定时刻的目标压力
        """
        if t <= self.t[0]:
            return self.p[0]
        elif t >= self.t[-1]:
            return self.p[-1]
        else:
            return self.t2p(t)

    def _update_by_modify_pore(self, t):
        """
        通过调整pore的方式来控制压力
        """
        target_fp = self._get_p(t)
        target_fv = max(0.0, self.cell.p2v(target_fp))
        dv = self.cell.fluid_vol - target_fv
        self.cell.v0 = max(0.0, self.cell.v0 + dv)

    def _update_by_modify_flu(self, t):
        """
        通过转移流体的方式来控制压力
        """
        # 获得当前的目标压力
        fp = self._get_p(t)
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

    def update(self, t, modify_pore=None):
        """
        给定时间，设置目标Cell的压力(通过调整其内部的流体)
        """
        if modify_pore is None:
            modify_pore = self.modify_pore
        if modify_pore:
            self._update_by_modify_pore(t)
        else:
            self._update_by_modify_flu(t)
