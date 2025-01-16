"""
基于Seepage，定义热-流-化耦合的公共的函数.

模型的属性关键词有：
    dt: 时间步长
    time: 时间
    step: 迭代步
    dv_relative：每一步走过的距离与网格尺寸的比值（用以控制时间步长），默认0.1
    dt_min：时间步长的最小值，单位：秒；默认：1.0e-15
    dt_max：时间步长的最大值，单位：秒；默认：1.0e10

模型的tag：
    disable_update_den：是否禁止更新密度
    disable_update_vis：是否禁止更新粘性
    has_solid：是否有固体；如果有，那么只能允许最后一个流体为固体
    disable_flow：是否禁止流动计算
    has_inertia：是否考虑流体的惯性，如果考虑，则需要额外的属性来存储（定义：fa_s, fa_q, fa_k）
    disable_ther：是否禁止传热计算
    disable_heat_exchange：禁止流体和固体之间的热交换
    disable_update_dt：禁止更新时间不长dt

流体的属性关键词:
    temperature: 温度
    specific_heat: 比热

Cell的属性:
    temperature: 温度
    mc：质量和比热的乘积
    pre：流体的压力：用来存储迭代计算的压力结果，可能和利用流体体积和孔隙弹性计算的压力略有不同
    fv0：流体体积的初始值（和初始的g0对应的数值）
    g_heat：流体和固体热交换的系数
    vol：体积

Face的属性：
    area：横截面积
    length：长度（流体经过这个face需要流过的距离）
    g0：初始时刻的导流系数
    igr：导流系数的相对曲线的id（用来修正孔隙空间大小改变所带来的渗透率的改变）
    g_heat：用于传热计算的导流系数（注意，并非热传导系数。这个系数，已经考虑了face的横截面积和长度）
"""
import os
import warnings

import numpy as np
from collections.abc import Iterable

from zml import get_average_perm, Tensor3, Seepage, ConjugateGradientSolver
from zmlx.alg.clamp import clamp
from zmlx.alg.join_cols import join_cols
from zmlx.alg.time2str import time2str
from zmlx.config import capillary, prod, fluid_heating, timer, sand, step_iteration, adjust_vis
from zmlx.config.attr_keys import cell_keys, face_keys, flu_keys
from zmlx.config.seepage_base import *
from zmlx.filesys.join_paths import join_paths
from zmlx.filesys.make_fname import make_fname
from zmlx.filesys.make_parent import make_parent
from zmlx.filesys.tag import print_tag
from zmlx.geometry.point_distance import point_distance
from zmlx.plt.tricontourf import tricontourf
from zmlx.ui.GuiBuffer import gui
from zmlx.utility.Field import Field
from zmlx.utility.GuiIterator import GuiIterator
from zmlx.utility.SaveManager import SaveManager
from zmlx.utility.SeepageCellMonitor import SeepageCellMonitor
from zmlx.utility.SeepageNumpy import as_numpy

# 确保这些import不会被PyCharm优化掉
_unused = [get_face_gradient, get_face_diff, get_face_sum, get_face_left,
           get_face_right, get_cell_average, get_cell_max]


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


def show_cells(model: Seepage, dim0, dim1, mask=None, show_p=True, show_t=True,
               show_s=True, folder=None, use_mass=False):
    """
    二维绘图显示

    参数:
    - model: Seepage 模型对象
    - dim0: 第一个维度索引（0, 1, 2 分别对应 x, y, z 维度）
    - dim1: 第二个维度索引（0, 1, 2 分别对应 x, y, z 维度）
    - mask: 可选的掩码，用于筛选特定的单元格
    - show_p: 是否显示压力（默认为 True）
    - show_t: 是否显示温度（默认为 True）
    - show_s: 是否显示饱和度（默认为 True）
    - folder: 图像保存的文件夹路径（可选）
    - use_mass: 是否使用质量饱和度（默认为 False）

    返回值:
    - 无

    该函数通过获取模型中单元格的位置和属性值，使用 tricontourf 函数绘制二维等值线图，
    显示模型中单元格的压力、温度和饱和度分布。如果提供了文件夹路径，则将图像保存到指定文件夹中。
    """
    if not gui.exists():
        return

    x = get_cell_pos(model=model, dim=dim0, mask=mask)
    y = get_cell_pos(model=model, dim=dim1, mask=mask)
    kw = {'title': f'time = {get_time(model, as_str=True)}'}

    year = get_time(model) / (365 * 24 * 3600)

    if show_p:  # 显示压力
        v = get_cell_pre(model, mask=mask)
        tricontourf(x, y, v, caption='pressure',
                    fname=make_fname(year, join_paths(folder, 'pressure'),
                                     '.jpg', 'y'),
                    **kw)

    if show_t:  # 显示温度
        v = get_cell_temp(model, mask=mask)
        tricontourf(x, y, v, caption='temperature',
                    fname=make_fname(year, join_paths(folder, 'temperature'),
                                     '.jpg', 'y'),
                    **kw)

    if not isinstance(show_s, list):
        if show_s:  # 此时，显示所有组分的饱和度
            show_s = list_comp(model, keep_structure=False)  # 所有的组分名称

    if isinstance(show_s, list):
        if use_mass:  # 此时，显示质量饱和度
            get = get_cell_fm
        else:
            get = get_cell_fv

        fv_all = get(model=model, mask=mask)
        for name in show_s:
            assert isinstance(name, str)
            idx = model.find_fludef(name=name)
            assert idx is not None
            fv = get(model=model, fid=idx, mask=mask)  # 流体体积
            v = fv / fv_all
            # 绘图
            tricontourf(x, y, v, caption=name,
                        fname=make_fname(year, join_paths(folder, name),
                                         '.jpg', 'y'),
                        **kw)


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
            result.append([idx]+item)
    return result


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


