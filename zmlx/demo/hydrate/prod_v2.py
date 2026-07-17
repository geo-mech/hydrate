# ** desc = '竖直方向二维的水合物开发过程'
#
# 物理问题描述：
#   本模型模拟竖直方向（x-z剖面）二维天然气水合物藏的开采过程。
#   模型包含三个地层：上覆层（z: -30~0 m）、水合物层（z: -70~-30 m）、
#   下伏层（z: -100~-70 m）。初始水合物仅存在于水合物层，饱和度为0.4。
#   采用降压开采，生产井位于模型中部（y方向偏移10 m处），井底流压3 MPa。
#   压力随深度线性增加（10 MPa + z * 0.01 MPa/m，z为负值），
#   温度也随深度线性增加（285 K - z * 0.04 K/m）。
#
# 建模方法：
#   使用create_xz创建竖直剖面网格，x方向0~50 m，z方向-100~0 m，
#   网格尺寸1 m x 1 m。上覆层和下伏层厚度各30 m。
#   通过add_cell_face在y方向偏移10 m处添加虚拟大体积cell模拟生产井。
#   上覆层和下伏层渗透率较低（1e-15 m^2，作为隔层），水合物层
#   渗透率较高（1e-14 m^2）。边界设置为高孔隙度/高密度以固定P/T。
#   重力设置为z方向-10 m/s^2。
#
# 关键参数说明：
#   网格范围：x=0~50 m, z=-100~0 m, dx=dz=1 m
#   初始水合物饱和度：0.4（水合物层），上/下伏层为纯水
#   初始压力：10 MPa + z * (-0.01 MPa/m)（随深度增加）
#   生产压力：3 MPa（恒定）
#   初始温度：285 K + z * (-0.04 K/m)（随深度增加）
#   渗透率：水合物层1e-14 m^2，上下隔层1e-15 m^2
#   孔隙度：0.3（储层区域），顶部边界设为大值以固定压力
#   模拟时间：3年

from zmlx import *
from zmlx.seepage_mesh.hydrate import create_xz


def create():
    """
    创建竖直方向二维的水合物降压开采模型。

    模型包含上覆层、水合物层、下伏层三层结构，生产井位于模型中部。

    参数:
        无

    返回:
        Seepage: 创建完成的渗流模型，包含3年模拟的配置信息
    """
    # 创建竖直剖面网格：x方向0~50m，z方向-100~0m，网格尺寸1m
    # upper=30表示上覆层厚度30m，lower=30表示下伏层厚度30m
    mesh = create_xz(x_max=50, z_min=-100, z_max=0, dx=1, dz=1, upper=30,
                     lower=30)

    # 添加虚拟的cell和face用于生产（位于y=10处，模拟水平井筒）
    add_cell_face(mesh, pos=[0, 0, -50], offset=[0, 10, 0], vol=1000,
                  area=5, length=1)

    # 找到上下范围，从而去找到顶底的边界
    z_min, z_max = mesh.get_pos_range(2)

    def is_upper(x, y, z):
        """判断是否为顶部边界cell（z接近z_max）"""
        return abs(z - z_max) < 0.01

    def is_lower(x, y, z):
        """判断是否为底部边界cell（z接近z_min）"""
        return abs(z - z_min) < 0.01

    def is_prod(x, y, z):
        """判断是否为生产井cell（y接近10）"""
        return abs(y - 10) < 0.1

    def get_s(x, y, z):
        """
        设置各区域的初始饱和度。
        生产井区域、上覆层（z>-30）、下伏层（z<-70）为纯水；
        水合物层（-70<=z<=-30）含0.4水合物和0.6水。
        """
        if is_prod(x, y, z) or z > -30 or z < -70:
            return {'h2o': 1}
        else:
            return {'h2o': 0.6, 'ch4_hydrate': 0.4}

    def get_k(x, y, z):
        """
        设置渗透率。
        上覆层和下伏层为低渗透隔层（1e-15 m^2）；
        水合物层为储层（1e-14 m^2）。
        """
        if z > -30 or z < -70:
            return 1.0e-15
        else:
            return 1.0e-14

    def get_p(x, y, z):
        """
        设置初始压力（随深度线性增加）。
        公式：p = 10e6 - z * 1e4，z为负值，深度越大压力越高。
        """
        return 10e6 - z * 1e4

    def get_t(x, y, z):
        """
        设置初始温度（随深度线性增加）。
        公式：T = 285 - z * 0.04，z为负值，深度越大温度越高。
        """
        return 285 - z * 0.04

    def denc(*pos):
        """设置密度乘比热容：边界为大值以固定温度边界条件"""
        return 1e20 if is_upper(*pos) or is_lower(*pos) else 5e6

    def get_fai(x, y, z):
        """
        设置孔隙度。
        顶部边界（z=z_max）设为大值1e10以固定压力边界条件（定压边界）。
        """
        if is_upper(x, y, z):  # 顶部固定压力
            return 1.0e10
        else:
            return 0.3

    def heat_cond(x, y, z):  # 确保不会有热量通过用于生产的虚拟的cell传递过来.
        """
        设置热导率。
        生产井附近区域（|y|<2）为1.0，其余区域为0.0，
        防止热量通过虚拟生产井cell传导。
        """
        return 1.0 if abs(y) < 2 else 0.0

    # 关键词 — 组装完整模型
    model = hydrate.create(
        gravity=[0, 0, -10],     # z方向重力加速度 10 m/s^2
        dt_min=1,                # 最小时间步长 1 秒
        dt_max=24 * 3600,        # 最大时间步长 1 天
        cfl=0.1,                 # CFL数，控制数值稳定性
        mesh=mesh,
        porosity=get_fai,
        pore_modulus=100e6,      # 孔隙模量 100 MPa
        denc=denc,
        temperature=get_t,
        p=get_p,
        s=get_s,
        perm=get_k,
        heat_cond=heat_cond,
        # 生产井定义：最后一个cell作为生产井，设定恒压3MPa从0到无限时间
        prods=[{'index': mesh.cell_number - 1,
                't': [0, 1e20], 'p': [3e6, 3e6]}]
    )
    # 用于solve的选项
    model.set_text(
        key='solve',
        text={'monitor': {'cell_ids': [model.cell_number - 1]},
              'time_max': 3 * 365 * 24 * 3600,  # 模拟3年
              }
    )
    # 返回模型
    return model


def main():
    """
    主函数：创建竖直二维水合物模型并启动求解过程。
    求解过程中实时显示x-z剖面的二维云图。
    """
    model = create()
    hydrate.solve(model, extra_plot=lambda: hydrate.show_2d_v2(model, yr=[-1, 1], dim0=0, dim1=2))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
