from ctypes import c_void_p, c_char_p, c_size_t

from zmlx.exts._ary import Array3, Array2
from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._fmap import FileMap
from zmlx.exts._tensor import Tensor3, Tensor2
from zmlx.exts._utils import HasHandle, make_parent, check_ipath


class Coord2(HasHandle):
    """二维坐标系表示类，包含原点和坐标轴方向信息。"""
    core.use(c_void_p, 'new_coord2')
    core.use(None, 'del_coord2', c_void_p)

    def __init__(self, origin=None, xdir=None, path=None, handle=None):
        """初始化二维坐标系。

        Args:
            origin (Array2|list|tuple, optional): 坐标系原点坐标
            xdir (Array2|list|tuple, optional): X轴方向向量
            path (str, optional): 序列化文件加载路径
            handle: 现有底层对象句柄
        """
        super().__init__(handle, core.new_coord2, core.del_coord2)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if origin is not None and xdir is not None:
                self.set(origin, xdir)

    core.use(None, 'coord2_save', c_void_p, c_char_p)

    def save(self, path):
        """保存坐标系数据到文件。

        Args:
            path (str): 文件路径，扩展名决定格式(.txt/.xml/其他=二进制)
        """
        if isinstance(path, str):
            make_parent(path)
            core.coord2_save(self.handle, make_c_char_p(path))

    core.use(None, 'coord2_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载坐标系数据。

        Args:
            path (str): 文件路径，自动识别序列化格式
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.coord2_load(self.handle, make_c_char_p(path))

    core.use(None, 'coord2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'coord2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """序列化到文件映射对象。

        Args:
            fmt (str): 序列化格式，可选text/xml/binary

        Returns:
            FileMap: 包含序列化数据的文件映射
        """
        fmap = FileMap()
        core.coord2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt='binary'):
        """从文件映射加载数据。

        Args:
            fmap (FileMap): 包含序列化数据的文件映射
            fmt (str): 必须与写入时的序列化格式一致
        """
        assert isinstance(fmap, FileMap)
        core.coord2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """二进制序列化访问接口(property形式)。"""
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    def __repr__(self):
        return (f'{type(self).__name__}(handle={int(self.handle)}, '
                f'origin={self.origin}, xdir={self.xdir})')

    def __str__(self):
        """返回坐标系的字符串表示。

        Returns:
            str: 格式为 zml.Coord2(origin=..., xdir=...)
        """
        return f'{type(self).__name__}(origin = {self.origin}, xdir = {self.xdir})'

    core.use(None, 'coord2_set', c_void_p, c_size_t, c_size_t)

    def set(self, origin, xdir):
        """设置坐标系参数。

        Args:
            origin (Array2|list|tuple): 原点坐标，自动转换为Array2类型
            xdir (Array2|list|tuple): X轴方向向量，自动转换为Array2类型
        """
        if not isinstance(origin, Array2):
            origin = Array2.from_list(origin)
        if not isinstance(xdir, Array2):
            xdir = Array2.from_list(xdir)
        core.coord2_set(self.handle, origin.handle, xdir.handle)

    core.use(c_void_p, 'coord2_get_origin', c_void_p)

    @property
    def origin(self) -> Array2:
        """获取坐标系原点。

        Returns:
            Array2: 原点坐标向量
        """
        return Array2(handle=core.coord2_get_origin(self.handle))

    core.use(None, 'coord2_get_xdir',
             c_void_p, c_size_t)

    @property
    def xdir(self) -> Array2:
        """获取X轴单位方向向量。

        Returns:
            Array2: 归一化后的方向向量
        """
        temp = Array2()
        core.coord2_get_xdir(self.handle, temp.handle)
        return temp

    core.use(None, 'coord2_get_ydir', c_void_p, c_size_t)

    @property
    def ydir(self) -> Array2:
        """获取Y轴单位方向向量（自动正交化）。

        Returns:
            Array2: 垂直于X轴的归一化向量
        """
        temp = Array2()
        core.coord2_get_ydir(self.handle, temp.handle)
        return temp

    core.use(None, 'coord2_view_array2', c_void_p, c_size_t, c_size_t, c_size_t)
    core.use(None, 'coord2_view_tensor2', c_void_p, c_size_t, c_size_t, c_size_t)

    def view(self, coord, o, buffer=None):
        """执行坐标系转换。

        Args:
            coord (Coord2): 目标坐标系
            o (Array2|Tensor2): 需要转换的向量或张量
            buffer (Array2|Tensor2, optional): 存储结果的缓冲区

        Returns:
            Array2|Tensor2: 转换后的结果

        Raises:
            TypeError: 当输入参数类型不符合要求时
        """
        assert isinstance(coord, Coord2)
        if isinstance(o, Array2):
            if not isinstance(buffer, Array2):
                buffer = Array2()
            core.coord2_view_array2(self.handle, buffer.handle, coord.handle,
                                    o.handle)
            return buffer
        elif isinstance(o, Tensor2):
            if not isinstance(buffer, Tensor2):
                buffer = Tensor2()
            core.coord2_view_tensor2(self.handle, buffer.handle, coord.handle,
                                     o.handle)
            return buffer
        else:
            return None

    core.use(None, 'coord2_clone', c_void_p, c_void_p)

    def clone(self, other):
        """
        拷贝所有的数据。
        """
        if other is not None:
            assert isinstance(other, Coord2)
            core.coord2_clone(self.handle, other.handle)
        return self

    def get_copy(self):
        """
        获取当前对象的拷贝。
        """
        result = Coord2()
        result.clone(self)
        return result


class Coord3(HasHandle):
    """三维笛卡尔坐标系，用于点和张量的坐标转换。"""
    core.use(c_void_p, 'new_coord3')
    core.use(None, 'del_coord3', c_void_p)

    def __init__(self, origin=None, xdir=None, ydir=None, path=None, handle=None):
        """初始化三维坐标系。

        Args:
            origin (Array3|list|tuple, optional): 坐标系原点坐标
            xdir (Array3|list|tuple, optional): X轴方向向量
            ydir (Array3|list|tuple, optional): Y轴方向向量
            path (str, optional): 序列化文件加载路径
            handle: 现有底层对象句柄（存在时忽略其他参数）
        """
        super().__init__(handle, core.new_coord3, core.del_coord3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if origin is not None and xdir is not None and ydir is not None:
                self.set(origin, xdir, ydir)
        else:
            assert origin is None and xdir is None and ydir is None

    core.use(None, 'coord3_save', c_void_p, c_char_p)

    def save(self, path):
        """保存坐标系数据到文件。

        Args:
            path (str): 文件路径，扩展名决定格式(.txt/.xml/其他=二进制)
        """
        if isinstance(path, str):
            make_parent(path)
            core.coord3_save(self.handle, make_c_char_p(path))

    core.use(None, 'coord3_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载坐标系数据。

        Args:
            path (str): 文件路径，自动识别序列化格式
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.coord3_load(self.handle, make_c_char_p(path))

    core.use(None, 'coord3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'coord3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """序列化到文件映射对象。

        Args:
            fmt (str): 序列化格式，可选text/xml/binary

        Returns:
            FileMap: 包含序列化数据的文件映射
        """
        fmap = FileMap()
        core.coord3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt='binary'):
        """从文件映射加载数据。

        Args:
            fmap (FileMap): 包含序列化数据的文件映射
            fmt (str): 必须与写入时的序列化格式一致
        """
        assert isinstance(fmap, FileMap)
        core.coord3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """二进制序列化访问接口(property形式)。"""
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    def __repr__(self):
        return (f'{type(self).__name__}(handle={int(self.handle)}, '
                f'origin={self.origin}, xdir={self.xdir}, ydir={self.ydir})')

    def __str__(self):
        """获取坐标系的字符串表示。

        Returns:
            str: 格式为 zml.Coord3(origin=..., xdir=..., ydir=...)
        """
        return (f'{type(self).__name__}(origin = {self.origin}, '
                f'xdir = {self.xdir}, ydir = {self.ydir})')

    core.use(None, 'coord3_set', c_void_p, c_void_p, c_void_p, c_void_p)

    def set(self, origin, xdir, ydir):
        """设置坐标系参数。

        Args:
            origin (Array3|list|tuple): 原点坐标，自动转换为Array3类型
            xdir (Array3|list|tuple): X轴方向向量，自动转换为Array3类型
            ydir (Array3|list|tuple): Y轴方向向量，自动转换为Array3类型
        """
        if not isinstance(origin, Array3):
            origin = Array3.from_list(origin)
        if not isinstance(xdir, Array3):
            xdir = Array3.from_list(xdir)
        if not isinstance(ydir, Array3):
            ydir = Array3.from_list(ydir)
        core.coord3_set(self.handle, origin.handle, xdir.handle, ydir.handle)

    core.use(c_void_p, 'coord3_get_origin', c_void_p)

    @property
    def origin(self):
        """获取坐标系原点（可修改的引用）。

        Returns:
            Array3: 原点坐标的引用
        """
        return Array3(handle=core.coord3_get_origin(self.handle))

    core.use(None, 'coord3_get_xdir', c_void_p, c_size_t)

    @property
    def xdir(self):
        """获取X轴单位方向向量（自动正交化）。

        Returns:
            Array3: 归一化后的X方向向量
        """
        temp = Array3()
        core.coord3_get_xdir(self.handle, temp.handle)
        return temp

    core.use(None, 'coord3_get_ydir', c_void_p, c_size_t)

    @property
    def ydir(self):
        """获取Y轴单位方向向量（自动正交化）。

        Returns:
            Array3: 与X轴垂直的归一化向量
        """
        temp = Array3()
        core.coord3_get_ydir(self.handle, temp.handle)
        return temp

    core.use(None, 'coord3_view_array3', c_void_p, c_size_t, c_size_t, c_size_t)
    core.use(None, 'coord3_view_tensor3', c_void_p, c_size_t, c_size_t, c_size_t)

    def view(self, coord, o, buffer=None):
        """执行坐标系间对象转换。

        Args:
            coord (Coord3): 原始坐标系
            o (Array3|Tensor3): 需要转换的向量或张量
            buffer (Array3|Tensor3, optional): 存储结果的缓冲区

        Returns:
            Array3|Tensor3: 转换后的对象

        Raises:
            TypeError: 当输入类型不符合要求时
        """
        assert isinstance(coord, Coord3)
        if isinstance(o, Array3):
            if not isinstance(buffer, Array3):
                buffer = Array3()
            core.coord3_view_array3(self.handle, buffer.handle, coord.handle,
                                    o.handle)
            return buffer
        elif isinstance(o, Tensor3):
            if not isinstance(buffer, Tensor3):
                buffer = Tensor3()
            core.coord3_view_tensor3(self.handle, buffer.handle, coord.handle,
                                     o.handle)
            return buffer
        else:
            return None

    core.use(None, 'coord3_clone', c_void_p, c_void_p)

    def clone(self, other):
        """
        拷贝所有的数据。
        """
        if other is not None:
            assert isinstance(other, Coord3)
            core.coord3_clone(self.handle, other.handle)
        return self

    def get_copy(self):
        """
        获取当前对象的拷贝。
        """
        result = Coord3()
        result.clone(self)
        return result
