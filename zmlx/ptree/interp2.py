import numpy as np
from scipy.interpolate import NearestNDInterpolator, LinearNDInterpolator

from zml import Interp2
from zmlx.alg.join_cols import join_cols
from zmlx.ptree.array import array
from zmlx.ptree.box import box2
from zmlx.ptree.ptree import PTree, open_pt
from zmlx.ptree.size import size2


def create_const(value):
    """
    创建常量场(给定的数值)
    """
    f = Interp2()
    f.create(xmin=0, dx=0, xmax=0, ymin=0, dy=0, ymax=0, get_value=lambda *args: value)
    return f


def create_linear(box, size, x, y, z, rescale=True):
    """
    创建zml二维插值
    """
    if len(z) == 1:
        return create_const(z[0])

    points = join_cols(x, y)
    values = z
    f1 = LinearNDInterpolator(points, values, rescale=rescale, fill_value=np.nan)
    f2 = NearestNDInterpolator(points, values, rescale=rescale)

    def get_value(*args):
        """
        返回给定点的数值
        """
        v = f1(*args)
        if np.isnan(v):
            return f2(*args)
        else:
            return v

    assert len(box) == 4
    assert box[0] <= box[2] and box[1] <= box[3]
    assert len(size) == 2
    assert size[0] >= 1 and size[1] >= 1

    f = Interp2()
    f.create(xmin=box[0], dx=(box[2] - box[0]) / size[0], xmax=box[2],
             ymin=box[1], dy=(box[3] - box[1]) / size[1], ymax=box[3], get_value=get_value)
    return f


def interp2(pt):
    """
    利用配置文件来创建二维的插值
    """
    assert isinstance(pt, PTree)
    data = array(pt['data'])

    if data is None:
        return

    if len(data.shape) == 1:
        if len(data) == 1:
            return create_const(data[0])

    assert len(data.shape) == 2
    assert data.shape[1] >= 3

    x = data[:, 0]
    y = data[:, 1]
    z = data[:, 2]

    box = box2(pt['box'])
    size = size2(pt['size'])

    assert len(box) == 4
    assert box[0] <= box[2] and box[1] <= box[3]
    assert len(size) == 2
    assert size[0] >= 1 and size[1] >= 1

    rescale = pt('rescale',
                 doc='Rescale points to unit cube before performing interpolation. '
                     'This is useful if some of the input dimensions have '
                     'incommensurable units and differ by many orders of magnitude.')

    return create_linear(box=box, size=size, x=x, y=y, z=z, rescale=rescale if rescale is not None else False)


def test():
    pt = PTree()
    pt.data = {
        "data": 5,
        "box": [
            0,
            0,
            1,
            1
        ],
        "size": [
            9,
            9
        ]
    }
    f = interp2(pt)
    print(f.get(0, 0))
    print(f.get(1, 1))


if __name__ == '__main__':
    test()
