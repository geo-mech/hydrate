import os
from io import StringIO

import numpy as np
from scipy.interpolate import NearestNDInterpolator, LinearNDInterpolator

from zml import Interp3
from zmlx.alg.join_cols import join_cols
from zmlx.io.json import ConfigFile


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


def from_file(file=None, data=None, text=None, filename=None, box=None, shape=None, rescale=True):
    """
    利用配置文件来创建3维的插值，在创建的过程中，会将后面给定的参数作为默认参数使用。如果cfg中定义了相应的参数，则最终会使用cfg中
    定义的参数值。
    """
    if file is not None:
        if not isinstance(file, ConfigFile):
            file = ConfigFile(file)

    if data is None:
        data = []

    if file is not None:
        data = file(key='data', default=data,
                    doc='The data of the interp. The data should be a list with only one value '
                        'or a list that can be converted a numpy array with 4 columns')

    data = np.asarray(data)

    if len(data.flatten()) == 0:
        if text is None:
            text = ''
        if file is not None:
            text = file(key='text', default=text,
                        doc='The text used for create data. The text will be read using function '
                            'numpy.readtxt.  The text should be parsed as single float value or '
                            'a numpy array with 4 columns')
        if len(text) > 0:
            data = np.loadtxt(StringIO(text))

    if len(data.flatten()) == 0:
        if filename is None:
            filename = ''
        if file is not None:
            filename = file.find_file(key='filename', default=filename,
                                      doc='The file from which to load data. The file will be read '
                                          'by numpy.readtxt and should be parsed as a 2d array with '
                                          '4 columns')
        if os.path.isfile(filename):
            data = np.loadtxt(filename)

    if len(data.flatten()) == 0:
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

    if box is None:
        box = [0, 0, 0, 1, 1, 1]
    if shape is None:
        shape = [1, 1, 1]

    if file is not None:
        box = file(key='box', default=box,
                   doc='The range of the interp. format: x_min, y_min, z_min, x_max, y_max, z_max')
        shape = file(key='shape', default=shape,
                     doc='The count of grid along each dimension')

    assert len(box) == 6
    assert box[0] <= box[3] and box[1] <= box[4] and box[2] <= box[5]
    assert len(shape) == 3
    assert shape[0] >= 1 and shape[1] >= 1 and shape[2] >= 1

    if file is not None:
        rescale = file(key='rescale', default=rescale,
                       doc='Rescale points to unit cube before performing interpolation. '
                           'This is useful if some of the input dimensions have '
                           'incommensurable units and differ by many orders of magnitude.')

    return create_linear(box=box, shape=shape, x=x, y=y, z=z, v=v, rescale=rescale)
