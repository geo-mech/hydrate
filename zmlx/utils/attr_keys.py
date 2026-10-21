"""属性名到整数 ID 的映射管理（自动从 0 编号）。

支持属性式/字典式访问、批量注册和 JSON 保存/加载。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""


from zmlx.system import warn
from zmlx.io import json_ex


def add_keys(*args):
    """在字典中注册键值（已弃用，请改用 ``AttrKeys``）。

    将从 0 开始尝试，直到发现不存在的数值再使用。
    若第一个参数为 ``AttrKeys`` 实例，则直接在其上操作并返回该实例。

    示例::

        keys = add_keys('x', 'y')
        print(keys)   # {'x': 0, 'y': 1}
        add_keys(keys, 'a', 'b', 'c')
        print(keys)   # {'x': 0, 'y': 1, 'a': 2, 'b': 3, 'c': 4}

    Args:
        *args: 一个可选 dict（或 ``AttrKeys``）后跟若干 str 键名。

    Returns:
        dict | AttrKeys: 添加了键值对的映射对象。
    """
    warn('The function zmlx.utils.AttrKeys.add_keys is deprecated '
                  '(will be removed after 2026-3-22), '
                  'please use zmlx.utils.AttrKeys instead.',
                  DeprecationWarning, stacklevel=2)

    # Check the input
    n1 = 0
    n2 = 0
    for key in args:
        if isinstance(key, AttrKeys):
            key.add_keys(*args)
            return key
        if isinstance(key, dict):
            n1 += 1
            continue
        if isinstance(key, str):
            n2 += 1
            continue
    assert n1 <= 1
    assert n1 + n2 == len(args)

    # Find the dict
    key_vals = None
    for key in args:
        if isinstance(key, dict):
            key_vals = key
            break
    if key_vals is None:
        key_vals = {}

    # Add keys
    for key in args:
        if not isinstance(key, str):
            continue
        if key not in key_vals:
            values = key_vals.values()
            succeed = False
            for val in range(len(key_vals) + 1):
                if val not in values:
                    key_vals[key] = val
                    succeed = True
                if succeed:
                    break
            assert succeed

    # Return the dict.
    return key_vals


class AttrKeys:
    """属性名到整数 ID 的映射管理器。

    自动从 0 开始编号，支持属性式访问（``keys.x``）、字典式访问（``keys['x']``）
    和 JSON 文件保存/加载。键名不存在时自动注册。
    """

    def __init__(self, *args, path=None):
        """初始化并注册键值，或从文件加载。

        ``path`` 与 ``*args`` 互斥：给定 ``path`` 时从 JSON 文件加载，
        否则将 ``*args`` 中的字符串依次注册。

        Args:
            *args: 要注册的键名（str）。
            path: JSON 文件路径，存在时从此加载（此时忽略 ``*args``）。
        """
        self.__keys = {}
        if path is not None:
            assert len(args) == 0
            self.load(path)
        else:
            self.add_keys(*args)

    def __str__(self):
        """返回内部映射的字符串表示。

        Returns:
            str: 键值对字符串。
        """
        return f'{self.__keys}'

    def save(self, path):
        """保存映射到 JSON 文件。

        Args:
            path: 文件路径（None 时无操作）。
        """
        if path is not None:
            json_ex.write(path, self.__keys)

    def load(self, path):
        """从 JSON 文件加载映射。

        Args:
            path: 文件路径（None 时无操作；数据非 dict 时忽略）。
        """
        if path is not None:
            data = json_ex.read(path)
            if isinstance(data, dict):
                self.__keys = data

    def __getattr__(self, name):
        """通过属性访问注册并返回 ID（不存在时自动创建）。

        Args:
            name: 键名。

        Returns:
            int: 属性 ID。
        """
        return self.reg_key(name)

    def __getitem__(self, name):
        """通过字典式访问注册并返回 ID（不存在时自动创建）。

        Args:
            name: 键名。

        Returns:
            int: 属性 ID。
        """
        return self.reg_key(name)

    def values(self):
        """返回所有已注册的值。

        Returns:
            ValuesView[int]: 所有属性 ID。
        """
        return self.__keys.values()

    def add_keys(self, *args):
        """批量添加属性 ID（已存在则跳过）。

        从 0 开始寻找第一个未使用的 ID 分配给新键。

        Args:
            *args: 键名列表（str）。
        """
        for key in args:
            if isinstance(key, str):
                if key not in self.__keys:
                    values = self.values()
                    for val in range(len(self.__keys) + 1):
                        if val not in values:
                            self.__keys[key] = val
                            break

    def get_key(self, name):
        """返回属性 ID（不添加，找不到则返回 None）。

        Args:
            name: 键名。

        Returns:
            int | None: 属性 ID，不存在时为 None。
        """
        return self.__keys.get(name)

    def add_key(self, name):
        """添加单个属性 ID。

        Args:
            name: 键名。
        """
        self.add_keys(name)

    def reg_key(self, name):
        """注册并返回 ID（不存在则自动创建）。

        Args:
            name: 键名。

        Returns:
            int: 属性 ID。
        """
        value = self.get_key(name)
        if value is None:
            self.add_key(name)
            return self.get_key(name)
        else:
            return value


def test():
    key = AttrKeys()
    print(key.reg_key('x'))
    print(key.reg_key('y'))
    print(key.x)
    print(key.y)
    print(key.z)
    print(key)


if __name__ == '__main__':
    test()