def get_recommended_dt(model: Seepage, previous_dt,
                       dv_relative=0.1,
                       using_flow=True, using_ther=True):
    """
    在调用了 iterate 函数之后，调用此函数，来获取更优的时间步长。

    参数:
    - model: Seepage 模型对象
    - previous_dt: 之前的时间步长
    - dv_relative: 相对体积变化率，默认为 0.1
    - using_flow: 是否使用流动模型，默认为 True
    - using_ther: 是否使用热模型，默认为 True

    返回值:
    - 更优的时间步长

    该函数首先断言 `using_flow` 或 `using_ther` 至少有一个为真。
    然后，根据是否使用流动模型和热模型，分别计算推荐的时间步长 `dt1` 和 `dt2`。
    最后，返回 `dt1` 和 `dt2` 中的较小值。
    """
    assert using_flow or using_ther
    if using_flow:
        dt1 = model.get_recommended_dt(previous_dt=previous_dt,
                                       dv_relative=dv_relative)
    else:
        dt1 = 1.0e100

    if using_ther:
        ca_t = model.reg_cell_key('temperature')
        ca_mc = model.reg_cell_key('mc')
        dt2 = model.get_recommended_dt(previous_dt=previous_dt,
                                       dv_relative=dv_relative,
                                       ca_t=ca_t, ca_mc=ca_mc)
    else:
        dt2 = 1.0e100
    return min(dt1, dt2)


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


solid_buffer = Seepage.CellData()


