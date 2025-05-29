import os

from zmlx.io.load_col import load_col as loadcol
from zmlx.react.freeze import create as create_freeze


def create(gas, liq, fa_t, fa_c, t2q=None):
    """
    创建在低气压下（1kPa以内的量级，水的三相点附近），水的气体和水的液体之间的相变反应

    参考文献：Phase equilibria in the system CO2-H2O I: New equilibrium relations at low temperatures
    """
    fname = os.path.join(os.path.dirname(__file__), 'p2t_h2o_gas_liq.txt')
    vp = loadcol(fname, 0)
    vt = loadcol(fname, 1)
    return create_freeze(
        flu=gas, sol=liq,
        vp=vp, vt=vt,
        temp=273.15, heat=336000.0,
        fa_t=fa_t, fa_c=fa_c,
        t2q=t2q)


if __name__ == '__main__':
    print(create(0, 1, 0, 1))
