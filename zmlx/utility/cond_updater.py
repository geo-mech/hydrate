from zml import Seepage, Vector


class CondUpdater:
    """
    用以更新Face的cond属性
    """

    def __init__(self, v0=None, g0=None, krf=None):
        """
        构造函数，后续必须添加必要的配置
        """
        self.v0 = v0
        self.g0 = g0
        self.krf = krf
        self.fk = None
        self.s1 = None

    def __call__(self, model, relax_factor=1.0):
        """
        更新模型中各个Cell中流体的总体积和v0的体积的比值，更新各个Face的cond属性
        """
        raise NotImplementedError
        assert isinstance(model, Seepage)
        if self.v0 is not None and self.g0 is not None and self.krf is not None:
            model.update_cond(ca_v0=self.v0, fa_g0=self.g0, fa_igr=self.krf,
                              relax_factor=relax_factor)

    def set_v0(self, model):
        """
        将此刻的流体体积设置为v0. 注意：这里将所有的流体都视为可以流动的。如果流体组分中有固体，那么请首先移除固体组分之后再调用此函数
        """
        assert isinstance(model, Seepage)
        self.v0 = Vector(value=[cell.fluid_vol for cell in model.cells])

    def set_g0(self, model):
        """
        将此刻的face.cond设置为g0
        """
        assert isinstance(model, Seepage)
        self.g0 = Vector(value=[face.cond for face in model.faces])

    def set_s1(self, mesh):
        """
        当Face两侧距离为折减为1的时候，Face的面积
        """
        self.s1 = Vector(value=[face.area / face.length for face in mesh.faces])

    def set_fk(self, model, mesh):
        """
        Face位置的渗透率（根据此刻的cond来计算）
        """
        vs1 = [face.area / face.length for face in mesh.faces]
        count = min(len(vs1), model.face_number)
        self.fk = Vector(
            value=[model.get_face(i).cond / vs1[i] for i in range(count)])

    # core.use(None, 'update_g0', c_void_p, c_void_p, c_void_p)

    def update_g0(self, fk=None, s1=None):
        """
        更新g0. 其中fk为渗透率属性，s1为Face的面积除以流动的距离；
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
