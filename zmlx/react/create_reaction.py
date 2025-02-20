from collections.abc import Iterable

from zml import Seepage


def create_reaction(model, **kwargs):
    """
    根据给定的参数，创建一个反应（可能需要读取model中的流体定义，以及会在model中注册属性）
    """
    data = Seepage.Reaction()

    temp = kwargs.get('temp')
    if temp is not None:
        data.temp = temp

    heat = kwargs.get('heat')
    if heat is not None:
        data.heat = heat

    p2t = kwargs.get('p2t')
    if p2t is not None:
        p, t = p2t
        data.set_p2t(p, t)

    t2q = kwargs.get('t2q')
    if t2q is not None:
        t, q = t2q
        data.set_t2q(t, q)

    components = kwargs.get('components')
    if components is not None:
        assert isinstance(components, Iterable)
        for comp in components:
            kind = comp.get('kind')
            if isinstance(kind, str):
                kind = model.find_fludef(kind)

            weight = comp.get('weight')
            assert -1 <= weight <= 1

            fa_t = comp.get('fa_t')
            assert fa_t is not None
            if isinstance(fa_t, str):
                fa_t = model.reg_flu_key(fa_t)

            fa_c = comp.get('fa_c')
            assert fa_c is not None
            if isinstance(fa_c, str):
                fa_c = model.reg_flu_key(fa_c)

            data.add_component(index=kind, weight=weight, fa_t=fa_t, fa_c=fa_c)

    inhibitors = kwargs.get('inhibitors')
    if inhibitors is not None:
        assert isinstance(inhibitors, Iterable)
        for inh in inhibitors:
            # 这里要注意的是，这里的浓度指的是质量浓度.
            sol = inh.get('sol')
            if isinstance(sol, str):
                sol = model.find_fludef(sol)

            liq = inh.get('liq')
            if isinstance(liq, str):
                liq = model.find_fludef(liq)

            use_vol = inh.get('use_vol', False)
            data.add_inhibitor(sol=sol, liq=liq, c=inh.get('c'), t=inh.get('t'),
                               use_vol=use_vol)

    idt = kwargs.get('idt')
    if idt is not None:
        if isinstance(idt, str):
            idt = model.reg_cell_key(idt)
        data.idt = idt

    wdt = kwargs.get('wdt')
    if wdt is not None:
        data.wdt = wdt

    irate = kwargs.get('irate')
    if irate is not None:
        if isinstance(irate, str):
            irate = model.reg_cell_key(irate)
        data.irate = irate

    return data
