"""版本信息.

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-29: 默认版本号改读 ``core.version``（模块级 ``version`` 已弃用）
"""
from zmlx.exts._dll import core

#: 取不到内核版本（没有 DLL）时内建的数据版本。
#:
#: ⚠️ 这就是原先 ``_dll`` 里 ``version`` 的兜底值 ``110101``，只是**不再**冒充
#: 「内核版本」：它只作为 :class:`_DataVersion` 的默认值，用来决定流体数据的
#: 「解析到哪个版本的格式」，与「本机装的是哪一版内核」无关。
FALLBACK_VERSION = 110101


class _DataVersion:
    """管理数据版本号的内部工具类。

    版本号为6位整数，格式为yymmdd(年年月月日日)，例如230701表示2023年7月1日。

    Attributes:
        __default (int): 默认版本号（受保护的属性）
        __versions (dict): 各键值对应的版本号字典（受保护的属性）
    """

    def __init__(self, value=None):
        """初始化数据版本管理器。

        Args:
            value (int, optional): 默认版本号，必须为6位整数。默认使用内核版本
                ``core.version``；取不到（没有 DLL）时退回 :data:`FALLBACK_VERSION`。
        """
        if value is None:
            # ⚠️ ``core.version`` 在内核没加载成时是 ``None``（旧 DLL 的导出是空函数，
            #    返回 ``None`` 而不是整数），那时不能拿它当默认值 —— 下面的范围校验
            #    会直接炸掉整个 ``zmlx.exts`` 的导入。
            value = getattr(core, 'version', None)
            if not isinstance(value, int):
                value = FALLBACK_VERSION
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
