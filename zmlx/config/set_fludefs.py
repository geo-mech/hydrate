from zml import Seepage
from zmlx.fluid.from_file import from_file as get_flu
from zmlx.io.json import ConfigFile


def set_fludefs(model, file=None, fluid_n=0, den=None, vis=None, specific_heat=None):
    """
    设置模型中的流体定义. 注意，此函数会首先清除模型中的已有的流体定义
    """
    assert isinstance(model, Seepage)

    if file is not None:
        if not isinstance(file, ConfigFile):
            file = ConfigFile(file)

    model.clear_fludefs()

    if file is not None:
        fluid_n = file(key='fluid_n', default=fluid_n, doc='The count of fluids')

    if fluid_n <= 0:
        return

    for idx in range(fluid_n):
        if file is None:
            flu = get_flu(den=den, vis=vis, specific_heat=specific_heat)
            assert isinstance(flu, Seepage.FluDef)
            model.add_fludef(flu)
            continue

        assert isinstance(file, ConfigFile)

        file_i = file.child(key=f'fluid_{idx}',
                            doc=f'The settings of the fluid {idx}')

        comp_n = file_i(key='comp_n', default=0,
                        doc='The count of the components for this fluid')

        if comp_n == 0:
            flu = get_flu(file_i, den=den, vis=vis, specific_heat=specific_heat)
            assert isinstance(flu, Seepage.FluDef)
            model.add_fludef(flu)
        else:
            flu = Seepage.FluDef()
            for comp_i in range(comp_n):
                comp = get_flu(file_i.child(f'comp_{comp_i}',
                                            doc=f'The settings of the component {comp_i}'),
                               den=den, vis=vis, specific_heat=specific_heat)
                assert isinstance(comp, Seepage.FluDef)
                flu.add_component(comp)
            assert flu.component_number == comp_n
            model.add_fludef(flu)

    assert model.fludef_number == fluid_n


def test():
    from zmlx.filesys.opath import opath
    model = Seepage()
    set_fludefs(model, file=opath('fdefs.json'))
    model.save(opath('model.xml'))


if __name__ == '__main__':
    test()
