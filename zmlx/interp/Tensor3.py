import os.path
from scipy.interpolate import NearestNDInterpolator
import numpy as np
import zml
from zmlx.io.json import ConfigFile
from io import StringIO


class Interp3:
    """
    关于三阶张量的三维插值. 使用NearestNDInterpolator的这种插值的方式
    """

    def __init__(self, fname=None):
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
        self.create(fname)

    def create(self, fname):
        """
        读取数据，创建插值. 数据格式:
            x  y  z  hmax  hmin  angl  vert

        或者如果只有一行数据，则格式为：
            hmax  hmin  angl  vert
        """
        data = np.loadtxt(fname)
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
            self.hmax = zml.Field.Constant(data[0])
            self.hmin = zml.Field.Constant(data[1])
            self.angl = zml.Field.Constant(data[2])
            self.vert = zml.Field.Constant(data[3])

    def __call__(self, x, y, z):
        """
        返回给定位置的张量
        """
        hmax = self.hmax(x, y, z)
        hmin = self.hmin(x, y, z)
        angl = self.angl(x, y, z)
        vert = self.vert(x, y, z)
        ts2 = zml.Tensor2.create(hmax, hmin, angl)
        return zml.Tensor3(xx=ts2.xx, yy=ts2.yy, zz=vert, xy=ts2.xy, yz=0, zx=0)


def from_config(config, default_name=None, default_text=None):
    """
    根据参数配置文件来创建一个张量场
    """
    if not isinstance(config, ConfigFile):
        config = ConfigFile(config)

    assert isinstance(config, ConfigFile)

    if default_name is None:
        default_name = ''
    # 尝试从文件中读取数据
    name = config.as_path('filename', default=default_name,
                          doc='first, try to read file. format: [x  y  z  hmax  hmin  angl  vert]')

    if name is not None:
        if os.path.isfile(name):
            return Interp3(fname=name)

    # 尝试直接读取
    if default_text is None:
        default_text = "0 0 0 0"

    text = config.get('text', default=default_text,
                      doc='use when name is not a file. format: [hmax  hmin  angl  vert]')

    return Interp3(fname=StringIO(text))


def test_1():
    f = Interp3(StringIO("""
    0 0 0 5 6 7 8
    1 1 1 9 9 9 9
    """))
    print(f(0, 0, 0))
    print(f(1, 1, 2))


def test_2():
    f = Interp3(StringIO("""
    5 6 7 8
    """))
    print(f(0, 0, 0))
    print(f(1, 1, 2))


if __name__ == '__main__':
    test_2()
