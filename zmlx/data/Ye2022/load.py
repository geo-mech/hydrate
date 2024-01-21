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
    return Adaptor(t2pre=load_('pressure_prod.txt'),
                   t2pre_smooth=load_('pressure_prod_smooth.txt'),
                   t2rate=load_('prod_rate_gas.txt'),
                   z2ki=load_('perm_ini.txt'),
                   z2k0=load_('perm.txt'),
                   z2k0_smooth=load_('perm_smooth.txt'),
                   z2porosity=load_('porosity.txt'),
                   z2porosity_smooth=load_('porosity_smooth.txt'),
                   z2s=load_('sat_hyd.txt'),
                   z2s_smooth=load_('sat_hyd_smooth.txt'), )


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
