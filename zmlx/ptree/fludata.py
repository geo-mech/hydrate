from zml import Seepage
from zmlx.filesys.path import *
from zmlx.ptree.ptree import PTree


def fludata(pt):
    """
    从json来创建流体数据
    """
    assert isinstance(pt, PTree)

    comp_n = pt('comp_n', doc='The count of component')
    if comp_n is not None:
        assert comp_n > 0
        data = Seepage.FluData()
        for i in range(comp_n):
            comp = fludata(pt[f'comp{i}'])
            assert isinstance(comp, Seepage.FluData)
            data.add_component(comp)
        return data

    if isinstance(pt.data, str):
        fname = pt.find(pt.data)
        if isfile(fname):
            try:
                data = Seepage.FluData()
                data.load(fname)
                return data
            except:
                pass

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


def test():
    pt = PTree()
    data = fludata(pt)
    print(data)


if __name__ == '__main__':
    test()
