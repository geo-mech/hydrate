import ctypes
import math
import warnings
from ctypes import c_double, c_void_p, c_size_t, c_bool, c_char_p, POINTER, c_int64
from typing import Optional, Iterable, Tuple, List, Union, Any

from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._fmap import FileMap
from zmlx.exts._interp import Interp1, Interp2
from zmlx.exts._lexpr import LinearExpr
from zmlx.exts._lic import lic
from zmlx.exts._map import Map
from zmlx.exts._mesh import Groups
from zmlx.exts._pool import ThreadPool
from zmlx.exts._sol import ConjugateGradientSolver
from zmlx.exts._str import String
from zmlx.exts._utils import (
    HasCells, HasHandle, Iterator, Object, attr_in_range, get_distance, f64_ptr, const_f64_ptr, get_index, IDX_INF,
    is_array, parse_fid3, log, make_parent, check_ipath, np, parse_fid
)
from zmlx.exts._vec import UintVector, Vector


class Reaction(HasHandle):
    """
    定义一个化学反应。

    这里，所谓“化学反应”，是一种或者几种流体（或者流体的组分）转化为另外一种或者几种
        流体或者组分，并吸收或者释放能量的过程。
    这个Reaction类，定义参与反应的各种物质的比例、反应的速度以及反应过程中的能量变化。
    基于Seepage类模拟水合物的分解或者生成、冰的形成和融化、重油的裂解等，均基于此Reaction类进行定义。

    反应速率q定义：
        在单位时间内（1秒内），“反应所消耗的物质的质量（左侧物质质量的减少量）”
            与 “在Cell中所有与此反应相关的组分的质量之和”的比值.
        注意：
            此定义与一般反应速率的定义不同，需要进行转换.

    当Reaction作用到一个Cell上的时候，反应速率的计算步骤如下：
        1. 根据Cell内流体的压力，使用p2t曲线，计算出基准温度T0。如果p2t没有定义，则
            基准温度为0;
        2. 遍历各个Inhibitor，如果定义了c2t曲线，则计算此Inhibitor的浓度，并使用
            c2t曲线，计算出此Inhibitor对基准温度的影响。
            注意：此浓度的计算是基于sol和liq的比值计算的。
        3. 尝试读取Cell的idt属性和wdt属性，在此Cell内，T0=T0+idt属性值*wdt属性值.
            至此，获得了经过矫正的基准温度T0;
        4. 读取反应相关的各个组分的平均温度T，并减去基准温度T0，即得到dT=T-T0。下面，将
            使用这个dT来计算反应速率.
        5. 使用dT，以及t2q曲线，计算出正向反应速率q；同理，基于t2qr曲线，根据dT，计算出
            逆向的反应速率qr.
        6. 遍历各个Inhibitor，如果其定义了exp，则令q=q*c^exp；如果其定义了exp_r则令
            qr=qr*c^exp_r。 这个步骤，即使用相关组分的浓度来对正向和逆向的反应速率进行
            必要的矫正。
        7. 令反应速率Q=q-qr。
        8. 遍历各个Inhibitor，如果其定义了c2q曲线，则使用c2q曲线，对反应速率Q进行矫正。
            即Q=Q+c2q(c)。
        9. 查看Cell是否定义了irate属性，如果定义了，则读取irate属性为此Cell内速率的倍率，
            令Q=Q*irate属性值
        10. 至此，得到了最终的反应速率Q。
    """

    class Component:
        """
        组分。定义的是反应方程式中的一项。
        """

        def __init__(self, handle: c_void_p):
            self.handle = handle

        core.use(c_void_p, 'rea_comp_get_index', c_void_p)

        @property
        def index(self) -> List[int]:
            """
            流体组分的序号. 长度为1到3之间的list
            """
            idx = UintVector(handle=core.rea_comp_get_index(self.handle))
            return idx.to_list()

        @index.setter
        def index(self, value: List[int]):
            """
            流体组分的序号. 长度为1到3之间的list
            """
            idx = UintVector(handle=core.rea_comp_get_index(self.handle))
            idx.set(value)

        core.use(c_size_t, 'rea_comp_get_fa_t', c_void_p)

        @property
        def fa_t(self) -> int:
            """
            组分温度属性的ID. 必须定义
            """
            return core.rea_comp_get_fa_t(self.handle)

        core.use(None, 'rea_comp_set_fa_t',
                 c_void_p, c_size_t)

        @fa_t.setter
        def fa_t(self, value: int):
            """
            组分温度属性的ID. 必须定义
            """
            core.rea_comp_set_fa_t(self.handle, value)

        core.use(c_size_t, 'rea_comp_get_fa_c', c_void_p)

        @property
        def fa_c(self) -> int:
            """
            组分比热属性的ID. 必须定义
            """
            return core.rea_comp_get_fa_c(self.handle)

        core.use(None, 'rea_comp_set_fa_c',
                 c_void_p, c_size_t)

        @fa_c.setter
        def fa_c(self, value: int):
            """
            组分比热属性的ID. 必须定义
            """
            core.rea_comp_set_fa_c(self.handle, value)

        core.use(c_double, 'rea_comp_get_weight', c_void_p)

        @property
        def weight(self) -> float:
            """
            组分权重。 左侧物质的权重为负值，右侧为正值. 所有左侧物质权重的加和等于-1
            右侧物质权重的加和等于+1
            """
            return core.rea_comp_get_weight(self.handle)

        core.use(None, 'rea_comp_set_weight',
                 c_void_p, c_double)

        @weight.setter
        def weight(self, value: float):
            """
            组分权重
            """
            core.rea_comp_set_weight(self.handle, value)

    class Inhibitor:
        """
        定义抑制剂，或者催化剂。这种物质不参与反应，但是可能会影响到反应的速率。
        所有可以影响到反应速率的物质，在这里统一都定义为抑制剂
        """

        def __init__(self, handle: c_void_p):
            self.handle = handle

        core.use(c_void_p, 'rea_inh_get_sol', c_void_p)

        @property
        def sol(self) -> List[int]:
            """
            溶质对应的ID.
            说明：
                在实际计算的时候，将根据sol的质量（或者体积）除以liq的质量（或者体积）来
                获得溶质的浓度，并根据此浓度来矫正反应速率。
                具体是使用质量浓度还是体积浓度，取决于use_vol的取值。
                默认使用质量浓度。
                计算得到的溶质的浓度将会是0到1之间的数值。
            """
            return UintVector(
                handle=core.rea_inh_get_sol(self.handle)).to_list()

        @sol.setter
        def sol(self, value: List[int]):
            """
            溶质对应的ID
            """
            UintVector(
                handle=core.rea_inh_get_sol(self.handle)).set(value)

        core.use(c_void_p, 'rea_inh_get_liq', c_void_p)

        @property
        def liq(self) -> List[int]:
            """
            溶液对应的ID.
            说明：
                在实际计算的时候，将根据sol的质量（或者体积）除以liq的质量（或者体积）来
                获得溶质的浓度，并根据此浓度来矫正反应速率。
                具体是使用质量浓度还是体积浓度，取决于use_vol的取值。
                默认使用质量浓度。
                计算得到的溶质的浓度将会是0到1之间的数值。
            """
            return UintVector(
                handle=core.rea_inh_get_liq(self.handle)).to_list()

        @liq.setter
        def liq(self, value: List[int]):
            """
            溶液对应的ID
            """
            UintVector(
                handle=core.rea_inh_get_liq(self.handle)).set(value)

        core.use(c_void_p, 'rea_inh_get_c2t', c_void_p)

        @property
        def c2t(self) -> Interp1:
            """
            溶质浓度（根据sol和liq的比值计算）对基准温度的矫正。
            定义一条曲线，其中
                x为溶质的浓度 （0到1之间）
                y为此抑制剂对基准温度的改变。y>0则相当于提升基准温度（等价于流体温度降低）。单位为K
            """
            handle = core.rea_inh_get_c2t(self.handle)
            return Interp1(handle=handle)

        core.use(c_bool, 'rea_inh_get_use_vol', c_void_p)
        core.use(None, 'rea_inh_set_use_vol',
                 c_void_p, c_bool)

        @property
        def use_vol(self) -> bool:
            """
            是否使用体积分数 (如果为False，则使用质量分数)。
                如果为True，则定义浓度c为c=sol的体积/liq的体积。
                否则，定义浓度c为c=sol的质量/liq的质量。
            """
            return core.rea_inh_get_use_vol(self.handle)

        @use_vol.setter
        def use_vol(self, value: bool):
            """
            是否使用体积分数 (如果为False，则使用质量分数)
            """
            core.rea_inh_set_use_vol(self.handle, value)

        core.use(c_void_p, 'rea_inh_get_c2q', c_void_p)

        @property
        def c2q(self) -> Interp1:
            """
            溶质浓度（根据sol和liq的比值计算）对反应速率矫正。
            定义一条曲线，其中
                x为溶质的浓度 （0到1之间）
                y为此抑制剂对反应速率的影响。基于此计算的反应速率，将直接叠加在反应的速率上。
            特别注意反应速率的定义：
                在单位时间内（1秒内），“反应所消耗的物质的质量（左侧物质质量的减少量）”
                与 “在Cell中所有与此反应相关的组分的质量之和”的比值.
            """
            handle = core.rea_inh_get_c2q(self.handle)
            return Interp1(handle=handle)

        core.use(c_double, 'rea_inh_get_exp', c_void_p)

        @property
        def exp(self) -> float:
            """
            反应速率的指数（正向反应）.
                在使用反应的t2q计算出正向反应速率之后，将乘以c^exp，其中c为溶质的浓度。
                特别注意：
                    这里浓度的定义和常规的不同，在化学反应中，一般采用mol/L这样的单位
                    但是，这里的浓度为质量分数(或者体积分数，取决于use_vol属性是否为True)，
                    是无量纲的量。因此，必须进行必要的转换。
                    如果此抑制剂的浓度不会对反应的速率造成影响，则将此指数设置为0
            注意：
                只有在计算正向反应速率的时候，此属性才会起作用
            """
            return core.rea_inh_get_exp(self.handle)

        core.use(None, 'rea_inh_set_exp',
                 c_void_p, c_double)

        @exp.setter
        def exp(self, value: float):
            """
            反应速率的指数（正向反应）.
            """
            core.rea_inh_set_exp(self.handle, value)

        core.use(c_double, 'rea_inh_get_exp_r', c_void_p)

        @property
        def exp_r(self) -> float:
            """
            反应速率的指数(逆向)
                在使用反应的t2qr计算出逆向反应速率之后，将乘以c^exp_r，其中c为溶质的浓度。
                特别注意：
                    这里浓度的定义和常规的不同，在化学反应中，一般采用mol/L这样的单位
                    但是，这里的浓度为质量分数(或者体积分数，取决于use_vol属性是否为True)，
                    是无量纲的量。因此，必须进行必要的转换。
                    如果此抑制剂的浓度不会对反应的速率造成影响，则将此指数设置为0
            注意：
                只有在计算逆向反应速率的时候，此属性才会起作用
            """
            return core.rea_inh_get_exp_r(self.handle)

        core.use(None, 'rea_inh_set_exp_r',
                 c_void_p, c_double)

        @exp_r.setter
        def exp_r(self, value: float):
            """
            反应速率的指数(逆向)
            """
            core.rea_inh_set_exp_r(self.handle, value)

    core.use(c_void_p, 'new_reaction')
    core.use(None, 'del_reaction', c_void_p)

    def __init__(self, path: Optional[str] = None, handle: Optional[c_void_p] = None):
        """
        初始化一个反应。

        Args:
            path (str, optional): 当给定path的时候，
                则载入之前创建好并序列化存储的反应。默认为None。
            handle (c_void_p, optional): 反应的句柄。如果为None，
                则根据path加载反应；否则忽略path。默认为None。
        """
        super().__init__(handle, core.new_reaction, core.del_reaction)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
        else:
            assert path is None, "If handle is given, path must be None"

    core.use(None, 'reaction_save', c_void_p, c_char_p)

    def save(self, path: str):
        """
        序列化保存。

        Args:
            path (str): 保存文件的路径。

        Notes:
            可选扩展格式：
            1：.txt
                .TXT 格式（跨平台，基本不可读）
            2：.xml
                .XML 格式（特定可读性，文件体积最大，读写速度最慢，跨平台）
            3：.其他
                二进制格式
                    （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）
        """
        if isinstance(path, str):
            make_parent(path)
            core.reaction_save(self.handle, make_c_char_p(path))

    core.use(None, 'reaction_load', c_void_p, c_char_p)

    def load(self, path: str):
        """
        读取序列化文件。

        Args:
            path (str): 读取文件的路径。

        Notes:
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.reaction_load(self.handle, make_c_char_p(path))

    core.use(None, 'reaction_write_fmap',
             c_void_p, c_void_p, c_char_p)
    core.use(None, 'reaction_read_fmap',
             c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt: str = 'binary'):
        """
        将数据序列化到一个Filemap中。

        Args:
            fmt (str, optional): 序列化格式，取值可以为 'text', 'xml'
                和 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的FileMap对象。
        """
        fmap = FileMap()
        core.reaction_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt: str = 'binary'):
        """
        从Filemap中读取序列化的数据。

        Args:
            fmap (FileMap): 包含序列化数据的FileMap对象。
            fmt (str, optional): 序列化格式，取值可以为 'text', 'xml'
                和 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.reaction_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self) -> FileMap:
        """
        返回一个二进制的FileMap对象。

        Returns:
            FileMap: 包含二进制序列化数据的FileMap对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: FileMap):
        """
        从二进制的FileMap对象中读取序列化的数据。

        Args:
            value (FileMap): 包含二进制序列化数据的FileMap对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(None, 'reaction_set_dheat', c_void_p, c_double)
    core.use(c_double, 'reaction_get_dheat', c_void_p)

    @property
    def heat(self) -> float:
        """
        反应热.
            发生1kg物质的化学反应(1kg的左侧物质，转化为1kg的右侧物质)释放的热量，单位焦耳。
            注意:
                1. 如果反应是吸热反应，则此heat为负值。
                2. 特别要注意单位。此heat的单位，实际为焦耳/kg，与一般的焦耳/mol不同。

        Returns:
            float: 单位质量化学反应释放的热量，单位焦耳。
        """
        return core.reaction_get_dheat(self.handle)

    @heat.setter
    def heat(self, value: float):
        """
        反应热.
        Args:
            value (float): 单位质量化学反应释放的热量，单位焦耳。
        """
        core.reaction_set_dheat(self.handle, value)

    # 兼容之前的接口 (将在2024-02-01之后移除)
    dheat = heat

    core.use(None, 'reaction_set_t0', c_void_p, c_double)
    core.use(c_double, 'reaction_get_t0', c_void_p)

    @property
    def temp(self) -> float:
        """
        和heat对应的参考温度（单位为K），只有当反应前后的温度都等于此temp的时候，
        释放的热量才可以使用heat来定义。
        注意：
            默认值为280.0K

        Returns:
            float: 参考温度。单位K
        """
        return core.reaction_get_t0(self.handle)

    @temp.setter
    def temp(self, value: float):
        """
        设置参考温度。
        Args:
            value (float): 参考温度。
        """
        core.reaction_set_t0(self.handle, value)

    def set_p2t(self, p: List[float], t: List[float]):
        """
        设置p2t，具体参考对p2t的说明
        """
        self.p2t.set_xy(p, t)

    def set_t2q(self, t: List[float], q: List[float]):
        """
        设置t2q，具体参考对t2q的说明
        """
        self.t2q.set_xy(t, q)

    core.use(c_void_p, 'reaction_get_p2t', c_void_p)

    @property
    def p2t(self) -> Interp1:
        """
        不同的压力下，反应的基准温度. 单位K
        说明：
            在此反应定义中，反应的速率是根据温度来计算的。但是，温度总是一个相对的数值，
            因此，才有一个基准温度的概念。而且，这个基准温度是和压力相关的。
            比如说，1MPa下的基准温度是0度，2MPa下的基准温度是10度，那么后续计算反应
            速率的时候，压力1MPa，温度1度的反应速率，将和压力2MPa，温度11度的反应速率相等。
        此属性定义了一条曲线，其中：
            自变量x: 压力（一个向量），单位是Pa
            因变量y: 给定压力下对应的基准温度（一个向量，长度和x相等），单位是K
        """
        handle = core.reaction_get_p2t(self.handle)
        return Interp1(handle=handle)

    core.use(c_void_p, 'reaction_get_t2q', c_void_p)

    @property
    def t2q(self) -> Interp1:
        """
        当温度偏离平衡温度的时候反应的速率（正向反应速率，此属性必须正确设置）。
        如果定义了t2qr（逆向速率），则实际的反应速率，将是正向的速率减去逆向的速率。

        定一个一条曲线，其中：
            自变量x: 温度偏移量。单位K
            因变量y: 反应速率。单位: 1/s。
                (反应的速率定义为：对于1kg的总的反应物质，在1s内，左侧物质质量的较少量)
                小于0的q表示反应是逆向的（右侧物质质量减少）
                注意这个速率后续需要根据exp以及组分的浓度来矫正
        注意:
            一般地，对于吸热反应，随着温度的增加，反应的速率应当增加；
            反之，对于放热反应，随着温度的降低，反应的速率降低；
        """
        handle = core.reaction_get_t2q(self.handle)
        return Interp1(handle=handle)

    core.use(c_void_p, 'reaction_get_t2qr', c_void_p)

    @property
    def t2qr(self) -> Interp1:
        """
        一条曲线，表示不同的温度(实际温度减去基准温度)下的逆向反应速率。参考t2q的说明。
        """
        handle = core.reaction_get_t2qr(self.handle)
        return Interp1(handle=handle)

    def add_component(self, index: List[int], weight: float, fa_t: int, fa_c: int):
        """
        添加一种反应物质。

        Args:
            index: Seepage.Cell中定义的流体组分的序号。
            weight: 发生1kg的反应的时候此物质变化的质量，
                其中左侧物质的weight为负值，右侧为正值。
            fa_t (int): 定义流体温度的属性ID。
            fa_c (int): 定义流体比热的属性ID。

        Raises:
            AssertionError: 如果fa_t或fa_c为None，或者weight的绝对值大于1.00001。
        """
        idx = self.component_n
        self.component_n = idx + 1
        comp = self.get_component(idx)

        comp.index = parse_fid(index)

        assert fa_t is not None, "fa_t must be not None"
        comp.fa_t = fa_t

        assert fa_c is not None, "fa_c must be not None"
        comp.fa_c = fa_c

        assert abs(weight) <= 1.00001, "weight must be smaller than 1"
        comp.weight = weight

    def clear_components(self) -> None:
        """
        清除所有的反应组分。
        """
        self.component_n = 0

    core.use(c_size_t, 'reaction_get_component_n', c_void_p)

    @property
    def component_n(self) -> int:
        """
        反应组分的数量。
        """
        return core.reaction_get_component_n(self.handle)

    core.use(None, 'reaction_set_component_n', c_void_p, c_size_t)

    @component_n.setter
    def component_n(self, value: int):
        """
        反应组分的数量。
        """
        core.reaction_set_component_n(self.handle, value)

    core.use(c_void_p, 'reaction_get_component', c_void_p, c_size_t)

    def get_component(self, index: int) -> Optional['Reaction.Component']:
        """
        获取指定索引的反应组分。
        """
        idx_ = get_index(index, count=self.component_n)
        if idx_ is None:
            return None
        else:
            return Reaction.Component(
                handle=core.reaction_get_component(self.handle, idx_))

    @property
    def components(self) -> Iterable['Reaction.Component']:
        """
        迭代所有的组分
        """
        return Iterator(self, self.component_n,
                        lambda m, ind: m.get_component(ind))

    def add_inhibitor(self, *args, **kwargs):
        warnings.warn(
            'Reaction.add_inhibitor will be removed after 2026-5-31, '
            'use zmlx.react.alg.add_inhibitor instead',
            DeprecationWarning, stacklevel=2)
        from zmlx.react import alg
        return alg.add_inhibitor(self, *args, **kwargs)

    def clear_inhibitors(self):
        """
        清除所有的抑制剂定义。
        """
        self.inhibitor_n = 0

    core.use(c_size_t, 'reaction_get_inh_n', c_void_p)

    @property
    def inhibitor_n(self) -> int:
        """
        抑制剂的数量。
        """
        return core.reaction_get_inh_n(self.handle)

    core.use(None, 'reaction_set_inh_n', c_void_p, c_size_t)

    @inhibitor_n.setter
    def inhibitor_n(self, value: int):
        """
        设置抑制剂的数量。
        """
        core.reaction_set_inh_n(self.handle, value)

    core.use(c_void_p, 'reaction_get_inh', c_void_p, c_size_t)

    def get_inhibitor(self, index: int) -> Optional['Reaction.Inhibitor']:
        """
        获取指定索引的抑制剂。
        """
        idx_ = get_index(index, count=self.inhibitor_n)
        if idx_ is None:
            return None
        else:
            return Reaction.Inhibitor(
                handle=core.reaction_get_inh(self.handle, idx_))

    @property
    def inhibitors(self) -> Iterable['Reaction.Inhibitor']:
        """
        迭代所有的抑制剂
        """
        return Iterator(self, self.inhibitor_n,
                        lambda m, ind: m.get_inhibitor(ind))

    core.use(None, 'reaction_react', c_void_p, c_void_p, c_double, c_void_p, c_void_p)

    def react(self, model: 'Seepage', dt: float, buf=None, pool: Optional[ThreadPool] = None):
        """
        将该反应作用到Seepage的所有的Cell上dt时间。

        Args:
            model (Seepage): Seepage模型对象。
            dt (float): 时间步长。
            buf (Any, optional): 一个缓冲区(double*)，
                记录各个Cell上发生的反应的质量。务必确保此缓冲区的大小足够，
                否则会出现致命的错误。默认为None。
            pool: 线程池
        """
        self.adjust_weights()  # 确保权重正确，保证质量守恒
        handle = pool.handle if isinstance(pool, ThreadPool) else 0
        core.reaction_react(
            self.handle, model.handle, dt,
            0 if buf is None else ctypes.cast(buf, c_void_p),
            handle
        )

    core.use(None, 'reaction_adjust_weights', c_void_p)

    def adjust_weights(self):
        """
        等比例地调整权重。确保方程左侧系数加和之后等于-1，右侧的系数加和之后等于1.
        """
        core.reaction_adjust_weights(self.handle)

    def adjust_widghts(self):
        """
        同adjust_weights （曾经单纯的拼写错误）

        Warnings:
            此方法已弃用，将在2024-1-1之后移除，请使用 <adjust_weights>。
        """
        warnings.warn(
            'Use <adjust_weights>. <adjust_widghts> will be '
            'removed after 2024-1-1',
            DeprecationWarning, stacklevel=2)
        self.adjust_weights()

    core.use(c_double, 'reaction_get_rate', c_void_p, c_void_p)

    def get_rate(self, cell: 'CellData') -> float:
        """
        获得给定Cell在当前状态(温度、压力、抑制剂等条件)下的<瞬时的>反应速率。
        此函数主要用来测试

        Args:
            cell (CellData): Seepage的CellData对象。

        Returns:
            float: 反应速率。
        """
        assert isinstance(cell, CellData), 'cell must be a CellData object'
        return core.reaction_get_rate(self.handle, cell.handle)

    core.use(None, 'reaction_set_idt', c_void_p, c_size_t)
    core.use(c_size_t, 'reaction_get_idt', c_void_p)

    @property
    def idt(self) -> int:
        """
        Cell的属性ID。Cell的此属性用以定义反应作用到该Cell上的时候，基准温度的调整量。
        这允许在不同的Cell上，有不同的基准温度（而不仅仅是压力的函数）。
        在使用p2t计算了基准温度之后，将额外附加上idt的属性值.
        默认情况下，此属性不定义，则反应在各个Cell上的基准温度是一样的。

        Notes:
            此属性为一个测试功能，当后续有更好的实现方案的时候，可能会被移除。

        Returns:
            int: Cell的属性ID。
        """
        return core.reaction_get_idt(self.handle)

    @idt.setter
    def idt(self, value: int):
        """
        设置Cell的属性ID。

        Args:
            value (int): Cell的属性ID。
        """
        core.reaction_set_idt(self.handle, value)

    core.use(None, 'reaction_set_wdt', c_void_p, c_double)
    core.use(c_double, 'reaction_get_wdt', c_void_p)

    @property
    def wdt(self) -> float:
        """
        和idt配合使用。在Cell定义温度调整量的时候， 可以利用这个权重再对这个调整量进行（缩放）调整。
        比如，当Cell给的温度的调整量的单位不是K的时候， 可以利用wdt属性来添加一个倍率。
        默认为1，即不进行缩放处理。

        Notes:
            此属性为一个测试功能，当后续有更好的实现方案的时候，可能会被移除。

        Returns:
            float: 权重。
        """
        return core.reaction_get_wdt(self.handle)

    @wdt.setter
    def wdt(self, value: float):
        """
        设置idt的权重（缩放系数）

        Args:
            value (float): 权重。
        """
        core.reaction_set_wdt(self.handle, value)

    core.use(None, 'reaction_set_irate', c_void_p, c_size_t)
    core.use(c_size_t, 'reaction_get_irate', c_void_p)

    @property
    def irate(self) -> int:
        """
        Cell的属性ID。Cell的此属性用以定义反应作用到该Cell上的时候，
        反应速率应该乘以的倍数。
        若定义这个属性，且Cell的这个属性值小于等于0，那么反应在这个Cell上将不会发生。

        Notes:
            如果希望某个反应只在部分Cell上发生，则可以利用这个属性来实现。

        Returns:
            int: Cell的属性ID。
        """
        return core.reaction_get_irate(self.handle)

    @irate.setter
    def irate(self, value: int):
        """
        设置Cell的属性ID。

        Args:
            value (int): Cell的属性ID。
        """
        core.reaction_set_irate(self.handle, value)

    core.use(None, 'reaction_clone', c_void_p, c_void_p)

    def clone(self, other: Optional['Reaction'] = None) -> 'Reaction':
        """
        拷贝所有的数据。

        Args:
            other (Reaction): 要拷贝的Reaction对象。

        Returns:
            Reaction: 拷贝后的Reaction对象。
        """
        if other is not None:
            assert isinstance(other, Reaction), 'other must be a Reaction object in clone'
            core.reaction_clone(self.handle, other.handle)
        return self

    def get_copy(self) -> 'Reaction':
        """
        返回一个拷贝(而非一个引用)。

        Returns:
            Reaction: 拷贝后的Reaction对象。
        """
        result = Reaction()
        result.clone(self)
        return result

    core.use(c_char_p, 'reaction_get_name', c_void_p)
    core.use(None, 'reaction_set_name', c_void_p, c_char_p)

    @property
    def name(self) -> str:
        """
        反应的名字（字符串），主要用于区分不同的反应，不参与任何计算
        """
        return core.reaction_get_name(self.handle).decode()

    @name.setter
    def name(self, value: str):
        """
        反应的名字（字符串），主要用于区分不同的反应，不参与任何计算
        """
        core.reaction_set_name(self.handle, make_c_char_p(value))


