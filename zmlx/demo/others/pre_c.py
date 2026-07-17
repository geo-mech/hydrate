# ** desc = '天然气储层降压开发的时候的压力降低漏斗'
#
# 本示例模拟天然气储层降压开发过程中的压力降低漏斗，
# 与pre.py不同，本示例使用圆形网格（径向网格），更好地模拟
# 径向流动特征。网格由create_c10000函数生成（约10000个单元的圆盘形网格），
# 并通过seepage_mesh_rescale缩放到合适尺寸。
# 生产井位于圆盘中心，以3MPa定压生产；边界保持10MPa初始压力。
# 圆形网格的优势在于：网格分布更符合径向流动的物理特征，
# 在井点附近网格更密，可以更精确地捕捉近井地带的压力梯度。

from zmlx import *


def create():
    """
    创建一个圆形天然气降压开采的压力漏斗模型。

    使用create_c10000生成约10000个单元的圆盘形网格，然后缩放到合适尺寸。
    生产井位于圆盘中心，以3MPa定压生产；边界（圆盘外缘）保持10MPa。
    圆形网格更符合径向流动的几何特征，能更精确模拟近井地带的压力分布。

    Returns:
        返回创建的Seepage模型对象，包含圆形网格、流体定义和边界条件。
    """
    mesh = create_c10000(z=0)  # 生成约10000个单元的圆盘形网格（z=0平面）
    seepage_mesh_rescale(mesh, factor=50.0)  # 将网格放大50倍，使半径达到约50m

    r_max = 0
    # 计算网格中所有单元的最大径向距离（即圆盘半径）
    for cell in mesh.cells:
        r_max = max(r_max, get_norm(cell.pos))

    def boundary(x, y, z):
        """判断单元是否位于圆盘外缘边界"""
        return abs(r_max - get_norm([x, y])) < 1

    center = mesh.get_nearest_cell(pos=[0, 0, 0]).pos

    def is_prod(*args):
        assert len(args) == 3
        return point_distance(args, center) < 0.1

    def porosity(*args):
        """定义孔隙度：边界和生产井处设极大值以固定压力"""
        return 1e6 if boundary(*args) or is_prod(*args) else 0.3

    def denc(*args):
        """定义热容量：边界处设极大值以固定温度"""
        return 1e20 if boundary(*args) else 5e6

    def pressure(*args):
        return 3e6 if is_prod(*args) else 10e6

    # 创建模型
    model = tfc.create(
        mesh=mesh,
        fludefs=[create_ch4(name='ch4')],  # 使用CH4（甲烷）作为流体组分
        porosity=porosity,  # 函数定义：边界/生产井处大孔隙固定压力
        pore_modulus=100e6,  # 孔隙模量100MPa
        denc=denc,  # 热容量分布（边界处固定温度）
        temperature=285.0,  # 初始温度285K
        p=pressure,  # 初始压力分布函数
        s={'ch4': 1},  # 初始饱和度：100%甲烷
        perm=1e-15,  # 渗透率1e-15 m^2
        dt_min=1, dt_max=24 * 3600, cfl=0.1,  # 时间步长控制
    )
    # 用于solve的选项
    tfc.set_text(
        model,
        solve=dict(
            show_cells=dict(
                dim0=0, dim1=1, show_t=False, show_s=False  # 显示xy平面，不显示温/饱和度
            ),
            time_max=3600 * 24 * 10,  # 模拟总时长10天
        )
    )
    return model


if __name__ == '__main__':
    gui.execute(lambda: tfc.solve(create(),
              folder=opath('pressure_funnel_circular')),  # 结果保存到'pressure_funnel_circular'
              close_after_done=False)
