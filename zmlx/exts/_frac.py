import warnings
from ctypes import c_double, c_void_p, c_size_t, c_bool, c_char_p
from typing import Optional, Iterable, Tuple, List, Union

from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._fmap import FileMap
from zmlx.exts._lexpr import LinearExpr
from zmlx.exts._seepage import Seepage
from zmlx.exts._tensor import Tensor2
from zmlx.exts._utils import (
    HasHandle, Iterator, Object, get_distance, get_index, IDX_INF, is_array, log, make_parent, check_ipath
)
from zmlx.exts._vec import Vector


class Dfn2(HasHandle):
    """
    用于生成二维的离散裂缝网络
    """
    core.use(c_void_p, 'new_dfn2d')
    core.use(None, 'del_dfn2d', c_void_p)

    def __init__(self, path=None, handle=None):
        """
        初始化Dfn2对象

        Args:
            path (str, optional): 序列化文件的路径。如果提供，将加载该文件。默认为None。
            handle: 句柄对象。默认为None。
        """
        super().__init__(handle, core.new_dfn2d, core.del_dfn2d)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'dfn2d_save',
             c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存。可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.dfn2d_save(self.handle, make_c_char_p(path))

    core.use(None, 'dfn2d_load',
             c_void_p, c_char_p)

    def load(self, path):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 要读取的文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.dfn2d_load(self.handle, make_c_char_p(path))

    core.use(None, 'dfn2d_set_range',
             c_void_p, c_double, c_double, c_double,
             c_double)
    core.use(c_double, 'dfn2d_get_range',
             c_void_p, c_size_t)

    @property
    def range(self):
        """
        位置的范围(一个矩形区域)

        Returns:
            list: 包含四个浮点数的列表，表示矩形区域的范围 [xmin, ymin, xmax, ymax]。
        """
        return [core.dfn2d_get_range(self.handle, i) for i in range(4)]

    @range.setter
    def range(self, value):
        """
        设置位置的范围(一个矩形区域)

        Args:
            value (list): 包含四个浮点数的列表，
                表示矩形区域的范围 [xmin, ymin, xmax, ymax]。

        Raises:
            AssertionError: 如果输入的列表长度不为4。
        """
        assert len(
            value) == 4, f'The format of pos range is [xmin, ymin, xmax, ymax]'
        core.dfn2d_set_range(self.handle, *value)

    core.use(c_bool, 'dfn2d_add_frac',
             c_void_p, c_double, c_double, c_double,
             c_double, c_double)
    core.use(None, 'dfn2d_randomly_add_frac',
             c_void_p, c_void_p, c_void_p,
             c_double, c_double)

    def add_frac(self, x0=None, y0=None, x1=None, y1=None, angles=None,
                 lengths=None, p21=None, l_min=None):
        """
        添加一个裂缝或者随机添加多条裂缝。
            当给定x0, y0, x1, y1的时候，添加这一条裂缝;
            否则，则需要给定angle(一个list，用以定义角度),
             length(list: 用以定义角度), p21(新添加的裂缝的密度)来随机添加一组裂缝。

        Args:
            x0 (float, optional): 裂缝起点的x坐标。默认为None。
            y0 (float, optional): 裂缝起点的y坐标。默认为None。
            x1 (float, optional): 裂缝终点的x坐标。默认为None。
            y1 (float, optional): 裂缝终点的y坐标。默认为None。
            angles (list or Vector, optional): 角度列表，
                用于随机添加裂缝。默认为None。
            lengths (list or Vector, optional): 长度列表，
                用于随机添加裂缝。默认为None。
            p21 (float, optional): 新添加的裂缝的密度。默认为None。
            l_min (float, optional): 最小长度。默认为-1.0。

        Raises:
            AssertionError: 如果未提供x0, y0, x1, y1且angles、lengths或p21为None。
        """
        if l_min is None:
            l_min = -1.0
        if (x0 is not None and y0 is not None and x1 is not None
                and y1 is not None):
            return core.dfn2d_add_frac(
                self.handle, x0, y0, x1, y1, l_min)
        else:
            assert (angles is not None and lengths is not None
                    and p21 is not None)
            if not isinstance(angles, Vector):
                angles = Vector(value=angles)
            if not isinstance(lengths, Vector):
                lengths = Vector(value=lengths)
            core.dfn2d_randomly_add_frac(
                self.handle, angles.handle, lengths.handle, p21, l_min)
            return None

    core.use(c_size_t, 'dfn2d_get_fracture_number',
             c_void_p)

    @property
    def fracture_n(self):
        """
        目前体系中已经存在的裂缝的数量

        Returns:
            int: 裂缝的数量。
        """
        return core.dfn2d_get_fracture_number(self.handle)

    core.use(c_double, 'dfn2d_get_fracture_pos',
             c_void_p, c_size_t, c_size_t)

    def get_fracture(self, index):
        """
        返回第idx个裂缝的位置

        Args:
            index (int): 裂缝的索引。

        Returns:
            list or None: 包含四个浮点数的列表，表示裂缝的位置 [x0, y0, x1, y1]；
            如果索引无效，则返回None。
        """
        index = get_index(index, self.fracture_n)
        if index is not None:
            return [core.dfn2d_get_fracture_pos(self.handle, index, i) for i in
                    range(4)]
        else:
            return None

    def get_fractures(self):
        """
        返回所有的裂缝的位置

        Returns:
            list: 包含所有裂缝位置的列表，每个元素是一个包含四个浮点数的列表 [x0, y0, x1, y1]。
        """
        return [self.get_fracture(index) for index in range(self.fracture_n)]

    core.use(c_double, 'dfn2d_get_p21', c_void_p)

    @property
    def p21(self):
        """
        返回当前的裂缝的密度

        Returns:
            float: 当前的裂缝的密度。
        """
        return core.dfn2d_get_p21(self.handle)

    def print_file(self, path):
        """
        将所有的裂缝打印到文件

        Args:
            path (str): 要打印到的文件的路径。
        """
        with open(path, 'w') as file:
            for i in range(self.fracture_n):
                p = self.get_fracture(i)
                if p is not None:
                    file.write(f'{p[0]}\t{p[1]}\t{p[2]}\t{p[3]}\n')


