from zml import create_dict


def create_inh(sol, liq, c, t, *, use_vol=False):
    return create_dict(sol=sol, liq=liq, c=c, t=t, use_vol=use_vol)


def add_inh(r: dict, *, sol, liq, c, t, use_vol=False):
    r['inhibitors'].append(create_inh(sol=sol, liq=liq, c=c, t=t, use_vol=use_vol))
