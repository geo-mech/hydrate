"""压力控制器，按预设的时间-压力曲线维持指定 Cell 的压力，用于定压生产.

Modified by Claude, 2026-08-12
"""

from zmlx.exts import Seepage, Interp1


class PressureController(Seepage.CellData):
    """压力控制器。

    继承自 ``Seepage.CellData``，在每一步 ``update`` 时动态调整 Cell 内的流体
    （或修改 pore），使 Cell 压力等于时间-压力曲线定义的目标值。
    支持两种控制模式：转移流体（默认）和修改孔隙体积。
    """

    def __init__(self, cell, t, p, modify_pore=False):
        """初始化压力控制器。

        拷贝目标 Cell 的流体状态作为"储罐"，通过向 Cell 中注入/从 Cell 中抽取
        流体来维持目标压力。时间-压力曲线通过 ``Interp1`` 插值，需覆盖足够大的范围。

        Args:
            cell: 目标 Cell（Seepage.CellData）。
            t: 时间序列（长度 >= 2）。
            p: 目标压力序列 [Pa]，与 ``t`` 长度相同。
            modify_pore: True 时通过修改 pore 控制压力（不保证成功），
                          False 时通过转移流体控制。
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
        """返回给定时刻的目标压力。超出曲线范围时钳制到端点值。"""
        if t <= self.t[0]:
            return self.p[0]
        elif t >= self.t[-1]:
            return self.p[-1]
        else:
            return self.t2p(t)

    def _update_by_modify_pore(self, t):
        """通过调整 pore 控制压力。"""
        target_fp = self._get_p(t)
        target_fv = max(0.0, self.cell.p2v(target_fp))
        dv = self.cell.fluid_vol - target_fv
        self.cell.v0 = max(0.0, self.cell.v0 + dv)

    def _update_by_modify_flu(self, t):
        """通过转移流体控制压力。"""
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
        """按目标压力调整 Cell。

        Args:
            t: 当前时间 [s]。
            modify_pore: 是否通过修改 pore 控制（None 时使用构造时的设定）。
        """
        if modify_pore is None:
            modify_pore = self.modify_pore
        if modify_pore:
            self._update_by_modify_pore(t)
        else:
            self._update_by_modify_flu(t)
