from zml import *
from zmlx.alpha import seepage


class CellKeys:
    """
    定义Cell的属性
    """

    def __init__(self, model):
        assert isinstance(model, Seepage)

        self.s = seepage.reg_cell_key(model, 's')

        self.x0 = seepage.reg_cell_key(model, 'x0')
        self.x1 = seepage.reg_cell_key(model, 'x1')
        self.x2 = seepage.reg_cell_key(model, 'x2')
        self.x3 = seepage.reg_cell_key(model, 'x3')

        self.y0 = seepage.reg_cell_key(model, 'y0')
        self.y1 = seepage.reg_cell_key(model, 'y1')
        self.y2 = seepage.reg_cell_key(model, 'y2')
        self.y3 = seepage.reg_cell_key(model, 'y3')

        self.z0 = seepage.reg_cell_key(model, 'z0')
        self.z1 = seepage.reg_cell_key(model, 'z1')
        self.z2 = seepage.reg_cell_key(model, 'z2')
        self.z3 = seepage.reg_cell_key(model, 'z3')

        self.v0 = seepage.reg_cell_key(model, 'v0')
        self.fp = seepage.reg_cell_key(model, 'fp')

        self.ny = seepage.reg_cell_key(model, 'ny')
        self.fl = seepage.reg_cell_key(model, 'fl')
        self.fh = seepage.reg_cell_key(model, 'fh')
        self.G = seepage.reg_cell_key(model, 'G')
        self.mu = seepage.reg_cell_key(model, 'mu')

        self.idx12 = [self.x0, self.x1, self.x2, self.x3,
                      self.y0, self.y1, self.y2, self.y3,
                      self.z0, self.z1, self.z2, self.z3]

        self.kw12 = create_dict(ca_x0=self.x0, ca_x1=self.x1, ca_x2=self.x2, ca_x3=self.x3,
                                ca_y0=self.y0, ca_y1=self.y1, ca_y2=self.y2, ca_y3=self.y3,
                                ca_z0=self.z0, ca_z1=self.z1, ca_z2=self.z2, ca_z3=self.z3)


class FaceKeys:
    """
    定义Face的属性
    """
    def __init__(self, model):
        assert isinstance(model, Seepage)
        self.g0 = seepage.reg_face_key(model, 'g0')
        # face的种类.
        #    1. 主裂缝在水平方向的连接;
        #    2. 主裂缝在竖直方向的连接;
        #    3. 不同的DFN之间的连接;
        self.tag = seepage.reg_face_key(model, 'tag')


class FracKeys:
    """
    裂缝单元的属性
    """
    id = 0
    tmp = 1
