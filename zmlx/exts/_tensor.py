from ctypes import c_double, c_void_p, c_char_p, c_size_t
from typing import Tuple, Optional

from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._fmap import FileMap
from zmlx.exts._utils import HasHandle, get_index, make_parent, check_ipath


class Tensor2(HasHandle):
    """二维二阶张量类，用于表示二维空间中的应力、应变等张量数据。

    支持张量分量存取、特征值计算、旋转变换及序列化操作。
    """
    core.use(c_void_p, 'new_tensor2')
    core.use(None, 'del_tensor2', c_void_p)

    def __init__(self, xx=None, yy=None, xy=None, path=None, handle=None):
        """初始化二维张量对象。

        Args:
            xx (float, optional): xx分量的初始值。
            yy (float, optional): yy分量的初始值。
            xy (float, optional): xy分量的初始值。
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super().__init__(handle, core.new_tensor2, core.del_tensor2)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if xx is not None:
                self.xx = xx
            if yy is not None:
                self.yy = yy
            if xy is not None:
                self.xy = xy
        else:
            assert xx is None and yy is None and xy is None and path is None

    core.use(None, 'tensor2_save', c_void_p, c_char_p)

    def save(self, path: str):
        """序列化保存张量数据。

        支持以下文件格式：
            - `.txt`(扩展名部分包含txt关键词即可)：跨平台，基本不可读。
            - `.xml`(扩展名部分包含xml关键词即可)：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.tensor2_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor2_load', c_void_p, c_char_p)

    def load(self, path: str):
        """从文件加载序列化数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.tensor2_load(self.handle, make_c_char_p(path))

    core.use(None, 'tensor2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'tensor2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt: str = 'binary') -> FileMap:
        """将张量数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
                默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.tensor2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt: str = 'binary'):
        """从 FileMap 中读取序列化数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
                默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.tensor2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self) -> FileMap:
        """获取二进制序列化表示。

        Returns:
            FileMap: 包含二进制数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: FileMap):
        """从二进制数据加载张量。

        Args:
            value (FileMap): 包含二进制数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    def __repr__(self) -> str:
        return f'{type(self).__name__}(handle={int(self.handle)}, xx={self.xx}, yy={self.yy}, xy={self.xy})'

    def __str__(self) -> str:
        """返回张量的字符串表示。

        Returns:
            str: 格式为 zml.Tensor2(xx, yy, xy) 的字符串。
        """
        return f'{type(self).__name__}({self.xx}, {self.yy}, {self.xy})'

    core.use(c_double, 'tensor2_get', c_void_p, c_size_t, c_size_t)

    def __getitem__(self, key: Tuple[int, int]) -> Optional[float]:
        """通过二维索引访问张量分量。

        Args:
            key (tuple[int, int]): 二维索引元组，如 (0,0) 表示 xx 分量。

        Returns:
            float: 对应分量的值。

        Raises:
            AssertionError: 如果索引长度不为2。
        """
        assert len(key) == 2
        i = get_index(key[0], 2)
        j = get_index(key[1], 2)
        if i is not None and j is not None:
            return core.tensor2_get(self.handle, i, j)
        else:
            return None

    core.use(None, 'tensor2_set', c_void_p, c_size_t, c_size_t, c_double)

    def __setitem__(self, key: Tuple[int, int], value: float):
        """通过二维索引设置张量分量。

        Args:
            key (tuple[int, int]): 二维索引元组，如 (0,0) 表示 xx 分量。
            value (float): 要设置的值。

        Raises:
            AssertionError: 如果索引长度不为2。
        """
        assert len(key) == 2
        i = get_index(key[0], 2)
        j = get_index(key[1], 2)
        if i is not None and j is not None:
            core.tensor2_set(self.handle, i, j, value)

    core.use(None, 'tensor2_set_max_min_angle', c_void_p, c_double, c_double, c_double)

    def set_max_min_angle(self, max_value=None, min_value=None, angle=None):
        """通过主值和方向角设置张量。

        Args:
            max_value (float): 最大主应力/应变值。
            min_value (float): 最小主应力/应变值。
            angle (float): 最大主值方向与x轴正方向的夹角（弧度，逆时针方向为正）。
        """
        if max_value is not None and min_value is not None and angle is not None:
            core.tensor2_set_max_min_angle(self.handle, max_value, min_value, angle)

    @property
    def xx(self) -> float:
        """获取或设置xx分量。"""
        res = self[(0, 0)]
        assert res is not None, "Tensor2.xx: res is None"
        return res

    @xx.setter
    def xx(self, value: float):
        self[0, 0] = value

    @property
    def yy(self) -> float:
        """获取或设置yy分量。"""
        res = self[(1, 1)]
        assert res is not None, "Tensor2.yy: res is None"
        return res

    @yy.setter
    def yy(self, value: float):
        self[(1, 1)] = value

    @property
    def xy(self) -> float:
        """获取或设置xy分量。"""
        res = self[(0, 1)]
        assert res is not None, "Tensor2.xy: res is None"
        return res

    @xy.setter
    def xy(self, value: float):
        self[(0, 1)] = value

    @staticmethod
    def create(max, min, angle):
        """通过主值创建二维张量。

        Args:
            max (float): 最大主值。
            min (float): 最小主值。
            angle (float): 最大主值方向角（弧度）。

        Returns:
            Tensor2: 新创建的张量实例。
        """
        tensor = Tensor2()
        tensor.set_max_min_angle(max, min, angle)
        return tensor

    def __add__(self, other):
        """张量加法运算。

        Args:
            other (Tensor2): 另一个张量。

        Returns:
            Tensor2: 新的张量实例，包含各分量之和。
        """
        xx = self.xx + other.xx
        yy = self.yy + other.yy
        xy = self.xy + other.xy
        return Tensor2(xx=xx, yy=yy, xy=xy)

    def __sub__(self, other):
        """张量减法运算。

        Args:
            other (Tensor2): 另一个张量。

        Returns:
            Tensor2: 新的张量实例，包含各分量之差。
        """
        xx = self.xx - other.xx
        yy = self.yy - other.yy
        xy = self.xy - other.xy
        return Tensor2(xx=xx, yy=yy, xy=xy)

    def __mul__(self, value):
        """标量乘法运算。

        Args:
            value (float): 标量乘数。

        Returns:
            Tensor2: 新的张量实例，各分量乘以标量值。
        """
        xx = self.xx * value
        yy = self.yy * value
        xy = self.xy * value
        return Tensor2(xx=xx, yy=yy, xy=xy)

    def __truediv__(self, value):
        """标量除法运算。

        Args:
            value (float): 标量除数。

        Returns:
            Tensor2: 新的张量实例，各分量除以标量值。
        """
        xx = self.xx / value
        yy = self.yy / value
        xy = self.xy / value
        return Tensor2(xx=xx, yy=yy, xy=xy)

    core.use(None, 'tensor2_clone', c_void_p, c_void_p)

    def clone(self, other):
        """克隆另一个张量的数据。

        Args:
            other (Tensor2): 要克隆的张量对象。

        Returns:
            Tensor2: 当前对象（支持链式调用）。
        """
        if other is not None:
            assert isinstance(other, Tensor2)
            core.tensor2_clone(self.handle, other.handle)
        return self

    core.use(None, 'tensor2_rotate', c_void_p, c_void_p, c_double)

    def get_rotate(self, angle, buffer=None):
        """获取旋转后的张量。

        Args:
            angle (float): 旋转角度（弧度，逆时针方向为正）。
            buffer (Tensor2, optional): 用于存储结果的缓冲区。

        Returns:
            Tensor2: 旋转后的张量实例。
        """
        if not isinstance(buffer, Tensor2):
            buffer = Tensor2()
        core.tensor2_rotate(self.handle, buffer.handle, angle)
        return buffer

    core.use(c_double, 'tensor2_get_max_principle_value', c_void_p)

    @property
    def max_principle_value(self):
        """获取最大主值。

        Returns:
            float: 最大主应力/应变值。
        """
        return core.tensor2_get_max_principle_value(self.handle)

    core.use(c_double, 'tensor2_get_min_principle_value', c_void_p)

    @property
    def min_principle_value(self):
        """获取最小主值。

        Returns:
            float: 最小主应力/应变值。
        """
        return core.tensor2_get_min_principle_value(self.handle)

    core.use(c_double, 'tensor2_get_principle_angle', c_void_p)

    @property
    def principle_angle(self):
        """获取主值方向角。

        Returns:
            float: 最大主值方向与x轴的夹角（弧度）。
        """
        return core.tensor2_get_principle_angle(self.handle)


class Tensor3(HasHandle):
    """三维二阶张量类，用于表示三维空间中的应力、应变等张量数据。

    支持张量分量存取、方向投影计算及序列化操作。
    """
    core.use(c_void_p, 'new_tensor3')
    core.use(None, 'del_tensor3', c_void_p)

    def __init__(self, xx=None, yy=None, zz=None,
                 xy=None, yz=None, zx=None,
                 path=None, handle=None):
        """初始化三维张量对象。

        Args:
            xx (float, optional): xx分量的初始值。
            yy (float, optional): yy分量的初始值。
            zz (float, optional): zz分量的初始值。
            xy (float, optional): xy分量的初始值。
            yz (float, optional): yz分量的初始值。
            zx (float, optional): zx分量的初始值。
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super().__init__(handle, core.new_tensor3, core.del_tensor3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if xx is not None:
                self.xx = xx
            if yy is not None:
                self.yy = yy
            if zz is not None:
                self.zz = zz
            if xy is not None:
                self.xy = xy
            if yz is not None:
                self.yz = yz
            if zx is not None:
                self.zx = zx
        else:
            assert xx is None and yy is None and zz is None and xy is None and yz is None and zx is None

    core.use(None, 'tensor3_save', c_void_p, c_char_p)

    def save(self, path):
        """序列化保存张量数据。

        支持以下文件格式：
            - `.txt`(扩展名部分包含txt关键词即可)：跨平台，基本不可读。
            - `.xml`(扩展名部分包含xml关键词即可)：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.tensor3_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor3_load',
             c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.tensor3_load(self.handle, make_c_char_p(path))

    core.use(None, 'tensor3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'tensor3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """将张量数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
                默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.tensor3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt='binary'):
        """从 FileMap 中读取序列化数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。
                默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.tensor3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """获取二进制序列化表示。

        Returns:
            FileMap: 包含二进制数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """从二进制数据加载张量。

        Args:
            value (FileMap): 包含二进制数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    def __repr__(self):
        return (f'{type(self).__name__}(handle={int(self.handle)}, '
                f'xx={self.xx}, yy={self.yy}, zz={self.zz}, '
                f'xy={self.xy}, yz={self.yz}, zx={self.zx})')

    def __str__(self):
        """返回张量的字符串表示。

        Returns:
            str: 格式为 zml.Tensor3(xx, yy, zz, xy, yz, zx) 的字符串。
        """
        return (f'{type(self).__name__}({self.xx}, {self.yy}, {self.zz}, '
                f'{self.xy}, {self.yz}, {self.zx})')

    core.use(c_double, 'tensor3_get',
             c_void_p, c_size_t, c_size_t)

    def __getitem__(self, key) -> Optional[float]:
        """通过二维索引访问张量分量。

        Args:
            key (tuple): 二维索引元组，如 (0,0) 表示 xx 分量。

        Returns:
            float: 对应分量的值。

        Raises:
            AssertionError: 如果索引长度不为2。
        """
        assert len(key) == 2
        i = get_index(key[0], 3)
        j = get_index(key[1], 3)
        if i is not None and j is not None:
            return core.tensor3_get(self.handle, i, j)
        else:
            return None

    core.use(None, 'tensor3_set', c_void_p, c_size_t, c_size_t, c_double)

    def __setitem__(self, key, value):
        """通过二维索引设置张量分量。

        Args:
            key (tuple): 二维索引元组，如 (0,0) 表示 xx 分量。
            value (float): 要设置的值。

        Raises:
            AssertionError: 如果索引长度不为2。
        """
        assert len(key) == 2
        i = get_index(key[0], 3)
        j = get_index(key[1], 3)
        if i is not None and j is not None:
            core.tensor3_set(self.handle, i, j, value)

    @property
    def xx(self) -> float:
        """获取或设置xx分量。

        Returns:
            float: xx分量的值。
        """
        res = self[(0, 0)]
        assert res is not None, "Tensor3.xx is None"
        return res

    @xx.setter
    def xx(self, value):
        """设置xx分量。

        Args:
            value (float): 要设置的xx分量值。
        """
        self[0, 0] = value

    @property
    def yy(self) -> float:
        """获取或设置yy分量。

        Returns:
            float: yy分量的值。
        """
        res = self[(1, 1)]
        assert res is not None, "Tensor3.yy is None"
        return res

    @yy.setter
    def yy(self, value):
        """设置yy分量。

        Args:
            value (float): 要设置的yy分量值。
        """
        self[(1, 1)] = value

    @property
    def zz(self) -> float:
        """获取或设置zz分量。

        Returns:
            float: zz分量的值。
        """
        res = self[(2, 2)]
        assert res is not None, "Tensor3.zz is None"
        return res

    @zz.setter
    def zz(self, value):
        """设置zz分量。

        Args:
            value (float): 要设置的zz分量值。
        """
        self[(2, 2)] = value

    @property
    def xy(self) -> float:
        """获取或设置xy分量。

        Returns:
            float: xy分量的值。
        """
        res = self[(0, 1)]
        assert res is not None, "Tensor3.xy is None"
        return res

    @xy.setter
    def xy(self, value):
        """设置xy分量。

        Args:
            value (float): 要设置的xy分量值。
        """
        self[(0, 1)] = value

    @property
    def yz(self) -> float:
        """获取或设置yz分量。

        Returns:
            float: yz分量的值。
        """
        res = self[(1, 2)]
        assert res is not None, "Tensor3.yz is None"
        return res

    @yz.setter
    def yz(self, value):
        """设置yz分量。

        Args:
            value (float): 要设置的yz分量值。
        """
        self[(1, 2)] = value

    @property
    def zx(self) -> float:
        """获取或设置zx分量。

        Returns:
            float: zx分量的值。
        """
        res = self[(2, 0)]
        assert res is not None, "Tensor3.zx is None"
        return res

    @zx.setter
    def zx(self, value):
        """设置zx分量。

        Args:
            value (float): 要设置的zx分量值。
        """
        self[(2, 0)] = value

    def __add__(self, other):
        """执行张量逐分量加法运算。

        Args:
            other (Tensor3): 另一个三维张量对象。

        Returns:
            Tensor3: 新的张量实例，包含各分量之和。

        Raises:
            TypeError: 如果other不是Tensor3类型。
        """
        return Tensor3(xx=self.xx + other.xx,
                       yy=self.yy + other.yy,
                       zz=self.zz + other.zz,
                       xy=self.xy + other.xy,
                       yz=self.yz + other.yz,
                       zx=self.zx + other.zx,
                       )

    def __sub__(self, other):
        """执行张量逐分量减法运算。

        Args:
            other (Tensor3): 另一个三维张量对象。

        Returns:
            Tensor3: 新的张量实例，包含各分量之差。

        Raises:
            TypeError: 如果other不是Tensor3类型。
        """
        return Tensor3(xx=self.xx - other.xx,
                       yy=self.yy - other.yy,
                       zz=self.zz - other.zz,
                       xy=self.xy - other.xy,
                       yz=self.yz - other.yz,
                       zx=self.zx - other.zx,
                       )

    def __mul__(self, value):
        """执行标量乘法运算。

        Args:
            value (float): 标量乘数。

        Returns:
            Tensor3: 新的张量实例，各分量乘以标量值。

        Raises:
            TypeError: 如果value不是数值类型。
        """
        return Tensor3(xx=self.xx * value,
                       yy=self.yy * value,
                       zz=self.zz * value,
                       xy=self.xy * value,
                       yz=self.yz * value,
                       zx=self.zx * value,
                       )

    def __truediv__(self, value):
        """执行标量除法运算。

        Args:
            value (float): 标量除数，不能为0。

        Returns:
            Tensor3: 新的张量实例，各分量除以标量值。

        Raises:
            ZeroDivisionError: 如果value为0。
            TypeError: 如果value不是数值类型。
        """
        return Tensor3(xx=self.xx / value,
                       yy=self.yy / value,
                       zz=self.zz / value,
                       xy=self.xy / value,
                       yz=self.yz / value,
                       zx=self.zx / value,
                       )

    core.use(c_double, 'tensor3_get_along', c_void_p, c_double, c_double, c_double)

    def get_along(self, *args):
        """计算给定方向上的投影值。

        支持两种参数形式：
        1. 三个独立坐标分量 (x, y, z)
        2. 包含三个元素的向量 (vector, )

        Args:
            *args: 可以是三个float参数，或单个向量参数

        Returns:
            float: 该方向上的投影值
        """
        if len(args) == 3:
            return core.tensor3_get_along(self.handle, *args)
        else:
            assert len(args) == 1
            x = args[0]
            return core.tensor3_get_along(self.handle, x[0], x[1], x[2])

    core.use(None, 'tensor3_clone', c_void_p, c_void_p)

    def clone(self, other):
        """克隆另一个张量的数据到当前对象。

        Args:
            other (Tensor3): 要克隆的源张量对象

        Returns:
            Tensor3: 当前对象实例，支持链式调用
        """
        if other is not None:
            assert isinstance(other, Tensor3)
            core.tensor3_clone(self.handle, other.handle)
        return self
