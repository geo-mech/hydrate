"""
渗流类的一些基础的接口。注意，此模块不依赖其它顶层的模块。此模块存在的意义，是为了
config中的其它模块调用。

此模块中定义的所有的功能，都会被import到seepage模块中。

如果在config之外使用，则请直接使用seepage模块。
"""
import ctypes
import warnings
from ctypes import c_void_p

from zml import Seepage, Vector, is_array
from zmlx.alg.time2str import time2str


def get_attr(model: Seepage, key, default_val=None, cast=None,
             **valid_range):
    """
    返回模型的属性。其中 key 可以是字符串，也可以是一个 int。
    valid_range 主要用来定义范围，即 left 和 right 两个属性
    (也包括弃用的 min 和 max 两个属性)

    参数:
    - model: Seepage 模型对象
    - key: 属性的键，可以是字符串或整数
    - default_val: 如果属性不存在，返回的默认值
    - cast: 可选的类型转换函数，用于将属性值转换为特定类型
    - **valid_range: 包含属性值有效范围的关键字参数，如 left 和 right

    返回值:
    - 属性的值，如果属性不存在且没有提供默认值，则返回 None

    该函数首先检查 key 是否为字符串或整数。如果是字符串，它会将其转换为模型内部使用的键。
    然后，它尝试从模型中获取属性值，如果属性不存在，它会返回默认值或发出警告。
    如果提供了类型转换函数 cast，它会将属性值转换为指定的类型。最后，它返回属性值或默认值。
    """
    assert isinstance(key, (int, str))
    key_backup = key
    if isinstance(key, str):
        key = model.get_model_key(key)
    if key is not None:
        value = model.get_attr(index=key,
                               default_val=default_val,
                               **valid_range)
    else:
        if default_val is None:
            warnings.warn(f'The key ({key_backup}) is None '
                          f'and default_val is None when get_attr')
        value = default_val
    if cast is None:
        return value
    else:
        return cast(value)


def set_attr(model: Seepage, key=None, value=None, **key_values):
    """
    设置模型的属性. 其中key可以是字符串，也可以是一个int

    参数:
    - model: Seepage 模型对象
    - key: 属性的键，可以是字符串或整数
    - value: 属性的值
    - **key_values: 包含多个属性键值对的关键字参数

    返回值:
    - 无

    该函数首先检查是否提供了单个键值对。如果提供了键，它会将键转换为模型内部使用的键，并尝试设置属性值。如果值为 None，它会发出警告。如果提供了多个键值对，它会遍历这些键值对，并调用自身来设置每个属性。
    """
    if key is not None:
        if isinstance(key, str):
            key = model.reg_model_key(key)
        assert key is not None
        if value is not None:
            model.set_attr(key, value)
        else:
            warnings.warn(f'The value is None while set key = {key}')

    # 如果给定了关键词列表，那么就设置多个属性.
    if len(key_values) > 0:
        for key, value in key_values.items():
            set_attr(model, key=key, value=value)


def set_dt(model: Seepage, dt):
    """
    设置模型的时间步长

    参数:
    - model: Seepage 模型对象
    - dt: 要设置的时间步长

    返回值:
    - 无

    该函数通过调用 `set_attr` 函数来设置模型的时间步长属性。
    """
    set_attr(model, 'dt', dt)


def get_dt(model: Seepage, as_str=False):
    """
    返回模型内存储的时间步长. 当as_str的时候，返回一个字符串用以显示

    参数:
    - model: Seepage 模型对象
    - as_str: 是否以字符串形式返回时间步长

    返回值:
    - 如果 as_str 为 False，返回时间步长的数值
    - 如果 as_str 为 True，返回时间步长的字符串表示

    该函数通过调用 `get_attr` 函数获取模型的时间步长属性，并根据 `as_str` 参数决定返回值的格式。
    """
    result = get_attr(model, key='dt', default_val=1.0e-10)
    return time2str(result) if as_str else result


def get_time(model: Seepage, as_str=False):
    """
    返回模型的时间. 当as_str的时候，返回一个字符串用以显示

    参数:
    - model: Seepage 模型对象
    - as_str: 是否以字符串形式返回时间

    返回值:
    - 如果 as_str 为 False，返回时间的数值
    - 如果 as_str 为 True，返回时间的字符串表示

    该函数通过调用 `get_attr` 函数获取模型的时间属性，并根据 `as_str` 参数决定返回值的格式。
    """
    result = get_attr(model, key='time', default_val=0.0)
    return time2str(result) if as_str else result


def set_time(model: Seepage, value):
    """
    设置模型的时间

    参数:
    - model: Seepage 模型对象
    - value: 要设置的时间值

    返回值:
    - 无

    该函数通过调用 `set_attr` 函数来设置模型的时间属性。
    """
    set_attr(model, 'time', value)


def get_step(model: Seepage):
    """
    返回模型迭代的次数

    参数:
    - model: Seepage 模型对象

    返回值:
    - 模型迭代的次数，如果模型尚未迭代，则返回默认值 0

    该函数通过调用 `get_attr` 函数获取模型的 `step` 属性，并将其转换为整数类型。
    如果模型尚未迭代，`step` 属性可能不存在，此时函数将返回默认值 0。
    """
    return get_attr(model, 'step', default_val=0, cast=round)


def set_step(model: Seepage, step):
    """
    设置模型迭代的步数

    参数:
    - model: Seepage 模型对象
    - step: 要设置的迭代步数

    返回值:
    - 无

    该函数通过调用 `set_attr` 函数来设置模型的 `step` 属性。
    """
    set_attr(model, 'step', step)


