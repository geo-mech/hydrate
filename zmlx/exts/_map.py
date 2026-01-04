from ctypes import c_double, c_void_p, c_char_p

from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._utils import HasHandle
from zmlx.exts._vec import StrVector


class Map(HasHandle):
    """映射 C++ 类：std::map<std::string, double>。

    该类用于管理字符串到双精度浮点数的映射，支持初始化、获取键值对、设置键值对等操作。
    """
    core.use(c_void_p, 'new_string_double_map')
    core.use(None, 'del_string_double_map', c_void_p)

    def __init__(self, handle=None):
        """初始化 Map 对象。

        Args:
            handle: 已有的句柄。如果提供，则使用给定的句柄初始化对象。
        """
        super().__init__(handle, core.new_string_double_map,
                         core.del_string_double_map)

    core.use(c_void_p, 'string_double_map_get_keys',
             c_void_p)

    @property
    def keys(self):
        """获取映射中的所有键。

        Returns:
            list: 包含所有键的列表。
        """
        h = core.string_double_map_get_keys(self.handle)
        v = StrVector(handle=h)
        return v.to_list()

    core.use(c_double, 'string_double_map_get',
             c_void_p, c_char_p)

    def get(self, key):
        """获取指定键对应的值。

        Args:
            key (str): 要查找的键。

        Returns:
            float: 指定键对应的值。
        """
        return core.string_double_map_get(self.handle, make_c_char_p(key))

    core.use(None, 'string_double_map_set',
             c_void_p, c_char_p, c_double)

    def set(self, key, value):
        """设置指定键的值。

        Args:
            key (str): 要设置的键。
            value (float): 要设置的值。
        """
        core.string_double_map_set(self.handle, make_c_char_p(key), value)

    core.use(None, 'string_double_map_clear',
             c_void_p)

    def clear(self):
        """清空映射中的所有键值对。"""
        core.string_double_map_clear(self.handle)

    def from_dict(self, value):
        """从字典中加载键值对到映射中。

        Args:
            value (dict): 包含键值对的字典。
        """
        self.clear()
        for key, val in value.items():
            self.set(key, val)

    def to_dict(self):
        """将映射转换为字典。

        Returns:
            dict: 包含映射中所有键值对的字典。
        """
        r = {}
        for key in self.keys:
            r[key] = self.get(key)
        return r
