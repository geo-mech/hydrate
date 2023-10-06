import os

from zml import Seepage
from zmlx.ptree.interp2 import interp2
from zmlx.ptree.ptree import PTree, as_ptree


def fludef(pt):
    """
    利用配置文件载入/创建流体的定义
    """
    if not isinstance(pt, PTree):
        pt = as_ptree(pt)

    data = pt.data

    if isinstance(data, list):
        f_def = Seepage.FluDef()
        for item in data:
            f_def.add_component(fludef(as_ptree(item, pt.path)))
        return f_def

    if isinstance(data, str):
        if data == '@c11h24':
            from zmlx.fluid.c11h24 import create
            return create()

        if data == '@ch4_lyx':
            from zmlx.fluid.ch4_lyx import create
            return create()

        if data == '@co2':
            from zmlx.fluid.co2 import create
            return create()

        if data == '@h2o_gas':
            from zmlx.fluid.h2o_gas import create
            return create()

        if data == '@ch4':
            from zmlx.fluid.ch4 import create
            return create()

        if data == '@ch4_hydrate':
            from zmlx.fluid.ch4_hydrate import create
            return create()

        if data == '@char':
            from zmlx.fluid.char import create
            return create()

        if data == '@co2_hydrate':
            from zmlx.fluid.co2_hydrate import create
            return create()

        if data == '@h2o':
            from zmlx.fluid.h2o import create
            return create()

        if data == '@h2o_ice':
            from zmlx.fluid.h2o_ice import create
            return create()

        if data == '@kerogen':
            from zmlx.fluid.kerogen import create
            return create()

        if data == '@oil':
            from zmlx.fluid.oil import create
            return create()

        fname = pt.find(data)
        if isinstance(fname, str):
            if os.path.isfile(fname):
                try:
                    return Seepage.FluDef(path=fname)
                except:
                    pass

    assert isinstance(data, dict)
    # 下面创建一个自定义的数据.
    f_def = Seepage.FluDef()

    den = interp2(pt['den'])
    if den is not None:
        f_def.den = den
    else:
        f_def.den.clear()    # 删除

    vis = interp2(pt['vis'])
    if vis is not None:
        f_def.vis = vis
    else:
        f_def.vis.clear()    # 删除

    specific_heat = pt('specific_heat', doc='the specific heat of the fluid')
    if specific_heat is not None:
        f_def.specific_heat = specific_heat

    return f_def


def fludefs(pt):
    """
    创建多个流体定义
    """
    assert isinstance(pt.data, list)
    f_defs = []
    for item in pt.data:
        f_defs.append(fludef(as_ptree(item, pt.path)))
    return f_defs


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
