def mass2str(kg):
    """将千克为单位的质量转换为带合适单位的字符串表示。

    根据质量大小自动选择合适的计量单位，转换优先级为：微克(ug) < 毫克(mg) < 克(g) < 千克(kg) < 吨(t)
    转换阈值为2000（当数值绝对值超过2000时使用更大单位）

    Args:
        kg (float): 以千克为单位的质量值，支持正负值

    Returns:
        str: 格式化的带单位字符串，保留两位小数。单位符号直接附加在数值后，吨(t)除外：
            - 数值范围在±2000ug内时返回ug单位
            - 数值范围在±2000mg内时返回mg单位
            - 数值范围在±2000g内时返回g单位
            - 数值范围在±2000kg内时返回kg单位
            - 超过±2000kg时返回吨(t)单位
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


def time2str(s):
    """将时间从秒转换为字符串表示，使用纳秒（ns）、微秒（us）、毫秒（ms）、秒（s）、
    分钟（m）、小时（h）、天（d）和年（y）作为单位。

    Args:
        s (float): 要转换的时间，单位为秒。

    Returns:
        str: 时间的字符串表示，格式为 'x.xxns', 'x.xxus', 'x.xxms', 'x.xxs',
        'x.xxm', 'x.xxh', 'x.xxd' 或 'x.xxy'。
    """
    if abs(s) < 200:
        if s > 2.0:
            return '%.2fs' % s
        s *= 1000
        if s > 2.0:
            return '%.2fms' % s
        s *= 1000
        if s > 2.0:
            return '%.2fus' % s
        s *= 1000
        return '%.2fns' % s
    m = s / 60
    if abs(m) < 200:
        return '%.2fm' % m
    h = m / 60
    if abs(h) < 60:
        return '%.2fh' % h
    d = h / 24
    if abs(d) < 800:
        return '%.2fd' % d
    y = d / 365
    return '%.2fy' % y


def fsize2str(size):
    size /= 1024
    if size < 2000:
        return '%0.2f kb' % size

    size /= 1024
    if size < 2000:
        return '%0.2f Mb' % size

    size /= 1024
    if size < 2000:
        return '%0.2f Gb' % size
    else:
        size /= 1024
        return '%0.2f Tb' % size
