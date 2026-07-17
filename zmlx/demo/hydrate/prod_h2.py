# ** desc = '水平方向二维的水合物开发过程'
#
# 物理问题描述：
#   本模型模拟水平方向（x-y平面）二维天然气水合物藏的开采过程。
#   储层为一个矩形区域，初始水合物饱和度为0.4，初始压力10 MPa，
#   初始温度285 K。采用降压开采方式，在模型中心设置一口生产井，
#   井底流压维持在3 MPa。
#
# 建模方法：
#   使用create_cube构建二维矩形网格（x-y平面），z方向仅1层薄网格。
#   通过add_cell_face在中心添加一个虚拟的大体积cell模拟生产井，
#   该cell的z > 1，具有固定的低压（3 MPa）。边界cell设置极高的
#   孔隙度（1e6）和热容量（1e20）以固定边界压力（10 MPa）和
#   温度（285 K）。生产井cell同样设置高孔隙度以模拟井筒的大容积。
#   重力设置为零（水平二维模型），CFL数为0.1以保证数值稳定性。
#
# 关键参数说明：
#   网格：x方向[-70, 70]范围内70个网格，y方向[-50, 50]范围内50个网格
#   初始水合物饱和度：0.4（储层区域）
#   初始压力：10 MPa，生产压力：3 MPa
#   初始温度：285 K
#   渗透率：1e-14 m^2
#   孔隙度：0.3（储层区域）
#   模拟时间步长：最小1秒，最大10天

from zmlx import *


def create(jx, jy, xr=None, yr=None):
    """
    创建水平方向二维的水合物降压开采模型。

    参数:
        jx (int): x方向的网格单元数
        jy (int): y方向的网格单元数
        xr (tuple, optional): x方向的范围 (min, max)，默认为 (-50, 50)
        yr (tuple, optional): y方向的范围 (min, max)，默认为 (-50, 50)

    返回:
        Seepage: 创建完成的渗流模型，可用于后续的求解计算
    """
    assert np is not None
    if xr is None:
        xr = (-50, 50)
    if yr is None:
        yr = (-50, 50)
    # 创建二维矩形网格（z方向仅1层，厚度2m）
    mesh = create_cube(x=np.linspace(*xr, jx + 1), y=np.linspace(*yr, jy + 1), z=(-1, 1))

    # 添加虚拟的cell和face用于生产（位于中心，z > 1，模拟井筒）
    add_cell_face(mesh, pos=[0, 0, 0], offset=[0, 0, 5], vol=1.0e6,
                  area=5, length=1)

    # 获取网格在x和y方向的范围，用于识别边界单元
    x_min, x_max = mesh.get_pos_range(0)
    y_min, y_max = mesh.get_pos_range(1)

    def boundary(x, y, z):
        """判断是否为边界单元（位于网格四周边界上）"""
        return abs(x - x_min) < 1e-3 or abs(x - x_max) < 1e-3 or abs(
            y - y_min) < 1e-3 or abs(y - y_max) < 1e-3

    def is_prod(x, y, z):
        """判断是否为生产井单元（z > 1的虚拟cell）"""
        return z > 1

    def get_s(*args):
        """
        设置各区域的初始饱和度。
        生产井区域：纯水；储层区域：含水0.6 + 水合物0.4
        """
        if is_prod(*args):
            return {'h2o': 1}
        else:
            return {'h2o': 1, 'ch4_hydrate': 0.4}

    def heat_cond(x, y, z):
        """设置热导率：储层区域1.0，生产井区域0.0（防止热量从井筒传入）"""
        return 1.0 if abs(z) < 1 else 0.0

    # 调用hydrate.create组装完整的渗流模型
    return hydrate.create(
        gravity=[0, 0, 0],       # 水平二维模型，忽略重力
        mesh=mesh,
        # 边界和生产井的孔隙度设为大值以固定压力/温度条件
        porosity=lambda *args: 1e6 if boundary(*args) or is_prod(*args) else 0.3,
        pore_modulus=100e6,      # 孔隙模量 100 MPa
        denc=lambda *args: 1e20 if boundary(*args) else 5e6,  # 边界高密度以固定温度
        temperature=285.0,       # 初始温度 285 K (约12°C)
        p=lambda *args: 3e6 if is_prod(*args) else 10e6,  # 生产井3 MPa，储层10 MPa
        s=get_s,
        perm=1e-14,              # 储层渗透率 1e-14 m^2
        heat_cond=heat_cond,
        dt_min=1,                # 最小时间步长 1 秒
        dt_max=24 * 3600 * 10,   # 最大时间步长 10 天
        cfl=0.1                  # CFL数，控制数值稳定性
    )


def show(model: Seepage, jx, jy, caption=None):
    """
    显示模型的二维云图。

    参数:
        model: 渗流模型
        jx (int): x方向网格数
        jy (int): y方向网格数
        caption (str, optional): 图像标题
    """
    hydrate.show_2d_v2(model, shape=(jx, jy), dim0=0, dim1=1, zr=[-1, 1], caption=caption)


def main():
    """
    主函数：创建模型并启动求解。
    网格规模70x50，求解过程中实时显示二维云图。
    """
    jx, jy = 70, 50
    model = create(jx, jy, xr=[-70, 70], yr=[-50, 50])
    # 启动求解，每个时间步后调用show函数显示更新后的状态
    hydrate.solve(model, extra_plot=lambda: show(model, jx, jy))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
