"""
定义流体
"""

from zmlx.fluid.h2o import create as create_h2o
from zmlx.fluid.solution import create_solute
from zmlx.tfc import Seepage


def _vapor():
    """
    水蒸气
    """
    return Seepage.FluDef(name='vapor', den=30.0, vis=1.0e-5)


def _he():
    # 修正：20MPa, 80℃ 下氦气真实密度约为 27 kg/m^3，粘度约为 2.2e-5 Pa·s
    return Seepage.FluDef(name='he', den=27.0, vis=2.2e-5)

def _n2():
    # 修正：20MPa, 80℃ 下氮气真实密度约为 195 kg/m^3，粘度约为 2.1e-5 Pa·s
    return Seepage.FluDef(name='n2', den=195.0, vis=2.1e-5)


def _h2o():
    return create_h2o(name='h2o')


def _he_sol(h2o):
    """
    作为溶质的氦气
    """
    return create_solute(solvent=h2o, c=0.01, den_times=1.0, vis_times=1.0, name='he_sol')


def _n2_sol(h2o):
    """
    作为溶质的氮气
    """
    return create_solute(solvent=h2o, c=0.01, den_times=1.0, vis_times=1.0, name='n2_sol')


def create_fludefs():
    """
    创建流体定义
    """
    gas = Seepage.FluDef.create(
        name='gas',
        defs=[_vapor(), _he(), _n2()]
    )
    h2o = _h2o()
    liq = Seepage.FluDef.create(
        name='liq',
        defs=[h2o, _he_sol(h2o), _n2_sol(h2o)]
    )
    return [gas, liq]