class Lattice3(HasHandle):
    """
    用以临时存放数据序号的格子
    """
    core.use(c_void_p, 'new_lat3')
    core.use(None, 'del_lat3', c_void_p)

    def __init__(self, box=None, shape=None, handle: Optional[c_void_p] = None):
        """
        初始化Lattice3对象

        Args:
            box (list, optional): 数据在三维空间内的范围，
                格式为 [x0, y0, z0, x1, y1, z1]。默认为None。
            shape (list or float, optional): 单个网格的大小。
                如果是列表，长度应为3；如果是浮点数，则表示三个维度上的大小相同。默认为None。
            handle: 句柄对象。默认为None。
        """
        super().__init__(handle, core.new_lat3, core.del_lat3)
        if handle is None:
            if box is not None and shape is not None:
                self.create(box, shape)

    def __repr__(self) -> str:
        """
        返回对象的字符串表示形式

        Returns:
            str: 包含盒子范围、形状和大小的字符串。
        """
        return f'{type(self).__name__}(box={self.box}, shape={self.shape}, size={self.size})'

    core.use(None, 'lat3_save', c_void_p, c_char_p)

    def save(self, path: str):
        """
        序列化保存。可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.lat3_save(self.handle, make_c_char_p(path))

    core.use(None, 'lat3_load', c_void_p, c_char_p)

    def load(self, path: str):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 要读取的文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.lat3_load(self.handle, make_c_char_p(path))

    core.use(c_double, 'lat3_lrange', c_void_p, c_size_t)

    @property
    def box(self) -> List[float]:
        """
        数据在三维空间内的范围，格式为：
            x0, y0, z0, x1, y1, z1
        其中 x0为x的最小值，x1为x的最大值; y和z类似

        Returns:
            list: 包含六个浮点数的列表，表示数据在三维空间内的范围。
        """
        lr = [core.lat3_lrange(self.handle, i) for i in range(3)]
        sh = self.shape
        sz = self.size
        rr = [lr[i] + sh[i] * sz[i] for i in range(3)]
        return lr + rr

    core.use(c_double, 'lat3_shape', c_void_p, c_size_t)

    @property
    def shape(self) -> List[float]:
        """
        返回每个网格在三个维度上的大小

        Returns:
            list: 包含三个浮点数的列表，表示每个网格在三个维度上的大小。
        """
        return [core.lat3_shape(self.handle, i) for i in range(3)]

    core.use(c_size_t, 'lat3_size', c_void_p, c_size_t)

    @property
    def size(self) -> List[int]:
        """
        返回三维维度上网格的数量<至少为1>

        Returns:
            list: 包含三个整数的列表，表示三维维度上网格的数量。
        """
        return [core.lat3_size(self.handle, i) for i in range(3)]

    core.use(c_double, 'lat3_get_center', c_void_p, c_size_t, c_size_t)
    core.use(None, 'lat3_get_centers', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_center(self, index=None, x=None, y=None, z=None):
        """
        返回格子的中心点

        Args:
            index (list, optional): 包含三个整数的列表，表示格子的索引。
                默认为None。
            x (Vector, optional): 存储x坐标的向量。默认为None。
            y (Vector, optional): 存储y坐标的向量。默认为None。
            z (Vector, optional): 存储z坐标的向量。默认为None。

        Returns:
            list or tuple: 如果提供了index，则返回包含三个浮点数的列表，
            表示格子的中心点；否则，返回包含三个Vector对象的元组。
        """
        if index is not None:
            assert len(index) == 3
            return [core.lat3_get_center(self.handle, index[i], i) for i in range(3)]
        else:
            if not isinstance(x, Vector):
                x = Vector()
            if not isinstance(y, Vector):
                y = Vector()
            if not isinstance(z, Vector):
                z = Vector()
            core.lat3_get_centers(self.handle, x.handle, y.handle, z.handle)
            return x, y, z

    core.use(None, 'lat3_create',
             c_void_p, c_double, c_double, c_double, c_double, c_double, c_double,
             c_double, c_double, c_double)

    def create(self, box: List[float], shape: Union[List[float], Tuple[float], float]):
        """
        创建网格. 其中box为即将划分网格的区域的范围，参考box属性的注释.
        shape为单个网格的大小.

        Args:
            box (list): 包含六个浮点数的列表，表示数据在三维空间内的范围。
            shape (list or tuple or float): 单个网格的大小。如果是列表或元组，长度应为3；
                如果是浮点数，则表示三个维度上的大小相同。

        Raises:
            AssertionError: 如果box的长度不为6或shape的长度不为3。
        """
        assert len(box) == 6, f'box size must be 6, but box = {box}'
        if not is_array(shape):
            core.lat3_create(self.handle, *box, shape, shape, shape)
        else:
            assert len(shape) == 3, f'shape size must be 3, but shape = {shape}'
            jx = shape[0]
            jy = shape[1]
            jz = shape[2]
            core.lat3_create(self.handle, *box, jx, jy, jz)

    core.use(None, 'lat3_random_shuffle', c_void_p)

    def random_shuffle(self):
        """
        随机更新格子里面的数据的顺序<随机洗牌>
        """
        core.lat3_random_shuffle(self.handle)

    core.use(None, 'lat3_add_point',
             c_void_p, c_double, c_double, c_double, c_size_t)

    def add_point(self, pos, index):
        """
        将位置在pos，序号为index的对象放入到格子里面<不会去查重复>

        Args:
            pos (list): 包含三个浮点数的列表，表示对象的位置。
            index (int): 对象的序号。

        Raises:
            AssertionError: 如果pos的长度不为3。
        """
        assert len(pos) == 3, f'pos = {pos}'
        core.lat3_add_point(self.handle, pos[0], pos[1], pos[2], index)


class DDMSolution2(HasHandle):
    """
    二维DDM的基本解：计算裂缝单元在任意位置的诱导应力.
    """
    core.use(c_void_p, 'new_ddm_sol2')
    core.use(None, 'del_ddm_sol2', c_void_p)

    def __init__(self, handle: Optional[c_void_p] = None):
        """
        初始化DDMSolution2对象

        Args:
            handle (Optional[c_void_p], optional): 句柄对象。默认为None。
        """
        super().__init__(handle, core.new_ddm_sol2, core.del_ddm_sol2)

    def __repr__(self):
        return (f'{type(self).__name__}(handle={int(self.handle)}, '
                f'alpha={self.alpha}, beta={self.beta}, '
                f'shear_modulus={self.shear_modulus / 1.0e9}GPa, '
                f'poisson_ratio={self.poisson_ratio}, '
                f'adjust_coeff={self.adjust_coeff})')

    core.use(None, 'ddm_sol2_save', c_void_p, c_char_p)
    core.use(None, 'ddm_sol2_load', c_void_p, c_char_p)

    def save(self, path: str):
        """
        序列化保存。可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.ddm_sol2_save(self.handle, make_c_char_p(path))

    def load(self, path: str):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 要读取的文件的路径。
        """
        if isinstance(path, str):
            core.ddm_sol2_load(self.handle, make_c_char_p(path))

    core.use(None, 'ddm_sol2_set_alpha', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_alpha', c_void_p)

    @property
    def alpha(self) -> float:
        """
        获取alpha值

        Returns:
            float: alpha值
        """
        return core.ddm_sol2_get_alpha(self.handle)

    @alpha.setter
    def alpha(self, value: float):
        """
        设置alpha值

        Args:
            value (float): 要设置的alpha值
        """
        core.ddm_sol2_set_alpha(self.handle, value)

    core.use(None, 'ddm_sol2_set_beta', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_beta', c_void_p)

    @property
    def beta(self) -> float:
        """
        获取beta值

        Returns:
            float: beta值
        """
        return core.ddm_sol2_get_beta(self.handle)

    @beta.setter
    def beta(self, value: float):
        """
        设置beta值

        Args:
            value (float): 要设置的beta值
        """
        core.ddm_sol2_set_beta(self.handle, value)

    core.use(None, 'ddm_sol2_set_shear_modulus', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_shear_modulus', c_void_p)

    @property
    def shear_modulus(self) -> float:
        """
        获取剪切模量

        Returns:
            float: 剪切模量
        """
        return core.ddm_sol2_get_shear_modulus(self.handle)

    @shear_modulus.setter
    def shear_modulus(self, value: float):
        """
        设置剪切模量

        Args:
            value (float): 要设置的剪切模量
        """
        core.ddm_sol2_set_shear_modulus(self.handle, value)

    core.use(None, 'ddm_sol2_set_poisson_ratio', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_poisson_ratio', c_void_p)

    @property
    def poisson_ratio(self) -> float:
        """
        获取泊松比

        Returns:
            float: 泊松比
        """
        return core.ddm_sol2_get_poisson_ratio(self.handle)

    @poisson_ratio.setter
    def poisson_ratio(self, value: float):
        """
        设置泊松比

        Args:
            value (float): 要设置的泊松比
        """
        core.ddm_sol2_set_poisson_ratio(self.handle, value)

    core.use(None, 'ddm_sol2_set_adjust_coeff', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_adjust_coeff', c_void_p)

    @property
    def adjust_coeff(self) -> float:
        """
        获取调整系数

        Returns:
            float: 调整系数
        """
        return core.ddm_sol2_get_adjust_coeff(self.handle)

    @adjust_coeff.setter
    def adjust_coeff(self, value: float):
        """
        设置调整系数

        Args:
            value (float): 要设置的调整系数
        """
        core.ddm_sol2_set_adjust_coeff(self.handle, value)

    core.use(None, 'ddm_sol2_get_induced',
             c_void_p, c_void_p,
             c_double, c_double, c_double, c_double,
             c_double, c_double, c_double, c_double,
             c_double, c_double, c_double)

    def get_induced(self, pos: List[float], fracture: List[float], ds: float, dn: float, height: float,
                    buffer: Optional[Tensor2] = None) -> Tensor2:
        """
        返回一个裂缝单元的诱导应力

        Args:
            buffer: 用于存储结果的张量
            pos (List[float]): 位置信息，长度可以为2或4。
            fracture (List[float]): 裂缝信息，长度必须为4。
            ds (float): 未知含义的参数
            dn (float): 未知含义的参数
            height (float): 高度

        Returns:
            Tensor2: 结果张量
        """
        assert len(fracture) == 4, "fracture must have 4 elements"
        if isinstance(buffer, Tensor2):
            res = buffer
        else:
            res = Tensor2()
        assert isinstance(res, Tensor2)
        if len(pos) == 2:
            core.ddm_sol2_get_induced(self.handle, res.handle, *pos, *pos,
                                      *fracture, ds, dn, height)
        else:
            assert len(pos) == 4, "pos must have 4 or 2elements"
            core.ddm_sol2_get_induced(self.handle, res.handle, *pos,
                                      *fracture, ds, dn, height)
        return res


class FractureNetwork(HasHandle):
    """
    裂缝网络(二维). 由顶点和裂缝所组成的网络. 存储裂缝网络的数据.
    """

    class VertexData(Object):
        """
        顶点的数据
        """

        def __init__(self, handle: c_void_p):
            """
            初始化顶点数据对象

            Args:
                handle: 顶点数据的句柄
            """
            self.handle = handle

        core.use(c_double, 'frac_nd_get_pos', c_void_p, c_size_t)

        @property
        def x(self) -> float:
            """
            顶点的x坐标
            """
            return core.frac_nd_get_pos(self.handle, 0)

        @property
        def y(self) -> float:
            """
            顶点的y坐标
            """
            return core.frac_nd_get_pos(self.handle, 1)

        @property
        def pos(self) -> Tuple[float, float]:
            """
            顶点的位置
            """
            return self.x, self.y

        core.use(c_double, 'frac_nd_get_attr', c_void_p, c_size_t)
        core.use(None, 'frac_nd_set_attr', c_void_p, c_size_t, c_double)

        def get_attr(self, index: Optional[int], default_val: Optional[float] = None, *,
                     left: float = -1.0e100, right: float = 1.0e100) -> Optional[float]:
            """
            获取第index个自定义属性

            Args:
                index (Optional[int]): 自定义属性的索引
                default_val (float, optional): 属性不存在时的默认值，默认为None
                left (float): 属性的左边界，默认为-1.0e100
                right (float): 属性的右边界，默认为1.0e100

            Returns:
                float: 如果属性存在且在有效范围内，返回属性值；否则返回默认值
            """
            if index is None:
                return default_val
            # 当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
            assert index >= 0, "属性索引必须大于等于0"
            value = core.frac_nd_get_attr(self.handle, index)
            if left <= value <= right:
                return value
            else:
                return default_val

        def set_attr(self, index: Optional[int], value: Optional[float]):
            """
            设置第index个自定义属性

            Args:
                index (Optional[int]): 自定义属性的索引
                value (float): 要设置的属性值

            Returns:
                VertexData: 返回当前顶点数据对象
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            assert index >= 0, "属性索引必须大于等于0"
            core.frac_nd_set_attr(self.handle, index, value)
            return self

    class FractureData(HasHandle):
        """
        裂缝的数据
        """
        core.use(c_void_p, 'new_frac_bd')
        core.use(None, 'del_frac_bd', c_void_p)

        def __init__(self, handle: Optional[c_void_p] = None):
            """
            初始化裂缝数据对象

            Args:
                handle: 裂缝数据的句柄，默认为None
            """
            super().__init__(handle, core.new_frac_bd, core.del_frac_bd)

        core.use(c_double, 'frac_bd_get_attr', c_void_p, c_size_t)
        core.use(None, 'frac_bd_set_attr', c_void_p, c_size_t, c_double)

        def get_attr(self, index: Optional[int], default_val: Optional[float] = None, *,
                     left: float = -1.0e100, right: float = 1.0e100) -> Optional[float]:
            """
            获取第index个自定义属性

            Args:
                index (Optional[int]): 自定义属性的索引
                default_val (float, optional): 属性不存在时的默认值，默认为None
                left (float): 属性的左边界，默认为-1.0e100
                right (float): 属性的右边界，默认为1.0e100

            Returns:
                Optional[float]: 如果属性存在且在有效范围内，返回属性值；否则返回默认值
            """
            if index is None:
                return default_val
            # 当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
            assert index >= 0, "属性索引必须大于等于0"
            value = core.frac_bd_get_attr(self.handle, index)
            if left <= value <= right:
                return value
            else:
                return default_val

        def set_attr(self, index: Optional[int], value: Optional[float]):
            """
            设置第index个自定义属性

            Args:
                index (Optional[int]): 自定义属性的索引
                value (Optional[float]): 要设置的属性值

            Returns:
                FractureData: 返回当前裂缝数据对象
            """
            if index is None:
                return self
            if value is None:  # 此时，相当于移除属性
                value = 1.0e200
            core.frac_bd_set_attr(self.handle, index, value)
            return self

        core.use(c_double, 'frac_bd_get_ds', c_void_p)
        core.use(None, 'frac_bd_set_ds', c_void_p, c_double)

        @property
        def ds(self) -> float:
            """
            ds属性. 裂缝的剪切间断位移 [单位: m]
            """
            return core.frac_bd_get_ds(self.handle)

        @ds.setter
        def ds(self, value: float):
            """
            ds属性. 裂缝的剪切间断位移 [单位: m]
            """
            core.frac_bd_set_ds(self.handle, value)

        core.use(c_double, 'frac_bd_get_dn', c_void_p)
        core.use(None, 'frac_bd_set_dn', c_void_p, c_double)

        @property
        def dn(self) -> float:
            """
            dn属性. 裂缝的法向间断位移 [单位: m]
            """
            return core.frac_bd_get_dn(self.handle)

        @dn.setter
        def dn(self, value: float):
            """
            dn属性. 裂缝的法向间断位移 [单位: m]
            """
            core.frac_bd_set_dn(self.handle, value)

        core.use(c_double, 'frac_bd_get_h', c_void_p)
        core.use(None, 'frac_bd_set_h', c_void_p, c_double)

        @property
        def h(self) -> float:
            """
            裂缝的高度 [单位: m]
            """
            return core.frac_bd_get_h(self.handle)

        @h.setter
        def h(self, value: float):
            """
            裂缝的高度 [单位: m]
            """
            core.frac_bd_set_h(self.handle, value)

        core.use(c_double, 'frac_bd_get_fric', c_void_p)
        core.use(None, 'frac_bd_set_fric', c_void_p, c_double)

        @property
        def f(self) -> float:
            """
            裂缝的摩擦系数
            """
            return core.frac_bd_get_fric(self.handle)

        @f.setter
        def f(self, value: float):
            """
            裂缝的摩擦系数
            """
            core.frac_bd_set_fric(self.handle, value)

        core.use(c_double, 'frac_bd_get_p0', c_void_p)
        core.use(None, 'frac_bd_set_p0', c_void_p, c_double)

        @property
        def p0(self) -> float:
            """
            裂缝内流体压力公式中的p0参数: fp = p0 + k * dn
            """
            return core.frac_bd_get_p0(self.handle)

        @p0.setter
        def p0(self, value: float):
            """
            裂缝内流体压力公式中的p0参数: fp = p0 + k * dn
            """
            core.frac_bd_set_p0(self.handle, value)

        core.use(c_double, 'frac_bd_get_k', c_void_p)
        core.use(None, 'frac_bd_set_k', c_void_p, c_double)

        @property
        def k(self) -> float:
            """
            裂缝内流体压力公式中的k参数: fp = p0 + k * dn
            """
            return core.frac_bd_get_k(self.handle)

        @k.setter
        def k(self, value: float):
            """
            裂缝内流体压力公式中的k参数: fp = p0 + k * dn
            """
            core.frac_bd_set_k(self.handle, value)

        core.use(c_double, 'frac_bd_get_fp', c_void_p)

        @property
        def fp(self) -> float:
            """
            根据当前的dn、p0和k计算得到的裂缝内流体压力: fp = p0 + k * dn
            """
            return core.frac_bd_get_fp(self.handle)

        core.use(c_void_p, 'frac_bd_get_flu', c_void_p)

        @property
        def flu_expr(self) -> Optional[LinearExpr]:
            """
            流体的映射数据. 用于在裂缝扩展的时候，跟踪流体的数据
            """
            handle = core.frac_bd_get_flu(self.handle)
            if handle:
                return LinearExpr(handle=handle)
            else:
                return None

        @flu_expr.setter
        def flu_expr(self, value: LinearExpr):
            """
            流体的映射数据. 用于在裂缝扩展的时候，跟踪流体的数据
            """
            if isinstance(value, LinearExpr):
                left = self.flu_expr
                if left is not None:
                    left.clone(value)

        @property
        def flu(self):
            """
            流体的映射数据（已弃用，请使用flu_expr）
            """
            warnings.warn(
                f'{type(self).__name__}: flu is deprecated,'
                f' please use flu_expr instead.',
                DeprecationWarning, stacklevel=2)
            return self.flu_expr

        @flu.setter
        def flu(self, value):
            """
            流体的映射数据（已弃用，请使用flu_expr）
            """
            warnings.warn(
                f'{type(self).__name__}: flu is deprecated,'
                f' please use flu_expr instead.',
                DeprecationWarning, stacklevel=2)
            self.flu_expr = value

        @staticmethod
        def create(**kwargs) -> 'FractureNetwork.FractureData':
            """
            创建裂缝数据
            """
            data = FractureNetwork.FractureData()
            for key, value in kwargs.items():
                setattr(data, key, value)
            return data

    class Vertex(VertexData):
        """
        顶点
        """
        core.use(c_void_p, 'frac_nt_get_nd', c_void_p, c_size_t)

        def __init__(self, network: "FractureNetwork", index: int):
            """
            初始化顶点对象

            Args:
                network (FractureNetwork): 所属的裂缝网络对象
                index (int): 顶点的索引
            """
            assert isinstance(network, FractureNetwork)
            assert isinstance(index, int)
            assert index < network.vertex_number
            self.network = network
            self.index = index
            super().__init__(handle=core.frac_nt_get_nd(network.handle, index))

        def __str__(self) -> str:
            """
            返回顶点对象的字符串表示

            Returns:
                str: 包含顶点索引和位置的字符串
            """
            return f'zml.FractureNetwork.Vertex(index={self.index}, pos=[{self.x}, {self.y}])'

        core.use(c_size_t, 'frac_nt_nd_get_bd_n', c_void_p, c_size_t)

        @property
        def fracture_number(self) -> int:
            """
            获取共享此顶点的裂缝单元的数量

            Returns:
                int: 共享此顶点的裂缝单元的数量
            """
            return core.frac_nt_nd_get_bd_n(self.network.handle, self.index)

        core.use(c_size_t, 'frac_nt_nd_get_bd_i', c_void_p, c_size_t, c_size_t)

        def get_fracture(self, index: Optional[int]) -> Optional["FractureNetwork.Fracture"]:
            """
            获取此顶点周边的裂缝单元

            Args:
                index (Optional[int]): 裂缝单元的索引

            Returns:
                Fracture: 此顶点周边的裂缝单元对象，如果索引无效则返回None
            """
            index = get_index(index, self.fracture_number)
            if index is not None:
                return self.network.get_fracture(core.frac_nt_nd_get_bd_i(self.network.handle, self.index, index))
            else:
                return None

        @property
        def fractures(self) -> Iterable['FractureNetwork.Fracture']:
            """
            获取所有的裂缝，用于迭代

            Returns:
                Iterator: 包含所有裂缝的迭代器对象
            """
            return Iterator(model=self, count=self.fracture_number, get=lambda m, ind: m.get_fracture(ind))

        @property
        def vertex_number(self) -> int:
            """
            获取此顶点周围的顶点的数量
            """
            return self.fracture_number

        def get_vertex(self, index: Optional[int]) -> Optional["FractureNetwork.Vertex"]:
            """
            获取此顶点周围的顶点

            Args:
                index (Optional[int]): 周围的顶点的索引，从0开始

            Returns:
                Vertex: 裂缝的顶点对象，如果索引无效则返回None
            """
            f = self.get_fracture(index)
            if f is None:
                return None
            else:
                return f.get_another(self)

        @property
        def vertexes(self) -> Iterable['FractureNetwork.Vertex']:
            """
            获取此顶点周围所有的顶点，用于迭代

            Returns:
                Iterator: 包含所有顶点的迭代器对象
            """
            return Iterator(model=self, count=self.vertex_number, get=lambda m, ind: m.get_vertex(ind))

    class Fracture(FractureData):
        """
        裂缝.
        """
        core.use(c_void_p, 'frac_nt_get_bd', c_void_p, c_size_t)

        def __init__(self, network: "FractureNetwork", index: int):
            """
            初始化裂缝对象

            Args:
                network (FractureNetwork): 所属的裂缝网络对象
                index (int): 裂缝的索引
            """
            assert isinstance(network, FractureNetwork)
            assert isinstance(index, int)
            assert index < network.fracture_number
            super().__init__(handle=core.frac_nt_get_bd(network.handle, index))
            self.network = network
            self.index = index

        def __str__(self) -> str:
            """
            返回裂缝对象的字符串表示

            Returns:
                str: 包含裂缝索引、位置、ds和dn属性的字符串
            """
            return f'zml.FractureNetwork.Fracture(index={self.index}, pos={self.pos}, ds={self.ds}, dn={self.dn})'

        @property
        def vertex_number(self) -> int:
            """
            获取裂缝顶点的数量

            Returns:
                int: 裂缝顶点的数量，固定为2
            """
            return 2

        core.use(c_size_t, 'frac_nt_bd_get_nd_i', c_void_p, c_size_t, c_size_t)

        def get_vertex(self, index: Optional[int]) -> Optional["FractureNetwork.Vertex"]:
            """
            获取裂缝的顶点

            Args:
                index (Optional[int]): 顶点的索引

            Returns:
                Vertex: 裂缝的顶点对象，如果索引无效则返回None
            """
            index = get_index(index, self.vertex_number)
            if index is not None:
                return self.network.get_vertex(core.frac_nt_bd_get_nd_i(self.network.handle, self.index, index))
            else:
                return None

        @property
        def vertexes(self) -> Tuple['FractureNetwork.Vertex', 'FractureNetwork.Vertex']:
            """
            获取所有的顶点，用于迭代
            """
            v0 = self.get_vertex(0)
            v1 = self.get_vertex(1)
            assert isinstance(v0, FractureNetwork.Vertex)
            assert isinstance(v1, FractureNetwork.Vertex)
            return v0, v1

        def get_another(self, vertex: "FractureNetwork.Vertex") -> Optional["FractureNetwork.Vertex"]:
            """
            一个Fracture有两个顶点，给定一个顶点，返回另外一个顶点
            """
            if vertex.network.handle != self.network.handle:
                return None
            v0, v1 = self.vertexes
            if vertex.handle == v0.handle:
                return v1
            elif vertex.handle == v1.handle:
                return v0
            else:
                return None

        @property
        def pos(self) -> Tuple[float, float, float, float]:
            """
            获取裂缝的位置
            Returns:
                tuple: 包含裂缝两个端点的x和y坐标的元组，格式为 (x0, y0, x1, y1)
            """
            v0 = self.get_vertex(0)
            v1 = self.get_vertex(1)
            assert isinstance(v0, FractureNetwork.Vertex)
            assert isinstance(v1, FractureNetwork.Vertex)
            p0 = v0.pos
            p1 = v1.pos
            return p0[0], p0[1], p1[0], p1[1]

        @property
        def length(self) -> float:
            """
            获取裂缝的长度
            Returns:
                float: 裂缝的长度，根据裂缝两个端点的位置计算
            """
            v0 = self.get_vertex(0)
            v1 = self.get_vertex(1)
            assert isinstance(v0, FractureNetwork.Vertex)
            assert isinstance(v1, FractureNetwork.Vertex)
            p0 = v0.pos
            p1 = v1.pos
            return get_distance(p0, p1)

        @property
        def center(self) -> Tuple[float, float]:
            """
            获取裂缝的中心点坐标

            Returns:
                tuple: 包含裂缝中心点的x和y坐标的元组
            """
            v0 = self.get_vertex(0)
            v1 = self.get_vertex(1)
            assert isinstance(v0, FractureNetwork.Vertex)
            assert isinstance(v1, FractureNetwork.Vertex)
            p0 = v0.pos
            p1 = v1.pos
            return (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2

        core.use(c_double, 'frac_nt_get_bd_angle', c_void_p, c_size_t)

        @property
        def angle(self) -> float:
            """
            获取裂缝的方向角度

            Returns:
                float: 裂缝的方向角度
            """
            return core.frac_nt_get_bd_angle(self.network.handle, self.index)

    core.use(c_void_p, 'new_frac_nt')
    core.use(None, 'del_frac_nt', c_void_p)

    def __init__(self, path: Optional[str] = None, handle: Optional[c_void_p] = None):
        """
        初始化裂缝网络对象

        Args:
            path (str, optional): 序列化文件的路径，用于加载数据，默认为None
            handle (c_void_p, optional): 裂缝网络的句柄，默认为None
        """
        super().__init__(handle, core.new_frac_nt, core.del_frac_nt)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
        try:
            name = type(self).__name__
            log(f'{name} created', tag=f'{name}_Init')
        except:
            pass

    def __repr__(self) -> str:
        return f'{type(self).__name__}(handle={int(self.handle)}, vertex_n={self.vertex_number}, fracture_n={self.fracture_number})'

    core.use(None, 'frac_nt_save', c_void_p, c_char_p)

    def save(self, path: str):
        """
        序列化保存裂缝网络数据

        可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

        Args:
            path (str): 保存文件的路径
        """
        if isinstance(path, str):
            make_parent(path)
            core.frac_nt_save(self.handle, make_c_char_p(path))

    core.use(None, 'frac_nt_load', c_void_p, c_char_p)

    def load(self, path: str):
        """
        读取序列化文件来加载裂缝网络数据

        根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 要读取的文件的路径
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.frac_nt_load(self.handle, make_c_char_p(path))

    core.use(None, 'frac_nt_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'frac_nt_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt: str = 'binary') -> FileMap:
        """
        将裂缝网络数据序列化到一个Filemap中

        Args:
            fmt (str, optional): 序列化格式，可以为 'text', 'xml' 或 'binary'，
                默认为 'binary'

        Returns:
            FileMap: 包含序列化数据的Filemap对象
        """
        fmap = FileMap()
        core.frac_nt_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt: str = 'binary'):
        """
        从Filemap中读取序列化的裂缝网络数据

        Args:
            fmap (FileMap): 包含序列化数据的Filemap对象
            fmt (str, optional): 序列化格式，可以为 'text', 'xml' 或 'binary'，
                默认为 'binary'
        """
        assert isinstance(fmap, FileMap)
        core.frac_nt_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self) -> FileMap:
        """
        获取裂缝网络数据的二进制序列化Filemap对象

        Returns:
            FileMap: 包含二进制序列化数据的Filemap对象
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: FileMap):
        """
        从Filemap中加载二进制序列化的裂缝网络数据

        Args:
            value (FileMap): 包含二进制序列化数据的Filemap对象
        """
        self.from_fmap(value, fmt='binary')

    core.use(c_size_t, 'frac_nt_get_nd_n', c_void_p)

    @property
    def vertex_number(self):
        """
        获取顶点的数量

        Returns:
            int: 顶点的数量
        """
        return core.frac_nt_get_nd_n(self.handle)

    def get_vertex(self, index: Optional[int]) -> Optional['FractureNetwork.Vertex']:
        """
        获取指定索引的顶点

        Args:
            index (Optional[int]): 顶点的索引

        Returns:
            Vertex: 顶点对象，如果索引无效则返回None
        """
        index = get_index(index, self.vertex_number)
        if index is not None:
            return FractureNetwork.Vertex(self, index)
        else:
            return None

    core.use(c_size_t, 'frac_nt_get_bd_n', c_void_p)

    @property
    def fracture_number(self) -> int:
        """
        获取裂缝单元(线段)的数量

        Returns:
            int: 裂缝单元的数量
        """
        return core.frac_nt_get_bd_n(self.handle)

    def get_fracture(self, index: Optional[int]) -> Optional['FractureNetwork.Fracture']:
        """
        获取指定索引的裂缝单元

        Args:
            index (Optional[int]): 裂缝单元的索引

        Returns:
            Fracture: 裂缝单元对象，如果索引无效则返回None
        """
        index = get_index(index, self.fracture_number)
        if index is not None:
            return FractureNetwork.Fracture(self, index)
        else:
            return None

    core.use(c_size_t, 'frac_nt_add_nd', c_void_p, c_double, c_double)

    def add_vertex(self, x, y) -> 'FractureNetwork.Vertex':
        """
        添加顶点(要添加裂缝单元，必须首先添加顶点)

        Args:
            x (float): 顶点的x坐标
            y (float): 顶点的y坐标

        Returns:
            Vertex: 新添加的顶点对象
        """
        index = core.frac_nt_add_nd(self.handle, x, y)
        res = self.get_vertex(index)
        assert res is not None
        return res

    core.use(c_size_t, 'frac_nt_add_bd', c_void_p, c_size_t, c_size_t)
    core.use(None, 'frac_nt_add_frac',
             c_void_p, c_double, c_double, c_double, c_double, c_double, c_void_p)

    def add_fracture(self, first=None, second=None, *,
                     lave=None, data=None,
                     pos=None) -> Optional['FractureNetwork.Fracture']:
        """
        添加裂缝单元(线段)

        注意：
            当给定lave的时候，将根据给定的lave来分割单元，并自动处理和已有裂缝之间的位置关系。

        Args:
            first (tuple, optional): 第一个顶点的坐标或者序号，默认为None
            second (tuple, optional): 第二个顶点的坐标或者序号，默认为None
            lave (float, optional): 分割单元的参数，默认为None
            data (FractureData, optional): 裂缝数据对象，默认为None
            pos (tuple, optional): 裂缝的位置，格式为 (x0, y0, x1, y1)， 默认为None

        Returns:
            Fracture: 新添加的裂缝单元对象，如果使用lave参数则返回None
        """
        if pos is not None:
            assert len(pos) == 4
            assert first is None and second is None, \
                'you should not set first and second when pos is given'
            first = pos[0: 2]
            second = pos[2: 4]

        if lave is None:
            index = core.frac_nt_add_bd(self.handle, first, second)
            return self.get_fracture(index)
        else:
            if data is not None:
                assert isinstance(data, FractureNetwork.FractureData)
            core.frac_nt_add_frac(
                self.handle, first[0], first[1], second[0], second[1], lave,
                0 if data is None else data.handle)
            return None

    core.use(None, 'frac_nt_clear', c_void_p)

    def clear(self):
        """
        清除裂缝网络中的所有数据
        """
        core.frac_nt_clear(self.handle)

    @property
    def vertexes(self) -> Iterable['FractureNetwork.Vertex']:
        """
        获取所有的顶点，用于迭代

        Returns:
            Iterator: 包含所有顶点的迭代器对象
        """
        return Iterator(model=self, count=self.vertex_number, get=lambda m, ind: m.get_vertex(ind))

    @property
    def fractures(self) -> Iterable['FractureNetwork.Fracture']:
        """
        获取所有的裂缝，用于迭代

        Returns:
            Iterator: 包含所有裂缝的迭代器对象
        """
        return Iterator(model=self, count=self.fracture_number, get=lambda m, ind: m.get_fracture(ind))

    core.use(None, 'frac_nt_get_induced_at', c_void_p, c_void_p, c_double, c_double, c_void_p)
    core.use(None, 'frac_nt_get_induced_along',
             c_void_p, c_void_p, c_double, c_double, c_double, c_double, c_void_p)
    core.use(None, 'frac_nt_get_induced', c_void_p, c_size_t, c_size_t, c_void_p)

    def get_induced(self, pos=None, sol2=None, buf=None, *,
                    fa_xy=None, fa_yy=None, matrix=None):
        """
        返回在指定位置的诱导应力

        Args:
            pos (list, optional): 位置信息，长度可以为2或4，默认为None
            sol2 (DDMSolution2, optional): 二维DDM的基本解对象，默认为None
            buf (Tensor2, optional): 存储诱导应力的张量对象，默认为None
            fa_xy (int, optional): 地应力的切向分量，默认为None
            fa_yy (int, optional): 地应力的法向分量，默认为None
            matrix (InfMatrix, optional): 影响系数矩阵对象，默认为None

        Returns:
            Tensor2: 诱导应力张量对象
        """
        if fa_xy is not None and fa_yy is not None and matrix is not None:
            assert isinstance(matrix, InfMatrix)
            assert self.fracture_number == matrix.size
            core.frac_nt_get_induced(self.handle, fa_xy, fa_yy, matrix.handle)
            return None
        else:
            assert len(pos) == 2 or len(pos) == 4
            assert isinstance(sol2, DDMSolution2)
            if not isinstance(buf, Tensor2):
                buf = Tensor2()
            if len(pos) == 2:
                core.frac_nt_get_induced_at(self.handle, buf.handle,
                                            pos[0], pos[1], sol2.handle)
            else:
                core.frac_nt_get_induced_along(self.handle, buf.handle,
                                               pos[0], pos[1], pos[2], pos[3],
                                               sol2.handle)
            return buf

    core.use(c_size_t, 'frac_nt_update_disp',
             c_void_p, c_void_p, c_size_t, c_size_t, c_double, c_double,
             c_size_t, c_size_t, c_double, c_double, c_double, c_double)

    def update_disp(self, matrix: 'InfMatrix', fa_yy=IDX_INF, fa_xy=IDX_INF,
                    gradw_max=0, err_max=0.1, iter_min=10,
                    iter_max=10000,
                    ratio_max=0.99, dist_max=1.0e6,
                    dn_max=1e100, ds_max=1e100):
        """
        更新位移(这是DDM计算的最核心的函数)

        Args:
            matrix (InfMatrix): 最新的应力影响矩阵
            fa_yy (float, optional): 在裂缝上，地应力的法向分量。
                当应力场更新了之后，必须要更新这个属性，默认为INT_INF
            fa_xy (float, optional): 在裂缝上，地应力的切向分量。
                当应力场更新了之后，必须要更新这个属性，默认为INT_INF
            gradw_max (float, optional): 裂缝宽度的最大的变化梯度，默认为0
            err_max (float, optional): 迭代的最大残差，默认为0.1
            iter_min (int, optional): 迭代的最少次数，默认为10
            iter_max (int, optional): 迭代的最大次数，默认为10000
            ratio_max (float, optional): 当收敛速率低于这个数值的时候，终止迭代，
                默认为0.99
            dist_max (float, optional): 将应力考虑为近场的临界的距离，
                默认为1.0e6
            dn_max (float, optional): 法向位移的最大值，默认为1e100
            ds_max (float, optional): 切向位移的最大值，默认为1e100

        Returns:
            int: 核心函数的返回值
        """
        assert isinstance(matrix, InfMatrix)
        return core.frac_nt_update_disp(
            self.handle, matrix.handle, fa_yy, fa_xy, gradw_max, err_max, iter_min, iter_max, ratio_max, dist_max,
            dn_max, ds_max)

    core.use(None, 'frac_nt_extend_tip',
             c_void_p, c_void_p, c_void_p, c_double, c_double, c_size_t, c_double)

    def extend_tip(self, kic, sol2, l_extend, va_wmin=IDX_INF,
                   angle_max=0.6,
                   lave=-1.0):
        """
        尝试进行裂缝的扩展

        其中 l_extend是扩展的长度。
        注意，默认的情况下(即lave小于等于0的时候)，将简单地在裂缝的尖端添加新的单元。
        当lave大于0的时候，将首先尝试增加尖端裂缝单元的长度（并在长度大于特定阈值的时候进行分割）。

        在2025-1-8添加了lave参数。

        Args:
            kic (Tensor2): 断裂韧性张量对象
            sol2 (DDMSolution2): 二维DDM的基本解
            l_extend (float): 裂缝扩展的长度
            va_wmin (float, optional): Vertex的属性，返回一个允许扩展的最小的裂缝宽度。
                    如果实际宽度小于这个数值，则不允许在这个Vertex的裂缝扩展。
                    如果不希望裂缝在某个位置扩展，则可以设置这个属性，
                    并将最小宽度设置为一个
                    非常大的数值。
                    va_wmin的默认数值为INT_INF，这是这个不存在的属性ID。
                    当内核监测到Vertex
                    没有定义给定的属性时，则默认wmin为0，即只要裂缝的开度大于0，就可以允许
                    裂缝在这个位置扩展
            angle_max (float, optional): 最大角度阈值，默认为0.6
            lave (float, optional): 分割单元的参数，默认为-1.0
        """
        assert isinstance(kic, Tensor2)
        assert isinstance(sol2, DDMSolution2)
        core.frac_nt_extend_tip(self.handle, kic.handle, sol2.handle, lave, l_extend, va_wmin, angle_max)

    core.use(None, 'frac_nt_get_sub_network', c_void_p, c_size_t, c_void_p)

    def get_sub_network(self, fa_key: int, sub: 'FractureNetwork' = None) -> 'FractureNetwork':
        """
        创建一个子网络

        注意，在裂缝中，所有定义了fa_key且属性值大于0.5的裂缝单元将被保留。

        Args:
            fa_key (int): 属性，用于判断是否保留裂缝单元
            sub (FractureNetwork, optional): 保存结果的缓冲区，默认为None

        Returns:
            FractureNetwork: 创建的子网络对象
        """
        if not isinstance(sub, FractureNetwork):
            sub = FractureNetwork()
        core.frac_nt_get_sub_network(self.handle, fa_key, sub.handle)
        return sub

    core.use(None, 'frac_nt_copy_fracture_from_sub_network', c_void_p, c_size_t, c_void_p)

    def copy_fracture_from_sub_network(self, fa_key: int, sub: 'FractureNetwork'):
        """
        从子网络中拷贝裂缝数据

        Args:
            fa_key (int): 属性，用于判断是否保留裂缝单元
            sub (FractureNetwork): 子裂缝网络对象
        """
        if isinstance(sub, FractureNetwork):
            core.frac_nt_copy_fracture_from_sub_network(self.handle, fa_key, sub.handle)

    core.use(c_size_t, 'frac_nt_get_nearest_vertex_id', c_void_p, c_double, c_double)

    def get_nearest_vertex(self, pos: Union[Tuple[float, float], List[float]]) -> Optional["FractureNetwork.Vertex"]:
        """
        返回与给定位置距离最近的Vertex

        Args:
            pos (tuple | list): 包含两个浮点数的元组，表示二维空间中的位置。

        Returns:
            Vertex: 与给定位置距离最近的Vertex对象，
                如果网格中有Vertex；否则返回None。
        """
        if self.vertex_number > 0:
            pos = [1.0e210 if pos[i] is None else pos[i] for i in range(2)]
            return self.get_vertex(core.frac_nt_get_nearest_vertex_id(self.handle, pos[0], pos[1]))
        else:
            return None


