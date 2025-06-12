from zmlx.react import endothermic


def create(gas, liq, hyd, mg, vp, vt, temp, heat, fa_t=None, fa_c=None,
           t2q=None, rate=1.0,
           dissociation=True, formation=True):
    """
    创建一个水合物反应<一种固体hyd和两种流体<gas, liq>之间的可逆反应>
        (默认<当t2p未指定的时候>使用rate)
    by 张召彬

    注意：
        返回一个dict，包含了反应的所有的信息。此dict定义的data可以在
        zmlx.react.alg.add_reaction中使用，将反应添加到Seepage中
    """
    assert 0 < mg < 1, f'The mg should be in (0, 1) while it is {mg}'
    assert heat > 0
    assert dissociation or formation
    return endothermic.create(
        left=[(hyd, 1.0), ],
        right=[(gas, mg),
               (liq, 1.0 - mg)],
        temp=temp,
        heat=heat,
        rate=rate,
        fa_t=fa_t,
        fa_c=fa_c,
        l2r=dissociation,  # 允许水合物分解
        r2l=formation,  # 允许水合物生成
        p2t=[vp, vt], t2q=t2q)
