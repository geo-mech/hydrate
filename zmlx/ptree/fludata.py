from zml import Seepage
from zmlx.alg.fsys import *
from zmlx.ptree.ptree import PTree, as_ptree


def fludata(pt):
    """
    从json来创建流体数据
    """
    assert isinstance(pt, PTree)

    if isinstance(pt.data, str):  # 读取文件
        fname = pt.find(pt.data)
        if isfile(fname):
            data = Seepage.FluData()
            data.load(fname)
            return data
        else:
            return None

    if isinstance(pt.data, list):  # 各个组分
        data = Seepage.FluData()
        for item in pt.data:
            comp = fludata(as_ptree(item, path=pt.path))
            assert isinstance(comp, Seepage.FluData)
            data.add_component(comp)
        return data

    # 构建一个数据体
    data = Seepage.FluData()

    mass = pt('mass', doc='The mass of fluid [kg] ')
    if mass is not None:
        data.mass = mass

    den = pt('den', doc='The density of fluid [kg/m^3]')
    if den is not None:
        data.den = den

    vis = pt('vis', doc='The viscosity of fluid [Pa.s]')
    if vis is not None:
        data.vis = vis

    attrs = pt('attrs', doc='The attributions (a list)')
    if isinstance(attrs, list):
        for i in range(len(attrs)):
            data.set_attr(i, attrs[i])

    # 返回数据
    return data
