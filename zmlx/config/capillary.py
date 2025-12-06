"""
用于管理毛管压力驱动下的流动。

这里，我们将毛管压力理解为驱动相邻Cell之间流体交换的“驱动压力”。
在这个驱动下，Cell内流体的组分会进行交换，但是，
各个Cell内流体的“总的体积”均不会发生任何改变。

"""

from zmlx.base.seepage import get_face_sum, get_face_diff, get_dt, as_numpy
from zmlx.base.zml import Seepage, Interp1, get_pointer64, np, Vector
from zmlx.base.zml import clock

# 用于存储毛管压力驱动下的流动设置（不可以修改，否则之前的设置失效）
text_key = 'cap_settings'


def get_settings(model: Seepage):
    """
    返回模型中的cap设置
    """
    settings = []

    # from buffer
    buf = model.get_buffer(text_key)
    ind = 0
    while ind + 6 < buf.size:
        # 流体0
        a0 = round(buf[ind + 0])
        b0 = round(buf[ind + 1])
        c0 = round(buf[ind + 2])
        # 流体1
        a1 = round(buf[ind + 3])
        b1 = round(buf[ind + 4])
        c1 = round(buf[ind + 5])
        # 属性
        ca_ipc = round(buf[ind + 6])
        ind += 7
        #
        settings.append(
            {'fid0': [a0, b0, c0],
             'fid1': [a1, b1, c1],
             'ca_ipc': ca_ipc}
        )

    # from text
    text = model.get_text(text_key)
    if len(text) > 0:
        temp = eval(text)
        assert isinstance(temp, list)
        settings = settings + temp

    # return all
    return settings


def set_settings(model: Seepage, settings):
    """
    将cap设置存储到model
    """
    assert isinstance(settings, list)
    model.set_text(text_key, f'{settings}')


def _make_s2p(text):
    """
    根据文本来创建从饱和度到毛管压力的插值
    """
    vv = [[float(w) for w in line.split()] for line in text.splitlines() if
          len(line) > 2]
    s = [v[0] for v in vv]
    p = [v[1] for v in vv]
    assert len(s) == len(p) and len(s) >= 2
    for i in range(1, len(s)):
        assert s[i - 1] < s[i]
        assert p[i - 1] < p[i]
    return Interp1(x=s, y=p)


def add_setting(model: Seepage, fid0=None, fid1=None,
                get_idx=None, data=None,
                gravity=None):
    """
    创建一个毛管压力计算模型，其中fid0和fid1为涉及的两种流体。
    毛管压力定义为fid0的压力减去fid1的压力。model为创建好的渗流模型（或者Mesh）.
        idx = get_idx(x, y, z)
    是一个函数，该函数返回给定位置所需要采用的毛管压力曲线的ID，
        注意这个ID从0开始编号.
    后续的所有参数为毛管压力曲线，可以是Interp1类型，也可以给定两个list.
    """
    if fid0 is None or fid1 is None:  # 必须指定一对流体
        return

    if data is None and gravity is None:
        # 必须有毛管压力或者重力，否则，这个函数是不起作用的.
        return

    # 获取现在已经有的设置.
    settings = get_settings(model)
    assert isinstance(settings, list)
    count = len(settings)

    if data is not None:  # 给定的毛管压力的数据
        # 在cell中注册一个key，用来存储pc的id
        ca_ipc = model.reg_cell_key(f'ipc_{count}')
        # 将data添加到model
        ipcs = []
        for curve_id in range(len(data)):
            if isinstance(data[curve_id], Interp1):
                c = data[curve_id]
            elif isinstance(data[curve_id], str):
                c = _make_s2p(data[curve_id])
            else:
                s, p = data[curve_id]  # 从饱和度到压力的插值.
                c = Interp1(x=s, y=p)
            idx = model.add_pc(c, need_id=True)
            ipcs.append(idx)

        # 设置cell的pc的id
        for cell_id in range(model.cell_number):
            idx = round(get_idx(*model.get_cell(cell_id).pos))
            assert 0 <= idx < len(data)
            ipc = ipcs[idx]
            model.get_cell(cell_id).set_attr(ca_ipc, ipc)  # 设置pc的id
    else:  # 此时，不再考虑毛细管压力.
        ca_ipc = None

    # 将设置添加到model
    settings.append({
        'ca_ipc': ca_ipc, 'fid0': fid0, 'fid1': fid1,
        'gravity': gravity})
    set_settings(model, settings)


# 兼容之前的名字
add = add_setting


