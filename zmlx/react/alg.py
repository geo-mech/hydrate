import warnings
from collections.abc import Iterable

from zml import Seepage, parse_fid


def __add_inhibitor(
        reaction: Seepage.Reaction, sol, liq, c=None, t=None, *, use_vol=False,
        c2q=None, exp=None, exp_r=None, c2t=None):
    """
    添加一种抑制剂。

    Args:
        reaction: 需要添加inhibitor的反应
        sol (int): 抑制剂对应的组分ID。
        liq (int): 流体的组分ID。
        c (Vector or list): 抑制剂浓度向量 (弃用)
        t (Vector or list): 化学反应平衡温度向量 (弃用)
        use_vol (bool, optional): 是否使用体积。默认为False。
        c2t: 从浓度到平衡温度调整量的映射
        exp_r: 逆向反应的浓度指数
        exp: 正向反应的浓度指数
        c2q: 从浓度到反应速率的矫正量
    """
    idx = reaction.inhibitor_n
    reaction.inhibitor_n = idx + 1
    inh = reaction.get_inhibitor(idx)
    inh.sol = parse_fid(sol)
    inh.liq = parse_fid(liq)

    if c is not None and t is not None:
        c2t = c, t
        warnings.warn(
            'The arguments c and t will be removed after 2026-5-30, '
            'please use c2t instead',
            DeprecationWarning, stacklevel=3)

    if c2t is not None:
        c, t = c2t
        inh.c2t.set_xy(c, t)

    inh.use_vol = use_vol

    if c2q is not None:
        c, q = c2q
        inh.c2q.set_xy(c, q)

    if exp is not None:
        inh.exp = exp

    if exp_r is not None:
        inh.exp_r = exp_r


def add_inhibitor(*args, **kwargs):
    warnings.warn('function add_inhibitor will be removed after 2026-5-31',
                  DeprecationWarning, stacklevel=2)
    return __add_inhibitor(*args, **kwargs)


def __create_reaction(model, **opts):
    """
    根据给定的参数，创建一个反应（可能需要读取model中的流体定义，以及会在model中注册属性）
    返回的是一个Seepage.Reaction对象.
    可以参考这个函数对数据的定义，来生成相关的数据.
    """
    data = Seepage.Reaction()

    name = opts.get('name')
    if isinstance(name, str):
        data.name = name

    temp = opts.get('temp')
    if temp is not None:
        data.temp = temp

    heat = opts.get('heat')
    if heat is not None:
        data.heat = heat

    p2t = opts.get('p2t')
    if p2t is not None:
        p, t = p2t
        data.p2t.set_xy(p, t)

    t2q = opts.get('t2q')
    if t2q is not None:
        t, q = t2q
        data.t2q.set_xy(t, q)

    t2qr = opts.get('t2qr')  # 逆向反应的速率
    if t2qr is not None:
        t, qr = t2qr
        data.t2qr.set_xy(t, qr)

    components = opts.get('components')
    if components is not None:
        assert isinstance(components, Iterable)
        for comp in components:
            kind = comp.get('kind')
            if isinstance(kind, str):
                kind = model.find_fludef(kind)

            weight = comp.get('weight')
            assert -1.0 <= weight <= 1.0

            fa_t = comp.get('fa_t')
            assert fa_t is not None
            if isinstance(fa_t, str):
                fa_t = model.reg_flu_key(fa_t)

            fa_c = comp.get('fa_c')
            assert fa_c is not None
            if isinstance(fa_c, str):
                fa_c = model.reg_flu_key(fa_c)

            data.add_component(
                index=kind, weight=weight, fa_t=fa_t, fa_c=fa_c)

    inhibitors = opts.get('inhibitors')
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

            __add_inhibitor(
                data, sol=sol, liq=liq,
                use_vol=use_vol,
                c=inh.get('c'), t=inh.get('t'),
                c2t=inh.get('c2t'),
                c2q=inh.get('c2q'),
                exp=inh.get('exp'),
                exp_r=inh.get('exp_r')
            )

    idt = opts.get('idt')
    if idt is not None:
        if isinstance(idt, str):
            idt = model.reg_cell_key(idt)
        data.idt = idt

    wdt = opts.get('wdt')
    if wdt is not None:
        data.wdt = wdt

    irate = opts.get('irate')
    if irate is not None:
        if isinstance(irate, str):
            irate = model.reg_cell_key(irate)
        data.irate = irate

    return data


def create_reaction(model, **opts):
    warnings.warn('function create_reaction will be removed after 2026-5-31',
                  DeprecationWarning, stacklevel=2)
    return __create_reaction(model, **opts)


def add_reaction(model: Seepage, data, need_id=False):
    """
    添加一个反应
    """
    if not isinstance(data, Seepage.Reaction):
        data = __create_reaction(model, **data)
    return model.add_reaction(data=data, need_id=need_id)
