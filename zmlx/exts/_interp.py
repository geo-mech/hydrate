from ctypes import POINTER, c_double, c_void_p, c_char_p, c_size_t, c_bool, CFUNCTYPE
from typing import Tuple, Iterable, Callable, Optional

from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._fmap import FileMap
from zmlx.exts._tensor import Tensor2, Tensor3
from zmlx.exts._utils import HasHandle, const_f64_ptr, make_parent, check_ipath
from zmlx.exts._vec import Vector


class Interp1(HasHandle):
    """映射 C++ 类：zml::Interp1。

    该类用于一维插值计算，支持从离散数据点、均匀分布数据或常数值创建插值函数，
    并支持序列化保存/加载数据。
    """
    core.use(c_void_p, 'new_interp1')
    core.use(None, 'del_interp1', c_void_p)

    def __init__(self, xmin=None, dx=None, x=None, y=None, value=None,
                 path=None, handle=None):
        """初始化一维插值对象。

        Args:
            xmin (float, optional): 均匀分布数据的起始 x 值。
            dx (float, optional): 均匀分布数据的步长。
            x (Vector/list, optional): 离散数据点的 x 坐标集合。
            y (Vector/list, optional): 离散数据点的 y 值集合。
            value (float, optional): 常数值插值。
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super().__init__(handle, core.new_interp1, core.del_interp1)
        if handle is None:
            self.set(xmin=xmin, dx=dx, x=x, y=y, value=value)
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'interp1_save', c_void_p, c_char_p)

    def save(self, path: str):
        """将插值数据序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.interp1_save(self.handle, make_c_char_p(path))

    core.use(None, 'interp1_load', c_void_p, c_char_p)

    def load(self, path: str):
        """从文件加载序列化的插值数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.interp1_load(self.handle, make_c_char_p(path))

    core.use(None, 'interp1_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'interp1_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary') -> FileMap:
        """将插值数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
            默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.interp1_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt='binary'):
        """从 FileMap 中读取序列化的插值数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
            默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.interp1_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self) -> FileMap:
        """获取插值数据的二进制序列化表示。

        Returns:
            FileMap: 包含二进制序列化数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: FileMap):
        """从二进制序列化数据加载插值。

        Args:
            value (FileMap): 包含二进制序列化数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(None, 'interp1_set', c_void_p, POINTER(c_double), c_size_t, POINTER(c_double), c_size_t)

    def set_xy(self, x, y):
        """
        设置x和y的数据
        """
        core.interp1_set(self.handle, const_f64_ptr(x), len(x), const_f64_ptr(y), len(y))

    def set(self, xmin=None, dx=None, x=None, y=None, value=None):
        """设置插值数据，支持多种初始化方式。

        调用方式：
        1. 离散数据点模式: set(x=Vector_x, y=Vector_y)
        2. 均匀分布模式: set(xmin=起始值, dx=步长, y=Vector_y)
        3. 常数值模式: set(value=常数值) 或 set(y=常数值)

        Args:
            xmin (float, optional): 均匀分布数据的起始 x 值。
            dx (float, optional): 均匀分布数据的步长。
            x (Vector/list): 离散数据点的 x 坐标集合。
            y (Vector/list/float): 数据点的 y 值集合或常数值。
            value (float, optional): 常数值插值。
        """
        if x is not None and y is not None:
            self.set_xy(x, y)
            return
        if xmin is not None and dx is not None and y is not None:
            self.set_xy([xmin, xmin + dx], y)
            return
        if y is not None:
            self.set_xy([], [y])
            return
        if value is not None:
            self.set_xy([], [value])
            return

    def create(self, xmin: float, dx: float, xmax: float, get_value: Callable[[float], float]):
        """通过回调函数创建插值数据。

        Args:
            xmin (float): 插值区间的最小 x 值。
            dx (float): 采样步长。
            xmax (float): 插值区间的最大 x 值。
            get_value (Callable): 函数指针，格式为 y = get_value(x)。

        Note:
            需要保证 xmin < xmax 且 dx > 0。
        """
        assert xmin < xmax and dx > 0
        n = int((xmax - xmin) / dx) + 1
        dx = (xmax - xmin) / n
        vx = [xmin, xmin + dx]
        vy = [get_value(xmin + dx * i) for i in range(n)]
        self.set_xy(vx, vy)

    core.use(c_bool, 'interp1_empty', c_void_p)

    def is_empty(self):
        """检查插值数据是否为空。

        Returns:
            bool: 如果插值数据为空返回 True，否则返回 False。
        """
        return core.interp1_empty(self.handle)

    @property
    def empty(self):
        """检查插值数据是否为空。

        Returns:
            bool: 如果插值数据为空返回 True，否则返回 False。
        """
        return self.is_empty()

    core.use(None, 'interp1_clear', c_void_p)

    def clear(self):
        """清空插值数据。"""
        core.interp1_clear(self.handle)

    core.use(None, 'interp1_get_vx', c_void_p, c_void_p)
    core.use(None, 'interp1_get_vy', c_void_p, c_void_p)

    def get_data(self, x=None, y=None):
        """获取插值数据的拷贝。

        Args:
            x (Vector, optional): 用于接收 x 坐标数据的 Vector 对象。
            y (Vector, optional): 用于接收 y 值数据的 Vector 对象。

        Returns:
            tuple: 包含 x 和 y 数据的 Vector 对象元组。
        """
        if not isinstance(x, Vector):
            x = Vector()
        if not isinstance(y, Vector):
            y = Vector()
        core.interp1_get_vx(self.handle, x.handle)
        core.interp1_get_vy(self.handle, y.handle)
        return x, y

    core.use(c_double, 'interp1_get', c_void_p, c_double, c_bool)

    def get(self, x, no_external=True):
        """执行插值计算。

        Args:
            x (float/Iterable): 要计算插值的 x 坐标或坐标集合。
            no_external (bool, optional): 是否禁止外推。默认为 True。

        Returns:
            float/list: 插值结果。输入为单个值时返回 float，输入为集合时返回 list。
        """
        if isinstance(x, Iterable):
            return [core.interp1_get(self.handle, scale, no_external) for scale in x]
        else:
            return core.interp1_get(self.handle, x, no_external)

    def __call__(self, *args, **kwargs):
        """使实例可调用，等效于 get 方法。"""
        return self.get(*args, **kwargs)

    core.use(c_bool, 'interp1_is_inner', c_void_p, c_double)

    def is_inner(self, x):
        """检查给定 x 坐标是否在插值区间内。

        Args:
            x (float): 要检查的 x 坐标。

        Returns:
            bool: 如果在区间内返回 True，否则返回 False。
        """
        return core.interp1_is_inner(self.handle, x)

    core.use(c_double, 'interp1_get_xmin', c_void_p)
    core.use(c_double, 'interp1_get_xmax', c_void_p)

    def xrange(self) -> Tuple[float, float]:
        """获取插值区间的 x 范围。

        Returns:
            tuple: (xmin, xmax) 组成的元组。
        """
        return core.interp1_get_xmin(self.handle), core.interp1_get_xmax(self.handle)

    core.use(None, 'interp1_to_evenly_spaced', c_void_p, c_size_t, c_size_t)

    def to_evenly_spaced(self, nmin=100, nmax=1000):
        """将插值数据转换为均匀间隔格式以加速查找。

        Args:
            nmin (int, optional): 最小采样点数。默认为 100。
            nmax (int, optional): 最大采样点数。默认为 1000。

        Returns:
            Interp1: 当前对象（支持链式调用）。
        """
        core.interp1_to_evenly_spaced(self.handle, nmin, nmax)
        return self

    core.use(None, 'interp1_clone', c_void_p, c_void_p)

    def clone(self, other: 'Interp1') -> 'Interp1':
        """克隆另一个插值对象的数据到当前对象。

        Args:
            other (Interp1): 要克隆的插值对象。

        Returns:
            Interp1: 当前对象（支持链式调用）。
        """
        if other is not None:
            assert isinstance(other, Interp1)
            core.interp1_clone(self.handle, other.handle)
        return self

    def get_copy(self) -> 'Interp1':
        """创建当前对象的深拷贝。

        Returns:
            Interp1: 新的插值对象实例。
        """
        result = Interp1()
        result.clone(self)
        return result

    core.use(None, 'interp1_iadd', c_void_p, c_double)

    def __iadd__(self, value):
        """实现 += 操作，将值添加到所有 y 坐标上。

        Args:
            value (float): 要添加的值。

        Returns:
            Interp1: 当前对象（支持链式调用）。
        """
        core.interp1_iadd(self.handle, value)
        return self

    core.use(None, 'interp1_imul', c_void_p, c_double)

    def __imul__(self, value):
        """实现 *= 操作，将值乘以所有 y 坐标上。

        Args:
            value (float): 要乘以的值。

        Returns:
            Interp1: 当前对象（支持链式调用）。
        """
        core.interp1_imul(self.handle, value)
        return self

    def __add__(self, value):
        """
        实现加法操作，将当前对象的值加上指定值。

        Args:
            value (float): 要添加的值。

        Returns:
            Interp1: 新的插值对象，包含相加后的值。
        """
        result = self.get_copy()
        result += value
        return result

    def __radd__(self, value):
        """
        实现右加法操作，将指定值加上当前对象的值。

        Args:
            value (float): 要添加的值。

        Returns:
            Interp1: 新的插值对象，包含相加后的值。
        """
        return self + value

    def __mul__(self, value):
        """
        实现乘法操作，将当前对象的值乘以指定值。

        Args:
            value (float): 要乘以的值。

        Returns:
            Interp1: 新的插值对象，包含相乘后的值。
        """
        result = self.get_copy()
        result *= value
        return result

    def __rmul__(self, value):
        """
        实现右乘法操作，将当前对象的值乘以指定值。

        Args:
            value (float): 要乘以的值。

        Returns:
            Interp1: 新的插值对象，包含相乘后的值。
        """
        return self * value


class Interp2(HasHandle):
    """映射 C++ 类：zml::Interp2。

    该类用于二维插值计算，支持从文件加载数据、创建插值函数及数值查询等功能。
    """
    core.use(c_void_p, 'new_interp2')
    core.use(None, 'del_interp2', c_void_p)

    def __init__(self, path=None, handle=None):
        """初始化二维插值对象。

        Args:
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super().__init__(handle, core.new_interp2, core.del_interp2)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'interp2_save', c_void_p, c_char_p)

    def save(self, path):
        """将插值数据序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.interp2_save(self.handle, make_c_char_p(path))

    core.use(None, 'interp2_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化的插值数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.interp2_load(self.handle, make_c_char_p(path))

    core.use(None, 'interp2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'interp2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary') -> FileMap:
        """将插值数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
            默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.interp2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt='binary'):
        """从 FileMap 中读取序列化的插值数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
            默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.interp2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self) -> FileMap:
        """获取插值数据的二进制序列化表示。

        Returns:
            FileMap: 包含二进制序列化数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: FileMap):
        """从二进制序列化数据加载插值。

        Args:
            value (FileMap): 包含二进制序列化数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(None, 'interp2_create', c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double, c_void_p)

    def create(self, xmin, dx, xmax, ymin, dy, ymax, get_value):
        """通过回调函数创建二维插值数据。

        Args:
            xmin (float): X 轴最小值。
            dx (float): X 轴采样步长。
            xmax (float): X 轴最大值。
            ymin (float): Y 轴最小值。
            dy (float): Y 轴采样步长。
            ymax (float): Y 轴最大值。
            get_value (callable): 回调函数，格式为 z = get_value(x, y)。

        Note:
            - 当 xmin == xmax 或 dx == 0 时，在 X 方向上视为常数场
            - 当 ymin == ymax 或 dy == 0 时，在 Y 方向上视为常数场
        """
        assert xmin <= xmax and dx >= 0
        assert ymin <= ymax and dy >= 0
        kernel = CFUNCTYPE(c_double, c_double, c_double)
        core.interp2_create(self.handle, xmin, dx, xmax, ymin, dy, ymax, kernel(get_value))

    @staticmethod
    def create_const(value: float) -> 'Interp2':
        """创建常数值插值场。

        Args:
            value (float): 常数值。

        Returns:
            Interp2: 创建的常数值插值对象。
        """
        f = Interp2()
        f.create(xmin=0, dx=0, xmax=0, ymin=0, dy=0, ymax=0, get_value=lambda *args: value)
        return f

    core.use(c_bool, 'interp2_empty', c_void_p)

    def is_empty(self) -> bool:
        """检查插值数据是否为空。

        Returns:
            bool: 如果插值数据为空返回 True，否则返回 False。
        """
        return core.interp2_empty(self.handle)

    @property
    def empty(self) -> bool:
        """检查插值数据是否为空。

        Returns:
            bool: 如果插值数据为空返回 True，否则返回 False。
        """
        return self.is_empty()

    core.use(None, 'interp2_clear', c_void_p)

    def clear(self):
        """清空插值数据。"""
        core.interp2_clear(self.handle)

    core.use(c_double, 'interp2_get', c_void_p, c_double, c_double, c_bool)

    def get(self, x, y, no_external=True):
        """获取指定坐标点的插值结果。

        Args:
            x (float): X 坐标值。
            y (float): Y 坐标值。
            no_external (bool, optional): 是否禁止外推。默认为 True。

        Returns:
            float: 插值计算结果。
        """
        return core.interp2_get(self.handle, x, y, no_external)

    def __call__(self, *args, **kwargs):
        """使实例可调用，等效于 get 方法。"""
        return self.get(*args, **kwargs)

    core.use(c_bool, 'interp2_is_inner', c_void_p, c_double, c_double)

    def is_inner(self, x, y):
        """判断坐标点是否在插值域内部。

        Args:
            x (float): X 坐标值。
            y (float): Y 坐标值。

        Returns:
            bool: 如果坐标在有效域内返回 True，否则返回 False。
        """
        return core.interp2_is_inner(self.handle, x, y)

    core.use(c_double, 'interp2_get_xmin', c_void_p)
    core.use(c_double, 'interp2_get_xmax', c_void_p)
    core.use(c_double, 'interp2_get_ymin', c_void_p)
    core.use(c_double, 'interp2_get_ymax', c_void_p)

    def xrange(self) -> Tuple[float, float]:
        """获取 X 轴的有效范围。

        Returns:
            tuple: (xmin, xmax) 组成的元组。
        """
        return core.interp2_get_xmin(self.handle), core.interp2_get_xmax(self.handle)

    def yrange(self) -> Tuple[float, float]:
        """获取 Y 轴的有效范围。

        Returns:
            tuple: (ymin, ymax) 组成的元组。
        """
        return core.interp2_get_ymin(self.handle), core.interp2_get_ymax(self.handle)

    core.use(None, 'interp2_clone', c_void_p, c_void_p)

    def clone(self, other: 'Interp2') -> 'Interp2':
        """克隆另一个插值对象的数据到当前对象。

        Args:
            other (Interp2): 要克隆的插值对象。

        Returns:
            Interp2: 当前对象（支持链式调用）。
        """
        if other is not None:
            assert isinstance(other, Interp2)
            core.interp2_clone(self.handle, other.handle)
        return self

    def get_copy(self) -> 'Interp2':
        """创建当前对象的深拷贝。

        Returns:
            Interp2: 新的插值对象实例。
        """
        result = Interp2()
        result.clone(self)
        return result

    core.use(None, 'interp2_iadd', c_void_p, c_double)

    def __iadd__(self, value: float) -> 'Interp2':
        """实现 += 操作，将值添加到所有 z 坐标上。

        Args:
            value (float): 要添加的值。

        Returns:
            Interp2: 当前对象（支持链式调用）。
        """
        core.interp2_iadd(self.handle, value)
        return self

    core.use(None, 'interp2_imul', c_void_p, c_double)

    def __imul__(self, value: float) -> 'Interp2':
        """实现 *= 操作，将值乘以所有 z 坐标上。

        Args:
            value (float): 要乘以的值。

        Returns:
            Interp2: 当前对象（支持链式调用）。
        """
        core.interp2_imul(self.handle, value)
        return self

    def __add__(self, value: float) -> 'Interp2':
        """
        实现加法操作，将当前对象的值加上指定值。

        Args:
            value (float): 要添加的值。

        Returns:
            Interp1: 新的插值对象，包含相加后的值。
        """
        result = self.get_copy()
        result += value
        return result

    def __radd__(self, value: float) -> 'Interp2':
        """
        实现右加法操作，将指定值加上当前对象的值。

        Args:
            value (float): 要添加的值。

        Returns:
            Interp1: 新的插值对象，包含相加后的值。
        """
        return self + value

    def __mul__(self, value: float) -> 'Interp2':
        """
        实现乘法操作，将当前对象的值乘以指定值。

        Args:
            value (float): 要乘以的值。

        Returns:
            Interp1: 新的插值对象，包含相乘后的值。
        """
        result = self.get_copy()
        result *= value
        return result

    def __rmul__(self, value: float) -> 'Interp2':
        """
        实现右乘法操作，将当前对象的值乘以指定值。

        Args:
            value (float): 要乘以的值。

        Returns:
            Interp1: 新的插值对象，包含相乘后的值。
        """
        return self * value


class Interp3(HasHandle):
    """映射 C++ 类：zml::Interp3。

    该类用于三维插值计算，支持从文件加载数据、创建插值函数及空间插值查询等功能。
    """
    core.use(c_void_p, 'new_interp3')
    core.use(None, 'del_interp3', c_void_p)

    def __init__(self, path: Optional[str] = None, handle: Optional[c_void_p] = None):
        """初始化三维插值对象。

        Args:
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super().__init__(handle, core.new_interp3, core.del_interp3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'interp3_save', c_void_p, c_char_p)

    def save(self, path: str):
        """将插值数据序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.interp3_save(self.handle, make_c_char_p(path))

    core.use(None, 'interp3_load', c_void_p, c_char_p)

    def load(self, path: str):
        """从文件加载序列化的插值数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.interp3_load(self.handle, make_c_char_p(path))

    core.use(None, 'interp3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'interp3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt: str = 'binary') -> FileMap:
        """将插值数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
                默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.interp3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt: str = 'binary'):
        """从 FileMap 中读取序列化的插值数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
                默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.interp3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self) -> FileMap:
        """获取插值数据的二进制序列化表示。

        Returns:
            FileMap: 包含二进制序列化数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: FileMap):
        """从二进制序列化数据加载插值。

        Args:
            value (FileMap): 包含二进制序列化数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(None, 'interp3_create', c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_void_p)

    def create(self, xmin, dx, xmax, ymin, dy, ymax, zmin, dz, zmax,
               get_value):
        """通过回调函数创建三维插值数据。

        Args:
            xmin (float): X 轴最小值。
            dx (float): X 轴采样步长。
            xmax (float): X 轴最大值。
            ymin (float): Y 轴最小值。
            dy (float): Y 轴采样步长。
            ymax (float): Y 轴最大值。
            zmin (float): Z 轴最小值。
            dz (float): Z 轴采样步长。
            zmax (float): Z 轴最大值。
            get_value (callable): 回调函数，格式为 value = get_value(x, y, z)。

        Note:
            - 当某轴的 min == max 或步长 == 0 时，该方向视为常数场
            - 需要保证 xmin <= xmax, ymin <= ymax, zmin <= zmax
            - 步长 dx/dy/dz 必须 >= 0
        """
        assert xmin <= xmax and dx >= 0
        assert ymin <= ymax and dy >= 0
        assert zmin <= zmax and dz >= 0
        kernel = CFUNCTYPE(c_double, c_double, c_double, c_double)
        core.interp3_create(self.handle, xmin, dx, xmax, ymin, dy, ymax, zmin,
                            dz, zmax,
                            kernel(get_value))

    @staticmethod
    def create_const(value: float) -> 'Interp3':
        """创建常数值插值场。

        Args:
            value (float): 常数值。

        Returns:
            Interp3: 创建的常数值插值对象。
        """
        f = Interp3()
        f.create(xmin=0, dx=0, xmax=0,
                 ymin=0, dy=0, ymax=0,
                 zmin=0, dz=0, zmax=0, get_value=lambda *args: value)
        return f

    core.use(c_bool, 'interp3_empty', c_void_p)

    def is_empty(self) -> bool:
        """检查插值数据是否为空。

        Returns:
            bool: 如果插值数据为空返回 True，否则返回 False。
        """
        return core.interp3_empty(self.handle)

    @property
    def empty(self) -> bool:
        """检查插值数据是否为空。

        Returns:
            bool: 如果插值数据为空返回 True，否则返回 False。
        """
        return self.is_empty()

    core.use(None, 'interp3_clear', c_void_p)

    def clear(self):
        """清空插值数据。"""
        core.interp3_clear(self.handle)

    core.use(c_double, 'interp3_get', c_void_p, c_double, c_double, c_double, c_bool)

    def get(self, x, y, z, no_external=True):
        """获取三维空间点的插值结果。

        Args:
            x (float): X 坐标值。
            y (float): Y 坐标值。
            z (float): Z 坐标值。
            no_external (bool, optional): 是否禁止外推。默认为 True。

        Returns:
            float: 插值计算结果。
        """
        return core.interp3_get(self.handle, x, y, z, no_external)

    def __call__(self, *args, **kwargs):
        """使实例可调用，等效于 get 方法。"""
        return self.get(*args, **kwargs)

    core.use(c_bool, 'interp3_is_inner', c_void_p, c_double, c_double, c_double)

    def is_inner(self, x, y, z):
        """判断坐标点是否在插值域内部。

        Args:
            x (float): X 坐标值。
            y (float): Y 坐标值。
            z (float): Z 坐标值。

        Returns:
            bool: 如果坐标在有效域内返回 True，否则返回 False。
        """
        return core.interp3_is_inner(self.handle, x, y, z)

    core.use(c_double, 'interp3_get_xmin', c_void_p)
    core.use(c_double, 'interp3_get_xmax', c_void_p)
    core.use(c_double, 'interp3_get_ymin', c_void_p)
    core.use(c_double, 'interp3_get_ymax', c_void_p)
    core.use(c_double, 'interp3_get_zmin', c_void_p)
    core.use(c_double, 'interp3_get_zmax', c_void_p)

    def xrange(self) -> Tuple[float, float]:
        """获取 X 轴的有效范围。

        Returns:
            tuple: (xmin, xmax) 组成的元组。
        """
        return core.interp3_get_xmin(self.handle), core.interp3_get_xmax(self.handle)

    def yrange(self) -> Tuple[float, float]:
        """获取 Y 轴的有效范围。

        Returns:
            tuple: (ymin, ymax) 组成的元组。
        """
        return core.interp3_get_ymin(self.handle), core.interp3_get_ymax(self.handle)

    def zrange(self) -> Tuple[float, float]:
        """获取 Z 轴的有效范围。

        Returns:
            tuple: (zmin, zmax) 组成的元组。
        """
        return core.interp3_get_zmin(self.handle), core.interp3_get_zmax(self.handle)

    core.use(None, 'interp3_clone', c_void_p, c_void_p)

    def clone(self, other: 'Interp3') -> 'Interp3':
        """克隆另一个插值对象的数据到当前对象。

        Args:
            other (Interp3): 要克隆的插值对象。

        Returns:
            Interp3: 当前对象（支持链式调用）。
        """
        if other is not None:
            assert isinstance(other, Interp3)
            core.interp3_clone(self.handle, other.handle)
        return self

    def get_copy(self) -> 'Interp3':
        """创建当前对象的深拷贝。

        Returns:
            Interp3: 新的插值对象实例。
        """
        result = Interp3()
        result.clone(self)
        return result

    core.use(None, 'interp3_iadd', c_void_p, c_double)

    def __iadd__(self, value):
        """实现 += 操作，将值添加到所有 z 坐标上。

        Args:
            value (float): 要添加的值。

        Returns:
            Interp3: 当前对象（支持链式调用）。
        """
        core.interp3_iadd(self.handle, value)
        return self

    core.use(None, 'interp3_imul', c_void_p, c_double)

    def __imul__(self, value):
        """实现 *= 操作，将值乘以所有 z 坐标上。

        Args:
            value (float): 要乘以的值。

        Returns:
            Interp3: 当前对象（支持链式调用）。
        """
        core.interp3_imul(self.handle, value)
        return self

    def __add__(self, value):
        """
        实现加法操作，将当前对象的值加上指定值。

        Args:
            value (float): 要添加的值。

        Returns:
            Interp1: 新的插值对象，包含相加后的值。
        """
        result = self.get_copy()
        result += value
        return result

    def __radd__(self, value):
        """
        实现右加法操作，将指定值加上当前对象的值。

        Args:
            value (float): 要添加的值。

        Returns:
            Interp1: 新的插值对象，包含相加后的值。
        """
        return self + value

    def __mul__(self, value):
        """
        实现乘法操作，将当前对象的值乘以指定值。

        Args:
            value (float): 要乘以的值。

        Returns:
            Interp1: 新的插值对象，包含相乘后的值。
        """
        result = self.get_copy()
        result *= value
        return result

    def __rmul__(self, value):
        """
        实现右乘法操作，将当前对象的值乘以指定值。

        Args:
            value (float): 要乘以的值。

        Returns:
            Interp1: 新的插值对象，包含相乘后的值。
        """
        return self * value


