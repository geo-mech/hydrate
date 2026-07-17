"""
定义不依赖于DLL的通用的函数或者类
"""

import ctypes
import os
import warnings
from ctypes import c_void_p, c_double, POINTER
from typing import Any
from typing import Optional, Callable
from typing import Union

from zmlx.system import (app_data, in_linux, in_windows, in_macos, make_parent, read_text, write_text, make_dirs,
                         get_hash, log, sendmail, get_user_data_dir)

_keep = [app_data, in_linux, in_windows, in_macos, make_parent, read_text, write_text, make_dirs, get_hash, log,
         sendmail, get_user_data_dir]

try:
    import numpy as np
except ImportError:
    np = None

# 表征无穷大的序号值
IDX_INF: int = 2147483647


class Object:
    """
    提供受限属性管理的对象基类。
    """

    def set(self, **kwargs):
        """
        更新现有对象属性
        """
        current_keys = dir(self)
        for key, value in kwargs.items():
            assert key in current_keys, (f"add new attribution '{key}' "
                                         f"to {type(self).__name__} is forbidden")
            setattr(self, key, value)
        return self


def is_array(o: Any) -> bool:
    """判断对象是否支持类列表访问语义。

    Args:
        o (Any): 待检测对象

    Returns:
        bool: 当对象同时支持__getitem__和__len__协议时返回True
    """
    return hasattr(o, '__getitem__') and hasattr(o, '__len__')


def parse_fid3(fluid_id):
    """自动识别给定的流体 ID 为流体某个组分的 ID。

    Args:
        fluid_id: 流体 ID，可以是单个值或数组。

    Returns:
        tuple: 包含三个整数的元组，表示流体组件的 ID。如果未提供，则返回默认值 (IDX_INF, IDX_INF, IDX_INF)。
    """
    if fluid_id is None:
        return IDX_INF, IDX_INF, IDX_INF
    if is_array(fluid_id):
        count = len(fluid_id)
        assert 0 < count <= 3
        if count == 1:  # 此时，它仍然可能是一个array
            return parse_fid3(fluid_id[0])
        else:
            i0 = fluid_id[0] if 0 < count else IDX_INF
            i1 = fluid_id[1] if 1 < count else IDX_INF
            i2 = fluid_id[2] if 2 < count else IDX_INF
            return i0, i1, i2
    else:
        return fluid_id, IDX_INF, IDX_INF


def parse_fid(fluid_id):
    """自动识别给定的流体 ID 为流体某个组分的 ID。

    Args:
        fluid_id: 流体 ID，可以是单个值或数组。

    Returns:
        list: 流体ID序列
    """
    if fluid_id is None:
        return []
    if is_array(fluid_id):
        if len(fluid_id) == 1:  # 此时，它仍然可能是一个array
            return parse_fid(fluid_id[0])
        else:
            return fluid_id
    else:
        return [fluid_id]


def get_index(index: Optional[int], count: Optional[int] = None) -> Optional[int]:
    """返回修正后的序号，确保返回的序号满足 0 <= index < count。

    Args:
        index (Optional[int]): 原始序号。
        count (Optional[int]): 总数。默认为 None。

    Returns:
        Optional[int]: 修正后的序号。如果无法修正，则返回 None。
    """
    if index is None:
        return None
    if count is None:  # 此时，无法判断index是否越界
        if index >= 0:
            return index
        else:
            return None
    else:
        assert count >= 0
        if index >= 0:
            if index < count:
                return index  # 0 <= index < count
            else:
                return None
        else:
            assert index < 0
            index += count  # index < count
            if index >= 0:
                return index  # 0 <= index < count
            else:
                return None


def attr_in_range(value, *, left=None, right=None, min=None, max=None):
    """
    判断属性值是否在给定的范围内
    """
    if min is not None:
        warnings.warn(
            'The argument <min> of <_attr_in_range> '
            'will be removed after 2025-4-5, use <left> instead',
            DeprecationWarning, stacklevel=2)
        assert left is None
        left = min

    if max is not None:
        warnings.warn(
            'The argument <max> of <_attr_in_range> '
            'will be removed after 2025-4-5, use <right> instead',
            DeprecationWarning, stacklevel=2)
        assert right is None
        right = max

    if left is None:
        left = -1.0e100

    if right is None:
        right = 1.0e100

    return left <= value <= right


def get_distance(p0, p1):
    """计算两个点之间的距离。

    Args:
        p0: 第一个点的坐标。
        p1: 第二个点的坐标。

    Returns:
        float: 两个点之间的距离。
    """
    dist = 0.0
    for i in range(min(len(p0), len(p1))):
        dist += (p0[i] - p1[i]) ** 2
    return dist ** 0.5


