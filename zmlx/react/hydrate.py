# -*- coding: utf-8 -*-


from zml import Reaction
from zmlx.alg.make_index import make_index


def create(igas, iliq, isol, mg, vp, vt, temp, heat, fa_t, fa_c, t2p=None):
    """
    创建一个水合物反应<一种固体isol和两种流体<igas, iliq>之间的可逆反应>
        (默认<当t2p未指定的时候>为平衡态的反应，即反应的速率给的非常大<几乎相当于无穷大>)
    by 张召彬
    """
    data = Reaction()
    assert 0 < mg < 1, f'The mg should be in (0, 1) while it is {mg}'
    mw = 1 - mg
    data.add_component(index=make_index(igas), weight=-mg, fa_t=fa_t, fa_c=fa_c)
    data.add_component(index=make_index(iliq), weight=-mw, fa_t=fa_t, fa_c=fa_c)
    data.add_component(index=make_index(isol), weight=1.0, fa_t=fa_t, fa_c=fa_c)
    data.set_p2t(vp, vt)
    data.temp = temp
    data.heat = heat
    if t2p is None:
        # 采用默认的，就是反应的速率非常大
        data.set_t2q([-30, 0, 30], [30, 0, -30])
    else:
        t, p = t2p  # 假设给定t2p包含两个list.  Since 2023-1-28
        assert len(t) == len(p), f'len(t) = {len(t)} and len(p) = {len(p)}, they should be equal'
        data.set_t2q(t, p)

    return data
