# ** desc = '水平井注入，浮力作用下气体运移、水合物成藏过程模拟(co2)'
"""
物理问题描述：本模型模拟通过水平井向海底含水合物地层注入CO2气体。CO2在浮力作用下向上运移，
在适宜的温度压力条件下与水反应生成CO2水合物，模拟气体运移与水合物成藏的完整过程。
建模方法：采用x-z平面内的二维模型，使用hydrate.create()函数建立热-流-化（THC）耦合模型。
模型考虑CO2在水中的溶解与扩散、抑制剂（盐分）对水合物相平衡的影响、相对渗透率曲线、
以及水合物生成/分解动力学反应。采用水平井注入，支持注入速率随时间变化（可定义为曲线）。
边界条件：海底面设置为定温定压边界，顶部设为自由出口边界（高孔隙度），底部和两侧为绝热封闭边界。
关键参数：mass_rate（CO2注入质量速率，单位kg/s）、years_inj（注入年限，单位年）、
depth_inj（注入点深度，单位m，范围50-500m）、perm（渗透率，单位m²）、
grad_t（地温梯度，单位K/m）、free_h（海底附近禁止生成水合物的区域高度，单位m）。
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
    创建CO2注入与甲烷水合物成藏的耦合模型。

    本函数构建一个二维（x-z平面）的热-流-化（THC）耦合模型，模拟CO2通过水平井注入
    后在地层中的运移、与水反应生成CO2水合物的过程。模型包含初始温度场、压力场、
    饱和度场、渗透率场和孔隙度场的定义，以及注入井的设置。

    参数:
        mass_rate (float or list): CO2注入质量速率，单位kg/s。
            若为列表则需提供时间-速率曲线[[t1, t2, ...], [q1, q2, ...]]。
            默认值: 50.0 / (3600.0 * 24.0) = 约0.000579 kg/s。
        years_inj (float): 注入持续时间，单位年。默认值: 20.0年。
        p_seabed (float): 海底压力，单位Pa。范围2e6-30e6，默认值: 10e6 Pa。
        t_seabed (float): 海底温度，单位K。范围273-300，默认值: 275.0 K。
        depth_inj (float): 注入点深度（正值），单位m。范围50-500m，默认值: 200.0m。
        x_inj (float): 注入点x坐标，单位m。默认值: 0.0。
        y_inj (float): 注入点y坐标，单位m。默认值: 0.0。
        perm (float or callable): 渗透率，单位m²。可以是常数或关于(x,y,z)的函数。
            默认值: 1.0e-15 m²。
        free_h (float): 海底以下禁止生成水合物的区域高度，单位m。范围0-30m，默认值: 5.0m。
        mesh (Mesh): 计算网格。若为None则自动创建水平井适用的xz半平面网格。
        s_ini (callable, optional): 初始饱和度函数s_ini(x,y,z)，返回字典。
            若为None则默认包含水(1-0.0315/2.165)和抑制剂(0.0315/2.165)。
        save_dt_min (float, optional): 最小保存时间间隔，单位s。默认值: 365*24*3600s。
        save_dt_max (float, optional): 最大保存时间间隔，单位s。默认值: 365*24*3600*1000s。
        years_max (float): 最大模拟时间，单位年。默认值: 200.0年。
        co2_temp (float): 注入CO2的温度，单位K。默认值: 280.0 K。
        z2porosity (callable, optional): 根据z坐标计算孔隙度的函数。
        grad_t (float): 地温梯度，单位K/m。默认值: 0.0443 K/m。
        **opts: 其他传递给hydrate.create()的可选参数。

    返回:
        Seepage: 创建的水合物模型对象（Seepage实例），包含完整的网格、流体、
            反应体系和求解设置。
    """
    if mesh is None:  # 默认的mesh，是使用水平井
        from zmlx.seepage_mesh.xz_half import create_xz_half
        mesh = create_xz_half(x_max=300.0)

    # 海底的温度
    assert 273.0 <= t_seabed <= 300.0

    def get_t(x, y, z):  # 初始温度：海底以上为恒温，以下按地温梯度递增
        if z >= 0:
            return t_seabed
        else:
            return t_seabed - grad_t * z  # 深度越大（z为负），温度越高

    # 海底的压力
    assert 2e6 <= p_seabed <= 30e6

    def get_p(x, y, z):  # 初始压力：按静水压力分布，每10米约增加0.1MPa
        return p_seabed - 1e4 * z

    # 初始的饱和度
    if s_ini is None:
        def s_ini(x, y, z):  # 初始的体积饱和度
            return {'h2o': 1 - 0.0315 / 2.165,
                    'inh': 0.0315 / 2.165
                    }

    # z坐标的范围
    z0, z1 = mesh.get_pos_range(2)

    def get_denc(x, y, z):  # 土体密度和比热的乘积（热容），单位J/(m^3*K)
        if abs(z - z0) < 0.1 or z >= -1:
            return 1.0e20  # 边界处设极大值，近似绝热边界条件
        else:
            return 3.0e6  # 典型土体体积热容

    def get_porosity(x, y, z):  # 这样，确保在顶部是自由的出口边界
        if abs(z - z1) < 1:
            return 1.0e10
        else:
            if callable(z2porosity):
                return z2porosity(z)
            else:
                return 0.3

    default_opts = dict(
        has_inh=True,  # 存在抑制剂（盐分），影响水合物相平衡
        has_co2=True,  # 模型中包含CO2组分
        gravity=[0, 0, -10],  # 重力加速度，单位m/s²，沿z负方向（向下）
        has_co2_in_liq=True,  # CO2可溶解于液相
        heat_cond=2.0,  # 热传导系数，单位W/(m*K)
        dt_max=3600 * 24 * 365 * 10,  # 允许的最大时间步长（10年），单位s
        cfl=0.1,  # CFL条件限制：每步流体运移距离与网格尺寸的比值上限
        pore_modulus=200e6,  # 孔隙体积模量，单位Pa，控制孔隙压缩性
        sol_dt=-0.3,  # 溶解度对温度变化的敏感系数（负值表示随温度升高溶解度降低）
        inh_diff=1.0e6 / 400,  # 抑制剂扩散系数，单位m²/s
        co2_sol_data=dict(c=0.05, den_times=1.01),  # CO2溶解度参数：浓度c和溶解后密度变化倍数
        ch4_sol_data=dict(c=0.01, den_times=0.999),  # CH4溶解度参数
        inh_sol_data=dict(c=0.035, den_times=1026.8 / 999.7),  # 抑制剂（盐分）溶解参数，密度比约1.027
        gr=create_krf(  # 气体相对渗透率曲线（生成插值表）
            0.2, 3, as_interp=True,
            k_max=1, s_max=1, count=200
        ),
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

    opts = {**default_opts, **opts}  # 使用给定的参数覆盖默认的参数

    # 生成用于建立水合物模型的关键词.
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

    # 设置相渗（相对渗透率）曲线，控制气-液两相流动
    vs, kg, opts = create_kr(srg=0.01, srw=0.4, ag=3.5, aw=4.5)  # 残余气0.01，残余水0.4
    i_gas = model.find_fludef('gas')
    i_liq = model.find_fludef('liq')
    assert len(i_gas) == 1 and len(i_liq) == 1
    i_gas = i_gas[0]
    i_liq = i_liq[0]
    model.set_kr(i_gas, vs, kg)  # 设置气相相对渗透率
    model.set_kr(i_liq, vs, opts)  # 设置液相相对渗透率

    # 设置注入点 (co2). 注意: mass_rate 可以是一条曲线.
    assert 50 <= depth_inj <= 500.0
    assert 200 <= co2_temp <= 373
    fid = model.find_fludef(name='co2')  # 查找CO2流体的定义索引
    cell = model.get_nearest_cell(pos=[x_inj, y_inj, -depth_inj])  # 定位注入点所在网格
    flu = cell.get_fluid(*fid).get_copy()
    # 原始情况下，co2的饱和度是0，因此，此时flu的质量是0。现在，
    # 需要将它的质量设置为一个宏观的量，确保属性能传进去
    flu.mass = 1
    flu.set_attr(
        index=model.get_flu_key('temperature'),
        value=co2_temp)  # 设置注入CO2的温度
    try:  # 尝试将它作为曲线 (由两个list组成的)
        vt, vq = mass_rate
        assert len(vt) == len(vq) and len(vq) > 0
        opers = []  # 构建注入操作序列
        for idx in range(len(vt)):
            t, q = vt[idx], vq[idx]
            if t < years_inj * 3600.0 * 24.0 * 365.0:
                vol_rate = q / flu.den  # 将质量速率转换为体积速率
                opers.append([t, f'{vol_rate}'])
        opers.append([years_inj * 3600.0 * 24.0 * 365.0, '0'])  # 注入结束时关闭注入
    except:  # 失败了之后，再作为一个数字来对待
        vol_rate = mass_rate / flu.den
        opers = [[0.0, f'{vol_rate}'], [years_inj * 3600.0 * 24.0 * 365.0, '0']]
    model.add_injector(
        cell=cell,
        value=0,  # 指定注入点为恒定体积速率模式
        fluid_id=fid,
        flu=flu,
        opers=opers,  # 时间-注入速率操作列表
    )
    # 返回创建的模型.
    return model


def show(model: Seepage):
    """
    显示CO2注入水合物模型的可视化结果。

    使用hydrate.show_2d_v2函数在x-z平面（dim0=0, dim1=2）上展示模型状态，
    包括CH4气相、CH4水合物、CO2气相、溶解态CO2、CO2水合物和抑制剂的空间分布。

    参数:
        model (Seepage): 要显示的水合物模型对象。
    """
    hydrate.show_2d_v2(
        model, dim0=0, dim1=2,
        fids=['ch4', 'ch4_hydrate', 'co2',
              'co2_in_liq',
              'co2_hydrate', 'inh'],
    )


def solve(model, *args, extra_plot=None, **kwargs):
    """
    求解CO2注入水合物模型。

    对给定的模型执行瞬态求解，在每一步迭代后调用show()函数显示当前状态。
    用户可通过extra_plot参数添加额外的绘图回调函数。

    参数:
        model (Seepage): 要求解的水合物模型对象。
        *args: 传递给hydrate.solve()的位置参数。
        extra_plot (callable, optional): 额外的绘图回调函数，在show()之后调用。
        **kwargs: 传递给hydrate.solve()的关键字参数。
    """
    def x():
        show(model)
        if callable(extra_plot):
            extra_plot()

    hydrate.solve(model, *args, extra_plot=x, **kwargs)


def main():
    """
    co2.py的主入口函数。

    使用默认参数创建CO2注入模型，然后执行求解。结果保存在
    opath('hydrate', 'co2')目录下，求解完成后不自动关闭窗口。
    """
    model = create()
    solve(
        model,
        folder=opath('hydrate', 'co2')
    )


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
