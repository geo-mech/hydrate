# ** desc = '水平井注入，浮力作用下气体运移、水合物成藏过程模拟(co2)'
"""
水平井注入，浮力作用下气体运移、水合物成藏过程模拟(co2)。x-z平面内的二维的模型。
"""

from zmlx import *


def create(
        mass_rate=50.0 / (3600.0 * 24.0),
        years_inj=20.0,
        p_seabed=10e6,
        t_seabed=275.0,
        depth_inj=200.0,
        x_inj=0.0,
        y_inj=0.0,
        perm=1.0e-15,
        free_h=5.0,
        mesh=None,
        s_ini=None,
        save_dt_min=None,
        save_dt_max=None,
        years_max=200.0,
        co2_temp=280.0,
        z2porosity=None,  # 一个函数，根据z坐标计算孔隙度
        grad_t=0.0443,
        **opts
):
    """
    free_h: 在海底一下，一定区域内，禁止生成水合物.
    创建模型(返回Seepage对象).
    """
    if mesh is None:  # 默认的mesh，是使用水平井
        from zmlx.seepage_mesh.xz_half import create_xz_half
        mesh = create_xz_half(x_max=300.0)

    # 海底的温度
    assert 273.0 <= t_seabed <= 300.0

    def get_t(x, y, z):  # 初始温度
        if z >= 0:
            return t_seabed
        else:
            return t_seabed - grad_t * z

    # 海底的压力
    assert 2e6 <= p_seabed <= 30e6

    def get_p(x, y, z):  # 初始压力
        return p_seabed - 1e4 * z

    # 初始的饱和度
    if s_ini is None:
        def s_ini(x, y, z):  # 初始的体积饱和度
            return {'h2o': 1 - 0.0315 / 2.165,
                    'inh': 0.0315 / 2.165
                    }

    # z坐标的范围
    z0, z1 = mesh.get_pos_range(2)

    def get_denc(x, y, z):  # 土体密度和比热的乘积
        if abs(z - z0) < 0.1 or z >= -1:
            return 1.0e20
        else:
            return 3.0e6

    def get_porosity(x, y, z):  # 这样，确保在顶部是自由的出口边界
        if abs(z - z1) < 1:
            return 1.0e10
        else:
            if callable(z2porosity):
                return z2porosity(z)
            else:
                return 0.3

    default_opts = dict(
        has_inh=True,  # 存在抑制剂
        has_co2=True,
        gravity=[0, 0, -10],
        has_co2_in_liq=True,
        heat_cond=2.0,
        dt_max=3600 * 24 * 365 * 10,  # 允许的最大的时间步长
        dv_relative=0.1,  # 每一步流体流体的距离与网格大小的比值
        pore_modulus=200e6,
        sol_dt=-0.3,
        inh_diff=1.0e6 / 400,
        co2_sol_data=dict(c=0.05, den_times=1.01),
        ch4_sol_data=dict(c=0.01, den_times=0.999),
        inh_sol_data=dict(c=0.035, den_times=1026.8 / 999.7),
        gr=create_krf(
            0.2, 3, as_interp=True,
            k_max=1, s_max=1, count=200
        ),
    )

    opts = {**default_opts, **opts}  # 使用给定的参数覆盖默认的参数

    # 生成用于建立水合物模型的关键词.
    opts = hydrate.create_opts(
        mesh=mesh,
        porosity=get_porosity,
        denc=get_denc,
        temperature=get_t,
        p=get_p,
        s=s_ini,  # 初始饱和度自定义
        perm=perm,
        **opts
    )

    # 用于求解的选项
    if save_dt_min is None:
        save_dt_min = 365.0 * 24.0 * 3600.0
    if save_dt_max is None:
        save_dt_max = 365.0 * 24.0 * 3600.0 * 1000.0

    solve_opts = {
        'time_max': years_max * 365.0 * 24.0 * 3600.0,
        'save_dt_min': save_dt_min,
        'save_dt_max': save_dt_max,
    }

    # 创建模型
    model = seepage.create(texts={'solve': solve_opts}, **opts)

    # 添加溶解态co2的扩散 (2025-11-25)
    diffusion.add_setting(
        model,
        flu0='co2_in_liq', flu1='liq', d=1.0e-9)

    # 设置co2的溶解度
    key = model.get_cell_key('n_co2_sol')
    for cell in model.cells:
        # 这里，将溶解度设置为固定的，也是一种近似。在不同的压力和温度下，溶解度应该是变化的.
        cell.set_attr(key, 0.06)

    # 设置在海底面附近，不能发生水合物的反应(气体进入这个区域)
    ca_rate = model.reg_cell_key('hyd_rate')
    for r in model.reactions:
        r.irate = ca_rate

    assert 0 <= free_h <= 30
    for cell in model.cells:
        if cell.z > - free_h:  # 在海底面以上的计算区域，作为缓冲边界，不生成水合物
            cell.set_attr(ca_rate, 0)

    # 设置相渗
    vs, kg, opts = create_kr(srg=0.01, srw=0.4, ag=3.5, aw=4.5)
    i_gas = model.find_fludef('gas')
    i_liq = model.find_fludef('liq')
    assert len(i_gas) == 1 and len(i_liq) == 1
    i_gas = i_gas[0]
    i_liq = i_liq[0]
    model.set_kr(i_gas, vs, kg)
    model.set_kr(i_liq, vs, opts)

    # 设置注入点 (co2). 注意: mass_rate 可以是一条曲线.
    assert 50 <= depth_inj <= 500.0
    assert 200 <= co2_temp <= 373
    fid = model.find_fludef(name='co2')
    cell = model.get_nearest_cell(pos=[x_inj, y_inj, -depth_inj])
    flu = cell.get_fluid(*fid).get_copy()
    # 原始情况下，co2的饱和度是0，因此，此时flu的质量是0。现在，
    # 需要将它的质量设置为一个宏观的量，确保属性能传进去
    flu.mass = 1
    flu.set_attr(
        index=model.get_flu_key('temperature'),
        value=co2_temp)
    try:  # 尝试将它作为曲线 (由两个list组成的)
        vt, vq = mass_rate
        assert len(vt) == len(vq) and len(vq) > 0
        opers = []
        for idx in range(len(vt)):
            t, q = vt[idx], vq[idx]
            if t < years_inj * 3600.0 * 24.0 * 365.0:
                vol_rate = q / flu.den
                opers.append([t, f'{vol_rate}'])
        opers.append([years_inj * 3600.0 * 24.0 * 365.0, '0'])
    except:  # 失败了之后，再作为一个数字来对待
        vol_rate = mass_rate / flu.den
        opers = [[0, f'{vol_rate}'], [years_inj * 3600.0 * 24.0 * 365.0, '0']]
    model.add_injector(
        cell=cell,
        value=0,
        fluid_id=fid,
        flu=flu,
        opers=opers,
    )
    # 返回创建的模型.
    return model


def show(model: Seepage):
    hydrate.show_2d_v2(
        model, dim0=0, dim1=2,
        fids=['ch4', 'ch4_hydrate', 'co2',
              'co2_in_liq',
              'co2_hydrate', 'inh'],
    )


def solve(model, *args, extra_plot=None, **kwargs):
    def x():
        show(model)
        if callable(extra_plot):
            extra_plot()

    seepage.solve(model, *args, extra_plot=x, **kwargs)


def main():
    model = create()
    solve(
        model, close_after_done=False,
        folder=opath('hydrate', 'co2')
    )


if __name__ == '__main__':
    main()
