from zmlx.io.json_ex import ConfigFile, get_child
from zml import Seepage


def from_json(json=None, mass=0.0, den=1000.0, vis=1.0e-3, attrs=None):
    """
    从json来创建流体数据
    """
    if json is not None:
        if not isinstance(json, ConfigFile):
            json = ConfigFile(json)

    comp_n = 0
    if json is not None:
        comp_n = json(key='comp_n', default=0, doc='The count of component')

    if comp_n == 0:
        if attrs is None:
            attrs = []

        if json is not None:
            mass = json(key='mass', default=mass, doc='The mass')
            den = json(key='den', default=den, doc='The density')
            vis = json(key='vis', default=vis, doc='The viscosity')
            attrs = json(key='attrs', default=attrs, doc='The attributions')

        data = Seepage.FluData(mass=mass, den=den, vis=vis)
        for i in range(len(attrs)):
            data.set_attr(i, attrs[i])

        return data

    else:
        data = Seepage.FluData()
        for i in range(comp_n):
            comp = from_json(json=get_child(json, f'comp_{i}',
                                            doc=f'The settings for component {i}'),
                             mass=mass, den=den, vis=vis, attrs=attrs)
            data.add_component(comp)
        assert data.component_number == comp_n

        return data
