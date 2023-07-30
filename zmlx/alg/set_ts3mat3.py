from zml import *
from zmlx.interp.Tensor3 import from_file, Interp3 as Ts3Interp3
from zmlx.io.json import ConfigFile
import warnings


def set_ts3mat3(mat3, file=None, box=None, shape=None, interp=None, filename=None, text=None):
    """
    设置张量场。注意，如果file有定义，则最终使用file定义的数值
    """
    assert isinstance(mat3, Tensor3Matrix3)

    if file is not None:
        if not isinstance(file, ConfigFile):
            file = ConfigFile(file)

    if interp is None:
        interp = from_file(file=file, filename=filename, text=text)

    if not isinstance(interp, Ts3Interp3):
        warnings.warn('can not set mat3 without given interp as Ts3Interp3')
        return

    if shape is None:
        shape = [2, 2, 2]

    if file is not None:
        shape = file(key='shape', default=shape,
                     doc='The grid number along dimension each dimension [jx, jy, jz]')

    # 检查数据的范围.
    assert shape is not None
    assert len(shape) == 3
    assert shape[0] >= 1 and shape[1] >= 1 and shape[2] >= 1
    assert shape[0] < 1000 and shape[1] < 1000 and shape[2] < 1000

    mat3.size = shape

    if box is None:
        box = [0, 0, 0, 1, 1, 1]

    if file is not None:
        box = file(key='box', default=box,
                   doc='The position range [xmin, ymin, zmin, xmax, ymax, zmax]')

    assert len(box) == 6
    left = box[0: 3]
    right = box[3: 6]

    step = [(right[i] - left[i]) / max(1.0, shape[i] - 1) for i in range(3)]

    # 遍历，设置矩阵的元素.
    for i0 in range(shape[0]):
        x0 = left[0] + i0 * step[0]
        for i1 in range(shape[1]):
            x1 = left[1] + i1 * step[1]
            for i2 in range(shape[2]):
                x2 = left[2] + i2 * step[2]
                stress = interp(x0, x1, x2)
                mat3[(i0, i1, i2)].clone(stress)