class InfMatrix(HasHandle):
    """
    影响系数矩阵.
    """
    core.use(c_void_p, 'new_frac_mat')
    core.use(None, 'del_frac_mat', c_void_p)

    def __init__(self, network=None, sol2=None, handle=None):
        """
        创建给定handle的引用

        Args:
            network (FractureNetwork, optional): 裂缝网络对象，默认为None。
            sol2 (DDMSolution2, optional): 二维DDM的基本解对象，默认为None。
            handle (c_void_p, optional): 矩阵的句柄，默认为None。

        Raises:
            AssertionError: 如果 network 不是 FractureNetwork 类型，
            或者 sol2 不是 DDMSolution2 类型。
        """
        super().__init__(handle, core.new_frac_mat, core.del_frac_mat)
        if network is not None and sol2 is not None:
            self.update(network=network, sol2=sol2)

    def __repr__(self):
        return f'{type(self).__name__}(handle={int(self.handle)}, size={self.size})'

    core.use(c_size_t, 'frac_mat_size', c_void_p)

    @property
    def size(self) -> int:
        """
        获取裂缝单元的数量

        Returns:
            int: 裂缝单元的数量
        """
        return core.frac_mat_size(self.handle)

    core.use(None, 'frac_mat_create', c_void_p, c_void_p, c_void_p)

    def update(self, network, sol2):
        """
        更新矩阵

        Args:
            network (FractureNetwork): 裂缝网络对象。
            sol2 (DDMSolution2): 二维DDM的基本解对象。

        Raises:
            AssertionError: 如果 network 不是 FractureNetwork 类型，
            或者 sol2 不是 DDMSolution2 类型。
        """
        assert isinstance(network, FractureNetwork)
        assert isinstance(sol2, DDMSolution2)
        core.frac_mat_create(self.handle, network.handle, sol2.handle)


