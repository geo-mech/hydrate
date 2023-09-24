from zmlx.ptree.array import array
from zmlx.ptree.ptree import PTree, open_pt


def box(pt, ndim):
    assert isinstance(pt, PTree)
    data = array(pt)
    if data is None:
        return
    if len(data) // 2 >= ndim:
        data_dim = len(data) // 2
        left, right = [], []
        for dim in range(ndim):
            a = data[dim]
            b = data[dim + data_dim]
            assert a <= b
            left.append(a)
            right.append(b)
        return left + right


def box2(pt):
    return box(pt, ndim=2)


def box3(pt):
    return box(pt, ndim=3)


def test():
    pt = open_pt('box.json')
    print(box2(pt))
    print(pt.data)


if __name__ == '__main__':
    test()
