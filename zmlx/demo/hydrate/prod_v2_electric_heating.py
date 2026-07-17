# ** desc = '水合物开发：电加热 + 降压，固定相对渗透率。竖直二维剖面，先电加热分解水合物，再降压产气。'

from zmlx import *
from zmlx.seepage_mesh.hydrate import create_xz


def create():
    """
    创建模型：50m × 100m 的竖直二维剖面，中心为水合物储层（厚 40m），
    上下被低渗透盖层/底层包围。采用固定相对渗透率曲线。
    """
    # 创建竖直二维网格：x方向0~50m, z方向-100~0m, 网格间距1m
    mesh = create_xz(x_max=50, z_min=-100, z_max=0, dx=1, dz=1, upper=30,
                     lower=30)

    # 在 (0, 0, -50) 处添加虚拟Cell/Face，用于连接生产井
    add_cell_face(mesh, pos=[0, 0, -50], offset=[0, 10, 0], vol=1000,
                  area=5, length=1)

    z_min, z_max = mesh.get_pos_range(2)

    def is_upper(x, y, z):
        """顶部边界"""
        return abs(z - z_max) < 0.01

    def is_lower(x, y, z):
        """底部边界"""
        return abs(z - z_min) < 0.01

    def is_prod(x, y, z):
        """生产井附近"""
        return abs(y - 10) < 0.1

    def get_s(x, y, z):
        """初始饱和度分布：储层含 40% 水合物，其余区域纯水"""
        if is_prod(x, y, z) or z > -30 or z < -70:
            return {'h2o': 1}
        else:
            return {'h2o': 0.6, 'ch4_hydrate': 0.4}

    def get_k(x, y, z):
        """渗透率分布：盖层/底层为低渗屏障，储层为高渗"""
        if z > -30 or z < -70:
            return Tensor3(xx=1.0e-15, yy=1.0e-15, zz=0.3e-15)
        else:
            return Tensor3(xx=1.0e-14, yy=1.0e-14, zz=1.0e-15)

    def get_p(x, y, z):
        """初始静水压力分布，12MPa 为顶面参考压力"""
        return 12e6 - z * 1e4

    def get_t(x, y, z):
        """初始温度分布，285K 为顶面参考温度，地温梯度 0.04 K/m"""
        return 285 - z * 0.04

    def denc(*pos):
        """岩石密度×比热：盖层/底层设为极大值以实现恒温边界"""
        return 1e20 if is_upper(*pos) or is_lower(*pos) else 5e6

    def get_fai(x, y, z):
        """孔隙度：顶部设为极大值以实现定压边界"""
        if is_upper(x, y, z):
            return 1.0e10
        else:
            return 0.3

    def heat_cond(x, y, z):
        """导热系数：仅在井附近导热，防止热量通过虚拟Cell泄漏"""
        return 1.0 if abs(y) < 2 else 0.0

    # 创建水合物模型（包含 CH4、H2O、CH4水合物三相）
    model = hydrate.create(
        gravity=[0, 0, -10],   # 重力方向（z轴负方向）
        dt_min=1,              # 最小时间步长 1s
        dt_max=24 * 3600,      # 最大时间步长 1 天
        cfl=0.1,               # CFL 数（控制时间步长）
        mesh=mesh,             # 计算网格
        porosity=get_fai,      # 孔隙度
        pore_modulus=100e6,    # 孔隙弹性模量
        denc=denc,             # 体积热容
        temperature=get_t,     # 初始温度
        p=get_p,               # 初始压力
        s=get_s,               # 初始饱和度
        perm=get_k,            # 渗透率
        heat_cond=heat_cond,   # 导热系数
        prods=[{'index': mesh.cell_number - 1,  # 生产井设置在虚拟Cell上
                't': [0, 1e20],                   # 始终开启
                'p': [3e6, 3e6]}]                 # 井底流压 3MPa
    )

    # 启用以CFL约束自动调整时间步长
    model.add_tag("check_dt")

    # 配置监控：记录生产井所在Cell的状态
    model.set_text(
        key='solve',
        text={'monitor': {'cell_ids': [model.cell_number - 1]}}
    )

    return model


