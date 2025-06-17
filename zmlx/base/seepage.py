"""
渗流类Seepage的一些基础的接口。注意，此模块不依赖其它顶层的模块。
"""
import ctypes
import os
from ctypes import c_void_p

import zmlx.alg.sys as warnings
from zml import Seepage, Vector, is_array, get_pointer64, np
from zmlx.alg.base import time2str


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
                self.model.cells_write(
                    pointer=get_pointer64(buf),
                    index=index)
                return buf
            return None

        def set(self, index, buf):
            """
            Cell属性。index的含义参考 Seepage.cells_write
            """
            if not is_array(buf):
                self.model.cells_read(value=buf, index=index)
                return
            else:
                assert len(buf) == self.model.cell_number
                self.model.cells_read(
                    pointer=get_pointer64(buf, readonly=True),
                    index=index)

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
                self.model.faces_write(
                    pointer=get_pointer64(buf),
                    index=index)
                return buf
            return None

        def set(self, index, buf):
            """
            设置各个Face的属性
            """
            if not is_array(buf):
                self.model.faces_read(value=buf, index=index)
                return
            else:
                assert len(buf) == self.model.face_number
                self.model.faces_read(
                    pointer=get_pointer64(buf, readonly=True),
                    index=index)

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

        @property
        def gravity(self):
            """
            重力的分量与face两侧Cell距离的乘积. inner_prod(gravity, cell1.pos - cell0.pos)
            """
            return self.get(-4)

    class Fluids:
        """
        用以批量读取或者设置某一种流体的属性
        """

        def __init__(self, model, fluid_id):
            assert isinstance(model, Seepage)
            assert np is not None
            self.model = model
            if isinstance(fluid_id, str):
                fluid_id = self.model.find_fludef(name=fluid_id)
                assert fluid_id is not None
                assert len(fluid_id) > 0
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
                self.model.fluids_write(
                    fluid_id=self.fluid_id, index=index,
                    pointer=get_pointer64(buf))
                return buf
            return None

        def set(self, index, buf):
            """
            设置属性
            """
            if not is_array(buf):
                self.model.fluids_read(
                    fluid_id=self.fluid_id, value=buf,
                    index=index)
                return
            else:
                assert len(buf) == self.model.cell_number
                self.model.fluids_read(
                    fluid_id=self.fluid_id, index=index,
                    pointer=get_pointer64(buf, readonly=True))

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
        if len(fluid_id) == 1:
            if isinstance(fluid_id[0], str):
                return SeepageNumpy.Fluids(
                    model=self.model,
                    fluid_id=fluid_id[0])
        return SeepageNumpy.Fluids(model=self.model, fluid_id=fluid_id)


