def add_keys(*args):
    """
    在字典中注册键值。将从0开始尝试，直到发现不存在的数值再使用. 返回添加了key之后的字典对象.
    示例:
        from zml import add_keys
        keys = add_keys('x', 'y')
        print(keys)
        add_keys(keys, 'a', 'b', 'c')
        print(keys)
    输出:
        {'x': 0, 'y': 1}
        {'x': 0, 'y': 1, 'a': 2, 'b': 3, 'c': 4}
    """

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

    def __init__(self, *args):
        self.__keys = {}
        self.add_keys(*args)

    def __str__(self):
        return f'{self.__keys}'

    def __getattr__(self, item):
        return self.__keys[item]

    def __getitem__(self, item):
        return self.__keys[item]

    def values(self):
        return self.__keys.values()

    def add_keys(self, *args):
        for key in args:
            if isinstance(key, str):
                if key not in self.__keys:
                    values = self.values()
                    for val in range(len(self.__keys) + 1):
                        if val not in values:
                            self.__keys[key] = val
                            break