def iterate(model: Seepage, dt=None, solver=None, fa_s=None,
            fa_q=None, fa_k=None, cond_updaters=None, diffusions=None,
            react_bufs=None, vis_max=None, vis_min=None, slots=None):
    """
    在时间上向前迭代。其中
        dt:     时间步长,若为None，则使用自动步长
        solver: 线性求解器，若为None,则使用内部定义的共轭梯度求解器.
        fa_s:   Face自定义属性的ID，代表Face的横截面积（用于计算Face内流体的受力）;
        fa_q：   Face自定义属性的ID，代表Face内流体在通量(也将在iterate中更新)
        fa_k:   Face内流体的惯性系数的属性ID
            (若fa_k属性不为None，则所有Face的该属性需要提前给定).
        react_bufs:  反应的缓冲区，用来记录各个cell发生的反应的质量，
            其中的每一个buf都应该是一个pointer，且长度等于cell的数量;
    """
    if gui.exists():  # 添加断点，从而使得在这里可以暂停和终止
        gui.break_point()

    if dt is not None:
        set_dt(model, dt)

    dt = get_dt(model)
    assert dt is not None, 'You must set dt before iterate'

    # 执行定时器函数.
    timer.iterate(model, t0=get_time(model), t1=get_time(model) + dt,
                  slots=slots)

    # 执行step迭代
    step_iteration.iterate(model=model,
                           current_step=get_step(model),
                           slots=slots)

    if model.not_has_tag('disable_update_den') and model.fludef_number > 0:
        fa_t = model.reg_flu_key('temperature')
        model.update_den(relax_factor=0.3, fa_t=fa_t)

    if model.not_has_tag('disable_update_vis') and model.fludef_number > 0:
        # 更新流体的粘性系数(注意，当有固体存在的时候，务必将粘性系数的最大值设置为1.0e30)
        if vis_min is None:
            # 允许的最小的粘性系数
            vis_min = 1.0e-7
        if vis_max is None:
            # !!
            # 自2024-5-23开始，将vis_max的默认值从1.0修改为1.0e30，即默认
            #                 不再对粘性系数的最大值进行限制.
            #                 !!
            vis_max = 1.0e30

        assert 1.0e-10 <= vis_min <= vis_max <= 1.0e40
        ca_p = model.reg_cell_key('pre')
        fa_t = model.reg_flu_key('temperature')
        model.update_vis(ca_p=ca_p,  # 压力属性
                         fa_t=fa_t,  # 温度属性
                         relax_factor=1.0, min=vis_min, max=vis_max)

    if model.injector_number > 0:
        # 实施流体的注入操作.
        model.apply_injectors(dt=dt, time=get_time(model))

    # 尝试修改边界的压力，从而使得流体生产 (使用模型内部定义的time)
    #   since 2024-6-12
    prod.iterate(model, time=get_time(model))

    # 对流体进行加热
    fluid_heating.iterate(model, dt=dt)

    has_solid = model.has_tag('has_solid')

    if has_solid:
        # 此时，认为最后一种流体其实是固体，并进行备份处理
        model.pop_fluids(solid_buffer)

    if model.gr_number > 0:
        # 此时，各个Face的导流系数是可变的
        #       (并且，这里由于已经弹出了固体，因此计算体积使用的是流体的数值).
        # 注意：
        #     在建模的时候，务必要设置Cell的v0属性，Face的g0属性和igr属性，
        #     并且，在model中，应该有相应的gr和它对应。
        ca_v0 = model.get_cell_key('fv0')
        fa_g0 = model.get_face_key('g0')
        fa_igr = model.get_face_key('igr')
        if ca_v0 is not None and fa_g0 is not None and fa_igr is not None:
            model.update_cond(ca_v0=ca_v0, fa_g0=fa_g0,
                              fa_igr=fa_igr, relax_factor=0.3)

    # 施加cond的更新操作
    if cond_updaters is not None:
        for update in cond_updaters:
            update(model)

    # 当未禁止更新flow且流体的数量非空
    update_flow = model.not_has_tag('disable_flow') and model.fludef_number > 0

    if update_flow:
        ca_p = model.reg_cell_key('pre')
        adjust_vis.adjust(model=model)  # 备份粘性，并且尝试调整
        if model.has_tag('has_inertia'):
            r1 = model.iterate(dt=dt, solver=solver, fa_s=fa_s,
                               fa_q=fa_q, fa_k=fa_k, ca_p=ca_p)
        else:
            r1 = model.iterate(dt=dt, solver=solver, ca_p=ca_p)
        adjust_vis.restore(model=model)  # 恢复之前备份的粘性
    else:
        r1 = None

    # 执行所有的扩散操作，这一步需要在没有固体存在的条件下进行
    if diffusions is not None:
        for update in diffusions:
            update(model, dt)

    # 执行毛管力相关的操作
    capillary.iterate(model, dt)

    if has_solid:
        # 恢复备份的固体物质
        model.push_fluids(solid_buffer)

    # 更新沙子的沉降
    sand.iterate(model=model, last_dt=dt)

    update_ther = model.not_has_tag('disable_ther')

    if update_ther:
        ca_t = model.reg_cell_key('temperature')
        ca_mc = model.reg_cell_key('mc')
        fa_g = model.reg_face_key('g_heat')
        r2 = model.iterate_thermal(dt=dt, solver=solver, ca_t=ca_t,
                                   ca_mc=ca_mc, fa_g=fa_g)
    else:
        r2 = None

    # 不存在禁止标识且存在流体
    exchange_heat = model.not_has_tag('disable_heat_exchange'
                                      ) and model.fludef_number > 0

    if exchange_heat:
        ca_g = model.reg_cell_key('g_heat')
        ca_t = model.reg_cell_key('temperature')
        ca_mc = model.reg_cell_key('mc')
        fa_t = model.reg_flu_key('temperature')
        fa_c = model.reg_flu_key('specific_heat')
        model.exchange_heat(dt=dt, ca_g=ca_g, ca_t=ca_t,
                            ca_mc=ca_mc, fa_t=fa_t, fa_c=fa_c)

    # 反应
    for idx in range(model.reaction_number):
        reaction = model.get_reaction(idx)
        assert isinstance(reaction, Seepage.Reaction)
        buf = None
        if react_bufs is not None:
            if idx < len(react_bufs):
                # 使用这个buf
                #   (必须确保这个buf是一个double类型的指针，并且长度等于cell_number)
                buf = react_bufs[idx]
        reaction.react(model, dt, buf=buf)

    set_time(model, get_time(model) + dt)
    set_step(model, get_step(model) + 1)

    if not model.has_tag('disable_update_dt'):
        # 只要不禁用dt更新，就尝试更新dt
        if update_flow or update_ther:
            # 只有当计算了流动或者传热过程，才可以使用自动的时间步长
            dt = get_recommended_dt(model, dt, get_dv_relative(model),
                                    using_flow=update_flow,
                                    using_ther=update_ther
                                    )
        dt = max(get_dt_min(model), min(get_dt_max(model), dt))
        set_dt(model, dt)  # 修改dt为下一步建议使用的值

    return r1, r2


