from zml import Seepage
from zmlx.fluid import c11h24
from zmlx.fluid import char
from zmlx.fluid import kerogen
from zmlx.fluid import oil
from zmlx.fluid.ch4 import create as create_ch4
from zmlx.fluid.h2o import create as create_h2o
from zmlx.fluid.h2o_gas import create as create_steam


def create_fludefs():
    """
    创建流体定义.
        0. gas: ch4, steam
        1. h2o
        2. lo = light oil
        3. ho = heavy oil
        4. solid: kg = kerogen, char
    """
    gas = Seepage.FluDef.create(name='gas',
                                defs=[create_ch4(name='ch4'), create_steam(name='steam')])
    h2o = create_h2o(name='h2o')
    lo = c11h24.create(name='lo')
    ho = oil.create(name='ho')
    sol = Seepage.FluDef.create(name='sol',
                                defs=[kerogen.create(name='kg'),
                                      char.create(den=1800.0, name='char')])
    # 返回定义
    return [gas, h2o, lo, ho, sol]

