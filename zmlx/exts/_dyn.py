import ctypes
from ctypes import c_void_p, c_char_p, c_double, c_size_t, c_int
from typing import Optional, Iterable

from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._fmap import FileMap
from zmlx.exts._lexpr import LinearExpr
from zmlx.exts._mesh import Mesh3
from zmlx.exts._sol import ConjugateGradientSolver
from zmlx.exts._utils import (
    HasHandle, Iterator, Object, attr_in_range, f64_ptr, const_f64_ptr, get_index, log, make_parent, check_ipath
)
from zmlx.exts._vec import Vector


class DynSys(HasHandle):
    """
    质量-弹性动力学系统。用以实现固体计算的模型。对于任何固体的变形及运动问题，
    都可以归结为两个概念，即质量和弹性。对于任何一个自由度，
    都可以定义“质量”和“位置”。

    由于整个体系是线性的，因此，某个自由度的“受力”一定是一个或者多个自由度“位置”的线性函数，即
        f = ax + b                                                       (1)
    其中f代表各个自由度的“受力”，x代表各个自由度的“位置”，f和x均为N阶向量，
    其中N为自由度的数量。
    a是一个N*N的稀疏矩阵，b为一个长度为N的常向量。

    同时，在给定时间步长dt之后，一个自由度在dt之后的“位置”，也是dt之后“受力”的线性函数。
    根据牛顿第二定律，有
        x=x0 + v0*dt + 0.5*(f/m)*dt*dt                                   (2)
    整理可得:
        x = cf + d                                                       (3)
    其中 c=0.5*dt*dt/m, d=x0 + v0*dt. 其中m为各个自由度的质量，
    x0为上一次更新之后的各个自由度的位置, v0为各个自由度的速度. 其中
    m, x0, v0均为长度为N的向量.

    以上方程(1)和(3)构成了以向量x和向量f为未知量的N阶的线性方程组，
    求解之后，即可得到t0+dt时刻之后，整个体系各个自由度的“位置”向量x和
    “受力”向量f，并进一步得到各个自由度的速度v.

    以上步骤完成一次迭代。
    """
    core.use(c_void_p, 'new_dynsys')
    core.use(None, 'del_dynsys', c_void_p)

    def __init__(self, path: Optional[str] = None, handle: Optional[c_void_p] = None):
        """
        初始化动力学系统。

        Args:
            path (str, optional): 序列化文件路径，若存在则从文件加载
            handle: 已存在的底层对象句柄

        Raises:
            FileNotFoundError: 当指定path但文件不存在时抛出
        """
        super().__init__(handle, core.new_dynsys, core.del_dynsys)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
        self.solver = None
        try:
            name = type(self).__name__
            log(f'{name} created', tag=f'{name}_Init')
        except:
            pass

    def get_sol(self) -> 'ConjugateGradientSolver':
        if not isinstance(self.solver, ConjugateGradientSolver):
            self.solver = ConjugateGradientSolver(tolerance=1.0e-20)
        return self.solver

    def __repr__(self) -> str:
        """
        返回系统的详细字符串表示。

        Returns:
            str: 包含系统信息的详细字符串
        """
        return f'{type(self).__name__}(handle={int(self.handle)}, size={self.size})'

    def __str__(self) -> str:
        """
        返回系统的字符串表示。
        Returns:
            str: 包含系统信息的字符串
        """
        return f'{type(self).__name__}(size={self.size})'

    core.use(None, 'dynsys_save', c_void_p, c_char_p)

    def save(self, path: str):
        """
        序列化保存系统状态到文件。

        Args:
            path (str): 文件保存路径，支持格式：
                - .txt: 跨平台文本格式（不可读）
                - .xml: 可读XML格式（体积大）
                - 其他: 高效二进制格式（平台相关）

        Note:
            自动创建父目录，会覆盖已存在的文件
        """
        if isinstance(path, str):
            make_parent(path)
            core.dynsys_save(self.handle, make_c_char_p(path))

    core.use(None, 'dynsys_load', c_void_p, c_char_p)

    def load(self, path: str):
        """
        从文件加载系统状态。

        Args:
            path (str): 序列化文件路径

        Raises:
            ValueError: 文件格式不匹配时抛出
            RuntimeError: 数据加载失败时抛出
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.dynsys_load(self.handle, make_c_char_p(path))

    core.use(None, 'dynsys_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'dynsys_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt: str = 'binary') -> FileMap:
        """
        序列化到文件映射对象。

        Args:
            fmt (str): 序列化格式，可选 'text', 'xml', 'binary'

        Returns:
            FileMap: 包含序列化数据的文件映射
        """
        fmap = FileMap()
        core.dynsys_write_fmap(
            self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt: str = 'binary'):
        """
        从文件映射加载数据。

        Args:
            fmap (FileMap): 包含序列化数据的文件映射
            fmt (str): 数据格式，需与写入时一致

        Raises:
            TypeError: 当fmap参数类型错误时抛出
        """
        assert isinstance(fmap, FileMap)
        core.dynsys_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self) -> FileMap:
        """
        文件映射属性（二进制格式序列化）。

        Getter返回FileMap对象，Setter从FileMap加载数据
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: FileMap):
        self.from_fmap(value, fmt='binary')

    core.use(c_int, 'dynsys_iterate', c_void_p, c_double, c_void_p)

    def iterate(self, dt: float, solver: Optional['ConjugateGradientSolver'] = None) -> int:
        """
        执行单次时间步长迭代。

        Args:
            dt (float): 时间步长（秒）
            solver: 线性方程组求解器实例

        Returns:
            int: 迭代状态码（0表示成功）

        Note:
            需要有效的求解器来处理线性方程组
        """
        if not isinstance(solver, ConjugateGradientSolver):
            solver = self.get_sol()
            assert isinstance(solver, ConjugateGradientSolver)
        return core.dynsys_iterate(self.handle, dt, solver.handle)

    core.use(c_size_t, 'dynsys_size', c_void_p)

    @property
    def size(self) -> int:
        """
        系统的自由度数量（读写属性）。

        例如：
            3节点三角形网格每个节点2个自由度 → size=6
            2个共享边的三角形网格 → size=8
        """
        return core.dynsys_size(self.handle)

    core.use(None, 'dynsys_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value: int):
        core.dynsys_resize(self.handle, value)

    core.use(c_double, 'dynsys_get_pos', c_void_p, c_size_t)

    def get_pos(self, index: int) -> Optional[float]:
        """
        获取指定自由度的当前位置。

        Args:
            index (int): 自由度索引（0 <= idx < size）

        Returns:
            float: 当前位置值
        """
        idx_ = get_index(index, self.size)
        if idx_ is not None:
            return core.dynsys_get_pos(self.handle, idx_)
        else:
            return None

    core.use(None, 'dynsys_set_pos', c_void_p, c_size_t, c_double)

    def set_pos(self, index: int, value: float):
        """
        设置指定自由度的位置。

        Args:
            index (int): 自由度索引（0 <= idx < size）
            value (float): 新位置值
        """
        idx_ = get_index(index, self.size)
        if idx_ is not None:
            core.dynsys_set_pos(self.handle, idx_, value)

    core.use(None, 'dynsys_write_pos', c_void_p, c_void_p)

    def write_pos(self, pointer):
        """
        批量写入pos
        """
        core.dynsys_write_pos(self.handle, f64_ptr(pointer))

    core.use(None, 'dynsys_read_pos', c_void_p, c_void_p)

    def read_pos(self, pointer):
        """
        批量读取pos
        """
        core.seepage_cells_read(self.handle, const_f64_ptr(pointer))

    core.use(c_double, 'dynsys_get_vel', c_void_p, c_size_t)

    def get_vel(self, index):
        """
        获取指定自由度的当前速度。

        Args:
            index (int): 自由度索引（0 <= idx < size）

        Returns:
            float: 当前速度值
        """
        idx_ = get_index(index, self.size)
        if idx_ is not None:
            return core.dynsys_get_vel(self.handle, idx_)
        else:
            return None

    core.use(None, 'dynsys_set_vel', c_void_p, c_size_t, c_double)

    def set_vel(self, index, value):
        """
        设置指定自由度的速度。

        Args:
            index (int): 自由度索引（0 <= idx < size）
            value (float): 新速度值
        """
        idx_ = get_index(index, self.size)
        if idx_ is not None:
            core.dynsys_set_vel(self.handle, idx_, value)

    core.use(None, 'dynsys_write_vel', c_void_p, c_void_p)

    def write_vel(self, pointer):
        """
        批量写入vel
        """
        core.dynsys_write_vel(self.handle, f64_ptr(pointer))

    core.use(None, 'dynsys_read_vel', c_void_p, c_void_p)

    def read_vel(self, pointer):
        """
        批量读取vel
        """
        core.seepage_cells_read(self.handle, const_f64_ptr(pointer))

    core.use(c_double, 'dynsys_get_mass', c_void_p, c_size_t)

    def get_mass(self, index: int) -> Optional[float]:
        """
        获取指定自由度的质量。

        Args:
            index (int): 自由度索引（0 <= idx < size）

        Returns:
            float: 质量值
        """
        idx_ = get_index(index, self.size)
        if idx_ is not None:
            return core.dynsys_get_mass(self.handle, idx_)
        else:
            return None

    core.use(None, 'dynsys_set_mass', c_void_p, c_size_t, c_double)

    def set_mass(self, index: int, value: float):
        """
        设置指定自由度的质量。

        Args:
            index (int): 自由度索引（0 <= idx < size）
            value (float): 新质量值
        """
        idx_ = get_index(index, self.size)
        if idx_ is not None:
            core.dynsys_set_mass(self.handle, idx_, value)

    get_mas = get_mass
    set_mas = set_mass

    core.use(None, 'dynsys_write_mass', c_void_p, c_void_p)

    def write_mass(self, pointer):
        """
        批量写入mass
        """
        core.dynsys_write_mass(self.handle, f64_ptr(pointer))

    core.use(None, 'dynsys_read_mass', c_void_p, c_void_p)

    def read_mass(self, pointer):
        """
        批量读取mass
        """
        core.seepage_cells_read(self.handle, const_f64_ptr(pointer))

    core.use(c_void_p, 'dynsys_get_p2f', c_void_p, c_size_t)

    def get_p2f(self, index: int) -> Optional[LinearExpr]:
        """
        获取位置到受力的线性关系表达式。

        Args:
            index (int): 自由度索引（0 <= idx < size）

        Returns:
            LinearExpr: 描述受力与位置关系的线性表达式
        """
        idx_ = get_index(index, self.size)
        if idx_ is not None:
            handle = core.dynsys_get_p2f(self.handle, idx_)
            if handle:
                return LinearExpr(handle=handle)
            else:
                return None
        else:
            return None

    core.use(None, 'dynsys_write_p2f_c', c_void_p, c_void_p)

    def write_p2f_c(self, pointer):
        """
        批量写入p2f的常数项
        """
        core.dynsys_write_p2f_c(self.handle, f64_ptr(pointer))

    core.use(None, 'dynsys_read_p2f_c', c_void_p, c_void_p)

    def read_p2f_c(self, pointer):
        """
        批量读取p2f的常数项
        """
        core.seepage_cells_read(self.handle, const_f64_ptr(pointer))

    core.use(c_double, 'dynsys_get_lexpr_value', c_void_p, c_void_p)

    def get_lexpr_value(self, lexpr: LinearExpr) -> float:
        """
        计算线性表达式在当前状态的取值。

        Args:
            lexpr (LinearExpr): 需要计算的线性表达式

        Returns:
            float: 表达式的当前计算值

        Example:
            用于计算应力、应变等派生量
        """
        assert isinstance(lexpr, LinearExpr)
        return core.dynsys_get_lexpr_value(self.handle, lexpr.handle)


class SpringSys(HasHandle):
    """
    质点弹簧系统模拟器，用于测试弹性体变形。

    Note:
        系统由以下组件构成：
        - Node: 具有质量、位置、速度的实际节点
        - VirtualNode: 由实际节点位置定义的虚拟位置
        - Spring: 连接两个VirtualNode的弹性元件
        - Damper: 连接两个实际Node的阻尼元件
    """

    class Node(Object):
        """
        具有质量、位置、速度属性的节点。是弹簧系统的基本概念，
        建模时需要将实体离散为一个个的node，将质量集中到这些node上。

        Args:
            model (SpringSys): 所属弹簧系统实例
            index (int): 节点索引（需满足 0 <= index < model.node_number）

        Raises:
            AssertionError: 当参数类型或索引范围不合法时抛出
        """

        def __init__(self, model, index):
            assert isinstance(model, SpringSys)
            assert isinstance(index, int)
            assert index < model.node_number
            self.model = model
            self.index = index

        core.use(c_double, 'springsys_get_node_pos',
                 c_void_p, c_size_t,
                 c_size_t)
        core.use(None, 'springsys_set_node_pos',
                 c_void_p, c_size_t, c_size_t,
                 c_double)

        @property
        def pos(self):
            """
            节点在三维空间的位置 <单位m>

            Returns:
                list[float]: 三维坐标列表 [x, y, z]
            """
            return [
                core.springsys_get_node_pos(self.model.handle, self.index, i)
                for i in range(3)]

        @pos.setter
        def pos(self, value):
            """
            节点在三维空间的位置 <单位m>

            Args:
                value (list[float]): 新的三维坐标 [x, y, z]

            Raises:
                AssertionError: 当输入维度不等于3时抛出
            """
            assert len(value) == 3
            for i in range(3):
                core.springsys_set_node_pos(self.model.handle, self.index, i,
                                            value[i])

        core.use(c_double, 'springsys_get_node_vel',
                 c_void_p, c_size_t,
                 c_size_t)
        core.use(None, 'springsys_set_node_vel',
                 c_void_p, c_size_t, c_size_t,
                 c_double)

        @property
        def vel(self):
            """
            节点的速度  <单位m/s>
            """
            return (
                core.springsys_get_node_vel(self.model.handle, self.index, 0),
                core.springsys_get_node_vel(self.model.handle, self.index, 1),
                core.springsys_get_node_vel(self.model.handle, self.index, 2))

        @vel.setter
        def vel(self, value):
            """
            节点的速度  <单位m/s>
            """
            assert len(value) == 3
            for i in range(3):
                core.springsys_set_node_vel(self.model.handle, self.index, i,
                                            value[i])

        core.use(c_double, 'springsys_get_node_force',
                 c_void_p, c_size_t,
                 c_size_t)
        core.use(None, 'springsys_set_node_force',
                 c_void_p, c_size_t, c_size_t,
                 c_double)

        @property
        def force(self):
            """
            在节点上施加的外部力  <单位N>
            """
            return (
                core.springsys_get_node_force(self.model.handle, self.index, 0),
                core.springsys_get_node_force(self.model.handle, self.index, 1),
                core.springsys_get_node_force(self.model.handle, self.index, 2))

        @force.setter
        def force(self, value):
            """
            在节点上施加的外部力  <单位N>
            """
            assert len(value) == 3
            for i in range(3):
                core.springsys_set_node_force(
                    self.model.handle, self.index, i, value[i])

        core.use(None, 'springsys_set_node_mass',
                 c_void_p, c_size_t, c_double)
        core.use(c_double, 'springsys_get_node_mass',
                 c_void_p, c_size_t)

        @property
        def mass(self):
            """
            节点的集中质量  <单位kg>
            """
            return core.springsys_get_node_mass(self.model.handle, self.index)

        @mass.setter
        def mass(self, value):
            """
            节点的集中质量  <单位kg>
            """
            core.springsys_set_node_mass(self.model.handle, self.index, value)

    class VirtualNode(Object):
        """
        虚拟节点类：其位置可以用实际的多个node的空间位置的线性组合来表示的虚拟位置。
        用以辅助建立Node之间的力的关系，不具有质量和速度的属性。
        虚拟节点的位置不会作为未知量参与到迭代中，因此增加虚拟节点的数量，
        不会明显降低计算的速度。

        Args:
            model (SpringSys): 所属弹簧系统实例
            index (int): 虚拟节点索引
                （需满足 0 <= index < model.virtual_node_number）

        Raises:
            AssertionError: 当参数类型或索引范围不合法时抛出
        """

        def __init__(self, model, index):
            assert isinstance(model, SpringSys)
            assert isinstance(index, int)
            assert index < model.virtual_node_number
            self.model = model
            self.index = index

        core.use(None, 'springsys_get_virtual_node',
                 c_void_p, c_size_t,
                 c_size_t, c_size_t)

        def __getitem__(self, idim):
            """
            获取指定维度的位置表达式

            Args:
                idim (int): 维度索引（0=x, 1=y, 2=z）

            Returns:
                LinearExpr: 对应维度的线性表达式
            """
            lexpr = LinearExpr()
            core.springsys_get_virtual_node(
                self.model.handle, self.index, idim, lexpr.handle)
            return lexpr

        core.use(None, 'springsys_set_virtual_node',
                 c_void_p, c_size_t,
                 c_size_t, c_size_t)

        def __setitem__(self, idim, lexpr):
            """
            设置指定维度的位置表达式

            Args:
                idim (int): 维度索引（0=x, 1=y, 2=z）
                lexpr (LinearExpr): 新的线性表达式

            Raises:
                AssertionError: 当lexpr类型错误时抛出
            """
            assert isinstance(lexpr, LinearExpr)
            core.springsys_set_virtual_node(
                self.model.handle, self.index, idim, lexpr.handle)

        @property
        def x(self):
            """x轴位置表达式（等效于self[0]）"""
            return self[0]

        @x.setter
        def x(self, value):
            """设置x轴位置表达式（等效于self[0] = value）"""
            self[0] = value

        @property
        def y(self):
            """y轴位置表达式（等效于self[1]）"""
            return self[1]

        @y.setter
        def y(self, value):
            """设置y轴位置表达式（等效于self[1] = value）"""
            self[1] = value

        @property
        def z(self):
            """z轴位置表达式（等效于self[2]）"""
            return self[2]

        @z.setter
        def z(self, value):
            """设置z轴位置表达式（等效于self[2] = value）"""
            self[2] = value

        core.use(c_double, 'springsys_get_virtual_node_pos',
                 c_void_p, c_size_t,
                 c_size_t)

        @property
        def pos(self):
            """
            获取虚拟节点当前计算位置。

            Returns:
                list[float]: 三维坐标 [x, y, z]，单位：米

            Note:
                该位置根据关联的实际节点实时计算得出
            """
            return [
                core.springsys_get_virtual_node_pos(
                    self.model.handle, self.index, i) for i in range(3)]

    class Spring(Object):
        """
        弹簧，用以连接两个virtual_node，在两者之间建立线性的弹性关系。
        注意，Spring只能用以连接两个virtual_node，
        不能连接在两个实际的node上。如果要用弹簧连接实际的node，
        则必须首先在实际node的位置建立virtual_node，然后
        连接相应的virtual_node。
        注意：两个虚拟节点之间，可以添加多个不同的弹簧，这些弹簧会同时发挥作用。

        Args:
            model (SpringSys): 所属弹簧系统实例
            index (int): 弹簧索引
                （需满足 0 <= index < model.spring_number）

        Note:
            - 只能连接VirtualNode，连接Node时会自动创建对应VirtualNode
            - 同一对虚拟节点可添加多个不同参数的弹簧
        """

        def __init__(self, model, index):
            assert isinstance(model, SpringSys)
            assert isinstance(index, int)
            assert index < model.spring_number
            self.model = model
            self.index = index

        core.use(None, 'springsys_set_spring_len0',
                 c_void_p, c_size_t,
                 c_double)
        core.use(c_double, 'springsys_get_spring_len0',
                 c_void_p, c_size_t)

        @property
        def len0(self):
            """
            获取/设置弹簧自然长度。

            Returns:
                float: 当前自然长度值，单位：米
            """
            return core.springsys_get_spring_len0(
                self.model.handle, self.index)

        @len0.setter
        def len0(self, value):
            """
            设置弹簧自然长度。

            Args:
                value (float): 新自然长度值，单位：米
            """
            core.springsys_set_spring_len0(
                self.model.handle, self.index, value)

        core.use(c_double, 'springsys_get_spring_tension',
                 c_void_p, c_size_t)

        @property
        def tension(self):
            """
            获取当前张力值。

            Returns:
                float: 瞬时张力值，单位：牛（N）

            Note:
                正值表示拉力，负值表示压力
            """
            return core.springsys_get_spring_tension(
                self.model.handle, self.index)

        core.use(None, 'springsys_set_spring_k',
                 c_void_p, c_size_t, c_double)
        core.use(c_double, 'springsys_get_spring_k',
                 c_void_p, c_size_t)

        @property
        def k(self):
            """
            获取/设置弹性系数。

            Returns:
                float: 当前弹性系数，单位：牛/米（N/m）
            """
            return core.springsys_get_spring_k(self.model.handle,
                                               self.index)

        @k.setter
        def k(self, value):
            """
            设置弹性系数。

            Args:
                value (float): 新弹性系数值，单位：牛/米（N/m）
            """
            core.springsys_set_spring_k(self.model.handle, self.index, value)

        core.use(c_size_t, 'springsys_get_spring_link_n',
                 c_void_p, c_size_t)
        core.use(c_size_t, 'springsys_get_spring_link',
                 c_void_p, c_size_t,
                 c_size_t)
        core.use(None, 'springsys_set_spring_link',
                 c_void_p, c_size_t,
                 c_size_t, c_size_t)

        @property
        def virtual_nodes(self):
            """
            获取/设置连接的虚拟节点对。

            Returns:
                tuple[VirtualNode, VirtualNode]: 当前连接的虚拟节点元组

            Note:
                设置时若传入Node对象，会自动转换为对应位置的VirtualNode
            """
            n = core.springsys_get_spring_link_n(
                self.model.handle, self.index)
            if n != 2:
                return None, None

            i0 = core.springsys_get_spring_link(
                self.model.handle, self.index, 0)
            i1 = core.springsys_get_spring_link(
                self.model.handle, self.index, 1)

            return (self.model.get_virtual_node(i0),
                    self.model.get_virtual_node(i1))

        @virtual_nodes.setter
        def virtual_nodes(self, value):
            assert len(value) == 2
            assert isinstance(value[0], SpringSys.VirtualNode)
            assert isinstance(value[1], SpringSys.VirtualNode)
            assert value[0].model.handle == self.model.handle
            assert value[1].model.handle == self.model.handle
            assert value[0].index != value[1].index
            core.springsys_set_spring_link(self.model.handle, self.index,
                                           value[0].index, value[1].index)

        @property
        def pos(self):
            """
            计算弹簧中心点空间坐标。

            Returns:
                tuple[float, float, float]|None: 三维坐标(x,y,z)元组，单位：米
                          当任一节点无效时返回None
            """
            virtual_nodes = self.virtual_nodes
            if len(virtual_nodes) == 2:
                if virtual_nodes[0] is not None and virtual_nodes[
                    1] is not None:
                    a = virtual_nodes[0].pos
                    b = virtual_nodes[1].pos
                    return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (
                            a[2] + b[2]) / 2
                else:
                    return None
            else:
                return None

        core.use(c_double, 'springsys_get_spring_attr',
                 c_void_p, c_size_t,
                 c_size_t)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取弹簧自定义属性值。

            Args:
                index (int): 自定义属性索引
                default_val: 默认返回值（当属性无效时）
                valid_range: 有效性范围校验（如min=0, max=100）

            Returns:
                float: 属性值或default_val（当值超出有效范围时）
            """
            if index is None:
                return default_val
            value = core.springsys_get_spring_attr(self.model.handle,
                                                   self.index, index)
            if attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        core.use(None, 'springsys_set_spring_attr',
                 c_void_p, c_size_t,
                 c_size_t, c_double)

        def set_attr(self, index, value):
            """
            设置弹簧自定义属性值。

            Args:
                index (int): 自定义属性索引
                value (float): 新属性值（设为None时重置为默认值1e200）

            Returns:
                Spring: 自身实例，支持链式调用
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.springsys_set_spring_attr(
                self.model.handle, self.index, index, value)
            return self

    class Damper(Object):
        """
        阻尼器元件，连接两个实际节点并施加粘性阻力。

        Args:
            model (SpringSys): 所属弹簧系统实例
            index (int): 阻尼器索引（需满足 0 <= index < model.damper_number）

        Raises:
            AssertionError: 当参数类型或索引范围不合法时抛出

        Note:
            - 只能连接实际节点(Node)，连接VirtualNode会导致断言失败
            - 阻尼力方向与节点相对速度方向相反
        """

        def __init__(self, model, index):
            assert isinstance(model, SpringSys)
            assert isinstance(index, int)
            assert index < model.damper_number
            self.model = model
            self.index = index

        core.use(None, 'springsys_set_damper_link',
                 c_void_p, c_size_t,
                 c_size_t, c_size_t)
        core.use(c_size_t, 'springsys_get_damper_link',
                 c_void_p, c_size_t,
                 c_size_t)
        core.use(c_size_t, 'springsys_get_damper_link_n',
                 c_void_p, c_size_t)

        @property
        def nodes(self):
            """
            获取/设置连接的实际节点对。

            Returns:
                tuple[Node, Node]|(None, None): 当前连接的节点元组，
                无效时返回(None, None)
            """
            n = core.springsys_get_damper_link_n(self.model.handle, self.index)
            if n != 2:
                return None, None

            i0 = core.springsys_get_damper_link(
                self.model.handle, self.index, 0)
            i1 = core.springsys_get_damper_link(
                self.model.handle, self.index, 1)

            return self.model.get_node(i0), self.model.get_node(i1)

        @nodes.setter
        def nodes(self, value):
            """
            设置连接的实际节点对。

            Args:
                value (tuple[Node, Node]): 包含两个Node实例的元组

            Raises:
                AssertionError: 当节点类型错误、属于不同系统或索引相同时抛出
            """
            assert len(value) == 2
            assert isinstance(value[0], SpringSys.Node)
            assert isinstance(value[1], SpringSys.Node)
            assert value[0].handle == self.model.handle
            assert value[1].handle == self.model.handle
            assert value[0].index != value[1].index
            core.springsys_set_damper_link(
                self.model.handle, self.index, value[0].index, value[1].index)

        core.use(None, 'springsys_set_damper_vis',
                 c_void_p, c_size_t, c_double)
        core.use(c_double, 'springsys_get_damper_vis',
                 c_void_p, c_size_t)

        @property
        def vis(self):
            """
            获取当前粘性阻尼系数。

            Returns:
                float: 阻尼系数值
            """
            return core.springsys_get_damper_vis(
                self.model.handle, self.index)

        @vis.setter
        def vis(self, value):
            """
            设置粘性阻尼系数。

            Args:
                value (float): 新阻尼系数值
            """
            core.springsys_set_damper_vis(
                self.model.handle, self.index, value)

    core.use(c_void_p, 'new_springsys')
    core.use(None, 'del_springsys', c_void_p)

    def __init__(self, path=None, handle=None):
        """
        初始化弹簧系统实例。

        Args:
            path (str, optional): 序列化文件路径，当handle为None时有效
            handle (c_void_p, optional): 已有系统句柄，用于包装已有对象

        Note:
            当handle为None时会创建新系统，若指定path参数则从文件加载
        """
        super().__init__(handle, core.new_springsys,
                         core.del_springsys)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
        try:
            name = type(self).__name__
            log(f'{name} created', tag=f'{name}_Init')
        except:
            pass

    def __repr__(self):
        return (
            f'{type(self).__name__}(handle={int(self.handle)}, '
            f'node_n={self.node_number}, '
            f'virtual_node_n={self.virtual_node_number}, '
            f'spring_n={self.spring_number})')

    @staticmethod
    def virtual_x(node):
        """
        创建x轴方向的位置线性表达式。

        Args:
            node (Node|VirtualNode): 实际或虚拟节点

        Returns:
            LinearExpr: x轴位置表达式
        """
        if isinstance(node, SpringSys.VirtualNode):
            return node.x
        if isinstance(node, SpringSys.Node):
            node = node.index
        return LinearExpr.create(node * 3 + 0)

    @staticmethod
    def virtual_y(node):
        """
        创建y轴方向的位置线性表达式。

        Args:
            node (Node|VirtualNode): 实际或虚拟节点

        Returns:
            LinearExpr: y轴位置表达式
        """
        if isinstance(node, SpringSys.VirtualNode):
            return node.y
        if isinstance(node, SpringSys.Node):
            node = node.index
        return LinearExpr.create(node * 3 + 1)

    @staticmethod
    def virtual_z(node):
        """
        创建z轴方向的位置线性表达式。

        Args:
            node (Node|VirtualNode): 实际或虚拟节点

        Returns:
            LinearExpr: z轴位置表达式
        """
        if isinstance(node, SpringSys.VirtualNode):
            return node.z
        if isinstance(node, SpringSys.Node):
            node = node.index
        return LinearExpr.create(node * 3 + 2)

    core.use(None, 'springsys_save',
             c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存系统状态到文件。

        Args:
            path (str): 保存路径，扩展名决定格式：
                - .txt: 跨平台文本格式（不可读）
                - .xml: 可读XML格式（体积大速度慢）
                - 其他: 二进制格式（最快最小，但跨平台不兼容）

        Note:
            自动创建父目录，二进制格式在Windows/Linux之间不兼容
        """
        if isinstance(path, str):
            assert isinstance(path, str)
            make_parent(path)
            core.springsys_save(self.handle, make_c_char_p(path))

    core.use(None, 'springsys_load',
             c_void_p, c_char_p)

    def load(self, path):
        """
        从文件加载序列化系统状态。

        Args:
            path (str): 文件路径，格式由扩展名决定（参考save方法说明）

        Note:
            加载前会验证文件路径有效性
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.springsys_load(self.handle, make_c_char_p(path))

    core.use(None, 'springsys_print_node_pos',
             c_void_p, c_char_p)

    def print_node_pos(self, path):
        """
        将节点坐标输出到指定文件。

        Args:
            path (str): 输出文件路径

        Note:
            文件格式为每行包含一个节点的x,y,z坐标，空格分隔
        """
        assert isinstance(path, str)
        core.springsys_print_node_pos(self.handle, make_c_char_p(path))

    def iterate(self, dt, dynsys, solver):
        """
        执行系统动力学迭代。

        Args:
            dt (float): 时间步长（单位：秒）
            dynsys (DynSys): 动态系统实例，用于存储状态变量
            solver (Solver): 微分方程求解器

        Note:
            迭代过程包含以下步骤：
            1、尝试创建DynSys(只有当DynSys的size不正确的时候才去更新)
            2、更新DynSys (借助给定的solver)
            3、从DynSys读取数据，更新弹簧各个Node的位置和速度
        """
        assert isinstance(dynsys, DynSys)
        if dynsys.size != self.node_number * 3:
            dynsys.size = self.node_number * 3
            self.export_p2f(dynsys)
        self.export_mas_pos_vel(dynsys)
        dynsys.iterate(dt, solver)
        self.update_pos_vel(dynsys)
        self.apply_dampers(dt)

    core.use(c_size_t, 'springsys_get_node_n',
             c_void_p)

    @property
    def node_number(self):
        """
        获取实际节点数量。

        Returns:
            int: 当前系统内实际节点总数
        """
        return core.springsys_get_node_n(self.handle)

    core.use(c_size_t, 'springsys_get_virtual_node_n',
             c_void_p)

    @property
    def virtual_node_number(self):
        """
        获取虚拟节点数量。

        Returns:
            int: 当前系统内虚拟节点总数
        """
        return core.springsys_get_virtual_node_n(self.handle)

    core.use(c_size_t, 'springsys_get_spring_n',
             c_void_p)

    @property
    def spring_number(self):
        """
        获取弹簧元件数量。

        Returns:
            int: 当前系统内弹簧总数
        """
        return core.springsys_get_spring_n(self.handle)

    core.use(c_size_t, 'springsys_get_damper_n',
             c_void_p)

    @property
    def damper_number(self):
        """
        获取阻尼器元件数量。

        Returns:
            int: 当前系统内阻尼器总数
        """
        return core.springsys_get_damper_n(self.handle)

    def get_node(self, index):
        """
        通过索引获取实际节点对象。

        Args:
            index (int): 节点索引（0 <= index < node_number）

        Returns:
            Node|None: 节点对象，索引无效时返回None
        """
        index = get_index(index, self.node_number)
        if index is not None:
            return SpringSys.Node(self, index)
        else:
            return None

    def get_virtual_node(self, index):
        """
        通过索引获取虚拟节点对象。

        Args:
            index (int): 虚拟节点索引（0 <= index < virtual_node_number）

        Returns:
            VirtualNode|None: 虚拟节点对象，索引无效时返回None
        """
        index = get_index(index, self.virtual_node_number)
        if index is not None:
            return SpringSys.VirtualNode(self, index)
        else:
            return None

    def get_spring(self, index):
        """
        通过索引获取弹簧对象。

        Args:
            index (int): 弹簧索引（0 <= index < spring_number）

        Returns:
            Spring|None: 弹簧对象，索引无效时返回None
        """
        index = get_index(index, self.spring_number)
        if index is not None:
            return SpringSys.Spring(self, index)
        else:
            return None

    def get_damper(self, index):
        """
        通过索引获取阻尼器对象。

        Args:
            index (int): 阻尼器索引（0 <= index < damper_number）

        Returns:
            Damper|None: 阻尼器对象，索引无效时返回None
        """
        index = get_index(index, self.damper_number)
        if index is not None:
            return SpringSys.Damper(self, index)
        else:
            return None

    @property
    def nodes(self) -> Iterable['SpringSys.Node']:
        """
        实际节点迭代器。

        Returns:
            Iterator[Node]: 遍历所有实际节点的迭代器
        """
        return Iterator(self, self.node_number,
                        lambda m, ind: m.get_node(ind))

    @property
    def virtual_nodes(self) -> Iterable['SpringSys.VirtualNode']:
        """
        虚拟节点迭代器。

        Returns:
            Iterator[VirtualNode]: 遍历所有虚拟节点的迭代器
        """
        return Iterator(self, self.virtual_node_number,
                        lambda m, ind: m.get_virtual_node(ind))

    @property
    def springs(self) -> Iterable['SpringSys.Spring']:
        """
        弹簧元件迭代器。

        Returns:
            Iterator[Spring]: 遍历所有弹簧的迭代器
        """
        return Iterator(self, self.spring_number,
                        lambda m, ind: m.get_spring(ind))

    @property
    def dampers(self) -> Iterable['SpringSys.Damper']:
        """
        阻尼器元件迭代器。

        Returns:
            Iterator[Damper]: 遍历所有阻尼器的迭代器
        """
        return Iterator(self, self.damper_number,
                        lambda m, ind: m.get_damper(ind))

    core.use(c_size_t, 'springsys_add_node',
             c_void_p)

    def add_node(self, pos=None, vel=None, force=None, mass=None):
        """
        创建新实际节点并设置初始参数。

        Args:
            pos (list[float], optional): 初始位置 [x,y,z]（单位：米）
            vel (list[float], optional): 初始速度 [vx,vy,vz]（单位：米/秒）
            force (list[float], optional): 初始受力 [fx,fy,fz]（单位：牛）
            mass (float, optional): 节点质量（单位：千克）

        Returns:
            Node: 新建节点实例
        """
        node = self.get_node(core.springsys_add_node(self.handle))
        if node is not None:
            if pos is not None:
                node.pos = pos
            if vel is not None:
                node.vel = vel
            if force is not None:
                node.force = force
            if mass is not None:
                node.mass = mass
        return node

    core.use(c_size_t, 'springsys_add_virtual_node',
             c_void_p)

    def add_virtual_node(self, node=None, x=None, y=None, z=None):
        """
        添加一个虚拟节点，并返回虚拟节点对象

        Args:
            node (Node, optional): 基于实际节点创建位置表达式
            x (LinearExpr, optional): 直接设置x轴表达式
            y (LinearExpr, optional): 直接设置y轴表达式
            z (LinearExpr, optional): 直接设置z轴表达式

        Returns:
            VirtualNode: 新建虚拟节点实例

        Note:
            添加一个虚拟节点，并返回虚拟节点对象。当给定参数node时，
            则在该node的位置创建一个虚拟节点。
            或者，给定x、y、z三个参数，则会分别对虚拟节点的x、y和z进行具体配置。
        """
        virtual_node = self.get_virtual_node(
            core.springsys_add_virtual_node(self.handle))
        if virtual_node is not None:
            if node is not None:
                assert isinstance(node, SpringSys.Node)
                virtual_node.x = SpringSys.virtual_x(node)
                virtual_node.y = SpringSys.virtual_y(node)
                virtual_node.z = SpringSys.virtual_z(node)
            if x is not None:
                assert isinstance(x, LinearExpr)
                virtual_node.x = x
            if y is not None:
                assert isinstance(y, LinearExpr)
                virtual_node.y = y
            if z is not None:
                assert isinstance(z, LinearExpr)
                virtual_node.z = z
        return virtual_node

    core.use(c_size_t, 'springsys_add_spring', c_void_p)

    def add_spring(self, virtual_nodes=None, len0=None, k=None):
        """
        创建并配置新弹簧元件。

        Args:
            virtual_nodes (tuple, optional): 连接的虚拟节点对，支持以下类型：
                - (VirtualNode, VirtualNode): 直接使用现有虚拟节点
                - (Node, Node): 自动转换为对应虚拟节点
            len0 (float, optional): 弹簧初始长度（单位：米），未设置时保留默认值
            k (float, optional): 刚度系数（单位：牛/米），未设置时保留默认值

        Returns:
            Spring: 新建弹簧实例

        Raises:
            AssertionError: 当节点类型不符合要求时抛出

        Note:
            当传入Node实例时会自动创建对应的虚拟节点
        """
        spring = self.get_spring(core.springsys_add_spring(self.handle))
        if spring is not None:
            if virtual_nodes is not None:
                assert len(virtual_nodes) == 2
                a = virtual_nodes[0]
                b = virtual_nodes[1]
                if isinstance(a, SpringSys.Node):
                    a = self.add_virtual_node(node=a)
                if isinstance(b, SpringSys.Node):
                    b = self.add_virtual_node(node=b)
                assert (isinstance(a, SpringSys.VirtualNode) and
                        isinstance(b, SpringSys.VirtualNode))
                spring.virtual_nodes = (a, b)
            if len0 is not None:
                spring.len0 = len0
            if k is not None:
                spring.k = k
        return spring

    core.use(c_size_t, 'springsys_add_damper',
             c_void_p)

    def add_damper(self, nodes=None, vis=None):
        """
        创建并配置新阻尼器元件。

        Args:
            nodes (tuple[Node, Node]): 连接的实际节点对
            vis (float, optional): 粘性阻尼系数（单位：牛/(米/秒)），
                未设置时保留默认值

        Returns:
            Damper: 新建阻尼器实例

        Raises:
            AssertionError: 当节点类型不符合要求时抛出

        Note:
            必须连接实际节点(Node)，连接虚拟节点会导致断言失败
        """
        damper = self.get_damper(core.springsys_add_damper(self.handle))
        if damper is not None:
            if nodes is not None:
                damper.nodes = nodes
            if vis is not None:
                damper.vis = vis
        return damper

    core.use(None, 'springsys_modify_vel',
             c_void_p, c_double)

    def modify_vel(self, scale):
        """
        全局调整节点运动速度。

        Args:
            scale (float): 速度缩放系数（范围：0.0-1.0）

        Note:
            将所有实际节点的速度向量乘以该系数，用于模拟能量耗散
        """
        core.springsys_modify_vel(self.handle, scale)

    core.use(None, 'springsys_get_pos',
             c_void_p, c_void_p, c_void_p, c_void_p)

    def get_pos(self, x=None, y=None, z=None):
        """
        获取所有实际节点的坐标数据。

        Args:
            x (Vector, optional): 用于存储x坐标的向量，未提供时自动创建
            y (Vector, optional): 用于存储y坐标的向量，未提供时自动创建
            z (Vector, optional): 用于存储z坐标的向量，未提供时自动创建

        Returns:
            tuple[Vector, Vector, Vector]: 包含x,y,z坐标向量的元组

        Note:
            返回向量长度等于节点数量，坐标单位：米
        """
        if not isinstance(x, Vector):
            x = Vector()
        if not isinstance(y, Vector):
            y = Vector()
        if not isinstance(z, Vector):
            z = Vector()
        core.springsys_get_pos(self.handle, x.handle, y.handle, z.handle)
        return x, y, z

    core.use(None, 'springsys_get_len',
             c_void_p, c_void_p)

    def get_len(self, buffer=None):
        """
        获取所有弹簧的当前长度。

        Args:
            buffer (Vector, optional): 用于存储长度的向量，未提供时自动创建

        Returns:
            Vector: 包含所有弹簧长度的向量，单位：米

        Note:
            向量索引与弹簧索引一一对应
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.springsys_get_len(self.handle, buffer.handle)
        return buffer

    core.use(None, 'springsys_get_k',
             c_void_p, c_void_p)

    def get_k(self, buffer=None):
        """
        获取所有弹簧的刚度系数。

        Args:
            buffer (Vector, optional): 用于存储刚度的向量，未提供时自动创建

        Returns:
            Vector: 包含所有弹簧刚度系数的向量，单位：牛/米
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.springsys_get_k(self.handle, buffer.handle)
        return buffer

    core.use(None, 'springsys_set_k',
             c_void_p, c_void_p)

    def set_k(self, k):
        """
        批量设置所有弹簧的刚度系数。

        Args:
            k (Vector): 包含新刚度系数的向量，长度必须等于弹簧数量

        Note:
            向量索引必须与弹簧索引严格对应
        """
        assert isinstance(k, Vector)
        core.springsys_set_k(self.handle, k.handle)

    core.use(None, 'springsys_get_len0',
             c_void_p, c_void_p)

    def get_len0(self, buffer=None):
        """
        获取所有弹簧的初始长度。

        Args:
            buffer (Vector, optional): 用于存储长度的向量，未提供时自动创建

        Returns:
            Vector: 包含所有弹簧初始长度的向量，单位：米

        Note:
            向量索引与弹簧索引一一对应
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.springsys_get_len0(self.handle, buffer.handle)
        return buffer

    core.use(None, 'springsys_set_len0',
             c_void_p, c_void_p)

    def set_len0(self, len0):
        """
        批量设置所有弹簧的初始长度。

        Args:
            len0 (Vector): 包含新初始长度的向量，长度必须等于弹簧数量

        Note:
            向量索引必须与弹簧索引严格对应
        """
        assert isinstance(len0, Vector)
        core.springsys_set_len0(self.handle, len0.handle)

    core.use(c_size_t, 'springsys_apply_k_reduction',
             c_void_p, c_size_t)

    def apply_k_reduction(self, sa_tmax):
        """
        根据张力阈值实施刚度折减。

        Args:
            sa_tmax (int): 弹簧自定义属性索引，代表最大承受张力（单位：牛）

        Returns:
            int: 发生刚度折减的弹簧数量

        Note:
            当弹簧张力超过该属性值时，刚度将调整为原值的1%
        """
        return core.springsys_apply_k_reduction(self.handle, sa_tmax)

    core.use(None, 'springsys_adjust_len0',
             c_void_p, c_size_t)

    def adjust_len0(self, sa_times):
        """
        根据属性值调整弹簧初始长度。

        Args:
            sa_times (int): 弹簧自定义属性索引，代表长度调整系数

        Note:
            - 仅当属性值在[0.5, 2.0]范围内时生效
            - 新长度 = 原长度 × 调整系数
            - 超出范围的调整系数会被自动忽略
        """
        core.springsys_adjust_len0(self.handle, sa_times)

    core.use(None, 'springsys_export_mas_pos_vel',
             c_void_p, c_void_p)

    def export_mas_pos_vel(self, dynsys):
        """
        导出节点物理量到动态系统。

        Args:
            dynsys (DynSys): 目标动态系统实例

        Note:
            导出数据包含：
            - 节点质量（单位：千克）
            - 节点位置（单位：米）
            - 节点速度（单位：米/秒）
            应在每个时间步开始时调用
        """
        core.springsys_export_mas_pos_vel(self.handle, dynsys.handle)

    core.use(None, 'springsys_export_p2f',
             c_void_p, c_void_p)

    def export_p2f(self, dynsys):
        """
        将弹簧系统的刚度矩阵导出到动态系统。

        Args:
            dynsys (DynSys): 目标动态系统实例，用于存储刚度矩阵

        Note:
            - 当系统发生显著变形时需要调用此方法
            - 更新动态系统的系数矩阵P和力向量F
            - 应在每个时间步开始前调用以确保矩阵最新
        """
        core.springsys_export_p2f(self.handle, dynsys.handle)

    core.use(None, 'springsys_update_pos_vel',
             c_void_p, c_void_p)

    def update_pos_vel(self, dynsys):
        """
        从动态系统读取数据更新节点位置和速度。

        Args:
            dynsys (DynSys): 动态系统实例，包含最新的状态变量

        Note:
            - 将动态系统中存储的位置和速度同步到所有实际节点
            - 应在每个时间步迭代完成后调用
        """
        core.springsys_update_pos_vel(self.handle, dynsys.handle)

    core.use(None, 'springsys_apply_dampers',
             c_void_p, c_double)

    def apply_dampers(self, dt):
        """
        应用阻尼器作用，计算粘性阻尼力并更新系统状态。

        Args:
            dt (float): 时间步长，单位：秒

        Note:
            - 根据阻尼器连接的节点速度差计算阻尼力
            - 阻尼力公式：F = vis * (v2 - v1)
            - 会直接修改节点的受力状态
        """
        core.springsys_apply_dampers(self.handle, dt)

    core.use(None, 'springsys_modify_pos',
             c_void_p, c_size_t, c_double,
             c_double)

    def modify_pos(self, idim, left, right):
        """
        约束节点在指定维度的坐标范围。

        Args:
            idim (int): 维度索引 (0=x, 1=y, 2=z)
            left (float): 最小允许坐标值，None表示无下限
            right (float): 最大允许坐标值，None表示无上限

        Note:
            - 当坐标超出范围时会被自动截断到边界值
            - 设置left=right可固定节点在该维度的坐标
            - 默认边界值为±1e100（近似无约束）
        """
        if left is None and right is None:
            return
        if left is None:
            left = -1e100
        if right is None:
            right = 1e100
        core.springsys_modify_pos(self.handle, idim, left, right)


class FemAlg:
    core.use(None, 'fem_alg_create2',
             c_void_p, c_void_p, c_void_p, c_size_t,
             c_size_t, c_size_t)

    @staticmethod
    def create2(mesh: Mesh3, fa_den, fa_h, face_stiffs: Vector):
        """
        创建二维的动力学模型。 其中mesh为网格.
        Args:
            mesh: 网格对象，其中主要用到的是Face的数据
            fa_den: 密度属性ID
            fa_h: 厚度属性ID
            face_stiffs: 所有face的刚度矩阵

        Returns:
            动力学系统对象
        """
        dyn = DynSys()
        core.fem_alg_create2(dyn.handle, mesh.handle,
                             ctypes.cast(face_stiffs.pointer, c_void_p),
                             face_stiffs.size,
                             fa_den, fa_h)
        return dyn

    core.use(None, 'fem_alg_add_strain2',
             c_void_p, c_void_p, c_void_p,
             c_size_t, c_size_t)

    @staticmethod
    def add_strain2(dyn, mesh, fa_strain, face_stiffs):
        assert isinstance(dyn, DynSys)
        assert isinstance(mesh, Mesh3)
        assert isinstance(face_stiffs, Vector)
        core.fem_alg_add_strain2(dyn.handle, mesh.handle,
                                 ctypes.cast(face_stiffs.pointer, c_void_p),
                                 face_stiffs.size, fa_strain)
