from ctypes import c_double, c_void_p, c_char_p, c_size_t
from typing import List, Tuple, Optional, Union

from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._fmap import FileMap
from zmlx.exts._utils import HasHandle, get_index, make_parent, check_ipath


class Array2(HasHandle):
    """二维数组容器类，用于存储两个双精度浮点数。

    支持初始化、序列化、元素访问及角度计算等操作。
    """
    core.use(c_void_p, 'new_array2')
    core.use(None, 'del_array2', c_void_p)

    def __init__(self, x=None, y=None, path=None, handle=None):
        """初始化二维数组对象。

        Args:
            x (float, optional): 第一个元素的初始值。
            y (float, optional): 第二个元素的初始值。
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super().__init__(handle, core.new_array2, core.del_array2)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if x is not None:
                self[0] = x
            if y is not None:
                self[1] = y
        else:
            assert x is None and y is None and path is None

    core.use(None, 'array2_save', c_void_p, c_char_p)

    def save(self, path: str):
        """将数据序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.array2_save(self.handle, make_c_char_p(path))

    core.use(None, 'array2_load', c_void_p, c_char_p)

    def load(self, path: str):
        """从文件加载序列化数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.array2_load(self.handle, make_c_char_p(path))

    core.use(None, 'array2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'array2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt: str = 'binary') -> 'FileMap':
        """将数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
                默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.array2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt: str = 'binary'):
        """从 FileMap 中读取序列化数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
                默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.array2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self) -> 'FileMap':
        """获取二进制序列化表示。

        Returns:
            FileMap: 包含二进制数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: 'FileMap'):
        """从二进制数据加载。

        Args:
            value (FileMap): 包含二进制数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    def __str__(self) -> str:
        """返回对象的字符串表示。

        Returns:
            str: 格式为 zml.Array2(x, y) 的字符串。
        """
        return f'{type(self).__name__}({self[0]}, {self[1]})'

    def __repr__(self) -> str:
        return f'{type(self).__name__}(handle={int(self.handle)}, x={self[0]}, y={self[1]})'

    def __len__(self) -> int:
        """获取数组长度。

        Returns:
            int: 固定返回 2。
        """
        return 2

    core.use(c_double, 'array2_get', c_void_p, c_size_t)

    def get(self, dim: int) -> Optional[float]:
        """获取指定维度的值。

        Args:
            dim (int): 维度索引 (0 或 1)。

        Returns:
            float | None: 对应维度的值，或 None 表示索引无效。
        """
        dim_ = get_index(dim, 2)
        if dim_ is not None:
            return core.array2_get(self.handle, dim_)
        else:
            return None

    core.use(None, 'array2_set', c_void_p, c_size_t, c_double)

    def set(self, dim: int, value: float):
        """设置指定维度的值。

        Args:
            dim (int): 维度索引 (0 或 1)。
            value (float): 要设置的值。
        """
        dim_ = get_index(dim, 2)
        if dim_ is not None:
            core.array2_set(self.handle, dim_, value)

    def __getitem__(self, key: int) -> Optional[float]:
        """通过索引访问元素。

        Args:
            key (int): 维度索引 (0 或 1)。

        Returns:
            float | None: 对应维度的值，或 None 表示索引无效。
        """
        return self.get(key)

    def __setitem__(self, key: int, value: float):
        """通过索引设置元素。

        Args:
            key (int): 维度索引 (0 或 1)。
            value (float): 要设置的值。
        """
        self.set(key, value)

    def to_list(self) -> List[float]:
        """转换为列表格式。

        Returns:
            list: 包含两个元素的列表 [x, y]。
        """
        x = self[0]
        y = self[1]
        assert x is not None and y is not None
        return [x, y]

    def to_tuple(self) -> Tuple[Optional[float], Optional[float]]:
        """转换为元组格式。

        Returns:
            tuple: 包含两个元素的元组 (x, y)。
        """
        x = self[0]
        y = self[1]
        assert x is not None and y is not None
        return x, y

    @staticmethod
    def from_list(values: Union[list, tuple]):
        """从列表创建 Array2 实例。

        Args:
            values (list | tuple): 必须包含两个元素的列表或元组。

        Returns:
            Array2: 新创建的实例。

        Raises:
            AssertionError: 如果输入列表长度不为 2。
        """
        assert len(values) == 2
        return Array2(x=values[0], y=values[1])

    def clone(self, other):
        """克隆另一个 Array2 对象的数据。

        Args:
            other (Array2): 要克隆的对象。

        Returns:
            Array2: 当前对象（支持链式调用）。
        """
        if other is not None:
            for i in range(2):
                value = other[i]
                assert value is not None
                self.set(i, value)
        return self

    core.use(c_double, 'array2_get_angle', c_void_p)

    def get_angle(self) -> float:
        """计算与 X 轴正方向的夹角。

        Returns:
            float: 弧度值，范围 [-π, π]。
        """
        return core.array2_get_angle(self.handle)


class Array3(HasHandle):
    """三维数组容器类，用于存储三个双精度浮点数。

    支持初始化、序列化、元素访问及数据转换等操作。
    """
    core.use(c_void_p, 'new_array3')
    core.use(None, 'del_array3', c_void_p)

    def __init__(self, x=None, y=None, z=None, path=None, handle=None):
        """初始化三维数组对象。

        Args:
            x (float, optional): 第一个元素的初始值。
            y (float, optional): 第二个元素的初始值。
            z (float, optional): 第三个元素的初始值。
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super().__init__(handle, core.new_array3, core.del_array3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if x is not None:
                self[0] = x
            if y is not None:
                self[1] = y
            if z is not None:
                self[2] = z
        else:
            assert x is None and y is None and z is None and path is None

    core.use(None, 'array3_save', c_void_p, c_char_p)

    def save(self, path):
        """将数据序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.array3_save(self.handle, make_c_char_p(path))

    core.use(None, 'array3_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.array3_load(self.handle, make_c_char_p(path))

    core.use(None, 'array3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'array3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt: str = 'binary') -> 'FileMap':
        """将数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
                默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.array3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt: str = 'binary'):
        """从 FileMap 中读取序列化数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
                默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.array3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self) -> 'FileMap':
        """获取二进制序列化表示。

        Returns:
            FileMap: 包含二进制数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: 'FileMap'):
        """从二进制数据加载。

        Args:
            value (FileMap): 包含二进制数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    def __repr__(self) -> str:
        return f'{type(self).__name__}(handle={int(self.handle)}, x={self[0]}, y={self[1]}, z={self[2]})'

    def __str__(self) -> str:
        """返回对象的字符串表示。

        Returns:
            str: 格式为 Array3(x, y, z) 的字符串。
        """
        return f'{type(self).__name__}({self[0]}, {self[1]}, {self[2]})'

    def __len__(self) -> int:
        """获取数组长度。

        Returns:
            int: 固定返回 3。
        """
        return 3

    core.use(c_double, 'array3_get', c_void_p, c_size_t)

    def get(self, dim: int) -> Optional[float]:
        """获取指定维度的值。

        Args:
            dim (int): 维度索引 (0, 1 或 2)。

        Returns:
            float: 对应维度的值。
        """
        dim_ = get_index(dim, 3)
        if dim_ is not None:
            return core.array3_get(self.handle, dim_)
        else:
            return None

    core.use(None, 'array3_set', c_void_p, c_size_t, c_double)

    def set(self, dim: int, value: float):
        """设置指定维度的值。

        Args:
            dim (int): 维度索引 (0, 1 或 2)。
            value (float): 要设置的值。
        """
        dim_ = get_index(dim, 3)
        if dim_ is not None:
            core.array3_set(self.handle, dim_, value)

    def __getitem__(self, key: int) -> Optional[float]:
        """通过索引访问元素。

        Args:
            key (int): 维度索引 (0, 1 或 2)。

        Returns:
            float: 对应维度的值。
        """
        return self.get(key)

    def __setitem__(self, key: int, value: float):
        """通过索引设置元素。

        Args:
            key (int): 维度索引 (0, 1 或 2)。
            value (float): 要设置的值。
        """
        self.set(key, value)

    def to_list(self) -> List[float]:
        """转换为列表格式。

        Returns:
            list: 包含三个元素的列表 [x, y, z]。
        """
        x = self.get(0)
        y = self.get(1)
        z = self.get(2)
        assert x is not None and y is not None and z is not None
        return [x, y, z]

    def to_tuple(self) -> Tuple[float, float, float]:
        """转换为元组格式。

        Returns:
            tuple: 包含三个元素的元组 (x, y, z)。
        """
        x = self.get(0)
        y = self.get(1)
        z = self.get(2)
        assert x is not None and y is not None and z is not None
        return x, y, z

    @staticmethod
    def from_list(values: Union[list, tuple]):
        """从列表创建 Array3 实例。

        Args:
            values (list, tuple): 必须包含三个元素的列表。

        Returns:
            Array3: 新创建的实例。

        Raises:
            AssertionError: 如果输入列表长度不为 3。
        """
        assert len(values) == 3
        return Array3(x=values[0], y=values[1], z=values[2])

    def clone(self, other: 'Array3'):
        """克隆另一个 Array3 对象的数据。

        Args:
            other (Array3): 要克隆的对象。

        Returns:
            Array3: 当前对象（支持链式调用）。
        """
        if other is not None:
            for i in range(3):
                value = other[i]
                assert value is not None, "Array3.clone: other[i] is None"
                self.set(i, value)
        return self
