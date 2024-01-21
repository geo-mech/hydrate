def time2str(s):
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

