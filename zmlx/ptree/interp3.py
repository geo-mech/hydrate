import numpy as np
from scipy.interpolate import NearestNDInterpolator, LinearNDInterpolator
from zml import Interp3
from zmlx.alg.join_cols import join_cols
from zmlx.ptree.array import array
from zmlx.ptree.box import box3
from zmlx.ptree.shape import shape3


def create_const(value):
    """
    创建常量场(给定的数值)
    """
    f = Interp3()
    f.create(xmin=0, dx=0, xmax=0,
             ymin=0, dy=0, ymax=0,
             zmin=0, dz=0, zmax=0, get_value=lambda *args: value)
    return f


def create_linear(box, shape, x, y, z, v, rescale=True):
    """
    创建zml插值
    """
    if len(v) == 1:
        return create_const(v[0])

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
    assert len(shape) == 3
    assert shape[0] >= 1 and shape[1] >= 1 and shape[2] >= 1

    f = Interp3()
    f.create(xmin=box[0], dx=(box[3] - box[0]) / shape[0], xmax=box[3],
             ymin=box[1], dy=(box[4] - box[1]) / shape[1], ymax=box[4],
             zmin=box[2], dz=(box[5] - box[2]) / shape[2], zmax=box[5], get_value=get_value)
    return f


def interp3(pt, data=None, text=None, file=None, box=None, shape=None, rescale=True):
    """
    利用配置文件来创建3维的插值，在创建的过程中，会将后面给定的参数作为默认参数使用。如果cfg中定义了相应的参数，则最终会使用cfg中
    定义的参数值。
    """
    data = array(pt=pt, data=data, text=text, file=file)

    if data is None:
        return

    if len(data.shape) == 1:
        if len(data) == 1:
            return create_const(data[0])

    assert len(data.shape) == 2
    assert data.shape[1] == 4

    x = data[:, 0]
    y = data[:, 1]
    z = data[:, 2]
    v = data[:, 3]

    box = box3(pt, default=box if box is not None else [0, 0, 0, 1, 1, 1])
    shape = shape3(pt, default=shape if shape is not None else [1, 1, 1])

    assert len(box) == 6
    assert box[0] <= box[3] and box[1] <= box[4] and box[2] <= box[5]
    assert len(shape) == 3
    assert shape[0] >= 1 and shape[1] >= 1 and shape[2] >= 1

    rescale = pt(key='rescale', default=rescale,
                 doc='Rescale points to unit cube before performing interpolation. '
                     'This is useful if some of the input dimensions have '
                     'incommensurable units and differ by many orders of magnitude.')

    return create_linear(box=box, shape=shape, x=x, y=y, z=z, v=v, rescale=rescale)
