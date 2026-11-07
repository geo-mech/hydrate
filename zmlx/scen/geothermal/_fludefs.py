"""井截面取热模型的**流体定义**（``create_fludefs``）.

网格在 ``_mesh.py``，流体在本文件，建模（孔隙度、压力、温度 / 热容边界）
由 ``_well_cross_section.py`` 组装。
换流体（水 → 其它介质、单相 → 多相）时只需改这里，不必动建模逻辑。

为什么单独拆出来
----------------

``tfc.create(fludefs=...)`` 收的是一张 ``FluDef`` 列表，而 ``h2o.create`` 的
**物性表在调用时就会建好**（密度 / 粘度各插一张 ``Interp2`` 表，见
``zmlx/fluids/h2o.py``）。所以它既不是纯常量、也不适合和几何参数混在一起 ——
单独成模块后，「这次算例用水」这件事一眼可见。
"""

import math

from zmlx import FluDef, Interp2, h2o

#: 水的物性表范围（温度 K、压力 Pa）.
#:
#: ⚠️ **这两个数是查表的钳制边界，不是「算例的温度区间」**：``h2o.create`` 内部对
#: 超出范围的值做 ``max(t_min, min(t_max, T))`` 截断 —— 温度跑到表外会被**按边界值**
#: 计算，不会报错、也不会外推。于是范围给窄了，物性就成了「常数」，这对流场是**静默**的失真。
#:
#: 取值依据（本算例，见 ``cases/case_02.py``）：
#:
#: - 温度 280~320 K（井单元 280、其余岩石 320），故 ``t_min`` 取 272 留出
#:   结冰点附近的余量、``t_max`` 取 340 留出升温余量；
#: - 压力 5 MPa（``_well_cross_section.py`` 的 ``p=5e6``），``[1 MPa, 40 MPa]`` 覆盖了它。
T_MIN, T_MAX = 272.0, 340.0
P_MIN, P_MAX = 1.0e6, 40.0e6


def create_fludefs(*, t_min=None, t_max=None):
    """创建算例用的流体定义列表（当前只有**液态水**一种）.

    物性的温度 / 压力范围取模块级常量 ``T_MIN`` / ``T_MAX`` / ``P_MIN`` /
    ``P_MAX``（含义与注意事项见那一段注释）。

    Args:
        t_min: 可选查表下界K，默认沿用T_MIN。
        t_max: 可选查表上界K，默认沿用T_MAX；达到350K时沿用原公式重建表。

    Returns:
        list[FluDef]: 长度为 1 的列表，元素是名为 ``'h2o'`` 的水。
        ``tfc.create(fludefs=...)`` 要的就是这张表；在算例里它是**第 0 号流体**，
        所以 ``tfc.get_fa(model, 0, 'temperature', ...)`` 之类的 ``0`` 就指它。

    Raises:
        ValueError: 显式温度范围不满足269 < t_min < t_max <= 400 K。
        AssertionError: ``h2o.create`` 内部对范围有硬断言
            ``269 < t_min < t_max < 350`` 与 ``0.01e6 < p_min < p_max < 50e6``；
            模块级常量若被改到界外（例如把 ``t_max`` 提到 474），这里会失败。

    ⚠️ 返回值是**新建的列表**，每次调用都重新建物性表 —— 不要在一次建模里反复调它，
    也不要把返回值当常量缓存后跨模型复用（``FluDef`` 会绑到具体模型上）。

    ⚠️ 只返回列表、不返回单个 ``FluDef``：``tfc.create`` 的 ``fludefs`` 要的就是
    列表，多相算例以后往这里追加元素即可，接口不必改。
    """
    lower = T_MIN if t_min is None else float(t_min)
    upper = T_MAX if t_max is None else float(t_max)
    if not (269 < lower < upper <= 400):
        raise ValueError("水表要求269 < t_min < t_max <= 400 K")
    if upper >= 350:
        # 不能直接把370K传给h2o.create：该函数有T<350的硬断言。
        # 此处保留原公式和4200比热；高于350K仍属于未经标定的外推。
        def density(pressure, temperature):
            """按原水密度拟合返回kg/m³；输入为Pa和K。"""
            return 999.8 * (1 + pressure / 2e9) * (1 - 0.0002 * ((temperature - 277) / 5.6) ** 2)

        def viscosity(pressure, temperature):
            """按原水黏度拟合返回Pa·s；输入为Pa和K。"""
            return 2e-6 * math.exp(1808.5 / temperature)

        den, vis = Interp2(), Interp2()
        den.create(P_MIN, 0.1e6, P_MAX, lower, 0.5, upper, density)
        vis.create(P_MIN, 0.1e6, P_MAX, lower, 0.5, upper, viscosity)
        return [FluDef(den=den, vis=vis, specific_heat=4200, name="h2o")]
    fludefs = [h2o.create(t_min=lower, t_max=upper, p_min=P_MIN, p_max=P_MAX, name="h2o")]
    return fludefs