class Tensor2Interp2(HasHandle):
    """二维张量插值类，提供二维空间中的张量场插值功能。

    支持从函数创建插值、范围查询、插值计算及序列化操作。
    """
    core.use(c_void_p, 'new_tensor2interp2')
    core.use(None, 'del_tensor2interp2', c_void_p)

    def __init__(self, path: str = None, handle: Optional[c_void_p] = None):
        """初始化二维张量插值对象。

        Args:
            path (str, optional): 从文件加载数据的路径。
            handle (c_void_p, optional): 已有的C句柄。如果提供，则忽略其他参数。
        """
        super().__init__(handle, core.new_tensor2interp2, core.del_tensor2interp2)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'tensor2interp2_save', c_void_p, c_char_p)

    def save(self, path: str):
        """序列化保存插值数据。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台
            - 其他：二进制格式（最快且最小，但跨平台兼容性差）

        Args:
            path (str): 保存文件的路径

        Raises:
            ValueError: 如果路径格式不合法
        """
        if isinstance(path, str):
            make_parent(path)
            core.tensor2interp2_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor2interp2_load', c_void_p, c_char_p)

    def load(self, path: str):
        """从文件加载序列化数据。

        根据扩展名自动判断文件格式（txt/xml/二进制）

        Args:
            path (str): 加载文件的路径

        Raises:
            FileNotFoundError: 如果文件不存在
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.tensor2interp2_load(self.handle, make_c_char_p(path))

    core.use(None, 'tensor2interp2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'tensor2interp2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt: str = 'binary') -> FileMap:
        """将插值数据序列化到FileMap。

        Args:
            fmt (str, optional): 序列化格式，可选 'text'/'xml'/'binary'，默认二进制

        Returns:
            FileMap: 包含序列化数据的文件映射对象
        """
        fmap = FileMap()
        core.tensor2interp2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt: str = 'binary'):
        """从FileMap反序列化数据。

        Args:
            fmap (FileMap): 包含序列化数据的文件映射对象
            fmt (str, optional): 序列化格式，需与写入时一致，可选 'text'/'xml'/'binary'，默认二进制

        Raises:
            TypeError: 如果fmap参数类型错误
        """
        assert isinstance(fmap, FileMap)
        core.tensor2interp2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self) -> FileMap:
        """获取二进制格式的序列化表示。

        Returns:
            FileMap: 二进制格式的文件映射对象
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: FileMap):
        """从二进制FileMap加载数据。

        Args:
            value (FileMap): 包含二进制数据的文件映射对象
        """
        self.from_fmap(value, fmt='binary')

    core.use(None, 'tensor2interp2_create',
             c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double, c_void_p)

    def create(self, xmin, dx, xmax, ymin, dy, ymax, get_value):
        """通过回调函数创建插值场。

        Args:
            xmin (float): X轴最小值
            dx (float): X轴采样步长（需>0）
            xmax (float): X轴最大值（需≥xmin）
            ymin (float): Y轴最小值
            dy (float): Y轴采样步长（需>0）
            ymax (float): Y轴最大值（需≥ymin）
            get_value (callable): 形如 def (x: float, y: float) -> Tensor2 的回调函数

        Note:
            - 当xmin=xmax或ymin=ymax时创建常数字段
            - 步长过小可能导致内存溢出
        """
        kernel = CFUNCTYPE(c_double, c_double, c_double, c_size_t)
        core.tensor2interp2_create(
            self.handle, xmin, dx, xmax, ymin, dy, ymax,
            kernel(get_value))

    core.use(c_bool, 'tensor2interp2_empty', c_void_p)

    @property
    def empty(self) -> bool:
        """检查插值场是否为空。

        Returns:
            bool: True表示未初始化，False表示已载入数据
        """
        return core.tensor2interp2_empty(self.handle)

    core.use(None, 'tensor2interp2_get',
             c_void_p, c_void_p,
             c_double, c_double, c_bool)

    def get(self, x, y, no_external=True, value=None):
        """获取指定坐标点的张量值。

        Args:
            x (float): X坐标
            y (float): Y坐标
            no_external (bool, optional): 是否禁止外推（默认True，禁用外推）
            value (Tensor2, optional): 用于存储结果的张量对象

        Returns:
            Tensor2: 插值结果张量

        Raises:
            ValueError: 当坐标超出范围且no_external=True时
        """
        if value is None:
            value = Tensor2()
        core.tensor2interp2_get(self.handle, value.handle, x, y, no_external)
        return value

    def __call__(self, *args, **kwargs):
        """使实例可调用，等效于get方法。"""
        return self.get(*args, **kwargs)

    core.use(c_bool, 'tensor2interp2_is_inner', c_void_p, c_double, c_double)

    def is_inner(self, x, y):
        """判断坐标是否在有效插值域内。

        Args:
            x (float): X坐标
            y (float): Y坐标

        Returns:
            bool: True表示在有效域内，False表示在外部
        """
        return core.tensor2interp2_is_inner(self.handle, x, y)

    core.use(c_double, 'tensor2interp2_get_xmin', c_void_p)
    core.use(c_double, 'tensor2interp2_get_xmax', c_void_p)
    core.use(c_double, 'tensor2interp2_get_ymin', c_void_p)
    core.use(c_double, 'tensor2interp2_get_ymax', c_void_p)

    def xrange(self) -> Tuple[float, float]:
        """获取X轴的有效范围。

        Returns:
            tuple: (xmin, xmax) 组成的元组
        """
        return core.tensor2interp2_get_xmin(self.handle), core.tensor2interp2_get_xmax(self.handle)

    def yrange(self) -> Tuple[float, float]:
        """获取Y轴的有效范围。

        Returns:
            tuple: (ymin, ymax) 组成的元组
        """
        return core.tensor2interp2_get_ymin(self.handle), core.tensor2interp2_get_ymax(self.handle)


