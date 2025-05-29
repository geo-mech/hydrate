from zmlx.ptree.array import array
from zmlx.ptree.ptree import PTree


def size(pt, ndim):
    assert isinstance(pt, PTree)
    data = array(pt)
    if data is None:
        return None
    if len(data) >= ndim:
        return [round(data[i]) for i in range(ndim)]
    return None


def size2(pt):
    return size(pt, ndim=2)


def size3(pt):
    return size(pt, ndim=3)


def test():
    pt = PTree()
    pt.data = '1.0, 2.1, 3.3, 4.4'
    print(size2(pt))
    print(size3(pt))
    print(pt.data)


if __name__ == '__main__':
    test()
