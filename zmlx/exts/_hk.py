from ctypes import c_void_p, c_char_p, c_longlong
from typing import Optional

from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._utils import (
    HasHandle, make_parent, check_ipath
)


class HasKeys(HasHandle):
    """
    动态属性的管理
    """
    core.use(c_void_p, 'new_hk')
    core.use(None, 'del_hk', c_void_p)

    def __init__(self, path: Optional[str] = None, *, handle: Optional[c_void_p] = None):
        super().__init__(handle, core.new_hk, core.del_hk)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
        self._inf = None

    core.use(None, 'hk_save', c_void_p, c_char_p)

    def save(self, path: str):
        """序列化保存到文件。

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
            core.hk_save(self.handle, make_c_char_p(path))

    core.use(None, 'hk_load', c_void_p, c_char_p)

    def load(self, path: str):
        """从文件加载序列化的数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.hk_load(self.handle, make_c_char_p(path))

    core.use(c_longlong, 'hk_inf')

    def get_inf(self):
        """
        当属性不存在的时候返回的一个无穷大的数值(longlong类型)
        """
        if self._inf is None:
            self._inf = core.hk_inf()
        return self._inf

    core.use(c_longlong, 'hk_reg_ty_key', c_void_p, c_char_p, c_char_p)
    core.use(c_longlong, 'hk_reg_key', c_void_p, c_char_p)

    def reg_key(self, key, *, ty=None):
        """
        注册一个属性key并且返回key的值
        """
        if ty is None:
            res = core.hk_reg_key(self.handle, make_c_char_p(key))
        else:
            res = core.hk_reg_ty_key(self.handle, make_c_char_p(ty), make_c_char_p(key))
        if res == self.get_inf():
            return None
        else:
            return res

    core.use(c_longlong, 'hk_get_key', c_void_p, c_char_p)

    def get_key(self, key, *, ty=None):
        """
        返回key的值
        """
        if ty is not None:
            key = ty + key
        res = core.hk_get_key(self.handle, make_c_char_p(key))
        if res == self.get_inf():
            return None
        else:
            return res

    core.use(None, 'hk_set_key', c_void_p, c_char_p, c_longlong)

    def set_key(self, key, value):
        """
        设置key的值
        """
        core.hk_set_key(self.handle, make_c_char_p(key), value)

    core.use(None, 'hk_del_key', c_void_p, c_char_p)

    def del_key(self, key):
        """
        删除一个key
        """
        core.hk_set_key(self.handle, make_c_char_p(key))
