def shape(pt, ndim, default=None):
    assert 0 < ndim < 10

    if default is not None:
        assert len(default) == ndim

    result = []

    for dim in range(ndim):
        a = pt(key=f'shape{dim}', default=default[dim] if default is not None else 0,
               doc=f'The shape of dimension {dim}', cast=int)
        assert a >= 0
        result.append(a)

    return result


def shape2(pt, default=None):
    return shape(pt, ndim=2, default=default)


def shape3(pt, default=None):
    return shape(pt, ndim=3, default=default)
