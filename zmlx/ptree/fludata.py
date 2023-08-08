from zml import Seepage
from zmlx.ptree.ptree import PTree
from zmlx.filesys.path import *


def fludata(pt, mass=0.0, den=1000.0, vis=1.0e-3, attrs=None, file=None):
    """
    从json来创建流体数据
    """
    assert isinstance(pt, PTree)

    file = pt.find_file(key='file', default=file if file is not None else '',
                        doc='The file where to load the fluid data')
    if isfile(file):
        try:
            data = Seepage.FluData()
            data.load(file)
            return data
        except:
            pass

    comp_n = pt(key='comp_n', default=0, doc='The count of component')

    if comp_n == 0:
        mass = pt(key='mass', default=mass, doc='The mass')
        den = pt(key='den', default=den, doc='The density')
        vis = pt(key='vis', default=vis, doc='The viscosity')
        attrs = pt(key='attrs', default=attrs if attrs is not None else [], doc='The attributions')

        data = Seepage.FluData(mass=mass, den=den, vis=vis)
        for i in range(len(attrs)):
            data.set_attr(i, attrs[i])

        return data

    else:
        data = Seepage.FluData()
        for i in range(comp_n):
            comp = fludata(pt=pt.child(f'comp_{i}',
                                       doc=f'The settings for component {i}'),
                           mass=mass, den=den, vis=vis, attrs=attrs)
            data.add_component(comp)
        assert data.component_number == comp_n

        return data
