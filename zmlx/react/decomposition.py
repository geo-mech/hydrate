# -*- coding: utf-8 -*-


from zml import Reaction
from zmlx.alg.make_index import make_index
from zmlx.alg.clamp import clamp


def create(index, iweights, temp, heat, rate, fa_t, fa_c):
    """
    创建物质吸热分解的反应<不可逆的>. 其中index为待分解的物质，iweights为右侧物质的序号和权重，temp为分解的温度，heat为分解1kg左侧物质的耗能，
    rate是温度超过分解温度1度的时候，对于左侧1kg的物质，1s内能否反应的物质的质量；
    fa_t和fa_c为物质的属性ID，定义物质的温度和比热;
    """

    data = Reaction()

    assert fa_t >= 0
    assert fa_c >= 0
    # 左侧的物质
    data.add_component(index=make_index(index), weight=-1.0, fa_t=fa_t, fa_c=fa_c)

    # 右侧的物质
    for index, weight in iweights:
        data.add_component(index=make_index(index), weight=clamp(weight, 1.0e-5, 1.0), fa_t=fa_t, fa_c=fa_c)

    assert temp > 0
    assert heat > 0
    assert rate > 0

    # 设置分解的温度曲线 <与压力无关的曲线>
    data.set_p2t([0.01e6, 100e6], [temp, temp])
    data.temp = temp
    data.heat = heat

    # 定义反应的速率
    data.set_t2q([-100, 0, 100], [0, 0, rate * 100])

    # 完成，返回数据
    return data

