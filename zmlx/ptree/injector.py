from zmlx.filesys.path import *
from zml import Seepage
from zmlx.ptree.fludata import fludata
from zmlx.ptree.array import array
from zmlx.ptree.ptree import PTree


def injector(pt, pos=None, radi=None, fluid_id=None, mass=0.0, den=1000.0, vis=1.0e-3, attrs=None,
             t2q=None, file=None):
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

    pos = pt('pos', default=pos if pos is not None else [0, 0, 0],
             doc='The position in 3d')
    assert len(pos) == 3
    data.pos = pos

    data.radi = pt(key='radi',
                   default=radi if radi is not None else data.radi,
                   doc='The controlling radius')

    fluid_id = pt(key='fluid_id',
                  default=fluid_id if fluid_id is not None else [],
                  doc='the fluid index')
    assert 0 < len(fluid_id) <= 2
    data.set_fid(fluid_id)

    flu = fludata(pt=pt.child('fludata', doc='The setting of fluid data'),
                  mass=mass, den=den, vis=vis, attrs=attrs)
    assert isinstance(flu, Seepage.FluData)
    data.flu.clone(flu)

    t2q = array(pt=pt.child(key='t2q', doc='The setting of t2q'),
                data=None if t2q is None else t2q)

    if len(t2q.flatten()) == 1:
        data.add_oper(0, t2q[0])
    else:
        for i in range(t2q.shape[0]):
            t = t2q[i, 0]
            q = t2q[i, 1]
            data.add_oper(t, q)

    return data

