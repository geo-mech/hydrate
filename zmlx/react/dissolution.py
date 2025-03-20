import warnings

from zml import Seepage
from zmlx.react.add_reaction import add_reaction


def create(*, sol=None, sol_in_liq=None, liq=None, ca_sol=None, rate=1.0, fa_t=None, fa_c=None,
           gas=None, gas_in_liq=None):
    """
    创建物质 <比如盐或者气体> 在液体中中的溶解反应 <可逆的过程>，溶解度由ca_sol指定，且和温度压力无关;
        sol：溶质(自由的部分，尚未溶解进液体中的部分)
        sol_in_liq：溶解在液体中的溶质的ID
        liq：液体的ID
        ca_sol: Cell的属性ID, 溶解度 (质量浓度) 应为0到1之间的数值
        fa_t, fa_c：定义流体的温度和比热的属性ID;

    注：
        要求流体的温度在几百K的范围内, 否则可能会对定义的溶解度造成影响；
    """

    # 这个模块，最初是模拟气体的溶解。现在推广到一般的溶解过程，因此，修改参数的名字.
    if sol is None:
        if gas is not None:
            warnings.warn('The argument "gas" will be removed after 2025-4-14', DeprecationWarning)
            sol = gas

    if sol_in_liq is None:
        if gas_in_liq is not None:
            warnings.warn('The argument "gas_in_liq" will be removed after 2025-4-14', DeprecationWarning)
            sol_in_liq = gas_in_liq

    assert 0 < rate

    if fa_t is None:
        fa_t = 'temperature'

    if not isinstance(fa_t, str):
        if fa_t > 9999:
            fa_t = 'temperature'

    if fa_c is None:
        fa_c = 'specific_heat'

    if not isinstance(fa_c, str):
        if fa_c > 9999:
            fa_c = 'specific_heat'

    assert sol is not None
    assert sol_in_liq is not None
    assert liq is not None

    # 溶解量增大1，则teq增加1e8，则T-teq减小1e8，q减小，不利于溶解
    # 溶解度增大1，则teq降低1e8，则T-teq升高1e8，q增大，促进溶解
    # 设置当<虚拟>温度升高的时候，促进溶解
    return {'components': [dict(kind=sol, weight=-1.0, fa_t=fa_t, fa_c=fa_c),
                           dict(kind=sol_in_liq, weight=1.0, fa_t=fa_t, fa_c=fa_c)], 'temp': 280, 'heat': 0,
            'p2t': ([0, 1e8], [280, 280]),
            'inhibitors': [dict(sol=sol_in_liq, liq=liq, c=[0, 1], t=[0, 1e8])],
            'idt': ca_sol,  # 可以是一个属性字符串，后续添加的时候去注册
            'wdt': -1.0e8,
            't2q': ([-1e8, 1e8], [-rate, rate])
            }


def test():
    model = Seepage()

    c = model.add_cell()
    assert isinstance(c, Seepage.Cell)

    fa_c = 0
    fa_t = 1

    c.fluid_number = 2
    f0 = c.get_fluid(0)
    f0.mass = 1
    f0.set_attr(fa_t, 280).set_attr(fa_c, 1000)

    f1 = c.get_fluid(1)
    f1.component_number = 2
    f1.get_component(0).mass = 1
    f1.get_component(1).mass = 1
    f1.set_attr(fa_t, 280).set_attr(fa_c, 1000)

    c.set_attr(0, 0.1)

    print(c.get_fluid(0).mass, c.get_fluid(1).get_component(0).mass, c.get_fluid(1).get_component(1).mass)
    r = add_reaction(model, create(sol=0, sol_in_liq=(1, 1), liq=1, ca_sol=0, fa_c=fa_c, fa_t=fa_t))
    for step in range(20):
        r.react(model, dt=0.1)
        print(c.get_fluid(0).mass, c.get_fluid(1).get_component(0).mass, c.get_fluid(1).get_component(1).mass)


if __name__ == '__main__':
    test()