def as_numpy(model):
    """
    返回利用numpy来读写属性的接口
    """
    return SeepageNumpy(model)


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
        value = model.get_attr(
            index=key,
            default_val=default_val,
            **valid_range)
    else:
        if default_val is None:
            warnings.warn(
                f'The key ({key_backup}) is None '
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


def update_time(model: Seepage, dt=None):
    """
    更新模型的时间

    参数:
    - model: Seepage 模型对象
    - dt: 要更新的时间步长，如果为 None，则使用模型当前的时间步长

    返回值:
    - 无

    该函数首先检查是否提供了时间步长。如果没有提供，它会获取模型当前的时间步长。
    然后，它将模型的时间更新为当前时间加上时间步长。
    """
    if dt is None:
        dt = get_dt(model)
    set_time(model, get_time(model) + dt)


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
        value (Vector | array-like | ctypes.c_void_p | None):
            输入的数据，可以是 Vector 对象、数组、指针或者 None。
        is_input (bool | None): 指示数据是否为输入数据，
            当 value 为 None 时必须提供。
        length (int | None): 数据的长度，当 value 为 None 时必须提供。

    Raises:
        AssertionError:
            - 当 value 为 None 时，is_input 或 length 未提供，
                或者 is_input 为 True。
            - 当 value 为 Vector 时，is_input 或 length 未提供，
                或者 is_input 为 True 但 Vector 的大小不等于 length。
            - 当 value 为数组时，is_input 或 length 未提供，
                或者 is_input 为 True 但数组长度不等于 length，或者 is_input 为 False。
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
        ca (Union[ctypes.c_void_p, Vector]): 输入参数，
            表示单元格中心位置的属性值。可以是指针或者 Vector 对象。
        fa (Optional[Union[ctypes.c_void_p, Vector]]): 输出参数，
            表示面位置的差异结果。可以是指针或者 Vector 对象，默认为 None。

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
        ca (Union[ctypes.c_void_p, Vector]): 输入参数，
            表示单元格中心位置的属性值。可以是指针或者 Vector 对象。
        fa (Optional[Union[ctypes.c_void_p, Vector]]): 输出参数，
            表示面位置的和结果。可以是指针或者 Vector 对象，默认为 None。

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


def _get_names(f_def: Seepage.FluDef):
    """
    返回给定流体定义的所有的组分的名字
    :param f_def: 流体定义
    :return: 如果f_def没有组分，则返回f_def的名字；否则，将所有组分的名字作为list返回
    """
    if f_def.component_number == 0:
        return f_def.name
    else:
        names = []
        for idx in range(f_def.component_number):
            names.append(_get_names(f_def.get_component(idx)))
        return names


def _flatten_comp(name):
    """
    用在list_comp中，去除组分的结构

    参数:
    - name: 组分的名字，可以是字符串或列表

    返回值:
    - 一个列表，包含所有组分的名字，去除了嵌套结构

    如果输入的是字符串，则直接返回一个包含该字符串的列表；
    如果输入的是列表，则遍历该列表，递归地展开所有嵌套的子列表，并将结果合并成一个平面列表。
    """
    if isinstance(name, str):
        return [name]
    else:
        assert isinstance(name, list)
        temp = []
        for item in name:
            temp = temp + _flatten_comp(item)
        return temp


def list_comp(model: Seepage, keep_structure=True):
    """
    列出所有组分的名字
    :param keep_structure: 返回的结构是否保持流体的结构 (since 2024-7-25)
    :param model: 需要列出组分的模型
    :return: 所有组分的名字作为list返回(注意，会维持流体和组分的组成结构)
    """
    names = []
    for idx in range(model.fludef_number):
        names.append(_get_names(model.get_fludef(idx)))
    if keep_structure:
        return names
    else:
        return _flatten_comp(names)


def _list_comp_ids(fdef: Seepage.FluDef):
    """
    用在list_comp_ids中，列出组分中具有子组分的id (since 2024-7-25)
    """
    if fdef.component_number == 0:
        return [[]]
    result = []
    for idx in range(fdef.component_number):
        ids = _list_comp_ids(fdef.get_component(idx))
        for item in ids:
            result.append([idx] + item)
    return result


def list_comp_ids(model: Seepage):
    """
    列出模型中所有的流体的ID(其中每一个元素都是list)  (since 2024-7-25)
    """
    result = []
    for idx in range(model.fludef_number):
        ids = _list_comp_ids(model.get_fludef(idx))
        for item in ids:
            result.append([idx] + item)
    return result


def get_cell_mask(model: Seepage, xr=None, yr=None, zr=None):
    """
    返回给定坐标范围内的cell的index。主要用来辅助绘图。since 2024-6-12

    参数:
    - model: Seepage 模型对象
    - xr: x 坐标范围（可选）
    - yr: y 坐标范围（可选）
    - zr: z 坐标范围（可选）

    返回值:
    - 一个列表，包含给定坐标范围内的单元格索引

    如果 xr、yr 或 zr 为 None，则表示该方向上没有限制
    """

    def get_(v, r):
        """
        辅助函数，用于判断每个坐标是否在给定范围内

        参数:
        - v: 坐标值列表
        - r: 坐标范围（可选）

        返回值:
        - 一个列表，包含每个坐标是否在给定范围内的布尔值
        """
        if r is None:
            return [True] * len(v)  # 此时为所有
        else:
            return [r[0] <= v[i] <= r[1] for i in range(len(v))]

    # 三个方向分别的mask
    x_mask = get_(as_numpy(model).cells.x, xr)
    y_mask = get_(as_numpy(model).cells.y, yr)
    z_mask = get_(as_numpy(model).cells.z, zr)

    # 返回结果
    return [x_mask[i] and y_mask[i] and z_mask[i] for i in range(len(x_mask))]


def get_cell_pos(model: Seepage, dim, mask=None):
    """
    返回cell的位置向量

    参数:
    - model: Seepage 模型对象
    - dim: 维度索引（0, 1, 2 分别对应 x, y, z 维度）
    - mask: 可选的掩码，用于筛选特定的单元格

    返回值:
    - 一个 numpy 数组，包含给定维度上单元格的位置向量

    如果 mask 为 None，则返回所有单元格的位置向量；否则，返回掩码指定的单元格的位置向量
    """
    assert 0 <= dim < 3
    v = as_numpy(model).cells.get(-(dim + 1))
    return v if mask is None else v[mask]


def get_cell_pre(model: Seepage, mask=None):
    """
    返回模型中单元格的压力值。

    参数:
    - model: Seepage 模型对象
    - mask: 可选的掩码，用于筛选特定的单元格

    返回值:
    - 一个 numpy 数组，包含模型中所有单元格的压力值。
    - 如果提供了掩码，则返回掩码指定的单元格的压力值。
    """
    v = as_numpy(model).cells.pre
    return v if mask is None else v[mask]


def get_cell_temp(model: Seepage, mask=None):
    """
    返回模型中单元格的温度值。

    参数:
    - model: Seepage 模型对象
    - mask: 可选的掩码，用于筛选特定的单元格

    返回值:
    - 一个 numpy 数组，包含模型中所有单元格的温度值。
    - 如果提供了掩码，则返回掩码指定的单元格的温度值。
    """
    v = as_numpy(model).cells.get(model.get_cell_key('temperature'))
    return v if mask is None else v[mask]


def get_cell_fv(model: Seepage, fid=None, mask=None):
    """
    返回模型中单元格的流体体积。

    参数:
    - model: Seepage 模型对象
    - fid: 流体 ID（可选），如果未提供，则返回所有流体的总体积
    - mask: 可选的掩码，用于筛选特定的单元格

    返回值:
    - 一个 numpy 数组，包含模型中所有单元格的流体体积。
    - 如果提供了流体 ID，则返回该流体在所有单元格中的体积。
    - 如果提供了掩码，则返回掩码指定的单元格的流体体积。
    """
    if fid is None:
        v = as_numpy(model).cells.fluid_vol
    else:
        v = as_numpy(model).fluids(*fid).vol
    return v if mask is None else v[mask]


def get_cell_fm(model: Seepage, fid=None, mask=None):
    """
    返回模型中单元格的流体质量。

    参数:
    - model: Seepage 模型对象
    - fid: 流体 ID（可选），如果未提供，则返回所有流体的总质量
    - mask: 可选的掩码，用于筛选特定的单元格

    返回值:
    - 一个 numpy 数组，包含模型中所有单元格的流体质量。
    - 如果提供了流体 ID，则返回该流体在所有单元格中的质量。
    - 如果提供了掩码，则返回掩码指定的单元格的流体质量。
    """
    if fid is None:
        v = as_numpy(model).cells.fluid_mass
    else:
        v = as_numpy(model).fluids(*fid).mass
    return v if mask is None else v[mask]


def _pop_sat(name, table: dict):
    """
    从饱和度表中获取指定流体或流体组分的饱和度值。

    参数:
    - name: 流体或流体组分的名称，可以是字符串或列表。
    - table: 饱和度表，一个字典，其中键是流体或流体组分的名称，值是对应的饱和度值。

    返回值:
    - 如果 name 是字符串，则返回该流体的饱和度值；如果 name 是列表，
    则返回一个列表，包含每个流体组分的饱和度值。
    - 如果指定的流体或流体组分名称不在饱和度表中，则返回默认值 0.0。

    该函数首先检查 name 是否为字符串。如果是字符串，它会验证名称是否为空，
    并从饱和度表中获取相应的饱和度值。如果 name 不在表中，它会返回默认值 0.0。
    如果 name 是列表，函数会遍历列表中的每个元素，递归调用 _pop_sat
    函数获取每个流体组分的饱和度值，并将这些值收集到一个列表中返回。
    """
    if isinstance(name, str):
        assert len(name) > 0, 'fluid name not set'
        return table.pop(name, 0.0)
    else:
        values = []
        for item in name:
            values.append(_pop_sat(item, table))
        return values


def get_sat(names, table: dict):
    """
    返回各个组分的饱和度数值
    :param names: 组分的名字列表
    :param table: 饱和度表
    :return: 各个组分的饱和度（维持和name相同的结构，默认为0）
    """
    the_copy = table.copy()
    values = _pop_sat(names, the_copy)
    if len(the_copy) > 0:
        assert False, (f'names not used: {list(the_copy.keys())}. '
                       f'The required names: {names}')
    return values