def get_inited(fludefs=None, reactions=None, gravity=None, path=None,
               time=None, dt=None, dv_relative=None,
               dt_max=None, dt_min=None,
               keys=None, tags=None, model_attrs=None):
    """
    创建一个模型，初始化必要的属性.
    """
    model = Seepage(path=path)

    if keys is not None:
        # 预定义一些keys;
        # 主要目的是为了保证两个Seepage的keys的一致，
        # 在两个Seepage需要交互的时候，很重要.
        model.set_keys(**keys)

    if tags is not None:
        # 预定义的tags; since 2024-5-8
        model.add_tag(*tags)

    if model_attrs is not None:
        # 添加额外的模型属性  since 2024-5-8
        for key, value in model_attrs:
            set_attr(model, key=key, value=value)

    # 添加流体的定义和反应的定义 (since 2023-4-5)
    model.clear_fludefs()  # 首先，要清空已经存在的流体定义.
    if fludefs is not None:
        for flu in fludefs:
            model.add_fludef(Seepage.FluDef.create(flu))

    model.clear_reactions()  # 清空已经存在的定义.
    if reactions is not None:
        for r in reactions:
            model.add_reaction(r)

    if gravity is not None:
        assert len(gravity) == 3
        model.gravity = gravity
        if point_distance(gravity, [0, 0, -10]) > 1.0:
            print(f'Warning: In general, gravity should be [0,0, -10], '
                  f'but here it is {gravity}, '
                  f'please make sure this is the setting you need')

    if time is not None:
        set_time(model, time)

    if dt is not None:
        set_dt(model, dt)

    if dt_min is not None:
        set_dt_min(model, dt_min)

    if dt_max is not None:
        set_dt_max(model, dt_max)

    if dv_relative is not None:
        set_dv_relative(model, dv_relative)

    return model


def create(mesh=None,
           disable_update_den=False, disable_update_vis=False,
           disable_ther=False, disable_heat_exchange=False,
           fludefs=None, has_solid=False, reactions=None,
           gravity=None,
           dt_max=None, dt_min=None, dt_ini=None, dv_relative=None,
           gr=None, bk_fv=None, bk_g=None, caps=None,
           keys=None, tags=None, kr=None, default_kr=None,
           model_attrs=None, prods=None,
           warnings_ignored=None, injectors=None, texts=None,
           **kwargs):
    """
    利用给定的网格来创建一个模型.
        其中gr用来计算孔隙体积变化之后的渗透率的改变量.  gr的类型是一个Interp1.
    """
    model = Seepage()
    if warnings_ignored is None:  # 忽略掉的警告
        warnings_ignored = set()

    if keys is not None:
        # 预定义一些keys; 主要目的是为了保证两个Seepage的keys的一致，
        # 在两个Seepage需要交互的时候，很重要.
        model.set_keys(**keys)

    if tags is not None:
        # 预定义的tags; since 2024-5-8
        model.add_tag(*tags)

    if disable_update_den:
        model.add_tag('disable_update_den')

    if disable_update_vis:
        model.add_tag('disable_update_vis')

    if disable_ther:
        model.add_tag('disable_ther')

    if disable_heat_exchange:
        model.add_tag('disable_heat_exchange')

    if has_solid:
        model.add_tag('has_solid')

    if model_attrs is not None:
        # 添加额外的模型属性  since 2024-5-8
        for key, value in model_attrs:
            set_attr(model, key=key, value=value)

    # 添加流体的定义和反应的定义 (since 2023-4-5)
    model.clear_fludefs()  # 首先，要清空已经存在的流体定义.
    if fludefs is not None:
        for flu in fludefs:
            model.add_fludef(Seepage.FluDef.create(flu))

    model.clear_reactions()  # 清空已经存在的定义.
    if reactions is not None:
        for r in reactions:
            model.add_reaction(r)

    # 设置重力
    if gravity is not None:
        assert len(gravity) == 3
        model.gravity = gravity
        if point_distance(gravity, [0, 0, -10]) > 1.0:
            if 'gravity' not in warnings_ignored:
                warnings.warn(f'In general, gravity should be [0,0, -10], '
                              f'but here it is {gravity}, '
                              f'please make sure this is the setting you need')

    if dt_max is not None:
        set_dt_max(model, dt_max)

    if dt_min is not None:
        set_dt_min(model, dt_min)

    if dt_ini is not None:
        set_dt(model, dt_ini)

    if dv_relative is not None:
        set_dv_relative(model, dv_relative)

    if gr is not None:
        igr = model.add_gr(gr, need_id=True)
    else:
        igr = None

    if kr is not None:  # since 2024-1-26
        # 设置相渗.
        for item in kr:
            if len(item) == 2:
                idx, val = item
                model.set_kr(index=idx, kr=val)
            else:
                assert len(item) == 3
                idx, x, y = item
                model.set_kr(index=idx, saturation=x, kr=y)

    if default_kr is not None:  # since 2024-5-8
        model.set_default_kr(default_kr)

    if mesh is not None:
        add_mesh(model, mesh)

    if bk_fv is None:  # 未给定数值，则自动设定
        bk_fv = model.gr_number > 0

    if bk_g is None:  # 未给定数值，则自动设定
        bk_g = model.gr_number > 0

    # 对模型的细节进行必要的配置
    set_model(model, igr=igr, bk_fv=bk_fv, bk_g=bk_g, **kwargs)

    # 添加注入点   since 24-6-20
    if injectors is not None:
        if isinstance(injectors, dict):
            model.add_injector(**injectors)
        else:
            for item in injectors:
                assert isinstance(item, dict)
                model.add_injector(**item)

    # 添加毛管效应.
    if caps is not None:
        for cap in caps:
            capillary.add(model, **cap)

    if prods is not None:  # 添加用于生产的压力控制.
        if isinstance(prods, dict):
            prods = [prods, ]
        for item in prods:
            assert isinstance(item, dict)
            prod.add_setting(model, **item)

    # 添加文本属性
    if texts is not None:
        assert isinstance(texts, dict)
        for key, value in texts.items():
            model.set_text(key=key, text=value)

    return model


