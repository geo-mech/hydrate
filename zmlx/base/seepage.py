"""
渗流类的一些基础的接口。注意，此模块不依赖其它顶层的模块。此模块存在的意义，是为了
config中的其它模块调用。

此模块中定义的所有的功能，都会被import到seepage模块中。

如果在config之外使用，则请直接使用seepage模块。
"""
import ctypes
import os
import warnings
from ctypes import c_void_p

from zml import Seepage, Vector, is_array
from zmlx.alg.to_string import time2str


def get_attr(model: Seepage, key, default_val=None, cast=None,
             **valid_range):
    """
    返回模型的属性。其中 key 可以是字符串，也可以是一个 int。
    valid_range 主要用来定义范围，即 left 和 right 两个属性
    (也包括弃用的 min 和 max 两个属性)

    Args:
        model (Seepage): 要获取属性的渗流模型对象
        key (int|str): 属性键值，字符串会被转换为模型内部键
        default_val (Any): 属性不存在时返回的默认值（默认为None）
        cast (Callable): 用于转换属性值的类型转换函数（可选）
        **valid_range: 数值验证范围参数 (left/right 或 min/max)

    Returns:
        Any: 属性值。当属性不存在且未提供默认值时返回None

    Raises:
        AssertionError: 当key不是int或str类型时抛出

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

    Args:
        model (Seepage): 要设置属性的渗流模型对象
        key (int|str): 属性键值（字符串会被注册为模型内部键）
        value (Any): 要设置的属性值
        **key_values: 批量设置的键值对参数

    Returns:
        None: 没有返回值

    Notes:
        当value为None时会触发警告但不会设置属性

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
    设置模型的时间步长。

    Args:
        model (Seepage): 要设置时间步长的渗流模型对象
        dt (float): 要设置的时间步长值（单位：秒）

    Returns:
        None: 没有返回值
    """
    set_attr(model, 'dt', dt)


def get_dt(model: Seepage, as_str=False):
    """
    获取模型的时间步长。

    Args:
        model (Seepage): 要获取时间步长的渗流模型对象
        as_str (bool): 是否返回格式化的时间字符串（默认返回浮点数）

    Returns:
        float|str: 当as_str为True时返回格式化的时间字符串，否则返回浮点数
    """
    result = get_attr(model, key='dt', default_val=1.0e-10)
    return time2str(result) if as_str else result


def get_time(model: Seepage, as_str=False):
    """获取模型当前的计算时间。

    Args:
        model (Seepage): 渗流模型对象
        as_str (bool, optional): 是否返回格式化时间字符串，默认为False

    Returns:
        float | str: 当as_str=False时返回浮点型时间值（秒），当as_str=True时返回格式化的时间字符串

    Notes:
        底层通过get_attr获取'time'属性，默认值为0.0秒
    """
    result = get_attr(model, key='time', default_val=0.0)
    return time2str(result) if as_str else result


def set_time(model: Seepage, value):
    """设置模型的计算时间

    Args:
        model (Seepage): 渗流模型对象
        value (float): 要设置的时间值（单位：秒）

    Raises:
        ValueError: 当输入值小于0时会触发警告（通过底层set_attr实现）
    """
    set_attr(model, 'time', value)


def get_step(model: Seepage):
    """获取模型已完成的计算步数

    Args:
        model (Seepage): 渗流模型对象

    Returns:
        int: 整型迭代步数，若模型未初始化则返回0

    Notes:
        通过round函数对获取值进行四舍五入处理
    """
    return get_attr(model, 'step', default_val=0, cast=round)


def set_step(model: Seepage, step):
    """设置模型的计算步数

    Args:
        model (Seepage): 渗流模型对象
        step (int): 要设置的迭代步数

    Raises:
        TypeError: 当输入值无法转换为整数时会触发异常（通过底层set_attr实现）
    """
    set_attr(model, 'step', step)


def get_dv_relative(model: Seepage):
    """获取流体运移网格数比（时间步长控制参数）

    Args:
        model (Seepage): 渗流模型对象

    Returns:
        float: 流体流经网格数与时间步长的比值，默认值0.1

    Notes:
        正常取值范围建议为[0,1]，超出范围可能导致计算不稳定
    """
    return get_attr(model, 'dv_relative', default_val=0.1)


def set_dv_relative(model: Seepage, value):
    """设置流体流过的网格数与时间步长的比值 (dv_relative)。

    该比值用于控制渗流模型中的自适应时间步长计算。

    Args:
        model (Seepage): 要修改的渗流模型实例。
        value (float): 新的 dv_relative 值（必须为正数）。

    Note:
        实际通过 `set_attr(model, 'dv_relative', value)` 存储该值。
    """
    set_attr(model, 'dv_relative', value)


def get_dt_min(model: Seepage):
    """获取允许的最小时间步长（硬约束）。

    若自适应时间步长（通过 dv_relative 计算）小于此值，
    将被强制限制为 dt_min。

    Args:
        model (Seepage): 要查询的渗流模型实例。

    Returns:
        float: 允许的最小时间步长。若未设置，默认返回 `1.0e-15`。

    Note:
        实际通过 `get_attr(model, 'dt_min', default_val=1.0e-15)` 获取该值。
    """
    return get_attr(model, key='dt_min', default_val=1.0e-15)


def set_dt_min(model: Seepage, value):
    """设置允许的最小时间步长（硬约束）。

    Args:
        model (Seepage): 要修改的渗流模型实例。
        value (float): 新的最小时间步长（必须为正数且 ≤ dt_max）。

    Raises:
        ValueError: 如果 value 为负数或超过 dt_max。

    Note:
        实际通过 `set_attr(model, 'dt_min', value)` 存储该值。
    """
    set_attr(model, 'dt_min', value)


