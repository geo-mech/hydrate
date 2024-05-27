import ctypes
from ctypes import c_void_p

from zml import Seepage, Vector, is_array


class FloatBuffer:
    """
    准备一个数据的缓冲区
    """

    def __init__(self, value, is_input=None, length=None):
        self.data = None
        self.pointer = None

        # 设置数据
        if value is None:
            assert is_input is not None and length is not None
            assert not is_input  # 此时，只能用于输出
            self.data = Vector(size=length)
            self.pointer = ctypes.cast(self.data.pointer, c_void_p)
            return
        elif isinstance(value, Vector):
            assert is_input is not None and length is not None
            if is_input:
                assert value.size == length
            else:
                value.size = length  # 输出，所以可以重新设置长度
            self.data = value
            self.pointer = ctypes.cast(self.data.pointer, c_void_p)
            return
        elif is_array(value):
            assert is_input is not None and length is not None
            if is_input:
                assert len(value) == length
                self.data = Vector(value=value)
                self.pointer = ctypes.cast(self.data.pointer, c_void_p)
                return
            else:
                # 作为输出，这并非一个可以接受的类型
                assert False
        else:
            # 此时，必须确保value已经是指针类型了
            self.data = None
            self.pointer = ctypes.cast(value, c_void_p)
            return


def get_face_gradient(model: Seepage, ca, fa=None):
    """
    根据cell中心位置的属性的值来计算各个face位置的梯度.
        (c1 - c0) / dist
    默认：
        ca可以是一个pointer或者是一个Vector(输入)
        fa可以是一个pointer，或者是一个Vector(输出)
    """
    ca = FloatBuffer(value=ca, is_input=True, length=model.cell_number)
    fa = FloatBuffer(value=fa, is_input=False, length=model.face_number)
    model.get_face_gradient(fa=fa.pointer, ca=ca.pointer)
    return fa.data


def get_face_diff(model: Seepage, ca, fa=None):
    """
    根据cell中心位置的属性的值来计算各个face位置的差异
        c1 - c0
    默认：
        ca可以是一个pointer或者是一个Vector(输入)
        fa可以是一个pointer，或者是一个Vector(输出)
    """
    ca = FloatBuffer(value=ca, is_input=True, length=model.cell_number)
    fa = FloatBuffer(value=fa, is_input=False, length=model.face_number)
    model.get_face_diff(fa=fa.pointer, ca=ca.pointer)
    return fa.data


def get_face_sum(model: Seepage, ca, fa=None):
    """
    根据cell中心位置的属性的值来计算各个face位置的和
        c1 + c0
    默认：
        ca可以是一个pointer或者是一个Vector(输入)
        fa可以是一个pointer，或者是一个Vector(输出)
    """
    ca = FloatBuffer(value=ca, is_input=True, length=model.cell_number)
    fa = FloatBuffer(value=fa, is_input=False, length=model.face_number)
    model.get_face_sum(fa=fa.pointer, ca=ca.pointer)
    return fa.data


def get_face_left(model: Seepage, ca, fa=None):
    """
    默认：
        ca可以是一个pointer或者是一个Vector(输入)
        fa可以是一个pointer，或者是一个Vector(输出)
    """
    ca = FloatBuffer(value=ca, is_input=True, length=model.cell_number)
    fa = FloatBuffer(value=fa, is_input=False, length=model.face_number)
    model.get_face_left(fa=fa.pointer, ca=ca.pointer)
    return fa.data


def get_face_right(model: Seepage, ca, fa=None):
    """
    默认：
        ca可以是一个pointer或者是一个Vector(输入)
        fa可以是一个pointer，或者是一个Vector(输出)
    """
    ca = FloatBuffer(value=ca, is_input=True, length=model.cell_number)
    fa = FloatBuffer(value=fa, is_input=False, length=model.face_number)
    model.get_face_right(fa=fa.pointer, ca=ca.pointer)
    return fa.data


def get_cell_average(model: Seepage, fa, ca=None):
    """
    计算cell周围face的平均值
    默认：
        fa可以是一个pointer，或者是一个Vector(输入)
        ca可以是一个pointer或者是一个Vector(输出)
    """
    fa = FloatBuffer(value=fa, is_input=True, length=model.face_number)
    ca = FloatBuffer(value=ca, is_input=False, length=model.cell_number)
    model.get_cell_average(fa=fa.pointer, ca=ca.pointer)
    return ca.data