def add_mesh(model: Seepage, mesh):
    """
    根据给定的mesh，添加Cell和Face. 并对Cell和Face设置基本的属性.
        对于Cell，仅仅设置位置和体积这两个属性.
        对于Face，仅仅设置面积和长度这两个属性.

    参数:
    - model: Seepage 模型对象
    - mesh: 要添加的网格对象

    返回值:
    - 无

    该函数通过遍历网格中的单元格和面，将它们添加到模型中，并设置相应的属性。
    """
    if mesh is not None:
        ca_vol = cell_keys(model).vol
        fa_s = face_keys(model).area
        fa_l = face_keys(model).length

        cell_n0 = model.cell_number

        for c in mesh.cells:
            cell = model.add_cell()
            cell.pos = c.pos
            cell.set_attr(ca_vol, c.vol)

        for f in mesh.faces:
            face = model.add_face(model.get_cell(f.link[0] + cell_n0),
                                  model.get_cell(f.link[1] + cell_n0))
            face.set_attr(fa_s, f.area)
            face.set_attr(fa_l, f.length)


def set_model(model: Seepage, porosity=0.1,
              pore_modulus=1000e6, denc=1.0e6, dist=0.1,
              temperature=280.0, p=None,
              s=None, perm=1e-14, heat_cond=1.0,
              sample_dist=None, pore_modulus_range=None,
              igr=None, bk_fv=True,
              bk_g=True, **ignores):
    """
    设置模型的网格，并顺便设置其初始的状态.
    --
    注意各个参数的含义：
        porosity: 孔隙度；
        pore_modulus：空隙的刚度，单位Pa；正常取值在100MPa到1000MPa之间；
        denc：土体的密度和比热的乘积；
                假设土体密度2000kg/m^3，比热1000，denc取值就是2.0e6；
        dist：一个单元包含土体和流体两个部分，dist是土体和流体换热的距离。
                这个值越大，换热就越慢。如果希望土体和流体的温度非常接近，
                就可以把dist设置得比较小。一般，可以设置为网格大小的几分之一；
        temperature: 温度K
        p：压力Pa
        s：各个相的饱和度，tuple/list/dict；
        perm：渗透率 m^2
        heat_cond: 热传导系数
    -
    注意：
        每一个参数，都可以是一个具体的数值，或者是一个和x，y，z坐标相关的一个分布
            (判断是否定义了obj.__call__这样的成员函数，有这个定义，则视为一个分布，
            否则是一个全场一定的值)
    --
    注意:
        在使用这个函数之前，请确保Cell需要已经正确设置了位置，并且具有网格体积vol这个自定义属性；
        对于Face，需要设置面积s和长度length这两个自定义属性。否则，此函数的执行会出现错误.

    """
    if len(ignores) > 0:
        print(f'Warning: The following arguments ignored in '
              f'zmlx.config.seepage.set_model: {list(ignores.keys())}')

    porosity = Field(porosity)
    pore_modulus = Field(pore_modulus)
    denc = Field(denc)
    dist = Field(dist)
    temperature = Field(temperature)
    p = Field(p)
    s = Field(s)
    perm = Field(perm)
    heat_cond = Field(heat_cond)
    igr = Field(igr)
    bk_fv = Field(bk_fv)
    bk_g = Field(bk_g)

    comp_names = list_comp(model)

    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        pos = cell.pos

        sat = s(*pos)
        if isinstance(sat, dict):
            sat = get_sat(comp_names, sat)

        # 热传导系数. todo: 当热传导系数各向异性的时候，取平均值，这可能并不是最合适的.  @2024-8-11
        tmp = heat_cond(*pos)
        if isinstance(tmp, Tensor3):
            tmp = (tmp.xx + tmp.yy + tmp.zz) / 3.0

        # 设置cell
        set_cell(cell, porosity=porosity(*pos),
                 pore_modulus=pore_modulus(*pos), denc=denc(*pos),
                 temperature=temperature(*pos),
                 p=p(*pos), s=sat,
                 pore_modulus_range=pore_modulus_range,
                 dist=dist(*pos), bk_fv=bk_fv(*pos), heat_cond=tmp)

    for face in model.faces:
        assert isinstance(face, Seepage.Face)
        p0 = face.get_cell(0).pos
        p1 = face.get_cell(1).pos
        set_face(face, perm=get_average_perm(p0, p1, perm, sample_dist),
                 heat_cond=get_average_perm(p0, p1, heat_cond, sample_dist),
                 igr=igr(*face.pos), bk_g=bk_g(*face.pos))


