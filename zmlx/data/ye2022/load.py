import os
import numpy as np

folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'raw')


class Adaptor:
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


def path(name):
    return os.path.join(folder, name)


def load_(name):
    return np.loadtxt(path(name))


def load():
    return Adaptor(t2pre=load_('生产压力.txt'),
                   t2pre_smooth=load_('生产压力_smooth.txt'),
                   t2rate=load_('产气速率.txt'),
                   z2ki=load_('初始渗透率.txt'),
                   z2k0=load_('绝对渗透率.txt'),
                   z2k0_smooth=load_('绝对渗透率_smooth.txt'),
                   z2porosity=load_('孔隙度.txt'),
                   z2porosity_smooth=load_('孔隙度_smooth.txt'),
                   z2s=load_('水合物饱和度.txt'),
                   z2s_smooth=load_('水合物饱和度_smooth.txt'), )


def load_120():
    # 总共包含120深度的数据
    data120 = load()

    def modify_z(d):
        d[:, 0] -= 10
        d[0, 0] = 0
        d[-1, 0] = -120

    modify_z(data120.z2ki)
    modify_z(data120.z2k0)
    modify_z(data120.z2k0_smooth)
    modify_z(data120.z2porosity)
    modify_z(data120.z2porosity_smooth)
    modify_z(data120.z2s)
    modify_z(data120.z2s_smooth)
    return data120