def get_dv_relative(model: Seepage):
    """
    每一个时间步dt内流体流过的网格数. 用于控制时间步长. 正常取值应该在0到1之间.

    参数:
    - model: Seepage 模型对象

    返回值:
    - dv_relative: 流体流过的网格数与时间步长的比值，如果模型中未设置该值，则返回默认值 0.1

    该函数通过调用 `get_attr` 函数获取模型的 `dv_relative` 属性，并将其作为时间步长的控制参数。
    """
    return get_attr(model, 'dv_relative', default_val=0.1)


def set_dv_relative(model: Seepage, value):
    """
    设置模型中流体流过的网格数与时间步长的比值，该比值用于控制时间步长

    参数:
    - model: Seepage 模型对象
    - value: 要设置的 dv_relative 值

    返回值:
    - 无

    该函数通过调用 `set_attr` 函数来设置模型的 `dv_relative` 属性。
    """
    set_attr(model, 'dv_relative', value)


def get_dt_min(model: Seepage):
    """
    允许的最小的时间步长
        注意: 这是对时间步长的一个硬约束。
        当利用dv_relative计算的步长不在此范围内的时候，则将它强制拉回到这个范围.

    参数:
    - model: Seepage 模型对象

    返回值:
    - 模型允许的最小时间步长，如果模型中未设置该值，则返回默认值 1.0e-15

    该函数通过调用 `get_attr` 函数获取模型的 `dt_min` 属性，并将其作为时间步长的硬约束。
    """
    return get_attr(model, key='dt_min', default_val=1.0e-15)


def set_dt_min(model: Seepage, value):
    """
    设置模型允许的最小时间步长
        注意: 这是对时间步长的一个硬约束。
        当利用dv_relative计算的步长不在此范围内的时候，则将它强制拉回到这个范围.

    参数:
    - model: Seepage 模型对象
    - value: 要设置的最小时间步长值

    返回值:
    - 无

    该函数通过调用 `set_attr` 函数来设置模型的 `dt_min` 属性，并将其作为时间步长的硬约束。
    """
    set_attr(model, 'dt_min', value)


def get_dt_max(model: Seepage):
    """
    允许的最大的时间步长
        注意: 这是对时间步长的一个硬约束。
        当利用dv_relative计算的步长不在此范围内的时候，则将它强制拉回到这个范围.

    参数:
    - model: Seepage 模型对象

    返回值:
    - 模型允许的最大时间步长，如果模型中未设置该值，则返回默认值 1.0e10

    该函数通过调用 `get_attr` 函数获取模型的 `dt_max` 属性，并将其作为时间步长的硬约束。
    """
    return get_attr(model, 'dt_max', default_val=1.0e10)


def set_dt_max(model: Seepage, value):
    """
    设置模型允许的最大时间步长
        注意: 这是对时间步长的一个硬约束。
        当利用dv_relative计算的步长不在此范围内的时候，则将它强制拉回到这个范围.

    参数:
    - model: Seepage 模型对象
    - value: 要设置的最大时间步长值

    返回值:
    - 无

    该函数通过调用 `set_attr` 函数来设置模型的 `dt_max` 属性，并将其作为时间步长的硬约束。
    """
    set_attr(model, 'dt_max', value)


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
    model.get_face_gradient(buf=fa.pointer, ca=ca.pointer)
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
    model.get_face_diff(buf=fa.pointer, ca=ca.pointer)
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
    model.get_face_sum(buf=fa.pointer, ca=ca.pointer)
    return fa.data


def get_face_average(model: Seepage, ca, fa=None):
    """
    根据cell中心位置的属性的值来计算各个face位置的平均值
        c1 + c0
    默认：
        ca可以是一个pointer或者是一个Vector(输入)
        fa可以是一个pointer，或者是一个Vector(输出)
    """
    ca = FloatBuffer(value=ca, is_input=True, length=model.cell_number)
    fa = FloatBuffer(value=fa, is_input=False, length=model.face_number)
    model.get_face_average(buf=fa.pointer, ca=ca.pointer)
    return fa.data


def get_face_left(model: Seepage, ca, fa=None):
    """
    默认：
        ca可以是一个pointer或者是一个Vector(输入)
        fa可以是一个pointer，或者是一个Vector(输出)
    """
    ca = FloatBuffer(value=ca, is_input=True, length=model.cell_number)
    fa = FloatBuffer(value=fa, is_input=False, length=model.face_number)
    model.get_face_left(buf=fa.pointer, ca=ca.pointer)
    return fa.data


def get_face_right(model: Seepage, ca, fa=None):
    """
    默认：
        ca可以是一个pointer或者是一个Vector(输入)
        fa可以是一个pointer，或者是一个Vector(输出)
    """
    ca = FloatBuffer(value=ca, is_input=True, length=model.cell_number)
    fa = FloatBuffer(value=fa, is_input=False, length=model.face_number)
    model.get_face_right(buf=fa.pointer, ca=ca.pointer)
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
    model.get_cell_average(fa=fa.pointer, buf=ca.pointer)
    return ca.data


def get_cell_max(model: Seepage, fa, ca=None):
    """
    计算cell周围face的最大值
    默认：
        fa可以是一个pointer，或者是一个Vector(输入)
        ca可以是一个pointer或者是一个Vector(输出)
    """
    fa = FloatBuffer(value=fa, is_input=True, length=model.face_number)
    ca = FloatBuffer(value=ca, is_input=False, length=model.cell_number)
    model.get_cell_max(fa=fa.pointer, buf=ca.pointer)
    return ca.data
