import warnings
import numpy as np
from zmlx.io.json_ex import ConfigFile, get_child
from zml import Seepage
from zmlx.io.fludata import from_json as fludata
from zmlx.io.array import from_json as array


def from_json(json=None, pos=None, radi=-1.0, fluid_id=None, mass=0.0, den=1000.0, vis=1.0e-3, attrs=None,
              opers=None):
    """
    创建注入点.
    """
    if json is not None:
        if not isinstance(json, ConfigFile):
            json = ConfigFile(json)

    data = Seepage.Injector()

    if pos is None:
        pos = []

    if json is not None:
        pos = json('pos', default=pos, doc='The position in 3d')

    if len(pos) == 3:
        data.pos = pos
    else:
        warnings.warn('The position should be in 3d')

    if json is not None:
        radi = json('radi', default=radi, doc='The controlling radius')

    if radi > 0:
        data.radi = radi

    if fluid_id is None:
        fluid_id = []

    if json is not None:
        fluid_id = json('fluid_id', default=fluid_id, doc='the fluid index')

    if 0 < len(fluid_id) <= 2:
        data.set_fid(fluid_id)
    else:
        warnings.warn('The length of fluid id should be 1 or 2')

    flu = fludata(json=get_child(json, 'fludata', doc='The setting of fluid data'),
                  mass=mass, den=den, vis=vis, attrs=attrs)
    assert isinstance(flu, Seepage.FluData)

    data.flu.clone(flu)

    if json is not None:
        opers = array(json=get_child(json, key='opers', doc='The setting of opers'),
                      data=None if opers is None else opers)
    else:
        if opers is not None:
            opers = np.array(opers)

    if opers is not None:
        if len(opers.flatten()) == 1:
            data.add_oper(0, opers[0])
        else:
            for i in range(opers.shape[0]):
                t = opers[i, 0]
                q = opers[i, 1]
                data.add_oper(t, q)

    return data


def add_injector(model, **kwargs):
    """
    在模型中添加一个注入点
    """
    assert isinstance(model, Seepage)
    inj = from_json(**kwargs)
    assert isinstance(inj, Seepage.Injector)
    model.add_injector(data=inj)
