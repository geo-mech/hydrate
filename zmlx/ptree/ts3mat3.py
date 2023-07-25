from zml import *
from zmlx.ptree.box import box3
from zmlx.ptree.ptree import PTree
from zmlx.ptree.size import size3
from zmlx.ptree.ts3intp3 import get_ts3intp3, Ts3Interp3


def ts3mat3(pt, buffer=None, box=None, size=None):
    """
    创建一个张量的矩阵。其中：
        buffer是即将写入的矩阵
        pt是给定的PTree
    当box为None的时候，则从pt中读取box;
    """
    assert isinstance(pt, PTree)
    if not isinstance(buffer, Tensor3Matrix3):
        buffer = Tensor3Matrix3()

    interp = get_ts3intp3(pt['data'])

    if not isinstance(interp, Ts3Interp3):
        print('can not set without given interp as Ts3Interp3')
        return buffer

    if size is None:
        size = size3(pt['size'])

    assert len(size) == 3
    assert size[0] >= 1 and size[1] >= 1 and size[2] >= 1
    assert size[0] < 1000 and size[1] < 1000 and size[2] < 1000

    buffer.size = size

    if box is None:
        box = box3(pt['box'])

    assert len(box) == 6
    left = box[0: 3]
    right = box[3: 6]

    step = [(right[i] - left[i]) / max(1.0, size[i] - 1) for i in range(3)]

    # 遍历，设置矩阵的元素.
    for i0 in range(size[0]):
        x0 = left[0] + i0 * step[0]
        for i1 in range(size[1]):
            x1 = left[1] + i1 * step[1]
            for i2 in range(size[2]):
                x2 = left[2] + i2 * step[2]
                stress = interp(x0, x1, x2)
                buffer[(i0, i1, i2)].clone(stress)

    return buffer


def test():
    pt = PTree()
    pt.data = {
        "size": [
            4,
            4,
            4
        ],
        "box": [
            0,
            0,
            0,
            1,
            1,
            1
        ],
        "data": [
            1,
            2,
            3,
            4
        ]
    }
    m = ts3mat3(pt)
    print(m.size)


if __name__ == '__main__':
    test()
