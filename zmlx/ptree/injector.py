from zml import Seepage
from zmlx.filesys.path import *
from zmlx.ptree.array import array
from zmlx.ptree.fludata import fludata
from zmlx.ptree.ptree import PTree, as_ptree


def injector(pt):
    """
    创建注入点.
    """
    assert isinstance(pt, PTree)

    if isinstance(pt.data, str):
        file = pt.find(pt.data)
        if exists(file):
            return Seepage.Injector(path=file)

    data = Seepage.Injector()

    pos = pt('pos', doc='The position in 3d. (a list)')
    if pos is not None:
        data.pos = pos

    time = pt('time', doc='The current time')
    if time is not None:
        data.time = time

    rate = pt('rate', doc='The current rate')
    if rate is not None:
        data.add_oper(-1.0e100, rate)

    radi = pt('radi', doc='The controlling radius [m]')
    if radi is not None:
        data.radi = radi

    g_heat = pt('g_heat')
    if g_heat is not None:
        data.g_heat = g_heat

    ca_mc = pt('ca_mc')
    if ca_mc is not None:
        data.ca_mc = ca_mc

    ca_t = pt('ca_t')
    if ca_t is not None:
        data.ca_t = ca_t

    fluid_id = pt('fluid_id')
    if fluid_id is not None:
        data.set_fid(fluid_id)

    flu = fludata(pt['flu'])
    assert isinstance(flu, Seepage.FluData)
    data.flu.clone(flu)

    t2q = array(pt['t2q'])

    if t2q is not None:
        if len(t2q.flatten()) == 1:
            data.add_oper(0, t2q[0])
        else:
            for i in range(t2q.shape[0]):
                t = t2q[i, 0]
                q = t2q[i, 1]
                data.add_oper(t, q)

    return data


def injectors(pt):
    assert isinstance(pt, PTree)
    assert isinstance(pt.data, list)
    injs = []
    for item in pt.data:
        data = injector(as_ptree(item, pt.path))
        assert isinstance(data, Seepage.Injector)
        injs.append(data)
    return injs
