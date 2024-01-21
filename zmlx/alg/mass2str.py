def mass2str(kg):
    ug = kg * 1.0e9
    if abs(ug) < 2000:
        return '%.2fug' % ug
    mg = ug / 1000
    if abs(mg) < 2000:
        return '%.2fmg' % mg
    g = mg / 1000
    if abs(g) < 2000:
        return '%.2fg' % g
    kg = g / 1000
    if abs(kg) < 2000:
        return '%.2fkg' % kg
    t = kg / 1000
    return '%.2ft' % t

