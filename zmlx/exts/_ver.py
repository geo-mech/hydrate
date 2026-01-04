from zmlx.exts._dll import version


class _DataVersion:
    """管理数据版本号的内部工具类。

    版本号为6位整数，格式为yymmdd(年年月月日日)，例如230701表示2023年7月1日。

    Attributes:
        __default (int): 默认版本号（受保护的属性）
        __versions (dict): 各键值对应的版本号字典（受保护的属性）
    """

    def __init__(self, value=version):
        """初始化数据版本管理器。

        Args:
            value (int, optional): 默认版本号，必须为6位整数。默认使用全局version值

        Raises:
            AssertionError: 当value不是整数或不在[100000, 999999]范围内时抛出
        """
        assert isinstance(value, int)
        assert 100000 <= value <= 999999
        self.__versions = {}
        self.__default = value

    def set(self, value=None, key=None):
        """设置指定键或默认的版本号。

        Args:
            value (int): 必须为6位整数，表示年月日(yymmdd)
            key (Hashable, optional):
                当提供键值时，设置该键对应的版本；
                当为None时，设置默认版本

        Raises:
            AssertionError: 当value不符合6位整数要求时抛出
        """
        assert isinstance(value, int)
        assert 100000 <= value <= 999999
        if key is None:
            self.__default = value
        else:
            self.__versions[key] = value

    def __getattr__(self, key):
        """通过属性访问获取版本号。

        Args:
            key (str): 版本键值名称

        Returns:
            int: 指定键对应的版本号，若不存在则返回默认版本号
        """
        return self.__versions.get(key, self.__default)

    def __getitem__(self, key):
        """通过字典方式访问获取版本号。

        Args:
            key (Hashable): 版本键值名称

        Returns:
            int: 指定键对应的版本号，若不存在则返回默认版本号
        """
        return self.__versions.get(key, self.__default)

    def __setitem__(self, key, value):
        """通过字典方式设置版本号。

        Args:
            key (Hashable): 版本键值名称
            value (int): 必须为6位整数，表示年月日(yymmdd)

        Raises:
            AssertionError: 通过set方法间接抛出参数校验异常
        """
        self.set(key=key, value=value)


data_version = _DataVersion()
