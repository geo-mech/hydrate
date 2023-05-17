# -*- coding: utf-8 -*-


from zml import Reaction
from zmlx.alg.make_index import make_index


def create(iflu, isol, vp, vt, temp, heat, fa_t, fa_c, t2q=None):
    """
    创建一个从液体到固体结冰的反应，或者从气体到液体的凝结过程(默认：平衡态的反应，反应的速率给的非常大);

    其中：
        当模拟结冰/融化时：iflu为液体，isol为固体；假设融化吸热
        当模拟凝结/蒸发时：iflu为气体，isol为液体；假设蒸发吸热

    相变的温度和压力相关：
        vp为压力，vt温度

    相变的耗能由temp和heat指定：
        temp为参考温度，heat为在该参考温度下发生1kg物质相变的时候所消耗（或产生）的能量，大于0

    流体的温度和比热：
        fa_t和fa_c为流体的属性，代表流体的温度和比热;

    相变的速度由t2q指定，必须满足：
        当温度t等于0的时候，q等于0；
        当温度t小于0的时候，q大于0；
        当温度t大于0的时候，q小于0；
    """
    data = Reaction()
    data.add_component(index=make_index(iflu), weight=-1, fa_t=fa_t, fa_c=fa_c)
    data.add_component(index=make_index(isol), weight=1, fa_t=fa_t, fa_c=fa_c)
    data.set_p2t(vp, vt)
    data.temp = temp
    assert heat > 0, 'Heat released when fluid convert to solid <icing>'
    data.heat = heat
    if t2q is None:
        data.set_t2q([-300, 0, 300], [300, 0, -300])
    else:
        assert len(t2q) == 2
        data.set_t2q(*t2q)
    return data
