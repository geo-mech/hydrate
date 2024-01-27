import os

from zml import Seepage
from zmlx.ptree.interp2 import interp2
from zmlx.ptree.ptree import PTree, as_ptree


def _from_text(text, find=None, name=None):
    """
    尝试使用预定义的流体
    """
    if text is None:
        return

    if text == '@c11h24':
        from zmlx.fluid.c11h24 import create
        return create(name=name)

    if text == '@ch4_lyx':
        from zmlx.fluid.ch4_lyx import create
        return create(name=name)

    if text == '@co2':
        from zmlx.fluid.co2 import create
        return create(name=name)

    if text == '@h2o_gas':
        from zmlx.fluid.h2o_gas import create
        return create(name=name)

    if text == '@ch4':
        from zmlx.fluid.ch4 import create
        return create(name=name)

    if text == '@ch4_hydrate':
        from zmlx.fluid.ch4_hydrate import create
        return create(name=name)

    if text == '@char':
        from zmlx.fluid.char import create
        return create(name=name)

    if text == '@co2_hydrate':
        from zmlx.fluid.co2_hydrate import create
        return create(name=name)

    if text == '@h2o':
        from zmlx.fluid.h2o import create
        return create(name=name)

    if text == '@h2o_ice':
        from zmlx.fluid.h2o_ice import create
        return create(name=name)

    if text == '@kerogen':
        from zmlx.fluid.kerogen import create
        return create(name=name)

    if text == '@oil':
        from zmlx.fluid.oil import create
        return create(name=name)

    if find is not None:
        fname = find(text)
        if isinstance(fname, str):
            if os.path.isfile(fname):
                try:
                    return Seepage.FluDef(path=fname, name=name)
                except:
                    pass


def _from_list(data, path, name=None):
    if data is None:
        return
    f_def = Seepage.FluDef(name=name)
    for item in data:
        f_def.add_component(fludef(as_ptree(item, path)))
    return f_def


def fludef(pt):
    """
    利用配置文件载入/创建流体的定义
    """
    if not isinstance(pt, PTree):
        pt = as_ptree(pt)

    data = pt.data

    if isinstance(data, str):  # 此时，使用预定义的流体
        return _from_text(data, pt.find, name=None)

    if isinstance(data, list):  # 此时，创建一个多组分的流体(无法定义name)
        return _from_list(data, pt.path, name=None)

    if isinstance(data, dict):  # 下面创建一个自定义的数据 (默认不包含密度和粘性数据)
        name = pt('name', doc='The fluid name')

        # 尝试预定义的或者是从文件读取
        f_def = _from_text(pt('text', doc='filename or pre-defined fluid name'), pt.find, name=name)
        if f_def is not None:
            return f_def

        # 尝试多组分
        f_def = _from_list(pt('comp', doc='The components'), pt.path, name=name)
        if f_def is not None:
            return f_def

        # 尝试创建并自定义
        f_def = Seepage.FluDef(den=interp2(pt['den']), vis=interp2(pt['vis']), name=name)

        specific_heat = pt('specific_heat', doc='the specific heat of the fluid')
        if specific_heat is not None:
            f_def.specific_heat = specific_heat

        # 返回创建的定义
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
