def val_range(pt, doc=None, default=None):
    """
    返回一个数据的范围. 由min和max定义的数据的范围.
    """
    if default is None:
        default = [0, 1]
    else:
        assert len(default) == 2
        assert default[0] <= default[1]

    a = pt('min',
           doc=f'The minimum value. ({doc})',
           default=default[0])
    b = pt('max',
           doc=f'The maximum value. ({doc})',
           default=default[1])

    # 返回范围.
    return [a, b]


def test():
    from zmlx.ptree.ptree import PTree
    pt = PTree()
    print(val_range(pt, default=[2, 3]))
    print(pt.data)


if __name__ == '__main__':
    test()
