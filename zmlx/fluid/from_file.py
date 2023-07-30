import os

from zml import Seepage, Interp2
from zmlx.interp.dim2 import from_file as get_interp2
from zmlx.io.json import ConfigFile


def from_file(file=None, den=None, vis=None, specific_heat=None, filename=None):
    """
    利用配置文件载入/创建流体的定义. 注意，file后面的参数，是在读取file的时候所采用的默认值。如果file也定义了同样的参数，则
    最终使用file中定义的数值.
    """
    if file is not None:
        if not isinstance(file, ConfigFile):
            file = ConfigFile(file)

    if filename is None:
        filename = ''

    if file is not None:
        filename = file(key='filename', default=filename,
                        doc='The file name of fluid. Will first try to import the pre-defined '
                            'fluid in zmlx.fluid. If not found, will then try to read the '
                            'fluid file (saved by Seepage.FluDef.save)')

    if filename == '@c11h24':
        from zmlx.fluid.c11h24 import create
        return create()

    if filename == '@ch4_lyx':
        from zmlx.fluid.ch4_lyx import create
        return create()

    if filename == '@co2':
        from zmlx.fluid.co2 import create
        return create()

    if filename == '@h2o_gas':
        from zmlx.fluid.h2o_gas import create
        return create()

    if filename == '@ch4':
        from zmlx.fluid.ch4 import create
        return create()

    if filename == '@ch4_hydrate':
        from zmlx.fluid.ch4_hydrate import create
        return create()

    if filename == '@char':
        from zmlx.fluid.char import create
        return create()

    if filename == '@co2_hydrate':
        from zmlx.fluid.co2_hydrate import create
        return create()

    if filename == '@h2o':
        from zmlx.fluid.h2o import create
        return create()

    if filename == '@h2o_ice':
        from zmlx.fluid.h2o_ice import create
        return create()

    if filename == '@kerogen':
        from zmlx.fluid.kerogen import create
        return create()

    if filename == '@oil':
        from zmlx.fluid.oil import create
        return create()

    if file is not None:
        filepath = file.find_file(filename)
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

    if file is not None:
        den = get_interp2(file=file.child(key='den', doc='The density data. be parsed as zml.Interp2'),
                          data=[den])
        assert isinstance(den, Interp2)

        vis = get_interp2(file=file.child(key='vis', doc='The viscosity data. be parsed as zml.Interp2'),
                          data=[vis])
        assert isinstance(vis, Interp2)

        specific_heat = file(key='specific_heat', default=specific_heat, doc='the specific heat of the fluid')
        assert specific_heat > 0

    return Seepage.FluDef(den=den, vis=vis, specific_heat=specific_heat)


if __name__ == '__main__':
    from zmlx.filesys.opath import opath

    f = from_file(opath('fluid.json'))
    f.save(opath('fluid.xml'))
