# -*- coding: utf-8 -*-


from zmlx.react.freeze import create as create_freeze


def create(iflu, isol, fa_t, fa_c, temp=273.15, heat=336000.0):
    """
    创建水和水冰之间相变的反应;
    """
    assert 250.0 < temp < 350.0
    assert 0 < heat
    vp = [0, 1e8]
    vt = [temp, temp]
    return create_freeze(iflu=iflu, isol=isol, vp=vp, vt=vt,
                         temp=temp, heat=heat, fa_t=fa_t, fa_c=fa_c, t2q=None)
