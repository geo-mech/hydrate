# ** desc = '天然气储层降压开发的时候的压力降低漏斗'
#
# 本示例模拟天然气储层在降压开发过程中形成的压力降低漏斗。
# 模型为100m×100m的二维正方形区域，采用100×100的均匀网格剖分。
# 初始储层压力为10MPa，在生产井处（中心）将压力降至3MPa进行开采。
# 边界处设置为恒压边界（大孔隙体积法），模拟无限大储层或
# 注水井保持压力的效果。
# 模拟时长为10天，使用CH4（甲烷）作为流体组分，展示了单相气体
# 在压力梯度驱动下向生产井流动的过程，以及压力降从井点向四周
# 逐渐传播所形成的漏斗状压力分布。

from zmlx import *


def create():
    """
    创建一个天然气降压开采的压力漏斗模型。

    模型采用100×100的均匀网格覆盖100m×100m的区域（-50m~50m）。
    在生产井位置（中心点）设置低压（3MPa），边界保持初始压力（10MPa），
    模拟气体在压力梯度驱动下向井流动的过程。

    边界条件：使用大孔隙体积法（孔隙度设为1e6）固定边界压力。
    生产井：同样使用大孔隙体积法固定低压，模拟定压生产。

    Returns:
        返回创建的Seepage模型对象，包含网格、流体定义、边界条件和生产井设置。
    """
    mesh = create_cube(
        x=np.linspace(-50, 50, 100),  # x方向：-50到50m，100个网格
        y=np.linspace(-50, 50, 100),  # y方向：-50到50m，100个网格
        z=(-1, 1))  # z方向厚度2m，构成二维平面模型

    x_min, x_max = mesh.get_pos_range(0)  # 获取x方向坐标范围
    y_min, y_max = mesh.get_pos_range(1)  # 获取y方向坐标范围

    def boundary(x, y, z):
        """判断单元格是否位于模型边界"""
        return abs(x - x_min) < 1e-3 or abs(x - x_max) < 1e-3 or abs(
            y - y_min) < 1e-3 or abs(y - y_max) < 1e-3

    center = mesh.get_nearest_cell(pos=[0, 0, 0]).pos

    def is_prod(*args):
        assert len(args) == 3
        return point_distance(args, center) < 0.1

    def porosity(*args):
        """定义孔隙度：边界和生产井处设为极大值以固定压力"""
        return 1e6 if boundary(*args) or is_prod(*args) else 0.3

    def denc(*args):
        """定义热容量（J/(m^3·K)）：边界处极大值以固定温度"""
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
        temperature=285.0,  # 初始温度285K（约12°C）
        p=pressure,  # 初始压力分布函数
        s={'ch4': 1},  # 初始饱和度：100%甲烷
        perm=1e-15,  # 渗透率1e-15 m^2（约1 Darcy）
        dt_min=1, dt_max=24 * 3600, cfl=0.1,  # 时间步长控制：最小1s，最大1天
    )
    # 用于solve的选项
    tfc.set_text(
        model,
        solve=dict(
            show_cells=dict(  # 绘图设置：显示xy平面
                dim0=0, dim1=1, show_t=False, show_s=False  # 不显示温度和饱和度
            ),
            time_max=3600 * 24 * 10,  # 模拟总时长10天
        )
    )
    return model


if __name__ == '__main__':
    gui.execute(lambda: tfc.solve(create(),
              folder=opath('pressure_funnel'),  # 结果保存到'pressure_funnel'文件夹
              time_unit='d'),  # 时间显示单位设为天
              close_after_done=False)