def set_cell(cell: Seepage.Cell, pos=None, vol=None,
             porosity=0.1, pore_modulus=1000e6,
             denc=1.0e6, dist=0.1,
             temperature=280.0, p=1.0, s=None,
             pore_modulus_range=None, bk_fv=True, heat_cond=1.0):
    """
    设置Cell的初始状态.

    参数:
    - cell: Seepage.Cell 类型的单元格对象
    - pos: 单元格的位置，可选参数
    - vol: 单元格的体积，可选参数
    - porosity: 孔隙度，默认值为0.1
    - pore_modulus: 孔隙模量，默认值为1000e6
    - denc: 密度，默认值为1.0e6
    - dist: 距离，默认值为0.1
    - temperature: 温度，默认值为280.0
    - p: 压力，默认值为1.0
    - s: 饱和度，可选参数
    - pore_modulus_range: 孔隙模量范围，可选参数
    - bk_fv: 是否备份流体体积，默认值为True
    - heat_cond: 热传导系数，默认值为1.0

    返回值:
    - 无

    该函数通过设置单元格的位置、体积、孔隙度、孔隙模量、密度、距离、温度、压力、饱和度等属性，
    来初始化单元格的状态。
    """
    assert isinstance(cell, Seepage.Cell)
    ca = cell_keys(cell.model)
    fa = flu_keys(cell.model)  # 流体的属性id

    if pos is not None:
        cell.pos = pos
    else:
        pos = cell.pos

    if vol is not None:
        cell.set_attr(ca.vol, vol)
    else:
        vol = cell.get_attr(ca.vol)
        assert vol is not None

    if isinstance(s, dict):  # 查表：应该尽量避免此语句执行，效率较低
        s = get_sat(list_comp(cell.model), s)

    cell.set_ini(ca_mc=ca.mc, ca_t=ca.temperature,
                 fa_t=fa.temperature, fa_c=fa.specific_heat,
                 pos=pos, vol=vol, porosity=porosity,
                 pore_modulus=pore_modulus,
                 denc=denc,
                 temperature=temperature, p=p, s=s,
                 pore_modulus_range=pore_modulus_range
                 )

    if bk_fv:  # 备份流体体积
        cell.set_attr(ca.fv0, cell.fluid_vol)

    # 流体的固体之间的换热的系数
    cell.set_attr(ca.g_heat, vol * heat_cond / (dist ** 2))


def set_face(face: Seepage.Face, area=None, length=None,
             perm=None, heat_cond=None, igr=None, bk_g=True):
    """
    对一个Face进行配置

    参数:
    - face: Seepage.Face 类型的面对象
    - area: 面的面积，可选参数
    - length: 面的长度，可选参数
    - perm: 渗透率，可选参数
    - heat_cond: 热传导系数，可选参数
    - igr: 未知参数，可选参数
    - bk_g: 是否备份渗透率，默认值为True

    返回值:
    - 无

    该函数通过设置面的面积、长度、渗透率、热传导系数等属性，来初始化面的状态。
    """
    assert isinstance(face, Seepage.Face)
    fa = face_keys(face.model)

    if area is not None:
        assert 0 <= area <= 1.0e30
        face.set_attr(fa.area, area)
    else:
        area = face.get_attr(fa.area)
        assert area is not None
        assert 0 <= area <= 1.0e30

    if length is not None:
        assert 0 < length <= 1.0e30
        face.set_attr(fa.length, length)
    else:
        length = face.get_attr(fa.length)
        assert length is not None
        assert 0 < length <= 1.0e30

    assert area >= 0
    assert length > 0

    if perm is not None:
        if hasattr(perm, '__call__'):
            # 当单独调用set_face的时候，可能会遇到这种情况
            p0 = face.get_cell(0).pos
            p1 = face.get_cell(1).pos
            perm = get_average_perm(p0, p1, perm, point_distance(p0, p1))

        if isinstance(perm, Tensor3):
            # 当单独调用set_face的时候，可能会遇到这种情况
            p0 = face.get_cell(0).pos
            p1 = face.get_cell(1).pos
            perm = perm.get_along([p1[i] - p0[i] for i in range(3)])
            perm = max(perm, 0.0)
        assert 0 <= perm <= 1.0e10
        face.set_attr(fa.perm, perm)
    else:
        perm = face.get_attr(fa.perm)
        assert perm is not None
        assert 0 <= perm <= 1.0e10

    g0 = area * perm / length
    face.cond = g0

    if bk_g:
        face.set_attr(fa.g0, g0)

    if heat_cond is not None:
        face.set_attr(fa.g_heat, area * heat_cond / length)

    if igr is not None:
        face.set_attr(fa.igr, igr)


def add_cell(model: Seepage, *args, **kwargs):
    """
    添加一个新的Cell，并返回Cell对象

    参数:
    - model: Seepage 模型对象
    - *args: 传递给 set_cell 函数的位置参数
    - **kwargs: 传递给 set_cell 函数的关键字参数

    返回值:
    - cell: 新添加的 Cell 对象

    该函数通过调用模型的 add_cell 方法创建一个新的单元格，
    然后使用 set_cell 函数设置该单元格的初始状态，并返回这个单元格对象。
    """
    cell = model.add_cell()
    set_cell(cell, *args, **kwargs)
    return cell


