# ** desc = '竖直方向二维的水合物开发过程（并行地执行多个模型，用于测试）'
#
# 物理问题描述：
#   与prod_v2.py相同的竖直方向二维水合物降压开采模型。
#   本文件的主要目的是演示并行计算能力：同时创建多个相同模型的副本，
#   利用线程池(ThreadPool)并行推进各模型的时间步迭代，以提高计算效率。
#
# 建模方法：
#   使用create_xz创建竖直剖面网格（x方向0~50m，z方向-100~0m），
#   包含上覆层、水合物层、下伏层三层结构。
#   生产井位于y=10处，井底流压3 MPa。
#   核心差异：在main函数中通过model.get_copy()创建10个模型副本，
#   在solve函数中使用ThreadPool并行地一次迭代所有模型，
#   并使用GuiIterator控制迭代循环和可视化更新。
#
# 关键参数说明：
#   并行模型数：10个完全相同模型的副本
#   线程池：ThreadPool用于并行执行tfc.iterate
#   迭代控制：GuiIterator，外层循环最多1000步
#   cfl=0.1：相对体积变化限制，用于自适应时间步长控制
#   其他参数与prod_v2.py相同

from zmlx import *
from zmlx.scen.hydrate import show_2d_v2
from zmlx.seepage_mesh.hydrate import create_xz


def create():
    """
    创建竖直方向二维的水合物降压开采模型。

    模型包含上覆层（z=-30~0m）、水合物层（z=-70~-30m）、
    下伏层（z=-100~-70m）三层结构，生产井位于y=10处。
    压力/温度随深度线性增加，初始水合物饱和度0.4。

    参数:
        无

    返回:
        Seepage: 创建完成的渗流模型
    """
    # 创建竖直剖面网格：x方向0~50m，z方向-100~0m，网格尺寸1m
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
        生产井、上覆层（z>-30）、下伏层（z<-70）为纯水；
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
        """设置初始压力：10 MPa + z * (-0.01 MPa/m)（随深度增加）"""
        return 10e6 - z * 1e4

    def get_t(x, y, z):
        """设置初始温度：285 K + z * (-0.04 K/m)（随深度增加）"""
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
        cfl=0.1,         # 相对体积变化限制，用于自适应时间步长
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


def solve(*models):
    """
    并行求解多个模型的时间步迭代。

    使用ThreadPool线程池同时对多个模型执行tfc.iterate，
    并通过GuiIterator控制迭代步进和可视化更新。
    外层循环最多1000步，每一步都显示所有模型的当前状态。

    参数:
        *models: 可变数量的Seepage模型实例（需要同时迭代的多个模型副本）
    """
    # 创建线程池用于并行计算
    pool = ThreadPool()

    def iterate():
        """对传入的所有模型同时执行一步迭代（使用线程池并行）"""
        tfc.iterate(*models, pool=pool)

    def show_x():
        """显示所有模型当前状态的二维云图"""
        for model in models:
            show_2d_v2(model, yr=[-1, 1], dim0=0, dim1=2)

    # GuiIterator封装了迭代和显示逻辑
    it = GuiIterator(iterate, show_x)
    for step in range(1000):
        it()  # 执行一步迭代并更新显示
        print(f'step = {step}')


def main():
    """
    主函数：创建模型并启动并行求解。
    通过model.get_copy()创建10个模型副本，然后并行推进迭代。
    """
    model = create()
    # 创建10个模型副本用于并行计算
    models = [model.get_copy() for i in range(10)]
    solve(*models)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
