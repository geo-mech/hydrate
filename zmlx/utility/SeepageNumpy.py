"""
用以实现Seepage和numpy之间的数据交换
"""
from ctypes import c_double, POINTER

import numpy as np

from zml import Seepage, is_array
from zmlx.alg.numpy import get_pointer


class SeepageNumpy:
    """
    用以Seepage类和Numpy之间交换数据的适配器
    """

    class Cells:
        """
        用以批量读取或者设置Cells的属性
        """

        def __init__(self, model):
            assert isinstance(model, Seepage)
            assert np is not None
            self.model = model

        def get(self, index, buf=None):
            """
            Cell属性。index的含义参考 Seepage.cells_write
            """
            if np is not None:
                if buf is None:
                    buf = np.zeros(shape=self.model.cell_number, dtype=float)
                else:
                    assert len(buf) == self.model.cell_number
                self.model.cells_write(pointer=get_pointer(buf, c_double), index=index)
                return buf

        def set(self, index, buf):
            """
            Cell属性。index的含义参考 Seepage.cells_write
            """
            if not is_array(buf):
                self.model.cells_read(value=buf, index=index)
                return
            if np is not None:
                assert len(buf) == self.model.cell_number
                self.model.cells_read(pointer=get_pointer(buf, c_double), index=index)

        def get_attr(self, *args, **kwargs):
            return self.get(*args, **kwargs)

        def set_attr(self, *args, **kwargs):
            return self.set(*args, **kwargs)

        @property
        def x(self):
            """
            各个Cell的x坐标
            """
            return self.get(-1)

        @x.setter
        def x(self, value):
            """
            各个Cell的x坐标
            """
            self.set(-1, value)

        @property
        def y(self):
            """
            各个Cell的y坐标
            """
            return self.get(-2)

        @y.setter
        def y(self, value):
            """
            各个Cell的y坐标
            """
            self.set(-2, value)

        @property
        def z(self):
            """
            各个Cell的z坐标
            """
            return self.get(-3)

        @z.setter
        def z(self, value):
            """
            各个Cell的z坐标
            """
            self.set(-3, value)

        @property
        def v0(self):
            """
            各个Cell的v0属性(孔隙的v0，参考Cell定义)
            """
            return self.get(-4)

        @v0.setter
        def v0(self, value):
            self.set(-4, value)

        @property
        def k(self):
            """
            各个Cell的k属性(孔隙的k，参考Cell定义)
            """
            return self.get(-5)

        @k.setter
        def k(self, value):
            self.set(-5, value)

        @property
        def g_pos(self):
            """
            inner_prod(gravity, pos)
            """
            return self.get(-6)

        @property
        def fluid_mass(self):
            """
            所有流体的总的质量<只读>
            """
            return self.get(-10)

        @property
        def fluid_vol(self):
            """
            所有流体的总的体积<只读>
            """
            return self.get(-11)

        @property
        def pre(self):
            """
            流体的压力(根据总的体积和孔隙弹性来计算)
            """
            return self.get(-12)

    class Faces:
        """
        用以批量读取或者设置Faces的属性
        """

        def __init__(self, model):
            assert isinstance(model, Seepage)
            assert np is not None
            self.model = model

        def get(self, index, buf=None):
            """
            读取各个Face的属性
            """
            if np is not None:
                if buf is None:
                    buf = np.zeros(shape=self.model.face_number, dtype=float)
                else:
                    assert len(buf) == self.model.face_number
                self.model.faces_write(pointer=get_pointer(buf, c_double), index=index)
                return buf

        def set(self, index, buf):
            """
            设置各个Face的属性
            """
            if not is_array(buf):
                self.model.faces_read(value=buf, index=index)
                return
            if np is not None:
                assert len(buf) == self.model.face_number
                self.model.faces_read(pointer=get_pointer(buf, c_double), index=index)

        def get_attr(self, *args, **kwargs):
            return self.get(*args, **kwargs)

        def set_attr(self, *args, **kwargs):
            return self.set(*args, **kwargs)

        @property
        def cond(self):
            """
            各个Face位置的导流系数
            """
            return self.get(-1)

        @cond.setter
        def cond(self, value):
            """
            各个Face位置的导流系数
            """
            self.set(-1, value)

        @property
        def dr(self):
            return self.get(-2)

        @dr.setter
        def dr(self, value):
            self.set(-2, value)

        def get_dv(self, index=None, buf=None):
            """
            上一次迭代经过Face流体的体积.
            """
            if index is None:
                return self.get(-19, buf=buf)
            else:
                assert 0 <= index < 9, f'index = {index} is not permitted'
                return self.get(-10 - index, buf=buf)

        @property
        def dist(self):
            """
            face两侧的cell的距离
            """
            return self.get(-3)

    class Fluids:
        """
        用以批量读取或者设置某一种流体的属性
        """

        def __init__(self, model, fluid_id):
            assert isinstance(model, Seepage)
            assert np is not None
            self.model = model
            self.fluid_id = fluid_id

        def get(self, index, buf=None):
            """
            返回属性
            """
            if np is not None:
                if buf is None:
                    buf = np.zeros(shape=self.model.cell_number, dtype=float)
                else:
                    assert len(buf) == self.model.cell_number
                self.model.fluids_write(fluid_id=self.fluid_id, index=index,
                                        pointer=get_pointer(buf, c_double))
                return buf

        def set(self, index, buf):
            """
            设置属性
            """
            if not is_array(buf):
                self.model.fluids_read(fluid_id=self.fluid_id, value=buf, index=index)
                return
            if np is not None:
                assert len(buf) == self.model.cell_number
                self.model.fluids_read(fluid_id=self.fluid_id, index=index,
                                       pointer=get_pointer(buf, c_double))

        def get_attr(self, *args, **kwargs):
            return self.get(*args, **kwargs)

        def set_attr(self, *args, **kwargs):
            return self.set(*args, **kwargs)

        @property
        def mass(self):
            """
            流体质量
            """
            return self.get(-1)

        @mass.setter
        def mass(self, value):
            self.set(-1, value)

        @property
        def den(self):
            """
            流体密度
            """
            return self.get(-2)

        @den.setter
        def den(self, value):
            self.set(-2, value)

        @property
        def vol(self):
            """
            流体体积
            """
            return self.get(-3)

        @vol.setter
        def vol(self, value):
            self.set(-3, value)

        @property
        def vis(self):
            """
            流体粘性系数
            """
            return self.get(-4)

        @vis.setter
        def vis(self, value):
            self.set(-4, value)

    def __init__(self, model):
        self.model = model

    @property
    def cells(self):
        return SeepageNumpy.Cells(model=self.model)

    @property
    def faces(self):
        return SeepageNumpy.Faces(model=self.model)

    def fluids(self, *fluid_id):
        """
        返回给定流体或者组分的属性适配器
        """
        return SeepageNumpy.Fluids(model=self.model, fluid_id=fluid_id)


def as_numpy(model):
    """
    返回利用numpy来读写属性的接口
    """
    return SeepageNumpy(model)
