def time2str(s):
    """
    将时间从秒转换为字符串表示，使用纳秒（ns）、微秒（us）、毫秒（ms）、秒（s）、分钟（m）、小时（h）、天（d）和年（y）作为单位。

    参数:
    s (float): 要转换的时间，单位为秒。

    返回:
    str: 时间的字符串表示，格式为 'x.xxns', 'x.xxus', 'x.xxms', 'x.xxs', 'x.xxm', 'x.xxh', 'x.xxd' 或 'x.xxy'。
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
