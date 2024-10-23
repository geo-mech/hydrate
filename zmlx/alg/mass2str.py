def mass2str(kg):
    """
    将质量从千克转换为字符串表示，使用微克（ug）、毫克（mg）、克（g）、千克（kg）和吨（t）作为单位。

    参数:
    kg (float): 要转换的质量，单位为千克。

    返回:
    str: 质量的字符串表示，格式为 'x.xxug', 'x.xxmg', 'x.xxg', 'x.xxkg' 或 'x.xx t'。
    """
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
