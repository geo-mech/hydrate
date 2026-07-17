# ** desc = '直井注入（采用柱坐标体系），浮力作用下气体运移、水合物成藏过程模拟(co2)'
"""
物理问题描述：本模型模拟通过垂直直井（直井注入）向海底含水合物地层注入CO2气体，
采用柱坐标系（r-z）考虑井筒的轴对称几何特征。CO2在浮力作用下向上运移，
在适宜的温度压力条件下与水反应形成CO2水合物。
建模方法：采用柱坐标系下的二维模型（r-z平面），与co2.py的区别在于使用
圆柱坐标权重（thick=2*pi*r）处理轴对称几何，更真实地模拟单井注入场景。
网格厚度随径向距离r线性增加，以正确反映圆柱体积分中的面积权重。
关键参数：mass_rate（注入质量速率，单位kg/s）、years_inj（注入年限，单位年）、
depth_inj（注入点深度，单位m）、perm（渗透率，单位m²）、
grad_t（地温梯度，单位K/m）、free_h（海底附近禁止生成水合物的区域高度，单位m）。
注：与水平井情况相比，此处注入速率和模拟时间尺度更小（months级），
反映直井注入速率更高的特点。
"""

from zmlx import *


def create(
        mass_rate=500.0 / (3600.0 * 24.0),
        years_inj=1.0 / 12.0,  # 默认注入1个月
        p_seabed=10e6,
        t_seabed=275.0,
        depth_inj=30.0,  # 注入深度较浅（与水平井相比）
        x_inj=0.0,  # 井位于r=0（对称轴）
        y_inj=0.0,
        perm=1.0e-15,
        free_h=3.0,  # 在海底以下，一定区域内，禁止生成水合物
        mesh=None,
        s_ini=None,
        save_dt_min=None,
        save_dt_max=None,
        years_max=1.0,  # 最大模拟时间（直井模拟时间较短）
        co2_temp=280.0,
        z2porosity=None,  # 一个函数，根据z坐标计算孔隙度
        grad_t=0.0443,  # 地温梯度，单位K/m
        **opts
):
    """
    创建直井注入CO2的柱坐标系模型。

    本函数构建一个柱坐标系（r-z平面）的THC耦合模型，模拟CO2通过垂直直井
    注入后在地层中的轴对称运移与水合物生成过程。网格使用柱坐标权重
    （thick=2*pi*r）以正确反映轴对称几何的体积积分。

    参数:
        mass_rate (float or list): CO2注入质量速率，单位kg/s。默认值约0.0058 kg/s。
        years_inj (float): 注入持续时间，单位年。默认值: 1/12 ≈ 1个月。
        p_seabed (float): 海底压力，单位Pa。范围2e6-30e6，默认值: 10e6 Pa。
        t_seabed (float): 海底温度，单位K。范围273-300，默认值: 275.0 K。
        depth_inj (float): 注入点深度（正值），单位m。默认值: 30.0m。
        x_inj (float): 注入点r坐标（柱坐标径向），单位m。默认值: 0.0（井轴位置）。
        y_inj (float): 注入点y坐标（柱坐标环向），单位m。默认值: 0.0。
        perm (float or callable): 渗透率，单位m²。默认值: 1.0e-15 m²。
        free_h (float): 海底以下禁止生成水合物的区域高度，单位m。默认值: 3.0m。
        mesh (Mesh): 计算网格。若为None则自动创建柱坐标适用的半平面网格。
        s_ini (callable, optional): 初始饱和度函数。
        save_dt_min (float, optional): 最小保存时间间隔，单位s。
        save_dt_max (float, optional): 最大保存时间间隔，单位s。
        years_max (float): 最大模拟时间，单位年。默认值: 1.0年。
        co2_temp (float): 注入CO2的温度，单位K。默认值: 280.0 K。
        z2porosity (callable, optional): 根据z坐标计算孔隙度的函数。
        grad_t (float): 地温梯度，单位K/m。默认值: 0.0443 K/m。
        **opts: 其他传递给hydrate.create()的可选参数。

    返回:
        Seepage: 柱坐标系下的水合物模型对象。
    """
    if mesh is None:  # 默认的mesh，是使用水平井
        from zmlx.seepage_mesh.xz_half import create_xz_half
        mesh = create_xz_half(x_max=40.0, depth=80.0, height=30.0, dx=0.5, dz=0.5, hc=50.0,
                              rc=10.0)  # 厚度为1，目标，调整为，厚度=2pi*r

        # 将网格从直角坐标系转换为柱坐标系（轴对称）
        # 每个网格的体积乘以 2*pi*r（r为径向距离），以模拟轴对称圆柱体积分权重
        for cell in mesh.cells:
            (x, y, z) = cell.pos  # x坐标在此处代表径向距离r
            thick = 2.0 * 3.1415 * x  # 圆柱坐标系下的周向长度权重
            cell.vol *= thick

        # 同样调整面的面积以匹配柱坐标系
        for face in mesh.faces:
            (i0, i1) = face.link
            (x0, y0, _) = mesh.get_cell(i0).pos
            (x1, y1, _) = mesh.get_cell(i1).pos
            x = (x0 + x1) / 2  # 取面中心处的径向距离
            thick = 2.0 * 3.1415 * x
            face.area *= thick

    # 海底的温度
    assert 273.0 <= t_seabed <= 300.0

    def get_t(x, y, z):  # 初始温度：海底以上恒温，以下按地温梯度递增
        if z >= 0:
            return t_seabed
        else:
            return t_seabed - grad_t * z  # z为负，深度越大温度越高

    # 海底的压力
    assert 2e6 <= p_seabed <= 30e6

    def get_p(x, y, z):  # 初始压力：按静水压力分布
        return p_seabed - 1e4 * z  # z为负，深度越大压力越高

    # 初始的饱和度
    if s_ini is None:
        def s_ini(x, y, z):  # 初始的体积饱和度
            return {'h2o': 1 - 0.0315 / 2.165,
                    'inh': 0.0315 / 2.165
                    }

    # z坐标的范围
    z0, z1 = mesh.get_pos_range(2)

    def get_denc(x, y, z):  # 土体密度和比热的乘积（体积热容），单位J/(m^3*K)
        if abs(z - z0) < 0.1 or z >= -1:
            return 1.0e20  # 边界处设极大值，近似绝热边界
        else:
            return 3.0e6  # 典型土体体积热容

    def get_porosity(x, y, z):  # 这样，确保在顶部是自由的出口边界
        if abs(z - z1) < 1:
            return 1.0e10  # 顶部边界设极大孔隙度，允许流体自由流出
        else:
            if callable(z2porosity):
                return z2porosity(z)
            else:
                return 0.3

    default_opts = dict(
        has_inh=True,  # 存在抑制剂（盐分）
        has_co2=True,  # 包含CO2组分
        gravity=[0, 0, -10],  # 重力加速度，单位m/s²
        has_co2_in_liq=True,  # CO2可溶于液相
        heat_cond=2.0,  # 热传导系数，单位W/(m*K)
        dt_max=3600 * 24 * 365,  # 允许的最大时间步长（1年），单位s
        cfl=0.1,  # CFL条件：每步流体运移距离/网格尺寸的比值上限
        pore_modulus=200e6,  # 孔隙体积模量，单位Pa
        sol_dt=-0.3,  # 溶解度对温度的敏感系数
        inh_diff=1.0e6 / 400,  # 抑制剂扩散系数，单位m²/s
        co2_sol_data=dict(c=0.05, den_times=1.01),  # CO2溶解度参数
        ch4_sol_data=dict(c=0.01, den_times=0.999),  # CH4溶解度参数
        inh_sol_data=dict(c=0.035, den_times=1026.8 / 999.7),  # 抑制剂溶质密度比约1.027
        gr=create_krf(  # 气体相对渗透率曲线（插值表形式）
            0.2, 3, as_interp=True,
            k_max=1, s_max=1, count=200
        ),
    )

    # 使用给定的参数覆盖默认的参数
    opts = {**default_opts, **opts}

    # 用于求解的选项
    if save_dt_min is None:
        save_dt_min = 0.1 * 24.0 * 3600.0
    if save_dt_max is None:
        save_dt_max = 10 * 24.0 * 3600.0

    solve_opts = {
        'time_max': years_max * 365.0 * 24.0 * 3600.0,
        'save_dt_min': save_dt_min,
        'save_dt_max': save_dt_max,
    }

    model = hydrate.create(
        mesh=mesh,
        porosity=get_porosity,
        denc=get_denc,
        temperature=get_t,
        p=get_p,
        s=s_ini,  # 初始饱和度自定义
        perm=perm,
        texts={'solve': solve_opts},
        **opts
    )

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

    # 设置相渗（相对渗透率）曲线：控制气-液两相流动行为
    vs, kg, opts = create_kr(srg=0.01, srw=0.4, ag=3.5, aw=4.5)  # 残余气0.01，残余水0.4
    i_gas = model.find_fludef('gas')
    i_liq = model.find_fludef('liq')
    assert len(i_gas) == 1 and len(i_liq) == 1
    i_gas = i_gas[0]
    i_liq = i_liq[0]
    model.set_kr(i_gas, vs, kg)  # 设置气相相对渗透率
    model.set_kr(i_liq, vs, opts)  # 设置液相相对渗透率

    # 设置注入点 (co2). 注意: mass_rate 可以是一条曲线（时间和速率的列表）.
    assert 20 <= depth_inj <= 500.0
    assert 200 <= co2_temp <= 373
    fid = model.find_fludef(name='co2')  # 查找CO2流体的定义索引
    cell = model.get_nearest_cell(pos=[x_inj, y_inj, -depth_inj])  # 定位注入井所在网格
    flu = cell.get_fluid(*fid).get_copy()
    # 原始情况下，co2的饱和度是0，因此，此时flu的质量是0。现在，
    # 需要将它的质量设置为一个宏观的量，确保属性能传进去
    flu.mass = 1
    flu.set_attr(
        index=model.get_flu_key('temperature'),
        value=co2_temp  # 设置注入CO2的温度
    )
    try:  # 尝试将mass_rate作为曲线（由两个list组成的）
        vt, vq = mass_rate
        assert len(vt) == len(vq) and len(vq) > 0
        opers = []  # 构建注入操作序列
        for idx in range(len(vt)):
            t, q = vt[idx], vq[idx]
            if t < years_inj * 3600.0 * 24.0 * 365.0:
                vol_rate = q / flu.den  # 将质量速率转换为体积速率
                opers.append([t, f'{vol_rate}'])
        opers.append([years_inj * 3600.0 * 24.0 * 365.0, '0'])  # 注入结束时关闭
    except:  # 失败后作为单个数值处理
        vol_rate = mass_rate / flu.den
        opers = [[0, f'{vol_rate}'], [years_inj * 3600.0 * 24.0 * 365.0, '0']]
    model.add_injector(
        cell=cell,
        value=0,  # 恒定体积速率模式
        fluid_id=fid,
        flu=flu,
        opers=opers,  # 时间-速率操作列表
    )
    # 返回创建的模型.
    return model


