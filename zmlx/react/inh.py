from zml import create_dict


def create_inh(sol, liq, c, t):
    return create_dict(sol=sol, liq=liq, c=c, t=t)


def add_inh(r: dict, *, sol, liq, c, t):
    r['inhibitors'].append(create_inh(sol=sol, liq=liq, c=c, t=t))
