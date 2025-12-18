"""
对于某一个流体组分，计算扩散过程。

@2025-10-2
"""
from zml import clock
from zmlx.base.seepage import (
    as_numpy, Seepage, reg_cell_tmp, reg_face_tmp,
    get_dt, get_func_opts, get_dv_relative, Map, ThreadPool,
    set_attr, get_attr
)
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


def add_setting(
        model: Seepage, flu0=None, flu1=None, ca_m1=None,
        fa_g=None, fa_d=None, ca_c=None, cfl=None,
        fa_s=None, fa_l=None, d=None,
):
    """
    添加一个设置。具体的参数，参考 iterate 函数的参数.
    """
    assert flu0 is not None, "flu0 (溶质) 必须指定"
    assert flu1 is not None or ca_m1 is not None, \
        "flu1 (溶液) 或者其质量(ca_m1)必须给定，否则无法计算浓度"

    if d is not None:  # 给定了扩散系数，则设置给各个Face
        if fa_d is None:
            for index in range(20):  # 尝试注册fa_d
                key = f'diffusion_{index}'
                fa = model.get_face_key(key=key)
                if fa is None:
                    fa_d = model.reg_face_key(key=key)  # 新注册
                    break

        # 此时，上面尝试注册属性失败
        assert fa_d is not None, "fa_d (扩散系数属性) 必须指定"

        for face in model.faces:
            assert isinstance(face, Seepage.Face)
            if callable(d):
                value = d(*face.pos)
            else:
                value = d
            face.set_attr(fa_d, value)

    assert fa_g is not None or fa_d is not None, \
        "fa_g (face的扩散常数) 或者 fa_d(扩散系数)，必须给定一个"

    settings.add(
        model, text_key=text_key,
        flu0=flu0, flu1=flu1, ca_m1=ca_m1,
        fa_g=fa_g, fa_d=fa_d, ca_c=ca_c,
        cfl=cfl, fa_s=fa_s, fa_l=fa_l
    )


