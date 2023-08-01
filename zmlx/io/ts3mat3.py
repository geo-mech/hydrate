from scipy.interpolate import NearestNDInterpolator
from zml import *
from zmlx.io.json_ex import ConfigFile
from zmlx.io.array import from_json as get_array


class Ts3Interp3:
    """
    关于三阶张量的三维插值. 使用NearestNDInterpolator的这种插值的方式
    """

    def __init__(self, data=None):
        """
        初始化.           数据格式:
            x  y  z  hmax  hmin  angl  vert

        或者如果只有一行数据，则格式为：
            hmax  hmin  angl  vert
        """
        self.hmax = None
        self.hmin = None
        self.angl = None
        self.vert = None
        self.create(data)

    def create(self, data):
        """
        读取数据，创建插值. 数据格式:
            x  y  z  hmax  hmin  angl  vert

        或者如果只有一行数据，则格式为：
            hmax  hmin  angl  vert
        """
        if data is None:
            return
        if len(data.shape) == 2:
            assert data.shape[0] >= 1, f'shape = {data.shape}'
            assert data.shape[1] >= 7, f'shape = {data.shape}'
            self.hmax = NearestNDInterpolator(x=data[:, 0: 3], y=data[:, 3])
            self.hmin = NearestNDInterpolator(x=data[:, 0: 3], y=data[:, 4])
            self.angl = NearestNDInterpolator(x=data[:, 0: 3], y=data[:, 5])
            self.vert = NearestNDInterpolator(x=data[:, 0: 3], y=data[:, 6])
        else:
            assert len(data.shape) == 1, f'shape = {data.shape}'
            assert len(data) == 4
            self.hmax = Field.Constant(data[0])
            self.hmin = Field.Constant(data[1])
            self.angl = Field.Constant(data[2])
            self.vert = Field.Constant(data[3])

    def __call__(self, x, y, z):
        """
        返回给定位置的张量
        """
        hmax = self.hmax(x, y, z)
        hmin = self.hmin(x, y, z)
        angl = self.angl(x, y, z)
        vert = self.vert(x, y, z)
        ts2 = Tensor2.create(hmax, hmin, angl)
        return Tensor3(xx=ts2.xx, yy=ts2.yy, zz=vert, xy=ts2.xy, yz=0, zx=0)


def get_ts3intp3(json=None, data=None, file=None, text=None):
    """
    根据参数配置文件来创建一个张量场
    """
    if text is None:
        text = "0 0 0 0"
    data = get_array(json=json, data=data, text=text, file=file)
    return Ts3Interp3(data)


def from_json(json=None, box=None, shape=None, interp=None, data=None, text=None, file=None, buffer=None):
    """
    设置张量场。注意，如果file有定义，则最终使用file定义的数值
    """
    if not isinstance(buffer, Tensor3Matrix3):
        buffer = Tensor3Matrix3()

    if json is not None:
        if not isinstance(json, ConfigFile):
            json = ConfigFile(json)

    if interp is None:
        interp = get_ts3intp3(json=json, data=data, text=text, file=file)

    if not isinstance(interp, Ts3Interp3):
        warnings.warn('can not set buffer without given interp as Ts3Interp3')
        return buffer

    if shape is None:
        shape = [2, 2, 2]

    if json is not None:
        shape = json(key='shape', default=shape,
                     doc='The grid number along dimension each dimension [jx, jy, jz]')

    # 检查数据的范围.
    assert shape is not None
    assert len(shape) == 3
    assert shape[0] >= 1 and shape[1] >= 1 and shape[2] >= 1
    assert shape[0] < 1000 and shape[1] < 1000 and shape[2] < 1000

    buffer.size = shape

    if box is None:
        box = [0, 0, 0, 1, 1, 1]

    if json is not None:
        box = json(key='box', default=box,
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
                buffer[(i0, i1, i2)].clone(stress)

    return buffer