class FluDef(HasHandle):
    """
    流体定义。在本程序中，我们假设流体的密度和粘性系数都是压力和温度的函数，
        并且利用二维插值来存储。
        比热容被视为常数(这可能不严谨，但是大多数情况下够用).
    流体定义被存储在Seepage中，被所有的Cell所共用。
    """
    core.use(c_void_p, 'new_fludef')
    core.use(None, 'del_fludef', c_void_p)

    def __init__(self, den: Union[float, Interp2] = 1000.0,
                 vis: Union[float, Interp2] = 1.0e-3,
                 specific_heat: float = 4200.0,
                 name: Optional[str] = None, path: Optional[str] = None, handle: Optional[c_void_p] = None
                 ):
        """
        构造函数。

        Args:
            den (float or Interp2, optional): 流体密度，
                当为None时清除C++层面的默认数据。默认为1000.0。
            vis (float or Interp2, optional): 流体粘性，
                当为None时清除C++层面的默认数据。默认为1.0e-3。
            specific_heat (float, optional): 流体比热容。
                默认为4200。
            name (str, optional): 流体名称。默认为None。
            path (str, optional): 加载流体定义的文件路径。
                默认为None。
            handle (c_void_p, optional): 指向底层C对象的句柄。
                如果为None，则根据其他参数初始化；否则创建当前数据的引用。
                默认为None。
        """
        super().__init__(handle, core.new_fludef, core.del_fludef)
        if handle is None:
            # 现在，这是一个新建数据，将进行必要的初始化
            if isinstance(path, str):
                self.load(path)
            else:
                self.den = den  # 即便给定的数据为None，也将使用(清除当前数据)
                self.vis = vis  # 即便给定的数据为None，也将使用(清除当前数据)
                if specific_heat is not None:
                    self.specific_heat = specific_heat
            # 只要给定name，无论是load，还是create，都修改name
            if name is not None:
                self.name = name
        else:
            assert path is None

    def __repr__(self) -> str:
        """
        返回一个字符串表示当前对象。
        """
        return f"""{type(self).__name__}(handle={int(self.handle)}, name='{self.name}')"""

    def __str__(self) -> str:
        """
        返回一个字符串表示当前对象。
        """
        name = self.name
        if len(name) == 0:
            name = "unnamed"
        if self.component_number == 0:
            return name
        else:
            text = ", ".join([str(c) for c in self.components])
            return f"{name}({text})"

    core.use(None, 'fludef_save', c_void_p, c_char_p)

    def save(self, path: str):
        """
        序列化保存。

        Args:
            path (str): 保存文件的路径。

        Notes:
            可选扩展格式：
            1：.txt
                .TXT 格式（跨平台，基本不可读）
            2：.xml
                .XML 格式（特定可读性，文件体积最大，读写速度最慢，跨平台）
            3：.其他
                二进制格式（最快且最小，但在 Windows 和 Linux
                下生成的文件无法互相读取）
        """
        if isinstance(path, str):
            make_parent(path)
            core.fludef_save(self.handle, make_c_char_p(path))

    core.use(None, 'fludef_load', c_void_p, c_char_p)

    def load(self, path: str):
        """
        读取序列化文件。

        Args:
            path (str): 读取文件的路径。

        Notes:
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.fludef_load(self.handle, make_c_char_p(path))

    core.use(None, 'fludef_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'fludef_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt: str = 'binary') -> FileMap:
        """
        将数据序列化到一个Filemap中。

        Args:
            fmt (str, optional): 序列化格式，取值可以为 'text', 'xml'
                和 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的FileMap对象。
        """
        fmap = FileMap()
        core.fludef_write_fmap(
            self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt: str = 'binary'):
        """
        从Filemap中读取序列化的数据。

        Args:
            fmap (FileMap): 包含序列化数据的FileMap对象。
            fmt (str, optional): 序列化格式，取值可以为 'text', 'xml'
                和 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.fludef_read_fmap(
            self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self) -> FileMap:
        """
        返回一个二进制的FileMap对象。

        Returns:
            FileMap: 包含二进制序列化数据的FileMap对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: FileMap):
        """
        从二进制的FileMap对象中读取序列化的数据。

        Args:
            value (FileMap): 包含二进制序列化数据的FileMap对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(c_void_p, 'fludef_get_den', c_void_p)

    @property
    def den(self) -> Interp2:
        """
        流体密度的插值。

        Returns:
            Interp2: 流体密度的插值对象。

        Raises:
            AssertionError: 如果组分的数量不为0。
        """
        assert self.component_number == 0
        return Interp2(handle=core.fludef_get_den(self.handle))

    @den.setter
    def den(self, value: Optional[Union[float, Interp2]] = None):
        """
        设置密度数据。

        Args:
            value (float or Interp2, optional): 密度数据，
                当为None时清除现有数据。

        Raises:
            AssertionError: 如果组分的数量不为0，或者给定的非插值数据不在有效范围内。
        """
        assert self.component_number == 0
        if value is None:
            self.den.clear()
        else:
            if isinstance(value, Interp2):
                self.den.clone(value)
            else:  # 转化为二维插值
                assert 1.0e-3 < value <= 1.0e7
                itp = Interp2.create_const(value)
                self.den.clone(itp)

    core.use(c_void_p, 'fludef_get_vis', c_void_p)

    @property
    def vis(self) -> Interp2:
        """
        流体粘性的插值。

        Returns:
            Interp2: 流体粘性的插值对象。

        Raises:
            AssertionError: 如果组分的数量不为0。
        """
        assert self.component_number == 0
        return Interp2(handle=core.fludef_get_vis(self.handle))

    @vis.setter
    def vis(self, value: Optional[Union[float, Interp2]] = None):
        """
        设置粘性数据。

        Args:
            value (float or Interp2, optional): 粘性数据，
                当为None时清除现有数据。

        Raises:
            AssertionError: 如果组分的数量不为0，或者给定的非插值数据不在有效范围内。
        """
        assert self.component_number == 0
        if value is None:
            self.vis.clear()
        else:
            if isinstance(value, Interp2):
                self.vis.clone(value)
            else:  # 转化为二维插值
                assert 1.0e-7 < value < 1.0e40
                itp = Interp2.create_const(value)
                self.vis.clone(itp)

    def get_den(self, pressure: float, temp: float) -> float:
        """
        返回给定压力和温度下的密度。

        Args:
            pressure (float): 压力值。
            temp (float): 温度值。

        Returns:
            float: 给定压力和温度下的密度。
        """
        return self.den(pressure, temp)

    def get_vis(self, pressure: float, temp: float) -> float:
        """
        返回给定压力和温度下的粘性。

        Args:
            pressure (float): 压力值。
            temp (float): 温度值。

        Returns:
            float: 给定压力和温度下的粘性。
        """
        return self.vis(pressure, temp)

    core.use(c_double, 'fludef_get_specific_heat', c_void_p)

    @property
    def specific_heat(self) -> float:
        """
        流体的比热(常数)。

        Returns:
            float: 流体的比热。

        Raises:
            AssertionError: 如果组分的数量不为0。
        """
        assert self.component_number == 0
        return core.fludef_get_specific_heat(self.handle)

    core.use(None, 'fludef_set_specific_heat', c_void_p, c_double)

    @specific_heat.setter
    def specific_heat(self, value: float):
        """
        设置流体的比热。

        Args:
            value (float): 流体的比热。

        Raises:
            AssertionError: 如果组分的数量不为0，或者给定的值不在有效范围内。
        """
        assert self.component_number == 0
        assert 0.1 <= value <= 1.0e8
        core.fludef_set_specific_heat(self.handle, value)

    core.use(c_size_t, 'fludef_get_component_number', c_void_p)

    @property
    def component_number(self) -> int:
        """
        流体组分的数量。

        Returns:
            int: 流体组分的数量。
        """
        return core.fludef_get_component_number(self.handle)

    core.use(None, 'fludef_set_component_number', c_void_p, c_size_t)

    @component_number.setter
    def component_number(self, value: int):
        """
        设置流体组分的数量。

        Args:
            value (int): 流体组分的数量。
        """
        core.fludef_set_component_number(self.handle, value)

    core.use(c_void_p, 'fludef_get_component', c_void_p, c_size_t)

    def get_component(self, index: int) -> Optional['FluDef']:
        """
        返回流体的组分。

        Args:
            index (int): 组分的索引。

        Returns:
            FluDef: 流体的组分对象，如果索引有效；否则返回None。
        """
        idx_ = get_index(index, self.component_number)
        if idx_ is not None:
            return FluDef(
                handle=core.fludef_get_component(self.handle, idx_))
        else:
            return None

    def clear_components(self):
        """
        清除所有的组分。
        """
        self.component_number = 0

    def add_component(self, flu: 'FluDef', name: Optional[str] = None):
        """
        添加流体组分，并返回组分的ID。

        Args:
            flu (FluDef): 要添加的流体组分对象。
            name (str, optional): 流体组分的名称。默认为None。

        Returns:
            int: 新添加组分的ID。
        """
        assert isinstance(flu, FluDef)
        idx = self.component_number
        self.component_number = idx + 1
        temp = self.get_component(idx)
        assert isinstance(temp, FluDef), f'get_component failed at index {idx}'
        temp.clone(flu)
        if name is not None:
            temp.name = name
        return idx

    @property
    def components(self) -> Iterable['FluDef']:
        return Iterator(self, self.component_number, lambda m, i: m.get_component(i))

    @staticmethod
    def create(defs: Union['FluDef', List['FluDef']], name: str = None) -> 'FluDef':
        """
        将存储在list中的多个流体的定义，组合成为一个具有多个组分的单个流体定义。

        Args:
            defs (list or FluDef): 流体定义列表或单个流体定义对象。
            name (str, optional): 返回的流体定义的名称。默认为None。

        Returns:
            FluDef: 组合后的流体定义对象。

        Notes:
            当给定name的时候，则返回的数据使用此name。
            此函数将返回给定数据的拷贝，因此，原始的数据并不会被引用和修改。
        """
        if isinstance(defs, FluDef):
            return defs.get_copy(name=name)
        else:
            result = FluDef(name=name)
            for x in defs:
                result.add_component(FluDef.create(x))
            return result

    core.use(c_char_p, 'fludef_get_name', c_void_p)

    @property
    def name(self) -> str:
        """
        流体组分的名称。

        Returns:
            str: 流体组分的名称。
        """
        return core.fludef_get_name(self.handle).decode()

    core.use(None, 'fludef_set_name', c_void_p, c_char_p)

    @name.setter
    def name(self, value: str):
        """
        设置流体组分的名称。

        Args:
            value (str): 流体组分的名称。
        """
        core.fludef_set_name(self.handle, make_c_char_p(value))

    core.use(None, 'fludef_clone', c_void_p, c_void_p)

    def clone(self, other: Optional['FluDef'] = None) -> 'FluDef':
        """
        克隆数据。

        Args:
            other (FluDef, optional): 要克隆的FluDef对象。默认为None。

        Returns:
            FluDef: 克隆后的FluDef对象。
        """
        if other is not None:
            assert isinstance(other, FluDef)
            core.fludef_clone(self.handle, other.handle)
        return self

    def get_copy(self, name: Optional[str] = None) -> 'FluDef':
        """
        返回当前数据的一个拷贝。

        Args:
            name (str, optional): 拷贝后的数据的名称。默认为None。

        Returns:
            FluDef: 拷贝后的FluDef对象。
        """
        result = FluDef()
        result.clone(self)
        if name is not None:
            result.name = name
        return result


class FluData(HasHandle):
    """
    流体数据(存储在Cell中)。一个流体数据由以下属性组成：
    1、流体的质量、密度、粘性系数。
    2、流体的自定义属性。
        在FluData内存储一个浮点型的数组，存储一系列自定义的属性，
        用于辅助存储和计算。自定义属性从0开始编号。
    3、流体的组分。
        流体的组分亦采用FluData类进行定义（即FluData为一个嵌套的类），
        因此，流体的组分也具有和流体同样的数据。流体的组分存储在
        一个数组内，且从0开始编号。当流体的组分数量不为0的时候，
        则存储在流体自身的数据自动失效，并利用组分的属性来自动计算
        这些组分作为一个整体的属性。如：流体的质量等于各个组分的质量之和，
        体积等于各个组分的体积之和，自定义属性则等于不同组分
        根据质量的加权平均。
    """
    core.use(c_void_p, 'new_fluid')
    core.use(None, 'del_fluid', c_void_p)

    def __init__(self, mass: Optional[float] = None, den: Optional[float] = None, vis: Optional[float] = None,
                 vol: Optional[float] = None, handle: Optional[c_void_p] = None):
        """
        创建给定handle的引用，或者创建流体数据。

        Args:
            mass (float, optional): 流体的质量，单位为kg。默认为None。
            den (float, optional): 流体的密度，单位为kg/m^3。默认为None。
            vis (float, optional): 流体的粘性系数，单位为Pa.s。默认为None。
            vol (float, optional): 流体的体积，单位为m^3。默认为None。
            handle (c_void_p, optional): 流体数据的句柄。默认为None。
        """
        super().__init__(handle, core.new_fluid,
                         core.del_fluid)
        if handle is None:
            if mass is not None:
                self.mass = mass
            if den is not None:
                self.den = den
            if vis is not None:
                self.vis = vis
            if vol is not None:
                assert mass is None
                self.vol = vol
        else:
            assert (mass is None and den is None
                    and vis is None and vol is None)

    core.use(None, 'fluid_save', c_void_p, c_char_p)

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
            core.fluid_save(self.handle, make_c_char_p(path))

    core.use(None, 'fluid_load', c_void_p, c_char_p)

    def load(self, path: str):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 读取文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.fluid_load(self.handle, make_c_char_p(path))

    core.use(None, 'fluid_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'fluid_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt: str = 'binary') -> FileMap:
        """
        将数据序列化到一个Filemap中。其中fmt的取值可以为: text, xml和binary。

        Args:
            fmt (str, optional): 序列化的格式，可选值为'text', 'xml'
                和'binary'。默认为'binary'。

        Returns:
            FileMap: 序列化后的FileMap对象。
        """
        fmap = FileMap()
        core.fluid_write_fmap(
            self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt: str = 'binary'):
        """
        从Filemap中读取序列化的数据。其中fmt的取值可以为: text, xml和binary。

        Args:
            fmap (FileMap): 包含序列化数据的FileMap对象。
            fmt (str, optional): 反序列化的格式，可选值为'text', 'xml'
                和'binary'。默认为'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.fluid_read_fmap(
            self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self) -> FileMap:
        """
        获取二进制格式的序列化数据。

        Returns:
            FileMap: 二进制格式的序列化数据。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: FileMap):
        """
        设置二进制格式的序列化数据。

        Args:
            value (FileMap): 二进制格式的序列化数据。
        """
        self.from_fmap(value, fmt='binary')

    core.use(c_double, 'fluid_get_mass', c_void_p)
    core.use(None, 'fluid_set_mass', c_void_p, c_double)

    @property
    def mass(self) -> float:
        """
        流体的质量，单位为kg。

        Returns:
            float: 流体的质量。
        """
        return core.fluid_get_mass(self.handle)

    @mass.setter
    def mass(self, value: float):
        """
        设置流体的质量，单位为kg。

        Args:
            value (float): 流体的质量，必须大于等于0。
        """
        assert value >= 0
        core.fluid_set_mass(self.handle, value)

    core.use(c_double, 'fluid_get_vol', c_void_p)
    core.use(None, 'fluid_set_vol', c_void_p, c_double)

    @property
    def vol(self) -> float:
        """
        流体的体积，单位为m^3。
        注意:
            内核中并不存储流体体积，而是根据质量和密度计算得到的。

        Returns:
            float: 流体的体积。
        """
        return core.fluid_get_vol(self.handle)

    @vol.setter
    def vol(self, value: float):
        """
        修改流体的体积，单位为m^3。
        注意:
            内核中并不存储流体体积，而是根据质量和密度计算得到的。
            将修改mass，并保持density不变。

        Args:
            value (float): 流体的体积，必须大于等于0。
        """
        assert value >= 0
        core.fluid_set_vol(self.handle, value)

    core.use(c_double, 'fluid_get_den', c_void_p)
    core.use(None, 'fluid_set_den', c_void_p, c_double)

    @property
    def den(self) -> float:
        """
        流体密度，单位为kg/m^3。
            注意: 流体不可压缩，除非外部修改，否则密度永远维持不变。
        假设：
            在计算的过程中，流体的密度不会发生剧烈的变化，
            因此，在一次迭代的过程中，流体的密度可以
            视为不变的。在一次迭代之后，可以根据最新的温度和压力来更新流体的密度。
        注意：
            在利用TherFlowConfig来iterate的时候，
            如果模型中存储了流体的定义，那么流体密度的
            更新会被自动调用，从而保证流体的密度总是最新的。

        Returns:
            float: 流体的密度。
        """
        return core.fluid_get_den(self.handle)

    @den.setter
    def den(self, value: float):
        """
        设置流体的密度，单位为kg/m^3。

        Args:
            value (float): 流体的密度，必须大于0。
        """
        assert value > 0
        core.fluid_set_den(self.handle, value)

    core.use(c_double, 'fluid_get_vis', c_void_p)
    core.use(None, 'fluid_set_vis', c_void_p, c_double)

    @property
    def vis(self) -> float:
        """
        流体粘性系数，单位为Pa.s。
            注意: 除非外部修改，否则vis维持不变。
        流体粘性的更新规则和密度相似。

        Returns:
            float: 流体的粘性系数。
        """
        return core.fluid_get_vis(self.handle)

    @vis.setter
    def vis(self, value: float):
        """
        设置流体的粘性系数，单位为Pa.s。

        Args:
            value (float): 流体的粘性系数，必须大于0。
        """
        assert value > 0
        core.fluid_set_vis(self.handle, value)

    @property
    def is_solid(self) -> bool:
        """
        该流体单元在计算内核中是否可以被视为固体。
        注意：
            该属性将被弃用。

        Returns:
            bool: 如果流体的粘性系数大于等于0.5e30，则返回True；
            否则返回False。
        """
        warnings.warn('FluData.is_solid will be deleted '
                      'after 2024-5-5',
                      DeprecationWarning, stacklevel=2)
        return self.vis >= 0.5e30

    core.use(c_double, 'fluid_get_attr', c_void_p, c_size_t)
    core.use(None, 'fluid_set_attr', c_void_p, c_size_t, c_double)

    def get_attr(self, index: Union[int, str], default_val: Optional[float] = None, **valid_range):
        """
        获取第index个流体自定义属性。当两个流体数据相加时，
        自定义属性将根据质量进行加权平均。

        Args:
            index (int or str): 自定义属性的索引或键。
            default_val (float, optional): 当属性不存在
                或不在有效范围内时返回的默认值。默认为None。
            **valid_range: 自定义属性的有效范围。

        Returns:
            float: 自定义属性的值，如果不存在或不在有效范围内，则返回默认值。
        """
        if isinstance(index, str):
            assert isinstance(self, Fluid)
            assert isinstance(self.cell, Cell)
            index = self.cell.model.get_flu_key(key=index)
        if index is None:
            return default_val
        # 当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
        value = core.fluid_get_attr(self.handle, index)
        if attr_in_range(value, **valid_range):
            return value
        else:
            return default_val

    def set_attr(self, index: Union[int, str], value: Optional[float] = None) -> 'FluData':
        """
        设置第index个流体自定义属性。参考get_attr函数。

        Args:
            index (int or str): 自定义属性的索引或键。
            value (float): 自定义属性的值。

        Returns:
            FluData: 返回当前对象。
        """
        if isinstance(index, str):
            assert isinstance(self, Fluid)
            assert isinstance(self.cell, Cell)
            index = self.cell.model.reg_flu_key(key=index)
        if index is None:
            return self
        if value is None:
            value = 1.0e200
        core.fluid_set_attr(self.handle, index, value)
        return self

    core.use(None, 'fluid_clone',
             c_void_p, c_void_p)

    def clone(self, other: Optional['FluData'] = None) -> 'FluData':
        """
        拷贝所有的数据。

        Args:
            other (FluData): 要拷贝的FluData对象。

        Returns:
            FluData: 返回当前对象。
        """
        if other is not None:
            assert isinstance(other, FluData)
            core.fluid_clone(self.handle, other.handle)
        return self

    def get_copy(self, mass: Optional[float] = None) -> 'FluData':
        """
        获取当前对象的拷贝。

        Returns:
            FluData: 当前对象的拷贝。
        """
        result = FluData()
        result.clone(self)
        if mass is not None:
            result.mass = mass
        return result

    core.use(None, 'fluid_add', c_void_p, c_void_p)

    def add(self, other: 'FluData'):
        """
        将other所定义的流体数据添加到self。注意，并不是添加组分。
        类似于: self = self + other。
        比如:
            若self的质量为1kg，other的质量也为1kg，
            则当执行了此函数之后，self的质量会成为2kg，而other保持不变。

        Args:
            other (FluData): 要添加的FluData对象。
        """
        assert isinstance(other, FluData)
        core.fluid_add(self.handle, other.handle)

    core.use(c_size_t, 'fluid_get_component_number', c_void_p)

    @property
    def component_number(self) -> int:
        """
        流体组分的数量。当流体不可再分的时候，组分数量为0；
        否则，流体被视为混合物，且组分的数量大于0。

        Returns:
            int: 流体组分的数量。
        """
        return core.fluid_get_component_number(self.handle)

    core.use(None, 'fluid_set_component_number', c_void_p, c_size_t)

    @component_number.setter
    def component_number(self, value: int):
        """
        设置流体组分的数量。

        Args:
            value (int): 流体组分的数量。
        """
        core.fluid_set_component_number(self.handle, value)

    core.use(c_void_p, 'fluid_get_component', c_void_p, c_size_t)

    def get_component(self, index: int) -> Optional['FluData']:
        """
        返回给定的组分。

        Args:
            index (int): 组分的索引。

        Returns:
            FluData: 给定索引的组分对象，如果索引无效则返回None。
        """
        idx_ = get_index(index, self.component_number)
        if idx_ is not None:
            return FluData(
                handle=core.fluid_get_component(self.handle, idx_))
        else:
            return None

    core.use(None, 'fluid_clear_components',
             c_void_p)

    def clear_components(self):
        """
        清除所有的组分。
        """
        core.fluid_clear_components(self.handle)

    core.use(c_size_t, 'fluid_add_component', c_void_p, c_void_p)

    def add_component(self, flu: 'FluData') -> int:
        """
        添加流体组分，并返回组分的ID。

        Args:
            flu (FluData): 要添加的流体组分对象。

        Returns:
            int: 新添加组分的ID。
        """
        assert isinstance(flu, FluData)
        return core.fluid_add_component(self.handle, flu.handle)

    core.use(None, 'fluid_set_property',
             c_void_p, c_double, c_size_t,
             c_size_t, c_void_p)

    def set_property(self, p: float, fa_t: int, fa_c: int, fdef: 'FluDef'):
        """
        在给定压力和由 <fa_T> 定义的流体温度下，设置流体的密度、粘度和比热。

        Args:
            p (float): 压力。
            fa_t (int): 流体温度的索引。
            fa_c (int): 流体组分的索引。
            fdef (FluDef): 流体定义对象。
        """
        assert isinstance(fdef, FluDef)
        core.fluid_set_property(self.handle, p, fa_t, fa_c, fdef.handle)

    core.use(None, 'fluid_set_components', c_void_p, c_void_p)

    def set_components(self, fdef: 'FluDef'):
        """
        按照fdef的定义来设置流体的组分的数量，从而使得这个流体数据和给定的
        流体定义具有相同的结构。

        Args:
            fdef (FluDef): 流体定义对象。
        """
        assert isinstance(fdef, FluDef)
        core.fluid_set_components(self.handle, fdef.handle)


class Fluid(FluData):
    core.use(c_void_p, 'seepage_cell_get_fluid', c_void_p, c_size_t)

    def __init__(self, cell: "CellData", fid: int):
        """
        初始化Fluid对象。

        Args:
            cell (CellData): 流体所在的Cell对象。
            fid (int): 流体在Cell中的编号，必须小于Cell内流体的数量。
        """
        assert isinstance(cell, CellData)
        assert isinstance(fid, int)
        assert fid < cell.fluid_number
        self.cell = cell
        self.fid = fid
        super().__init__(handle=core.seepage_cell_get_fluid(self.cell.handle, self.fid))

    @property
    def vol_fraction(self) -> float:
        """
        流体的体积占Cell内所有流体总体积的比例。

        Returns:
            float: 流体的体积占比。
        """
        res = self.cell.get_fluid_vol_fraction(self.fid)
        assert res is not None
        return res