def get_os_type() -> str:
    """
    返回操作系统类型字符串 (注意，zml模块仅支持 Windows和Linux两个系统，在Mac系统未测试)
    """
    if in_windows():
        return 'windows'
    elif in_linux():
        return 'linux'
    elif in_macos():
        return 'macos'
    else:
        return 'unknown'


# 是否是Windows系统 (注: 此常量后续弃用，请使用函数 in_windows)
is_windows = in_windows()

# 是否是Linux系统 (注: 此常量后续弃用，请使用函数 in_linux)
is_linux = in_linux()

# 是否是MacOS系统 (注: 此常量后续弃用，请使用函数 in_macos)
is_macos = in_macos()

# Alias of the function < for compatibility with previous code >
makedirs = make_dirs


def check_ipath(path: str, obj=None):
    """在读取文件时检查输入的文件名。

    Args:
        path (str): 文件路径。
        obj: 读取文件的对象。

    Raises:
        AssertionError: 如果路径不是字符串或文件不存在。
    """
    assert isinstance(path, str), f'The given path <{path}> is not string while load {type(obj)}'
    assert os.path.isfile(path), f'The given path <{path}> is not file while load {type(obj)}'


class HasHandle(Object):
    """管理具有句柄（handle）的对象的基类。

    该类提供了创建、释放和访问句柄的方法，用于管理具有句柄的对象。
    Args:
        handle: 对象的句柄。如果未提供，则会调用 `create` 方法创建一个新的句柄。
        create: 一个函数，用于创建新的句柄。
        release: 一个函数，用于释放句柄。
    """

    def __init__(self, handle: Optional[c_void_p] = None, create: Optional[Callable] = None,
                 release: Optional[Callable] = None):
        """初始化 HasHandle 对象。

        Args:
            handle: 对象的句柄。如果未提供，则会调用 `create` 方法创建一个新的句柄。
            create: 一个函数，用于创建新的句柄。
            release: 一个函数，用于释放句柄。
        """
        if handle is None:
            assert callable(create) and callable(release)
            self.__handle = create()
            self.__release = release
        else:
            assert handle, 'handle should be not None'
            self.__handle = handle
            self.__release = None

    def __del__(self):
        """在对象被销毁时调用，用于释放句柄。"""
        if callable(self.__release):
            self.__release(self.__handle)

    @property
    def handle(self) -> c_void_p:
        """
        获取对象的句柄。
        Returns:
            对象的句柄。
        """
        return self.__handle

    @property
    def handle_str(self):
        """
        获取对象的句柄的十六进制字符串表示。
        """
        return f'{int(self.handle): 08x}'

    def __repr__(self) -> str:
        return f'{type(self).__name__}(handle={self.handle_str})'

    def __str__(self) -> str:
        return repr(self)


def get_nearest_cell(model: Any, pos, mask=None):
    """
    找到model中，距离给定的pos最为接近的cell
    """
    if model.cell_number == 0:
        return None

    result = None
    dist = 1.0e100

    # 遍历，找到最接近的cell.
    for cell in model.cells:
        if mask is not None:
            if not mask(cell):  # 只有满足条件的cell才会被检查.
                continue

        # 计算距离
        d = get_distance(cell.pos, pos)
        if result is None or d < dist:
            dist = d
            result = cell  # 更新结果

    # 返回结果
    return result


def get_pos_range(model: Any, dim):
    """
    返回cells在某一个坐标维度上的范围

    参数:
    - model: 网格模型对象
    - dim: 维度索引（0表示x维度，1表示y维度，2表示z维度）

    返回:
    - l_range: 该维度上的最小位置值
    - r_range: 该维度上的最大位置值

    异常:
    - 断言错误: 如果模型中的单元格数量小于等于0，或者维度索引不在[0, 2]范围内
    """
    assert model.cell_number > 0
    assert 0 <= dim <= 2
    l_range, r_range = 1e100, -1e100
    for c in model.cells:
        p = c.pos[dim]
        l_range = min(l_range, p)
        r_range = max(r_range, p)
    return l_range, r_range


def get_cells_in_range(model: Any, xr=None, yr=None, zr=None,
                       center=None, radi=None):
    """
    返回在给定的坐标范围内的所有的cell. 其中xr为x坐标的范围，yr为y坐标的范围，zr为
    z坐标的范围。当某个范围为None的时候，则不检测.

    参数:
    - model: 网格模型对象
    - xr: x坐标范围（可选）
    - yr: y坐标范围（可选）
    - zr: z坐标范围（可选）
    - center: 中心点坐标（可选）
    - radi: 半径（可选）

    返回:
    - cells: 在给定范围内的单元格列表

    异常:
    - 无异常抛出
    """
    if xr is None and yr is None and zr is None and center is not None and radi is not None:
        cells = []
        for c in model.cells:
            if get_distance(center, c.pos) <= radi:
                cells.append(c)
        return cells
    ranges = (xr, yr, zr)
    cells = []
    for c in model.cells:
        out_of_range = False
        for i in range(len(ranges)):
            r = ranges[i]
            if r is not None:
                p = c.pos[i]
                if p < r[0] or p > r[1]:
                    out_of_range = True
                    break
        if not out_of_range:
            cells.append(c)
    return cells


