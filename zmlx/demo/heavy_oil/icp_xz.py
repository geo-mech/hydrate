# ** desc = '原位转化：在xz平面二维的模型'
#
# 本案例模拟油页岩原位转化（ICP）过程的二维xz剖面模型：
# 模型区域为x方向[0,15]m，z方向[-30,30]m，储层位于z方向[-15,15]m范围内。
# 初始条件下，储层内含干酪根（kg）、重油（ho）、轻油（lo）、甲烷（ch4）、水（h2o）等组分。
# 在x=15m处设置两个加热点（z=-7.5m和z=+7.5m），每个加热点功率2.5kW（总功率5kW），
# 加热时长为5年，总模拟时长8年。
# 在模型右下角添加了一个虚拟生产井（通过add_cell_face实现），用于流体产出。
# 与圆柱模型不同，本模型采用直角坐标网格，便于观察水平井或倾斜井情景。
# 通过icp框架（基于tfc的热-流-化学耦合）模拟干酪根热解、油气生成和运移的完整过程。

from zmlx import *


def create(years_heating=5.0, years_max=8.0, power=5e3):
    """
    创建原位转化xz二维模型。

    参数:
        years_heating: float，加热时长（年）。控制加热器工作时间
        years_max: float，总计算时长（年）。整个模拟的时间跨度
        power: float，加热功率（瓦特）。所有加热点的总功率
    返回:
        Seepage对象，配置完成的渗流-热-化学耦合模型
    """
    # 创建二维xz网格：x方向0~15m，步长0.5m；z方向-30~30m，步长0.5m
    mesh = create_xz(x_min=0, dx=0.5, x_max=15.0, y_min=-1, y_max=0,
                     z_min=-30.0, dz=0.5, z_max=30.0)

    z_min, z_max = get_pos_range(mesh, 2)  # 获取网格在z方向的范围

    # 添加虚拟的cell和face用于生产（在网格右上方添加一个大体积单元格作为虚拟生产井）
    add_cell_face(mesh, pos=[0, 0, 0], offset=[0, 10, 0],
                  vol=10000, area=1, length=1)

    def get_perm(x, y, z):                 # 渗透率分布函数：仅储层范围（-15~15m）有渗透率
        return 1.0e-15 if -15 <= z <= 15 else 0

    def get_s(x, y, z):                    # 初始饱和度分布函数
        # 储层内且y<5的区域：包含干酪根、重油、轻油、甲烷和水等多种组分
        if -15 <= z <= 15 and y < 5:
            return {'ch4': 0.08, 'h2o': 0.04, 'lo': 0.08,
                    'ho': 0.2, 'kg': 0.6}
        else:
            return {'ch4': 1}              # 储层外围岩：纯甲烷

    def get_denc(x, y, z):                 # 体积热容（密度*比热）分布函数
        if abs(z - z_min) < 0.1 or abs(z - z_max) < 0.1:  # 上下边界处设极大值模拟恒温边界
            return 1e20
        else:
            return 4e6                      # 储层正常体积热容

    def get_porosity(x, y, z):             # 孔隙度分布函数
        return 0.3 if -15 <= z <= 15 else 0.01  # 储层内0.3，储层外仅0.01

    # 渗透率曲线（用于计算相对渗透率随饱和度的变化）
    gr = create_krf(faic=0.02, n=3.0, k_max=100, s_max=2.0,
                    count=500, as_interp=True)

    # 默认的相对渗透率曲线（用于未明确指定的流体组合）
    default_kr = create_krf(faic=0.05, n=2.0, count=300,
                            as_interp=True)

    # 定义加热点的位置（两个加热点分别位于储层上下部）
    v_pos = [[15.0, 1, -7.5],              # 下部加热点
             [15.0, 1, +7.5]]              # 上部加热点
    ca = tfc.cell_keys()                    # 获取tfc框架的单元格键定义
    # 定义加热器（以注入器的形式向单元格添加热量）
    injectors = [
        {'pos': pos, 'radi': 3, 'ca_mc': ca.mc,  # 位置、影响半径、质量/能量键
         'ca_t': ca.temperature,                   # 温度键
         'value': power / len(v_pos),              # 每个加热点分配的功率
         'opers': [[years_heating * 3600.0 * 24.0 * 365.0,  # 加热时长转换为秒
                    '0']],                                  # 加热结束后功率归零
         } for pos in v_pos]

    # 定义生产井：最后一个单元格（虚拟生产井）以恒定压力20MPa产出
    prods = [
        {'index': mesh.cell_number - 1,    # 虚拟生产井的单元格索引
         't': [0, 1e10],                   # 生产时间范围（从0到极长时间，表示持续生产）
         'p': [20e6, 20e6]                 # 生产井底压力恒定20MPa
         }]

    # 用于求解器（solve）的选项
    solve = {
        'monitor': {'cell_ids': [mesh.cell_number - 1]},  # 监视虚拟生产井的状态
        'time_max': 3600.0 * 24.0 * 365.0 * years_max,   # 总模拟时间（秒）
    }

    # 创建模型（使用icp框架封装，自动配置流体定义和化学反应）
    model = icp.create(
        mesh=mesh,
        keys=ca.get_keys(),                   # 使用tfc框架定义的属性键
        porosity=get_porosity,                 # 孔隙度（空间分布函数）
        pore_modulus=100e6,                    # 孔隙体积模量（100MPa）
        p=20e6,                                # 初始压力20MPa
        temperature=350.0,                     # 初始温度350K
        denc=get_denc,                         # 体积热容（空间分布函数）
        s=get_s,                               # 初始饱和度（空间分布函数）
        perm=get_perm,                         # 渗透率（空间分布函数）
        heat_cond=2.0,                         # 热传导系数2.0 W/(mK)
        dist=0.2,                              # 热扩散率
        has_solid=False,                       # 不单独考虑固体相
        dt_max=3600.0 * 24.0 * 10.0,           # 最大时间步长10天
        gravity=[0, 0, -10],                   # 重力加速度（z方向-10 m/s^2）
        gr=gr,                                 # 渗透率曲线
        default_kr=default_kr,                 # 默认相对渗透率曲线
        injectors=injectors,                   # 加热器定义
        prods=prods,                           # 生产井定义
        texts={'solve': solve},                # 传递给求解器的额外文本参数
    )
    # 返回模型
    return model


def main():
    """
    主函数：创建ICP xz二维模型并执行求解。
    默认参数：加热5年，总时长8年，加热功率5kW。
    显示范围：x方向[-3,3]m（但实际因模型限制只显示有效范围），z方向[-15,15]m。
    """
    model = create()                          # 创建模型
    # 求解模型并实时显示xz剖面的温度、压力和饱和度分布
    icp.solve(model=model, extra_plot=lambda: icp.show_xz(model, caption='当前状态', yr=[-3, 3], zr=[-15, 15]))


if __name__ == '__main__':
    # 通过GUI执行主函数；--no-gui参数用于无图形界面运行
    gui.execute(main, close_after_done=False)