def add_face(model: Seepage, cell0, cell1, *args, **kwargs):
    """
    添加一个Face，并且返回

    参数:
    - model: Seepage 模型对象
    - cell0: 第一个单元格对象
    - cell1: 第二个单元格对象
    - *args: 传递给 set_face 函数的位置参数
    - **kwargs: 传递给 set_face 函数的关键字参数

    返回值:
    - face: 新添加的 Face 对象

    该函数通过调用模型的 add_face 方法创建一个新的面，
    然后使用 set_face 函数设置该面的初始状态，并返回这个面对象。
    """
    face = model.add_face(cell0, cell1)
    set_face(face, *args, **kwargs)
    return face


def print_cells(path, model, ca_keys=None, fa_keys=None,
                fmt='%.18e', export_mass=False):
    """
    输出cell的属性（前三列固定为x y z坐标）. 默认第4列为pre，
            第5列温度，第6列为流体总体积，后面依次为各流体组分的体积饱和度.
    最后是ca_keys所定义的额外的Cell属性.

    注意：
        当export_mass为True的时候，则输出质量（第6列为总质量），
        后面的饱和度为质量的比例 （否则为体积）.
    """
    assert isinstance(model, Seepage)
    if path is None:
        return

    # 找到所有的流体的ID
    fluid_ids = []
    for i0 in range(model.fludef_number):
        f0 = model.get_fludef(i0)
        if f0.component_number == 0:
            fluid_ids.append([i0, ])
            continue
        for i1 in range(f0.component_number):
            assert f0.get_component(i1).component_number == 0
            fluid_ids.append([i0, i1])

    cells = as_numpy(model).cells
    v = cells.fluid_mass if export_mass else cells.fluid_vol

    vs = []
    for fluid_id in fluid_ids:
        f = as_numpy(model).fluids(*fluid_id)
        s = (f.mass if export_mass else f.vol) / v
        vs.append(s)

    # 返回温度(未必有定义)
    ca_t = model.get_cell_key('temperature')
    if ca_t is not None:
        t = cells.get(ca_t)
    else:
        t = np.zeros(shape=v.shape)

    # 即将保存的数据
    d = join_cols(cells.x, cells.y, cells.z, cells.pre, t, v, *vs,
                  *([] if ca_keys is None else
                    [cells.get(key) for key in ca_keys]),
                  *([] if fa_keys is None else
                    [as_numpy(model).fluids(*idx).get(key) for idx, key in fa_keys]),
                  )

    # 保存数据
    np.savetxt(path, d, fmt=fmt)


def append_cells_and_faces(model: Seepage, other: Seepage):
    """
    将另一个模型（other）中的所有的cell和face都追加到这个模型（model）后面;
        since 2024-5-18
    """
    # Add all the cells
    cell_n0 = model.cell_number
    for c in other.cells:
        model.add_cell(data=c)

    # Add all the faces
    for f in other.faces:
        assert isinstance(f, Seepage.Face)
        c0 = f.get_cell(0)
        c1 = f.get_cell(1)
        model.add_face(model.get_cell(cell_n0 + c0.index),
                       model.get_cell(cell_n0 + c1.index), data=f)


def set_solve(model: Seepage, **kw):
    """
    设置用于求解的控制参数
    """
    text = model.get_text(key='solve')
    if len(text) > 0:
        options = eval(text)
    else:
        options = {}
    options.update(kw)
    model.set_text(key='solve', text=options)


