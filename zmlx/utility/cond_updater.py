"""导流系数更新器（已废弃）。

``__call__`` 与 ``update_g0`` 抛出 ``NotImplementedError``，
如需此功能可用 numpy 实现。``set_v0`` / ``set_g0`` / ``set_s1`` / ``set_fk``
等初始化方法仍可正常使用。

Modified by Claude, 2026-08-12
"""

from zmlx.exts import Seepage, Vector


class CondUpdater:
    """Face 导流系数更新器（已废弃）。

    原本用于管理基准孔隙体积、基准导流系数和渗透率折减，
    核心更新方法已废弃，如需此功能请用 numpy 重新实现。
    """

    def __init__(self, v0=None, g0=None, krf=None):
        """构造导流系数更新器。

        Args:
            v0: 基准孔隙体积（Vector）。
            g0: 基准导流系数（Vector）。
            krf: 渗透率折减因子。
        """
        self.v0 = v0
        self.g0 = g0
        self.krf = krf
        self.fk = None
        self.s1 = None

    def __call__(self, model, relax_factor=1.0):
        """更新 Face cond（已废弃）。

        Raises:
            NotImplementedError: 此功能已废弃。
        """
        raise NotImplementedError
        assert isinstance(model, Seepage)
        if self.v0 is not None and self.g0 is not None and self.krf is not None:
            model.update_cond(ca_v0=self.v0, fa_g0=self.g0, fa_igr=self.krf,
                              relax_factor=relax_factor)

    def set_v0(self, model):
        """将此刻各 Cell 的流体体积保存为 v0。

        注意：将全部流体视为可流动；如有固体组分请先移除。

        Args:
            model: 渗流模型（Seepage）。
        """
        assert isinstance(model, Seepage)
        self.v0 = Vector(value=[cell.fluid_vol for cell in model.cells])

    def set_g0(self, model):
        """将此刻各 Face 的 cond 保存为 g0。

        Args:
            model: 渗流模型（Seepage）。
        """
        assert isinstance(model, Seepage)
        self.g0 = Vector(value=[face.cond for face in model.faces])

    def set_s1(self, mesh):
        """计算 Face 在长度为 1 时的面积（area / length）。

        Args:
            mesh: 网格。
        """
        self.s1 = Vector(value=[face.area / face.length for face in mesh.faces])

    def set_fk(self, model, mesh):
        """根据当前 cond 反算 Face 位置的渗透率。

        Args:
            model: 渗流模型（Seepage）。
            mesh: 网格。
        """
        vs1 = [face.area / face.length for face in mesh.faces]
        count = min(len(vs1), model.face_number)
        self.fk = Vector(
            value=[model.get_face(i).cond / vs1[i] for i in range(count)])

    # core.use(None, 'update_g0', c_void_p, c_void_p, c_void_p)

    def update_g0(self, fk=None, s1=None):
        """更新 g0（已废弃）。

        Raises:
            NotImplementedError: 此功能已废弃，可用 numpy 重新实现。
        """
        if fk is None:
            fk = self.fk
        if s1 is None:
            s1 = self.s1
        if isinstance(fk, Vector) and isinstance(s1, Vector) and isinstance(
                self.g0, Vector):
            raise NotImplementedError
            # now, let  g0 = k * s1
            # core.update_g0(self.g0.handle, fk.handle, s1.handle)
            # 注意，此类暂时废弃了，如果必要，可以利用numpy来实现它所有的功能
