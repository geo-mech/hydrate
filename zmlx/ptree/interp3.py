import numpy as np
from scipy.interpolate import NearestNDInterpolator, LinearNDInterpolator

from zml import Interp3
from zmlx.alg.utils import join_cols
from zmlx.alg.fsys import *
from zmlx.ptree.array import array
from zmlx.ptree.box import box3
from zmlx.ptree.ptree import PTree
from zmlx.ptree.size import size3


def create_linear(box, size, x, y, z, v, rescale=True):
    """
    创建zml插值
    """
    if len(v) == 1:
        return Interp3.create_const(v[0])

    points = join_cols(x, y, z)
    values = v
    try:
        f1 = LinearNDInterpolator(points, values, rescale=rescale, fill_value=np.nan)
    except:
        def f1(*args):
            return np.nan
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

    assert len(box) == 6
    assert box[0] <= box[3] and box[1] <= box[4] and box[2] <= box[5]
    assert len(size) == 3
    assert size[0] >= 1 and size[1] >= 1 and size[2] >= 1

    f = Interp3()
    f.create(xmin=box[0], dx=(box[3] - box[0]) / size[0], xmax=box[3],
             ymin=box[1], dy=(box[4] - box[1]) / size[1], ymax=box[4],
             zmin=box[2], dz=(box[5] - box[2]) / size[2], zmax=box[5], get_value=get_value)
    return f


def interp3(pt):
    """
    利用配置文件来创建3维的插值
    """
    assert isinstance(pt, PTree)

    if isinstance(pt.data, str):  # 尝试读取文件
        fname = pt.find(pt.data)
        if isfile(fname):
            return Interp3(path=fname)
        else:
            return

    if isinstance(pt.data, (int, float)):  # 创建常量.
        return Interp3.create_const(pt.data)

    data = array(pt['data'])

    if data is None:
        return

    if len(data.shape) == 1:
        if len(data) == 1:
            return Interp3.create_const(data[0])

    assert len(data.shape) == 2
    assert data.shape[1] >= 4

    x = data[:, 0]
    y = data[:, 1]
    z = data[:, 2]
    v = data[:, 3]

    box = box3(pt['box'])
    size = size3(pt['size'])

    assert len(box) == 6
    assert box[0] <= box[3] and box[1] <= box[4] and box[2] <= box[5]
    assert len(size) == 3
    assert size[0] >= 1 and size[1] >= 1 and size[2] >= 1

    rescale = pt('rescale',
                 doc='Rescale points to unit cube before performing interpolation. '
                     'This is useful if some of the input dimensions have '
                     'incommensurable units and differ by many orders of magnitude.')

    return create_linear(box=box, size=size, x=x, y=y, z=z, v=v, rescale=rescale if rescale is not None else False)


def test():
    pt = PTree()
    pt.data = {
        "data": [
            [
                0,
                0,
                0,
                0
            ],
            [
                1,
                0,
                0,
                1
            ],
            [
                0,
                1,
                0,
                2
            ],
            [
                0,
                0,
                1,
                3
            ]
        ],
        "box": [
            0,
            0,
            0,
            1,
            1,
            1
        ],
        "size": [
            10,
            10,
            10
        ]
    }
    f = interp3(pt)
    print(f.get(0, 0, 0))
    print(f.get(1, 0, 0))


if __name__ == '__main__':
    test()
