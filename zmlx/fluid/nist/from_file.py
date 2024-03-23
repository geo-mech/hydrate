import numpy as np

from zml import Interp2, Seepage
from zmlx.utility.Interp2 import Interp2 as Interpolator


def from_file(fname, t_min=None, t_max=None, p_min=None, p_max=None, name=None, specific_heat=None):
    """
    创建液态co2的定义.
    """
    data = np.loadtxt(fname=fname)

    if t_min is None:
        t_min = np.min(data[:, 0])
    if t_max is None:
        t_max = np.max(data[:, 0])
    assert t_min <= t_max

    if p_min is None:
        p_min = np.min(data[:, 1])
    if p_max is None:
        p_max = np.max(data[:, 1])
    assert p_min <= p_max

    den = Interpolator(data[:, 0], data[:, 1], data[:, 2], rescale=True)
    vis = Interpolator(data[:, 0], data[:, 1], data[:, 3], rescale=True)

    def gas_den(P, T):
        assert t_min <= T <= t_max
        assert p_min <= P <= p_max
        return den(T, P)

    def gas_vis(P, T):
        assert t_min <= T <= t_max
        assert p_min <= P <= p_max
        return vis(T, P)

    def create_density():
        itp = Interp2()
        itp.create(p_min, 1e6, p_max, t_min, 1, t_max, gas_den)
        return itp

    def create_viscosity():
        itp = Interp2()
        itp.create(p_min, 1e6, p_max, t_min, 1, t_max, gas_vis)
        return itp

    if specific_heat is None:
        specific_heat = 2000.0

    return Seepage.FluDef(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat,
                          name=name)