class FracAlg:
    """
    提供一些裂缝相关的基础的算法.
    """

    @staticmethod
    def update_disp(network: FractureNetwork, *args, **kwargs):
        warnings.warn(
            'FracAlg.update_disp will be removed after 2026-2-11, '
            'use FractureNetwork.update_disp instead',
            DeprecationWarning, stacklevel=2)
        return network.update_disp(*args, **kwargs)

    @staticmethod
    def add_frac(network: FractureNetwork, p0, p1, lave, *, data=None):
        warnings.warn(
            'FracAlg.add_frac will be removed after 2026-2-11, '
            'use FractureNetwork.add_fracture instead',
            DeprecationWarning, stacklevel=2)
        return network.add_fracture(first=p0, second=p1, lave=lave, data=data)

    @staticmethod
    def extend_tip(network: FractureNetwork, *args, **kwargs):
        warnings.warn(
            'FracAlg.extend_tip will be removed after 2026-2-11, '
            'use FractureNetwork.extend_tip instead',
            DeprecationWarning, stacklevel=2)
        return network.extend_tip(*args, **kwargs)

    @staticmethod
    def get_induced(network: FractureNetwork, fa_xy, fa_yy, matrix):
        warnings.warn(
            'FracAlg.get_induced will be removed after 2026-2-11, '
            'use FractureNetwork.get_induced instead',
            DeprecationWarning, stacklevel=2)
        return network.get_induced(fa_xy=fa_xy, fa_yy=fa_yy, matrix=matrix)

    core.use(None, 'frac_alg_update_topology',
             c_void_p,
             c_void_p, c_size_t, c_double, c_double,
             c_size_t, c_size_t, c_size_t)

    @staticmethod
    def update_topology(seepage: Seepage, network: FractureNetwork, *,
                        layer_n=1, z_min=-1, z_max=1,
                        ca_area=IDX_INF, fa_width=IDX_INF,
                        fa_dist=IDX_INF):
        """
        更新seepage的结构，
            对于新添加的Cell，设置位置(cell.pos)和面积(ca_area)属性
            对于新添加的Face，设置宽度(fa_width)和长度(fa_dist)属性
        注意：
            这里假设network有layer_n层的cell组成，并基于此来更新seepage的结构.

        Args:
            seepage (Seepage): 渗流对象。
            network (FractureNetwork): 裂缝网络对象。
            layer_n (int, optional): 层数，默认为1。
            z_min (float, optional): 最小z坐标，默认为-1。
            z_max (float, optional): 最大z坐标，默认为1。
            ca_area (float, optional): 单元面积，默认为INT_INF。
            fa_width (float, optional): 面的宽度，默认为INT_INF。
            fa_dist (float, optional): 面的长度，默认为INT_INF。

        Raises:
            AssertionError: 如果 seepage 不是 Seepage 类型，或者 network
            不是 FractureNetwork 类型。
        """
        assert isinstance(seepage, Seepage)
        assert isinstance(network, FractureNetwork)
        core.frac_alg_update_topology(seepage.handle, network.handle,
                                      layer_n,
                                      z_min, z_max,
                                      ca_area, fa_width, fa_dist)
