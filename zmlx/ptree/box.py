from zmlx.ptree.val_range import val_range


def box2(pt, doc=None, default=None):
    """
    返回二维的box
    """
    if default is None:
        default = [0, 0, 1, 1]
    else:
        assert len(default) == 4
        assert default[0] <= default[2]
        assert default[1] <= default[3]
    x0, x1 = val_range(pt['x'], doc=f'x ({doc})', default=[default[0], default[2]])
    y0, y1 = val_range(pt['y'], doc=f'y ({doc})', default=[default[1], default[3]])
    return [x0, y0, x1, y1]


def box3(pt, doc=None, default=None):
    """
    返回二3维的box
    """
    if default is None:
        default = [0, 0, 0, 1, 1, 1]
    else:
        assert len(default) == 6
        assert default[0] <= default[3]
        assert default[1] <= default[4]
        assert default[2] <= default[5]
    x0, x1 = val_range(pt['x'], doc=f'x ({doc})', default=[default[0], default[3]])
    y0, y1 = val_range(pt['y'], doc=f'y ({doc})', default=[default[1], default[4]])
    z0, z1 = val_range(pt['z'], doc=f'z ({doc})', default=[default[2], default[5]])
    return [x0, y0, z0, x1, y1, z1]


def test():
    from zmlx.ptree.ptree import PTree
    pt = PTree()
    print(box3(pt, doc='Test', default=[1, 2, 3, 4, 5, 6]))
    print(pt.data)


if __name__ == '__main__':
    test()