class Tensor3Interp3(HasHandle):
    """三维三阶张量插值器，用于三维空间中的张量场插值计算。"""
    core.use(c_void_p, 'new_tensor3interp3')
    core.use(None, 'del_tensor3interp3', c_void_p)

    def __init__(self, path=None, handle=None):
        """初始化三维张量插值器。

        Args:
            path (str, optional): 数据文件路径，支持序列化文件加载
            handle: 已有句柄，用于包装现有底层对象
        """
        super().__init__(handle, core.new_tensor3interp3, core.del_tensor3interp3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'tensor3interp3_save', c_void_p, c_char_p)

    def save(self, path):
        """保存插值器数据到文件。

        Args:
            path (str): 文件保存路径，扩展名决定格式(.txt/.xml/其他=二进制)
        """
        if isinstance(path, str):
            make_parent(path)
            core.tensor3interp3_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor3interp3_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载插值器数据。

        Args:
            path (str): 文件路径，自动根据扩展名识别格式
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.tensor3interp3_load(self.handle, make_c_char_p(path))

    core.use(None, 'tensor3interp3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'tensor3interp3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """序列化到文件映射对象。

        Args:
            fmt (str): 序列化格式，text/xml/binary

        Returns:
            FileMap: 包含序列化数据的文件映射对象
        """
        fmap = FileMap()
        core.tensor3interp3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt='binary'):
        """从文件映射对象加载数据。

        Args:
            fmap (FileMap): 包含序列化数据的文件映射
            fmt (str): 必须与写入时的序列化格式一致
        """
        assert isinstance(fmap, FileMap)
        core.tensor3interp3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """二进制序列化访问接口(property形式)。"""
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(None, 'tensor3interp3_create',
             c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double, c_void_p)

    def create(self, xmin, dx, xmax, ymin, dy, ymax, zmin, dz, zmax, get_value):
        """创建插值场。

        Args:
            xmin (float): X轴最小值
            dx (float): X轴步长(需>0)
            xmax (float): X轴最大值
            ymin (float): Y轴最小值
            dy (float): Y轴步长(需>0)
            ymax (float): Y轴最大值
            zmin (float): Z轴最小值
            dz (float): Z轴步长(需>0)
            zmax (float): Z轴最大值
            get_value (callable): 形如f(x,y,z,i)->float的回调函数，
                i∈[0,5]对应6个张量分量
        """
        kernel = CFUNCTYPE(c_double, c_double, c_double, c_double, c_size_t)
        core.tensor3interp3_create(self.handle, xmin, dx, xmax,
                                   ymin, dy, ymax,
                                   zmin, dz, zmax,
                                   kernel(get_value))

    def create_constant(self, value):
        """创建常数值张量场。

        Args:
            value (Tensor3|tuple): 张量值，支持Tensor3对象或6元素元组
        """
        if isinstance(value, Tensor3):
            value = (value[(0, 0)], value[(1, 1)],
                     value[(2, 2)], value[(0, 1)],
                     value[(1, 2)], value[(2, 0)])

        def get_value(x, y, z, i):
            assert 0 <= i < 6
            return value[i]

        vmax = 1e10
        self.create(-vmax, vmax, vmax, -vmax, vmax, vmax, -vmax, vmax, vmax, get_value)

    core.use(c_bool, 'tensor3interp3_empty', c_void_p)

    @property
    def empty(self):
        """检查插值器是否为空。

        Returns:
            bool: True表示未初始化数据
        """
        return core.tensor3interp3_empty(self.handle)

    core.use(None, 'tensor3interp3_get',
             c_void_p, c_void_p,
             c_double, c_double, c_double, c_bool)

    def get(self, x, y, z, no_external=True, value=None):
        """获取空间点的张量插值。

        Args:
            x (float): X坐标
            y (float): Y坐标
            z (float): Z坐标
            no_external (bool): 是否禁用外推
            value (Tensor3, optional): 存储结果的张量对象

        Returns:
            Tensor3: 插值结果张量
        """
        if value is None:
            value = Tensor3()
        core.tensor3interp3_get(
            self.handle, value.handle, x, y, z, no_external)
        return value

    def __call__(self, *args, **kwargs):
        """调用接口，等效于get方法。"""
        return self.get(*args, **kwargs)

    core.use(c_bool, 'tensor3interp3_is_inner', c_void_p, c_double, c_double, c_double)

    def is_inner(self, x, y, z):
        """判断坐标是否在插值域内。

        Returns:
            bool: True表示坐标在有效域内
        """
        return core.tensor3interp3_is_inner(self.handle, x, y, z)

    core.use(c_double, 'tensor3interp3_get_xmin', c_void_p)
    core.use(c_double, 'tensor3interp3_get_xmax', c_void_p)
    core.use(c_double, 'tensor3interp3_get_ymin', c_void_p)
    core.use(c_double, 'tensor3interp3_get_ymax', c_void_p)
    core.use(c_double, 'tensor3interp3_get_zmin', c_void_p)
    core.use(c_double, 'tensor3interp3_get_zmax', c_void_p)

    def xrange(self) -> Tuple[float, float]:
        """获取X轴有效范围。

        Returns:
            tuple: (最小值, 最大值)
        """
        return core.tensor3interp3_get_xmin(self.handle), core.tensor3interp3_get_xmax(self.handle)

    def yrange(self) -> Tuple[float, float]:
        """获取Y轴有效范围。

        Returns:
            tuple: (最小值, 最大值)
        """
        return core.tensor3interp3_get_ymin(self.handle), core.tensor3interp3_get_ymax(self.handle)

    def zrange(self) -> Tuple[float, float]:
        """获取Z轴有效范围。

        Returns:
            tuple: (最小值, 最大值)
        """
        return core.tensor3interp3_get_zmin(self.handle), core.tensor3interp3_get_zmax(self.handle)