def electric_heating(model: Seepage, time_forward=30.0 * 24 * 3600, folder=None,
                     power=500.0):
    """
    电加热阶段：关闭生产井，在井位置以恒功率注入热量。

    使用 add_injector 但不设置 fluid_id，即为纯热注入（点加热）。

    Args:
        model: 水合物模型
        time_forward: 加热持续时长（秒），默认 30 天
        folder: 自动保存目录（可选）
        power: 加热功率（W），默认 500W
    """
    # 关闭虚拟Face，隔离生产井
    virtual_face = model.get_face(-1)
    assert virtual_face is not None
    perm_backup = virtual_face.get_attr('perm')
    tfc.set_face(virtual_face, perm=0.0, heat_cond=0.0)

    # 获取生产井所在Cell作为加热位置（与注热水版本一致）
    target_id = min(virtual_face.get_cell(0).index, virtual_face.get_cell(1).index)

    # 获取 Cell 属性键（这些键在 hydrate.create 中已创建）
    ca_mc = model.get_cell_key('mc')
    ca_t = model.get_cell_key('temperature')
    assert ca_mc is not None and ca_t is not None

    # 添加点加热：add_injector 不设置 fluid_id 时，
    #   根据 ca_mc（热容）和 ca_t（温度）注入纯热量，不注入物质。
    #   恒功率模式（不设 g_heat）：value 为加热功率 (W)。
    #   恒温模式（设 g_heat>0）：opers 控制温度。
    inj_n_backup = model.injector_number
    model.add_injector(
        cell=target_id,
        ca_mc=ca_mc,           # Cell 热容属性键 (mass × specific_heat)
        ca_t=ca_t,             # Cell 温度属性键
        value=power            # 加热功率 (W)
    )

    # 运行加热模拟
    hydrate.solve(model,
                  extra_plot=lambda: hydrate.show_2d_v2(model, yr=[-1, 1], dim0=0, dim1=2),
                  time_forward=time_forward, folder=folder)

    # 恢复：移除所有加热点，恢复虚拟Face的原始渗透率
    model.injector_number = inj_n_backup
    tfc.set_face(virtual_face, perm=perm_backup, heat_cond=0.0)
    tfc.set_dt(model, 1.0e-3)


def gas_production(model: Seepage, folder=None, time_forward=3 * 365 * 24 * 3600):
    """
    降压生产阶段：打开生产井，通过 3MPa 的井底流压驱动气体产出。

    Args:
        model: 已完成加热的水合物模型
        time_forward: 生产持续时长（秒），默认 3 年
        folder: 自动保存目录（可选）
    """
    hydrate.solve(model,
                  extra_plot=lambda: hydrate.show_2d_v2(model, yr=[-1, 1], dim0=0, dim1=2),
                  time_forward=time_forward,
                  folder=folder)


def main(folder=None, heat_time=30.0 * 24 * 3600, prod_time=3 * 365 * 24 * 3600):
    """
    主流程：创建模型 → 电加热 → 降压生产。

    Args:
        folder: 自动保存目录（可选）
        heat_time: 电加热时长（秒），默认 30 天
        prod_time: 降压生产时长（秒），默认 3 年
    """
    model = create()
    electric_heating(model, folder=folder, time_forward=heat_time)
    gas_production(model, folder=folder, time_forward=prod_time)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='水合物开发：电加热 + 降压（固定相对渗透率）')
    parser.add_argument('--no-gui', action='store_true', help='非 GUI 模式运行')
    parser.add_argument('--heat-time', type=float, default=100.0,
                        help='电加热时长（天），默认 100')
    parser.add_argument('--prod-time', type=float, default=3 * 365,
                        help='降压生产时长（天），默认 3 年')
    parser.add_argument('--power', type=float, default=500.0,
                        help='加热功率（W），默认 500')
    args = parser.parse_args()

    heat_time = args.heat_time * 24 * 3600
    prod_time = args.prod_time * 24 * 3600

    gui.execute(main, kwargs={'heat_time': heat_time, 'prod_time': prod_time},
                disable_gui=args.no_gui, close_after_done=False)
