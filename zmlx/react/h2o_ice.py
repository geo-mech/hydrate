from zmlx.react import melt


def create(flu, sol, fa_t=None, fa_c=None, temp=273.15, heat=336000.0,
           enable_melt=True, enable_freeze=True):
    """
    创建水冰融化的反应（以及其逆过程）
    """
    assert 250.0 < temp < 350.0
    assert 0 < heat
    return melt.create(
        sol=sol, flu=flu, temp=temp, heat=heat,
        fa_t=fa_t, fa_c=fa_c, l2r=enable_melt, r2l=enable_freeze)