def _get_face_density_diff(
        model: Seepage, fid0, fid1):
    """
    获得face位置两种流体的密度差
    """
    ca = as_numpy(model).fluids(fid0).den - as_numpy(model).fluids(fid1).den
    fa = np.zeros(shape=model.face_number, dtype=float)
    get_face_sum(
        model, ca=get_pointer64(ca, readonly=True), fa=get_pointer64(fa))
    return fa / 2


def _get_face_gra(model: Seepage):
    """
    获取face两侧pos*gravity的差异
    """
    ca = as_numpy(model).cells.g_pos
    fa = np.zeros(shape=model.face_number, dtype=float)
    get_face_diff(
        model, ca=get_pointer64(ca, readonly=True),
        fa=get_pointer64(fa))
    return fa


def iterate_1(
        model=None, dt=None, fid0=None, fid1=None,
        ca_ipc=None, ds=0.05, gravity=None):
    """
    在毛管力驱动下的流动。如果只给定model，则根据model的设置进行迭代。
    Args:
        model: Seepage 对象
        dt: 时间步长
        fid0: 流体1的ID
        fid1: 流体2的ID
        ca_ipc: cell的属性，定义cell选择毛管压力曲线的id
        ds: 线性化的时候饱和度的变化幅度
        gravity: 驱动流体交换的重力加速度
    """
    assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'
    if dt is None:
        dt_used = get_dt(model)
    else:
        dt_used = dt

    if dt_used <= 1.0e-30:
        return

    if fid0 is not None and fid1 is not None:

        # 准备临时变量
        vs0 = model.temps.get('capillary.vs0')
        if vs0 is None:
            vs0 = Vector()
            model.temps['capillary.vs0'] = vs0

        vk = model.temps.get('capillary.vk')
        if vk is None:
            vk = Vector()
            model.temps['capillary.vk'] = vk

        vg = model.temps.get('capillary.vg')
        if vg is None:
            vg = Vector()
            model.temps['capillary.vg'] = vg

        # 毛管压力
        if ca_ipc is not None:
            model.get_linear_dpre(
                fid0=fid0, fid1=fid1,
                ca_ipc=ca_ipc, vs0=vs0,
                vk=vk, ds=ds, cell_ids=None)
        else:
            vs0.size = 0
            vk.size = 0

        # 重力
        if gravity is not None and gravity > 0:
            g = _get_face_gra(model) * _get_face_density_diff(
                model, fid0, fid1) * gravity
            ppg = get_pointer64(g)
            lpg = len(g)
        else:
            ppg = 0
            lpg = 0

        # 在重力和毛管力都没有定义的情况下，不需要计算
        if lpg == 0 and vs0.size == 0 and vk.size == 0:
            return

        if ca_ipc is not None:  # 定义了毛管力
            model.get_linear_dpre(
                fid0=fid0, fid1=fid1, ca_ipc=ca_ipc,
                vs0=vs0, vk=vk, ds=ds, cell_ids=None)
            model.get_cond_for_exchange(
                fid0=fid0, fid1=fid1,
                buffer=vg)
            model.diffusion(
                dt_used, fid0=fid0, fid1=fid1,
                ps0=vs0.pointer, ls0=vs0.size,
                pk=vk.pointer, lk=vk.size,
                pg=vg.pointer, lg=vg.size,
                ppg=ppg, lpg=lpg,
                ds_max=ds * 0.5)
        else:  # 没有定义毛管力，则仅仅考虑重力的效果
            if lpg > 0:  # 可以考虑重力
                # print(f'Iterate the Capillary By Gravity = {gravity}')
                model.get_cond_for_exchange(
                    fid0=fid0, fid1=fid1,
                    buffer=vg)  # 用来交换的g
                assert lpg == model.face_number
                model.diffusion(
                    dt_used, fid0=fid0, fid1=fid1,
                    pg=vg.pointer, lg=vg.size,
                    ppg=ppg, lpg=lpg, ds_max=ds * 0.5
                )
    else:  # 读取设置
        settings = get_settings(model)
        for setting in settings:
            assert isinstance(setting, dict)
            fid0 = setting.get('fid0')
            if isinstance(fid0, str):
                fid0 = model.find_fludef(fid0)
                assert fid0 is not None
            fid1 = setting.get('fid1')
            if isinstance(fid1, str):
                fid1 = model.find_fludef(fid1)
                assert fid1 is not None
            gravity = setting.get('gravity')
            iterate_1(
                model=model, dt=dt_used, fid0=fid0, fid1=fid1,
                ca_ipc=setting.get('ca_ipc'),
                ds=ds, gravity=gravity)  # 执行迭代.


@clock
def iterate(*models, **opts):
    """
    在毛管力驱动下的流动。如果只给定model，则根据model的设置进行迭代。
    Args:
        models: Seepage 对象
    """
    for model in models:
        assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'
        iterate_1(model, **opts)