def show(model: Seepage):
    """
    显示柱坐标下CO2注入模型的2D可视化结果。

    展示r-z平面内的CO2气相、液相溶解CO2、CO2水合物和抑制剂的分布。
    显示范围限定在径向0-20m，垂向-50到-10m（重点关注井附近区域）。

    参数:
        model (Seepage): 要显示的水合物模型对象。
    """
    hydrate.show_2d_v2(
        model, dim0=0, dim1=2,
        fids=['co2', 'co2_in_liq', 'co2_hydrate', 'inh'],
        xr=[0, 20], zr=[-50, -10],  # 径向范围0-20m，垂向范围-50到-10m
    )


def solve(model, *args, extra_plot=None, **kwargs):
    """
    求解柱坐标下CO2注入水合物模型。

    每一步迭代后调用show()显示当前状态，支持额外的绘图回调。

    参数:
        model (Seepage): 要求解的水合物模型对象。
        *args: 传递给hydrate.solve()的位置参数。
        extra_plot (callable, optional): 额外的绘图回调函数。
        **kwargs: 传递给hydrate.solve()的关键字参数。
    """
    def x():
        show(model)
        if callable(extra_plot):
            extra_plot()

    hydrate.solve(model, *args, extra_plot=x, **kwargs)


def main():
    """
    co2_cylinder.py的主入口函数。

    使用默认参数创建柱坐标CO2注入模型，执行求解并将结果保存到
    opath('hydrate', 'co2_cylinder')目录下。
    """
    model = create()
    solve(
        model,
        folder=opath('hydrate', 'co2_cylinder')
    )


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
