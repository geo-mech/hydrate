from ctypes import c_void_p, c_char_p, c_size_t
from typing import Optional

from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._utils import HasHandle


class String(HasHandle):
    """管理字符串对象的类，继承自 HasHandle 类。

    该类提供了字符串的创建、赋值、克隆和转换等方法，用于管理字符串对象。
    """
    core.use(None, 'del_str', c_void_p)
    core.use(c_void_p, 'new_str')

    def __init__(self, value: Optional[str] = None, handle: Optional[c_void_p] = None):
        """初始化 String 对象。

        Args:
            value (str): 要赋值给字符串的初始值。
            handle: 字符串对象的句柄。如果未提供，则会创建一个新的字符串对象。
        """
        super().__init__(handle, core.new_str, core.del_str)
        if handle is None:
            if value is not None:
                assert isinstance(value, str)
                self.assign(value)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(handle={int(self.handle)}, str='{self.to_str()}')"

    def __str__(self) -> str:
        """返回字符串对象的字符串表示。

        Returns:
            str: 字符串对象的字符串表示。
        """
        return self.to_str()

    def __len__(self) -> int:
        """返回字符串对象的长度。

        Returns:
            int: 字符串对象的长度。
        """
        return self.size

    core.use(c_size_t, 'str_size', c_void_p)

    @property
    def size(self) -> int:
        """获取字符串对象的长度。

        Returns:
            int: 字符串对象的长度。
        """
        return core.str_size(self.handle)

    core.use(None, 'str_assign', c_void_p, c_char_p)

    def assign(self, value: str):
        """给字符串对象赋值。

        Args:
            value (str): 要赋值给字符串对象的值。
        """
        if isinstance(value, String):
            self.clone(value)
        else:
            core.str_assign(self.handle, make_c_char_p(value))

    core.use(c_char_p, 'str_to_char_p', c_void_p)

    def to_str(self) -> str:
        """将字符串对象转换为 Python 字符串。

        Returns:
            str: 转换后的 Python 字符串。
        """
        if core.dll is not None:
            return core.str_to_char_p(self.handle).decode()
        else:
            return ''

    core.use(None, 'str_clone', c_void_p, c_void_p)

    def clone(self, other: Optional['String']) -> 'String':
        """克隆另一个字符串对象。

        Args:
            other (String): 要克隆的字符串对象。

        Returns:
            String: 当前字符串对象（用于链式调用）。
        """
        if other is not None:
            assert isinstance(other, String)
            core.str_clone(self.handle, other.handle)
        return self

    def make_copy(self, buf: Optional['String'] = None) -> 'String':
        """创建当前字符串对象的副本。

        Args:
            buf (String): 用于存储副本的字符串对象。如果未提供，则会创建一个新的字符串对象。

        Returns:
            String: 字符串对象的副本。
        """
        if not isinstance(buf, String):
            buf = String()
        assert isinstance(buf, String), f"buf must be String, but got {type(buf)}"
        buf.clone(self)
        return buf
