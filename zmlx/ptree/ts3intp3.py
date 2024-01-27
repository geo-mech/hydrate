from scipy.interpolate import NearestNDInterpolator

from zml import Tensor2, Tensor3
from zmlx.ptree.array import array
from zmlx.utility.Field import Field


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


def get_ts3intp3(pt):
    """
    根据参数配置文件来创建一个张量场
    """
    data = array(pt)
    return Ts3Interp3(data)