def get_cell_mask(model: Any, xr=None, yr=None, zr=None):
    """
    返回给定坐标范围内的cell的index。主要用来辅助绘图。since 2024-6-12

    参数:
    - model: 网格模型对象
    - xr: x坐标范围（可选）
    - yr: y坐标范围（可选）
    - zr: z坐标范围（可选）

    返回:
    - mask: 在给定范围内的单元格索引列表

    异常:
    - 无异常抛出
    """

    def get_(v, r):
        """
        根据给定的值和范围生成一个布尔掩码。

        参数:
        - v: 值的列表
        - r: 范围（可选）

        返回:
        - mask: 布尔掩码列表
        """
        if r is None:
            return [True] * len(v)  # 此时为所有
        else:
            return [r[0] <= v[i] <= r[1] for i in range(len(v))]

    v_pos = [c.pos for c in model.cells]
    # 三个方向分别的mask
    x_mask = get_([pos[0] for pos in v_pos], xr)
    y_mask = get_([pos[1] for pos in v_pos], yr)
    z_mask = get_([pos[2] for pos in v_pos], zr)

    # 返回结果
    return [x_mask[i] and y_mask[i] and z_mask[i] for i in range(len(x_mask))]


def get_cell_pos(model: Any, index=(0, 1, 2)):
    """
    从网格模型中获取指定索引的单元格位置信息

    参数:
    - model: 网格模型对象
    - index: 索引元组，默认为 (0, 1, 2)，表示获取 x、y、z 坐标

    返回:
    - results: 包含指定索引位置信息的元组

    异常:
    - 无异常抛出
    """
    vpos = [cell.pos for cell in model.cells]
    results = []
    for i in index:
        results.append([pos[i] for pos in vpos])
    return tuple(results)


def get_cell_property(model: Any, get):
    """
    从网格模型中获取每个单元格的指定属性值

    参数:
    - model: 网格模型对象
    - get: 用于获取单元格属性的函数

    返回:
    - results: 包含每个单元格属性值的列表

    异常:
    - 无异常抛出
    """
    return [get(cell) for cell in model.cells]


def plot_tricontourf(model: Any, get, caption=None, gui_only=False, title=None,
                     triangulation=None,
                     fname=None, dpi=300):
    """
    绘制网格模型中每个单元格的指定属性值的三角剖分等值线图。

    参数:
    - model: 网格模型对象
    - get: 用于获取单元格属性的函数
    - caption: 图形标题（可选）
    - gui_only: 是否仅在图形用户界面中显示（可选）
    - title: 图形标题（可选）
    - triangulation: 三角剖分对象（可选）
    - fname: 保存文件名（可选）
    - dpi: 图像分辨率（可选）

    返回:
    - 无返回值

    异常:
    - 无异常抛出
    """
    from zmlx.fig import tricontourf, plot2d
    from zmlx.ui import gui

    if gui_only and not gui.exists():
        return
    z = [get(cell) for cell in model.cells]
    if triangulation is None:
        pos = [cell.pos for cell in model.cells]
        x = [p[0] for p in pos]
        y = [p[1] for p in pos]
        o = tricontourf(x=x, y=y, z=z, triangulation=None, levels=20, cmap='coolwarm')
    else:
        o = tricontourf(z=z, triangulation=triangulation, levels=20, cmap='coolwarm')

    plot2d(o, xlabel='x/m', ylabel='y/m', aspect='equal', title=title,
           caption=caption, gui_only=gui_only, fname=fname, dpi=dpi)


class HasCells(Object):
    def get_pos_range(self, dim):
        return get_pos_range(self, dim)

    def get_cells_in_range(self, *args, **kwargs):
        return get_cells_in_range(self, *args, **kwargs)

    def get_cell_pos(self, *args, **kwargs):
        return get_cell_pos(self, *args, **kwargs)

    def get_cell_property(self, *args, **kwargs):
        return get_cell_property(self, *args, **kwargs)

    def plot_tricontourf(self, *args, **kwargs):
        plot_tricontourf(self, *args, **kwargs)


