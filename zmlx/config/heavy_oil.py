from zml import *
from zmlx.fluid.kerogen import create as create_kerogen
from zmlx.fluid.oil import create as create_heavy_oil
from zmlx.fluid.c11h24 import create as create_light_oil
from zmlx.fluid.char import create as create_char
from zmlx.fluid.ch4 import create as create_ch4
from zmlx.fluid.h2o import create as create_h2o
from zmlx.fluid.h2o_gas import create as create_h2o_gas
from zmlx.kr.create_krf import create_krf
from zmlx.react import decomposition
from zmlx.react import vapor as vapor_react
from zmlx.config.TherFlowConfig import TherFlowConfig


def create():
    """
    Create a configuration for problem of insitu upgrading of kerogen and heavy oil. The phases include:

    phase 0:
        [Ch4, H2o_Steam],

    phase 1:
        [H2o]

    phase 2:
        [light_oil]

    phase 3:
        [heavy_oil]

    phase 4：
        [Kerogen, Char]

    The reactions inlcude:
        1. The decomposition of Kerogen
        2. The decompositon of Heavy oil
        3. The reaction between h2o and h2o_steam
    iweights were adapted from Robert Braun and Alan Burnham: DOI:10.2172/10169154,
    The kinetic reaction from Lee at al, 2016 https://doi.org/10.2118/173299-PA
    """
    config = TherFlowConfig()

    # define gas
    config.igas = config.add_fluid([create_ch4(), create_h2o_gas()])
    config.components['gas'] = config.igas
    config.components['ch4'] = [config.igas, 0]
    config.components['h2o_gas'] = [config.igas, 1]

    # water
    config.iwat = config.add_fluid(create_h2o())
    config.components['h2o'] = config.iwat

    # light oil
    config.ilight_oil = config.add_fluid(create_light_oil())
    config.components['light_oil'] = config.ilight_oil

    # heavy oil
    config.iheavy_oil = config.add_fluid(create_heavy_oil())
    config.components['heavy_oil'] = config.iheavy_oil

    # solid phase
    config.isol = config.add_fluid([create_kerogen(), create_char(den=1800)])
    config.components['sol'] = config.isol
    config.components['kerogen'] = [config.isol, 0]
    config.components['char'] = [config.isol, 1]

    # h2o and steam
    config.reactions.append(
        vapor_react.create(
            vap=config.components['h2o_gas'],
            wat=config.components['h2o'],
            fa_t=config.flu_keys['temperature'],
            fa_c=config.flu_keys['specific_heat']))

    # The decomposition of Kerogen.
    config.reactions.append(
        decomposition.create(left=config.components['kerogen'], right=[(config.components['heavy_oil'], 0.6),
                                                                       (config.components['light_oil'], 0.1),
                                                                       (config.components['h2o'], 0.1),
                                                                       (config.components['ch4'], 0.1),
                                                                       (config.components['char'], 0.1),
                                                                       ],
                             temp=565, heat=161600.0,  # From Maryelin 2023-02-23
                             rate=1.0e-8,
                             fa_t=config.flu_keys['temperature'],
                             fa_c=config.flu_keys['specific_heat']))

    # The decomposition of Heavy oil
    r = decomposition.create(left=config.components['heavy_oil'], right=[(config.components['light_oil'], 0.5),
                                                                         (config.components['ch4'], 0.2),
                                                                         (config.components['char'], 0.3),
                                                                         ],
                             temp=603, heat=206034.0,  # From Maryelin 2023-02-23
                             rate=1.0e-8,
                             fa_t=config.flu_keys['temperature'],
                             fa_c=config.flu_keys['specific_heat'])
    r.add_inhibitor(sol=config.components['sol'],
                    liq=None,
                    c=[0, 0.8, 1.0],
                    t=[0, 0, 1.0e4],  # 当固体占据的比重达到80%之后，增加裂解温度，从而限制继续分解
                    )
    config.reactions.append(r)

    # 残余饱和度设置为0，确保任何时候，都可以有导流能力
    config.krf = create_krf(0, 2, as_interp=True)

    return config


if __name__ == '__main__':
    c = create()
    print(c.components)
