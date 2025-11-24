"""
对于某一个流体组分，计算扩散过程。

@2025-10-2
"""
from zmlx.base.seepage import as_numpy, Seepage, reg_cell_tmp, reg_face_tmp
from zmlx.config.alg import settings

# 存储的text
text_key = 'diffusion_settings'


def get_settings(model: Seepage) -> list:
    """
    读取扩散过程的设置。 对于一个模型，可以定义多个扩散的过程.
    """
    return settings.get(model, text_key=text_key)


def set_settings(model: Seepage, data: list | None):
    """
    写入设置
    """
    return settings.put(model, data=data, text_key=text_key)


def add_setting(model: Seepage, flu0=None, flu1=None, ca_m1=None,
                fa_g=None, fa_d=None, ca_c=None, cfl=None, fa_s=None, fa_l=None):
    """
    添加一个设置。具体的参数，参考 iterate 函数的参数.
    """
    assert flu0 is not None, "flu0 (溶质) 必须指定"
    assert flu1 is not None or ca_m1 is not None, "flu1 (溶液) 或者其质量(ca_m1)必须给定，否则无法计算浓度"
    assert fa_g is not None or fa_d is not None, "fa_g (face的扩散常数) 或者 fa_d(扩散系数)，必须给定一个"
    settings.add(model, text_key=text_key, flu0=flu0, flu1=flu1, ca_m1=ca_m1,
                 fa_g=fa_g, fa_d=fa_d, ca_c=ca_c, cfl=cfl, fa_s=fa_s, fa_l=fa_l)


def iterate(model: Seepage, dt,
            *, flu0=None, flu1=None, ca_m1=None, fa_g=None, fa_d=None, ca_c=None, cfl=None, fa_s=None, fa_l=None):
    """
    计算扩散过程. 如果具体的参数没有给出，则会尝试从model的配置中去获取。

    Args:
        model: 需要被迭代的模型。
        dt: 时间步长 (目标时间步长).
        flu0: 溶质的name或者索引
        flu1: 溶液的name或者索引
        ca_m1: “溶液”的质量属性
            在没有给定flu1的时候，会使用ca_m1作为“溶液”的质量属性.
        ca_c: 浓度属性的索引。
            浓度在这里是一个临时变量，因此ca_c可以为None. 此时，函数会创建一个临时的属性，用来暂时存储浓度.
        fa_d: 扩散系数属性. 此扩散系数乘以面积，再除以流动距离，就是g;
        fa_g: 用来计算扩散的cond的索引. 定义为 g=D*area/dist. 其中D为扩散系数 (有效扩散系数)
            当fa_g给定的时候，将会忽略fa_d
            注意：fa_d和fa_g必须给定1个
        cfl: CFL数，即通过Face扩散输运的质量与相邻的Cell中质量的比值 (用来计算建议的时间步长dt).
        fa_s: Face的属性，定义横截面积（当fa_g未指定时需要）
        fa_l: Face的属性，定义流动距离（当fa_g未指定时需要）

    Returns:
        计算的报告。一个dict类型. 当cfl不为None时，返回的报告中会包含“建议的时间步长dt”

    Notes:
        这里，我们关于溶质浓度，采用的是质量分数的定义，即浓度=溶质质量/溶液质量.
        此单位和化学中普遍采用的mol/L并不完全一样。关于浓度定义的差异，可能会影响到扩散系数的单位，
        因此，在给定fa_d属性的时候，需要考虑到这个差异。
    """
    assert isinstance(model, Seepage), 'model must be a Seepage model'
    if model.face_number == 0:
        return {}

    if flu0 is None:  # 没有给定“溶质”，此时，读取模型中存储的配置，并进行递归调用
        reports = []
        for setting in get_settings(model):
            assert isinstance(setting, dict)
            # 在配置中，必须已经给定了“溶质” (否则，这种递归调用会无限循环)
            assert setting.get('flu0') is not None, 'flu0 must be given in the setting'
            report = iterate(model, dt=dt, **setting)
            reports.append(report)
        return reports  # 返回多组计算报告

    # 确定“溶质”和“溶液”的ID
    if isinstance(flu0, str):  # 此时，代表溶质
        flu0 = model.find_fludef(name=flu0)
        assert flu0 is not None, f'Cannot find fludef with name {flu0}'

    if isinstance(flu0, int):
        flu0 = [flu0]

    if isinstance(flu1, str):
        flu1 = model.find_fludef(name=flu1)
        assert flu1 is not None, f'Cannot find fludef with name {flu1}'

    if isinstance(flu1, int):
        flu1 = [flu1]

    # 确定m1，即溶液的质量（在迭代的时候，假设m1是不变的。注意：这其实是一个近似!）
    if flu1 is None:  # 没有给定“溶液”，此时，必须在迭代之前，在外部给定溶液的质量
        assert ca_m1 is not None, 'ca_m1 must be given when solution is not given'
        m1 = as_numpy(model).cells.get(ca_m1)  # 要读取这个属性，因此，属性的值必须给定
    else:  # 使用溶液的质量
        m1 = as_numpy(model).fluids(*flu1).mass
        if ca_m1 is None:
            ca_m1 = reg_cell_tmp(model, 0)
        as_numpy(model).cells.set(ca_m1, m1)

    # 根据当前的"溶质"质量，计算当前的浓度c，并且存储为Cell的属性ca_c
    c = as_numpy(model).fluids(*flu0).mass / m1  # 浓度
    if ca_c is None:
        ca_c = reg_cell_tmp(model, 1)
    as_numpy(model).cells.set(ca_c, c)  # 设置浓度属性(对应于温度)

    if fa_g is None:  # 没有给定fa_g，此时，需要根据fa_d来计算fa_g
        assert fa_d is not None, 'fa_d must be given when fa_g is not given'
        fa_g = reg_face_tmp(model, 0)  # 此时，g就是临时变量
        d = as_numpy(model).faces.get(fa_d)
        if fa_s is None:
            fa_s = 'area'  # 要读取，因此，不能临时注册
        s = as_numpy(model).faces.get(fa_s)
        if fa_l is None:
            fa_l = 'length'  # 要读取，因此，不能临时注册
        l = as_numpy(model).faces.get(fa_l)
        g = s * d / l
        as_numpy(model).faces.set(fa_g, g)

    # 迭代计算浓度
    sol = model.temps.get('diffusion_sol')
    if sol is None:
        sol = Seepage.ThermalSol()
        model.temps['diffusion_sol'] = sol

    # 将浓度视为是温度场，将溶液的质量视为能量和温度的比值(即mc)，去迭代温度(修改浓度属性)
    r = sol.iterate(
        model, dt, ca_t=ca_c, ca_mc=ca_m1, fa_g=fa_g, solver=None,
        pool=None, report=None
    )
    if r is None:
        return {}

    # 根据浓度（ca_c属性，会在sol.iterate中被修改）计算质量m
    c = as_numpy(model).cells.get(ca_c)
    as_numpy(model).fluids(*flu0).mass = c * m1

    # 尝试计算建议的时间步长dt
    if cfl is not None:
        dt_new = sol.get_recommended_dt(
            model, dt, ca_t=ca_c, ca_mc=ca_m1, cfl=cfl)
        r['dt'] = dt_new

    # 返回计算的报告
    return r