def solve(model=None, folder=None, fname=None, gui_mode=None,
          close_after_done=None, solver=None,
          extra_plot=None,
          show_state=True, gui_iter=None, state_hint=None,
          slots=None,
          save_dt=None, export_mass=True,
          **kwargs):
    """
    求解模型，并尝试将结果保存到folder.
    """
    if model is None:
        if fname is not None:
            assert os.path.isfile(fname), f'The file not exist: {fname}'
            model = Seepage(path=fname)
            if folder is None:
                folder = os.path.splitext(fname)[0]
    else:
        if fname is not None:  # 此时，尝试保存到此文件
            model.save(make_parent(fname))  # 保存
            if folder is None:
                folder = os.path.splitext(fname)[0]

    # 打印标签
    if folder is not None:
        print_tag(folder=folder)

    # step 1. 读取求解选项
    text = model.get_text(key='solve')
    if len(text) > 0:
        solve_options = eval(text)
    else:
        solve_options = {}

    # 更新
    solve_options.update(kwargs)

    # 建立求解器
    if solver is None:  # 使用规定的精度
        solver = ConjugateGradientSolver(
            tolerance=solve_options.get('tolerance', 1.0e-25))

    # 创建monitor(同时，还保留了之前的配置信息)
    monitors = solve_options.get('monitor')
    if isinstance(monitors, dict):
        monitors = [monitors]
    elif monitors is None:
        monitors = []
    for item in monitors:
        if isinstance(item, dict):
            item['monitor'] = SeepageCellMonitor(
                get_t=lambda: get_time(model),
                cell=[model.get_cell(i) for i in item.get('cell_ids')])

    # 每年的秒的数量
    seconds_year = 3600.0 * 24.0 * 365.0

    # 保存间隔的范围(以秒为单位)
    save_dy_max = solve_options.get('save_dt_max', 5 * seconds_year) / seconds_year
    save_dy_min = solve_options.get('save_dt_min', 0.01 * seconds_year) / seconds_year

    # 定义函数get_save_dy
    if save_dt is None:
        def get_save_dy(year):
            return clamp(year * 0.05, save_dy_min, save_dy_max)
    else:
        if hasattr(save_dt, '__call__'):
            def get_save_dy(year):
                return clamp(save_dt(year * seconds_year) / seconds_year,
                             save_dy_min, save_dy_max)
        else:
            def get_save_dy(_):
                return clamp(save_dt / seconds_year,
                             save_dy_min, save_dy_max)

    # 执行数据的保存
    save_model = SaveManager(join_paths(folder, 'models'), save=model.save,
                             ext='.seepage', time_unit='y',
                             dtime=get_save_dy,
                             get_time=lambda: get_time(model) / (3600.0 * 24.0 * 365.0),
                             )

    # 打印cell
    save_cells = SaveManager(join_paths(folder, 'cells'),
                             save=lambda name: print_cells(name, model=model,
                                                           export_mass=export_mass),
                             ext='.txt', time_unit='y',
                             dtime=get_save_dy,
                             get_time=lambda: get_time(model) / (3600.0 * 24.0 * 365.0),
                             )

    # 保存所有
    def save(*args, **kw):
        save_model(*args, **kw)
        save_cells(*args, **kw)

    # 用来绘图的设置(show_cells)
    data = solve_options.get('show_cells')
    if isinstance(data, dict):
        def do_show():
            show_cells(model, folder=join_paths(folder, 'figures'), **data)
    else:
        do_show = None

    def plot():
        if do_show is not None:
            do_show()
        for index in range(len(monitors)):
            item1 = monitors[index]
            assert isinstance(item1, dict)
            monitor = item1.get('monitor')
            assert isinstance(monitor, SeepageCellMonitor)
            plot_rate = item1.get('plot_rate')
            if plot_rate is not None:
                for idx in plot_rate:
                    monitor.plot_rate(index=idx, caption=f'Rate_{index}.{idx}')  # 显示生产曲线
        if extra_plot is not None:  # 一些额外的，非标准的绘图操作
            if callable(extra_plot):
                try:
                    extra_plot()
                except:
                    pass
            elif isinstance(extra_plot, Iterable):
                for extra_plot_i in extra_plot:
                    if callable(extra_plot_i):
                        try:
                            extra_plot_i()
                        except:
                            pass

    def save_monitors():
        if folder is not None:
            for index in range(len(monitors)):
                item2 = monitors[index]
                assert isinstance(item2, dict)
                monitor = item2.get('monitor')
                assert isinstance(monitor, SeepageCellMonitor)
                monitor.save(join_paths(folder, f'monitor_{index}.txt'))

    # 执行最终的迭代
    if gui_iter is None:
        gui_iter = GuiIterator(iterate, plot=plot)
    else:  # 使用已有的配置(这样，方便多个求解过程，使用全局的iter)
        assert isinstance(gui_iter, GuiIterator)
        gui_iter.iterate = iterate
        gui_iter.plot = plot

    # 求解到的最大的时间
    time_max = solve_options.get('time_max')
    if time_max is None:
        time_forward = solve_options.get('time_forward')
        if time_forward is not None:
            time_max = get_time(model) + time_forward
    if time_max is None:  # 给定默认值
        time_max = 1.0e100

    # 求解到的最大的step
    step_max = solve_options.get('step_max')
    if step_max is None:
        step_forward = solve_options.get('step_forward')  # 向前迭代的步数
        if step_forward is not None:
            step_max = get_step(model) + step_forward
    if step_max is None:  # 给定默认值
        step_max = 999999999999

    # 状态提示
    if state_hint is None:
        state_hint = ''
    else:
        state_hint = state_hint + ': '

    def do_show_state():
        if show_state:
            print(f'{state_hint}step={get_step(model)}, dt={get_dt(model, as_str=True)}, '
                  f'time={get_time(model, as_str=True)}')

    def main_loop():  # 主循环
        if folder is not None:  # 显示求解的目录
            if gui.exists():
                gui.title(f'Solve seepage: {folder}')

        while get_time(model) < time_max and get_step(model) < step_max:
            gui_iter(model, solver=solver, slots=slots)
            save()

            for item3 in monitors:  # 更新所有的监控点
                monitor = item3.get('monitor')
                monitor.update(dt=3600.0)

            if get_step(model) % 20 == 0:
                do_show_state()
                save_monitors()

        # 显示并保存最终的状态
        do_show_state()
        save_monitors()
        plot()
        save(check_dt=False)  # 保存最终状态

    if close_after_done is not None and gui_mode is None:
        # 如果指定了close_after_done，那么一定是要使用界面
        gui_mode = True

    if gui_mode is None:  # 默认不使用界面
        gui_mode = False

    if close_after_done is None:  # 默认计算技术要关闭界面
        close_after_done = True

    gui.execute(func=main_loop, close_after_done=close_after_done,
                disable_gui=not gui_mode)
