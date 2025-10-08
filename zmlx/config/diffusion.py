"""
对于某一个流体组分，计算扩散过程。

在计算之前:
    对于cell，需要定义：质量与浓度的比值属性 (c2m);
    对于face，需要定义扩散常数(cond)，其中cond=lambda*area/dist.

计算过程:
    1、根据流体的质量，c2m，计算当前的浓度c; m=c*c2m, 因此 c=m/c2m
    2、根据cond，使用温度场的迭代方法，计算dt之后的浓度c；
    3、根据浓度c，再更新最新的流体质量m.

@2025-10-2
"""
from zmlx.base.seepage import as_numpy
from zmlx.exts.base import Seepage


def iterate(model: Seepage, fid, dt, ca_c2m, fa_g, ca_c=None, cfl=None):
    """
    计算扩散过程.
    Args:
        model: 需要被迭代的模型
        fid: 流体组分的索性
        dt: 时间步长
        ca_c: 浓度属性的索引 (默认None)
        ca_c2m: 质量和浓度的比值
        fa_g: cond
        cfl: CFL数

    Returns:
        计算的报告。一个dict类型. 当cfl不为None时，会返回建议的时间步长dt.
    """
    # 做迭代前的准备
    if ca_c is None:
        ca_c = model.reg_cell_key('temp_variable')  # 临时变量

    c2m = as_numpy(model).cells.get(ca_c2m)
    c = as_numpy(model).fluids(*fid).mass / c2m  # 浓度
    as_numpy(model).cells.set(ca_c, c)  # 设置浓度属性(对应于温度)

    # 调用温度的接口进行迭代
    r = model.iterate_thermal(
        dt, ca_t=ca_c, ca_mc=ca_c2m, fa_g=fa_g, solver=None,
        pool=None, report=None
    )
    if r is None:
        r = {}

    # 根据浓度计算质量m
    c = as_numpy(model).cells.get(ca_c)
    as_numpy(model).fluids(*fid).mass = c * c2m

    # 尝试计算建议的时间步长dt
    if cfl is not None:
        dt_new = model.get_recommended_dt(
            dt,
            ca_t=ca_c, ca_mc=ca_c2m, cfl=cfl)
        r['dt'] = dt_new

    # 返回计算的报告
    return r
