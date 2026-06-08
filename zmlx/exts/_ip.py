import warnings
from ctypes import c_double, c_void_p, c_size_t, c_bool, c_char_p, POINTER
from typing import Union

from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._utils import (
    HasHandle, Object, f64_ptr, const_f64_ptr, get_index, IDX_INF, log, make_parent, check_ipath, np
)
from zmlx.exts._vec import Vector


class InvasionPercolation(HasHandle):
    """
    IP模型计算模型。该模型定义了所有用于求解的数据以及方法。
    """

    class NodeData(Object):
        """
        IP模型中的节点，也对应于Pore(相应地，Bond类型也可以对应于throat)；
        Node为流体的存储空间。

        Attributes:
            handle (c_void_p): 节点的句柄。
        """

        def __init__(self, handle):
            """
            初始化节点数据

            Args:
                handle (c_void_p): 节点的句柄。
            """
            self.handle = handle

        def __eq__(self, rhs):
            """
            判断两个Node是否是同一个

            Args:
                rhs (NodeData): 要比较的另一个节点数据对象。

            Returns:
                bool: 如果两个节点的句柄相同，则返回True；否则返回False。
            """
            return self.handle == rhs.handle

        def __ne__(self, rhs):
            """
            判断两个Node是否不是同一个

            Args:
                rhs (NodeData): 要比较的另一个节点数据对象。

            Returns:
                bool: 如果两个节点的句柄不同，则返回True；否则返回False。
            """
            return not (self == rhs)

        def __str__(self):
            """
            返回节点数据的字符串表示

            Returns:
                str: 包含节点句柄、位置和半径的字符串。
            """
            return (f'zml.InvasionPercolation.NodeData('
                    f'handle = {int(self.handle)}, pos = {self.pos}, '
                    f'radi = {self.radi})')

        core.use(c_size_t, 'ip_node_get_phase',
                 c_void_p)
        core.use(None, 'ip_node_set_phase',
                 c_void_p, c_size_t)

        def get_phase(self):
            """
            获取此Node中流体的相态。相态用一个整数(>=0)来表示。

            Returns:
                int: 节点中流体的相态。
            """
            return core.ip_node_get_phase(self.handle)

        def set_phase(self, value):
            """
            设置此Node中流体的相态。相态用一个整数(>=0)来表示。

            Args:
                value (int): 要设置的相态，必须大于等于0。

            Raises:
                AssertionError: 如果提供的值小于0。
            """
            assert value >= 0
            core.ip_node_set_phase(self.handle, value)

        @property
        def phase(self):
            """
            获取或设置此Node中流体的相态。相态用一个整数(>=0)来表示。

            Returns:
                int: 节点中流体的相态。

            Raises:
                AssertionError: 如果设置的值小于0。
            """
            return self.get_phase()

        @phase.setter
        def phase(self, value):
            self.set_phase(value)

        core.use(c_size_t, 'ip_node_get_cid',
                 c_void_p)
        core.use(None, 'ip_node_set_cid',
                 c_void_p, c_size_t)

        def get_cid(self):
            """
            获取Node所在的cluster的ID (从0开始编号)。程序会将各个Node，
            根据流体的phase和相互的连接关系，划分成为一个个cluster。
            每一个cluster都是一个流体相态一样，且相互联通的一系列Node。

            Returns:
                int: 节点所在的cluster的ID。
            """
            return core.ip_node_get_cid(self.handle)

        def set_cid(self, value):
            """
            设置Node所在的cluster的ID （注意：此函数仅供作者测试，
            且随时都可能被移除。在任何情况下，此函数都不应被调用）

            Args:
                value (int): 要设置的cluster的ID。
            """
            core.ip_node_set_cid(self.handle, value)

        @property
        def cid(self):
            """
            获取或设置Node所在的cluster的ID (从0开始编号)。

            Returns:
                int: 节点所在的cluster的ID。
            """
            return self.get_cid()

        @cid.setter
        def cid(self, value):
            self.set_cid(value)

        core.use(c_double, 'ip_node_get_radi',
                 c_void_p)
        core.use(None, 'ip_node_set_radi',
                 c_void_p, c_double)

        def get_radi(self):
            """
            获取此Node内孔隙的半径（单位：米）。
            这个内部半径主要用来计算流体侵入到该Node所必须克服的毛管压力。

            Returns:
                float: 节点内孔隙的半径。
            """
            return core.ip_node_get_radi(self.handle)

        def set_radi(self, value):
            """
            设置此Node内孔隙的半径（单位：米）。
            这个内部半径主要用来计算流体侵入到该Node所必须克服的毛管压力。

            Args:
                value (float): 要设置的半径，必须大于0。

            Raises:
                AssertionError: 如果提供的值小于等于0。
            """
            assert value > 0
            core.ip_node_set_radi(self.handle, value)

        @property
        def radi(self):
            """
            获取或设置此Node内孔隙的半径（单位：米）。

            Returns:
                float: 节点内孔隙的半径。

            Raises:
                AssertionError: 如果设置的值小于等于0。
            """
            return self.get_radi()

        @radi.setter
        def radi(self, value):
            self.set_radi(value)

        core.use(c_double, 'ip_node_get_time_invaded',
                 c_void_p)

        @property
        def time_invaded(self):
            """
            获取最后一个set_phase的时间

            Returns:
                float: 最后一个set_phase的时间。
            """
            return core.ip_node_get_time_invaded(self.handle)

        @property
        def time(self):
            """
            获取最后一个set_phase的时间

            Returns:
                float: 最后一个set_phase的时间。
            """
            return self.time_invaded

        core.use(c_double, 'ip_node_get_rate_invaded',
                 c_void_p)

        @property
        def rate_invaded(self):
            """
            获取节点的侵入速率

            Returns:
                float: 节点的侵入速率。
            """
            return core.ip_node_get_rate_invaded(self.handle)

        core.use(c_double, 'ip_node_get_pos',
                 c_void_p, c_size_t)
        core.use(None, 'ip_node_set_pos',
                 c_void_p, c_size_t, c_double)

        def get_pos(self):
            """
            获取此Node在三维空间的位置

            Returns:
                list: 包含节点在三维空间位置的列表。
            """
            return [core.ip_node_get_pos(self.handle, i) for i in range(3)]

        def set_pos(self, value):
            """
            设置此Node在三维空间的位置

            Args:
                value (list): 要设置的位置，列表长度必须大于等于3。

            Raises:
                AssertionError: 如果提供的列表长度小于3。
            """
            assert len(value) >= 3
            for i in range(3):
                core.ip_node_set_pos(self.handle, i, value[i])

        @property
        def pos(self):
            """
            获取或设置此Node在三维空间的位置

            Returns:
                list: 包含节点在三维空间位置的列表。

            Raises:
                AssertionError: 如果设置的列表长度小于3。
            """
            return self.get_pos()

        @pos.setter
        def pos(self, value):
            self.set_pos(value)

    class Node(NodeData):
        """
        IP模型中的节点，继承自NodeData。

        Attributes:
            model (InvasionPercolation): 所属的IP模型。
            index (int): 节点的索引。
        """

        core.use(c_void_p, 'ip_get_node',
                 c_void_p, c_size_t)

        def __init__(self, model, index):
            """
            初始化节点

            Args:
                model (InvasionPercolation): 所属的IP模型。
                index (int): 节点的索引。
            """
            super().__init__(
                handle=core.ip_get_node(model.handle, index))
            self.model = model
            self.index = index

        core.use(c_size_t, 'ip_get_node_bond_n',
                 c_void_p, c_size_t)

        @property
        def bond_n(self):
            """
            获取此Node连接的Bond的数量

            Returns:
                int: 节点连接的Bond的数量。
            """
            return core.ip_get_node_bond_n(self.model.handle, self.index)

        @property
        def node_n(self):
            """
            获取此Node连接的Node的数量

            Returns:
                int: 节点连接的Node的数量。
            """
            return self.bond_n

        core.use(c_size_t, 'ip_get_node_node_id',
                 c_void_p, c_size_t, c_size_t)

        def get_node(self, index):
            """
            获取此Node连接的第idx个Node

            Args:
                index (int): 要获取的相邻节点的索引。

            Returns:
                Node: 第index个相邻节点，如果索引有效；否则返回None。
            """
            index = get_index(index, self.node_n)
            if index is not None:
                i_node = core.ip_get_node_node_id(self.model.handle, self.index,
                                                  index)
                return self.model.get_node(i_node)
            else:
                return None

        core.use(c_size_t, 'ip_get_node_bond_id',
                 c_void_p, c_size_t, c_size_t)

        def get_bond(self, index):
            """
            获取此Node连接的第idx个Bond

            Args:
                index (int): 要获取的相邻Bond的索引。

            Returns:
                Bond: 第idx个相邻Bond，如果索引有效；否则返回None。
            """
            index = get_index(index, self.bond_n)
            if index is not None:
                i_bond = core.ip_get_node_bond_id(self.model.handle, self.index,
                                                  index)
                return self.model.get_bond(i_bond)
            else:
                return None

    class BondData(Object):
        """
        在IP模型中，连接两个Node的流体流动通道。

        Attributes:
            handle (c_void_p): 通道的句柄。
        """

        def __init__(self, handle):
            """
            初始化通道数据

            Args:
                handle (c_void_p): 通道的句柄。
            """
            self.handle = handle

        def __eq__(self, rhs):
            """
            判断两个Bond是否为同一个

            Args:
                rhs (BondData): 要比较的另一个通道数据对象。

            Returns:
                bool: 如果两个通道的句柄相同，则返回True；否则返回False。
            """
            return self.handle == rhs.handle

        def __ne__(self, rhs):
            """
            判断两个Bond是否不是同一个

            Args:
                rhs (BondData): 要比较的另一个通道数据对象。

            Returns:
                bool: 如果两个通道的句柄不同，则返回True；否则返回False。
            """
            return not (self == rhs)

        def __str__(self):
            """
            返回通道数据的字符串表示

            Returns:
                str: 包含通道句柄和半径的字符串。
            """
            return (f'zml.InvasionPercolation.Bond('
                    f'handle = {int(self.handle)}, '
                    f'radi = {self.radi})')

        core.use(c_double, 'ip_bond_get_radi',
                 c_void_p)
        core.use(None, 'ip_bond_set_radi',
                 c_void_p, c_double)

        def get_radi(self):
            """
            获取此Bond所在位置吼道的内部半径
            （主要用来计算流体界面通过这个Bond所必须克服的毛管压力）

            Returns:
                float: 通道所在位置吼道的内部半径。
            """
            return core.ip_bond_get_radi(self.handle)

        def set_radi(self, value):
            """
            设置此Bond所在位置吼道的内部半径
            （主要用来计算流体界面通过这个Bond所必须克服的毛管压力）

            Args:
                value (float): 要设置的半径，必须大于0。

            Raises:
                AssertionError: 如果提供的值小于等于0。
            """
            assert value > 0
            core.ip_bond_set_radi(self.handle, value)

        @property
        def radi(self):
            """
            获取或设置此Bond所在位置吼道的内部半径

            Returns:
                float: 通道所在位置吼道的内部半径。

            Raises:
                AssertionError: 如果设置的值小于等于0。
            """
            return self.get_radi()

        @radi.setter
        def radi(self, value):
            self.set_radi(value)

        core.use(c_double, 'ip_bond_get_dp0',
                 c_void_p)
        core.use(None, 'ip_bond_set_dp0',
                 c_void_p, c_double)

        def get_dp0(self):
            """
            获取此Bond左侧的流体侵入右侧时，在该Bond内必须克服的毛管阻力
            （注意：该属性仅供作者测试，请勿调用）

            Returns:
                float: 左侧流体侵入右侧时的毛管阻力。
            """
            return core.ip_bond_get_dp0(self.handle)

        def set_dp0(self, value):
            """
            设置此Bond左侧的流体侵入右侧时，在该Bond内必须克服的毛管阻力
            （注意：该属性仅供作者测试，请勿调用）

            Args:
                value (float): 要设置的毛管阻力。
            """
            core.ip_bond_set_dp0(self.handle, value)

        @property
        def dp0(self):
            """
            获取或设置此Bond左侧的流体侵入右侧时，在该Bond内必须克服的毛管阻力。

            Returns:
                float: 左侧流体侵入右侧时的毛管阻力。

            Note:
                该属性仅供作者测试，请勿调用。
            """
            return self.get_dp0()

        @dp0.setter
        def dp0(self, value):
            self.set_dp0(value)

        core.use(c_double, 'ip_bond_get_dp1',
                 c_void_p)
        core.use(None, 'ip_bond_set_dp1',
                 c_void_p, c_double)

        def get_dp1(self):
            """
            获取此Bond右侧的流体侵入左侧时，在该Bond内必须克服的毛管阻力
            （注意：该属性仅供作者测试，请勿调用）

            Returns:
                float: 右侧流体侵入左侧时的毛管阻力。
            """
            return core.ip_bond_get_dp1(self.handle)

        def set_dp1(self, value):
            """
            设置此Bond右侧的流体侵入左侧时，在该Bond内必须克服的毛管阻力
            （注意：该属性仅供作者测试，请勿调用）

            Args:
                value (float): 要设置的毛管阻力。
            """
            core.ip_bond_set_dp1(self.handle, value)

        @property
        def dp1(self):
            """
            获取或设置此Bond右侧的流体侵入左侧时，在该Bond内必须克服的毛管阻力。

            Returns:
                float: 右侧流体侵入左侧时的毛管阻力。

            Note:
                该属性仅供作者测试，请勿调用。
            """
            return self.get_dp1()

        @dp1.setter
        def dp1(self, value):
            self.set_dp1(value)

        core.use(c_double, 'ip_bond_get_contact_angle',
                 c_void_p, c_size_t,
                 c_size_t)

        def get_contact_angle(self, ph0, ph1):
            """
            获取当ph0驱替ph1的时候，在ph0中的接触角。
            当此处的值设置位0到PI之间时，将覆盖全局的设置

            Args:
                ph0 (int): 驱替流体的相态，必须大于等于0。
                ph1 (int): 被驱替流体的相态，必须大于等于0且不等于ph0。

            Returns:
                float: 接触角。

            Raises:
                AssertionError: 如果ph0或ph1小于0，或者ph0等于ph1。
            """
            assert 0 <= ph0 != ph1 >= 0
            return core.ip_bond_get_contact_angle(self.handle, ph0, ph1)

        core.use(None, 'ip_bond_set_contact_angle',
                 c_void_p, c_size_t,
                 c_size_t, c_double)

        def set_contact_angle(self, ph0, ph1, value):
            """
            设置当ph0驱替ph1的时候，在ph0中的接触角。
            当此处的值设置位0到PI之间时，将覆盖全局的设置

            Args:
                ph0 (int): 驱替流体的相态，必须大于等于0。
                ph1 (int): 被驱替流体的相态，必须大于等于0且不等于ph0。
                value (float): 要设置的接触角。

            Raises:
                AssertionError: 如果ph0或ph1小于0，或者ph0等于ph1。
            """
            assert 0 <= ph0 != ph1 >= 0
            core.ip_bond_set_contact_angle(self.handle, ph0, ph1, value)

        core.use(c_double, 'ip_bond_get_tension',
                 c_void_p, c_size_t, c_size_t)

        def get_tension(self, ph0, ph1):
            """
            获取流体ph0和ph1之间的表面张力，当值大于0时，将覆盖全局的参数

            Args:
                ph0 (int): 第一种流体的相态，必须大于等于0。
                ph1 (int): 第二种流体的相态，必须大于等于0且不等于ph0。

            Returns:
                float: 表面张力。

            Raises:
                AssertionError: 如果ph0或ph1小于0，或者ph0等于ph1。
            """
            assert 0 <= ph0 != ph1 >= 0
            return core.ip_bond_get_tension(self.handle, ph0, ph1)

        core.use(None, 'ip_bond_set_tension',
                 c_void_p, c_size_t, c_size_t,
                 c_double)

        def set_tension(self, ph0, ph1, value):
            """
            设置流体ph0和ph1之间的表面张力，当值大于0时，将覆盖全局的参数

            Args:
                ph0 (int): 第一种流体的相态，必须大于等于0。
                ph1 (int): 第二种流体的相态，必须大于等于0且不等于ph0。
                value (float): 要设置的表面张力，必须大于等于0。

            Raises:
                AssertionError: 如果ph0或ph1小于0，或者ph0等于ph1，或者value小于0。
            """
            assert 0 <= ph0 != ph1 >= 0
            assert value >= 0
            core.ip_bond_set_tension(self.handle, ph0, ph1, value)

        @property
        def tension(self):
            """
            获取或设置界面张力

            Returns:
                float: 界面张力。

            Raises:
                AssertionError: 如果设置的值小于0。
            """
            return self.get_tension(0, 1)

        @tension.setter
        def tension(self, value):
            assert value >= 0
            self.set_tension(0, 1, value)

        @property
        def ca0(self):
            """
            获取或设置当流体0驱替流体1的时候，在流体0中的接触角度

            Returns:
                float: 接触角度。
            """
            return self.get_contact_angle(0, 1)

        @ca0.setter
        def ca0(self, value):
            self.set_contact_angle(0, 1, value)

        @property
        def ca1(self):
            """
            获取或设置当流体1驱替流体0的时候，在流体1中的接触角度

            Returns:
                float: 接触角度。
            """
            return self.get_contact_angle(1, 0)

        @ca1.setter
        def ca1(self, value):
            self.set_contact_angle(1, 0, value)

    class Bond(BondData):
        """
        IP模型中的通道，继承自BondData。

        Attributes:
            model (InvasionPercolation): 所属的IP模型。
            index (int): 通道的索引。
        """

        core.use(c_void_p, 'ip_get_bond',
                 c_void_p, c_size_t)

        def __init__(self, model, index):
            """
            初始化通道

            Args:
                model (InvasionPercolation): 所属的IP模型。
                index (int): 通道的索引。
            """
            super().__init__(
                handle=core.ip_get_bond(model.handle, index))
            self.model = model
            self.index = index

        @property
        def node_n(self):
            """
            获取此Bond连接的Node的数量

            Returns:
                int: 通道连接的Node的数量，固定为2。
            """
            return 2

        core.use(c_size_t, 'ip_get_bond_node_id',
                 c_void_p, c_size_t, c_size_t)

        def get_node(self, index):
            """
            获取此Bond连接的第idx个Node

            Args:
                index (int): 要获取的相邻节点的索引。

            Returns:
                Node: 第idx个相邻节点，如果索引有效；否则返回None。
            """
            index = get_index(index, self.node_n)
            if index is not None:
                i_node = core.ip_get_bond_node_id(
                    self.model.handle, self.index, index)
                return self.model.get_node(i_node)
            else:
                return None

    class InjectorData(Object):
        """
        代表一个注入点。注意：一个注入点必须依赖于一个Node，即流体只能注入到Node里面。
        所以，注入点必须设置其作用的Node。

        Attributes:
            handle (c_void_p): 注入点的句柄。
        """

        def __init__(self, handle):
            """
            初始化注入点数据

            Args:
                handle (c_void_p): 注入点的句柄。
            """
            self.handle = handle

        def __eq__(self, rhs):
            """
            判断两个注入点是否为同一个

            Args:
                rhs (InjectorData): 要比较的另一个注入点数据对象。

            Returns:
                bool: 如果两个注入点的句柄相同，则返回True；否则返回False。
            """
            return self.handle == rhs.handle

        def __ne__(self, rhs):
            """
            判断两个注入点是否不是同一个

            Args:
                rhs (InjectorData): 要比较的另一个注入点数据对象。

            Returns:
                bool: 如果两个注入点的句柄不同，则返回True；否则返回False。
            """
            return not (self == rhs)

        def __str__(self):
            """
            返回注入点数据的字符串表示

            Returns:
                str: 包含注入点句柄的字符串。
            """
            return f'zml.InvasionPercolation.Injector(handle = {int(self.handle)})'

        core.use(c_size_t, 'ip_inj_get_node_id', c_void_p)
        core.use(None, 'ip_inj_set_node_id',
                 c_void_p, c_size_t)

        def get_node_id(self):
            """
            获取注入点作用的Node的ID

            Returns:
                int: 注入点作用的Node的ID。
            """
            return core.ip_inj_get_node_id(self.handle)

        def set_node_id(self, value):
            """
            设置注入点作用的Node的ID

            Args:
                value (int): 要设置的Node的ID。
            """
            core.ip_inj_set_node_id(self.handle, value)

        @property
        def node_id(self):
            """
            获取或设置注入点作用的Node的ID

            Returns:
                int: 注入点作用的Node的ID。
            """
            return self.get_node_id()

        @node_id.setter
        def node_id(self, value):
            self.set_node_id(value)

        core.use(c_size_t, 'ip_inj_get_phase', c_void_p)

        def get_phase(self):
            """
            获取通过该注入点注入的流体的类型(整数，从0开始编号)

            Returns:
                int: 注入流体的类型。
            """
            return core.ip_inj_get_phase(self.handle)

        core.use(None, 'ip_inj_set_phase',
                 c_void_p, c_size_t)

        def set_phase(self, value):
            """
            设置通过该注入点注入的流体的类型(整数，从0开始编号)

            Args:
                value (int): 要设置的流体类型，必须大于等于0。

            Raises:
                AssertionError: 如果提供的值小于0。
            """
            assert value >= 0
            core.ip_inj_set_phase(self.handle, value)

        @property
        def phase(self):
            """
            获取或设置通过该注入点注入的流体的类型(整数，从0开始编号)

            Returns:
                int: 注入流体的类型。

            Raises:
                AssertionError: 如果设置的值小于0。
            """
            return self.get_phase()

        @phase.setter
        def phase(self, value):
            self.set_phase(value)

        core.use(c_double, 'ip_inj_get_q', c_void_p)

        def get_qinj(self):
            """
            获取通过该注入点注入流体的速度。单位为 n/time。
            其中n为invade的node的个数。即表示单位时间内invade的node的个数。取值 > 0

            Returns:
                float: 注入流体的速度。
            """
            return core.ip_inj_get_q(self.handle)

        core.use(None, 'ip_inj_set_q',
                 c_void_p, c_double)

        def set_qinj(self, value):
            """
            设置通过该注入点注入流体的速度。单位为 n/time。
            其中n为invade的node的个数。即表示单位时间内invade的node的个数。取值 > 0

            Args:
                value (float): 要设置的注入速度，必须大于0。

            Raises:
                AssertionError: 如果提供的值小于等于0。
            """
            assert value > 0
            core.ip_inj_set_q(self.handle, value)

        @property
        def qinj(self):
            """
            获取或设置通过该注入点注入流体的速度。

            Returns:
                float: 注入流体的速度。

            Raises:
                AssertionError: 如果设置的值小于等于0。
            """
            return self.get_qinj()

        @qinj.setter
        def qinj(self, value):
            self.set_qinj(value)

    class Injector(InjectorData):
        """
        IP模型中的注入点，继承自InjectorData。

        Attributes:
            model (InvasionPercolation): 所属的IP模型。
            index (int): 注入点的索引。
        """
        core.use(c_void_p, 'ip_get_inj',
                 c_void_p, c_size_t)

        def __init__(self, model, index):
            """
            初始化注入点

            Args:
                model (InvasionPercolation): 所属的IP模型。
                index (int): 注入点的索引。
            """
            super().__init__(
                handle=core.ip_get_inj(model.handle, index))
            self.model = model
            self.index = index

    class InvadeOperation(Object):
        """
        一个侵入操作。

        Attributes:
            model (InvasionPercolation): 所属的IP模型。
            index (int): 侵入操作的索引。
        """

        def __init__(self, model, index):
            """
            初始化侵入操作

            Args:
                model (InvasionPercolation): 所属的IP模型。
                index (int): 侵入操作的索引。
            """
            self.model = model
            self.index = index

        def __eq__(self, rhs):
            """
            判断两个侵入操作是否为同一个

            Args:
                rhs (InvadeOperation): 要比较的另一个侵入操作对象。

            Returns:
                bool: 如果两个侵入操作所属的模型句柄和索引都相同，
                    则返回True；否则返回False。
            """
            return (self.model.handle == rhs.model.handle
                    and self.index == rhs.index)

        def __ne__(self, rhs):
            """
            判断两个侵入操作是否不是同一个

            Args:
                rhs (InvadeOperation): 要比较的另一个侵入操作对象。

            Returns:
                bool: 如果两个侵入操作所属的模型句柄和索引不同，
                    则返回True；否则返回False。
            """
            return not (self == rhs)

        def __str__(self):
            """
            返回侵入操作的字符串表示

            Returns:
                str: 包含侵入操作索引的字符串。
            """
            return (f'zml.InvasionPercolation.InvadeOperation('
                    f'index = {self.index})')

        core.use(c_size_t, 'ip_get_oper_bond_id',
                 c_void_p, c_size_t)

        def get_bond(self):
            """
            获取侵入操作对应的Bond

            Returns:
                Bond: 侵入操作对应的Bond。
            """
            bond_id = core.ip_get_oper_bond_id(self.model.handle, self.index)
            return self.model.get_bond(bond_id)

        @property
        def bond(self):
            """
            获取侵入操作对应的Bond

            Returns:
                Bond: 侵入操作对应的Bond。
            """
            return self.get_bond()

        core.use(c_bool, 'ip_get_oper_dir',
                 c_void_p, c_size_t)

        @property
        def dir(self):
            """
            获取侵入操作的方向

            Returns:
                bool: 侵入操作的方向。
            """
            return core.ip_get_oper_dir(self.model.handle, self.index)

        def get_node(self, index):
            """
            当idx==0时，返回上游的node；否则，返回下游的node

            Args:
                index (int): 节点索引，必须为0或1。

            Returns:
                Node: 对应的节点，如果Bond存在；否则返回None。

            Raises:
                AssertionError: 如果idx不等于0且不等于1。
            """
            assert index == 0 or index == 1
            if not self.dir:
                index = 1 - index
            bond = self.bond
            if bond is not None:
                return bond.get_node(index)
            else:
                return None

    core.use(c_void_p, 'new_ip')
    core.use(None, 'del_ip', c_void_p)

    def __init__(self, handle=None):
        """
        新建一个IP模型。

        Args:
            handle (c_void_p, optional): 模型的句柄。如果提供，
                将使用该句柄初始化模型。默认为None。
        """
        super().__init__(handle, core.new_ip,
                         core.del_ip)
        try:
            name = type(self).__name__
            log(f'{name} created', tag=f'{name}_Init')
        except:
            pass

    def __eq__(self, rhs):
        """
        判断两个IP模型是否为同一个

        Args:
            rhs (InvasionPercolation): 要比较的另一个IP模型。

        Returns:
            bool: 如果两个模型的句柄相同，则返回True；否则返回False。
        """
        return self.handle == rhs.handle

    def __ne__(self, rhs):
        """
        判断两个IP模型是否不是同一个

        Args:
            rhs (InvasionPercolation): 要比较的另一个IP模型。

        Returns:
            bool: 如果两个模型的句柄不同，则返回True；否则返回False。
        """
        return not (self == rhs)

    def __repr__(self):
        return (f'{type(self).__name__}(handle={int(self.handle)}, '
                f'node_n={self.node_n}, bond_n={self.bond_n})')

    core.use(None, 'ip_save',
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
            path (str): 要保存的文件路径。

        Raises:
            AssertionError: 如果提供的路径不是字符串类型。
        """
        assert isinstance(path, str)
        make_parent(path)
        core.ip_save(self.handle, make_c_char_p(path))

    core.use(None, 'ip_load',
             c_void_p, c_char_p)

    def load(self, path):
        """
        读取序列化文件。根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 要加载的文件路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.ip_load(self.handle, make_c_char_p(path))

    core.use(None, 'ip_print_nodes',
             c_void_p, c_char_p)

    def print_nodes(self, path):
        """
        将node的数据打印到文件

        Args:
            path (str): 要打印到的文件路径。

        Raises:
            AssertionError: 如果提供的路径不是字符串类型。
        """
        assert isinstance(path, str)
        core.ip_print_nodes(self.handle, make_c_char_p(path))

    core.use(None, 'ip_iterate', c_void_p)

    def iterate(self):
        """
        向前迭代一步。这个模型求解所需要的全部操作。
        """
        core.ip_iterate(self.handle)

    core.use(c_double, 'ip_get_time', c_void_p)

    def get_time(self):
        """
        获取模型内部的时间。模型每充注一次，则时间time的增量为 1.0/max(qinj)。
        其中max(qinj)为所有的注入点中qinj的最大值。

        Returns:
            float: 模型内部的时间。
        """
        return core.ip_get_time(self.handle)

    core.use(None, 'ip_set_time',
             c_void_p, c_double)

    def set_time(self, value):
        """
        设置模型内部的时间

        Args:
            value (float): 要设置的时间，必须大于等于0。

        Raises:
            AssertionError: 如果提供的值小于0。
        """
        assert value >= 0
        core.ip_set_time(self.handle, value)

    @property
    def time(self):
        """
        获取或设置模型内部的时间。

        Returns:
            float: 模型内部的时间。

        Raises:
            AssertionError: 如果设置的值小于0。
        """
        return self.get_time()

    @time.setter
    def time(self, value):
        self.set_time(value)

    core.use(None, 'ip_clear_nodes_and_bonds', c_void_p)

    def clear_nodes_and_bonds(self):
        """
        清除模型内所有的node和bond。
        Returns:
            None
        """
        core.ip_clear_nodes_and_bonds(self.handle)

    core.use(c_size_t, 'ip_add_node', c_void_p)
    core.use(None, 'ip_add_nodes', c_void_p, c_size_t)

    def add_node(self, count=None):
        """
        添加一个Node，并返回新添加的Node对象

        Args:
            count: 当需要批量添加的时候，添加的数量

        Returns:
            Node: 新添加的Node对象。
        """
        if count is None:
            index = core.ip_add_node(self.handle)
            return self.get_node(index)
        else:
            assert isinstance(count, int) and count >= 0
            if count > 0:
                core.ip_add_nodes(self.handle, count)
            return None

    def get_node(self, index):
        """
        返回序号为index的Node对象

        Args:
            index (int): 要获取的节点的索引。

        Returns:
            Node: 序号为index的Node对象，如果索引有效；否则返回None。
        """
        index = get_index(index, self.node_n)
        if index is not None:
            return InvasionPercolation.Node(self, index)
        else:
            return None

    core.use(c_size_t, 'ip_add_bond',
             c_void_p, c_size_t, c_size_t)
    core.use(None, 'ip_add_bonds',
             c_void_p, c_size_t,
             c_void_p, c_void_p, c_void_p)

    def add_bond(self, node0, node1, *,
                 count=None, p_bond_ids=None):
        """
        添加一个Bond，来连接给定序号的两个Node。

        Args:
            node0 (Node or int or pointer): 第一个节点或其索引。
            node1 (Node or int or pointer): 第二个节点或其索引。
            count: 当需要批量添加的时候，添加的数量
            p_bond_ids: 批量添加的时候返回的bond的index

        Returns:
            Bond: 新添加的Bond对象。

        Raises:
            AssertionError: 如果节点索引超出范围或两个节点索引相同。

        Note:
            尽管node0、node1、p_bond_ids应该是int类型的指针，但是为了保持zml中接口
            的一致性，这里仍假设它们是指向float64类型的指针。
            批量添加的功能(2025-4-8)尚未测试
        """
        if count is None:
            if isinstance(node0, InvasionPercolation.Node):
                node0 = node0.index
            if isinstance(node1, InvasionPercolation.Node):
                node1 = node1.index
            assert self.node_n > node0 != node1 < self.node_n
            index = core.ip_add_bond(self.handle, node0, node1)
            return self.get_bond(index)
        else:
            assert isinstance(count, int) and count >= 0
            if count > 0:
                core.ip_add_bonds(
                    self.handle,
                    count,
                    const_f64_ptr(node0),
                    const_f64_ptr(node1),
                    0 if p_bond_ids is None else f64_ptr(p_bond_ids)
                )
            return None

    def get_bond(self, index):
        """
        返回给定序号的Bond

        Args:
            index (int): 要获取的通道的索引。

        Returns:
            Bond: 给定序号的Bond对象，如果索引有效；否则返回None。
        """
        index = get_index(index, self.bond_n)
        if index is not None:
            return InvasionPercolation.Bond(self, index)
        else:
            return None

    core.use(c_size_t, 'ip_get_bond_id',
             c_void_p, c_size_t, c_size_t)

    def get_bond_id(self, node0, node1):
        """
        返回两个node中间的bond的id（如果不存在，则返回无穷大）

        Args:
            node0 (Node or int): 第一个节点或其索引。
            node1 (Node or int): 第二个节点或其索引。

        Returns:
            int: 两个节点中间的bond的id，如果不存在则返回无穷大。
        """
        if isinstance(node0, InvasionPercolation.Node):
            node0 = node0.index
        if isinstance(node1, InvasionPercolation.Node):
            node1 = node1.index
        return core.ip_get_bond_id(self.handle, node0, node1)

    def find_bond(self, node0, node1):
        """
        返回两个node中间的bond

        Args:
            node0 (Node or int): 第一个节点或其索引。
            node1 (Node or int): 第二个节点或其索引。

        Returns:
            Bond: 两个节点中间的bond对象，如果存在；否则返回None。
        """
        if isinstance(node0, InvasionPercolation.Node):
            node0 = node0.index
        if isinstance(node1, InvasionPercolation.Node):
            node1 = node1.index
        index = self.get_bond_id(node0, node1)
        return self.get_bond(index)

    core.use(c_size_t, 'ip_get_node_n', c_void_p)

    def get_node_n(self):
        """
        获取模型中节点的数量

        Returns:
            int: 模型中节点的数量。
        """
        return core.ip_get_node_n(self.handle)

    @property
    def node_n(self):
        """
        获取模型中节点的数量

        Returns:
            int: 模型中节点的数量。
        """
        return self.get_node_n()

    core.use(c_size_t, 'ip_get_bond_n', c_void_p)

    def get_bond_n(self):
        """
        获取模型中键（bond）的数量。

        Returns:
            int: 模型中键的数量。
        """
        return core.ip_get_bond_n(self.handle)

    @property
    def bond_n(self):
        """
        获取模型中键（bond）的数量。

        Returns:
            int: 模型中键的数量。
        """
        return self.get_bond_n()

    core.use(c_size_t, 'ip_get_outlet_n',
             c_void_p)
    core.use(None, 'ip_set_outlet_n',
             c_void_p, c_size_t)

    def get_outlet_n(self):
        """
        获取模型内被视为“出口”的节点（Node）的数量。

        Returns:
            int: 模型内被视为“出口”的节点的数量。
        """
        return core.ip_get_outlet_n(self.handle)

    def set_outlet_n(self, value):
        """
        设置模型内被视为“出口”的节点（Node）的数量。

        Args:
            value (int): 要设置的“出口”节点数量，必须大于等于0。

        Raises:
            AssertionError: 如果提供的值小于0。
        """
        assert value >= 0
        core.ip_set_outlet_n(self.handle, value)

    @property
    def outlet_n(self):
        """
        获取或设置模型内被视为“出口”的节点（Node）的数量。

        Returns:
            int: 模型内被视为“出口”的节点的数量。

        Raises:
            AssertionError: 如果设置的值小于0。
        """
        return self.get_outlet_n()

    @outlet_n.setter
    def outlet_n(self, value):
        """
        设置模型内被视为“出口”的节点（Node）的数量。

        Args:
            value (int): 要设置的“出口”节点数量，必须大于等于0。

        Raises:
            AssertionError: 如果提供的值小于0。
        """
        self.set_outlet_n(value)

    core.use(None, 'ip_set_outlet',
             c_void_p, c_size_t, c_size_t)

    def set_outlet(self, index, value):
        """
        设置第index个出口对应的节点（Node）的序号。

        Args:
            index (int): 出口的索引。
            value (int): 节点的索引。

        Raises:
            AssertionError: 如果索引无效。
        """
        index = get_index(index, self.outlet_n)
        if index is not None:
            value = get_index(value, self.node_n)
            if value is not None:
                core.ip_set_outlet(self.handle, index, value)

    core.use(c_size_t, 'ip_get_outlet',
             c_void_p, c_size_t)

    def get_outlet(self, index):
        """
        获取第index个出口对应的节点（Node）的序号。

        Args:
            index (int): 出口的索引。

        Returns:
            int: 第index个出口对应的节点的序号，如果索引有效；否则返回None。
        """
        index = get_index(index, self.outlet_n)
        if index is not None:
            return core.ip_get_outlet(self.handle, index)
        else:
            return None

    def add_outlet(self, node_id):
        """
        添加一个出口点，并返回这个出口点的序号。

        Args:
            node_id (int): 要添加为出口的节点的索引。

        Returns:
            int: 新添加的出口点的序号。

        Raises:
            AssertionError: 如果节点索引超出范围。
        """
        assert node_id < self.node_n
        index = self.outlet_n
        self.outlet_n = index + 1
        self.set_outlet(index, node_id)
        return index

    core.use(c_double, 'ip_get_tension',
             c_void_p, c_size_t, c_size_t)

    def get_tension(self, ph0, ph1):
        """
        获取两种相态ph0和ph1之间的界面张力。

        Args:
            ph0 (int): 第一种相态，必须大于等于0。
            ph1 (int): 第二种相态，必须大于等于0且不等于ph0。

        Returns:
            float: 两种相态之间的界面张力。

        Raises:
            AssertionError: 如果相态索引无效。
        """
        assert 0 <= ph0 != ph1 >= 0
        return core.ip_get_tension(self.handle, ph0, ph1)

    core.use(None, 'ip_set_tension',
             c_void_p, c_size_t, c_size_t, c_double)

    def set_tension(self, ph0, ph1, value):
        """
        设置两种相态ph0和ph1之间的界面张力。

        Args:
            ph0 (int): 第一种相态，必须大于等于0。
            ph1 (int): 第二种相态，必须大于等于0且不等于ph0。
            value (float): 要设置的界面张力值，必须为正数。

        Raises:
            AssertionError: 如果相态索引无效或界面张力值为负数。
        """
        assert 0 <= ph0 != ph1 >= 0
        core.ip_set_tension(self.handle, ph0, ph1, value)

    core.use(c_double, 'ip_get_contact_angle',
             c_void_p, c_size_t, c_size_t)

    def get_contact_angle(self, ph0, ph1):
        """
        获取当ph0驱替ph1时，在ph0中的接触角。注意，这是一个全局设置，
        后续会被各个节点（Node）和键（Bond）内的设置覆盖。

        Args:
            ph0 (int): 驱替相态，必须大于等于0。
            ph1 (int): 被驱替相态，必须大于等于0且不等于ph0。

        Returns:
            float: 接触角的值。

        Raises:
            AssertionError: 如果相态索引无效。
        """
        assert 0 <= ph0 != ph1 >= 0
        return core.ip_get_contact_angle(self.handle, ph0, ph1)

    core.use(None, 'ip_set_contact_angle',
             c_void_p, c_size_t, c_size_t,
             c_double)

    def set_contact_angle(self, ph0, ph1, value):
        """
        设置当ph0驱替ph1时，在ph0中的接触角。注意，这是一个全局设置，
        后续会被各个节点（Node）和键（Bond）内的设置覆盖。

        Args:
            ph0 (int): 驱替相态，必须大于等于0。
            ph1 (int): 被驱替相态，必须大于等于0且不等于ph0。
            value (float): 要设置的接触角的值。

        Raises:
            AssertionError: 如果相态索引无效。
        """
        assert 0 <= ph0 != ph1 >= 0
        core.ip_set_contact_angle(self.handle, ph0, ph1, value)

    core.use(c_double, 'ip_get_density',
             c_void_p, c_size_t)

    def get_density(self, ph):
        """
        获取流体ph的密度。

        Args:
            ph (int): 流体相态，必须大于等于0。

        Returns:
            float: 流体的密度。

        Raises:
            AssertionError: 如果相态索引无效。
        """
        assert ph >= 0
        return core.ip_get_density(self.handle, ph)

    core.use(None, 'ip_set_density',
             c_void_p, c_size_t, c_double)

    def set_density(self, ph, value):
        """
        设置流体ph的密度。

        Args:
            ph (int): 流体相态，必须大于等于0。
            value (float): 要设置的流体密度值，必须为正数。

        Returns:
            self: 返回当前对象实例。

        Raises:
            AssertionError: 如果相态索引无效或密度值为负数。
        """
        assert ph >= 0
        assert value > 0
        core.ip_set_density(self.handle, ph, value)
        return self

    core.use(c_double, 'ip_get_gravity', c_void_p, c_size_t)

    def get_gravity(self):
        """
        获取重力向量。注意，这个三维向量要和节点（Node）中pos属性的含义保持一致。

        Returns:
            list: 包含三个浮点数的列表，表示重力向量。
        """
        return [core.ip_get_gravity(self.handle, i) for i in range(3)]

    core.use(None, 'ip_set_gravity',
             c_void_p, c_size_t, c_double)

    def set_gravity(self, value):
        """
        设置重力向量。注意，这个三维向量要和节点（Node）中pos属性的含义保持一致。

        Args:
            value (list): 包含三个浮点数的列表，表示要设置的重力向量。

        Returns:
            self: 返回当前对象实例。
        """
        for i in range(3):
            core.ip_set_gravity(self.handle, i, value[i])
        return self

    @property
    def gravity(self):
        """
        获取或设置重力向量。注意，这个三维向量要和节点（Node）中pos属性的含义保持一致。

        Returns:
            list: 包含三个浮点数的列表，表示重力向量。
        """
        return self.get_gravity()

    @gravity.setter
    def gravity(self, value):
        """
        设置重力向量。注意，这个三维向量要和节点（Node）中pos属性的含义保持一致。

        Args:
            value (list): 包含三个浮点数的列表，表示要设置的重力向量。
        """
        self.set_gravity(value)

    core.use(c_size_t, 'ip_get_inj_n',
             c_void_p)
    core.use(None, 'ip_set_inj_n',
             c_void_p, c_size_t)

    def get_inj_n(self):
        """
        获取模型中注入点的数量。

        Returns:
            int: 模型中注入点的数量。
        """
        return core.ip_get_inj_n(self.handle)

    def set_inj_n(self, value):
        """
        设置模型中注入点的数量。

        Args:
            value (int): 要设置的注入点数量，必须大于等于0。

        Returns:
            self: 返回当前对象实例。

        Raises:
            AssertionError: 如果提供的值小于0。
        """
        assert value >= 0
        core.ip_set_inj_n(self.handle, value)
        return self

    @property
    def inj_n(self):
        """
        获取或设置模型中注入点的数量。

        Returns:
            int: 模型中注入点的数量。

        Raises:
            AssertionError: 如果设置的值小于0。
        """
        return self.get_inj_n()

    @inj_n.setter
    def inj_n(self, value):
        """
        设置模型中注入点的数量。

        Args:
            value (int): 要设置的注入点数量，必须大于等于0。

        Raises:
            AssertionError: 如果提供的值小于0。
        """
        self.set_inj_n(value)

    def get_inj(self, index):
        """
        返回第index个注入点。

        Args:
            index (int): 注入点的索引。

        Returns:
            InvasionPercolation.Injector: 第index个注入点对象，
            如果索引有效；否则返回None。
        """
        index = get_index(index, self.inj_n)
        if index is not None:
            return InvasionPercolation.Injector(self, index)
        else:
            return None

    def add_inj(self, node_id=None, phase=None, qinj=None):
        """
        添加一个注入点，并返回注入点对象。

        Args:
            node_id (int, 可选): 注入点所在的节点索引。
            phase (int, 可选): 注入流体的相态。
            qinj (float, 可选): 注入流量。

        Returns:
            InvasionPercolation.Injector: 新添加的注入点对象。
        """
        index = self.inj_n
        self.inj_n = self.inj_n + 1
        inj = self.get_inj(index)
        if node_id is not None:
            inj.node_id = node_id
        if phase is not None:
            inj.phase = phase
        if qinj is not None:
            inj.qinj = qinj
        return inj

    core.use(c_bool, 'ip_trap_enabled', c_void_p)

    @property
    def trap_enabled(self):
        """
        获取是否允许围困。当此开关为True，且出口（outlet）的数量不为0时，围困生效。

        Returns:
            bool: 是否允许围困。
        """
        return core.ip_trap_enabled(self.handle)

    core.use(None, 'ip_set_trap_enabled',
             c_void_p, c_bool)

    @trap_enabled.setter
    def trap_enabled(self, value):
        """
        设置是否允许围困。当此开关为True，且出口（outlet）的数量不为0时，围困生效。

        Args:
            value (bool): 是否允许围困。
        """
        core.ip_set_trap_enabled(self.handle, value)

    core.use(c_size_t, 'ip_get_oper_n',
             c_void_p)

    def get_oper_n(self):
        """
        获取模型中操作（operation）的数量。

        Returns:
            int: 模型中操作的数量。
        """
        return core.ip_get_oper_n(self.handle)

    @property
    def oper_n(self):
        """
        获取模型中操作（operation）的数量。

        Returns:
            int: 模型中操作的数量。
        """
        return self.get_oper_n()

    def get_oper(self, index):
        """
        返回第idx个操作。

        Args:
            index (int): 操作的索引。

        Returns:
            InvasionPercolation.InvadeOperation: 第idx个操作对象，
            如果索引有效；否则返回None。
        """
        index = get_index(index, self.oper_n)
        if index is not None:
            return InvasionPercolation.InvadeOperation(self, index)
        else:
            return None

    core.use(None, 'ip_remove_node',
             c_void_p, c_size_t)
    core.use(None, 'ip_remove_bond',
             c_void_p, c_size_t)

    def remove_node(self, node):
        """
        删除给定节点（Node）连接的所有键（Bond），然后删除该节点。

        Args:
            node (InvasionPercolation.Node or int): 要删除的节点对象或其索引。
        """
        if node is None:
            return
        if isinstance(node, InvasionPercolation.Node):
            assert node.model.handle == self.handle
            node = node.index
        if node < self.node_n:
            core.ip_remove_node(self.handle, node)

    def remove_bond(self, bond):
        """
        删除给定的键（Bond）。

        Args:
            bond (InvasionPercolation.Bond or int): 要删除的键对象或其索引。
        """
        if bond is None:
            return
        if isinstance(bond, InvasionPercolation.Bond):
            assert bond.model.handle == self.handle
            bond = bond.index
        if bond < self.bond_n:
            core.ip_remove_bond(self.handle, bond)

    core.use(c_size_t, 'ip_get_nearest_node_id', c_void_p, c_double, c_double, c_double)

    def get_nearest_node(self, pos):
        """
        返回距离给定点最近的节点（Node）。

        Args:
            pos (list | tuple): 包含三个浮点数的列表，表示点的三维坐标。

        Returns:
            InvasionPercolation.Node: 距离给定点最近的节点对象。

        Raises:
            AssertionError: 如果坐标列表的长度不为3。
        """
        assert len(pos) == 3
        pos = [1.0e210 if pos[i] is None else pos[i] for i in range(3)]
        index = core.ip_get_nearest_node_id(self.handle, pos[0], pos[1], pos[2])
        return self.get_node(index)

    core.use(None, 'ip_get_node_pos',
             c_void_p, c_void_p, c_void_p, c_void_p,
             c_size_t)

    def get_node_pos(self, x=None, y=None, z=None, phase=IDX_INF):
        """
        获得给定相态（phase）的节点（Node）的位置；如果相态大于INT_INF，
        则返回所有节点的位置。

        Args:
            x (Vector, 可选): 存储x坐标的向量对象。
            y (Vector, 可选): 存储y坐标的向量对象。
            z (Vector, 可选): 存储z坐标的向量对象。
            phase (int, 可选): 相态索引，默认为INT_INF。

        Returns:
            tuple: 包含三个Vector对象的元组，表示节点的x、y、z坐标。
        """
        if not isinstance(x, Vector):
            x = Vector()
        if not isinstance(y, Vector):
            y = Vector()
        if not isinstance(z, Vector):
            z = Vector()
        core.ip_get_node_pos(self.handle, x.handle, y.handle, z.handle, phase)
        return x, y, z

    core.use(None, 'ip_write_pos',
             c_void_p, c_size_t, POINTER(c_double))

    def write_pos(self, dim: int, pointer):
        """
        批量获得位置信息。

        Args:
            dim (int): 维度。
            pointer (POINTER(c_double)): 指向存储位置信息的指针。
        """
        assert dim in [0, 1, 2], f'dim must be 0, 1, or 2, but got {dim}'
        core.ip_write_pos(self.handle, dim, f64_ptr(pointer))

    core.use(None, 'ip_read_pos', c_void_p, c_size_t, POINTER(c_double))

    def read_pos(self, dim, pointer):
        """
        批量修改位置信息。

        Args:
            dim (int): 维度。
            pointer (POINTER(c_double)): 指向存储位置信息的指针。
        """
        assert dim in [0, 1, 2], f'dim must be 0, 1, or 2, but got {dim}'
        core.ip_read_pos(self.handle, dim, const_f64_ptr(pointer))

    core.use(None, 'ip_write_phase', c_void_p, POINTER(c_double))

    def write_phase(self, pointer):
        """
        获得相态（phase）信息，并将其写入到给定的指针。
        注意，虽然相态在模型内部的存储为int类型，但此函数使用的是double类型的指针。

        Args:
            pointer (POINTER(c_double)): 指向存储相态信息的指针。
        """
        core.ip_write_phase(self.handle, f64_ptr(pointer))

    core.use(None, 'ip_read_phase',
             c_void_p, POINTER(c_double))

    def read_phase(self, pointer):
        """
        从给定的指针读取相态（phase）信息并设置到模型中。
        注意，虽然相态在模型内部的存储为int类型，但此函数使用的是double类型的指针。

        Args:
            pointer (POINTER(c_double)): 指向存储相态信息的指针。
        """
        core.ip_read_phase(self.handle, const_f64_ptr(pointer))

    def nodes_write(self, *args, **kwargs):
        """
        此方法已弃用，将于2025-6-2之后移除。

        Args:
            *args: 可变位置参数。
            **kwargs: 可变关键字参数。

        Returns:
            调用zmlx.alg.ip_nodes_write模块的ip_nodes_write函数的结果。
        """
        warnings.warn('remove after 2025-6-2', DeprecationWarning, stacklevel=2)
        return ip_nodes_write(self, *args, **kwargs)

    core.use(None, 'ip_write_node_radi', c_void_p, POINTER(c_double))

    def write_node_radi(self, pointer):
        """
        将节点（Node）的半径数据写入到给定的指针。

        Args:
            pointer (POINTER(c_double)): 指向存储节点半径数据的指针。
        """
        core.ip_write_node_radi(self.handle, f64_ptr(pointer))

    core.use(None, 'ip_read_node_radi',
             c_void_p, POINTER(c_double))

    def read_node_radi(self, pointer):
        """
        从给定的指针读取节点（Node）的半径数据。

        Args:
            pointer (POINTER(c_double)): 指向存储节点半径数据的指针。
        """
        core.ip_read_node_radi(self.handle, const_f64_ptr(pointer))

    core.use(None, 'ip_write_bond_radi',
             c_void_p, POINTER(c_double))

    def write_bond_radi(self, pointer):
        """
        将键（Bond）的半径数据写入到给定的指针。

        Args:
            pointer (POINTER(c_double)): 指向存储键半径数据的指针。
        """
        core.ip_write_bond_radi(self.handle, f64_ptr(pointer))

    core.use(None, 'ip_read_bond_radi',
             c_void_p, POINTER(c_double))

    def read_bond_radi(self, pointer):
        """
        从给定的指针读取键（Bond）的半径数据。

        Args:
            pointer (POINTER(c_double)): 指向存储键半径数据的指针。
        """
        core.ip_read_bond_radi(self.handle, const_f64_ptr(pointer))

    core.use(None, 'ip_write_node_rate_invaded',
             c_void_p, POINTER(c_double))

    def write_node_rate_invaded(self, pointer):
        """
        将节点（Node）的侵入速率数据写入到给定的指针。

        Args:
            pointer (POINTER(c_double)): 指向存储节点侵入速率数据的指针。
        """
        core.ip_write_node_rate_invaded(self.handle,
                                        f64_ptr(pointer))

    core.use(None, 'ip_read_node_rate_invaded',
             c_void_p, POINTER(c_double))

    def read_node_rate_invaded(self, pointer):
        """
        从给定的指针读取节点（Node）的侵入速率数据。

        Args:
            pointer (POINTER(c_double)): 指向存储节点侵入速率数据的指针。
        """
        core.ip_read_node_rate_invaded(self.handle,
                                       const_f64_ptr(pointer))

    core.use(None, 'ip_write_node_time_invaded',
             c_void_p, POINTER(c_double))

    def write_node_time_invaded(self, pointer):
        """
        将节点（Node）的侵入时间数据写入到给定的指针。

        Args:
            pointer (POINTER(c_double)): 指向存储节点侵入时间数据的指针。
        """
        core.ip_write_node_time_invaded(self.handle,
                                        f64_ptr(pointer))

    core.use(None, 'ip_read_node_time_invaded',
             c_void_p, POINTER(c_double))

    def read_node_time_invaded(self, pointer):
        """
        从给定的指针读取节点（Node）的侵入时间数据。

        Args:
            pointer (POINTER(c_double)): 指向存储节点侵入时间数据的指针。
        """
        core.ip_read_node_time_invaded(self.handle,
                                       const_f64_ptr(pointer))

    core.use(None, 'ip_write_bond_dp0',
             c_void_p, POINTER(c_double))

    def write_bond_dp0(self, pointer):
        """
        将键（Bond）的dp0数据写入到给定的指针。

        Args:
            pointer (POINTER(c_double)): 指向存储键dp0数据的指针。
        """
        core.ip_write_bond_dp0(self.handle, f64_ptr(pointer))

    core.use(None, 'ip_read_bond_dp0',
             c_void_p, POINTER(c_double))

    def read_bond_dp0(self, pointer):
        """
        从给定的指针读取键（Bond）的dp0数据。

        Args:
            pointer (POINTER(c_double)): 指向存储键dp0数据的指针。
        """
        core.ip_read_bond_dp0(self.handle, const_f64_ptr(pointer))

    core.use(None, 'ip_write_bond_dp1',
             c_void_p, POINTER(c_double))

    def write_bond_dp1(self, pointer):
        """
        将键（Bond）的dp1数据写入到给定的指针。

        Args:
            pointer (POINTER(c_double)): 指向存储键dp1数据的指针。
        """
        core.ip_write_bond_dp1(self.handle, f64_ptr(pointer))

    core.use(None, 'ip_read_bond_dp1',
             c_void_p, POINTER(c_double))

    def read_bond_dp1(self, pointer):
        """
        从给定的指针读取键（Bond）的dp1数据。

        Args:
            pointer (POINTER(c_double)): 指向存储键dp1数据的指针。
        """
        core.ip_read_bond_dp1(self.handle, const_f64_ptr(pointer))

    core.use(None, 'ip_write_bond_tension',
             c_void_p, c_size_t, c_size_t,
             POINTER(c_double))

    def write_bond_tension(self, ph0, ph1, pointer):
        """
        将两种相态ph0和ph1之间键（Bond）的界面张力数据写入到给定的指针。

        Args:
            ph0 (int): 第一种相态，必须大于等于0。
            ph1 (int): 第二种相态，必须大于等于0且不等于ph0。
            pointer (POINTER(c_double)): 指向存储界面张力数据的指针。
        """
        core.ip_write_bond_tension(self.handle, ph0, ph1,
                                   f64_ptr(pointer))

    core.use(None, 'ip_read_bond_tension',
             c_void_p, c_size_t, c_size_t,
             POINTER(c_double))

    def read_bond_tension(self, ph0, ph1, pointer):
        """
        从给定的指针读取两种相态ph0和ph1之间键（Bond）的界面张力数据。

        Args:
            ph0 (int): 第一种相态，必须大于等于0。
            ph1 (int): 第二种相态，必须大于等于0且不等于ph0。
            pointer (POINTER(c_double)): 指向存储界面张力数据的指针。
        """
        core.ip_read_bond_tension(self.handle, ph0, ph1,
                                  const_f64_ptr(pointer))

    core.use(None, 'ip_write_bond_contact_angle',
             c_void_p, c_size_t, c_size_t,
             POINTER(c_double))

    def write_bond_contact_angle(self, ph0, ph1, pointer):
        """
        将两种相态ph0和ph1之间键（Bond）的接触角数据写入到给定的指针。

        Args:
            ph0 (int): 第一种相态，必须大于等于0。
            ph1 (int): 第二种相态，必须大于等于0且不等于ph0。
            pointer (POINTER(c_double)): 指向存储接触角数据的指针。
        """
        core.ip_write_bond_contact_angle(self.handle, ph0, ph1,
                                         f64_ptr(pointer))

    core.use(None, 'ip_read_bond_contact_angle',
             c_void_p, c_size_t, c_size_t,
             POINTER(c_double))

    def read_bond_contact_angle(self, ph0, ph1, pointer):
        """
        从给定的指针读取两种相态ph0和ph1之间键（Bond）的接触角数据。

        Args:
            ph0 (int): 第一种相态，必须大于等于0。
            ph1 (int): 第二种相态，必须大于等于0且不等于ph0。
            pointer (POINTER(c_double)): 指向存储接触角数据的指针。
        """
        core.ip_read_bond_contact_angle(self.handle, ph0, ph1,
                                        const_f64_ptr(pointer))

    core.use(None, 'ip_write_inj_node_id',
             c_void_p, POINTER(c_double))

    def write_inj_node_id(self, pointer):
        """
        将Injector的node_id写入到给定的指针

        Args:
            pointer (POINTER(c_double)): 指向存储数据的指针

        Note:
            尽管node_id是整形数据，但是为了zml接口的一致性，这里接受的pointer仍然是
            浮点型double的指针
            since 2025-4-8  尚未测试
        """
        core.ip_write_inj_node_id(self.handle, f64_ptr(pointer))

    core.use(None, 'ip_read_inj_node_id',
             c_void_p, POINTER(c_double))

    def read_inj_node_id(self, pointer):
        """
        从给定的指针读取Injector的node_id

        Args:
            pointer (POINTER(c_double)): 指向读取数据的指针。

        Note:
            尽管node_id是整形数据，但是为了zml接口的一致性，这里接受的pointer仍然是
            浮点型double的指针
            since 2025-4-8  尚未测试
        """
        core.ip_read_inj_node_id(self.handle, const_f64_ptr(pointer))

    core.use(None, 'ip_write_inj_phase',
             c_void_p, POINTER(c_double))

    def write_inj_phase(self, pointer):
        """
        将Injector的phase写入到给定的指针

        Args:
            pointer (POINTER(c_double)): 指向存储数据的指针

        Note:
            尽管phase是整形数据，但是为了zml接口的一致性，这里接受的pointer仍然是
            浮点型double的指针
            since 2025-4-8  尚未测试
        """
        core.ip_write_inj_phase(self.handle, f64_ptr(pointer))

    core.use(None, 'ip_read_inj_phase',
             c_void_p, POINTER(c_double))

    def read_inj_phase(self, pointer):
        """
        从给定的指针读取Injector的phase

        Args:
            pointer (POINTER(c_double)): 指向读取数据的指针。

        Note:
            尽管phase是整形数据，但是为了zml接口的一致性，这里接受的pointer仍然是
            浮点型double的指针
            since 2025-4-8  尚未测试
        """
        core.ip_read_inj_phase(self.handle, const_f64_ptr(pointer))

    core.use(None, 'ip_write_inj_q',
             c_void_p, POINTER(c_double))

    def write_inj_q(self, pointer):
        """
        将Injector的q写入到给定的指针

        Args:
            pointer (POINTER(c_double)): 指向存储数据的指针

        Note:
            since 2025-4-8  尚未测试
        """
        core.ip_write_inj_q(self.handle, f64_ptr(pointer))

    core.use(None, 'ip_read_inj_q',
             c_void_p, POINTER(c_double))

    def read_inj_q(self, pointer):
        """
        从给定的指针读取Injector的q

        Args:
            pointer (POINTER(c_double)): 指向读取数据的指针。

        Note:
            since 2025-4-8  尚未测试
        """
        core.ip_read_inj_q(self.handle, const_f64_ptr(pointer))

    core.use(None, 'ip_write_outlet',
             c_void_p, POINTER(c_double))

    def write_outlet(self, pointer):
        """
        将各个Outlet对应的node_id写入到给定的指针

        Args:
            pointer (POINTER(c_double)): 指向存储数据的指针

        Note:
            尽管node_id是整形数据，但是为了zml接口的一致性，这里接受的pointer仍然是
            浮点型double的指针
            since 2025-4-8  尚未测试
        """
        core.ip_write_outlet(self.handle, f64_ptr(pointer))

    core.use(None, 'ip_read_outlet',
             c_void_p, POINTER(c_double))

    def read_outlet(self, pointer):
        """
        从给定的指针读取各个Outlet对应的node_id

        Args:
            pointer (POINTER(c_double)): 指向读取数据的指针。

        Note:
            尽管node_id是整形数据，但是为了zml接口的一致性，这里接受的pointer仍然是
            浮点型double的指针
            since 2025-4-8  尚未测试
        """
        core.ip_read_outlet(self.handle, const_f64_ptr(pointer))


def ip_nodes_write(model: InvasionPercolation, index: Union[int, str], pointer=None, buf=None):
    """
    导出InvasionPercolation模型的节点的属性:
        index=-1, x坐标
        index=-2, y坐标
        index=-3, z坐标
        index=-4, phase
    """
    if pointer is None:
        assert np is not None
        if buf is None:
            buf = np.zeros(shape=model.node_n, dtype=np.float64)
            buf = np.ascontiguousarray(buf)
        else:
            assert len(buf) == model.node_n
            buf = np.ascontiguousarray(buf)
        assert buf.flags.c_contiguous, f'The buffer must be contiguous for save'
        pointer = buf.ctypes.data_as(POINTER(c_double))

    if isinstance(index, str):
        if index == 'x':
            index = -1
        elif index == 'y':
            index = -2
        elif index == 'z':
            index = -3
        elif index == 'phase':
            index = -4

    if index == -1 or index == -2 or index == -3:
        model.write_pos(-index - 1, pointer)
        return buf
    elif index == -4:
        model.write_phase(pointer)
        return buf
    else:
        return None


def _get_buf(count: int, buf=None):
    assert np is not None
    if buf is None:
        buf = np.zeros(shape=count, dtype=np.float64)
        buf = np.ascontiguousarray(buf)
    else:
        assert len(buf) == count
        buf = np.ascontiguousarray(buf)
    return buf


def get_pos(model: InvasionPercolation, dim: int, buf=None):
    """
    获得节点的坐标.
    Args:
        model: InvasionPercolation 模型.
        dim: 需要导出的维度 0、1、2
        buf: 结果缓冲区

    Returns:
        ndarray: 使用numpy的数组表示的坐标
    """
    assert dim in [0, 1, 2], f'dim must be 0, 1, or 2, but got {dim}'
    buf = _get_buf(model.node_n, buf)
    model.write_pos(dim, f64_ptr(buf))
    return buf


def get_x(model: InvasionPercolation, buf=None):
    return get_pos(model, 0, buf)


def get_y(model: InvasionPercolation, buf=None):
    return get_pos(model, 1, buf)


def get_z(model: InvasionPercolation, buf=None):
    return get_pos(model, 2, buf)


def get_phase(model: InvasionPercolation, buf=None):
    buf = _get_buf(model.node_n, buf)
    model.write_phase(f64_ptr(buf))
    return buf


def set_pos(model: InvasionPercolation, dim, pos):
    assert np is not None
    assert dim in [0, 1, 2], f'dim must be 0, 1, or 2, but got {dim}'
    if np.isscalar(pos):
        pos = np.full(shape=model.node_n, fill_value=pos)
    model.read_pos(dim, const_f64_ptr(pos))


def set_x(model: InvasionPercolation, pos):
    set_pos(model, 0, pos)


def set_y(model: InvasionPercolation, pos):
    set_pos(model, 1, pos)


def set_z(model: InvasionPercolation, pos):
    set_pos(model, 2, pos)


def set_phase(model: InvasionPercolation, phase):
    assert np is not None
    if np.isscalar(phase):
        phase = np.full(shape=model.node_n, fill_value=phase)
    model.read_phase(const_f64_ptr(phase))


def set_node_radi(model: InvasionPercolation, radi):
    assert np is not None
    if np.isscalar(radi):
        radi = np.full(shape=model.node_n, fill_value=radi)
    model.read_node_radi(const_f64_ptr(radi))


def set_nodes(model: InvasionPercolation, count, x=None, y=None, z=None, phase=None, radi=None):
    assert model.node_n == 0
    model.add_node(count)
    if x is not None:
        set_x(model, x)
    if y is not None:
        set_y(model, y)
    if z is not None:
        set_z(model, z)
    if phase is not None:
        set_phase(model, phase)
    if radi is not None:
        set_node_radi(model, radi)


def set_bonds(model: InvasionPercolation, count, node0, node1, radi=None):
    assert model.bond_n == 0
    model.add_bond(
        node0=const_f64_ptr(node0),
        node1=const_f64_ptr(node1),
        count=count)
    if radi is not None:
        model.read_bond_radi(const_f64_ptr(radi))


def show_xy(
        model: InvasionPercolation, caption='Invasion Process',
        jx=None, jy=None, cmap=None, clabel='Phase', grid=True,
        xlabel='x (m)', ylabel='y (m)', title='Fluid Invasion'
):
    from zmlx.fig import contourf, tricontourf, plot2d
    x = get_x(model)
    y = get_y(model)
    v = get_phase(model)
    if cmap is None:
        cmap = 'coolwarm'
    if jx is not None and jy is not None:
        assert np is not None
        o = contourf(np.reshape(x, (jx, jy)),
                     np.reshape(y, (jx, jy)),
                     np.reshape(v, (jx, jy)), cmap=cmap, cbar=dict(label=clabel))
    else:
        o = tricontourf(x, y, v, cmap=cmap, cbar=dict(label=clabel))

    plot2d(o, aspect='equal', xlabel=xlabel, ylabel=ylabel, title=title, grid=grid, caption=caption)
