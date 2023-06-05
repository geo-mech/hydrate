from zmlx.react import melt


def create(iflu, isol, fa_t, fa_c, temp=273.15, heat=336000.0):
    """
    创建水冰融化的反应（以及其逆过程）
    """
    assert 250.0 < temp < 350.0
    assert 0 < heat
    return melt.create(sol=isol, flu=iflu, temp=temp, heat=heat,
                       fa_t=fa_t, fa_c=fa_c)