def get_dt_max(model: Seepage):
    """获取允许的最大时间步长（硬约束）。

    若自适应时间步长（通过 dv_relative 计算）大于此值，
    将被强制限制为 dt_max。

    Args:
        model (Seepage): 要查询的渗流模型实例。

    Returns:
        float: 允许的最大时间步长。若未设置，默认返回 `1.0e10`。

    Note:
        实际通过 `get_attr(model, 'dt_max', default_val=1.0e10)` 获取该值。
    """
    return get_attr(model, 'dt_max', default_val=1.0e10)


def set_dt_max(model: Seepage, value):
    """设置允许的最大时间步长（硬约束）。

    Args:
        model (Seepage): 要修改的渗流模型实例。
        value (float): 新的最大时间步长（必须为正数且 ≥ dt_min）。

    Raises:
        ValueError: 如果 value 为负数或小于 dt_min。

    Note:
        实际通过 `set_attr(model, 'dt_max', value)` 存储该值。
    """
    set_attr(model, 'dt_max', value)


class FloatBuffer:
    """
    准备一个数据的缓冲区

    Attributes:
        data (Vector | None): 存储数据的 Vector 对象，如果没有则为 None。
        pointer (ctypes.c_void_p): 指向数据的指针。

    Args:
        value (Vector | array-like | ctypes.c_void_p | None): 输入的数据，可以是 Vector 对象、数组、指针或者 None。
        is_input (bool | None): 指示数据是否为输入数据，当 value 为 None 时必须提供。
        length (int | None): 数据的长度，当 value 为 None 时必须提供。

    Raises:
        AssertionError:
            - 当 value 为 None 时，is_input 或 length 未提供，或者 is_input 为 True。
            - 当 value 为 Vector 时，is_input 或 length 未提供，或者 is_input 为 True 但 Vector 的大小不等于 length。
            - 当 value 为数组时，is_input 或 length 未提供，或者 is_input 为 True 但数组长度不等于 length，或者 is_input 为 False。
            - 当 value 为其他类型时，不是指针类型。
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
    根据单元格中心位置的属性值计算各个面位置的差异。计算公式为 c1 - c0。

    Args:
        model (Seepage): 渗流模型对象，用于获取单元格数量和面数量等信息。
        ca (Union[ctypes.c_void_p, Vector]): 输入参数，表示单元格中心位置的属性值。可以是指针或者 Vector 对象。
        fa (Optional[Union[ctypes.c_void_p, Vector]]): 输出参数，表示面位置的差异结果。可以是指针或者 Vector 对象，默认为 None。

    Returns:
        Vector: 包含各个面位置差异结果的 Vector 对象。

    Notes:
        - 该函数会调用 `FloatBuffer` 类来处理输入和输出数据。
        - 输入的 `ca` 长度必须等于模型的单元格数量。
        - 输出的 `fa` 长度必须等于模型的面数量。
    """
    ca = FloatBuffer(value=ca, is_input=True, length=model.cell_number)
    fa = FloatBuffer(value=fa, is_input=False, length=model.face_number)
    model.get_face_diff(buf=fa.pointer, ca=ca.pointer)
    return fa.data


def get_face_sum(model: Seepage, ca, fa=None):
    """
    根据单元格中心位置的属性值计算各个面位置的和。计算公式为 c1 + c0。

    Args:
        model (Seepage): 渗流模型对象，用于获取单元格数量和面数量等信息。
        ca (Union[ctypes.c_void_p, Vector]): 输入参数，表示单元格中心位置的属性值。可以是指针或者 Vector 对象。
        fa (Optional[Union[ctypes.c_void_p, Vector]]): 输出参数，表示面位置的和结果。可以是指针或者 Vector 对象，默认为 None。

    Returns:
        Vector: 包含各个面位置和结果的 Vector 对象。

    Notes:
        - 该函数会调用 `FloatBuffer` 类来处理输入和输出数据。
        - 输入的 `ca` 长度必须等于模型的单元格数量。
        - 输出的 `fa` 长度必须等于模型的面数量。
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


def set_text(model: Seepage, **kwargs):
    for key, text in kwargs.items():
        model.set_text(key=key, text=text)


def __list(fdef):
    data = {}
    for i in range(fdef.component_number):
        name = fdef.get_component(i).name
        data[f'{name}' if len(name) > 0 else f'<{i}>'] = __list(
            fdef.get_component(i))
    return data


def list_fludefs(model):
    """
    列出模型中流体的定义
    """
    data = {}
    for i in range(model.fludef_number):
        name = model.get_fludef(i).name
        data[f'{name}' if len(name) > 0 else f'<{i}>'] = __list(
            model.get_fludef(i))
    return data


def seepage2txt(path=None, processes=None):
    """
    将seepage文件转化为txt （注意，文件必须存储在models中）
    """
    from zmlx.alg.fsys import change_fmt
    if path is None:
        path = os.getcwd()
    change_fmt(
        path=path, ext='.txt', keywords=['.seepage', 'models'],
        keep_file=False, create_data=Seepage,
        processes=processes)


def txt2seepage(path=None, processes=None):
    """
    将txt文件转化为seepage （注意，文件必须存储在models中）
    """
    from zmlx.alg.fsys import change_fmt
    if path is None:
        path = os.getcwd()
    change_fmt(
        path=path, ext='.seepage', keywords=['.txt', 'models'],
        keep_file=False, create_data=Seepage,
        processes=processes)