class CellData(HasHandle):
    """
    CellData类用于管理和操作控制体（Cell）的数据。

    该类提供了一系列方法用于序列化保存和加载数据，
    设置和获取Cell的位置、孔隙参数、流体属性等。
    """
    core.use(c_void_p, 'new_seepage_cell')
    core.use(None, 'del_seepage_cell', c_void_p)

    def __init__(self, path: Optional[str] = None, handle: Optional[c_void_p] = None):
        """
        初始化CellData对象。

        Args:
            path (str, optional): 用于加载数据的文件路径。默认为None。
            handle (c_void_p, optional): 指向底层数据的句柄。默认为None。
        """
        super().__init__(
            handle,
            core.new_seepage_cell,
            core.del_seepage_cell)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'seepage_cell_save', c_void_p, c_char_p)

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
            core.seepage_cell_save(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_cell_load', c_void_p, c_char_p)

    def load(self, path: str):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 读取文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.seepage_cell_load(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_cell_write_fmap',
             c_void_p, c_void_p, c_char_p)
    core.use(None, 'seepage_cell_read_fmap',
             c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt: str = 'binary') -> FileMap:
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary

        Args:
            fmt (str, optional): 序列化格式，
                可选值为 'text', 'xml', 'binary'。默认为 'binary'。

        Returns:
            FileMap: 序列化后的FileMap对象。
        """
        fmap = FileMap()
        core.seepage_cell_write_fmap(self.handle, fmap.handle,
                                     make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt: str = 'binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary

        Args:
            fmap (FileMap): 包含序列化数据的FileMap对象。
            fmt (str, optional): 反序列化格式，
                可选值为 'text', 'xml', 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.seepage_cell_read_fmap(self.handle, fmap.handle,
                                    make_c_char_p(fmt))

    @property
    def fmap(self) -> FileMap:
        """
        获取当前Cell对象的二进制格式FileMap对象。

        Returns:
            FileMap: 二进制格式的FileMap对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: FileMap):
        """
        通过FileMap对象设置当前Cell对象的数据。

        Args:
            value (FileMap): 包含序列化数据的FileMap对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(c_double, 'seepage_cell_get_pos',
             c_void_p, c_size_t)
    core.use(None, 'seepage_cell_set_pos',
             c_void_p, c_size_t, c_double)

    @property
    def x(self) -> float:
        """
        在三维空间中的x坐标

        Returns:
            float: x坐标的值。
        """
        return core.seepage_cell_get_pos(self.handle, 0)

    @x.setter
    def x(self, value: float):
        """
        设置在三维空间中的x坐标。

        Args:
            value (float): 新的x坐标的值。
        """
        core.seepage_cell_set_pos(self.handle, 0, value)

    @property
    def y(self) -> float:
        """
        在三维空间中的y坐标

        Returns:
            float: y坐标的值。
        """
        return core.seepage_cell_get_pos(self.handle, 1)

    @y.setter
    def y(self, value: float):
        """
        设置在三维空间中的y坐标。

        Args:
            value (float): 新的y坐标的值。
        """
        core.seepage_cell_set_pos(self.handle, 1, value)

    @property
    def z(self) -> float:
        """
        在三维空间中的z坐标

        Returns:
            float: z坐标的值。
        """
        return core.seepage_cell_get_pos(self.handle, 2)

    @z.setter
    def z(self, value: float):
        """
        设置在三维空间中的z坐标。

        Args:
            value (float): 新的z坐标的值。
        """
        core.seepage_cell_set_pos(self.handle, 2, value)

    @property
    def pos(self) -> List[float]:
        """
        该Cell在三维空间的坐标

        Returns:
            list: 包含x、y、z坐标的列表。
        """
        return [core.seepage_cell_get_pos(self.handle, i)
                for i in range(3)]

    @pos.setter
    def pos(self, value: Union[List[float], Tuple[float]]):
        """
        设置该Cell在三维空间的坐标。

        Args:
            value (list or tuple of float): 包含x、y、z坐标的列表或元组，长度必须为3。
        """
        assert len(value) == 3
        for dim in range(3):
            core.seepage_cell_set_pos(self.handle, dim, value[dim])

    def distance(self, other):
        """
        返回距离另外一个Cell或者另外一个位置的距离

        Args:
            other (CellData or list): 另一个Cell对象或者包含坐标的列表。

        Returns:
            float: 两个对象之间的距离。
        """
        if hasattr(other, 'pos'):
            return get_distance(self.pos, other.pos)
        else:
            return get_distance(self.pos, other)

    core.use(c_double, 'seepage_cell_get_v0', c_void_p)
    core.use(None, 'seepage_cell_set_v0', c_void_p, c_double)

    @property
    def v0(self) -> float:
        """
        当流体压力等于0时，该Cell内流体的存储空间 m^3.
        注意:
            务必设置合适的刚度和孔隙度，使得v0的数值大于0

        Returns:
            float: 流体存储空间的值。
        """
        return core.seepage_cell_get_v0(self.handle)

    @v0.setter
    def v0(self, value: float):
        """
        设置当流体压力等于0时，该Cell内流体的存储空间 m^3。

        Args:
            value (float): 新的流体存储空间的值，必须大于等于1.0e-10。
        """
        assert value >= 1.0e-10, f'value = {value}'
        core.seepage_cell_set_v0(self.handle, value)

    core.use(c_double, 'seepage_cell_get_k', c_void_p)
    core.use(None, 'seepage_cell_set_k', c_void_p, c_double)

    @property
    def k(self) -> float:
        """
        流体压力增加1Pa的时候，孔隙体积的增加量(m^3). k的数值越小，则刚度越大.

        Returns:
            float: 孔隙体积增加量的值。
        """
        return core.seepage_cell_get_k(self.handle)

    @k.setter
    def k(self, value: float):
        """
        设置流体压力增加1Pa的时候，孔隙体积的增加量(m^3)。

        Args:
            value (float): 新的孔隙体积增加量的值。
        """
        core.seepage_cell_set_k(self.handle, value)

    def set_pore(self, p: float, v: float, dp: float, dv: float) -> 'CellData':
        """
        创建一个孔隙，使得当内部压力等于p时，体积为v；
        如果压力变化dp，体积变化为dv

        Args:
            p (float): 内部压力。
            v (float): 体积。
            dp (float): 压力变化量。
            dv (float): 体积变化量。

        Returns:
            CellData: 返回当前CellData对象。
        """
        k = max(1.0e-30, abs(dv)) / max(1.0e-30, abs(dp))
        self.k = k
        v0 = v - p * k
        if v0 <= 0:
            warnings.warn(
                f'v0 (= {v0}) <= 0 at {self.pos}. '
                f'p={p}, v={v}, dp={dp}, dv={dv}')
        self.v0 = v0
        return self

    def v2p(self, v: float) -> float:
        """
        给定内部流体的体积，根据孔隙刚度计算孔隙内流体的压力。

        Args:
            v (float): 内部流体的体积。

        Returns:
            float: 孔隙内流体的压力。
        """
        return (v - self.v0) / self.k

    def p2v(self, p: float) -> float:
        """
        给定内部流体的压力，根据孔隙刚度计算内部流体的体积。

        Args:
            p (float): 内部流体的压力。

        Returns:
            float: 内部流体的体积。
        """
        return self.v0 + p * self.k

    core.use(None, 'seepage_cell_fill', c_void_p, c_double, c_void_p, c_size_t, c_bool)

    def fill(self, p: float, s: Union[Vector, list, tuple], use_mass: bool = False) -> 'CellData':
        """
        根据此时流体的密度，孔隙的v0和k，给定的目标压力和流体饱和度，设置各个组分的质量。
            这里p为目标压力，s为目标饱和度；
            当各个相的饱和度的和不等于1的时候，将首先对饱和度的值进行等比例调整；
        注意：
            s作为一个数组，它的长度应该等于流体的数量或者组分的数量(均可以)；
            当s的长度等于流体的数量的时候，需要事先设置流体中各个组分的比例；
        注意
            当s的总和等于0的时候，虽然给定目标压力，但是仍然不会填充流体。此时填充后
            所有的组分都等于0。

        Args:
            p (float): 目标压力。
            s (Vector | list | tuple): 目标饱和度。
            use_mass (bool, optional): 是否使用质量填充，默认为False。

        Returns:
            CellData: 返回当前CellData对象。
        """
        pointer = const_f64_ptr(s)
        count = len(s)
        core.seepage_cell_fill(self.handle, p, pointer, count, use_mass)
        return self

    core.use(c_double, 'seepage_cell_get_pre', c_void_p)

    @property
    def pre(self) -> float:
        """
        单元格内流体的压力
            (根据流体的总体积和孔隙弹性计算得出)

        Returns:
            float: 单元格内流体的压力。
        """
        return core.seepage_cell_get_pre(self.handle)

    core.use(c_size_t, 'seepage_cell_get_fluid_n', c_void_p)
    core.use(None, 'seepage_cell_set_fluid_n', c_void_p, c_size_t)

    @property
    def fluid_number(self) -> int:
        """
        单元格内流体的数量
            (至少设置为1，并且需要为模型中的所有单元格设置相同的值)

        Returns:
            int: 单元格内流体的数量。
        """
        return core.seepage_cell_get_fluid_n(self.handle)

    @fluid_number.setter
    def fluid_number(self, value: int):
        """
        设置单元格内流体的数量。

        Args:
            value (int): 新的流体数量，必须在0到10之间。
        """
        assert 0 <= value < 10
        core.seepage_cell_set_fluid_n(self.handle, value)

    def get_fluid(self, *args) -> Optional[Union['Fluid', 'FluData']]:
        """
        返回给定序号的流体。(当参数数量为1的时候，返回Seepage.Fluid对象；
        当参数数量大于1的时候，返回Seepage.FluData对象)

        Args:
            *args: 流体或组分的序号。

        Returns:
            Fluid or FluData: 返回相应的流体或组分对象，
            如果不存在则返回None。
        """
        if len(args) > 0:
            idx = get_index(args[0], self.fluid_number)
            if idx is not None:
                flu = Fluid(self, idx)
                if len(args) > 1:
                    for i in range(1, len(args)):
                        flu = flu.get_component(args[i])
                        if flu is None:
                            return None
                return flu
            else:
                return None
        else:
            return None

    @property
    def fluids(self) -> Iterable[Union['Fluid', 'FluData']]:
        """
        单元格内的所有流体

        Returns:
            Iterator: 包含所有流体的迭代器。
        """
        return Iterator(self, self.fluid_number,
                        lambda m, ind: m.get_fluid(ind))

    def get_component(self, indexes: Union[int, list]) -> Optional[Union['FluData']]:
        """
        返回给定序号的组分。

        Args:
            indexes (int or list): 组分的序号或序号列表。

        Returns:
            FluData: 返回相应的组分对象，如果不存在则返回None。
        """
        if is_array(indexes):
            return self.get_fluid(*indexes)
        else:
            return self.get_fluid(indexes)

    core.use(c_double, 'seepage_cell_get_fluid_vol', c_void_p)

    @property
    def fluid_vol(self) -> float:
        """
        所有流体的体积。
        注意：这个体积包含所有fluids的体积的和，包括那些粘性非常大，
        在计算内核中被视为固体的流体

        Returns:
            float: 所有流体的体积。
        """
        return core.seepage_cell_get_fluid_vol(self.handle)

    core.use(c_double, 'seepage_cell_get_fluid_mass', c_void_p)

    @property
    def fluid_mass(self) -> float:
        """
        所有流体的质量
        注意：这个体积包含所有fluids的体积的和，包括那些粘性非常大，
        在计算内核中被视为固体的流体

        Returns:
            float: 所有流体的质量。
        """
        return core.seepage_cell_get_fluid_mass(self.handle)

    core.use(c_double, 'seepage_cell_get_fluid_vol_fraction', c_void_p, c_size_t)

    def get_fluid_vol_fraction(self, index: int) -> Optional[float]:
        """
        返回index给定流体的体积饱和度

        Args:
            index (int): 流体的序号。

        Returns:
            float: 该流体的体积饱和度，如果序号无效则返回None。
        """
        index_ = get_index(index, self.fluid_number)
        if index_ is not None:
            return core.seepage_cell_get_fluid_vol_fraction(
                self.handle, index_)
        else:
            return None

    core.use(c_double, 'seepage_cell_get_attr',
             c_void_p, c_size_t)
    core.use(None, 'seepage_cell_set_attr',
             c_void_p, c_size_t, c_double)
    core.use(c_size_t, 'seepage_cell_get_attr_n',
             c_void_p)

    @property
    def attr_n(self) -> int:
        """
        当前存储attr的数组的长度

        Returns:
            int: 存储attr的数组的长度。
        """
        return core.seepage_cell_get_attr_n(self.handle)

    def get_attr(self, index: Union[int, str], default_val: float = None,
                 **valid_range) -> Optional[float]:
        """
        该Cell的第 attr_id个自定义属性值。
        当不存在时，默认为一个无穷大的值(大于1.0e100)

        Args:
            index (int or str): 自定义属性的序号或名称。
            default_val (float, optional): 当属性不存在时返回的默认值。
                默认为None。
            **valid_range: 可选的有效范围参数。

        Returns:
            float: 自定义属性的值，如果不存在则返回默认值。
        """
        if isinstance(index, str):
            assert isinstance(self, Cell)
            index = self.model.get_cell_key(key=index)
        if index is None:
            return default_val
        if index < 0:
            if index == -1:
                return self.x
            if index == -2:
                return self.y
            if index == -3:
                return self.z
            if index == -4:
                return self.v0
            if index == -5:
                return self.k
            return default_val
        value = core.seepage_cell_get_attr(self.handle, index)
        if attr_in_range(value, **valid_range):
            return value
        else:
            return default_val

    def set_attr(self, index: Union[int, str], value: float) -> 'CellData':
        """
        该Cell的第 attr_id个自定义属性值。当不存在时，
        默认为一个无穷大的值(大于1.0e100)

        Args:
            index (int or str): 自定义属性的序号或名称。
            value (float): 自定义属性的新值。

        Returns:
            CellData: 返回当前CellData对象。
        """
        if isinstance(index, str):
            assert isinstance(self, Cell)
            index = self.model.reg_cell_key(key=index)
        if index is None:
            return self
        if value is None:
            value = 1.0e200
        if index < 0:
            if index == -1:
                self.x = value
                return self
            if index == -2:
                self.y = value
                return self
            if index == -3:
                self.z = value
                return self
            if index == -4:
                self.v0 = value
                return self
            if index == -5:
                self.k = value
                return self
            assert False
        core.seepage_cell_set_attr(self.handle, index, value)
        return self

    core.use(None, 'seepage_cell_multiply',
             c_void_p, c_void_p, c_double)

    def multiply(self, scale: float, result: Optional['CellData'] = None) -> 'CellData':
        """
        将孔隙大小和流体都乘以相同的倍率，其余所有的属性保持不变。

        Args:
            scale (float): 缩放倍率。
            result (CellData, optional): 用于存储结果的CellData对象。
                默认为None。

        Returns:
            CellData: 缩放后的CellData对象。
        """
        if not isinstance(result, CellData):
            result = CellData()
        assert isinstance(result, CellData), 'result must be a CellData'
        core.seepage_cell_multiply(result.handle, self.handle, scale)
        return result

    def __mul__(self, scale: float) -> 'CellData':
        """
        将孔隙大小和流体都乘以相同的倍率，其余所有的属性保持不变。

        Args:
            scale (float): 缩放倍率。

        Returns:
            CellData: 缩放后的CellData对象。
        """
        return self.multiply(scale)

    core.use(None, 'seepage_cell_clone',
             c_void_p, c_void_p)

    def clone(self, other: Optional['CellData'] = None, *, scale: Optional[float] = None):
        """
        从other克隆数据（所有的数据）

        Args:
            other (CellData): 要克隆数据的源CellData对象。
            scale (float, optional): 可选的缩放倍率。默认为None。

        Returns:
            CellData: 克隆后的CellData对象。
        """
        if other is None:
            return self
        assert isinstance(other, CellData)
        if scale is not None:
            other.multiply(scale, result=self)
            return self
        else:
            core.seepage_cell_clone(self.handle, other.handle)
            return self

    core.use(None, 'seepage_cell_clone_all', POINTER(c_void_p), POINTER(c_void_p), c_size_t)

    @staticmethod
    def clone_all(targets, sources, count):
        """
        拷贝所有给定的Cell数据
        Args:
            targets: 即将被覆盖的目标Cell
            sources: 数据来源
            count: 需要拷贝的数量

        Returns:
            None
        """
        core.seepage_cell_clone_all(targets, sources, count)

    core.use(None, 'seepage_cell_set_fluid_components',
             c_void_p, c_void_p)

    def set_fluid_components(self, model: "Seepage"):
        """
        利用model中定义的流体来设置Cell中的流体的组分的数量。
        注意:
            此函数会递归地调用model中的组分定义，
            从而保证Cell中流体组分结构和model中完全一样。

        Args:
            model (Seepage): 用于定义流体组分的模型。
        """
        assert isinstance(model, Seepage)
        core.seepage_cell_set_fluid_components(self.handle, model.handle)

    core.use(None, 'seepage_cell_set_fluid_property', c_void_p, c_double, c_size_t, c_size_t, c_void_p)

    def set_fluid_property(self, p: float, fa_t: int, fa_c: int, model: "Seepage"):
        """
        利用model中定义的流体的属性来更新流体的比热、密度和粘性系数。
        注意：
            函数会使用在各个流体中由fa_t指定的温度，并根据给定的压力p来查找流体属性；
            因此，在调用这个函数之前，务必要设置各个流体的温度 (fa_t)。
        注意：
            在调用之前，务必保证此Cell内的流体的结构和model内fludef的结构一致。
            即，应该首先调用set_fluid_components函数

        Args:
            p (float): 压力。
            fa_t (int): 流体温度的索引。
            fa_c (int): 流体组分的索引。
            model (Seepage): 用于定义流体属性的模型。
        """
        assert isinstance(model, Seepage)
        core.seepage_cell_set_fluid_property(self.handle, p, fa_t, fa_c, model.handle)

    core.use(None, 'seepage_cell_set_fluids_by_lexpr', c_void_p, c_void_p, c_void_p)

    def set_fluids_by_lexpr(self, lexpr: LinearExpr, model: "Seepage"):
        """ 设置此Cell中的流体

        此函数将使用model中各个cell的流体，然后使用线性表达式lexpr来计算

        Args:
            lexpr (LinearExpr): 计算流体的线性表达式
            model (Seepage): 用来拷贝流体的另外一个模型

        Returns:
            None
        """
        core.seepage_cell_set_fluids_by_lexpr(
            self.handle, lexpr.handle, model.handle)

    core.use(None, 'seepage_cell_set_pore_by_lexpr',
             c_void_p, c_void_p, c_void_p)

    def set_pore_by_lexpr(self, lexpr: LinearExpr, model: "Seepage"):
        """ 设置此Cell中的孔隙

        此函数将使用model中各个cell的孔隙，然后使用线性表达式lexpr来计算

        Args:
            lexpr (LinearExpr): 计算pore的线性表达式
            model (Seepage): 用来拷贝pore的另外一个模型

        Returns:
            None
        """
        core.seepage_cell_set_pore_by_lexpr(self.handle, lexpr.handle,
                                            model.handle)

    core.use(None, 'seepage_cell_set_mass_attr_by_lexpr',
             c_void_p, c_size_t, c_void_p, c_void_p)

    def set_mass_attr_by_lexpr(self, index: int, lexpr: LinearExpr, model: "Seepage"):
        """ 设置此Cell中的自定义属性
        此函数将使用model中各个cell的自定义属性，然后使用线性表达式lexpr来计算
        Args:
            index (int): 自定义属性的序号
            lexpr (LinearExpr): 计算自定义属性的线性表达式
            model (Seepage): 用来拷贝自定义属性的另外一个模型
        Returns:
            None
        """
        core.seepage_cell_set_mass_attr_by_lexpr(
            self.handle, index, lexpr.handle, model.handle)

    core.use(None, 'seepage_cell_set_density_attr_by_lexpr',
             c_void_p, c_size_t, c_void_p, c_void_p)

    def set_density_attr_by_lexpr(self, index: int, lexpr: LinearExpr, model: "Seepage"):
        """ 设置此Cell中的自定义属性
        此函数将使用model中各个cell的自定义属性，然后使用线性表达式lexpr来计算
        Args:
            index (int): 自定义属性的序号
            lexpr (LinearExpr): 计算自定义属性的线性表达式
            model (Seepage): 用来拷贝自定义属性的另外一个模型
        Returns:
            None
        """
        core.seepage_cell_set_density_attr_by_lexpr(
            self.handle, index, lexpr.handle, model.handle)


class Cell(CellData):
    """
    Cell为控制体。一个Cell由如下几个部分组成：

    1、该控制体内流体存储空间的大小以及刚度(即设置Cell的pore).
        计算内核根据Cell内流体的总的体积，结合pore的弹性性质来定义Cell内流体
        的压力，所以在创建一个Cell之后，必须首先对Cell的pore进行配置。
        具体地，调用Cell.set_pore函数来设置Cell的pore;

    2、Cell内存储的流体。一个Cell内可以存储多种流体，这些流体存储在一个数组内，
        且从0开始编号。每一种流体可以由多个组分组成，流体的组分
        也从0开始编号；

    3、Cell的自定义属性。在Cell内存储一个浮点型的数组，存储一系列自定义的属性，
        用于辅助存储和计算。自定义属性从0开始编号。
    """

    core.use(c_void_p, 'seepage_get_cell', c_void_p, c_size_t)

    def __init__(self, model: "Seepage", index: int):
        """
        初始化Cell对象。

        Args:
            model (Seepage): 所属的Seepage模型。
            index (int): Cell的索引，必须小于模型中的Cell数量。

        Raises:
            AssertionError: 如果model不是Seepage类型，
            或者index不是整数，或者index大于等于模型中的Cell数量。
        """
        assert isinstance(model, Seepage)
        assert isinstance(index, int)
        assert index < model.cell_number
        self.model = model
        self.index = index
        super().__init__(handle=core.seepage_get_cell(model.handle, index))

    def __str__(self) -> str:
        """
        返回Cell对象的字符串表示。

        Returns:
            str: 包含Cell句柄、索引和位置的字符串。
        """
        return (f'zml.Cell(handle = {self.model.handle}, '
                f'index = {self.index}, pos = {self.pos})')

    core.use(c_size_t, 'seepage_get_cell_face_n',
             c_void_p, c_size_t)

    @property
    def face_number(self) -> int:
        """
        获取与该Cell连接的Face的数量。

        Returns:
            int: 与该Cell连接的Face的数量。
        """
        return core.seepage_get_cell_face_n(self.model.handle, self.index)

    @property
    def cell_number(self) -> int:
        """
        获取与该Cell相邻的Cell的数量。

        Returns:
            int: 与该Cell相邻的Cell的数量，等于face_number。
        """
        return self.face_number

    core.use(c_size_t, 'seepage_get_cell_face_id',
             c_void_p, c_size_t, c_size_t)

    core.use(c_size_t, 'seepage_get_cell_cell_id',
             c_void_p, c_size_t, c_size_t)

    def get_cell(self, index: int) -> Optional["Cell"]:
        """
        获取与该Cell相邻的第index个Cell。

        Args:
            index (int): 相邻Cell的索引。

        Returns:
            Cell or None: 与该Cell相邻的第index个Cell，
            如果不存在则返回None。
        """
        index_ = get_index(index, self.cell_number)
        if index_ is not None:
            cell_id = core.seepage_get_cell_cell_id(self.model.handle,
                                                    self.index, index_)
            return self.model.get_cell(cell_id)
        else:
            return None

    def get_face(self, index: int) -> Optional["Face"]:
        """
        获取与该Cell连接的第index个Face。

        Args:
            index (int): 连接Face的索引。

        Returns:
            Face or None: 与该Cell连接的第index个Face，
            如果不存在则返回None。
        注：该Face的另一侧，即为get_cell返回的Cell。
        """
        index_ = get_index(index, self.face_number)
        if index_ is not None:
            face_id = core.seepage_get_cell_face_id(self.model.handle, self.index, index_)
            return self.model.get_face(face_id)
        else:
            return None

    @property
    def cells(self) -> Iterable['Cell']:
        """
        获取此Cell周围的所有Cell。

        Returns:
            Iterator: 包含此Cell周围所有Cell的迭代器。
        """
        return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

    @property
    def faces(self) -> Iterable['Face']:
        """
        获取此Cell周围的所有Face。

        Returns:
            Iterator: 包含此Cell周围所有Face的迭代器。
        """
        return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

    def set_ini(self, *args, **kwargs):
        warnings.warn("set_ini is deprecated (removed after 2027-6-3). Please use zmlx.tfc.set_cell_ini instead.",
                      stacklevel=2, category=DeprecationWarning)
        from zmlx.tfc import set_cell_ini
        set_cell_ini(self, *args, **kwargs)


class FaceData(HasHandle):
    """
    FaceData类用于表示和操作Cell之间界面（Face）的数据。

    该类提供了一系列方法来处理Face的序列化保存、加载，
    以及获取和设置Face的各种属性，如自定义属性、导流能力、相对渗透率曲线等。
    """
    core.use(c_void_p, 'new_seepage_face')
    core.use(None, 'del_seepage_face', c_void_p)

    def __init__(self, path: str = None, handle: Optional[c_void_p] = None):
        """
        初始化FaceData对象。

        Args:
            path (str, optional): 用于加载序列化数据的文件路径。默认为None。
            handle (c_void_p, optional): 已有的FaceData句柄。默认为None。

        若handle为None且path为字符串，则会尝试从指定路径加载数据。
        """
        super().__init__(handle, core.new_seepage_face, core.del_seepage_face)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'seepage_face_save', c_void_p, c_char_p)

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
            path (str): 保存序列化数据的文件路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.seepage_face_save(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_face_load', c_void_p, c_char_p)

    def load(self, path: str):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 读取序列化数据的文件路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.seepage_face_load(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_face_write_fmap',
             c_void_p, c_void_p, c_char_p)
    core.use(None, 'seepage_face_read_fmap',
             c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt: str = 'binary') -> FileMap:
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml'
                和 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的FileMap对象。
        """
        fmap = FileMap()
        core.seepage_face_write_fmap(self.handle, fmap.handle,
                                     make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt: str = 'binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary

        Args:
            fmap (FileMap): 包含序列化数据的FileMap对象。
            fmt (str, optional): 反序列化格式，可选值为 'text', 'xml'
                和 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.seepage_face_read_fmap(self.handle, fmap.handle,
                                    make_c_char_p(fmt))

    @property
    def fmap(self) -> FileMap:
        """
        获取当前FaceData对象的二进制序列化FileMap对象。

        Returns:
            FileMap: 包含二进制序列化数据的FileMap对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: FileMap):
        """
        从给定的FileMap对象中加载二进制序列化数据。

        Args:
            value (FileMap): 包含二进制序列化数据的FileMap对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(c_double, 'seepage_face_get_attr',
             c_void_p, c_size_t)
    core.use(None, 'seepage_face_set_attr',
             c_void_p, c_size_t, c_double)

    def get_attr(self, index: Union[int, str], default_val: float = None,
                 **valid_range):
        """
        该Face的第 attr_id个自定义属性值。
        当不存在时，默认为一个无穷大的值(大于1.0e100)

        Args:
            index (int or str): 自定义属性的索引或键名。
            default_val (float, optional): 当属性不存在或不在有效范围内时
                返回的默认值。默认为None。
            **valid_range: 可选的有效范围参数。

        Returns:
            float: 自定义属性的值，如果不存在或不在有效范围内则返回默认值。
        """
        if isinstance(index, str):
            assert isinstance(self, Face)
            index = self.model.get_face_key(key=index)
        if index is None:
            return default_val
        value = core.seepage_face_get_attr(self.handle, index)
        if attr_in_range(value, **valid_range):
            return value
        else:
            return default_val

    def set_attr(self, index: Union[int, str], value: float):
        """
        该Face的第 attr_id个自定义属性值。
        当不存在时，默认为一个无穷大的值(大于1.0e100)

        Args:
            index (int or str): 自定义属性的索引或键名。
            value (float): 要设置的自定义属性的值。

        Returns:
            FaceData: 返回当前FaceData对象。
        """
        if isinstance(index, str):
            assert isinstance(self, Face)
            index = self.model.reg_face_key(key=index)
        if index is None:
            return self
        if value is None:
            value = 1.0e200
        core.seepage_face_set_attr(self.handle, index, value)
        return self

    core.use(None, 'seepage_face_clone',
             c_void_p, c_void_p)

    def clone(self, other: 'FaceData') -> 'FaceData':
        """
        从另一个FaceData对象克隆数据。

        Args:
            other (FaceData): 要克隆数据的源FaceData对象。

        Returns:
            FaceData: 返回当前FaceData对象。
        """
        if other is not None:
            assert isinstance(other, FaceData)
            core.seepage_face_clone(self.handle, other.handle)
        return self

    def get_copy(self) -> 'FaceData':
        """
        获取当前FaceData对象的副本。
        Returns:
            FaceData: 当前FaceData对象的副本。
        """
        data = FaceData()
        data.clone(self)
        return data

    core.use(c_double, 'seepage_face_get_cond',
             c_void_p)
    core.use(None, 'seepage_face_set_cond',
             c_void_p, c_double)

    @property
    def cond(self) -> float:
        """
        此Face的导流能力. dv=cond*dp*dt/vis，其中dp为两端的压力差，
        dt为时间步长，vis为内部流体的粘性系数
            cond = area * perm / dist.
        如果是多相的情况下，可能需要两步矫正（程序内部自动算，用户不用设置）：
            1. 如果多相中存在固体，首先，需要计算 流体体积/总体积，
                得到流体的体积分数 a，用 cond * kr(a)得到流体的cond1.
            2. 如果流体有多种，对于第0种流体，
                s0=v0/v_sum，cond1 * kr0(s0)
                得到 cond2_0.

        Returns:
            float: 此Face的导流能力。
        """
        return core.seepage_face_get_cond(self.handle)

    @cond.setter
    def cond(self, value: float):
        """
        此Face的导流能力. dv=cond*dp*dt/vis，其中dp为两端的压力差，
        dt为时间步长，vis为内部流体的粘性系数

        Args:
            value (float): 要设置的导流能力值。
        """
        core.seepage_face_set_cond(self.handle, value)

    core.use(c_double, 'seepage_face_get_dr',
             c_void_p)
    core.use(None, 'seepage_face_set_dr',
             c_void_p, c_double)

    @property
    def dr(self) -> float:
        """
        获取此Face的某个dr属性值(流体的额外驱动力)

        Returns:
            float: 此Face的属性值。
        """
        return core.seepage_face_get_dr(self.handle)

    @dr.setter
    def dr(self, value: float):
        """
        设置此Face的dr属性值(流体的额外驱动力)

        Args:
            value (float): 要设置的属性值。
        """
        core.seepage_face_set_dr(self.handle, value)

    core.use(c_double, 'seepage_face_get_dv',
             c_void_p, c_size_t)

    def get_dv(self, fluid_id: int) -> float:
        """
        返回上一步迭代通过这个face的流体的体积

        Args:
            fluid_id (int): 流体的ID。

        Returns:
            float: 上一步迭代通过这个face的指定流体的体积。
        """
        assert isinstance(fluid_id, int)
        return core.seepage_face_get_dv(self.handle, fluid_id)

    core.use(c_size_t, 'seepage_face_get_ikr',
             c_void_p, c_size_t)
    core.use(None, 'seepage_face_set_ikr',
             c_void_p, c_size_t, c_size_t)

    def get_ikr(self, index: int) -> int:
        """
        第index种流体的相对渗透率曲线的id

        Args:
            index (int): 流体的索引。

        Returns:
            int: 第index种流体的相对渗透率曲线的ID。
        """
        return core.seepage_face_get_ikr(self.handle, index)

    def set_ikr(self, index: int, value: int):
        """
        设置在这个Face中，第index种流体的相对渗透率曲线的id.
            如果在这个Face中，没有为某个流体选择相渗曲线，
            则如果该流体的序号为ID，则默认使用序号为ID的相渗曲线。

        Args:
            index (int): 流体的索引。
            value (int): 要设置的相对渗透率曲线的ID。
        """
        core.seepage_face_set_ikr(self.handle, index, value)


class Face(FaceData):
    """
    Face为Cell之间的界面。Cell由如下属性组成：

    1、Face的导流系数cond:  dv=dp*cond*dt/vis
        其中dv为流经face的流体的体积，cond为导流系数，dt为时长，vis为流体的粘性系数

    2、Face中不同流体所采用的相对渗透率曲线的序号。
        在Seepage中可以定义多个（最多10000个）相对渗透率曲线，且不同的Face可以选用
        不同的相对渗透率曲线。<相对渗透率曲线的序号>可以不定义，
        此时会采用默认值(即第i种流体，自动选用第i个相渗曲线)
        注意：需要为每一种流体配置相对渗透率曲线;

    3、Face的自定义属性。在Face内存储一个浮点型的数组，存储一系列自定义的属性，
        用于辅助存储和计算。自定义属性从0开始编号。
    """
    core.use(c_void_p, 'seepage_get_face', c_void_p, c_size_t)

    def __init__(self, model: 'Seepage', index: int):
        """
        初始化Face对象。

        Args:
            model (Seepage): 所属的Seepage模型对象。
            index (int): Face的索引。

        Raises:
            AssertionError: 如果model不是Seepage类型，或者index不是整数，
            或者index超出模型的Face数量范围。
        """
        assert isinstance(model, Seepage)
        assert isinstance(index, int)
        assert index < model.face_number
        self.model = model
        self.index = index
        super().__init__(handle=core.seepage_get_face(model.handle, index))

    def __str__(self) -> str:
        """
        返回Face对象的字符串表示。

        Returns:
            str: 包含Face句柄和索引的字符串。
        """
        return (f'zml.Face(handle = {self.model.handle}, '
                f'index = {self.index}) ')

    core.use(c_size_t, 'seepage_get_face_cell_id',
             c_void_p, c_size_t, c_size_t)

    @property
    def cell_number(self) -> int:
        """
        和Face连接的Cell的数量

        Returns:
            int: 与Face连接的Cell的数量，固定为2。
        """
        return 2

    def get_cell(self, index) -> Optional['Cell']:
        """
        和Face连接的第index个Cell

        Args:
            index (int): 要获取的Cell的索引。

        Returns:
            Cell or None: 与Face连接的第index个Cell，
            如果索引无效则返回None。
        """
        index = get_index(index, self.cell_number)
        if index is not None:
            cell_id = core.seepage_get_face_cell_id(self.model.handle, self.index, index)
            return self.model.get_cell(cell_id)
        else:
            return None

    @property
    def cells(self) -> Tuple[Optional['Cell'], Optional['Cell']]:
        """
        返回Face两端的Cell

        Returns:
            tuple: 包含Face两端Cell的元组。
        """
        return self.get_cell(0), self.get_cell(1)

    @property
    def pos(self) -> Tuple[float, ...]:
        """
        返回Face中心点的位置（根据两侧的Cell的位置来自动计算）

        Returns:
            tuple: 包含Face中心点位置坐标的元组。
        """
        p0 = self.get_cell(0).pos
        p1 = self.get_cell(1).pos
        return tuple([(p0[i] + p1[i]) / 2 for i in range(len(p0))])

    def distance(self, other):
        """
        返回距离另外一个Cell或者另外一个位置的距离

        Args:
            other (Cell or tuple): 另一个Cell对象或位置坐标元组。

        Returns:
            float: 与另一个Cell或位置的距离。
        """
        if hasattr(other, 'pos'):
            return get_distance(self.pos, other.pos)
        else:
            return get_distance(self.pos, other)

    def get_another(self, cell) -> Optional['Cell']:
        """
        返回另外一侧的Cell

        Args:
            cell (Cell or int): Cell对象或Cell的索引。

        Returns:
            Cell or None: 另一侧的Cell，如果输入无效则返回None。
        """
        if isinstance(cell, Cell):
            cell = cell.index

        c0 = self.get_cell(0)
        assert isinstance(c0, Cell)

        c1 = self.get_cell(1)
        assert isinstance(c1, Cell)

        if c0.index == cell:
            return c1
        elif c1.index == cell:
            return c0
        else:
            return None


class Injector(HasHandle):
    """
    流体的注入点。可以按照一定的规律向特定的Cell注入特定的流体(或者能量).
        注意Injector工作的逻辑：
        1. 如果设置了注入的流体的ID，则实施流体注入操作
            (此时value代表注入的体积速率: m^3/s);
        2. 如果没有设置流体ID，并且设置了 ca_mc和ca_t属性，则实施热量注入操作;
    """
    core.use(c_void_p, 'new_injector')
    core.use(None, 'del_injector', c_void_p)

    def __init__(self, path: Optional[str] = None, handle: Optional[c_void_p] = None):
        """
        初始化Injector对象。

        Args:
            path (str, optional): 用于加载序列化数据的文件路径。默认为None。
            handle (c_void_p, optional): 已有的Injector句柄。默认为None。

        如果handle为None且path为字符串，则会尝试从指定路径加载数据。
        """
        super().__init__(handle, core.new_injector, core.del_injector)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'injector_save', c_void_p, c_char_p)

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
            path (str): 保存序列化数据的文件路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.injector_save(self.handle, make_c_char_p(path))

    core.use(None, 'injector_load', c_void_p, c_char_p)

    def load(self, path: str):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 读取序列化数据的文件路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.injector_load(self.handle, make_c_char_p(path))

    core.use(None, 'injector_write_fmap',
             c_void_p, c_void_p, c_char_p)
    core.use(None, 'injector_read_fmap',
             c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt: str = 'binary') -> FileMap:
        """
        将数据序列化到一个Filemap中。其中fmt的取值可以为: text, xml和binary

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml'
                和 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的FileMap对象。
        """
        fmap = FileMap()
        core.injector_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt: str = 'binary'):
        """
        从Filemap中读取序列化的数据。其中fmt的取值可以为: text, xml和binary

        Args:
            fmap (FileMap): 包含序列化数据的FileMap对象。
            fmt (str, optional): 反序列化格式，可选值为 'text', 'xml'
                和 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.injector_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self) -> FileMap:
        """
        获取当前Injector对象的二进制序列化FileMap对象。

        Returns:
            FileMap: 包含二进制序列化数据的FileMap对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: FileMap):
        """
        从给定的FileMap对象中加载二进制序列化数据。

        Args:
            value (FileMap): 包含二进制序列化数据的FileMap对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(c_size_t, 'injector_get_cell_id',
             c_void_p)
    core.use(None, 'injector_set_cell_id',
             c_void_p, c_size_t)

    @property
    def cell_id(self) -> int:
        """
        注入点关联的Cell的ID。如果该ID不存在，则不会注入。
        注：
            默认为无穷大

        Returns:
            int: 注入点关联的Cell的ID。
        """
        return core.injector_get_cell_id(self.handle)

    @cell_id.setter
    def cell_id(self, value: int):
        """
        设置注入点关联的Cell的ID。如果该ID不存在，则不会注入。
        注：
            默认为无穷大

        Args:
            value (int): 要设置的Cell的ID。
        """
        core.injector_set_cell_id(self.handle, value)

    core.use(c_void_p, 'injector_get_flu', c_void_p)

    @property
    def flu(self) -> 'FluData':
        """
        即将注入到Cell中的流体的数据。这里返回的是一个引用 (从而可以直接修改内部的数据)。
        注：
            默认质量为1e-100，即无限接近于0

        Returns:
            FluData: 即将注入的流体的数据对象。
        """
        return FluData(handle=core.injector_get_flu(self.handle))

    core.use(None, 'injector_set_fid',
             c_void_p, c_size_t, c_size_t, c_size_t)

    def set_fid(self, fluid_id: Union[int, List[int], Tuple[int, ...]]):
        """
        设置注入的流体的ID。注意：如果需要注热的是热量，则将fluid_id设置为None。
        注：在没有做特殊设置的时候，fid默认为[]

        Args:
            fluid_id (int | list | tuple): 注入的流体的ID列表。
        """
        core.injector_set_fid(self.handle, *parse_fid3(fluid_id))

    core.use(c_size_t, 'injector_get_fid_length',
             c_void_p)
    core.use(c_size_t, 'injector_get_fid_of',
             c_void_p, c_size_t)

    def get_fid(self) -> List[int]:
        """
        返回注入流体的ID。
        注：在没有做特殊设置的时候，默认为[]

        Returns:
            list: 注入流体的ID列表。
        """
        count = core.injector_get_fid_length(self.handle)
        return [core.injector_get_fid_of(self.handle, idx) for idx in
                range(count)]

    @property
    def fid(self) -> List[int]:
        """
        注入的流体的ID。注意：如果需要注热的是热量，则将fluid_id设置为None。
        注：在没有做特殊设置的时候，fid默认为[]

        Returns:
            list: 注入流体的ID列表。
        """
        return self.get_fid()

    @fid.setter
    def fid(self, value: Union[int, List[int], Tuple[int, ...]]):
        """
        设置注入的流体的ID。注意：如果需要注热的是热量，则将fluid_id设置为None。
        注：在没有做特殊设置的时候，fid默认为[]

        Args:
            value: 要设置的注入流体的ID。
        """
        self.set_fid(value)

    core.use(c_double, 'injector_get_value',
             c_void_p)
    core.use(None, 'injector_set_value',
             c_void_p, c_double)

    @property
    def value(self) -> float:
        """
        注入的数值。可以有多重的含义：
            当注入流体的时候，为注入的体积速率 m^3/s
            当注热时：
                若恒温注热，则为温度
                若恒功率，则为功率
        注：
            在没有做任何设置时，默认值为0

        Returns:
            float: 注入的数值。
        """
        return core.injector_get_value(self.handle)

    @value.setter
    def value(self, val: float):
        """
        设置注入的数值。
        注：
            在没有做任何设置时，默认值为0

        Args:
            val (float): 要设置的注入数值。
        """
        core.injector_set_value(self.handle, val)

    @property
    def time(self):
        """
        此属性已被移除。

        注：
            此属性已被移除，调用时会发出警告。

        Returns:
            int: 固定返回0。
        """
        warnings.warn('Property Injector.time '
                      'has been removed',
                      DeprecationWarning, stacklevel=2)
        return 0

    @time.setter
    def time(self, _):
        """
        设置时间属性（此属性已被移除）。

        注：
            此属性已被移除，调用时会发出警告。

        Args:
            _: 此参数无实际作用。
        """
        warnings.warn('Property Injector.time '
                      'has been removed',
                      DeprecationWarning, stacklevel=2)

    core.use(c_double, 'injector_get_pos',
             c_void_p, c_size_t)
    core.use(None, 'injector_set_pos',
             c_void_p, c_size_t, c_double)

    @property
    def pos(self) -> List[float]:
        """
        该Injector在三维空间的坐标。
        注：
            在没有设置的时候，默认是一个无限远的位置 [1e+50, 1e+50, 1e+50]

        Returns:
            list: 包含三维坐标的列表。
        """
        return [core.injector_get_pos(self.handle, i) for i in range(3)]

    @pos.setter
    def pos(self, value: Union[List[float], Tuple[float], Tuple[float, ...]]):
        """
        设置该Injector在三维空间的坐标。
        注：
            在没有设置的时候，默认是一个无限远的位置 [1e+50, 1e+50, 1e+50]

        Args:
            value (list): 包含三维坐标的列表，长度必须为3。
        """
        assert len(value) == 3
        for dim in range(3):
            core.injector_set_pos(self.handle, dim, value[dim])

    core.use(c_double, 'injector_get_radi',
             c_void_p)
    core.use(None, 'injector_set_radi',
             c_void_p, c_double)

    @property
    def radi(self) -> float:
        """
        Injector的控制半径。
        注：
            在没有设置的时候，原始默认值为1e+100，即无穷大

        Returns:
            float: Injector的控制半径。
        """
        return core.injector_get_radi(self.handle)

    @radi.setter
    def radi(self, value: float):
        """
        设置Injector的控制半径。
        注：
            在没有设置的时候，原始默认值为1e+100，即无穷大

        Args:
            value (float): 要设置的控制半径。
        """
        core.injector_set_radi(self.handle, value)

    core.use(c_double, 'injector_get_g_heat',
             c_void_p)
    core.use(None, 'injector_set_g_heat',
             c_void_p, c_double)

    @property
    def g_heat(self) -> float:
        """
        热边界和cell之间换热的系数 (当大于0的时候，则实施固定温度的加热，
        否则为固定功率的加热)。
        注：
            默认为0

        Returns:
            float: 热边界和cell之间换热的系数。
        """
        return core.injector_get_g_heat(self.handle)

    @g_heat.setter
    def g_heat(self, value: float):
        """
        设置热边界和cell之间换热的系数 (当大于0的时候，则实施固定温度的加热，
        否则为固定功率的加热)。
        注：
            默认为0

        Args:
            value (float): 要设置的换热系数。
        """
        core.injector_set_g_heat(self.handle, value)

    core.use(c_size_t, 'injector_get_ca_mc',
             c_void_p)
    core.use(None, 'injector_set_ca_mc',
             c_void_p, c_size_t)

    @property
    def ca_mc(self) -> int:
        """
        cell的mc属性的ID。
        注：
            默认为无穷大18446744073709551615，即不存在的属性ID

        Returns:
            int: cell的mc属性的ID。
        """
        return core.injector_get_ca_mc(self.handle)

    @ca_mc.setter
    def ca_mc(self, value: int):
        """
        设置cell的mc属性的ID。
        注：
            默认为无穷大18446744073709551615，即不存在的属性ID

        Args:
            value (int): 要设置的cell的mc属性的ID。
        """
        core.injector_set_ca_mc(self.handle, value)

    core.use(c_size_t, 'injector_get_ca_t',
             c_void_p)
    core.use(None, 'injector_set_ca_t',
             c_void_p, c_size_t)

    @property
    def ca_t(self) -> int:
        """
        cell的温度属性的id。
        注：
            默认为无穷大18446744073709551615，即不存在的属性ID

        Returns:
            int: cell的温度属性的id。
        """
        return core.injector_get_ca_t(self.handle)

    @ca_t.setter
    def ca_t(self, value: int):
        """
        设置cell的温度属性的id。
        注：
            默认为无穷大18446744073709551615，即不存在的属性ID

        Args:
            value (int): 要设置的cell的温度属性的id。
        """
        core.injector_set_ca_t(self.handle, value)

    core.use(c_size_t, 'injector_get_ca_no_inj',
             c_void_p)
    core.use(None, 'injector_set_ca_no_inj',
             c_void_p, c_size_t)

    @property
    def ca_no_inj(self) -> int:
        """
        在根据位置来寻找注入的cell的时候，凡是设置了ca_no_inj的cell，
        将会被忽略（从而避免被Injector操作）。
        注：
            默认为无穷大18446744073709551615，即不存在的属性ID

        Returns:
            int: cell的ca_no_inj属性的ID。
        """
        return core.injector_get_ca_no_inj(self.handle)

    @ca_no_inj.setter
    def ca_no_inj(self, value: int):
        """
        设置在根据位置来寻找注入的cell的时候，凡是设置了ca_no_inj的cell，
        将会被忽略（从而避免被Injector操作）。
        注：
            默认为无穷大18446744073709551615，即不存在的属性ID

        Args:
            value (int): 要设置的cell的ca_no_inj属性的ID。
        """
        core.injector_set_ca_no_inj(self.handle, value)

    core.use(None, 'injector_add_oper',
             c_void_p, c_double, c_char_p)

    def add_oper(self, time: float, oper: Union[str, float]):
        """
        添加在time时刻的一个操作。注意，oper支持如下关键词
            value
            pos    x  y  z
            radi   r
            val    v
            den    v
            vis    v
            mass   m
            attr   id  val
            fid    a  b  c
            g_heat v            (since 2024-02-27)
        其它关键词将会被忽略(不抛出异常)。

        Args:
            time (float): 操作的时间。
            oper (str): 操作的关键词和参数。

        Returns:
            Injector: 返回当前Injector对象。
        """
        core.injector_add_oper(self.handle, time, make_c_char_p(
            oper if isinstance(oper, str) else f'{oper}'))
        return self

    core.use(None, 'injector_work',
             c_void_p, c_void_p, c_double, c_double)

    def work(self, model: 'Seepage', *, time: Optional[float] = None, dt: Optional[float] = None):
        """
        执行注入操作。
        注：
            此函数不需要调用。内置在Seepage中的Injector，
            会在Seepage.iterate函数中被自动调用。

        Args:
            model (Seepage): 所属的Seepage模型对象。
            time (float, optional): 操作的时间，默认为None，
                若为None则使用默认值0。
            dt (float, optional): 时间步长，默认为None，若为None则不执行操作。
        """
        assert isinstance(model, Seepage)
        if time is None:
            warnings.warn(
                'time is None for Injector, '
                'use time=0 as default')
            time = 0
        if dt is None:
            return
        core.injector_work(self.handle, model.handle, time, dt)

    core.use(None, 'injector_clone',
             c_void_p, c_void_p)

    def clone(self, other: Optional['Injector'] = None) -> 'Injector':
        """
        克隆所有的数据；包括作用的cell_id。

        Args:
            other (Injector): 要克隆数据的源Injector对象。

        Returns:
            Injector: 返回当前Injector对象。
        """
        if other is not None:
            assert isinstance(other, Injector)
            core.injector_clone(self.handle, other.handle)
        return self


def calc_recommended_dt(
        prev_dt: float, prev_cfl: float, target_cfl: Optional[float] = 0.1
) -> float:
    """
    计算建议的时间步长.
    Args:
        prev_dt: 上一次的时间步长。
        prev_cfl: 上一次的CFL数。
        target_cfl: 目标CFL数，默认为0.1。
    Returns:
        float: 建议的时间步长。
    """
    if target_cfl is None:
        target_cfl = 0.1
    prev_cfl = max(1.0e-6, prev_cfl)
    dt = prev_dt
    if prev_cfl > target_cfl:
        dt *= (target_cfl * 0.99 / prev_cfl)  # 使得略微小一些
    else:
        dt *= min(2.0, math.sqrt(target_cfl / prev_cfl))
    return dt


class FlowSol(HasHandle):
    """
    流动求解器
    """
    core.use(c_void_p, 'new_seepage_fs')
    core.use(None, 'del_seepage_fs', c_void_p)

    def __init__(self, handle: Optional[c_void_p] = None):
        """
        初始化UFlowSol类的实例。
        Args:
            handle: 句柄，默认为None(此时创建新的对象; 否则，为给定对象的引用)。
        """
        super().__init__(handle, core.new_seepage_fs, core.del_seepage_fs)
        self.solver = None
        self.report = None

    def get_report(self):
        """
        临时变量，存储计算的报告
        """
        if self.report is None:
            self.report = Map()
        return self.report

    def get_sol(self) -> 'ConjugateGradientSolver':
        """
        返回内部存储的一个默认的线性方程组求解器。
        """
        if self.solver is None:
            self.solver = ConjugateGradientSolver(tolerance=1.0e-25)
        return self.solver

    core.use(None, 'seepage_fs_reset', c_void_p)

    def reset(self):
        """
        重置求解器. 当model的数据发生改变的时候，重置求解器，确保在后续迭代的时候，求解器内部的拓扑结构
        是正确的。
        注意：重置并在后续重建，会有一定的计算消耗。
        """
        core.seepage_fs_reset(self.handle)

    core.use(None, 'seepage_fs_iterate',
             c_void_p, c_void_p, c_void_p,
             c_double, c_double,
             c_size_t, c_size_t, c_size_t, c_size_t, c_void_p,
             c_void_p  # ThreadPool since 2025-7-25
             )

    def iterate(
            self, model: 'Seepage', dt: float, *,
            fa_s: Optional[int] = None, fa_q: Optional[int] = None,
            fa_k: Optional[int] = None, ca_p: Optional[int] = None,
            cfl: Optional[float] = None,
            dv_rela: Optional[float] = None,  # 弃用
            solver: Optional['ConjugateGradientSolver'] = None,
            pool: Optional[ThreadPool] = None,
            report: Optional[Map] = None,
    ):
        """
        将给定的模型在时间上向前迭代(更新流动).

        Args:
            model: 即将被迭代的渗流模型对象(Seepage)
            dt (float): 迭代的目标时间步长 [单位：秒]
                注意，当给定dv_rela的时候，将会进行检查，最终采用的，可能并不是这个给定的
                时间步长。
            fa_s (int, optional): Face自定义属性的ID，
                代表Face的横截面积（用于计算Face内流体的受力），默认为None。
                当考虑惯性的时候，需要给定
            fa_q (int, optional): Face自定义属性的ID，
                代表Face内流体在通量(也将在iterate中更新)，默认为None。
                当考虑惯性的时候，需要给定(且需要给定初始值)
            fa_k (int, optional): Face内流体的"惯性系数"的属性ID，
                默认为None。
                当考虑惯性的时候，需要给定(且需要给定初始值)
            ca_p (int, optional): Cell的自定义属性，
                用于写入Cell内流体的压力(迭代时的压力，并非按照流体体积进行计算的)，
                默认为None（即不写入）
            solver (ConjugateGradientSolver, optional): 求解器实例，
                默认为None。
            pool (ThreadPool, optional): 线程池实例，
                默认为None。
            report (Map, optional): 报告对象，
                默认为None (此时，会新建一个Map并且传入内核).
            dv_rela (float, optional): CFL数 (弃用)
            cfl (float, optional): CFL数，默认为None.
                代表dt内流体流过的“最大距离”与网格的比值。
                当cfl为None的时候，将直接使用给定的dt来进行迭代。
                当cfl给定的时候，则会检查给定的dt是否满足条件。如果不满足，则会降低dt。

        Notes:
            关于惯性：
                对于Face中的流体，定义其动量为
                    momentum = m*v = k*q
                其中q为通过该Face的流体的速率，k是一个自定义的系数. 这个系数越大，则流体的惯性越强.
                另外，作用在Face上的流体的作用力为：
                    f = dp*s
                其中s为横截面积. 根据动量定理，动量的变化量为
                    m*d(v)=k*d(q)=f*d(t)
                以上就是在程序中考虑惯性的基本的逻辑。因此，要计算流体的惯性效应，关键是要正确设置Face的
                面积s和系数k这两个属性。另外，在迭代的过程中，随着face内流体的密度的变化，也应该去更新
                这两个属性的值.

        Returns:
            dict: 包含迭代报告的字典，可能会包括：
                dt_modify_times: 时间步长调整的次数
                cfl: 实际的CFL数
                dt_error: 1 (当dt错误的时候；)；若存在此key，则迭代失败
                dt: 实际采用的时间步长。
        """
        # 检查计算模块是否有授权
        lic.check_once()

        if solver is None:
            solver = self.get_sol()

        if not isinstance(report, Map):
            report = self.get_report()
            assert isinstance(report, Map), "report must be a Map object"

        # 如下几个属性，都不是必须的，这里，给出默认值
        if fa_s is None:
            fa_s = 1000000000
        if fa_q is None:
            fa_q = 1000000000
        if fa_k is None:
            fa_k = 1000000000
        if ca_p is None:
            ca_p = 1000000000

        if dv_rela is not None:
            warnings.warn("Option dv_rela is deprecated and will be removed after 2027-6-15",
                          DeprecationWarning, stacklevel=2)

        if cfl is None and dv_rela is not None:
            cfl = dv_rela

        if cfl is None:  # 给定一个非常大，一定可以满足的值
            cfl = 1.0e30
        else:
            assert 0 < cfl, f'cfl must be greater than 0, but got {cfl}'

        if isinstance(pool, ThreadPool):  # 将任务放入线程池，然后立即返回
            core.seepage_fs_iterate(
                self.handle, model.handle, report.handle,
                dt, cfl,
                fa_s, fa_q, fa_k, ca_p,
                solver.handle, pool.handle
            )
            return None

        else:  # 此时，直接运行，并且返回计算的报告
            core.seepage_fs_iterate(
                self.handle, model.handle, report.handle,
                dt, cfl,
                fa_s, fa_q, fa_k, ca_p,
                solver.handle, 0
            )
            return report.to_dict()

    core.use(c_double, 'seepage_fs_get_dv', c_void_p)

    def get_recommended_dt(
            self, previous_dt: float,
            dv_relative: Optional[float] = None,
            cfl: Optional[float] = None
    ) -> float:
        """
        在调用了iterate函数之后，调用此函数，来获取更优的时间步长。
        特别注意，
        这个函数依赖于模型内部的一些缓存，因此，需要在每次iterate之后，立即调用此
        函数来获取建议的时间步长，否则如果缓存失效，则此函数可能出错。

        Args:
            previous_dt: 上一次的时间步长。应该为iterate函数返回报告中的dt(实际的dt)
            cfl: Courant-Friedrichs-Lewy数
            dv_relative: CFL数。
        Returns:
            float: 建议的时间步长。
        """
        warnings.warn("FlowSol.get_recommended_dt is deprecated (will be removed after 2027-6-8).", DeprecationWarning,
                      stacklevel=2)

        real_cfl = core.seepage_fs_get_dv(self.handle)
        real_cfl = max(1.0e-6, real_cfl)

        if dv_relative is not None:
            warnings.warn("dv_relative is deprecated and will be removed after 2027-6-15",
                          DeprecationWarning, stacklevel=2
                          )

        if cfl is None and dv_relative is not None:
            cfl = dv_relative

        return calc_recommended_dt(prev_dt=previous_dt, prev_cfl=real_cfl, target_cfl=cfl)


class ThermalSol(HasHandle):
    """
    热传导求解器
    """
    core.use(c_void_p, 'new_seepage_ts')
    core.use(None, 'del_seepage_ts', c_void_p)

    def __init__(self, handle: Optional[c_void_p] = None):
        """
        初始化热传导求解器类的实例。
        Args:
            handle: 句柄，默认为None。
        """
        super().__init__(handle, core.new_seepage_ts, core.del_seepage_ts)
        self.solver = None  # 线性求解器，线性方程组Ax=b的计算引擎
        self.report = None

    def get_report(self):
        """
        临时变量，存储计算的报告
        """
        if self.report is None:
            self.report = Map()
        return self.report

    def get_sol(self) -> 'ConjugateGradientSolver':
        if self.solver is None:
            self.solver = ConjugateGradientSolver(tolerance=1.0e-25)
        return self.solver

    core.use(None, 'seepage_ts_reset', c_void_p)

    def reset(self):
        """
        重置求解器. 当model的数据发生改变的时候，重置求解器，确保在后续迭代的时候，求解器内部的拓扑结构
        是正确的。
        注意：重置并在后续重建，会有一定的计算消耗。
        """
        core.seepage_ts_reset(self.handle)

    core.use(None, 'seepage_ts_iterate',
             c_void_p, c_void_p,
             c_void_p,
             c_size_t, c_size_t, c_size_t,
             c_double, c_double,
             c_void_p,
             c_void_p  # ThreadPool since 2025-7-25
             )

    def iterate(self, model: 'Seepage', dt: float, *, ca_t=None, ca_mc=None, fa_g=None, solver=None,
                pool=None, report=None, cfl=None):
        """
        对于此渗流模型，当定义了热传导相关的参数之后，可以作为一个热传导模型来使用。
        具体和Thermal模型类似。

        Args:
            model: 渗流模型对象。
            dt (float): 时间步长。
            ca_t (int): Cell的温度属性的ID。
            ca_mc (int): Cell范围内质量和比热的乘积。
            fa_g (int): Face导热的通量g；
                单位时间内通过Face的热量dH = g * dT。
            solver (ConjugateGradientSolver, optional): 求解器实例，
                默认为None。
            pool (ThreadPool, optional): 线程池实例，
                默认为None。
            report (Map, optional): 报告对象，默认为None。
            cfl (float, optional): Courant-Friedrichs-Lewy数，默认为None。

        Returns:
            dict: 包含迭代报告的字典。
        """
        lic.check_once()

        if dt <= 0 or ca_t is None or ca_mc is None or fa_g is None:  # 此时无法迭代，直接返回
            return None

        if solver is None:
            solver = self.get_sol()

        if not isinstance(report, Map):
            report = self.get_report()
            assert isinstance(report, Map), "report must be a Map object"

        if cfl is None:
            cfl = 1.0e100
        else:
            assert 0 < cfl, f"CFL must be greater than 0, but {cfl} is given"

        if isinstance(pool, ThreadPool):  # 将任务放入线程池，然后立即返回（需要在后续手动进行同步）
            core.seepage_ts_iterate(
                self.handle, model.handle, report.handle,
                ca_t, ca_mc, fa_g,
                dt, cfl,
                solver.handle, pool.handle
            )
            return None

        else:  # 此时，直接运行
            core.seepage_ts_iterate(
                self.handle, model.handle,
                report.handle,
                ca_t, ca_mc, fa_g,
                dt, cfl,
                solver.handle, 0
            )
            return report.to_dict()

    core.use(c_double, 'seepage_ts_get_de',
             c_void_p,
             c_void_p, c_size_t, c_size_t)

    def get_recommended_dt(
            self, model: 'Seepage', previous_dt: float,
            cfl: Optional[float] = None, *,
            dv_relative: Optional[float] = None,
            ca_t: Optional[int] = None,
            ca_mc: Optional[int] = None) -> float:
        """
        在调用了iterate函数之后，调用此函数，来获取更优的时间步长。
        特别注意，
        这个函数依赖于模型内部的一些缓存，因此，需要在每次iterate之后，立即调用此
        函数来获取建议的时间步长，否则如果缓存失效，则此函数可能出错。

        Args:
            model: 渗流模型对象。
            previous_dt: 上一次的时间步长。
            cfl: Courant-Friedrichs-Lewy数，默认为None。
            dv_relative: 相对变化阈值.
                         此参数即为Courant-Friedrichs-Lewy数，简称CFL数。
            ca_t: Cell的温度属性的ID，默认为None。
            ca_mc: Cell范围内质量和比热的乘积，默认为None。

        Returns:
            float: 建议的时间步长。
        """
        warnings.warn("ThermalSol.get_recommended_dt is deprecated (will be removed after 2027-6-8).",
                      DeprecationWarning,
                      stacklevel=2)
        assert ca_mc is not None, "ca_mc must be specified"
        assert ca_t is not None, "ca_t must be specified"

        prev_cfl = core.seepage_ts_get_de(
            self.handle,
            model.handle, ca_t, ca_mc)
        prev_cfl = max(1.0e-6, prev_cfl)

        if dv_relative is not None:
            warnings.warn("dv_relative is deprecated and will be removed after 2027-6-15",
                          DeprecationWarning, stacklevel=2
                          )

        if cfl is None and dv_relative is not None:
            cfl = dv_relative

        return calc_recommended_dt(prev_dt=previous_dt, prev_cfl=prev_cfl, target_cfl=cfl)


class Seepage(HasHandle, HasCells):
    """
    多相多组分渗流模型。Seepage类是进行热流化耦合模拟的基础。
    Seepage类主要涉及单元Cell，界面Face，流体Fluid，反应Reaction，流体定义FluDef几个概念。
    对于任意渗流场，均可以离散为由Cell<控制体：流体的存储空间>和Face<两个Cell之间的界面，流体的流动通道>组成的结构。
    """
    Reaction = Reaction
    FluDef = FluDef
    FluData = FluData
    Fluid = Fluid
    CellData = CellData
    Cell = Cell
    FaceData = FaceData
    Face = Face
    Injector = Injector
    FlowSol = FlowSol
    ThermalSol = ThermalSol

    core.use(c_void_p, 'new_seepage')
    core.use(None, 'del_seepage', c_void_p)

    def __init__(self, path: Optional[str] = None, handle: Optional[c_void_p] = None):
        """
        初始化 Seepage 类的实例。

        Args:
            path (str, optional): 要加载的文件的路径。默认为 None。
            handle (optional): 底层核心对象的句柄。默认为 None。
        """
        super().__init__(handle, core.new_seepage, core.del_seepage)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

        # 一个dict，用来存储模型的临时变量 (since 2025-11-21)
        self.temps = {}

        try:
            name = type(self).__name__
            log(f'{name} created', tag=f'{name}_Init')
        except:
            pass

    def __repr__(self) -> str:
        return (f'{type(self).__name__}(handle={int(self.handle)}, '
                f'cell_n={self.cell_number}, '
                f'face_n={self.face_number}, '
                f'note={self.get_note()})')

    core.use(None, 'seepage_save', c_void_p, c_char_p)

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
            core.seepage_save(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_load', c_void_p, c_char_p)

    def load(self, path: str):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 要读取的文件的路径。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.seepage_load(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'seepage_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt: str = 'binary') -> FileMap:
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary

        Args:
            fmt (str, optional): 序列化格式，
                可选值为 'text', 'xml', 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.seepage_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap: FileMap, fmt: str = 'binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 反序列化格式，可选值为 'text', 'xml', 'binary'。
                默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.seepage_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self) -> FileMap:
        """
        获取二进制格式的 FileMap 对象。

        Returns:
            FileMap: 包含二进制序列化数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value: FileMap):
        """
        从给定的 FileMap 对象中加载二进制格式的数据。

        Args:
            value (FileMap): 包含二进制序列化数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(c_char_p, 'seepage_get_text', c_void_p, c_char_p)
    core.use(None, 'seepage_set_text', c_void_p, c_char_p, c_char_p)

    def get_text(self, key: str) -> str:
        """
        返回模型内部存储的文本数据

        Args:
            key (str): 文本数据的键。

        Returns:
            str: 存储的文本数据。
        """
        return core.seepage_get_text(self.handle, make_c_char_p(key)).decode()

    def set_text(self, key: str, text: Union[str, Any]):
        """
        设置模型中存储的文本数据

        Args:
            key (str): 文本数据的键。
            text (str | Any): 要存储的文本数据。
        """
        if not isinstance(text, str):
            text = f'{text}'
        core.seepage_set_text(self.handle, make_c_char_p(key), make_c_char_p(text))

    def add_note(self, text: str):
        """
        向模型的注释中添加文本。

        Args:
            text (str): 要添加的文本。
        """
        self.set_text('note', self.get_text('note') + text)

    def get_note(self) -> str:
        """
        获取模型的注释。

        Returns:
            str: 模型的注释。
        """
        return self.get_text('note')

    core.use(None, 'seepage_clear', c_void_p)

    def clear(self) -> 'Seepage':
        """
        删除所有的Cell、Face和Injector。其它所有的数据保持不变。
        """
        core.seepage_clear(self.handle)
        return self

    core.use(None, 'seepage_clear_cells_and_faces', c_void_p)

    def clear_cells_and_faces(self) -> 'Seepage':
        """
        删除所有的Cell和Face。其它所有的数据保持不变。
        """
        core.seepage_clear_cells_and_faces(self.handle)
        return self

    core.use(None, 'seepage_remove_cell', c_void_p, c_size_t)

    def remove_cell(self, cell_id: int) -> 'Seepage':
        """
        移除给定id的(孤立的)cell
        注意：
            1. 这是一个复杂的操作，会涉及到很多连接关系，
                以及Cell和Face的顺序的改变
            2. 必须确保给定的cell为孤立的，即没有face和此cell连接，
                否则，此函数不执行操作.

        Args:
            cell_id (int): 要移除的单元的 ID。
        """
        core.seepage_remove_cell(self.handle, cell_id)
        return self

    core.use(None, 'seepage_remove_face', c_void_p, c_size_t)

    def remove_face(self, face_id: int) -> 'Seepage':
        """
        移除给定id的face
        注意：
            这是一个复杂的操作，会涉及到很多连接关系，以及Cell和Face的顺序的改变

        Args:
            face_id (int): 要移除的面的 ID。
        """
        core.seepage_remove_face(self.handle, face_id)
        return self

    core.use(None, 'seepage_remove_faces_of_cell', c_void_p, c_size_t)

    def remove_faces_of_cell(self, cell_id: int) -> 'Seepage':
        """
        移除给定id的cell的所有的face，使其成为一个孤立的cell
        注意：
            这是一个复杂的操作，会涉及到很多连接关系，以及Cell和Face的顺序的改变

        Args:
            cell_id (int): 要移除面的单元的 ID。
        """
        core.seepage_remove_faces_of_cell(self.handle, cell_id)
        return self

    core.use(c_size_t, 'seepage_get_cell_n', c_void_p)

    @property
    def cell_number(self) -> int:
        """
        Cell的数量

        Returns:
            int: 模型中单元的数量。
        """
        return core.seepage_get_cell_n(self.handle)

    core.use(c_size_t, 'seepage_get_face_n', c_void_p)

    @property
    def face_number(self) -> int:
        """
        Face的数量

        Returns:
            int: 模型中面的数量。
        """
        return core.seepage_get_face_n(self.handle)

    core.use(c_size_t, 'seepage_get_inj_n', c_void_p)
    core.use(None, 'seepage_set_inj_n', c_void_p, c_size_t)

    @property
    def injector_number(self) -> int:
        """
        Injector的数量

        Returns:
            int: 模型中注入器的数量。
        """
        return core.seepage_get_inj_n(self.handle)

    @injector_number.setter
    def injector_number(self, count: int):
        """
        设置注入点的数量. 注意，对于新的injector，所有的参数都将使用默认值，
            后续必须进行配置.
            请谨慎使用此接口来添加注入点.
            重设injector_number主要用来清空已有的注入点.

        Args:
            count (int): 要设置的注入器数量。
        """
        core.seepage_set_inj_n(self.handle, count)

    def get_cell(self, index: int) -> Optional['Cell']:
        """
        返回第index个Cell对象

        Args:
            index (int): 单元的索引。

        Returns:
            Cell: 第 index 个单元对象，如果索引无效则返回 None。
        """
        index_ = get_index(index, self.cell_number)
        if index_ is not None:
            return Cell(self, index_)
        else:
            return None

    def get_face(self, index: int) -> Optional['Face']:
        """
        返回第index个Face对象

        Args:
            index (int): 面的索引。

        Returns:
            Face: 第 index 个面对象，如果索引无效则返回 None。
        """
        index_ = get_index(index, self.face_number)
        if index_ is not None:
            return Face(self, index_)
        else:
            return None

    core.use(c_void_p, 'seepage_get_inj', c_void_p, c_size_t)

    def get_injector(self, index: int) -> Optional['Injector']:
        """
        返回第index个Injector对象

        Args:
            index (int): 注入器的索引。

        Returns:
            Injector: 第 index 个注入器对象，如果索引无效则返回 None。
        """
        index_ = get_index(index, self.injector_number)
        if index_ is not None:
            return Injector(handle=core.seepage_get_inj(self.handle, index_))
        else:
            return None

    core.use(c_size_t, 'seepage_add_cell', c_void_p)

    def add_cell(self, data: Optional['CellData'] = None) -> 'Cell':
        """
        添加一个新的Cell，并返回Cell对象

        Args:
            data (optional): 要克隆到新单元的数据。默认为 None。

        Returns:
            Cell: 新添加的单元对象。
        """
        cell_id = core.seepage_add_cell(self.handle)
        cell = self.get_cell(cell_id)
        assert cell is not None
        if data is not None:
            cell.clone(data)
        return cell

    core.use(c_size_t, 'seepage_add_face', c_void_p, c_size_t, c_size_t)

    def add_face(self, cell0, cell1,
                 data: Optional['FaceData'] = None) -> Optional['Face']:
        """
        在两个给定的Cell之间创建Face（注意：两个Cell之间只能有一个Face）

        Args:
            cell0: 第一个单元对象或其 ID。
            cell1: 第二个单元对象或其 ID。
            data (optional): 要克隆到新面的数据。默认为 None。

        Returns:
            Face: 新添加的面对象，如果创建失败则返回 None。
        """
        if isinstance(cell0, Cell):
            assert cell0.model.handle == self.handle
            cell0 = cell0.index

        if isinstance(cell1, Cell):
            assert cell1.model.handle == self.handle
            cell1 = cell1.index

        # 检查cell0和cell1是否有效索引
        assert cell0 < self.cell_number, f'cell0={cell0} >= cell_number={self.cell_number}'
        assert cell1 < self.cell_number, f'cell1={cell1} >= cell_number={self.cell_number}'
        assert cell0 != cell1, f'cell0={cell0} == cell1={cell1}'

        # 返回新添加的face，或者已经存在的face
        face_id = core.seepage_add_face(self.handle, cell0, cell1)
        face = self.get_face(face_id)
        # todo: 检查，这里的face应该必然不是None. @26-4-17
        if face is not None and data is not None:
            face.clone(data)
        return face

    core.use(c_size_t, 'seepage_add_inj', c_void_p)

    def add_injector(self, cell: Optional[Union['Cell', int]] = None,
                     fluid_id: Optional[Union[int, str, List[int], Tuple[int, ...]]] = None,
                     flu: Optional['FluData'] = None,
                     data: Optional['Injector'] = None,
                     pos: Optional[Union[List[float], Tuple[float]]] = None,
                     radi: Optional[float] = None,
                     opers: Optional[List[Any]] = None,
                     ca_mc: Optional[int] = None,
                     ca_t: Optional[int] = None,
                     g_heat: Optional[float] = None, value: Optional[float] = None
                     ) -> 'Injector':
        """
        添加一个注入点. 首先尝试拷贝data；
        然后尝试利用给定cell、fluid_id和flu进行设置。返回新添加的Injector对象

        Note that this function can be used for both
            fluid injection and heat injection.
            When the parameter "fluid_id" is given,
            this function will be used to inject fluid,
            and at this time, the parameter "opers" is
            used to set the injected volume flow rate;

        When the parameter "fluid_id" is not set and
            both the parameters "ca_mc" and "ca_t" are set,
            this function is used to inject heat.

        When injecting heat, there are two ways to inject it.
            When the parameter "g_heat" is given
            a value greater than 0, it injects heat according
            to temperature. At this time, "opers"
            is used to set the temperature of the boundary
            during heat injection. When the parameter
            "g_heat" is None, heat is injected according
             to the power, and "opers" is used to set
            the power of the heat injection.

        举例，如果要恒定功率加热，那么，将是类似下面的调用:
            power = 1 # 瓦特
            model.add_injector(pos=[0, 0, 0],
                ca_mc=model.reg_cell_key('mc'),
                ca_t=model.reg_cell_key('temperature'),
                value=power)
        """
        inj = self.get_injector(core.seepage_add_inj(self.handle))
        assert inj is not None

        if data is not None:
            assert isinstance(data, Injector)
            inj.clone(data)

        if cell is not None:  # 可以是cell对象，也可以是cell的id
            if isinstance(cell, Cell):
                assert cell.model.handle == self.handle  # 必须是同一个模型
                cell = cell.index
            inj.cell_id = cell

        if fluid_id is not None:
            if isinstance(fluid_id, str):  # 给定组分名字，则从model中查找   since 2023-10-24
                fluid_id = self.find_fludef(name=fluid_id)
                assert fluid_id is not None
            assert isinstance(fluid_id,
                              (int, tuple, list)), f'fluid_id must be int, tuple, or list, but got {type(fluid_id)}'
            inj.set_fid(fluid_id)

        if isinstance(flu, FluData):  # 只有在等于FluData的时候才使用.
            inj.flu.clone(flu)
        else:
            assert flu is None, f"flu should be FluData or None, but got {type(flu).__name__}"

        if pos is not None:  # 给定注入的位置，后续，则自动去查找附近的cell
            inj.pos = pos

        if radi is not None:  # 查找的半径
            inj.radi = radi

        if ca_mc is not None:  # Cell的属性
            inj.ca_mc = ca_mc

        if ca_t is not None:  # Cell的属性(温度属性，在注入热量的时候会被修改)
            inj.ca_t = ca_t

        if g_heat is not None:  # 恒定温度加热的时候需要给定
            inj.g_heat = g_heat

        if opers is not None:  # 对属性的操作定时器
            for item in opers:
                inj.add_oper(*item)

        if value is not None:  # 当前的值
            inj.value = value

        return inj

    @property
    def cells(self) -> Iterable['Cell']:
        """
        模型中所有的Cell

        Returns:
            Iterator: 包含所有单元对象的迭代器。
        """
        return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

    @property
    def faces(self) -> Iterable['Face']:
        """
        模型中所有的Face

        Returns:
            Iterator: 包含所有面对象的迭代器。
        """
        return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

    @property
    def injectors(self) -> Iterable['Injector']:
        """
        模型中所有的Injector

        Returns:
            Iterator: 包含所有注入器对象的迭代器。
        """
        return Iterator(self, self.injector_number, lambda m, ind: m.get_injector(ind))

    core.use(None, 'seepage_apply_injs', c_void_p, c_double, c_double, c_void_p)

    def apply_injectors(self, *, time: Optional[float] = None, dt: Optional[float] = None,
                        pool: Optional[ThreadPool] = None):
        """
        所有的注入点执行注入操作.

        Args:
            time (float, optional): 时间。默认为 None。
            dt (float, optional): 时间步长。默认为 None。
            pool: 线程池
        """
        if time is None:
            warnings.warn(
                'time is None for Injector, use time=0 as default')
            time = 0
        if dt is None:
            return
        core.seepage_apply_injs(
            self.handle, time, dt,
            pool.handle if isinstance(pool, ThreadPool) else 0
        )

    core.use(None, 'seepage_append', c_void_p, c_void_p, c_bool, c_size_t)

    def append(self, other: "Seepage", cell_i0: Optional[int] = None, with_faces: bool = True) -> 'Seepage':
        """
        将other中所有的Cell和Face追加到这个模型中，并且从这个模型的cell_i0开始，
        和从other新添加的cell之间
        建立一一对应的Face. 默认情况下，仅仅追加，但是不建立和现有的Cell的连接。
            2023-4-19

        注意：
            仅仅追加Cell和Face，other中的其它数据，比如反应、注入点、相渗曲线等，
            均不会被追加到这个
            模型中。

        当with_faces为False的时候，则仅仅追加other中的Cell (other中的 Face 不被追加)

        注意函数实际的执行顺序：
            第一步：添加other的所有的Cell
            第二步：添加other的所有的Face (with_faces属性为True的时候)
            第三步：创建一些额外Face连接 (从这个模型的cell_i0开始，和other的cell之间)

        Args:
            other (Seepage): 要追加的另一个 Seepage 对象。
            cell_i0 (int, optional): 开始建立连接的单元索引。默认为 None。
            with_faces (bool, optional): 是否追加面。默认为 True。

        Returns:
            Seepage: 当前 Seepage 对象。
        """
        assert isinstance(other, Seepage)
        if cell_i0 is None:
            cell_i0 = self.cell_number
        core.seepage_append(self.handle, other.handle, with_faces, cell_i0)
        return self

    core.use(None, 'seepage_pop_cells', c_void_p, c_size_t)

    def pop_cells(self, count: int = 1):
        """
        删除最后count个Cell的所有的Face，然后移除最后count个Cell

        Args:
            count (int, optional): 要删除的单元数量。默认为 1。

        Returns:
            Seepage: 当前 Seepage 对象。
        """
        core.seepage_pop_cells(self.handle, count)
        return self

    core.use(c_double, 'seepage_get_gravity', c_void_p, c_size_t)
    core.use(None, 'seepage_set_gravity', c_void_p, c_size_t, c_double)

    @property
    def gravity(self) -> Tuple[float, float, float]:
        """
        重力加速度，默认为(0.0, 0.0, 0.0)

        Returns:
            tuple: 重力加速度的三维向量。
        """
        return (core.seepage_get_gravity(self.handle, 0),
                core.seepage_get_gravity(self.handle, 1),
                core.seepage_get_gravity(self.handle, 2))

    @gravity.setter
    def gravity(self, value: Union[Tuple[float], List[float]]):
        """
        重力加速度，默认为(0.0, 0.0, 0.0)

        Args:
            value (tuple): 要设置的重力加速度的三维向量。
        """
        assert len(value) == 3
        for dim in range(3):
            core.seepage_set_gravity(self.handle, dim, value[dim])

    core.use(c_size_t, 'seepage_get_gr_n', c_void_p)

    @property
    def gr_number(self) -> int:
        """
        返回model中gr的数量

        Returns:
            int: 模型中 gr 的数量。
        """
        return core.seepage_get_gr_n(self.handle)

    core.use(None, 'seepage_set_gr_n', c_void_p, c_size_t)

    @gr_number.setter
    def gr_number(self, value: int):
        """
        设置模型中gr的数量
        Args:
            value:
        """
        core.seepage_set_gr_n(self.handle, value)

    core.use(c_void_p, 'seepage_get_gr',
             c_void_p, c_size_t)

    def get_gr(self, index: int) -> Optional[Interp1]:
        """
        返回序号为idx的gr

        Args:
            index (int): gr 的索引。

        Returns:
            Interp1: 序号为 idx 的 gr 对象，如果索引无效则返回 None。
        """
        idx_ = get_index(index, self.gr_number)
        if idx_ is not None:
            return Interp1(handle=core.seepage_get_gr(self.handle, idx_))
        else:
            return None

    @property
    def grs(self) -> Iterable[Interp1]:
        """
        迭代所有的gr

        Returns:
            Iterator: 包含所有 gr 对象的迭代器。
        """
        return Iterator(model=self, count=self.gr_number,
                        get=lambda m, ind: m.get_gr(ind))

    def add_gr(self, gr, need_id: bool = False) -> Union[Interp1, int]:
        """
        添加一个gr. 其中gr应该为Interp1类型.

        Args:
            gr (Interp1 or tuple): 要添加的 gr 对象或数据。
            need_id (bool, optional): 是否返回添加的 gr 的 ID。默认为 False。

        Returns:
            Interp1 or int: 如果 need_id 为 False，则返回添加的 gr 对象；
            否则返回添加的 gr 的 ID。
        """
        idx = self.gr_number
        self.gr_number = idx + 1
        if isinstance(gr, Interp1):
            temp = self.get_gr(idx)  # 确保gr存在
            assert temp is not None
            temp.clone(gr)
        else:
            assert len(gr) == 2
            assert len(gr[0]) == len(gr[1])
            assert len(gr[0]) >= 2
            temp = self.get_gr(idx)  # 确保gr存在
            assert temp is not None
            temp.set_xy(gr[0], gr[1])
        if need_id:
            return idx  # 返回gr的序号
        else:
            res = self.get_gr(idx)
            assert res is not None
            return res  # 返回gr对象

    def clear_grs(self):
        """
        删除模型中所有的gr
        """
        self.gr_number = 0

    core.use(c_size_t, 'seepage_get_kr_n', c_void_p)
    core.use(None, 'seepage_set_kr_n', c_void_p, c_size_t)

    @property
    def kr_number(self) -> int:
        """
        相渗曲线的数量.
        注意:
            对于 0 <= id < fluid_n 的曲线，是各个流体的默认相渗.
            所以，如果需要对某些相渗进行特殊设置，务必去使用id大于流体数量的曲线.

        Returns:
            int: 模型中相渗曲线的数量。
        """
        return core.seepage_get_kr_n(self.handle)

    @kr_number.setter
    def kr_number(self, value: int):
        """
        设置模型中相渗曲线的数量

        Args:
            value (int): 要设置的相渗曲线的数量。
        """
        core.seepage_set_kr_n(self.handle, value)

    core.use(None, 'seepage_set_kr',
             c_void_p, c_size_t, c_void_p)

    def set_kr(self, index=None, saturation=None, kr=None):
        """
        设置第index个相对渗透率曲线。注意模型内部最多可以存储<10000个相对渗透率曲线>
            以及一个<默认相渗>。
            如果给定的Index大于10000，则此函数将修改默认相对渗透率曲线，
            否则会修改给定index的数据。
            当index为None的时候，则修改默认相渗曲线。
        在不同的Face中，可以选用不同的相渗曲线(参考Face.set_ikr)，
            但是默认条件下，如果不加设置，则第i种流体，将默认使用第i个相渗曲线.
            如果计算中需要使用到第i个相渗，但第i个相渗不存在，则会用<默认曲线>来代替。
        --
        通过这里Seepage.set_kr和Face.set_ikr配合，可以在模型的不同区域来配置不同的相渗.

        Args:
            index (int or str, optional): 要设置的相渗曲线的索引或名称。
                默认为 None。
            saturation (Vector or list, optional): 饱和度数据。
                默认为 None。
            kr (Vector or Interp1, optional): 相对渗透率数据或曲线对象。
                默认为 None。
        """
        assert kr is not None

        # 获得相对渗透率曲线数据，并且存储在tmp中
        if isinstance(kr, Interp1):
            assert saturation is None
            tmp = kr
        else:
            if not isinstance(saturation, Vector):
                saturation = Vector(saturation)
            if not isinstance(kr, Vector):
                kr = Vector(kr)
            assert len(saturation) > 0 and len(kr) > 0
            tmp = Interp1(x=saturation, y=kr)

        # 检查流体的id
        if index is None:
            index = IDX_INF  # Now, modify the default kr
        else:
            if isinstance(index, str):  # 此时，通过查表来获得流体的id. since 2024-5-8
                idx = self.find_fludef(name=index)
                assert len(
                    idx) == 1, (f'You can not set the kr of {index} '
                                f'while its id is: {idx}')
                index = idx[0]

        # 最终，设置相渗数据
        core.seepage_set_kr(self.handle, index, tmp.handle)

    core.use(c_void_p, 'seepage_get_kr', c_void_p, c_size_t)

    def get_kr(self, index=None, saturation=None):
        """
        返回第index个相对渗透率曲线(或者在给定saturation的时候，返回相对渗透率数值)。
        如果给定Index的kr不存在，则使用默认的kr

        Args:
            index (int): 要获取的相渗曲线的索引。
            saturation (float, optional): 饱和度值。默认为 None。

        Returns:
            Interp1 or float: 如果 saturation 为 None，
                则返回相渗曲线对象；否则返回相对渗透率数值。
        """
        if index is None:
            index = IDX_INF
        handle = core.seepage_get_kr(self.handle, index)
        assert handle > 0
        curve = Interp1(handle=handle)
        if saturation is None:
            return curve
        else:
            return curve.get(saturation)

    def set_default_kr(self, value):
        """
        set the default kr. since 2024-5-8

        Args:
            value (Interp1 or tuple): 要设置的默认相渗曲线对象或数据。
        """
        if isinstance(value, Interp1):
            self.set_kr(kr=value)
            return
        else:
            x = value[0]
            y = value[1]
            self.set_kr(saturation=x, kr=y)
            return

    def add_kr(self, saturation=None, kr=None, need_id=False):
        """
        添加一个相渗曲线，并且返回ID

        Args:
            saturation (Vector or list, optional): 饱和度数据。默认为 None。
            kr (Vector or Interp1, optional): 相对渗透率数据或曲线对象。默认为 None。
            need_id (bool, optional): 是否返回添加的相渗曲线的 ID。默认为 False。

        Returns:
            Interp1 or int: 如果 need_id 为 False，则返回添加的相渗曲线对象；
            否则返回添加的相渗曲线的 ID。
        """
        index = self.kr_number
        self.set_kr(index=index, saturation=saturation, kr=kr)
        if need_id:
            return index
        else:
            return self.get_kr(index)

    core.use(c_size_t, 'seepage_get_curve_n', c_void_p)

    @property
    def curve_number(self):
        """
        曲线的数量.

        Returns:
            int: 模型中曲线的数量。
        """
        return core.seepage_get_curve_n(self.handle)

    core.use(c_void_p, 'seepage_get_curve', c_void_p, c_size_t)

    def get_curve(self, index):
        """
        返回第index个曲线

        Args:
            index (int): 要获取的曲线的索引。

        Returns:
            Interp1: 第 index 个曲线对象，如果索引无效则返回 None。
        """
        handle = core.seepage_get_curve(self.handle, index)
        if handle:
            return Interp1(handle=handle)
        else:
            return None

    core.use(None, 'seepage_set_curve', c_void_p, c_size_t, c_void_p)

    def set_curve(self, index, curve):
        """
        设置第index个曲线

        Args:
            index (int): 要设置的曲线的索引。
            curve (Interp1): 要设置的曲线对象。
        """
        if isinstance(curve, Interp1):
            core.seepage_set_curve(self.handle, index, curve.handle)

    core.use(c_size_t, 'seepage_get_fludef_n', c_void_p)

    @property
    def fludef_number(self):
        """
        模型内存储的流体定义的数量

        Returns:
            int: 模型中流体定义的数量。
        """
        return core.seepage_get_fludef_n(self.handle)

    core.use(None, 'seepage_set_fludef_n', c_void_p, c_size_t)

    @fludef_number.setter
    def fludef_number(self, val):
        """
        设置模型中流体定义的数量
        Args:
            val (int): 要设置的流体定义数量。
        """
        core.seepage_set_fludef_n(self.handle, val)

    core.use(c_bool, 'seepage_find_fludef', c_void_p, c_char_p, c_void_p)

    def find_fludef(self, name, buffer=None):
        """
        查找给定name的流体定义的ID

        Args:
            name (str): 要查找的流体定义的名称。
            buffer (UintVector, optional): 存储查找结果的缓冲区。默认为 None。

        Returns:
            list: 找到的流体定义的 ID 列表，如果未找到则返回空列表。
        """
        if not isinstance(buffer, UintVector):
            buffer = UintVector()
        else:
            buffer.size = 0
        found = core.seepage_find_fludef(self.handle, make_c_char_p(name), buffer.handle)
        if found:
            return buffer.to_list()
        return None

    core.use(c_void_p, 'seepage_get_fludef', c_void_p, c_size_t, c_size_t, c_size_t)

    def get_fludef(self, key):
        """
        返回给定序号或者名字的流体定义. key可以是str类型/int类型/list类型.

        Args:
            key (str or int or list): 流体定义的名称、序号或序号列表。

        Returns:
            FluDef: 找到的流体定义对象，如果未找到则返回 None。
        """
        if isinstance(key, str):
            key = self.find_fludef(key)
        if key is None:
            return None
        handle = core.seepage_get_fludef(self.handle, *parse_fid3(key))
        if handle:
            return FluDef(handle=handle)
        else:
            return None

    def add_fludef(self, fdef, need_id=False, name=None):
        """
        添加一个流体定义

        Args:
            fdef (FluDef or list): 要添加的流体定义对象或数据。
            need_id (bool, optional): 是否返回添加的流体定义的 ID。默认为 False。
            name (str, optional): 流体定义的名称。默认为 None。

        Returns:
            FluDef or int: 如果 need_id 为 False，
            则返回添加的流体定义对象；否则返回添加的流体定义的 ID。
        """
        if not isinstance(fdef, FluDef):
            # 此时，可能是一个list
            fdef = FluDef.create(fdef)
        idx = self.fludef_number
        self.fludef_number = idx + 1
        result = self.get_fludef(idx)
        result.clone(fdef)
        if name is not None:
            result.name = name
        if need_id:
            return idx
        else:
            return result

    def clear_fludefs(self):
        """
        清除所有的流体定义
        """
        self.fludef_number = 0

    def set_fludefs(self, *args):
        """
        清除并设置所有的流体定义

        Args:
            *args (FluDef or list): 要设置的流体定义对象或数据。
        """
        self.clear_fludefs()
        for item in args:
            self.add_fludef(item)

    core.use(c_size_t, 'seepage_get_pc_n', c_void_p)

    @property
    def pc_number(self):
        """
        模型中存储的毛管压力曲线的数量

        Returns:
            int: 模型中毛管压力曲线的数量。
        """
        return core.seepage_get_pc_n(self.handle)

    core.use(None, 'seepage_set_pc_n', c_void_p, c_size_t)

    @pc_number.setter
    def pc_number(self, val):
        """
        设置模型中毛管压力曲线的数量
        Args:
            val (int): 要设置的毛管压力曲线数量。
        """
        core.seepage_set_pc_n(self.handle, val)

    core.use(c_void_p, 'seepage_get_pc', c_void_p, c_size_t)

    def get_pc(self, index):
        """
        返回给定序号的毛管压力曲线

        Args:
            index (int): 毛管压力曲线的索引。

        Returns:
            Interp1: 序号为 idx 的毛管压力曲线对象，如果索引无效则返回 None。
        """
        index = get_index(index, self.pc_number)
        if index is not None:
            return Interp1(handle=core.seepage_get_pc(self.handle, index))
        else:
            return None

    def add_pc(self, data, need_id=False):
        """
        添加一个毛管压力曲线

        Args:
            data (Interp1): 要添加的毛管压力曲线对象。
            need_id (bool, optional): 是否返回添加的毛管压力曲线的 ID。默认为 False。

        Returns:
            Interp1 or int: 如果 need_id 为 False，
            则返回添加的毛管压力曲线对象；否则返回添加的毛管压力曲线的 ID。
        """
        assert isinstance(data, Interp1)
        idx = self.pc_number
        self.pc_number = idx + 1
        temp = self.get_pc(idx)
        temp.clone(data)
        if need_id:
            return idx
        else:
            return temp

    def clear_pcs(self):
        """
        清除所有的毛管压力曲线
        """
        self.pc_number = 0

    core.use(c_size_t, 'seepage_get_reaction_n', c_void_p)

    @property
    def reaction_number(self):
        """
        模型中反应的数量

        Returns:
            int: 模型中反应的数量。
        """
        return core.seepage_get_reaction_n(self.handle)

    core.use(None, 'seepage_set_reaction_n',
             c_void_p, c_size_t)

    @reaction_number.setter
    def reaction_number(self, val):
        """
        设置模型中反应的数量
        Args:
            val (int): 要设置的反应数量。
        """
        core.seepage_set_reaction_n(self.handle, val)

    core.use(c_void_p, 'seepage_get_reaction', c_void_p, c_size_t)

    def get_reaction(self, index):
        """
        返回第idx个反应对象

        Args:
            index (int): 反应的索引。

        Returns:
            Reaction: 第 idx 个反应对象，如果索引无效则返回 None。
        """
        index = get_index(index, self.reaction_number)
        if index is not None:
            return Reaction(
                handle=core.seepage_get_reaction(self.handle, index))
        else:
            return None

    def add_reaction(self, data, need_id=False):
        """
        添加一个反应

        Args:
            data (Reaction): 要添加的反应对象。
            need_id (bool, optional): 是否返回添加的反应的 ID。默认为 False。

        Returns:
            Reaction or int: 如果 need_id 为 False，
            则返回添加的反应对象；否则返回添加的反应的 ID。
        """
        if not isinstance(data, Reaction):
            assert isinstance(data, dict)
            from zmlx.react import alg
            warnings.warn(
                'The none Reaction type will '
                'not be supported after 2026-2-7',
                DeprecationWarning, stacklevel=2)
            return alg.add_reaction(self, data, need_id=need_id)
        else:
            idx = self.reaction_number
            self.reaction_number = idx + 1
            self.get_reaction(idx).clone(data)
            if need_id:
                return idx
            else:
                return self.get_reaction(idx)

    def clear_reactions(self) -> 'Seepage':
        """
        清除所有的反应

        Returns:
            None
        """
        self.reaction_number = 0
        return self

    core.use(None, 'seepage_remove_reaction',
             c_void_p, c_size_t)

    def remove_reaction(self, index) -> 'Seepage':
        """
        移除给定序号的一个反应

        Args:
            index (int): 要移除的反应的序号

        Returns:
            None
        """
        index = get_index(index, self.reaction_number)
        if index is not None:
            core.seepage_remove_reaction(self.handle, index)
        return self

    def create_reaction(self, **kwargs):
        """
        根据给定的参数，创建一个反应（可能需要读取model中的流体定义，
        以及会在model中注册属性）

        Args:
            **kwargs: 创建反应所需的参数

        Returns:
            反应对象

        Warnings:
            zml.Reaction.create_reaction 将在2026-2-7之后移除，
            请使用 zmlx.react.create_reaction 代替。
        """
        warnings.warn(
            'zml.Reaction.create_reaction will be '
            'remove after 2026-2-7',
            DeprecationWarning, stacklevel=2)
        from zmlx.react.alg import create_reaction as create
        return create(self, **kwargs)

    @property
    def reactions(self) -> Iterable['Reaction']:
        """
        迭代所有的反应

        Returns:
            Iterator: 包含所有反应对象的迭代器。
        """
        return Iterator(model=self, count=self.reaction_number,
                        get=lambda m, ind: m.get_reaction(ind))

    core.use(c_void_p, 'seepage_get_buffer', c_void_p, c_char_p)

    def get_buffer(self, key):
        """
        返回模型内的一个缓冲区（如果不存在，则自动创建并返回）.

        Args:
            key (str): 缓冲区的键

        Returns:
            Vector: 模型内的缓冲区对象
        """
        return Vector(handle=core.seepage_get_buffer(self.handle, make_c_char_p(key)))

    core.use(None, 'seepage_del_buffer', c_void_p, c_char_p)

    def del_buffer(self, key):
        """
        删除模型内的缓冲区(如果缓冲区不存在，则不执行操作)

        Args:
            key (str): 要删除的缓冲区的键

        Returns:
            self: 返回当前对象
        """
        core.seepage_del_buffer(self.handle, make_c_char_p(key))
        return self

    core.use(c_bool, 'seepage_has_tag',
             c_void_p, c_char_p)

    def has_tag(self, tag):
        """
        返回模型是否包含给定的这个标签

        Args:
            tag (str): 要检查的标签

        Returns:
            bool: 如果模型包含该标签返回True，否则返回False
        """
        return core.seepage_has_tag(self.handle, make_c_char_p(tag))

    def not_has_tag(self, tag):
        """
        返回模型是否不包含给定的这个标签

        Args:
            tag (str): 要检查的标签

        Returns:
            bool: 如果模型不包含该标签返回True，否则返回False
        """
        return not self.has_tag(tag)

    core.use(None, 'seepage_add_tag', c_void_p, c_char_p)

    def add_tag(self, tag, *tags):
        """
        在模型中添加给定的标签. 支持添加多个(since 2024-2-23)

        Args:
            tag (str): 要添加的第一个标签
            *tags (str): 要添加的其他标签

        Returns:
            self: 返回当前对象
        """
        core.seepage_add_tag(self.handle, make_c_char_p(tag))
        # 再添加多个.
        if len(tags) > 0:
            for tag in tags:
                self.add_tag(tag=tag)
        return self

    core.use(None, 'seepage_del_tag', c_void_p, c_char_p)

    def del_tag(self, tag, *tags):
        """
        删除模型中的给定的标签

        Args:
            tag (str): 要删除的第一个标签
            *tags (str): 要删除的其他标签

        Returns:
            self: 返回当前对象
        """
        core.seepage_del_tag(self.handle, make_c_char_p(tag))
        if len(tags) > 0:
            for tag in tags:
                self.del_tag(tag=tag)
        return self

    core.use(None, 'seepage_clear_tags', c_void_p)

    def clear_tags(self) -> 'Seepage':
        """
        清除模型中的所有标签

        Returns:
            None
        """
        core.seepage_clear_tags(self.handle)
        return self

    core.use(c_int64, 'seepage_reg_key', c_void_p, c_char_p, c_char_p)

    def reg_key(self, ty, key):
        """
        注册一个键。其中ty为该键的前缀. 在注册的时候，将自动根据注册的顺序从0开始编号.

        说明:
            在之前的版本中，不依赖model中定义的key，反之，对于每一个属性，都有一个确定的键值.
            这样的问题是，每个具体的问题所用的key不同，这样全部采用静态的定义，就会浪费空间.
            因此，考虑将各个属性键的含义存储到model中，从而在计算的时候去动态读取. 这样，在
            定义方法的时候，只需要去记录键的名字，而不需要记录具体的键值.

        关于前缀：
            m_: 模型的属性
            n_: Cell属性
            b_: Face属性
            f_: 流体的属性

        Args:
            ty (str): 键的前缀
            key (str): 要注册的键

        Returns:
            int: 注册的键值
        """
        return core.seepage_reg_key(self.handle, make_c_char_p(ty), make_c_char_p(key))

    core.use(c_int64, 'seepage_get_key', c_void_p, c_char_p)

    def get_key(self, key):
        """
        返回键值：主要用于存储指定的属性ID

        Args:
            key (str): 要获取键值的键

        Returns:
            int: 键值，如果键值小于9999则返回，否则不返回
        """
        val = core.seepage_get_key(self.handle, make_c_char_p(key))
        if val < 9999:
            return val
        else:
            return None

    core.use(None, 'seepage_set_key', c_void_p, c_char_p, c_int64)

    def set_key(self, key, value):
        """
        设置键值. 会直接覆盖现有的键值

        Args:
            key (str): 要设置键值的键
            value (int): 要设置的键值

        Returns:
            self: 返回当前对象
        """
        if value is None:
            self.del_key(key)
            return self
        if value >= 9999:
            self.del_key(key)
            return self
        else:
            core.seepage_set_key(self.handle, make_c_char_p(key), value)
            return self

    core.use(None, 'seepage_del_key', c_void_p, c_char_p)

    def del_key(self, key, *keys):
        """
        删除键值

        Args:
            key (str): 要删除的第一个键
            *keys (str): 要删除的其他键

        Returns:
            self: 返回当前对象
        """
        core.seepage_del_key(self.handle, make_c_char_p(key))
        if len(keys) > 0:
            for key in keys:
                self.del_key(key=key)
        return self

    core.use(None, 'seepage_clear_keys', c_void_p)

    def clear_keys(self):
        """
        清除模型中的所有键值

        Returns:
            self: 返回当前对象
        """
        core.seepage_clear_keys(self.handle)
        return self

    def reg_model_key(self, key):
        """
        注册并返回用于model的键值

        Args:
            key (str): 要注册的键

        Returns:
            int: 注册的键值
        """
        return self.reg_key('m_', key)

    def reg_cell_key(self, key):
        """
        注册并返回用于cell的键值

        Args:
            key (str): 要注册的键

        Returns:
            int: 注册的键值
        """
        return self.reg_key('n_', key)

    def reg_face_key(self, key):
        """
        注册并返回用于face的键值

        Args:
            key (str): 要注册的键

        Returns:
            int: 注册的键值
        """
        return self.reg_key('b_', key)

    def reg_flu_key(self, key):
        """
        注册并返回用于flu的键值

        Args:
            key (str): 要注册的键

        Returns:
            int: 注册的键值
        """
        return self.reg_key('f_', key)

    def get_model_key(self, key):
        """
        返回用于model的键值

        Args:
            key (str): 要获取键值的键

        Returns:
            int: 键值
        """
        return self.get_key('m_' + key)

    def get_cell_key(self, key):
        """
        返回用于cell的键值

        Args:
            key (str): 要获取键值的键

        Returns:
            int: 键值
        """
        return self.get_key('n_' + key)

    def get_face_key(self, key):
        """
        返回用于face的键值

        Args:
            key (str): 要获取键值的键

        Returns:
            int: 键值
        """
        return self.get_key('b_' + key)

    def get_flu_key(self, key):
        """
        返回用于flu的键值

        Args:
            key (str): 要获取键值的键

        Returns:
            int: 键值
        """
        return self.get_key('f_' + key)

    core.use(None, 'seepage_get_keys', c_void_p, c_void_p)

    def get_keys(self):
        """
        返回所有的keys（作为dict）

        Returns:
            dict: 包含所有键值的字典
        """
        s = String()
        core.seepage_get_keys(self.handle, s.handle)
        return eval(s.to_str())

    def set_keys(self, **kwargs):
        """
        设置keys. 会覆盖现有的键值.

        Args:
            **kwargs: 要设置的键值对

        Returns:
            self: 返回当前对象
        """
        for key, value in kwargs.items():
            self.set_key(key, value)
        return self

    core.use(None, 'seepage_get_tags', c_void_p, c_void_p)

    def get_tags(self):
        """
        返回所有的tags（作为set）

        Returns:
            set: 包含所有标签的集合
        """
        s = String()
        core.seepage_get_tags(self.handle, s.handle)
        return eval(s.to_str())

    core.use(c_double, 'seepage_get_attr', c_void_p, c_size_t)
    core.use(None, 'seepage_set_attr', c_void_p, c_size_t, c_double)

    def get_attr(self, index, default_val=None, **valid_range):
        """
        模型的第index个自定义属性

        Args:
            index (int or str): 自定义属性的索引或键
            default_val (any, optional): 如果属性不存在或不在有效范围内，
                返回的默认值。默认为None。
            **valid_range: 属性的有效范围

        Returns:
            any: 自定义属性的值，如果属性不存在或不在有效范围内，返回默认值。
        """
        if isinstance(index, str):
            index = self.get_model_key(key=index)
        if index is None:
            return default_val
        value = core.seepage_get_attr(self.handle, index)
        if attr_in_range(value, **valid_range):
            return value
        else:
            return default_val

    def set_attr(self, index, value):
        """
        模型的第index个自定义属性

        Args:
            index (int or str): 自定义属性的索引或键
            value (float): 要设置的属性值

        Returns:
            self: 返回当前对象
        """
        if isinstance(index, str):
            index = self.reg_model_key(key=index)
        if index is None:
            return self
        if value is None:
            value = 1.0e200
        core.seepage_set_attr(self.handle, index, value)
        return self

    core.use(c_size_t, 'seepage_get_nearest_cell_id', c_void_p, c_double, c_double, c_double, c_size_t, c_size_t)

    def get_nearest_cell(self, pos, i_beg=None, i_end=None) -> Optional['Cell']:
        """
        返回与给定位置距离最近的cell (在[i_beg, i_end)的范围内搜索)

        Args:
            pos (tuple | list): 位置坐标 (x, y, z) 注意，如果希望忽略某一个坐标维度，则将相应的维度设置为None
            i_beg (int, optional): 搜索范围的起始索引。默认为None。
            i_end (int, optional): 搜索范围的结束索引。默认为None。

        Returns:
            Cell: 距离给定位置最近的cell对象，如果未找到则返回None。
        """
        cell_n = self.cell_number
        if cell_n > 0:
            pos = [1.0e210 if pos[i] is None else pos[i] for i in range(3)]
            index = core.seepage_get_nearest_cell_id(
                self.handle,
                pos[0],
                pos[1],
                pos[2],
                i_beg if i_beg is not None else 0,
                i_end if i_end is not None else cell_n)
            return self.get_cell(index)
        else:
            return None

    core.use(None, 'seepage_clone', c_void_p, c_void_p)

    def clone(self, other: 'Seepage') -> 'Seepage':
        """
        从另外一个模型克隆数据.

        Args:
            other (Seepage): 要克隆数据的源模型

        Returns:
            self: 返回当前对象
        """
        if other is not None:
            assert isinstance(other, Seepage)
            core.seepage_clone(self.handle, other.handle)
        return self

    def get_copy(self) -> 'Seepage':
        """
        返回一个拷贝.

        Returns:
            Seepage: 当前模型的拷贝对象
        """
        res = Seepage()
        res.clone(self)
        return res

    core.use(None, 'seepage_clone_cells', c_void_p, c_void_p, c_size_t, c_size_t, c_size_t)

    def clone_cells(self, ibeg0: int, other: 'Seepage', ibeg1: int, count: int) -> 'Seepage':
        """
        拷贝Cell数据:
            将other的[ibeg1, ibeg1+count)范围内的Cell的数据，
            拷贝到self的[ibeg0, ibeg0+count)范围内的Cell
        此函数会自动跳过不存在的CellID.
            since 2023-4-20

        Args:
            ibeg0 (int): 目标模型中Cell的起始索引
            other (Seepage): 源模型
            ibeg1 (int): 源模型中Cell的起始索引
            count (int): 要拷贝的Cell数量

        Returns:
            None
        """
        if count > 0:
            assert isinstance(other, Seepage), 'other must be a Seepage object'
            core.seepage_clone_cells(self.handle, other.handle, ibeg0, ibeg1, count)
        return self

    core.use(None, 'seepage_clone_inner_faces', c_void_p, c_void_p, c_size_t, c_size_t, c_size_t)

    def clone_inner_faces(self, ibeg0: int, other: 'Seepage', ibeg1: int, count: int):
        """
        拷贝Face数据:
            将other的[ibeg1, ibeg1+count)范围内的Cell对应的Face，
            拷贝到self的[ibeg0, ibeg0+count)范围内的Cell对应的Face
        此函数会自动跳过不存在的CellID.
            since 2023-9-3

        Args:
            ibeg0 (int): 目标模型中Cell对应的Face的起始索引
            other (Seepage): 源模型
            ibeg1 (int): 源模型中Cell对应的Face的起始索引
            count (int): 要拷贝的Cell对应的Face的数量

        Returns:
            None
        """
        if count <= 0:
            return
        assert isinstance(other, Seepage), 'other must be a Seepage object'
        core.seepage_clone_inner_faces(self.handle, other.handle, ibeg0, ibeg1, count)

    core.use(None, 'seepage_update_den',
             c_void_p, c_size_t, c_size_t, c_size_t,
             c_void_p, c_size_t,
             c_double, c_double, c_double, c_void_p)

    def update_den(self, fluid_id=None, kernel=None,
                   relax_factor=1.0,
                   fa_t=None, min=-1, max=-1, pool=None):
        """
        更新流体的密度。其中
            fluid_id为需要更新的流体的ID (当None的时候，则更新所有)
            kernel为Interp2(p,T)
            relax_factor为松弛因子，限定密度的最大变化幅度.

        注意:
            当 relax_factor <= 0的时候，内核不会执行任何更新
            (since 2023-9-27)

        Args:
            fluid_id (int, optional): 需要更新的流体的ID，默认为None，
                表示更新所有流体
            kernel (Interp2, optional): 插值函数，默认为None
            relax_factor (float, optional): 松弛因子，
                限定密度的最大变化幅度，默认为1.0
            fa_t (int): 温度属性的ID
            min (float, optional): 密度的最小值，默认为-1
            max (float, optional): 密度的最大值，默认为-1
            pool: 线程池. 如果给定，则此函数会立即退出。请在后续同步线程池内的任务

        Returns:
            None
        """
        if relax_factor <= 0:
            return
        assert isinstance(fa_t, int)
        core.seepage_update_den(
            self.handle, *parse_fid3(fluid_id),
            kernel.handle if isinstance(kernel, Interp2) else 0,
            fa_t, relax_factor, min, max,
            pool.handle if isinstance(pool, ThreadPool) else 0
        )

    core.use(None, 'seepage_update_vis',
             c_void_p, c_size_t, c_size_t, c_size_t,
             c_void_p, c_size_t, c_size_t, c_double,
             c_double, c_double, c_void_p)

    def update_vis(self, fluid_id=None, kernel=None, ca_p=None, fa_t=None,
                   relax_factor=0.3, min=1.0e-7, max=1.0, pool=None):
        """
        更新流体的粘性系数。
        Note:
            当不给定fluid_id的时候，则尝试更新所有流体的粘性
            （利用model内置的流体定义）；

        Note:
            当kernel为None的时候，使用模型内置的流体定义；

        注意:
            当 relax_factor <= 0的时候，内核不会执行任何更新
            (since 2023-9-27)

        Args:
            fluid_id (int, optional): 需要更新的流体的ID，
                默认为None，表示更新所有流体
            kernel (Interp2, optional): 插值函数，默认为None
            ca_p (int, optional): 压力属性的ID，默认为None
            fa_t (int): 温度属性的ID
            relax_factor (float, optional): 松弛因子，
                限定粘性系数的最大变化幅度，默认为0.3
            min (float, optional): 粘性系数的最小值，默认为1.0e-7
            max (float, optional): 粘性系数的最大值，默认为1.0
            pool: 线程池. 如果给定，则此函数会立即退出。请在后续同步线程池内的任务

        Returns:
            None
        """
        if relax_factor <= 0:
            return
        if ca_p is None:
            # 此时，利用流体的体积来计算压力 (不可以指定流体ID：此时更新所有的流体)
            ca_p = IDX_INF
            assert fluid_id is None
        else:
            assert isinstance(ca_p, int)
        assert isinstance(fa_t, int)
        if kernel is None:
            kernel_handle = 0
        else:
            assert isinstance(kernel, Interp2)
            kernel_handle = kernel.handle
        core.seepage_update_vis(
            self.handle, *parse_fid3(fluid_id),
            kernel_handle, ca_p, fa_t,
            relax_factor, min, max,
            pool.handle if isinstance(pool, ThreadPool) else 0
        )

    core.use(None, 'seepage_update_pore', c_void_p, c_size_t, c_size_t, c_double)

    def update_pore(self, ca_v0, ca_k, relax_factor=0.01) -> 'Seepage':
        """
        更新pore的属性，使得当前压力下，孔隙空间的体积可以逐渐逼近真实值
        (真实值由ca_v0和ca_k定义的属性给定).
        注意：这个函数仅更新那些定义了ca_v0和ca_k属性的Cell.

        Args:
            ca_v0 (int): 孔隙初始体积属性的ID
            ca_k (int): 孔隙压缩系数属性的ID
            relax_factor (float, optional): 松弛因子，默认为0.01

        Returns:
            self: 返回当前对象
        """
        core.seepage_update_pore(self.handle, ca_v0, ca_k, relax_factor)
        return self

    core.use(None, 'seepage_thermal_exchange',
             c_void_p, c_size_t, c_void_p,
             c_double,
             c_size_t, c_size_t, c_size_t)

    core.use(None, 'seepage_exchange_heat',
             c_void_p, c_double,
             c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t, c_void_p)

    def exchange_heat(self, fid=None, thermal_model=None,
                      dt=None, ca_g=None,
                      ca_t=None, ca_mc=None,
                      fa_t=None, fa_c=None, pool=None
                      ):
        """
        流体和固体交换热量。
        注意：
            1. 当thermal_model为None的时候，则在Seepage内部交换热量，
                此时，必须定义ca_t, ca_mc两个属性
            2. 当fid为None的时候，将所有的流体视为整体，与固体交换。
                此时，会计算各个流体的平均温度，并且，此函数运行之后
                各个流体的温度将相等

        Args:
            fid (int, optional): 流体的ID，默认为None
            thermal_model (Thermal, optional): 热模型，默认为None
            dt (float, optional): 时间步长，默认为None
            ca_g (int, optional): 重力属性的ID，默认为None
            ca_t (int, optional): 温度属性的ID，默认为None
            ca_mc (int, optional): 热容属性的ID，默认为None
            fa_t (int, optional): 面温度属性的ID，默认为None
            fa_c (int, optional): 面热容属性的ID，默认为None
            pool: 线程池

        Returns:
            None
        """
        if dt is None:
            return
        if dt <= 1.0e-20:
            return
        if thermal_model is None:  # 在模型的内部交换热量（流体和固体交换）
            assert fid is None
            all_right = True
            if ca_g is None:
                warnings.warn('ca_g is None in Seepage.exchange_heat')
                all_right = False
            if ca_t is None:
                warnings.warn('ca_t is None in Seepage.exchange_heat')
                all_right = False
            if ca_mc is None:
                warnings.warn('ca_mc is None in Seepage.exchange_heat')
                all_right = False
            if fa_t is None:
                warnings.warn('fa_t is None in Seepage.exchange_heat')
                all_right = False
            if fa_c is None:
                warnings.warn('fa_c is None in Seepage.exchange_heat')
                all_right = False
            if all_right:
                core.seepage_exchange_heat(
                    self.handle, dt, ca_g, ca_t, ca_mc, fa_t, fa_c,
                    pool.handle if isinstance(pool, ThreadPool) else 0
                )
            return
        else:
            assert isinstance(thermal_model, Thermal)
            if fid is None:
                fid = 100000000  # exchange with all fluid when fid not exists
            core.seepage_thermal_exchange(
                self.handle, fid,
                thermal_model.handle, dt, ca_g, fa_t, fa_c)
            return

    core.use(None, 'seepage_update_cond',
             c_void_p, c_size_t, c_size_t, c_size_t, c_double, c_void_p)

    def update_cond(self, ca_v0, fa_g0, fa_igr, relax_factor=1.0, pool=None) -> 'Seepage':
        """
        给定初始时刻各Cell流体体积v0，各Face的导流g0，v/v0到g/g0的映射gr，
        来更新此刻Face的g.
        ca_v0是cell的属性id，fa_g0是face初始导流能力的的属性id，
        fa_igr是face选用的gr的序号的属性id
            (用以表示此face选用的gr的序号。注意此时必须提前将gr存储到model中).

        Args:
            ca_v0 (int): 初始时刻各Cell流体体积属性的ID
            fa_g0 (int): 各Face的初始导流的属性ID
            fa_igr (int): 各Face选用的gr的序号属性的ID
            relax_factor (float, optional): 松弛因子，默认为1.0
            pool: 线程池

        Returns:
            self: 返回当前对象
        """
        core.seepage_update_cond(
            self.handle, ca_v0, fa_g0, fa_igr, relax_factor,
            pool.handle if isinstance(pool, ThreadPool) else 0
        )
        return self

    core.use(None, 'seepage_update_g0',
             c_void_p, c_size_t, c_size_t, c_size_t, c_size_t)

    def update_g0(self, fa_g0, fa_k, fa_s, fa_l) -> 'Seepage':
        """
        对于所有的face，根据它的渗透率，面积和长度来计算cond (流体饱和的时候的cond).
            ---
            此函数非必须，可以基于numpy在Python层面实现同样的功能，后续可能会移除.

        Args:
            fa_g0 (int): 各Face的导流属性的ID
            fa_k (int): 各Face的渗透率属性的ID
            fa_s (int): 各Face的面积属性的ID
            fa_l (int): 各Face的长度属性的ID

        Returns:
            self: 返回当前对象
        """
        core.seepage_update_g0(self.handle, fa_g0, fa_k, fa_s, fa_l)
        return self

    core.use(None, 'seepage_diffusion',
             c_void_p, c_double,
             c_size_t, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t,
             c_void_p, c_size_t, c_void_p, c_size_t, c_void_p, c_size_t,
             c_void_p, c_size_t,
             c_double, c_void_p)

    def diffusion(self, dt, fid0, fid1, *,
                  ps0=None, ls0=None, vs0=None,
                  pk=None, lk=None, vk=None,
                  pg=None, lg=None, vg=None,
                  ppg=None, lpg=None, vpg=None,
                  ds_max=0.05, face_groups=None):
        """
        扩散.
        其中fid0和fid1定义两种流体。在扩散的时候，相邻Cell的这两种流体会进行交换，
            但会保证每个Cell的流体体积不变；
            其中vs0定义两种流体压力相等的时候fid0的饱和度；
            vk当饱和度变化1的时候，压力的变化幅度；
            vg定义face的导流能力(针对fid0和fid1作为一个整体);
            vpg定义流体fid0受到的重力减去fid1的重力在face上的投影;
            ds_max为允许的饱和度最大的改变量

        Args:
            dt (float): 时间步长
            fid0 (int): 第一种流体的ID
            fid1 (int): 第二种流体的ID
            ps0 (ctypes.c_void_p, optional): 饱和度指针，默认为None
            ls0 (int, optional): 饱和度指针的长度，默认为None
            vs0 (Vector, optional): 饱和度向量，默认为None
            pk (ctypes.c_void_p, optional): 压力变化幅度指针，默认为None
            lk (int, optional): 压力变化幅度指针的长度，默认为None
            vk (Vector, optional): 压力变化幅度向量，默认为None
            pg (ctypes.c_void_p, optional): 导流能力指针，默认为None
            lg (int, optional): 导流能力指针的长度，默认为None
            vg (Vector, optional): 导流能力向量，默认为None
            ppg (ctypes.c_void_p, optional): 重力投影指针，默认为None
            lpg (int, optional): 重力投影指针的长度，默认为None
            vpg (Vector, optional): 重力投影向量，默认为None
            ds_max (float, optional): 允许的饱和度最大的改变量，默认为0.05
            face_groups (Groups, optional): 面分组，默认为None

        Returns:
            None
        """
        if ps0 is None:
            if isinstance(vs0, Vector):
                warnings.warn(
                    'parameter <vs0> of Seepage.diffusion '
                    'will be removed after 2025-4-6',
                    DeprecationWarning, stacklevel=2)
                if vs0.size > 0:
                    ps0 = vs0.pointer
                    ls0 = vs0.size

        if pk is None:
            if isinstance(vk, Vector):
                warnings.warn(
                    'parameter <vk> of Seepage.diffusion '
                    'will be removed after 2025-4-6',
                    DeprecationWarning, stacklevel=2)
                if vk.size > 0:
                    pk = vk.pointer
                    lk = vk.size

        if pg is None:
            if isinstance(vg, Vector):
                warnings.warn(
                    'parameter <vg> of Seepage.diffusion '
                    'will be removed after 2025-4-6',
                    DeprecationWarning, stacklevel=2)
                if vg.size > 0:
                    pg = vg.pointer
                    lg = vg.size

        if ppg is None:
            if isinstance(vpg, Vector):
                warnings.warn(
                    'parameter <vpg> of Seepage.diffusion '
                    'will be removed after 2025-4-6',
                    DeprecationWarning, stacklevel=2)
                if vpg.size > 0:
                    ppg = vpg.pointer
                    lpg = vpg.size

        if pg is None:
            return  # 没有g，则无法交换

        if pk is None and ppg is None:
            return  # 既没有定义毛管力，也没有定义重力，没有执行的必要了

        # 下面，解析指针和长度
        if ps0 is None:
            ps0 = 0
            ls0 = 0
        else:
            ps0 = ctypes.cast(ps0, c_void_p)
            if ls0 is None:
                ls0 = self.cell_number

        if pk is None:
            pk = 0
            lk = 0
        else:
            pk = ctypes.cast(pk, c_void_p)
            if lk is None:
                lk = self.cell_number

        if pg is None:
            pg = 0
            lg = 0
        else:
            pg = ctypes.cast(pg, c_void_p)
            if lg is None:
                lg = self.face_number

        if ppg is None:
            ppg = 0
            lpg = 0
        else:
            ppg = ctypes.cast(ppg, c_void_p)
            if lpg is None:
                lpg = self.face_number

        if face_groups is not None:
            assert isinstance(face_groups, Groups)  # 分组

        # 执行扩散操作.
        core.seepage_diffusion(
            self.handle, dt, *parse_fid3(fid0),
            *parse_fid3(fid1),
            ps0, ls0,
            pk, lk,
            pg, lg,
            ppg, lpg,
            ds_max,
            0 if face_groups is None else face_groups.handle)

    core.use(None, 'seepage_heating', c_void_p, c_size_t, c_size_t, c_size_t, c_double)

    def heating(self, ca_mc, ca_t, ca_p, dt) -> 'Seepage':
        """
        按照各个Cell给定的功率来对各个Cell进行加热 (此功能非必须，可以借助numpy实现).
        其中：
            ca_p：定义Cell加热的功率.

        Args:
            ca_mc (int): 热容属性的ID
            ca_t (int): 温度属性的ID
            ca_p (int): 加热功率属性的ID
            dt (float): 时间步长

        Returns:
            None
        """
        core.seepage_heating(self.handle, ca_mc, ca_t, ca_p, dt)
        return self

    core.use(None, 'seepage_update_sand', c_void_p, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t, c_void_p, c_void_p)

    def update_sand(self, *, sol_sand, flu_sand, ca_i0, ca_i1,
                    force, ratio=None):
        """
        更新流动的砂和沉降的砂之间的体积. 其中:
            sol_sand, flu_sand: 表示流动的砂和沉降的砂的Index.
            force: 一个指针，给定各个cell位置的单位面积孔隙表面的剪切力;
            ratio: 一个指针，定义各个Cell位置砂子趋向于目标浓度的达成比率(默认为1).
            ca_i0, ca_i1: Cell的属性ID，定义的是存储的曲线的ID。
                曲线的横坐标是剪切力，纵轴为流动砂的浓度.

        Args:
            sol_sand (list or str): 沉降的砂的Index或名称
            flu_sand (list or str): 流动的砂的Index或名称
            ca_i0 (int or str): Cell的属性ID或名称
            ca_i1 (int or str): Cell的属性ID或名称
            force (ctypes.c_void_p): 各个cell位置的单位面积孔隙表面的剪切力指针
            ratio (ctypes.c_void_p, optional): 各个Cell位置砂子趋向于目标浓度的
                达成比率指针，默认为None

        Returns:
            None
        """
        if isinstance(sol_sand, str):
            sol_sand = self.find_fludef(name=sol_sand)
            assert sol_sand is not None

        if isinstance(flu_sand, str):
            flu_sand = self.find_fludef(name=flu_sand)
            assert flu_sand is not None

        if isinstance(ca_i0, str):
            ca_i0 = self.get_cell_key(ca_i0)
            assert ca_i0 is not None

        if isinstance(ca_i1, str):
            ca_i1 = self.get_cell_key(ca_i1)
            assert ca_i1 is not None

        core.seepage_update_sand(
            self.handle, ca_i0, ca_i1,
            *parse_fid3(sol_sand),
            *parse_fid3(flu_sand),
            ctypes.cast(force, c_void_p),
            ctypes.cast(ratio, c_void_p))

    core.use(None, 'seepage_pop_fluids', c_void_p, c_void_p, c_void_p)
    core.use(None, 'seepage_push_fluids', c_void_p, c_void_p, c_void_p)

    def pop_fluids(self, buffer, *, pool=None):
        """
        将各个Cell中的最后一个流体暂存到buffer中。一般情况下，将固体作为最后一种流体。
        在计算流动的时候，如果这些固体存在，则会影响到相对渗透率。
        因此，当模型中存在固体的时候，需要先将固体组分
        弹出，然后再计算流动。计算流动之后，再将备份的固体组分压入，
        使得模型恢复到最初的状态。
        注意：在弹出最后一种流体的时候，会同步修改Cell中的pore的大小，并保证压力不变;
            since: 2023-04

        Args:
            buffer (CellData): 用于暂存流体的缓冲区
            pool: 线程池

        Returns:
            None
        """
        assert isinstance(buffer, CellData)
        core.seepage_pop_fluids(
            self.handle, buffer.handle,
            pool.handle if isinstance(pool, ThreadPool) else 0
        )

    def push_fluids(self, buffer, *, pool=None):
        """
        将buffer中暂存的流体追加到各个Cell中。和pop_fluids函数搭配使用。

        Args:
            buffer (CellData): 暂存流体的缓冲区
            pool: 线程池

        Returns:
            None
        """
        assert isinstance(buffer, CellData)
        core.seepage_push_fluids(
            self.handle, buffer.handle,
            pool.handle if isinstance(pool, ThreadPool) else 0
        )

    def get_temporary(self, key, the_type):
        """
        返回一个临时变量(这个临时变量在save和load的时候会丢失)。确保返回的类型为the_type
        Args:
            key: 临时变量的名称
            the_type: 临时变量的类型
        Returns:
            临时变量的实例
        """
        res = self.temps.get(key)
        if not isinstance(res, the_type):
            res = the_type()
            self.temps[key] = res
            return res
        else:
            return res

    def get_flow_sol(self) -> 'FlowSol':
        """
        返回模型内部的一个临时变量（用于流体求解）
        """
        res = self.get_temporary('flow_sol', FlowSol)
        assert isinstance(res, FlowSol)
        return res

    def iterate(self, dt, *,
                fa_s: Optional[int] = None, fa_q: Optional[int] = None,
                fa_k: Optional[int] = None, ca_p: Optional[int] = None,
                cfl: Optional[float] = None,
                pool: Optional[ThreadPool] = None,
                report: Optional[Map] = None,
                solver: Optional['ConjugateGradientSolver'] = None, **kwargs
                ):
        """
        迭代模型内的流动过程。
        """
        return self.get_flow_sol().iterate(
            model=self, dt=dt, fa_s=fa_s, fa_q=fa_q, fa_k=fa_k, ca_p=ca_p, cfl=cfl,
            solver=solver, pool=pool, report=report, **kwargs
        )

    def get_thermal_sol(self) -> 'ThermalSol':
        """
        返回模型内部的一个临时变量（用于温度场求解）
        """
        res = self.get_temporary('thermal_sol', ThermalSol)
        assert isinstance(res, ThermalSol)
        return res

    def iterate_thermal(self, dt, **opts):
        """
        迭代更新模型的热状态

        Args:
            dt (float): 时间步长。

        Returns:
            热状态迭代结果
        """
        return self.get_thermal_sol().iterate(self, dt=dt, **opts)

    def get_recommended_dt(self, *args, ca_t=None, ca_mc=None, **kwargs):
        """
        获取推荐的时间步长

        Args:
            ca_mc: Cell范围内质量和比热的乘积。
            ca_t: Cell的温度属性的ID。
            *args: 可变参数
            **kwargs: 关键字参数

        Returns:
            float: 推荐的时间步长
        """
        warnings.warn("Seepage.get_recommended_dt is deprecated (will be removed after 2027-6-8).", DeprecationWarning,
                      stacklevel=2)
        if ca_t is not None and ca_mc is not None:
            thermal_sol = self.get_thermal_sol()
            return thermal_sol.get_recommended_dt(self, *args, ca_t=ca_t, ca_mc=ca_mc, **kwargs)
        else:
            flow_sol = self.get_flow_sol()
            return flow_sol.get_recommended_dt(*args, **kwargs)

    core.use(c_double, 'seepage_get_fluid_mass', c_void_p, c_size_t, c_size_t, c_size_t)

    def get_fluid_mass(self, fluid_id=None):
        """
        返回模型中所有Cell内的流体mass的和。
            当fluid_id指定的时候，则仅仅对给定的流体进行加和，否则，将加和所有的流体

        Args:
            fluid_id (int, optional): 流体的ID，默认为None

        Returns:
            float: 流体的总质量
        """
        return core.seepage_get_fluid_mass(self.handle, *parse_fid3(fluid_id))

    @property
    def fluid_mass(self):
        """
        返回模型中所有Cell内的流体mass的和

        Returns:
            float: 流体的总质量
        """
        return self.get_fluid_mass()

    core.use(c_double, 'seepage_get_fluid_vol', c_void_p, c_size_t, c_size_t, c_size_t)

    def get_fluid_vol(self, fluid_id=None) -> float:
        """
        返回模型中所有Cell内的流体vol的和
            当fluid_id指定的时候，则仅仅对给定的流体进行加和，否则，将加和所有的流体

        Args:
            fluid_id (int, optional): 流体的ID，默认为None

        Returns:
            float: 流体的总体积
        """
        return core.seepage_get_fluid_vol(self.handle, *parse_fid3(fluid_id))

    @property
    def fluid_vol(self) -> float:
        """
        返回模型中所有Cell内的流体vol的和

        Returns:
            float: 流体的总体积
        """
        return self.get_fluid_vol()

    core.use(None, 'seepage_find_inner_face_ids', c_void_p, c_void_p, c_void_p)

    def find_inner_face_ids(self, cell_ids, buffer=None):
        """
        给定多个Cell，返回这些Cell内部相互连接的Face的序号

        Args:
            cell_ids (UintVector): 包含多个Cell的UintVector对象
            buffer (UintVector, optional): 用于存储结果的UintVector对象，默认为None

        Returns:
            UintVector: 包含内部相互连接的Face序号的UintVector对象
        """
        assert isinstance(cell_ids, UintVector)
        if not isinstance(buffer, UintVector):
            buffer = UintVector()
        core.seepage_find_inner_face_ids(self.handle, buffer.handle, cell_ids.handle)
        return buffer

    core.use(None, 'seepage_get_cond_for_exchange',
             c_void_p, c_void_p,
             c_size_t, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t)

    def get_cond_for_exchange(self, fid0, fid1, buffer=None):
        """
        根据相对渗透率曲线、粘性系数，计算相邻两个Cell交换流体的时候的导流系数

        Args:
            fid0: 第一个Cell的相关标识
            fid1: 第二个Cell的相关标识
            buffer (Vector, optional): 用于存储结果的Vector对象，默认为None

        Returns:
            Vector: 包含导流系数的Vector对象
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.seepage_get_cond_for_exchange(self.handle, buffer.handle, *parse_fid3(fid0), *parse_fid3(fid1))
        return buffer

    core.use(None, 'seepage_get_linear_dpre',
             c_void_p, c_void_p, c_void_p,
             c_size_t, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t,
             c_void_p, c_size_t, c_double, c_void_p)

    def get_linear_dpre(self, fid0, fid1, s2p=None, ca_ipc=IDX_INF, vs0=None,
                        vk=None, ds=0.05, cell_ids=None):
        """
        更新两种流体之间压力差和饱和度之间的线性关系

        Args:
            fid0: 第一个Cell的相关标识
            fid1: 第二个Cell的相关标识
            s2p (Interp1, optional): 插值对象，默认为None
            ca_ipc (int, optional): 一个整数参数，默认为INT_INF
            vs0 (Vector, optional): 用于存储结果的Vector对象，默认为None
            vk (Vector, optional): 用于存储结果的Vector对象，默认为None
            ds (float, optional): 一个浮点数参数，默认为0.05
            cell_ids (UintVector, optional): 包含Cell序号的UintVector对象，
                默认为None

        Returns:
            Tuple[Vector, Vector]: 包含更新后结果的两个Vector对象
        """
        if not isinstance(vs0, Vector):
            vs0 = Vector()
        if not isinstance(vk, Vector):
            vk = Vector()
        if cell_ids is not None:
            if not isinstance(cell_ids, UintVector):
                cell_ids = UintVector(cell_ids)
        core.seepage_get_linear_dpre(
            self.handle, vs0.handle, vk.handle,
            *parse_fid3(fid0),
            *parse_fid3(fid1),
            s2p.handle if isinstance(s2p, Interp1) else 0,
            ca_ipc, ds,
            0 if cell_ids is None else cell_ids.handle)
        return vs0, vk

    core.use(None, 'seepage_get_vol_fraction',
             c_void_p, c_void_p, c_size_t, c_size_t, c_size_t)

    def get_vol_fraction(self, fid, buffer=None):
        """
        返回给定序号的流体的体积饱和度，并且作为一个Vector返回

        Args:
            fid: 流体的序号
            buffer (Vector, optional): 用于存储结果的Vector对象，默认为None

        Returns:
            Vector: 包含体积饱和度的Vector对象
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.seepage_get_vol_fraction(self.handle, buffer.handle,
                                      *parse_fid3(fid))
        return buffer

    core.use(None, 'seepage_cells_write', c_void_p, c_void_p, c_int64)

    def cells_write(self, *, index, pointer):
        """
        导出属性(所有的Cell): 当 index >= 0 的时候，为属性ID; 如果index < 0，则：
            index=-1, x坐标
            index=-2, y坐标
            index=-3, z坐标
            index=-4, v0 of pore
            index=-5, k  of pore
            index=-6, inner_prod(pos, gravity)
        --- (以下为只读属性):
            index=-10, 所有流体的总的质量 (只读)
            index=-11, 所有流体的总的体积 (只读)
            index=-12, 根据流体的体积和pore，来计算的Cell的压力 (只读)

        Args:
            index (int or str): 属性的索引或名称
            pointer: 指向存储数据的指针
        """
        if isinstance(index, str):
            index = self.get_cell_key(key=index)
            assert index is not None
        core.seepage_cells_write(self.handle, f64_ptr(pointer), index)

    core.use(None, 'seepage_cells_read', c_void_p, c_void_p, c_double, c_int64)

    def cells_read(self, *, index, pointer=None, value=None):
        """
        导入属性: 当 index >= 0 的时候，为属性ID；如果index < 0，则：
            index=-1, x坐标
            index=-2, y坐标
            index=-3, z坐标
            index=-4, v0 of pore
            index=-5, k  of pore

        Args:
            index (int or str): 属性的索引或名称
            pointer: 指向存储数据的指针，默认为None
            value: 要导入的值，默认为None
        """
        if isinstance(index, str):
            index = self.reg_cell_key(key=index)
        if pointer is not None:
            core.seepage_cells_read(self.handle, const_f64_ptr(pointer), 0, index)
        else:
            assert value is not None
            core.seepage_cells_read(self.handle, 0, value, index)

    core.use(None, 'seepage_faces_write', c_void_p, c_void_p, c_int64)

    def faces_write(self, *, index, pointer):
        """
        导出属性:
            index >= 0 的时候，为属性ID；
        如果index < 0，则：
            index=-1, cond
            index=-2, dr
            index=-3, face两侧的cell的距离
            index=-4, 重力的分量与face两侧Cell距离的乘积.
                inner_prod(gravity, cell1.pos - cell0.pos)
            ...
            index=-10, dv of fluid 0
            index=-11, dv of fluid 1
            index=-12, dv of fluid 2
            ...
            index=-19, dv of fluid ALL

        Args:
            index (int or str): 属性的索引或名称
            pointer: 指向存储数据的指针
        """
        if isinstance(index, str):
            index = self.get_face_key(key=index)
            assert index is not None
        core.seepage_faces_write(self.handle, f64_ptr(pointer), index)

    core.use(None, 'seepage_faces_read', c_void_p, c_void_p, c_double, c_int64)

    def faces_read(self, *, index, pointer=None, value=None):
        """
        导入属性: 当 index >= 0 的时候，为属性ID；如果index < 0，则：
            index=-1, cond
            index=-2, dr

        Args:
            index (int or str): 属性的索引或名称
            pointer: 指向存储数据的指针，默认为None
            value: 要导入的值，默认为None
        """
        if isinstance(index, str):
            index = self.reg_face_key(key=index)
        if pointer is not None:
            core.seepage_faces_read(self.handle, const_f64_ptr(pointer), 0, index)
        else:
            assert value is not None
            core.seepage_faces_read(self.handle, 0, value, index)

    core.use(None, 'seepage_fluids_write',
             c_void_p, c_void_p, c_int64,
             c_size_t, c_size_t, c_size_t)

    def fluids_write(self, *, fluid_id, index, pointer):
        """
        导出属性: 当 index >= 0 的时候，为属性ID；如果index < 0，则：
            index=-1, 质量
            index=-2, 密度
            index=-3, 体积
            index=-4, 粘性

        Args:
            fluid_id: 流体的ID
            index (int or str): 属性的索引或名称
            pointer: 指向存储数据的指针
        """
        if isinstance(index, str):
            index = self.get_flu_key(key=index)
            assert index is not None
        core.seepage_fluids_write(self.handle, f64_ptr(pointer), index, *parse_fid3(fluid_id))

    core.use(None, 'seepage_fluids_read',
             c_void_p, c_void_p, c_double, c_int64,
             c_size_t, c_size_t, c_size_t)

    def fluids_read(self, *, fluid_id, index, pointer=None, value=None):
        """
        导入属性

        Args:
            fluid_id: 流体的ID
            index (int or str): 属性的索引或名称
            pointer: 指向存储数据的指针，默认为None
            value: 要导入的值，默认为None
        """
        if isinstance(index, str):
            index = self.reg_flu_key(key=index)
        if pointer is not None:
            core.seepage_fluids_read(self.handle, const_f64_ptr(pointer), 0, index, *parse_fid3(fluid_id))
        else:
            assert value is not None
            core.seepage_fluids_read(self.handle, 0, value, index, *parse_fid3(fluid_id))

    @property
    def numpy(self):
        """
        用以和numpy交互数据

        警告: Seepage.numpy将在2025-1-21之后移除。
            请使用zmlx.as_numpy。

        Returns:
            SeepageNumpy: 用于和numpy交互数据的SeepageNumpy对象
        """
        warnings.warn(
            'Seepage.numpy will be removed after 2025-1-21. '
            'Use zmlx.as_numpy Instead.'
            , DeprecationWarning, stacklevel=2)
        from zmlx.tfc._base import SeepageNumpy
        return SeepageNumpy(model=self)

    core.use(None, 'seepage_get_cells_v0',
             c_void_p, c_void_p)
    core.use(None, 'seepage_get_cells_k',
             c_void_p, c_void_p)
    core.use(None, 'seepage_get_cells_fv',
             c_void_p, c_void_p)
    core.use(None, 'seepage_get_cells_attr',
             c_void_p, c_size_t, c_void_p)
    core.use(None, 'seepage_get_faces_attr',
             c_void_p, c_size_t, c_void_p)
    core.use(None, 'seepage_set_cells_attr',
             c_void_p, c_size_t, c_void_p)
    core.use(None, 'seepage_set_faces_attr',
             c_void_p, c_size_t, c_void_p)

    def get_attrs(self, key, index=None, buffer=None):
        """
        返回所有指定元素的属性 <作为Vector返回>.

        警告: 请使用 <Seepage.cells_write> 和 <Seepage.faces_write> 函数代替。
        此函数将在2024-6-14之后移除。

        Args:
            key (str): 指定元素的键
            index (int, optional): 属性的索引，默认为None
            buffer (Vector, optional): 用于存储结果的Vector对象，默认为None

        Returns:
            Vector: 包含指定元素属性的Vector对象
        """
        warnings.warn(
            'please use function <Seepage.cells_write> '
            'and <Seepage.faces_write> instead. '
            'Will remove after 2024-6-14', DeprecationWarning, stacklevel=2)
        if not isinstance(buffer, Vector):
            buffer = Vector()
        if key == 'cells_v0':
            core.seepage_get_cells_v0(self.handle, buffer.handle)
            return buffer
        if key == 'cells_k':
            core.seepage_get_cells_k(self.handle, buffer.handle)
            return buffer
        if key == 'cells_fv':
            core.seepage_get_cells_fv(self.handle, buffer.handle)
            return buffer
        if key == 'cells':
            core.seepage_get_cells_attr(self.handle, index, buffer.handle)
            return buffer
        if key == 'faces':
            core.seepage_get_faces_attr(self.handle, index, buffer.handle)
            return buffer
        else:
            return None

    def set_attrs(self, key, value=None, index=None):
        """
        设置所有指定元素的属性

        警告: 请使用 <Seepage.cells_read> 和 <Seepage.faces_read> 函数代替。
        此函数将在2024-6-14之后移除。

        Args:
            key (str): 指定元素的键
            value (Vector): 要设置的属性值
            index (int, optional): 属性的索引，默认为None
        """
        warnings.warn(
            'please use function <Seepage.cells_read> '
            'and <Seepage.faces_read> instead. '
            'will be removed after 2024-6-14', DeprecationWarning, stacklevel=2)
        assert isinstance(value, Vector)
        if key == 'cells':
            core.seepage_set_cells_attr(self.handle, index, value.handle)
        if key == 'faces':
            core.seepage_set_faces_attr(self.handle, index, value.handle)

    def print_cells(self, path, get=None, properties=None):
        """
        输出cell的属性（前三列固定为x y z坐标）. 默认第4列为pre，第5列为体积，
            后面依次为各流体组分的体积饱和度.

        Args:
            path (str): 输出文件的路径
            get (Callable, optional): 用于获取cell属性字符串的函数，
                默认为None
            properties (List[Callable], optional): 额外的属性获取函数列表，
                默认为None
        """
        if path is None:
            return

        def get_vols(flu):
            if flu.component_number == 0:
                return [flu.vol]
            else:
                vols = []
                for i in range(flu.component_number):
                    vols.extend(get_vols(flu.get_component(i)))
                return vols

        def to_str(c):
            vols = []
            for i in range(c.fluid_number):
                vols.extend(get_vols(c.get_fluid(i)))
            vol = sum(vols)
            s = f'{c.pre}\t{vol}'
            for v in vols:
                s = f'{s}\t{v / vol}'
            return s

        if get is None:
            get = to_str
        with open(path, 'w') as file:
            for cell in self.cells:
                x, y, z = cell.pos
                file.write(f'{x}\t{y}\t{z}\t{get(cell)}')
                if properties is not None:
                    for prop in properties:
                        file.write(f'\t{prop(cell)}')
                file.write('\n')

    core.use(None, 'seepage_group_cells', c_void_p, c_void_p)

    def get_cell_groups(self):
        """
        对所有的cell进行分区，使得对于任意一个cell，都不会和与它相关的cell分在一组
        (用于并行)

        Returns:
            Groups: 包含分区结果的Groups对象
        """
        g = Groups()
        core.seepage_group_cells(self.handle, g.handle)
        return g

    core.use(None, 'seepage_group_faces', c_void_p, c_void_p)

    def get_face_groups(self):
        """
        对所有的face进行分区，使得对于任意一个face，都不会和与它相关的face分在一组
         (用于并行)

        Returns:
            Groups: 包含分区结果的Groups对象
        """
        g = Groups()
        core.seepage_group_faces(self.handle, g.handle)
        return g

    core.use(None, 'seepage_get_cell_flu_vel',
             c_void_p, c_void_p, c_size_t, c_double)

    def get_cell_flu_vel(self, fid, last_dt, buf=None):
        """
        根据上一个时间步各个face内流过的流体的体积，来计算各个cell位置流体流动的速度.

        Args:
            fid: 流体的ID
            last_dt: 上一个时间步的时间间隔
            buf (Vector, optional): 用于存储结果的Vector对象，默认为None

        Returns:
            Vector: 包含流体流动速度的Vector对象
        """
        if isinstance(fid, str):
            fid = self.find_fludef(name=fid)
        if is_array(fid):
            assert len(fid) == 1
            fid = fid[0]
        assert 0 <= fid < self.fludef_number
        if buf is None:
            buf = Vector(size=self.cell_number)
            core.seepage_get_cell_flu_vel(self.handle, buf.pointer, fid,
                                          last_dt)
            return buf
        elif isinstance(buf, Vector):
            buf.size = self.cell_number
            core.seepage_get_cell_flu_vel(self.handle, buf.pointer, fid,
                                          last_dt)
            return buf
        else:  # 此时，buf应该为一个长度为cell_number的指针类型
            core.seepage_get_cell_flu_vel(self.handle, buf, fid, last_dt)
            return None

    core.use(None, 'seepage_get_cell_gradient', c_void_p, c_void_p, c_void_p)

    def get_cell_gradient(self, data, buf=None):
        """
        计算cell位置各个物理量的梯度. 这里，给定的data和buf都应该为长度等于
        cell_number的double指针

        Args:
            data: 包含物理量数据的指针
            buf (Vector, optional): 用于存储结果的Vector对象，默认为None

        Returns:
            Vector: 包含梯度数据的Vector对象
        """
        if isinstance(data, Vector):
            data = data.pointer
        if buf is None:
            buf = Vector(size=self.cell_number)
            core.seepage_get_cell_gradient(self.handle, buf.pointer, data)
            return buf
        elif isinstance(buf, Vector):
            buf.size = self.cell_number
            core.seepage_get_cell_gradient(self.handle, buf.pointer, data)
            return buf
        else:  # 此时，buf应该为一个长度为cell_number的指针类型
            core.seepage_get_cell_gradient(self.handle, buf, data)
            return None

    core.use(None, 'seepage_get_cell_average', c_void_p, c_void_p, c_void_p)

    def get_cell_average(self, fa, *, buf=None):
        """
        计算cell周围face的平均值

        其中:
            fa为face的属性(指针，用于输入)
            buf为各个cell的属性(指针，用于输出)

        Args:
            fa: 包含face属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含平均值数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.cell_number)
            buf = f64_ptr(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_cell_average(self.handle, ctypes.cast(buf, c_void_p), ctypes.cast(fa, c_void_p))
        return data

    core.use(None, 'seepage_get_cell_max', c_void_p, c_void_p, c_void_p)

    def get_cell_max(self, fa, *, buf=None):
        """
        计算cell周围face的属性的最大值

        其中:
            fa为face的属性(指针，用于输入)
            buf为各个cell的属性(指针，用于输出)

        Args:
            fa: 包含face属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含最大值数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.cell_number)
            buf = f64_ptr(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_cell_max(self.handle, ctypes.cast(buf, c_void_p), ctypes.cast(fa, c_void_p))
        return data

    core.use(None, 'seepage_get_face_gradient', c_void_p, c_void_p, c_void_p)

    def get_face_gradient(self, ca, *, buf=None):
        """
        根据cell中心位置的属性的值来计算各个face位置的梯度.
            (c1 - c0) / dist
        其中:
            c1和c0分别位face右侧和左侧的cell的属性.
            buf为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)
        注意：
            这里计算梯度的时候，并未计算绝对值，即返回的gradient可能是负值.

        Args:
            ca: 包含cell属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含梯度数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.face_number)
            buf = f64_ptr(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_face_gradient(self.handle, ctypes.cast(buf, c_void_p), ctypes.cast(ca, c_void_p))
        return data

    core.use(None, 'seepage_get_face_diff', c_void_p, c_void_p, c_void_p)

    def get_face_diff(self, ca, *, buf=None):
        """
        计算face两侧的cell的属性的值的差异。
            c1 - c0
        其中:
            c1和c0分别位face右侧和左侧的cell的属性.
            buf为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)
        注意：
            并未计算绝对值，及返回的数值可能是负值.

        Args:
            ca: 包含cell属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含差异数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.face_number)
            buf = f64_ptr(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_face_diff(self.handle, ctypes.cast(buf, c_void_p), ctypes.cast(ca, c_void_p))
        return data

    core.use(None, 'seepage_get_face_sum', c_void_p, c_void_p, c_void_p)

    def get_face_sum(self, ca, *, buf=None):
        """
        计算face两侧的cell的属性的值的和。
            c1 + c0
        其中:
            buf为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)

        Args:
            ca: 包含cell属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含和数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.face_number)
            buf = f64_ptr(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_face_sum(self.handle, ctypes.cast(buf, c_void_p), ctypes.cast(ca, c_void_p))
        return data

    core.use(None, 'seepage_get_face_average', c_void_p, c_void_p, c_void_p)

    def get_face_average(self, ca, *, buf=None):
        """
        计算face两侧的cell的属性的值的平均值。
            (c1 + c0) / 2
        其中:
            buf为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)

        Args:
            ca: 包含cell属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含平均值数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.face_number)
            buf = f64_ptr(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_face_average(self.handle, ctypes.cast(buf, c_void_p), ctypes.cast(ca, c_void_p))
        return data

    core.use(None, 'seepage_get_face_left', c_void_p, c_void_p, c_void_p)

    def get_face_left(self, ca, *, buf=None):
        """
        计算face左侧的cell属性

        其中:
            buf为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)

        Args:
            ca: 包含cell属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含左侧cell属性数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.face_number)
            buf = f64_ptr(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_face_left(self.handle, ctypes.cast(buf, c_void_p), ctypes.cast(ca, c_void_p))
        return data

    core.use(None, 'seepage_get_face_right', c_void_p, c_void_p, c_void_p)

    def get_face_right(self, ca, *, buf=None):
        """
        计算face右侧的cell属性

        其中:
            buf为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)

        Args:
            ca: 包含cell属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含右侧cell属性数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.face_number)
            buf = f64_ptr(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_face_right(self.handle, ctypes.cast(buf, c_void_p), ctypes.cast(ca, c_void_p))
        return data


class Thermal(HasHandle):
    """
    热传导温度场
    """

    class Cell(Object):
        """
        控制体单元

        该类表示热传导模型中的一个控制体单元，包含与该单元相连的面和其他单元的信息，
        以及该单元的热容量和温度等属性。
        """

        def __init__(self, model, index):
            """
            初始化控制体单元

            Args:
                model (Thermal): 所属的热传导模型
                index (int): 单元的索引，必须小于模型中的单元数量
            """
            assert isinstance(model, Thermal)
            assert index < model.cell_number
            self.model = model
            self.index = index

        def __str__(self):
            """
            返回控制体单元的字符串表示

            Returns:
                str: 包含模型句柄和单元索引的字符串
            """
            return (f'zml.Thermal.Cell(handle = {self.model.handle}, '
                    f'index = {self.index})')

        core.use(c_size_t, 'thermal_get_cell_face_n',
                 c_void_p, c_size_t)

        @property
        def face_number(self):
            """
            连接的Face数量

            Returns:
                int: 与该单元相连的面的数量
            """
            return core.thermal_get_cell_face_n(self.model.handle, self.index)

        @property
        def cell_number(self):
            """
            连接的Cell数量

            Returns:
                int: 与该单元相连的其他单元的数量，等于相连面的数量
            """
            return self.face_number

        core.use(c_size_t, 'thermal_get_cell_face_id',
                 c_void_p, c_size_t,
                 c_size_t)
        core.use(c_size_t, 'thermal_get_cell_cell_id',
                 c_void_p, c_size_t,
                 c_size_t)

        def get_cell(self, index):
            """
            连接的第index个Cell

            Args:
                index (int): 要获取的相邻单元的索引

            Returns:
                Thermal.Cell: 第index个相邻单元，如果索引有效；否则返回None
            """
            index = get_index(index, self.cell_number)
            if index is not None:
                cell_id = core.thermal_get_cell_cell_id(self.model.handle,
                                                        self.index, index)
                return self.model.get_cell(cell_id)
            else:
                return None

        def get_face(self, index):
            """
            连接的第index个Face

            Args:
                index (int): 要获取的相邻面的索引

            Returns:
                Thermal.Face: 第index个相邻面，如果索引有效；否则返回None
            """
            index = get_index(index, self.face_number)
            if index is not None:
                face_id = core.thermal_get_cell_face_id(self.model.handle,
                                                        self.index, index)
                return self.model.get_face(face_id)
            else:
                return None

        @property
        def cells(self) -> Iterable['Thermal.Cell']:
            """
            所有相邻的Cell

            Returns:
                Iterator: 包含所有相邻单元的迭代器
            """
            return Iterator(self, self.cell_number,
                            lambda m, ind: m.get_cell(ind))

        @property
        def faces(self) -> Iterable['Thermal.Face']:
            """
            所有相邻的Face

            Returns:
                Iterator: 包含所有相邻面的迭代器
            """
            return Iterator(self, self.face_number,
                            lambda m, ind: m.get_face(ind))

        core.use(c_double, 'thermal_get_cell_mc',
                 c_void_p, c_size_t)
        core.use(None, 'thermal_set_cell_mc',
                 c_void_p, c_size_t, c_double)

        @property
        def mc(self):
            """
            控制体内物质的热容量，等于物质的质量乘以比热

            Returns:
                float: 控制体的热容量
            """
            return core.thermal_get_cell_mc(self.model.handle, self.index)

        @mc.setter
        def mc(self, value):
            """
            设置控制体内物质的热容量，等于物质的质量乘以比热

            Args:
                value (float): 要设置的热容量值
            """
            core.thermal_set_cell_mc(self.model.handle, self.index, value)

        core.use(c_double, 'thermal_get_cell_T',
                 c_void_p, c_size_t)
        core.use(None, 'thermal_set_cell_T',
                 c_void_p, c_size_t, c_double)

        @property
        def temperature(self):
            """
            控制体内物质的温度 K

            Returns:
                float: 控制体的温度
            """
            return core.thermal_get_cell_T(self.model.handle, self.index)

        @temperature.setter
        def temperature(self, value):
            """
            设置控制体内物质的温度 K

            Args:
                value (float): 要设置的温度值
            """
            core.thermal_set_cell_T(self.model.handle, self.index, value)

    class Face(Object):
        """
        表示热传导模型中的一个界面，包含与该界面相连的单元信息，以及该界面的导热能力等属性。
        """

        def __init__(self, model, index):
            """
            初始化界面

            Args:
                model (Thermal): 所属的热传导模型
                index (int): 界面的索引，必须小于模型中的界面数量
            """
            assert isinstance(model, Thermal)
            assert isinstance(index, int)
            assert index < model.face_number
            self.model = model
            self.index = index

        def __str__(self):
            """
            返回界面的字符串表示

            Returns:
                str: 包含模型句柄和界面索引的字符串
            """
            return (f'zml.Thermal.Face(handle = {self.model.handle}, '
                    f'index = {self.index}) ')

        core.use(c_size_t, 'thermal_get_face_cell_id',
                 c_void_p, c_size_t,
                 c_size_t)

        @property
        def cell_number(self):
            """
            连接的Cell的数量

            Returns:
                int: 与该界面相连的单元数量，固定为2
            """
            return 2

        def get_cell(self, index):
            """
            连接的第index个Cell

            Args:
                index (int): 要获取的相邻单元的索引

            Returns:
                Thermal.Cell: 第index个相邻单元，如果索引有效；否则返回None
            """
            index = get_index(index, self.cell_number)
            if index is not None:
                cell_id = core.thermal_get_face_cell_id(self.model.handle,
                                                        self.index, index)
                return self.model.get_cell(cell_id)
            else:
                return None

        @property
        def cells(self):
            """
            连接的所有的Cell

            Returns:
                tuple: 包含与该界面相连的两个单元的元组
            """
            return self.get_cell(0), self.get_cell(1)

        core.use(c_double, 'thermal_get_face_cond',
                 c_void_p, c_size_t)
        core.use(None, 'thermal_set_face_cond',
                 c_void_p, c_size_t, c_double)

        @property
        def cond(self):
            """
            Face的导热能力. E=cond*dT*dt，其中dT为Face两端的温度差，
            dt为时间步长，E为通过该Face输运的能量(J)

            Returns:
                float: 界面的导热能力
            """
            return core.thermal_get_face_cond(self.model.handle, self.index)

        @cond.setter
        def cond(self, value):
            """
            设置Face的导热能力. E=cond*dT*dt，其中dT为Face两端的温度差，
            dt为时间步长，E为通过该Face输运的能量(J)

            Args:
                value (float): 要设置的导热能力值
            """
            core.thermal_set_face_cond(self.model.handle, self.index, value)

    core.use(c_void_p, 'new_thermal')
    core.use(None, 'del_thermal', c_void_p)

    def __init__(self, path=None, handle=None):
        """
        初始化热传导模型

        Args:
            path (str, optional): 要加载的模型文件路径，如果提供则加载该文件
            handle (c_void_p, optional): 模型的句柄，如果提供则使用该句柄
        """
        super().__init__(handle, core.new_thermal,
                         core.del_thermal)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
        try:
            name = type(self).__name__
            log(f'{name} created', tag=f'{name}_Init')
        except:
            pass

    def __repr__(self):
        return (f'{type(self).__name__}(handle={int(self.handle)}, '
                f'cell_n={self.cell_number}, '
                f'face_n={self.face_number})')

    core.use(None, 'thermal_save',
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
            path (str): 要保存的文件路径
        """
        if isinstance(path, str):
            make_parent(path)
            core.thermal_save(self.handle, make_c_char_p(path))

    core.use(None, 'thermal_load',
             c_void_p, c_char_p)

    def load(self, path):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 要加载的文件路径
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.thermal_load(self.handle, make_c_char_p(path))

    core.use(None, 'thermal_clear',
             c_void_p)

    def clear(self):
        """
        删除所有的Cell和Face
        """
        core.thermal_clear(self.handle)

    core.use(c_size_t, 'thermal_get_cell_n',
             c_void_p)

    @property
    def cell_number(self):
        """
        模型中Cell的数量

        Returns:
            int: 模型中控制体单元的数量
        """
        return core.thermal_get_cell_n(self.handle)

    core.use(c_size_t, 'thermal_get_face_n',
             c_void_p)

    @property
    def face_number(self):
        """
        模型中Face的数量

        Returns:
            int: 模型中界面的数量
        """
        return core.thermal_get_face_n(self.handle)

    def get_cell(self, index):
        """
        模型中第index个Cell

        Args:
            index (int): 要获取的单元的索引

        Returns:
            Thermal.Cell: 第index个单元，如果索引有效；否则返回None
        """
        index = get_index(index, self.cell_number)
        if index is not None:
            return Thermal.Cell(self, index)
        else:
            return None

    def get_face(self, index):
        """
        模型中第index个Face

        Args:
            index (int): 要获取的界面的索引

        Returns:
            Thermal.Face: 第index个界面，如果索引有效；否则返回None
        """
        index = get_index(index, self.face_number)
        if index is not None:
            return Thermal.Face(self, index)
        else:
            return None

    core.use(c_size_t, 'thermal_add_cell',
             c_void_p)

    def add_cell(self):
        """
        添加一个Cell

        Returns:
            Thermal.Cell: 新添加的单元
        """
        cell_id = core.thermal_add_cell(self.handle)
        return self.get_cell(cell_id)

    core.use(c_size_t, 'thermal_add_face',
             c_void_p, c_size_t, c_size_t)

    def add_face(self, cell0, cell1):
        """
        在两个Cell之间添加Face以连接

        Args:
            cell0 (Thermal.Cell): 第一个单元
            cell1 (Thermal.Cell): 第二个单元

        Returns:
            Thermal.Face: 新添加的界面
        """
        assert isinstance(cell0, Thermal.Cell)
        assert isinstance(cell1, Thermal.Cell)
        assert cell0.model.handle == self.handle
        assert cell1.model.handle == self.handle
        assert cell0.index < self.cell_number
        assert cell1.index < self.cell_number
        assert cell0.index != cell1.index
        face_id = core.thermal_add_face(self.handle, cell0.index, cell1.index)
        return self.get_face(face_id)

    core.use(None, 'thermal_iterate',
             c_void_p, c_double, c_void_p)

    def iterate(self, dt, solver):
        """
        利用给定的时间步长dt，向前迭代一步

        Args:
            dt (float): 时间步长
            solver: 求解器对象，必须提供句柄
        """
        lic.check_once()
        assert solver is not None
        core.thermal_iterate(self.handle, dt, solver.handle)

    @property
    def cells(self) -> Iterable['Thermal.Cell']:
        """
        返回所有的Cell

        Returns:
            Iterator: 包含所有控制体单元的迭代器
        """
        return Iterator(self, self.cell_number,
                        lambda m, ind: m.get_cell(ind))

    @property
    def faces(self) -> Iterable['Thermal.Face']:
        """
        返回所有的Face

        Returns:
            Iterator: 包含所有界面的迭代器
        """
        return Iterator(self, self.face_number,
                        lambda m, ind: m.get_face(ind))

    def print_cells(self, path):
        """
        将所有的Cell的信息打印到文件

        Args:
            path (str): 要打印到的文件路径
        """
        with open(path, 'w') as file:
            for cell in self.cells:
                file.write(f'{cell.temperature}\t{cell.mc}\n')

    def exchange_heat(self, model, dt, fid=None,
                      ca_g=None, fa_t=None,
                      fa_c=None):
        """
        与另外一个模型交换热量

        Args:
            model (Seepage): 要交换热量的模型
            dt (float): 时间步长
            fid (optional): 流体ID，默认为None
            ca_g (optional): 单元属性，默认为None
            fa_t (optional): 界面温度，默认为None
            fa_c (optional): 界面导热能力，默认为None
        """
        if isinstance(model, Seepage):
            model.exchange_heat(fid=fid, thermal_model=self,
                                dt=dt, ca_g=ca_g,
                                fa_t=fa_t, fa_c=fa_c)
