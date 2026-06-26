import ctypes
from ctypes import c_int64, c_char_p, c_size_t, c_void_p, c_double, POINTER
from typing import Optional, List, Any

from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._str import String
from zmlx.exts._utils import HasHandle, make_parent, check_ipath, get_index, np, const_f64_ptr, f64_ptr


class Vector(HasHandle):
    """映射 C++ 类：std::vector<double>。

    该类用于管理动态数组，支持初始化、序列化、元素访问等操作。
    """
    core.use(c_void_p, 'new_vf')
    core.use(None, 'del_vf', c_void_p)

    def __init__(self, value: Optional[List[float]] = None, path: Optional[str] = None, size: Optional[int] = None,
                 handle: Optional[c_void_p] = None):
        """初始化 Vector 对象，并可选择性地进行初始化。

        Args:
            value (list or np.ndarray, optional): 用于初始化 Vector 的列表
                    或 NumPy 数组。
            path (str, optional): 从文件加载数据的路径。
            size (int, optional): 初始化 Vector 的大小。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super().__init__(handle, core.new_vf, core.del_vf)
        if handle is None:
            if value is not None:
                self.set(value)
                return
            if isinstance(path, str):
                self.load(path)
                return
            if size is not None:
                self.size = size
                return
        else:
            assert value is None and path is None and size is None, "Vector: handle must be None if value, path, and size are not None"

    def __repr__(self) -> str:
        return f'{type(self).__name__}(handle={int(self.handle)}, size={self.size})'

    def __str__(self) -> str:
        """返回 Vector 的字符串表示。

        Returns:
            str: Vector 的字符串表示。
        """
        return f'{self.to_list()}'

    core.use(None, 'vf_save', c_void_p, c_char_p)

    def save(self, path: str):
        """将 Vector 序列化保存到文件。

        支持以下文件格式：
            - `.txt`(扩展名部分包含txt关键词即可)：跨平台，基本不可读。
            - `.xml`(扩展名部分包含xml关键词即可)：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件
            无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.vf_save(self.handle, make_c_char_p(path))

    core.use(None, 'vf_load', c_void_p, c_char_p)

    def load(self, path: str):
        """从文件加载序列化的 Vector 数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.vf_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'vf_size', c_void_p)

    @property
    def size(self) -> int:
        """获取 Vector 的大小。

        Returns:
            int: Vector 的大小。
        """
        return core.vf_size(self.handle)

    core.use(None, 'vf_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value: int):
        """设置 Vector 的大小。

        Args:
            value (int): 新的 Vector 大小。
        """
        core.vf_resize(self.handle, value)

    def __len__(self) -> int:
        """返回 Vector 的大小。

        Returns:
            int: Vector 的大小。
        """
        return self.size

    core.use(c_double, 'vf_get', c_void_p, c_size_t)

    def __getitem__(self, index: Optional[int]) -> Optional[float]:
        """获取指定索引位置的元素。

        Args:
            index (int): 元素的索引。

        Returns:
            float: 指定索引位置的元素。
        """
        index = get_index(index, self.size)
        if index is not None:
            return core.vf_get(self.handle, index)
        else:
            return None

    core.use(None, 'vf_set', c_void_p, c_size_t, c_double)

    def __setitem__(self, index: Optional[int], value: float):
        """设置指定索引位置的元素。

        Args:
            index (int): 元素的索引。
            value (float): 要设置的值。
        """
        index = get_index(index, self.size)
        if index is not None:
            core.vf_set(self.handle, index, value)

    def append(self, value: float) -> "Vector":
        """向 Vector 尾部追加元素。

        Args:
            value (float): 要追加的元素。

        Returns:
            Vector: 当前 Vector 对象（用于链式调用）。
        """
        ind = self.size
        self.size += 1
        self[ind] = value
        return self

    def set(self, value: Optional[List[float]] = None):
        """将列表或 NumPy 数组赋值给 Vector。

        Args:
            value (list or np.ndarray, optional): 要赋值的列表或 NumPy 数组。
        """
        if value is not None:
            if np is not None:
                if isinstance(value, np.ndarray):
                    self.read_numpy(value)
                    return

            self.size = len(value)
            if len(value) > 0:
                p = self.pointer
                assert p is not None
                for i in range(len(value)):
                    p[i] = value[i]

    def fill(self, value: float = 0.0):
        """使用指定值填充 Vector。

        Args:
            value (float, optional): 填充值。默认为 0.0。
        """
        count = self.size
        if count > 0:
            p = self.pointer
            assert p is not None
            for i in range(count):
                p[i] = value

    def to_list(self) -> List[float]:
        """将 Vector 转换为 Python 列表。

        Returns:
            list: 转换后的 Python 列表。
        """
        count = self.size
        if count == 0:
            return []
        p = self.pointer
        assert p is not None
        return [p[i] for i in range(count)]

    core.use(None, 'vf_read', c_void_p, c_void_p)

    def read_memory(self, pointer):
        """从内存地址读取数据。

        Args:
            pointer: 内存地址

        Note:
            支持从 ctypes.POINTER(c_double)、c_void_p、Vector、np.ndarray[float] 或 list[float] 读取数据。
            此函数不会检查指针是否有效，以及指针的长度。请务必确保给定的指针是有效的。
        """
        core.vf_read(self.handle, const_f64_ptr(pointer))

    core.use(None, 'vf_write', c_void_p, c_void_p)

    def write_memory(self, pointer):
        """将数据写入到指定的内存地址。

        Args:
            pointer: 内存地址。

        Note:
            支持将 ctypes.POINTER(c_double)、c_void_p、Vector、np.ndarray[float] 或 list[float] 写入到内存地址。
            此函数不会检查指针是否有效，以及指针的长度。请务必确保给定的指针是有效的。
        """
        core.vf_write(self.handle, f64_ptr(pointer))

    def read_numpy(self, data):
        """从 NumPy 数组读取数据。

        Args:
            data (np.ndarray): 要读取的 NumPy 数组。
        """
        if np is not None:
            self.size = len(data)
            self.read_memory(data)

    def write_numpy(self, data):
        """将数据写入到 NumPy 数组。

        Args:
            data (np.ndarray): 要写入的 NumPy 数组。
        """
        if np is not None:
            assert isinstance(data, np.ndarray)
            assert len(data) >= self.size
            self.write_memory(data)

    def to_numpy(self):
        """将 Vector 转换为 NumPy 数组。

        Returns:
            np.ndarray: 转换后的 NumPy 数组。
        """
        if np is not None:
            arr = np.zeros(self.size)
            self.write_numpy(arr)
            return arr
        else:
            return None

    core.use(c_void_p, 'vf_pointer', c_void_p)

    @property
    def pointer(self) -> Any:
        """获取 Vector 首个元素的指针。

        Returns:
            ctypes.POINTER(c_double): 指向首个元素的指针。
        """
        ptr = core.vf_pointer(self.handle)
        if ptr:
            return ctypes.cast(ptr, POINTER(c_double))
        else:
            return None


class IntVector(HasHandle):
    """映射 C++ 类：std::vector<long long>。

    该类用于管理动态整数数组，支持初始化、序列化、元素访问等操作。
    """
    core.use(c_void_p, 'new_vi')
    core.use(None, 'del_vi', c_void_p)

    def __init__(self, value: Optional[List[int]] = None, handle: Optional[c_void_p] = None):
        """初始化 IntVector 对象。

        Args:
            value (list, optional): 用于初始化 IntVector 的列表。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super().__init__(handle, core.new_vi, core.del_vi)
        if handle is None:
            if value is not None:
                self.set(value)

    def __repr__(self) -> str:
        return f'{type(self).__name__}(handle={int(self.handle)}, size={self.size})'

    core.use(None, 'vi_save', c_void_p, c_char_p)

    def save(self, path: str):
        """将 IntVector 序列化保存到文件。

        支持以下文件格式：
            - `.txt`(扩展名部分包含txt关键词即可)：跨平台，基本不可读。
            - `.xml`(扩展名部分包含xml关键词即可)：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.vi_save(self.handle, make_c_char_p(path))

    core.use(None, 'vi_load', c_void_p, c_char_p)

    def load(self, path: str):
        """从文件加载序列化的 IntVector 数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.vi_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'vi_size', c_void_p)

    @property
    def size(self) -> int:
        """获取 IntVector 的大小。

        Returns:
            int: IntVector 的大小。
        """
        return core.vi_size(self.handle)

    core.use(None, 'vi_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value: int):
        """设置 IntVector 的大小。

        Args:
            value (int): 新的 IntVector 大小。
        """
        core.vi_resize(self.handle, value)

    def __len__(self) -> int:
        """返回 IntVector 的大小。

        Returns:
            int: IntVector 的大小。
        """
        return self.size

    core.use(c_int64, 'vi_get', c_void_p, c_size_t)

    def __getitem__(self, index: int) -> Optional[int]:
        """获取指定索引位置的元素。

        Args:
            index (int): 元素的索引。

        Returns:
            int: 指定索引位置的元素。

        Note:
            如果索引越界，则返回 None。
        """
        idx_ = get_index(index, self.size)
        if idx_ is not None:
            return core.vi_get(self.handle, idx_)
        else:
            return None

    core.use(None, 'vi_set',
             c_void_p, c_size_t, c_int64)

    def __setitem__(self, index: int, value: int):
        """设置指定索引位置的元素。

        Args:
            index (int): 元素的索引。
            value (int): 要设置的值。

        Note:
            如果索引越界，则设置失败。
        """
        idx_ = get_index(index, self.size)
        if idx_ is not None:
            core.vi_set(self.handle, idx_, value)

    def append(self, value: int):
        """向 IntVector 尾部追加元素。

        Args:
            value (int): 要追加的元素。
        """
        key = self.size
        self.size += 1
        self[key] = value

    def set(self, value: List[int]):
        """将列表赋值给 IntVector。

        Args:
            value (list): 要赋值的列表。
        """
        count = len(value)
        self.size = count
        p = self.pointer
        for i in range(count):
            p[i] = value[i]

    def to_list(self) -> List[int]:
        """将 IntVector 转换为 Python 列表。

        Returns:
            list: 转换后的 Python 列表。
        """
        count = self.size
        if count > 0:
            p = self.pointer
            return [p[i] for i in range(count)]
        else:
            return []

    core.use(c_void_p, 'vi_pointer', c_void_p)

    @property
    def pointer(self) -> Any:
        """获取 IntVector 首个元素的指针。

        Returns:
            ctypes.POINTER(c_int64): 指向首个元素的指针。

        Note:
            如果 IntVector 为空，则返回 None。
        """
        ptr = core.vi_pointer(self.handle)
        if ptr:
            return ctypes.cast(ptr, POINTER(c_int64))
        else:
            return None


Int64Vector = IntVector


class UintVector(HasHandle):
    """映射 C++ 类：std::vector<std::size_t>。

    该类用于管理动态无符号整数数组，支持初始化、序列化、元素访问等操作。
    """
    core.use(c_void_p, 'new_vui')
    core.use(None, 'del_vui', c_void_p)

    def __init__(self, value: Optional[List[int]] = None, handle: Optional[c_void_p] = None):
        """初始化 UintVector 对象。

        Args:
            value (list, optional): 用于初始化 UintVector 的列表。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super().__init__(handle, core.new_vui, core.del_vui)
        if handle is None:
            if value is not None:
                self.set(value)

    def __repr__(self) -> str:
        return f'{type(self).__name__}(handle={int(self.handle)}, size={self.size})'

    core.use(None, 'vui_save', c_void_p, c_char_p)

    def save(self, path: str):
        """将 UintVector 序列化保存到文件。

        支持以下文件格式：
            - `.txt`(扩展名部分包含txt关键词即可)：跨平台，基本不可读。
            - `.xml`(扩展名部分包含xml关键词即可)：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.vui_save(self.handle, make_c_char_p(path))

    core.use(None, 'vui_load', c_void_p, c_char_p)

    def load(self, path: str):
        """从文件加载序列化的 UintVector 数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.vui_load(self.handle, make_c_char_p(path))

    core.use(None, 'vui_print', c_void_p, c_char_p)

    def print_file(self, path: str):
        """将 UintVector 内容打印到文件中。

        Args:
            path (str): 打印文件的路径。

        Note:
            必须使用纯英文路径。
        """
        if isinstance(path, str):
            core.vui_print(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'vui_size', c_void_p)

    @property
    def size(self) -> int:
        """获取 UintVector 的大小。

        Returns:
            int: UintVector 的大小。
        """
        return core.vui_size(self.handle)

    core.use(None, 'vui_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value: int):
        """设置 UintVector 的大小。

        Args:
            value (int): 新的 UintVector 大小。
        """
        core.vui_resize(self.handle, value)

    def __len__(self) -> int:
        """返回 UintVector 的大小。

        Returns:
            int: UintVector 的大小。
        """
        return self.size

    core.use(c_size_t, 'vui_get', c_void_p, c_size_t)

    def __getitem__(self, index: int) -> Optional[int]:
        """获取指定索引位置的元素。

        Args:
            index (int): 元素的索引。

        Returns:
            int: 指定索引位置的元素。

        Note:
            如果索引越界，则返回 None。
        """
        idx_ = get_index(index, self.size)
        if idx_ is not None:
            return core.vui_get(self.handle, idx_)
        else:
            return None

    core.use(None, 'vui_set',
             c_void_p, c_size_t, c_size_t)

    def __setitem__(self, index: int, value: int):
        """设置指定索引位置的元素。

        Args:
            index (int): 元素的索引。
            value (int): 要设置的值。

        Note:
            如果索引越界，则设置失败。
        """
        idx_ = get_index(index, self.size)
        if idx_ is not None:
            core.vui_set(self.handle, idx_, value)

    def append(self, value: int):
        """向 UintVector 尾部追加元素。

        Args:
            value (int): 要追加的元素。
        """
        key = self.size
        self.size += 1
        self[key] = value

    def set(self, value: List[int]):
        """将列表赋值给 UintVector。 todo: 使用ptr接口效率更高

        Args:
            value (list): 要赋值的列表。
        """
        count = len(value)
        self.size = count
        if count > 0:
            p = self.pointer
            for i in range(count):
                p[i] = value[i]

    def to_list(self) -> List[int]:
        """将 UintVector 转换为 Python 列表。  todo: 使用ptr接口效率更高

        Returns:
            list: 转换后的 Python 列表。
        """
        count = self.size
        if count > 0:
            p = self.pointer
            return [p[i] for i in range(count)]
        else:
            return []

    core.use(c_void_p, 'vui_pointer', c_void_p)

    @property
    def pointer(self) -> Any:
        """获取 UintVector 首个元素的指针。

        Returns:
            ctypes.POINTER(c_size_t): 指向首个元素的指针。

        Note:
            如果 UintVector 为空，则返回 None。
        """
        ptr = core.vui_pointer(self.handle)
        if ptr:
            return ctypes.cast(ptr, POINTER(c_size_t))
        else:
            return None


class StrVector(HasHandle):
    """映射 C++ 类：std::vector<std::string>。

    该类用于管理动态字符串数组，支持初始化、元素访问等操作。
    """
    core.use(c_void_p, 'new_vs')
    core.use(None, 'del_vs', c_void_p)

    def __init__(self, handle=None):
        """初始化 StrVector 对象。

        Args:
            handle: 已有的句柄。如果提供，则使用给定的句柄初始化对象。
        """
        super().__init__(handle, core.new_vs, core.del_vs)

    def __repr__(self):
        return f'{type(self).__name__}(handle={int(self.handle)}, size={self.size})'

    core.use(c_size_t, 'vs_size', c_void_p)

    @property
    def size(self):
        """获取 StrVector 的大小。

        Returns:
            int: StrVector 的大小。
        """
        return core.vs_size(self.handle)

    core.use(None, 'vs_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        """设置 StrVector 的大小。

        Args:
            value (int): 新的 StrVector 大小。
        """
        core.vs_resize(self.handle, value)

    def __len__(self):
        """返回 StrVector 的大小。

        Returns:
            int: StrVector 的大小。
        """
        return self.size

    core.use(c_void_p, 'vs_get',
             c_void_p, c_size_t)

    def get(self, index):
        index = get_index(index, self.size)
        if index is not None:
            handle = core.vs_get(self.handle, index)
            return String(handle=handle)
        else:
            return None

    def __getitem__(self, index):
        """获取指定索引位置的字符串。

        Args:
            index (int): 元素的索引。

        Returns:
            str: 指定索引位置的字符串。

        Note:
            如果索引越界，则返回 None。
        """
        s = self.get(index)
        if s is not None:
            return s.to_str()
        else:
            return None

    def __setitem__(self, index, value):
        """设置指定索引位置的字符串。

        Args:
            index (int): 元素的索引。
            value (str): 要设置的字符串。

        Note:
            如果索引越界，则设置失败。
        """
        s = self.get(index)
        if s is not None:
            s.assign(value)

    def set(self, value):
        """将列表赋值给 StrVector。

        Args:
            value (list): 要赋值的字符串列表。
        """
        count = len(value)
        self.size = count
        for i in range(count):
            self[i] = value[i]

    def to_list(self):
        """将 StrVector 转换为 Python 列表。

        Returns:
            list: 转换后的 Python 列表。
        """
        return [self[i] for i in range(len(self))]


class PtrVector(HasHandle):
    """映射 C++ 类：std::vector<void*>。

    该类用于管理动态指针数组，支持初始化、元素访问等操作。注意：PtrVector 仅存储句柄（handle），
    不保有数据，因此需要确保原始对象在使用期间不被销毁，否则可能导致内核读取时出现致命错误。

    Attributes:
        size: 指针数组的大小。
    """
    core.use(c_void_p, 'new_vp')
    core.use(None, 'del_vp', c_void_p)

    def __init__(self, value=None, handle=None):
        """初始化 PtrVector 对象。

        Args:
            value (list, optional): 用于初始化指针数组的句柄列表。
            handle: 已有的句柄。如果提供，则使用给定的句柄初始化对象。
        """
        super().__init__(handle, core.new_vp, core.del_vp)
        if handle is None:
            if value is not None:
                self.set(value)

    def __repr__(self):
        return f'{type(self).__name__}(handle={int(self.handle)}, size={self.size})'

    core.use(c_size_t, 'vp_size', c_void_p)

    @property
    def size(self):
        """获取指针数组的大小。

        Returns:
            int: 指针数组的大小。
        """
        return core.vp_size(self.handle)

    core.use(None, 'vp_resize',
             c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        """设置指针数组的大小，并使用 nullptr 填充新元素。

        Args:
            value (int): 新的指针数组大小。
        """
        core.vp_resize(self.handle, value)

    def __len__(self):
        """返回指针数组的大小。

        Returns:
            int: 指针数组的大小。
        """
        return self.size

    core.use(c_void_p, 'vp_get',
             c_void_p, c_size_t)

    def __getitem__(self, index):
        """获取指定索引位置的句柄。

        Args:
            index (int): 元素的索引。

        Returns:
            c_void_p: 指定索引位置的句柄。

        Note:
            如果索引越界，则返回 None。
        """
        index = get_index(index, self.size)
        if index is not None:
            return core.vp_get(self.handle, index)
        return None

    core.use(None, 'vp_set',
             c_void_p, c_size_t, c_void_p)

    def __setitem__(self, index, value):
        """设置指定索引位置的句柄。

        Args:
            index (int): 元素的索引。
            value (c_void_p): 要设置的句柄。

        Note:
            如果索引越界，则设置失败。
        """
        index = get_index(index, self.size)
        if index is not None:
            core.vp_set(self.handle, index, value)

    def set(self, value):
        """将句柄列表赋值给指针数组。

        Args:
            value (list): 要赋值的句柄列表。
        """
        self.size = len(value)
        for i in range(len(value)):
            self[i] = value[i]

    def to_list(self):
        """将指针数组转换为 Python 列表。

        Returns:
            list: 转换后的 Python 列表。
        """
        elements = []
        for i in range(len(self)):
            elements.append(self[i])
        return elements

    def get_object(self, index, rtype):
        """将指定索引位置的句柄转换为 HasHandle 对象。

        Args:
            index (int): 元素的索引。
            rtype (type): 目标对象的类型（必须是 HasHandle 的子类）。

        Returns:
            HasHandle: 转换后的对象。

        Note:
            如果索引越界或句柄无效，则返回 None。
        """
        if index < len(self) and rtype is not None:
            handle = self[index]
            if handle:
                return rtype(handle=handle)
        return None

    def append(self, handle):
        """向指针数组尾部追加句柄。

        Args:
            handle (c_void_p): 要追加的句柄。

        Returns:
            PtrVector: 当前 PtrVector 对象（用于链式调用）。
        """
        ind = self.size
        self.size += 1
        self[ind] = handle
        return self

    @staticmethod
    def from_objects(objects):
        """从给定的对象列表中构建 PtrVector。

        Args:
            objects (list): 对象列表，对象必须是 HasHandle 类型。

        Returns:
            PtrVector: 构建的 PtrVector 对象。
        """
        return PtrVector(value=[o.handle for o in objects])
