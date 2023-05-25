from zmlx.react import endothermic


def create(igas, iliq, isol, mg, vp, vt, temp, heat, fa_t, fa_c, t2q=None):
    """
    创建一个水合物反应<一种固体isol和两种流体<igas, iliq>之间的可逆反应>
        (默认<当t2p未指定的时候>为平衡态的反应，即反应的速率给的非常大<几乎相当于无穷大>)
    by 张召彬
    """
    assert 0 < mg < 1, f'The mg should be in (0, 1) while it is {mg}'
    assert heat > 0
    return endothermic.create(left=[(isol, 1.0), ],
                              right=[(igas, mg),
                                     (iliq, 1.0 - mg)],
                              temp=temp, heat=heat,
                              rate=1.0,
                              fa_t=fa_t, fa_c=fa_c,
                              l2r=True, r2l=True,
                              p2t=[vp, vt], t2q=t2q)

