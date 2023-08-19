from zmlx.filesys.path import *
from zml import Seepage
from zmlx.ptree.fludata import fludata
from zmlx.ptree.array import array
from zmlx.ptree.ptree import PTree
import warnings


def injector(pt, pos=None, radi=None, fluid_id=None, mass=0.0, den=1000.0, vis=1.0e-3, attrs=None,
             t2q=None, file=None, time=None, rate=None, g_heat=None, ca_mc=None, ca_t=None, save_to=None):
    """
    创建注入点.
    """
    assert isinstance(pt, PTree)
    data = Seepage.Injector()

    # 尝试从文件中读取数据
    file = pt.find_file(key='file', default=file if file is not None else '',
                        doc='The file where to load the injector')

    if isfile(file):
        try:
            data.load(file)
            return data
        except:
            pass

    pos = pt(key='pos', default=pos if pos is not None else [0, 0, 0],
             doc='The position in 3d')
    assert len(pos) == 3
    data.pos = pos

    time = pt(key='time', default=time)
    if time is not None:
        data.time = time

    rate = pt(key='rate', default=rate)
    if rate is not None:
        data.add_oper(-1.0e100, rate)

    data.radi = pt(key='radi',
                   default=radi if radi is not None else data.radi,
                   doc='The controlling radius')

    g_heat = pt(key='g_heat', default=g_heat)
    if g_heat is not None:
        data.g_heat = g_heat

    ca_mc = pt(key='ca_mc', default=ca_mc)
    if ca_mc is not None:
        data.ca_mc = ca_mc

    ca_t = pt(key='ca_t', default=ca_t)
    if ca_t is not None:
        data.ca_t = ca_t

    pt_flu = pt.child(key='flu', doc='The setting of fluid data')

    fluid_id = pt_flu(key='id',
                      default=fluid_id if fluid_id is not None else [],
                      doc='the fluid index')
    if 0 < len(fluid_id) <= 2:
        data.set_fid(fluid_id)

    flu = fludata(pt=pt_flu,
                  mass=mass, den=den, vis=vis, attrs=attrs)
    assert isinstance(flu, Seepage.FluData)
    data.flu.clone(flu)

    t2q = array(pt=pt.child(key='t2q', doc='The setting of t2q'),
                data=None if t2q is None else t2q)

    if t2q is not None:
        if len(t2q.flatten()) == 1:
            data.add_oper(0, t2q[0])
        else:
            for i in range(t2q.shape[0]):
                t = t2q[i, 0]
                q = t2q[i, 1]
                data.add_oper(t, q)

    save_to = pt(key='save_to', default=save_to)
    if save_to is not None:
        try:
            data.save(pt.opath(save_to))
        except:
            warnings.warn(f'can not save data to file: {save_to}')

    return data


def injectors(pt, pos=None, radi=None, fluid_id=None, mass=0.0, den=1000.0, vis=1.0e-3, attrs=None,
              t2q=None, file=None, time=None, rate=None, g_heat=None, ca_mc=None, ca_t=None, inj_n=0):
    assert isinstance(pt, PTree)
    inj_n = pt(key='inj_n', default=inj_n, doc='The count of injectors')
    injs = []
    for i in range(inj_n):
        data = injector(pt=pt.child(key=f'inj{i}', doc=f'The setting of inj {i}'),
                        pos=pos, radi=radi, fluid_id=fluid_id, mass=mass, den=den, vis=vis, attrs=attrs,
                        t2q=t2q, file=file, time=time, rate=rate, g_heat=g_heat, ca_mc=ca_mc, ca_t=ca_t)
        assert isinstance(data, Seepage.Injector)
        injs.append(data)
    return injs


def test():
    from zmlx.ptree.ptree import json_file
    from zmlx.filesys.opath import opath
    pt = json_file(opath('inj.json'))
    data = injector(pt)
    print(data)


if __name__ == '__main__':
    test()
