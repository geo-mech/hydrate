# -*- coding: utf-8 -*-


from zmlx import *
from zmlx.alg.make_index import make_index


def create(igas, igas_in_liq, iliq, ca_sol, fa_t, fa_c, rate=1.0):
    """
    创建物质 <比如盐或者气体> 在液体中中的溶解反应 <可逆的过程>，溶解度由ca_sol指定，且和温度压力无关;
        igas：自由气的ID
        igas_in_liq：溶解在液体中的气体的ID（这里，两个气体被视为不同的物质组分）
        iliq：液体的ID
        ca_sol: 溶解度 (质量浓度) 应为0到1之间的数值
        fa_t, fa_c：定义流体的温度和比热;

    注：要求流体的温度在几百K的范围内；否则，可能会对定义的溶解度造成影响；
    """

    r = Reaction()

    assert 0 <= fa_t != fa_c and fa_c >= 0

    r.add_component(index=make_index(igas), weight=-1.0, fa_t=fa_t, fa_c=fa_c)         # 左侧物质
    r.add_component(index=make_index(igas_in_liq), weight=1.0, fa_t=fa_t, fa_c=fa_c)   # 右侧物质

    r.temp = 280
    r.heat = 0

    r.set_p2t(p=[0, 1e8], t=[280, 280])

    # 溶解量增大1，则teq增加1e8，则T-teq减小1e8，q减小，不利于溶解
    r.add_inhibitor(sol=igas_in_liq, liq=iliq, c=[0, 1], t=[0, 1e8])

    # 溶解度增大1，则teq降低1e8，则T-teq升高1e8，q增大，促进溶解
    r.idt = ca_sol
    r.wdt = -1.0e8

    # 设置当<虚拟>温度升高的时候，促进溶解
    assert 0 < rate
    r.set_t2q(t=[-1e8, 1e8], q=[-rate, rate])

    return r


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
    r = create(igas=0, igas_in_liq=(1, 1), iliq=1, ca_sol=0, fa_c=fa_c, fa_t=fa_t)

    for step in range(20):
        r.react(model, dt=0.1)
        print(c.get_fluid(0).mass, c.get_fluid(1).get_component(0).mass, c.get_fluid(1).get_component(1).mass)


if __name__ == '__main__':
    test()

