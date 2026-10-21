from zmlx.exts import FluDef
from zmlx.fluids import c11h24
from zmlx.fluids import char
from zmlx.fluids import kerogen
from zmlx.fluids import oil
from zmlx.fluids.ch4 import create as create_ch4
from zmlx.fluids.h2o import create as create_h2o
from zmlx.fluids.h2o_gas import create as create_steam


def create_fludefs():
    """
    创建流体定义.
        0. gas: ch4, steam
        1. h2o
        2. lo = light oil
        3. ho = heavy oil
        4. solid: kg = kerogen, char
    """
    gas = FluDef.create(
        name='gas',
        defs=[create_ch4(name='ch4'),
              create_steam(name='steam')])
    h2o = create_h2o(name='h2o')
    lo = c11h24.create(name='lo')
    ho = oil.create(name='ho')
    sol = FluDef.create(
        name='sol',
        defs=[kerogen.create(name='kg'),
              char.create(den=1800.0, name='char')])
    # 返回定义
    return [gas, h2o, lo, ho, sol]