class Iterator:
    """迭代器类，用于遍历模型中的元素。

    Attributes:
        __model: 模型对象。
        __index: 当前迭代的索引。
        __count: 模型中元素的总数。
        __get: 获取元素的函数。

    Args:
        model: 要迭代的模型对象。
        count: 模型中元素的总数。
        get: 一个函数，用于获取模型中指定索引位置的元素。
    """

    def __init__(self, model: Any, count: int, get: Callable[[Any, int], Any]):
        """初始化迭代器对象。

        Args:
            model (Any): 要迭代的模型对象。
            count (int): 模型中元素的总数。
            get (Callable[[Any, int], Any]): 一个函数，用于获取模型中指定索引位置的元素。
        """
        self.__model = model
        self.__index = 0
        self.__count = count
        self.__get = get

    def __iter__(self) -> 'Iterator':
        """返回迭代器对象本身。

        Returns:
            Iterator: 迭代器对象本身。
        """
        self.__index = 0
        return self

    def __next__(self) -> Any:
        """返回下一个元素，如果没有更多元素则抛出 StopIteration 异常。

        Returns:
            下一个元素。

        Raises:
            StopIteration: 如果没有更多元素。
        """
        if self.__index < self.__count:
            cell = self.__get(self.__model, self.__index)
            self.__index += 1
            return cell
        else:
            raise StopIteration()

    def __len__(self) -> int:
        """返回模型中元素的总数。

        Returns:
            int: 模型中元素的总数。
        """
        return self.__count

    def __getitem__(self, ind: int) -> Any:
        """返回指定索引位置的元素。

        Args:
            ind (int): 索引位置。

        Returns:
            指定索引位置的元素。
        """
        if ind < self.__count:
            return self.__get(self.__model, ind)
        else:
            return None


def const_f64_ptr(arr):
    """
    对于给定的Array，返回一个POINTER(c_double)，指向它的内存地址.
    返回的这个地址主要用于“读取”
    Args:
        arr: 需要获得内存地址的Array

    Returns:
        POINTER(c_double) or None: 一个只读的指针.
    """
    if arr is None:
        return None

    if isinstance(arr, POINTER(c_double)):
        return arr

    if isinstance(arr, c_void_p):
        return ctypes.cast(arr, POINTER(c_double))

    if hasattr(arr, 'pointer'):
        return arr.pointer

    # 下面，处理numpy的数组
    if np is not None:
        arr = np.ascontiguousarray(arr, dtype=np.float64)
        return arr.ctypes.data_as(POINTER(c_double))
    else:  # 没有安装numpy，只能使用ctypes
        temp = (ctypes.c_double * len(arr))(*arr)
        p = ctypes.cast(temp, ctypes.POINTER(ctypes.c_double))
        return p


def f64_ptr(arr):
    """
    对于给定的Array，返回一个POINTER(c_double)，指向它的内存地址.
    返回的内容是可“读写”的
    Args:
        arr: 需要获得内存地址的Array

    Returns:
        POINTER(c_double) or None: 一个可供读写的内存地址
    """
    if arr is None:
        return None

    if isinstance(arr, POINTER(c_double)):
        return arr

    if isinstance(arr, c_void_p):
        return ctypes.cast(arr, POINTER(c_double))

    if hasattr(arr, 'pointer'):
        return arr.pointer

    # 下面，处理numpy的数组
    if np is not None:
        assert isinstance(arr, np.ndarray), "Input must be a NumPy array"
        assert arr.flags.c_contiguous, "Array must be C-contiguous"
        assert arr.dtype == np.float64, \
            f"Array dtype must be float64, but got {arr.dtype}"
        return arr.ctypes.data_as(POINTER(c_double))
    else:
        raise ValueError(
            f"Can not convert to POINTER(c_double). type is {type(arr)}")


def get_pointer64(arr, readonly: bool = False):
    """将NumPy数组转换为C语言双精度指针。

    Args:
        arr (Union[np.ndarray, Vector]): 输入数据容器，支持以下类型：
            - dtype为float64的NumPy数组
            - 包含pointer属性的Vector对象
        readonly: 是否返回只读指针，默认为False

    Returns:
        POINTER(c_double) or None: 指向连续内存的指针

    Raises:
        ValueError: 输入类型不匹配时抛出
        AssertionError: 当NumPy数组dtype不是float64时抛出
    """
    if readonly:
        return const_f64_ptr(arr)
    else:
        return f64_ptr(arr)


class SelfPath:
    """
    返回基于当前文件的路径
    """

    def __init__(self, this_file):
        self.this_dir = os.path.dirname(os.path.abspath(this_file))

    def __call__(self, *args, mkdir: bool = False) -> str:
        res = os.path.join(self.this_dir, *args)
        if isinstance(res, str):
            if mkdir:
                make_parent(res)
            return res
        else:
            return ""
