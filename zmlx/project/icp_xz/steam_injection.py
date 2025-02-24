from icp_xz.create import create
from icp_xz.get_steam_rate import get_steam_rate
from icp_xz.mesh import create_mesh
from icp_xz.opath import opath
from icp_xz.solve import solve
from zml import Seepage, is_windows, Tensor3
from zmlx.config.seepage import flu_keys
from zmlx.fluid.alg import get_density, get_viscosity
from zmlx.fluid.h2o_gas import create as create_steam
from zmlx.ui import gui


def steam_injection(folder=None,
                    perm=None, heat_cond=None,
                    dx=None, dz=None,
                    years_heating=None,
                    years_balance=None,
                    years_prod=None,
                    s=None,
                    steam_temp=None,
                    time_to_power=None,  # 功率随着时间的变化，当定义这个参数的时候，将覆盖power.
                    power=None,
                    mesh=None,
                    gui_mode=None, close_after_done=True,
                    **space):
    """
    执行建模和求解 (蒸汽加热).
    """
    if years_heating is None:  # 注入蒸汽的时长
        years_heating = 5.0

    if years_balance is None:  # 温度平衡的时间长度(可以小于0)
        years_balance = 1.0

    if years_prod is None:
        years_prod = 4.0

    # 总共计算的时长
    assert years_balance + years_prod >= 0
    years_max = years_heating + years_balance + years_prod

    # 生产开启的时间
    year_prod_beg = years_heating + years_balance

    if heat_cond is None:
        heat_cond = 2.0

    if perm is None:  # 默认的渗透率
        perm = 1.0e-15

    if dx is None:  # x方向的网格大小
        dx = 0.3

    if dz is None:  # z方向的网格大小
        dz = 0.3

    # 水蒸气的温度
    if steam_temp is None:
        steam_temp = 800
    assert 400 <= steam_temp <= 1500

    # 每年的秒
    sec_y = 3600.0 * 24.0 * 365.0

    # 水蒸气的质量速率
    if time_to_power is None:  # 此时，将采用power定义的恒定功率
        if power is None:
            power = 5e3
        # 在years_heating之后，将power设置为0
        time_to_power = [[0, power],
                         [years_heating * sec_y, 0]]
    else:
        assert isinstance(time_to_power, list)
        # 此时，我们要确保时间控制在years_heating
        time_to_power = [item for item in time_to_power if item[0] < years_heating * sec_y]
        time_to_power.append([years_heating * sec_y, 0])

    # 利用功率来计算蒸汽的速率
    time_to_rate = []  # 不同时刻注入的质量速率
    for time, power in time_to_power:
        time_to_rate.append([time, get_steam_rate(power=power,
                                                  temp=steam_temp)])

    # 创建mesh (注意，这里的z代表了竖直方向)
    if mesh is None:
        mesh = create_mesh(dx=dx, dz=dz)

    # 水蒸气的定义
    steam = create_steam()

    # 蒸汽的性质
    steam_density = get_density(20e6, steam_temp, steam)
    assert steam_density is not None

    steam_viscosity = get_viscosity(20e6, steam_temp, steam)
    assert steam_viscosity is not None

    # 注册并使用动态的键值
    keys_holder = Seepage()
    fa = flu_keys(keys_holder)
    fa_t = fa.temperature
    fa_c = fa.specific_heat
    assert fa_t == 0 and fa_c == 1

    # 注入的流体的属性
    flu = Seepage.FluData(den=steam_density,
                          vis=steam_viscosity,
                          mass=1e6)
    flu.set_attr(fa_t, steam_temp)  # 温度
    flu.set_attr(fa_c, steam.specific_heat)  # 比热

    def make_inj(pos, ratio):
        opers = [[0.0, f'fid  0  1']]
        for t, rate in time_to_rate:
            opers.append([t, f'val  {rate * ratio / steam_density}'])

        return dict(pos=pos, opers=opers,
                    flu=flu,  # 注入的流体属性
                    )

    def run():
        """
        执行建模和求解过程
        """
        create(space,
               mesh=mesh,
               perm=Tensor3(xx=perm * 3, yy=perm * 3, zz=perm),
               injectors=[make_inj([15.0, 1, -7.5], 0.5),  # y>0，在裂缝介质
                          make_inj([15.0, 1, +7.5], 0.5)
                          ],
               heat_cond=Tensor3(xx=heat_cond,
                                 yy=heat_cond,
                                 zz=heat_cond / 3),
               s=s,
               z_max=15,
               z_min=-15,
               operations=[[sec_y * year_prod_beg, 'outlet', True]],
               dist=0.05,
               p_prod=20e6,  # 生产的压力
               keys=keys_holder.get_keys(),  # 预定义的keys
               temp_max=1000,  # 液态水允许的最高的温度
               )
        solve(space, folder=folder,
              time_max=years_max * sec_y)

    if gui_mode is None:
        gui_mode = is_windows

    gui.execute(run, close_after_done=close_after_done,
                disable_gui=not gui_mode)


if __name__ == '__main__':
    steam_injection(folder=opath('steam', 'base'))