def iterate_1(*local_opts, pool=None, key_opt=None, **global_opts):
    """
    计算扩散过程. 如果具体的参数没有给出，则会尝试从model的配置中去获取。

    Args:
        key_opt: 用来存储计算结果的key.
        pool: 线程池.

    Returns:
        None

    Notes:
        这里，我们关于溶质浓度，采用的是质量分数的定义，即浓度=溶质质量/溶液质量.
        此单位和化学中普遍采用的mol/L并不完全一样。关
        于浓度定义的差异，可能会影响到扩散系数的单位，
        因此，在给定fa_d属性的时候，需要考虑到这个差异。
    """
    assert key_opt is not None
    models = []  # 所有的模型

    for local_opt in local_opts:
        # 解析出model
        if isinstance(local_opt, dict):
            model = local_opt.pop('model', None)
            assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'
        else:
            assert isinstance(local_opt, Seepage)
            model = local_opt
            local_opt = {}

        # 记录模型
        models.append(model)

        # 获得内部定义的选项
        inner_opts = get_func_opts(model, key_opt)

        # 默认选项
        default_opts = dict(
            recommend_dt=model.has_tag('recommend_dt'),
            dt=get_dt(model),
            dv_rela=get_dv_relative(model),
        )

        # 所有用来迭代的选项
        opts = {
            **default_opts, **inner_opts, **global_opts, **local_opt
        }

        if model.face_number == 0:
            model.temps[key_opt] = None
            continue

        flu0 = opts.get('flu0')
        # 确定“溶质”和“溶液”的ID
        if isinstance(flu0, str):  # 此时，代表溶质
            flu0 = model.find_fludef(name=flu0)
            assert flu0 is not None, f'Cannot find fludef with name {flu0}'

        if isinstance(flu0, int):
            flu0 = [flu0]

        opts['flu0'] = flu0

        flu1 = opts.get('flu1')

        if isinstance(flu1, str):
            flu1 = model.find_fludef(name=flu1)
            assert flu1 is not None, f'Cannot find fludef with name {flu1}'

        if isinstance(flu1, int):
            flu1 = [flu1]

        opts['flu1'] = flu1

        ca_m1 = opts.get('ca_m1')

        # 确定m1，即溶液的质量（在迭代的时候，假设m1是不变的。注意：这其实是一个近似!）
        if flu1 is None:  # 没有给定“溶液”，此时，必须在迭代之前，在外部给定溶液的质量
            assert ca_m1 is not None, \
                'ca_m1 must be given when solution is not given'
            m1 = as_numpy(model).cells.get(ca_m1)  # 要读取这个属性，因此，属性的值必须给定
        else:  # 使用溶液的质量
            m1 = as_numpy(model).fluids(*flu1).mass
            if ca_m1 is None:
                ca_m1 = reg_cell_tmp(model, 0)
                opts['ca_m1'] = ca_m1
            as_numpy(model).cells.set(ca_m1, m1)

        opts['m1'] = m1  # 后面恢复的时候用

        # 根据当前的"溶质"质量，计算当前的浓度c，并且存储为Cell的属性ca_c
        assert flu0 is not None
        c = as_numpy(model).fluids(*flu0).mass / m1  # 浓度
        ca_c = opts.get('ca_c')
        if ca_c is None:
            ca_c = reg_cell_tmp(model, 1)
            opts['ca_c'] = ca_c
        as_numpy(model).cells.set(ca_c, c)  # 设置浓度属性(对应于温度)

        fa_g = opts.get('fa_g')

        if fa_g is None:  # 没有给定fa_g，此时，需要根据fa_d来计算fa_g
            fa_d = opts.get('fa_d')
            assert fa_d is not None, 'fa_d must be given when fa_g is not given'
            fa_g = reg_face_tmp(model, 0)  # 此时，g就是临时变量
            d = as_numpy(model).faces.get(fa_d)
            fa_s = opts.get('fa_s')
            if fa_s is None:
                fa_s = 'area'  # 要读取，因此，不能临时注册
            s = as_numpy(model).faces.get(fa_s)
            fa_l = opts.get('fa_l')
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
        assert isinstance(sol, Seepage.ThermalSol)

        # 将浓度视为是温度场，将溶液的质量视为能量和温度的比值(即mc)，去迭代温度(修改浓度属性)
        dt = opts['dt']
        assert dt is not None, 'dt must be given'

        # 迭代，或者启动线程
        opts['result'] = Map()
        model.temps[key_opt] = opts
        sol.iterate(
            model, dt=dt, ca_t=ca_c, ca_mc=ca_m1, fa_g=fa_g, solver=None,
            pool=pool, report=opts['result']
        )

    if isinstance(pool, ThreadPool):
        pool.sync()  # 等待放入pool中的任务执行完毕

    for model in models:
        assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'
        opts = model.temps[key_opt]
        if opts is None:
            continue
        # 根据浓度（ca_c属性，会在sol.iterate中被修改）计算质量m
        ca_c = opts['ca_c']
        c = as_numpy(model).cells.get(ca_c)
        flu0 = opts['flu0']
        m1 = opts['m1']
        as_numpy(model).fluids(*flu0).mass = c * m1  # 更新“溶质”的质量
        # 处理dt
        if opts['recommend_dt']:
            dv_rela = opts['dv_rela']
            if 0 < dv_rela < 1.0e3:
                sol = model.temps.get('diffusion_sol')
                assert isinstance(sol, Seepage.ThermalSol)
                dt_next = sol.get_recommended_dt(
                    model, previous_dt=opts['dt'],
                    dv_relative=dv_rela,
                    ca_t=opts['ca_c'], ca_mc=opts['ca_m1']
                )
                opts['dt_next'] = dt_next  # 存储在option里面


@clock
def iterate(*models, pool=None, **global_opts):
    all_settings = [get_settings(model) for model in models]
    count = 0
    for data in all_settings:
        count = max(count, len(data))
    if count == 0:
        return

    for layer in range(count):  # 逐层去进行扩散
        local_opts = []
        for i in range(len(models)):
            layer_n = len(all_settings[i])
            if layer < layer_n:
                data = all_settings[i][layer]
                assert data.get('flu0') is not None, \
                    'flu0 must be given in the setting'
                opts = dict(model=models[i], **data)
                local_opts.append(opts)
        assert len(local_opts) > 0
        key_opt = f'diffusion_opt_{layer}'
        for model in models:
            model.temps[key_opt] = None
        iterate_1(*local_opts, pool=pool, key_opt=key_opt, **global_opts)

    # 计算建议的时间步长
    for model in models:
        dt_next = None
        for layer in range(count):
            key_opt = f'diffusion_opt_{layer}'
            opts = model.temps[key_opt]
            if opts is None:
                continue
            value = opts.get('dt_next')
            if value is not None:
                if dt_next is None:
                    dt_next = value
                else:
                    dt_next = min(value, dt_next)
        if dt_next is not None:
            set_dt_next(model, dt_next)
        else:
            set_dt_next(model, -1)


def get_dt_next(model: Seepage):
    return get_attr(model, 'diffusion_dt_next', default_val=-1)


def set_dt_next(model: Seepage, dt_next):
    set_attr(model, 'diffusion_dt_next', dt_next)
