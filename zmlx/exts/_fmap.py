import os
from ctypes import c_void_p, c_bool, c_char_p
from typing import Optional, Union, Any

from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._str import String
from zmlx.exts._utils import HasHandle, make_parent, check_ipath


class FileMap(HasHandle):
    """文件映射类，用于将文件夹及多个文件合并为单个文件（不压缩）。

    支持目录结构映射、键值存取、序列化保存/加载等操作。
    """
    core.use(c_void_p, 'new_fmap')
    core.use(None, 'del_fmap', c_void_p)

    def __init__(self, data: Optional[str] = None, path: Optional[str] = None, handle: Optional[c_void_p] = None):
        """初始化文件映射对象。

        Args:
            data (str, optional): 初始文本内容。
            path (str, optional): 从文件加载的路径。
            handle (c_void_p, optional): 已有的句柄。如果提供，则忽略其他参数。
        """
        super().__init__(handle, core.new_fmap, core.del_fmap)
        if handle is None:
            if data is not None:
                self.data = data
            if isinstance(path, str):
                self.load(path)
        else:
            assert data is not None and path is not None, "data and path must be None if handle is provided"

    core.use(c_bool, 'fmap_is_dir', c_void_p)

    @property
    def is_dir(self) -> bool:
        """判断当前映射是否为目录结构。

        Returns:
            bool: 如果是目录映射返回 True，否则返回 False。
        """
        return core.fmap_is_dir(self.handle)

    core.use(c_bool, 'fmap_has_key', c_void_p, c_char_p)

    def has_key(self, key: str) -> bool:
        """检查指定键是否存在。

        Args:
            key (str): 要检查的键名。

        Returns:
            bool: 如果键存在返回 True，否则返回 False。
        """
        return core.fmap_has_key(self.handle, make_c_char_p(key))

    core.use(c_void_p, 'fmap_get', c_void_p, c_char_p)

    def get(self, key: str) -> Optional['FileMap']:
        """获取指定键对应的子映射。

        Args:
            key (str): 要获取的键名。

        Returns:
            FileMap: 对应的子映射对象。

        Note:
            调用前必须先用 has_key 确认键存在，否则可能返回 None。
        """
        handle = core.fmap_get(self.handle, make_c_char_p(key))
        if handle:
            return FileMap(handle=handle)
        else:
            return None

    core.use(None, 'fmap_set', c_void_p, c_void_p, c_char_p)

    def set(self, key: str, fmap: Union[str, 'FileMap', Any]):
        """设置键值映射。

        Args:
            key (str): 要设置的键名。
            fmap (str, FileMap, Any): 可以是 FileMap 对象或可转换为字符串的数据。

        Example:
            # 设置文本内容
            fmap.set('config', 'value')
            # 设置嵌套映射
            sub_fmap = FileMap()
            fmap.set('subdir', sub_fmap)
        """
        if isinstance(fmap, FileMap):
            core.fmap_set(self.handle, fmap.handle, make_c_char_p(key))
        else:
            fmap = FileMap(data=fmap)
            assert isinstance(fmap, FileMap), "Failed to create FileMap from data"
            core.fmap_set(self.handle, fmap.handle, make_c_char_p(key))

    core.use(None, 'fmap_erase', c_void_p, c_char_p)

    def erase(self, key: str):
        """删除指定键的映射。

        Args:
            key (str): 要删除的键名。
        """
        core.fmap_erase(self.handle, make_c_char_p(key))

    core.use(None, 'fmap_write', c_void_p, c_char_p)

    def write(self, path: str):
        """将映射内容提取到文件系统。

        Args:
            path (str): 目标路径。
        """
        core.fmap_write(self.handle, make_c_char_p(path))

    core.use(None, 'fmap_read', c_void_p, c_char_p)

    def read(self, path: str):
        """从文件系统读取内容到映射。

        Args:
            path (str): 源路径。
        """
        core.fmap_read(self.handle, make_c_char_p(path))

    core.use(None, 'fmap_save', c_void_p, c_char_p)

    def save(self, path: str):
        """序列化保存为二进制格式。

        Args:
            path (str): 保存路径。

        Raises:
            AssertionError: 如果尝试保存为 txt 或 xml 格式。
        """
        if isinstance(path, str):
            ext = os.path.splitext(path)[-1].lower()
            assert ext != '.txt' and ext != '.xml'
            make_parent(path)
            core.fmap_save(self.handle, make_c_char_p(path))

    core.use(None, 'fmap_load', c_void_p, c_char_p)

    def load(self, path: str):
        """从文件加载序列化数据。

        Args:
            path (str): 加载路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.fmap_load(self.handle, make_c_char_p(path))

    core.use(c_char_p, 'fmap_get_char_p', c_void_p)

    @property
    def data(self) -> str:
        """获取文本内容。

        Returns:
            str: 解码后的字符串内容。
        """
        return core.fmap_get_char_p(self.handle).decode()

    core.use(None, 'fmap_set_char_p', c_void_p, c_char_p)

    @data.setter
    def data(self, value: Union[str, Any]):
        """设置文本内容。

        Args:
            value (any): 自动转换为字符串的内容。
        """
        if not isinstance(value, str):
            value = f'{value}'
        core.fmap_set_char_p(self.handle, make_c_char_p(value))

    core.use(c_void_p, 'fmap_get_data', c_void_p)

    @property
    def buffer(self) -> String:
        """获取二进制数据缓冲区。

        Returns:
            String: 二进制数据对象。
        """
        return String(handle=core.fmap_get_data(self.handle))

    core.use(None, 'fmap_clone', c_void_p, c_void_p)

    def clone(self, other: Optional['FileMap']) -> 'FileMap':
        """克隆另一个文件映射对象的数据。

        Args:
            other (FileMap): 要克隆的对象。

        Returns:
            FileMap: 当前对象（支持链式调用）。
        """
        if other is not None:
            assert isinstance(other, FileMap)
            core.fmap_clone(self.handle, other.handle)
        return self
