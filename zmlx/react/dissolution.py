from zml import Seepage, create_dict


def create(gas, gas_in_liq, liq, ca_sol, rate=1.0, fa_t=None, fa_c=None):
    """
    创建物质 <比如盐或者气体> 在液体中中的溶解反应 <可逆的过程>，溶解度由ca_sol指定，且和温度压力无关;
        igas：自由气的ID
        igas_in_liq：溶解在液体中的气体的ID（这里，两个气体被视为不同的物质组分）
        iliq：液体的ID
        ca_sol: 溶解度 (质量浓度) 应为0到1之间的数值
        fa_t, fa_c：定义流体的温度和比热;

    注：要求流体的温度在几百K的范围内；否则，可能会对定义的溶解度造成影响；
    """
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

    # 溶解量增大1，则teq增加1e8，则T-teq减小1e8，q减小，不利于溶解
    # 溶解度增大1，则teq降低1e8，则T-teq升高1e8，q增大，促进溶解
    # 设置当<虚拟>温度升高的时候，促进溶解
    return {'components': [create_dict(kind=gas, weight=-1.0, fa_t=fa_t, fa_c=fa_c),
                           create_dict(kind=gas_in_liq, weight=1.0, fa_t=fa_t, fa_c=fa_c)], 'temp': 280, 'heat': 0,
            'p2t': ([0, 1e8], [280, 280]), 'inhibitors': [create_dict(sol=gas_in_liq, liq=liq, c=[0, 1], t=[0, 1e8])],
            'idt': ca_sol, 'wdt': -1.0e8, 't2q': ([-1e8, 1e8], [-rate, rate])}


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
    r = model.add_reaction(create(gas=0, gas_in_liq=(1, 1), liq=1, ca_sol=0, fa_c=fa_c, fa_t=fa_t))
    for step in range(20):
        r.react(model, dt=0.1)
        print(c.get_fluid(0).mass, c.get_fluid(1).get_component(0).mass, c.get_fluid(1).get_component(1).mass)


if __name__ == '__main__':
    test()
