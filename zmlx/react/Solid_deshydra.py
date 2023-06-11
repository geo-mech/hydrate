# -*- coding: utf-8 -*-


from zmlx.react import endothermic


def create(isol_d, iliq, isol, mg, vp, vt, temp, heat, fa_t, fa_c, t2q=None):
    """
    Create a reversible reaction of <(isol_d)> dehydration (i.e Ca(OH)2) and <(isol)> hydration (i.e. CaO).
    During dehydratation process (heat storage), <(isol_d)> absorbs heat and decomposes to produce <(isol)> and <(iliq)>.
    In the exothermic process, <(isol)> reacts with <(iliq)> to form <(isol_d)>, 
    releasing stored chemical energy as heat.
    by Maryelin
    """
    assert 0 < mg < 1, f'The mg should be in (0, 1) while it is {mg}'
    assert heat > 0
    return endothermic.create(left=[(isol_d, 1.0), ],
                              right=[(isol, 1.0), (iliq, 1.0 - mg)],
                              temp=temp, heat=heat,
                              rate=1.0,
                              fa_t=fa_t, fa_c=fa_c,
                              l2r=True, r2l=True,
                              p2t=[vp, vt], t2q=t2q)
