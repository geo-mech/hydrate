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
        c: 抑制剂浓度向量 (弃用)
        t: 化学反应平衡温度向量 (弃用)
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
    根据给定的参数，创建一个反应
        （可能需要读取model中的流体定义，以及会在model中注册属性）
    返回的是一个Seepage.Reaction对象.
    可以参考这个函数对数据的定义，来生成相关的数据.
    """
    data = Seepage.Reaction()

    name = opts.get('name')   # 定义反应的名字
    if isinstance(name, str):
        data.name = name

    temp = opts.get('temp')  # 定义和heat对应的温度（另外，当p2t没有定义的时候，此temp将作为默认的基准温度），单位为K
    if temp is not None:
        data.temp = temp

    heat = opts.get('heat')  # 反应的热量（发生1kg的反应所释放的热量）
    if heat is not None:
        data.heat = heat

    p2t = opts.get('p2t')  # 定义不同压力下的基准温度，如果没有定义，则直接使用temp属性作为基准温度
    if p2t is not None:
        p, t = p2t
        data.p2t.set_xy(p, t)

    t2q = opts.get('t2q')  # 不同温度下的基准的正向速率 (在此基础上，后续需要根据inhibitors浓度来进行矫正)
    if t2q is not None:
        t, q = t2q
        data.t2q.set_xy(t, q)

    t2qr = opts.get('t2qr')  # 逆向反应的速率 (在此基础上，后续需要根据inhibitors浓度来进行矫正)
    if t2qr is not None:
        t, qr = t2qr
        data.t2qr.set_xy(t, qr)

    components = opts.get('components')  # 反应的组分(反应的方程式)
    if components is not None:
        assert isinstance(components, Iterable)
        for comp in components:
            kind = comp.get('kind')  # 类型的name或者ID
            if isinstance(kind, str):
                kind = model.find_fludef(kind)

            weight = comp.get('weight')  # 权重，左侧为负值，右侧为正值，且左侧权重之和等于-1，右侧权重之和等于1
            assert -1.0 <= weight <= 1.0

            fa_t = comp.get('fa_t')  # 温度属性的ID
            assert fa_t is not None
            if isinstance(fa_t, str):
                fa_t = model.reg_flu_key(fa_t)

            fa_c = comp.get('fa_c')  # 比热属性的ID
            assert fa_c is not None
            if isinstance(fa_c, str):
                fa_c = model.reg_flu_key(fa_c)

            data.add_component(
                index=kind, weight=weight, fa_t=fa_t, fa_c=fa_c)

    inhibitors = opts.get('inhibitors')  # 抑制剂，请参考Seepage.Reaction.Inhibitor的定义和说明
    if inhibitors is not None:
        assert isinstance(inhibitors, Iterable)
        for inh in inhibitors:
            sol = inh.get('sol')   # 溶质
            if isinstance(sol, str):
                sol = model.find_fludef(sol)

            liq = inh.get('liq')  # 溶液
            if isinstance(liq, str):
                liq = model.find_fludef(liq)

            # 是否使用体积来计算浓度
            use_vol = inh.get('use_vol', False)

            # 浓度对基准温度的矫正 (x为浓度，y为温度矫正，单位是K)
            c2t = inh.get('c2t')

            # 浓度对反应速率的矫正 (x为浓度，y为速率矫正，单位是1/s)。
            # 反应速率的定义，请参考Seepage.Reaction的定义和注释
            c2q = inh.get('c2q')

            # 对正向反应速率的矫正指数
            exp = inh.get('exp')

            # 对逆向反应速率的矫正指数
            exp_r = inh.get('exp_r')

            # 生成抑制剂数据并且添加
            __add_inhibitor(
                data, sol=sol, liq=liq,
                use_vol=use_vol,
                c=inh.get('c'), t=inh.get('t'),  # 属性c和t弃用，用c2t替代
                c2t=c2t,
                c2q=c2q,
                exp=exp,
                exp_r=exp_r,
            )

    # 在使用p2t计算了基准温度之后，针对具体的Cell，再对基准温度进行的调整量（这允许对不同的Cell设置不同的基准温度）
    # 具体参考 Seepage.Reaction.idt属性的解释
    idt = opts.get('idt')
    if idt is not None:
        if isinstance(idt, str):
            idt = model.reg_cell_key(idt)
        data.idt = idt

    # 参考Seepage.Reaction.wdt的定义
    wdt = opts.get('wdt')
    if wdt is not None:
        data.wdt = wdt

    # 参考Seepage.Reaction.irate的定义
    irate = opts.get('irate')
    if irate is not None:
        if isinstance(irate, str):
            irate = model.reg_cell_key(irate)
        data.irate = irate

    # 返回生成的反应数据。注意，由于在生成数据的过程中，对模型进行了修改(注册某些属性)，因此，这里返回的data，
    # 应该立即被添加到model中，否则对model做的那些修改将是没有意义的。
    return data


def create_reaction(model, **opts):
    """
    在创建反应的时候，会修改到model，因此，创建的反应应该立即被添加到模型中。后续，将直接使用
    add_reaction来添加反应。
    """
    warnings.warn('function create_reaction will be removed after 2026-5-31',
                  DeprecationWarning, stacklevel=2)
    return __create_reaction(model, **opts)


def add_reaction(model: Seepage, data, need_id=False):
    """
    添加一个反应. 当给定的data是用于创建反应的dict时，请参考__create_reaction的文档以及代码中的注释来确定data的格式
    """
    if not isinstance(data, Seepage.Reaction):
        data = __create_reaction(model, **data)
    return model.add_reaction(data=data, need_id=need_id)
