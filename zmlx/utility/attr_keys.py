import zmlx.alg.sys as warnings

from zmlx.io import json_ex


def add_keys(*args):
    """
    在字典中注册键值。将从0开始尝试，直到发现不存在的数值再使用. 返回添加了key之后的字典对象.
    示例:
        from zmlx.base.zml import add_keys
        keys = add_keys('x', 'y')
        print(keys)
        add_keys(keys, 'a', 'b', 'c')
        print(keys)
    输出:
        {'x': 0, 'y': 1}
        {'x': 0, 'y': 1, 'a': 2, 'b': 3, 'c': 4}
    """
    warnings.warn('The function zmlx.utility.AttrKeys.add_keys is deprecated '
                  '(will be removed after 2026-3-22), '
                  'please use zmlx.utility.AttrKeys instead.',
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
    """
    用以管理属性. 自动从0开始编号.
    """

    def __init__(self, *args, path=None):
        """
        初始化，并且添加必要的键值 (或者从文件读取)
        """
        self.__keys = {}
        if path is not None:
            assert len(args) == 0
            self.load(path)
        else:
            self.add_keys(*args)

    def __str__(self):
        """
        转化为字符串
        """
        return f'{self.__keys}'

    def save(self, path):
        """
        保存文件
        """
        if path is not None:
            json_ex.write(path, self.__keys)

    def load(self, path):
        """
        导入文件
        """
        if path is not None:
            data = json_ex.read(path)
            if isinstance(data, dict):
                self.__keys = data

    def __getattr__(self, name):
        """
        注册并返回id
        """
        return self.reg_key(name)

    def __getitem__(self, name):
        """
        注册并返回id
        """
        return self.reg_key(name)

    def values(self):
        """
        返回所有的值
        """
        return self.__keys.values()

    def add_keys(self, *args):
        """
        添加多个属性id
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
        """
        返回属性id [不添加，如果找不到，则返回None]
        """
        return self.__keys.get(name)

    def add_key(self, name):
        """
        添加属性ID
        """
        self.add_keys(name)

    def reg_key(self, name):
        """
        注册并返回. 如果不存在，则创建.
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
