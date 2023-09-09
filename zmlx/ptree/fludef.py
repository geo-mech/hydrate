import os
from zml import Seepage
from zmlx.ptree.interp2 import interp2
from zmlx.ptree.ptree import PTree


def fludef(pt, den=None, vis=None, specific_heat=None, file=None):
    """
    利用配置文件载入/创建流体的定义. 注意，file后面的参数，是在读取file的时候所采用的默认值。如果file也定义了同样的参数，则
    最终使用file中定义的数值.
    """
    assert isinstance(pt, PTree)
    comp_n = pt(key='comp_n', default=0, doc='The number of components')
    if comp_n > 0:
        data = Seepage.FluDef()
        for i in range(comp_n):
            flu_i = fludef(pt=pt.child(key=f'comp{i}', doc=f'The setting of component {i}'),
                           den=den, vis=vis,
                           specific_heat=specific_heat, file=file)
            assert isinstance(flu_i, Seepage.FluDef)
            data.add_component(flu_i)
        return data

    file = pt(key='file', default=file if file is not None else '',
              doc='The file name of fluid. Will first try to import the pre-defined '
                  'fluid in zmlx.fluid. If not found, will then try to read the '
                  'fluid file (saved by Seepage.FluDef.save)')

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

    file = pt.find_file(filename=file)
    if isinstance(file, str):
        if os.path.isfile(file):
            try:
                return Seepage.FluDef(path=file)
            except:
                pass

    den = interp2(pt=pt.child(key='den', doc='The density data. be parsed as zml.Interp2'),
                  data=[1000.0] if den is None else den)
    assert den is not None

    vis = interp2(pt=pt.child(key='vis', doc='The viscosity data. be parsed as zml.Interp2'),
                  data=[1.0e-3] if vis is None else vis)
    assert vis is not None

    specific_heat = pt(key='specific_heat', default=4200.0 if specific_heat is None else specific_heat,
                       doc='the specific heat of the fluid')
    assert specific_heat > 0

    return Seepage.FluDef(den=den, vis=vis, specific_heat=specific_heat)


def fludefs(pt, den=None, vis=None, specific_heat=None, file=None, fluid_n=0):
    """
    创建多个流体定义
    """
    fluid_n = pt(key='fluid_n', default=fluid_n, doc='The count of fluids', cast=int)
    if fluid_n <= 0:
        return []

    fdefs = []
    for i in range(fluid_n):
        flu_i = fludef(pt=pt.child(key=f'fluid{i}', doc=f'The settings of the fluid {i}'),
                       den=den, vis=vis, specific_heat=specific_heat, file=file)
        assert isinstance(flu_i, Seepage.FluDef)
        fdefs.append(flu_i)
    return fdefs


def set_fludefs(model, pt, fluid_n=0, den=None, vis=None, specific_heat=None, file=None):
    """
    设置模型中的流体定义. 注意，此函数会首先清除模型中的已有的流体定义
    """
    assert isinstance(model, Seepage)
    model.clear_fludefs()
    fdefs = fludefs(pt=pt, den=den, vis=vis, specific_heat=specific_heat,
                    file=file, fluid_n=fluid_n)
    for f in fdefs:
        model.add_fludef(f)
