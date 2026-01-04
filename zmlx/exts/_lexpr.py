from ctypes import c_void_p, c_char_p, c_double, c_size_t
from typing import Optional, Tuple, Union, List

from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._fmap import FileMap
from zmlx.exts._utils import HasHandle, get_index, make_parent, check_ipath


class LinearExpr(HasHandle):
    core.use(c_void_p, 'new_lexpr')
    core.use(None, 'del_lexpr', c_void_p)

    def __init__(self, handle: Optional[c_void_p] = None):
        super().__init__(handle, core.new_lexpr, core.del_lexpr)

    core.use(None, 'lexpr_save', c_void_p, c_char_p)

    def save(self, path: str):
        """
        将线性表达式序列化到指定路径。

        Args:
            path (str): 文件保存路径，扩展名决定格式：
                - .txt: 跨平台文本格式（不可读）
                - .xml: 可读性XML格式（体积大）
                - 其他: 高效二进制格式（平台相关）

        Note:
            自动创建父目录，会覆盖已存在的文件
        """
        if isinstance(path, str):
            make_parent(path)
            core.lexpr_save(self.handle, make_c_char_p(path))

    core.use(None, 'lexpr_load', c_void_p, c_char_p)

    def load(self, path: str):
        """
        从文件加载线性表达式数据。

        Args:
            path (str): 文件路径，格式由扩展名决定

        Raises:
            FileNotFoundError: 当文件不存在时抛出
            ValueError: 当文件格式不匹配时抛出
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.lexpr_load(self.handle, make_c_char_p(path))

    core.use(None, 'lexpr_write_fmap',
             c_void_p, c_void_p, c_char_p)
    core.use(None, 'lexpr_read_fmap',
             c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt: str = 'binary') -> FileMap:
        """
        将表达式序列化到文件映射对象。

        Args:
            fmt (str): 序列化格式，可选 'text', 'xml', 'binary'

        Returns:
            FileMap: 包含序列化数据的文件映射对象
        """
        fmap = FileMap()
        core.lexpr_write_fmap(self.handle, fmap.handle,
                              make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt: str = 'binary'):
        """
        从文件映射对象加载表达式。

        Args:
            fmap (FileMap): 包含序列化数据的文件映射
            fmt (str): 数据格式，需与写入时一致

        Raises:
            TypeError: 当fmap参数类型错误时抛出
        """
        assert isinstance(fmap, FileMap)
        core.lexpr_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self) -> FileMap:
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: FileMap):
        self.from_fmap(value, fmt='binary')

    def __eq__(self, rhs: 'LinearExpr'):
        """判断两个线性表达式是否指向同一内存对象"""
        return self.handle == rhs.handle

    def __ne__(self, rhs: 'LinearExpr'):
        """判断两个线性表达式是否不同对象"""
        return not (self == rhs)

    def __str__(self) -> str:
        """
        获取线性表达式的字符串表示。

        Returns:
            str: 格式如'zml.LinearExpr(c + 1.2*x(3) + 0.5*x(5))'
        """
        if self.length > 0:
            s = ' + '.join(
                [f'{self[i][1]}*x({self[i][0]})' for i in range(len(self))])
            s = s.replace('+ -', '- ')
            return f'{type(self).__name__}({self.c} + {s})'
        else:
            return f'{type(self).__name__}({self.c})'

    core.use(c_double, 'lexpr_get_c', c_void_p)
    core.use(None, 'lexpr_set_c', c_void_p, c_double)

    @property
    def c(self) -> float:
        """
        线性表达式的常数项。

        Returns:
            float: 表达式中的常数偏移量
        """
        return core.lexpr_get_c(self.handle)

    @c.setter
    def c(self, value: float):
        """
        设置线性表达式的常数项。

        Args:
            value (float): 新的常数项值
        """
        core.lexpr_set_c(self.handle, value)

    def set_c(self, value: float):
        """
        设置常数项并返回当前实例以便链式调用。

        Args:
            value (float): 新的常数项值

        Returns:
            LinearExpr: self实例
        """
        self.c = value
        return self

    core.use(c_size_t, 'lexpr_get_length', c_void_p)

    @property
    def length(self) -> int:
        """
        获取线性项的数量（不包括常数项）。

        Returns:
            int: 当前表达式中的线性项数量
        """
        return core.lexpr_get_length(self.handle)

    def __len__(self) -> int:
        """
        获取线性项的数量（与length属性一致）。

        Returns:
            int: 当前表达式中的线性项数量
        """
        return self.length

    core.use(c_size_t, 'lexpr_get_index', c_void_p, c_size_t)
    core.use(c_double, 'lexpr_get_weight', c_void_p, c_size_t)

    def __getitem__(self, i: int) -> Optional[Tuple[int, float]]:
        """
        通过索引获取线性项信息。

        Args:
            i (int): 项索引（0 <= i < length）

        Returns:
            tuple: (变量索引, 系数) 的元组，格式为(int, float)
        """
        idx = get_index(i, self.length)
        if idx is not None:
            index = core.lexpr_get_index(self.handle, idx)
            weight = core.lexpr_get_weight(self.handle, idx)
            return index, weight
        else:
            return None

    core.use(None, 'lexpr_add', c_void_p, c_size_t, c_double)

    def add(self, index: int, weight: float) -> "LinearExpr":
        """
        添加线性项到表达式。

        Args:
            index (int): 变量索引
            weight (float): 变量系数

        Returns:
            LinearExpr: self实例便于链式调用
        """
        core.lexpr_add(self.handle, index, weight)
        return self

    core.use(None, 'lexpr_clear', c_void_p)

    def clear(self):
        """
        重置表达式为初始状态。

        Note:
            - 清除所有线性项
            - 将常数项置零
        """
        core.lexpr_clear(self.handle)
        return self

    core.use(None, 'lexpr_merge', c_void_p)

    def merge(self):
        """
        合并同类项并简化表达式。

        Note:
            - 合并相同变量索引的系数
            - 删除系数绝对值小于1e-15的项
            - 操作会改变表达式内部存储结构
        """
        core.lexpr_merge(self.handle)

    core.use(None, 'lexpr_plus', c_void_p, c_size_t, c_size_t)
    core.use(None, 'lexpr_multiply', c_void_p, c_size_t, c_double)

    def __add__(self, other: "LinearExpr") -> "LinearExpr":
        """
        实现线性表达式加法运算。

        Args:
            other (LinearExpr): 另一个线性表达式

        Returns:
            LinearExpr: 新的表达式对象，包含两个表达式之和
        """
        assert isinstance(other, LinearExpr)
        result = LinearExpr()
        core.lexpr_plus(result.handle, self.handle, other.handle)
        return result

    def __sub__(self, other: "LinearExpr") -> "LinearExpr":
        """
        实现线性表达式减法运算。

        Args:
            other (LinearExpr): 另一个线性表达式

        Returns:
            LinearExpr: 新的表达式对象，包含两个表达式之差
        """
        return self.__add__(other * (-1.0))

    def __mul__(self, scale: float) -> "LinearExpr":
        """
        实现表达式与标量的乘法运算。

        Args:
            scale (float): 缩放系数

        Returns:
            LinearExpr: 新的缩放后的表达式对象
        """
        result = LinearExpr()
        core.lexpr_multiply(result.handle, self.handle, scale)
        return result

    def __truediv__(self, scale: float) -> "LinearExpr":
        """
        实现表达式与标量的除法运算。

        Args:
            scale (float): 除数（不能为0）

        Returns:
            LinearExpr: 新的缩放后的表达式对象
        """
        return self.__mul__(1.0 / scale)

    @staticmethod
    def create(index: int) -> "LinearExpr":
        """
        创建基本变量表达式。

        Args:
            index (int): 变量索引

        Returns:
            LinearExpr: 形式为1.0*x(index)的表达式
        """
        lexpr = LinearExpr()
        lexpr.c = 0
        lexpr.add(index, 1.0)
        return lexpr

    @staticmethod
    def create_constant(c: float) -> "LinearExpr":
        """
        创建常数表达式。

        Args:
            c (float): 常数值

        Returns:
            LinearExpr: 仅包含常数项的表达式
        """
        lexpr = LinearExpr()
        lexpr.c = c
        return lexpr

    core.use(None, 'lexpr_clone', c_void_p, c_void_p)

    def clone(self, other: "LinearExpr") -> "LinearExpr":
        """
        深度克隆另一个表达式数据。

        Args:
            other (LinearExpr): 源表达式对象

        Returns:
            LinearExpr: self实例便于链式调用

        Note:
            完全复制源表达式的所有项和常数项
        """
        if isinstance(other, LinearExpr):
            core.lexpr_clone(self.handle, other.handle)
        return self


def create_lexpr(*args: Union[List, Tuple[int, float], float]) -> LinearExpr:
    """
    生成一个线性表达式
    Args:
        *args: 当为list或者tuple的时候，是index和weight，否则视为常数项

    Returns:
        LinearExpr: 生成的线性表达式
    """
    result = LinearExpr()
    for item in args:
        if isinstance(item, (list, tuple)):  # 仅支持list和tuple
            index, weight = item
            result.add(index, weight)
        else:  # 此时应该为浮点数
            result.c += item
    if len(args) > 1:  # 可能需要合并同类项
        result.merge()
    return result
