import os
from zml import Seepage, Interp2
from zmlx.io.json_ex import ConfigFile, get_child
from zmlx.io.intp2 import from_json as get_interp2


def from_json(json=None, den=None, vis=None, specific_heat=None, file=None):
    """
    利用配置文件载入/创建流体的定义. 注意，file后面的参数，是在读取file的时候所采用的默认值。如果file也定义了同样的参数，则
    最终使用file中定义的数值.
    """
    if json is not None:
        if not isinstance(json, ConfigFile):
            json = ConfigFile(json)

    if file is None:
        file = ''

    if json is not None:
        file = json(key='file', default=file,
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

    if json is not None:
        filepath = json.find_file(file)
        if filepath is not None:
            if os.path.isfile(filepath):
                try:
                    return Seepage.FluDef(path=filepath)
                except:
                    pass

    if den is None:
        den = 1000.0

    if vis is None:
        vis = 1.0e-3

    if specific_heat is None:
        specific_heat = 4200.0

    if json is not None:
        den = get_interp2(json=get_child(json, key='den', doc='The density data. be parsed as zml.Interp2'),
                          data=[den])
        assert isinstance(den, Interp2)

        vis = get_interp2(json=get_child(json, key='vis', doc='The viscosity data. be parsed as zml.Interp2'),
                          data=[vis])
        assert isinstance(vis, Interp2)

        specific_heat = json(key='specific_heat', default=specific_heat, doc='the specific heat of the fluid')
        assert specific_heat > 0

    return Seepage.FluDef(den=den, vis=vis, specific_heat=specific_heat)


def set_fludefs(model, json=None, fluid_n=0, den=None, vis=None, specific_heat=None):
    """
    设置模型中的流体定义. 注意，此函数会首先清除模型中的已有的流体定义
    """
    assert isinstance(model, Seepage)

    if json is not None:
        if not isinstance(json, ConfigFile):
            json = ConfigFile(json)

    model.clear_fludefs()

    if json is not None:
        fluid_n = json(key='fluid_n', default=fluid_n, doc='The count of fluids')

    if fluid_n <= 0:
        return

    for idx in range(fluid_n):
        if json is None:
            flu = from_json(den=den, vis=vis, specific_heat=specific_heat)
            assert isinstance(flu, Seepage.FluDef)
            model.add_fludef(flu)
            continue

        assert isinstance(json, ConfigFile)

        json_i = json.child(key=f'fluid_{idx}',
                            doc=f'The settings of the fluid {idx}')

        comp_n = json_i(key='comp_n', default=0,
                        doc='The count of the components for this fluid')

        if comp_n == 0:
            flu = from_json(json_i, den=den, vis=vis, specific_heat=specific_heat)
            assert isinstance(flu, Seepage.FluDef)
            model.add_fludef(flu)
        else:
            flu = Seepage.FluDef()
            for comp_i in range(comp_n):
                comp = from_json(json_i.child(f'comp_{comp_i}',
                                              doc=f'The settings of the component {comp_i}'),
                                 den=den, vis=vis, specific_heat=specific_heat)
                assert isinstance(comp, Seepage.FluDef)
                flu.add_component(comp)
            assert flu.component_number == comp_n
            model.add_fludef(flu)

    assert model.fludef_number == fluid_n
