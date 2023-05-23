from zml import *
from zmlx.alpha import seepage
from zmlx.alg.seg_intersection import seg_intersection


class CellAttrs(seepage.CellAttrs):
    def __init__(self, model):
        assert isinstance(model, Seepage)
        super().__init__(model=model)
        self.x0 = model.reg_cell_key('x0')
        self.x1 = model.reg_cell_key('x1')
        self.x2 = model.reg_cell_key('x2')
        self.x3 = model.reg_cell_key('x3')

        self.y0 = model.reg_cell_key('y0')
        self.y1 = model.reg_cell_key('y1')
        self.y2 = model.reg_cell_key('y2')
        self.y3 = model.reg_cell_key('y3')

        self.z0 = model.reg_cell_key('z0')
        self.z1 = model.reg_cell_key('z1')
        self.z2 = model.reg_cell_key('z2')
        self.z3 = model.reg_cell_key('z3')

        # 裂缝面积
        self.fs = model.reg_cell_key('fs')
        self.tag = model.reg_cell_key('tag')

    def set_rect3(self, cell, x0, y0, z0, x1, y1, z1):
        """
        设置纵向三维的属性
        """
        cell.set_attr(self.x0, x0)
        cell.set_attr(self.x1, x0)
        cell.set_attr(self.x2, x1)
        cell.set_attr(self.x3, x1)

        cell.set_attr(self.y0, y0)
        cell.set_attr(self.y1, y0)
        cell.set_attr(self.y2, y1)
        cell.set_attr(self.y3, y1)

        cell.set_attr(self.z0, z0)
        cell.set_attr(self.z1, z1)
        cell.set_attr(self.z2, z0)
        cell.set_attr(self.z3, z1)

    def get_f3(self, cell):
        return cell.get_attr(self.x0), cell.get_attr(self.y0), cell.get_attr(self.z0), cell.get_attr(
            self.x2), cell.get_attr(self.y2), cell.get_attr(self.z1)

    def intersected(self, cell1, cell2):
        """
        返回两个给定的竖直裂缝a和b是否相交
        """
        a = self.get_f3(cell1)
        b = self.get_f3(cell2)
        assert len(a) == 6 and len(b) == 6
        az0, az1 = a[2], a[5]
        bz0, bz1 = b[2], b[5]
        if max(bz0, bz1) <= min(az0, az1):
            return False
        if min(bz0, bz1) >= max(az0, az1):
            return False
        xy = seg_intersection(*a[0: 2], *a[3: 5], *b[0: 2], *b[3: 5])
        return xy is not None

    def get_fs(self, cell):
        """
        裂缝的面积
        """
        return cell.get_attr(self.fs)

    def set_fs(self, cell, fs):
        """
        裂缝的面积
        """
        cell.set_attr(self.fs, fs)

    def get_tag(self, cell):
        val = cell.get_attr(self.tag, min=-0.1, max=1000, default_val=None)
        if val is not None:
            return round(val)

    def set_tag(self, cell, value):
        cell.set_attr(self.tag, value)


class FaceAttrs(seepage.FaceAttrs):
    def __init__(self, model):
        assert isinstance(model, Seepage)
        super().__init__(model=model)
        self.tag = model.reg_face_key('tag')

    def get_tag(self, face):
        assert isinstance(face, Seepage.Face)
        val = face.get_attr(self.tag, min=-0.1, max=1000, default_val=None)
        if val is not None:
            return round(val)

    def set_tag(self, face, value):
        face.set_attr(self.tag, value)


FluAttrs = seepage.FluAttrs
