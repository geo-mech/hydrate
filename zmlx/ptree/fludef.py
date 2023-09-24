import os

from zml import Seepage
from zmlx.ptree.interp2 import interp2
from zmlx.ptree.ptree import PTree


def fludef(pt):
    """
    利用配置文件载入/创建流体的定义
    """
    assert isinstance(pt, PTree)

    comp_n = pt('comp_n', doc='The number of components')
    if comp_n is not None:
        assert comp_n > 0
        data = Seepage.FluDef()
        for i in range(comp_n):
            flu_i = fludef(pt[f'comp{i}'])
            assert isinstance(flu_i, Seepage.FluDef)
            data.add_component(flu_i)
        return data

    if isinstance(pt.data, str):
        file = pt.data
        if file == '@c11h24':
            from zmlx.fluid.c11h24 import create
            return create()

        if file == '@ch4_lyx':
            from zmlx.fluid.ch4_lyx import create
            return create()

        if file == '@co2':
            from zmlx.fluid.co2 import create
            return create()

        if file == '@h2o_gas':
            from zmlx.fluid.h2o_gas import create
            return create()

        if file == '@ch4':
            from zmlx.fluid.ch4 import create
            return create()

        if file == '@ch4_hydrate':
            from zmlx.fluid.ch4_hydrate import create
            return create()

        if file == '@char':
            from zmlx.fluid.char import create
            return create()

        if file == '@co2_hydrate':
            from zmlx.fluid.co2_hydrate import create
            return create()

        if file == '@h2o':
            from zmlx.fluid.h2o import create
            return create()

        if file == '@h2o_ice':
            from zmlx.fluid.h2o_ice import create
            return create()

        if file == '@kerogen':
            from zmlx.fluid.kerogen import create
            return create()

        if file == '@oil':
            from zmlx.fluid.oil import create
            return create()

        file = pt.find(file)
        if isinstance(file, str):
            if os.path.isfile(file):
                try:
                    return Seepage.FluDef(path=file)
                except:
                    pass

    # 下面创建一个自定义的数据.
    data = Seepage.FluDef()

    den = interp2(pt['den'])
    if den is not None:
        data.den = den

    vis = interp2(pt['vis'])
    if vis is not None:
        data.vis = vis

    specific_heat = pt('specific_heat', doc='the specific heat of the fluid')
    if specific_heat is not None:
        data.specific_heat = specific_heat

    return data


def fludefs(pt):
    """
    创建多个流体定义
    """
    fluid_n = pt('fluid_n', doc='The count of fluids', cast=int)
    if fluid_n is None:
        return []

    assert fluid_n > 0
    fdefs = []
    for i in range(fluid_n):
        flu_i = fludef(pt[f'fluid{i}'])
        assert isinstance(flu_i, Seepage.FluDef)
        fdefs.append(flu_i)
    return fdefs


def set_fludefs(model, pt):
    """
    设置模型中的流体定义. 注意，此函数会首先清除模型中的已有的流体定义
    """
    assert isinstance(model, Seepage)
    model.clear_fludefs()
    fdefs = fludefs(pt)
    for f in fdefs:
        model.add_fludef(f)


def test():
    pt = PTree()
    data = fludef(pt)
    print(data)


if __name__ == '__main__':
    test()
