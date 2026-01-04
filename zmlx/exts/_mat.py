from ctypes import c_void_p, c_char_p, c_size_t, c_double, c_bool

from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._fmap import FileMap
from zmlx.exts._tensor import Tensor3
from zmlx.exts._utils import HasHandle, get_index, make_parent, check_ipath


class Matrix2(HasHandle):
    """映射 C++ 类：zml::matrix_ty<double, 2>。

    该类用于管理二维矩阵，支持初始化、序列化、元素访问、填充等操作。
    """
    core.use(c_void_p, 'new_mat2')
    core.use(None, 'del_mat2', c_void_p)

    def __init__(self, path=None, handle=None, size=None, value=None):
        """初始化 Matrix2 对象。

        Args:
            path (str, optional): 从文件加载矩阵的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
            size (tuple, optional): 矩阵的大小 (size_0, size_1)。
            value (float, optional): 用于填充矩阵的值。
        """
        super().__init__(handle, core.new_mat2, core.del_mat2)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if size is not None:
                self.resize(size)
            if value is not None:
                self.fill(value)

    def __repr__(self):
        return f'{type(self).__name__}(handle={int(self.handle)}, size={self.size})'

    def __str__(self):
        """返回 Matrix2 的字符串表示。

        Returns:
            str: Matrix2 的字符串表示。
        """
        return f'{type(self).__name__}(size={self.size})'

    core.use(None, 'mat2_save',
             c_void_p, c_char_p)

    def save(self, path):
        """将矩阵序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.mat2_save(self.handle, make_c_char_p(path))

    core.use(None, 'mat2_load',
             c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化的矩阵数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.mat2_load(self.handle, make_c_char_p(path))

    core.use(None, 'mat2_write_fmap',
             c_void_p, c_void_p, c_char_p)
    core.use(None, 'mat2_read_fmap',
             c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """将矩阵数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
            默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.mat2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt='binary'):
        """从 FileMap 中读取序列化的矩阵数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
            默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.mat2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """获取矩阵的二进制序列化数据。

        Returns:
            FileMap: 包含二进制序列化数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """从二进制序列化数据加载矩阵。

        Args:
            value (FileMap): 包含二进制序列化数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(c_size_t, 'mat2_size_0', c_void_p)
    core.use(c_size_t, 'mat2_size_1', c_void_p)

    @property
    def size_0(self):
        """获取矩阵的第一维度大小。

        Returns:
            int: 矩阵的第一维度大小。
        """
        return core.mat2_size_0(self.handle)

    @property
    def size_1(self):
        """获取矩阵的第二维度大小。

        Returns:
            int: 矩阵的第二维度大小。
        """
        return core.mat2_size_1(self.handle)

    core.use(None, 'mat2_resize',
             c_void_p, c_size_t, c_size_t)

    def resize(self, value):
        """调整矩阵的大小。

        Args:
            value (tuple): 新的矩阵大小 (size_0, size_1)。
        """
        assert len(value) == 2
        core.mat2_resize(self.handle, value[0], value[1])

    @property
    def size(self):
        """获取矩阵的大小。

        Returns:
            tuple: 矩阵的大小 (size_0, size_1)。
        """
        return self.size_0, self.size_1

    @size.setter
    def size(self, value):
        """设置矩阵的大小。

        Args:
            value (tuple): 新的矩阵大小 (size_0, size_1)。
        """
        self.resize(value)

    core.use(c_double, 'mat2_get',
             c_void_p, c_size_t, c_size_t)

    def get(self, key0, key1):
        """获取矩阵中指定位置的元素。

        Args:
            key0 (int): 第一维度的索引。
            key1 (int): 第二维度的索引。

        Returns:
            float: 指定位置的元素值。

        Note:
            如果索引越界，则返回 None。
        """
        key0 = get_index(key0, self.size_0)
        key1 = get_index(key1, self.size_1)
        if key0 is not None and key1 is not None:
            assert key0 < self.size_0
            assert key1 < self.size_1
            return core.mat2_get(self.handle, key0, key1)
        return None

    core.use(None, 'mat2_set',
             c_void_p, c_size_t, c_size_t, c_double)

    def set(self, key0, key1, value):
        """设置矩阵中指定位置的元素。

        Args:
            key0 (int): 第一维度的索引。
            key1 (int): 第二维度的索引。
            value (float): 要设置的值。

        Note:
            如果索引越界，则设置失败。
        """
        key0 = get_index(key0, self.size_0)
        key1 = get_index(key1, self.size_1)
        if key0 is not None and key1 is not None:
            assert key0 < self.size_0
            assert key1 < self.size_1
            core.mat2_set(self.handle, key0, key1, value)

    def __getitem__(self, key):
        """获取矩阵中指定位置的元素。

        Args:
            key (tuple): 包含两个整数的元组，表示 (key0, key1)。

        Returns:
            float: 指定位置的元素值。
        """
        assert len(key) == 2
        i = key[0]
        j = key[1]
        return self.get(i, j)

    def __setitem__(self, key, value):
        """设置矩阵中指定位置的元素。

        Args:
            key (tuple): 包含两个整数的元组，表示 (key0, key1)。
            value (float): 要设置的值。
        """
        assert len(key) == 2
        i = key[0]
        j = key[1]
        self.set(i, j, value)

    core.use(None, 'mat2_clone',
             c_void_p, c_void_p)

    def clone(self, other):
        """克隆另一个矩阵的数据到当前矩阵。

        Args:
            other (Matrix2): 要克隆的矩阵对象。

        Returns:
            Matrix2: 当前矩阵对象（用于链式调用）。
        """
        if other is not None:
            assert isinstance(other, Matrix2)
            core.mat2_clone(self.handle, other.handle)
        return self

    core.use(None, 'mat2_fill',
             c_void_p, c_double, c_bool)

    def fill(self, value, parallel=False):
        """填充矩阵的所有元素为指定值。

        Args:
            value (float): 要填充的值。
            parallel (bool, optional): 是否并行填充。默认为 False。
        """
        core.mat2_fill(self.handle, value, parallel)


class Matrix3(HasHandle):
    """映射 C++ 类：zml::matrix_ty<double, 3>。

    该类用于管理三维浮点矩阵，支持初始化、序列化、元素访问、填充等操作。
    """
    core.use(c_void_p, 'new_mat3')
    core.use(None, 'del_mat3',
             c_void_p)

    def __init__(self, path=None, handle=None, size=None, value=None):
        """初始化 Matrix3 对象。

        Args:
            path (str, optional): 从文件加载矩阵的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
            size (tuple, optional): 矩阵的三维大小 (size_0, size_1, size_2)。
            value (float, optional): 用于填充矩阵的初始值。
        """
        super().__init__(handle, core.new_mat3, core.del_mat3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if size is not None:
                self.resize(size)
            if value is not None:
                self.fill(value)

    def __repr__(self):
        return f'{type(self).__name__}(handle={int(self.handle)}, size={self.size})'

    def __str__(self):
        """返回 Matrix3 的字符串表示。

        Returns:
            str: Matrix3 的字符串表示。
        """
        return f'{type(self).__name__}(size={self.size})'

    core.use(None, 'mat3_save', c_void_p, c_char_p)

    def save(self, path):
        """将矩阵序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.mat3_save(self.handle, make_c_char_p(path))

    core.use(None, 'mat3_load',
             c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化的矩阵数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.mat3_load(self.handle, make_c_char_p(path))

    core.use(None, 'mat3_write_fmap',
             c_void_p, c_void_p, c_char_p)
    core.use(None, 'mat3_read_fmap',
             c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """将矩阵数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
            默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.mat3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt='binary'):
        """从 FileMap 中读取序列化的矩阵数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
                默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.mat3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """获取矩阵的二进制序列化数据。

        Returns:
            FileMap: 包含二进制序列化数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """从二进制序列化数据加载矩阵。

        Args:
            value (FileMap): 包含二进制序列化数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(c_size_t, 'mat3_size_0', c_void_p)
    core.use(c_size_t, 'mat3_size_1', c_void_p)
    core.use(c_size_t, 'mat3_size_2', c_void_p)

    @property
    def size_0(self):
        """获取矩阵第一维度的大小。

        Returns:
            int: 第一维度的大小。
        """
        return core.mat3_size_0(self.handle)

    @property
    def size_1(self):
        """获取矩阵第二维度的大小。

        Returns:
            int: 第二维度的大小。
        """
        return core.mat3_size_1(self.handle)

    @property
    def size_2(self):
        """获取矩阵第三维度的大小。

        Returns:
            int: 第三维度的大小。
        """
        return core.mat3_size_2(self.handle)

    core.use(None, 'mat3_resize',
             c_void_p, c_size_t, c_size_t, c_size_t)

    def resize(self, value):
        """调整矩阵的三维大小。

        Args:
            value (tuple): 新的三维大小 (size_0, size_1, size_2)。
        """
        assert len(value) == 3
        core.mat3_resize(self.handle, value[0], value[1], value[2])

    @property
    def size(self):
        """获取矩阵的三维大小。

        Returns:
            tuple: 包含三个维度大小的元组 (size_0, size_1, size_2)。
        """
        return self.size_0, self.size_1, self.size_2

    @size.setter
    def size(self, value):
        """设置矩阵的三维大小。

        Args:
            value (tuple): 新的三维大小 (size_0, size_1, size_2)。
        """
        self.resize(value)

    core.use(c_double, 'mat3_get',
             c_void_p, c_size_t, c_size_t, c_size_t)

    def get(self, key0, key1, key2):
        """获取矩阵中指定位置的元素。

        Args:
            key0 (int): 第一维度的索引。
            key1 (int): 第二维度的索引。
            key2 (int): 第三维度的索引。

        Returns:
            float: 指定位置的元素值。

        Note:
            如果索引越界，则返回 None。
        """
        key0 = get_index(key0, self.size_0)
        key1 = get_index(key1, self.size_1)
        key2 = get_index(key2, self.size_2)
        if key0 is not None and key1 is not None and key2 is not None:
            return core.mat3_get(self.handle, key0, key1, key2)
        else:
            return None

    core.use(None, 'mat3_set',
             c_void_p, c_size_t, c_size_t, c_size_t, c_double)

    def set(self, key0, key1, key2, value):
        """设置矩阵中指定位置的元素。

        Args:
            key0 (int): 第一维度的索引。
            key1 (int): 第二维度的索引。
            key2 (int): 第三维度的索引。
            value (float): 要设置的值。

        Note:
            如果索引越界，则设置失败。
        """
        key0 = get_index(key0, self.size_0)
        key1 = get_index(key1, self.size_1)
        key2 = get_index(key2, self.size_2)
        if key0 is not None and key1 is not None and key2 is not None:
            core.mat3_set(self.handle, key0, key1, key2, value)

    def __getitem__(self, key):
        """通过元组索引获取元素。

        Args:
            key (tuple): 包含三个整数的元组，表示 (key0, key1, key2)。

        Returns:
            float: 指定位置的元素值。
        """
        assert len(key) == 3
        return self.get(*key)

    def __setitem__(self, key, value):
        """通过元组索引设置元素。

        Args:
            key (tuple): 包含三个整数的元组，表示 (key0, key1, key2)。
            value (float): 要设置的值。
        """
        assert len(key) == 3
        self.set(key[0], key[1], key[2], value)

    core.use(None, 'mat3_clone',
             c_void_p, c_void_p)

    def clone(self, other):
        """克隆另一个矩阵的数据到当前矩阵。

        Args:
            other (Matrix3): 要克隆的矩阵对象。

        Returns:
            Matrix3: 当前矩阵对象（用于链式调用）。
        """
        if other is not None:
            assert isinstance(other, Matrix3)
            core.mat3_clone(self.handle, other.handle)
        return self

    core.use(None, 'mat3_fill',
             c_void_p, c_double, c_bool)

    def fill(self, value, parallel=False):
        """填充矩阵的所有元素为指定值。

        Args:
            value (float): 要填充的值。
            parallel (bool, optional): 是否在内核层面并行填充。默认为 False。
        """
        core.mat3_fill(self.handle, value, parallel)


class Tensor3Matrix3(HasHandle):
    """映射 C++ 类：zml::matrix_ty<zml::tensor3_ty, 3>。

    该类用于管理三维张量矩阵，支持初始化、序列化、元素访问及插值等操作。
    """
    core.use(c_void_p, 'new_ts3mat3')
    core.use(None, 'del_ts3mat3',
             c_void_p)

    def __init__(self, path=None, handle=None):
        """初始化 Tensor3Matrix3 对象。

        Args:
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super().__init__(handle, core.new_ts3mat3,
                         core.del_ts3mat3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    def __repr__(self):
        return f'{type(self).__name__}(handle={int(self.handle)}, size={self.size})'

    core.use(None, 'ts3mat3_save',
             c_void_p, c_char_p)

    def save(self, path):
        """将张量矩阵序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.ts3mat3_save(self.handle, make_c_char_p(path))

    core.use(None, 'ts3mat3_load',
             c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化的张量矩阵数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.ts3mat3_load(self.handle, make_c_char_p(path))

    core.use(None, 'ts3mat3_write_fmap',
             c_void_p, c_void_p, c_char_p)
    core.use(None, 'ts3mat3_read_fmap',
             c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """将张量矩阵数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
                默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.ts3mat3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt='binary'):
        """从 FileMap 中读取序列化的张量矩阵数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
                默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.ts3mat3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """获取张量矩阵的二进制序列化数据。

        Returns:
            FileMap: 包含二进制序列化数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """从二进制序列化数据加载张量矩阵。

        Args:
            value (FileMap): 包含二进制序列化数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(c_size_t, 'ts3mat3_size_0', c_void_p)
    core.use(c_size_t, 'ts3mat3_size_1', c_void_p)
    core.use(c_size_t, 'ts3mat3_size_2', c_void_p)

    @property
    def size_0(self):
        """获取张量矩阵第一维度的大小。

        Returns:
            int: 第一维度的大小。
        """
        return core.ts3mat3_size_0(self.handle)

    @property
    def size_1(self):
        """获取张量矩阵第二维度的大小。

        Returns:
            int: 第二维度的大小。
        """
        return core.ts3mat3_size_1(self.handle)

    @property
    def size_2(self):
        """获取张量矩阵第三维度的大小。

        Returns:
            int: 第三维度的大小。
        """
        return core.ts3mat3_size_2(self.handle)

    core.use(None, 'ts3mat3_resize',
             c_void_p, c_size_t, c_size_t, c_size_t)

    def resize(self, value):
        """调整张量矩阵的三维大小。

        Args:
            value (tuple): 新的三维大小 (size_0, size_1, size_2)。

        Raises:
            AssertionError: 如果输入参数不是三元组。
        """
        assert len(value) == 3, 'The size must be a tuple of length 3.'
        core.ts3mat3_resize(self.handle, value[0], value[1], value[2])

    @property
    def size(self):
        """获取张量矩阵的三维大小。

        Returns:
            tuple: 包含三个维度大小的元组 (size_0, size_1, size_2)。
        """
        return self.size_0, self.size_1, self.size_2

    @size.setter
    def size(self, value):
        """设置张量矩阵的三维大小。

        Args:
            value (tuple): 新的三维大小 (size_0, size_1, size_2)。
        """
        self.resize(value)

    core.use(c_void_p, 'ts3mat3_get',
             c_void_p, c_size_t, c_size_t, c_size_t)

    def get(self, key0, key1, key2):
        """获取指定位置的张量元素。

        Args:
            key0 (int): 第一维度的索引。
            key1 (int): 第二维度的索引。
            key2 (int): 第三维度的索引。

        Returns:
            Tensor3: 指定位置的张量元素引用。

        Note:
            如果索引越界，则返回 None。
        """
        key0 = get_index(key0, self.size_0)
        key1 = get_index(key1, self.size_1)
        key2 = get_index(key2, self.size_2)
        if key0 is not None and key1 is not None and key2 is not None:
            return Tensor3(
                handle=core.ts3mat3_get(self.handle, key0, key1, key2))
        else:
            return None

    def __getitem__(self, key):
        """通过元组索引获取张量元素。

        Args:
            key (tuple): 包含三个整数的元组，表示 (key0, key1, key2)。

        Returns:
            Tensor3: 指定位置的张量元素引用。
        """
        assert len(key) == 3
        return self.get(*key)

    core.use(None, 'ts3mat3_clone',
             c_void_p, c_void_p)

    def clone(self, other):
        """克隆另一个张量矩阵的数据到当前矩阵。

        Args:
            other (Tensor3Matrix3): 要克隆的矩阵对象。

        Returns:
            Tensor3Matrix3: 当前矩阵对象（用于链式调用）。
        """
        if other is not None:
            assert isinstance(other, Tensor3Matrix3)
            core.ts3mat3_clone(self.handle, other.handle)
        return self

    core.use(None, 'ts3mat3_interp',
             c_void_p, c_void_p, c_double, c_double,
             c_double,
             c_double, c_double, c_double, c_double, c_double, c_double)

    def get_interp(self, left, step, pos, buffer=None):
        """执行三维插值计算。

        Args:
            left (tuple): 起始坐标三元组 (x0, y0, z0)。
            step (tuple): 步长三元组 (dx, dy, dz)。
            pos (tuple): 插值位置三元组 (x, y, z)。
            buffer (Tensor3, optional): 用于存储结果的缓冲区。默认为新建 Tensor3 对象。

        Returns:
            Tensor3: 包含插值结果的张量。

        Note:
            需要保证输入参数均为三元组格式。
        """
        assert len(left) == 3 and len(step) == 3 and len(pos) == 3
        if not isinstance(buffer, Tensor3):
            buffer = Tensor3()
        core.ts3mat3_interp(
            self.handle, buffer.handle, left[0], left[1],
            left[2],
            step[0], step[1], step[2], pos[0], pos[1], pos[2])
        return buffer
