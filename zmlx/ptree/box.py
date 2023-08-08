def box(pt, ndim, default=None):
    assert 0 < ndim < 10

    if default is not None:
        assert len(default) == ndim * 2

    left, right = [], []
    for dim in range(ndim):
        a = pt(key=f'left{dim}', default=default[dim] if default is not None else 0.0,
               doc=f'The left range of dimension {dim}', cast=float)
        b = pt(key=f'right{dim}', default=default[dim + ndim] if default is not None else 0.0,
               doc=f'The right range of dimension {dim}', cast=float)
        assert a <= b
        left.append(a)
        right.append(b)

    return left + right


def box2(pt, default=None):
    return box(pt, ndim=2, default=default)


def box3(pt, default=None):
    return box(pt, ndim=3, default=default)

