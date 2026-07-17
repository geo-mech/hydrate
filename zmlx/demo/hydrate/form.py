# ** desc = '纵向二维。浮力作用下气体运移、水合物成藏过程模拟（在模型的中间设置高渗透率的通道）'
"""
物理问题描述：本模型模拟甲烷气体（CH4）在浮力作用下向上运移并在适宜条件下
形成水合物的成藏过程。模型中心位置（x=150m, z=100m）存在一个半径为50m的
初始气源区，该区域设置为纯CH4气相。模型中部设置了一条高渗透率通道
（宽40m，渗透率1e-13 m²），模拟断裂带或高渗透层对气体运移的优先通道作用。
建模方法：采用纵向二维模型（x-z平面），使用hydrate.create()函数建立
热-流-化耦合模型。模型考虑抑制剂（盐分）的影响和CH4在水中的溶解。
边界条件：上下边界设为绝热封闭（大热容），左右和底部为封闭边界。
关键参数：jx/jz（网格数，默认150x250），模型尺寸300m x 500m。
高渗通道渗透率1e-13 m² vs 围岩渗透率1e-15 m²，相差两个数量级。
温度场按地温梯度0.0443 K/m计算，压力场按静水压力分布。
"""

from zmlx import *


def create(jx=150, jz=250):
    """
    创建含高渗透率通道的甲烷水合物成藏模型。

    构建一个纵向二维模型（x-z平面），在模型中心设置初始气源区，
    并在中部设置一条高渗透率通道（模拟断裂带），研究气体运移和水合物成藏过程。

    参数:
        jx (int): x方向网格数，默认150。
        jz (int): z方向网格数，默认250。

    返回:
        Seepage: 创建的水合物成藏模型对象。
    """
    assert np is not None
    mesh = create_cube(  # 创建矩形网格，模型范围：x=0~300m, z=0~500m
        x=np.linspace(0, 300, jx + 1),
        y=(-0.5, 0.5),  # y方向厚度为1m
        z=np.linspace(0, 500, jz + 1))

    def get_t(x, y, z):  # 初始温度分布（地温梯度0.0443 K/m，海床温度约300K）
        return 278 + 22.15 - 0.0443 * z

    def get_p(x, y, z):  # 初始压力分布（静水压力，参考压力15MPa）
        return 10e6 + 5e6 - 1e4 * z

    def is_gas_region(x, y, z):  # 判断是否在初始气源区内
        return get_distance((x, z), (150, 100)) < 50  # 以(150,100)为中心，半径50m的圆形区域

    def get_s(*pos):  # 初始饱和度：气源区为纯CH4，其余为纯水
        return {'ch4': 1} if is_gas_region(*pos) else {'h2o': 1}

    z0, z1 = mesh.get_pos_range(2)  # 获取z方向的范围

    def get_denc(x, y, z):  # 体积热容，单位J/(m^3*K)
        if abs(z - z0) < 0.1 or abs(z - z1) < 0.1:
            return 1.0e20  # 上下边界设极大值，近似绝热
        else:
            return 1.0e6  # 土体体积热容

    def get_k(x, y, z):  # 渗透率分布：中间40m宽的高渗通道
        if abs(x - 150) < 20:  # x在130-170m范围内为高渗透率通道
            return 1.0e-13  # 高渗通道（模拟断裂或高渗透层）
        else:
            return 1.0e-15  # 围岩低渗透率

    def get_porosity(*pos):  # 均匀孔隙度
        return 0.1

    model = hydrate.create(
        has_inh=True,  # 存在抑制剂（盐分）
        has_ch4_in_liq=True,  # CH4可溶解于液相
        gravity=[0, 0, -10],  # 重力加速度，单位m/s²
        mesh=mesh,
        porosity=get_porosity,
        pore_modulus=100e6,  # 孔隙体积模量，单位Pa
        denc=get_denc,
        dist=0.1,  # 初始水合物饱和度分布范围参数
        temperature=get_t, p=get_p, s=get_s,
        perm=get_k, heat_cond=2.0  # 热传导系数2.0 W/(m*K)
    )
    return model


def show(model: Seepage, jx, jz, caption=None):
    """
    显示甲烷水合物成藏模型的可视化结果。

    在模型上叠加显示初始气源区圆形边界（红色虚线）和高渗透率通道边界（黑色虚线），
    帮助对比气体运移路径与地质结构的关系。

    参数:
        model (Seepage): 水合物模型对象。
        jx (int): x方向网格数。
        jz (int): z方向网格数。
        caption (str, optional): 图表标题。
    """
    assert np is not None
    angles = np.linspace(0, np.pi * 2, 100)
    c1 = item('xy', np.cos(angles) * 50 + 150, np.sin(angles) * 50 + 100, 'r--', linewidth=0.5)  # 初始气源区边界
    c2 = item('xy', [130, 130], [10, 490], 'k--', linewidth=0.5)  # 高渗通道左边界
    c3 = item('xy', [170, 170], [10, 490], 'k--', linewidth=0.5)  # 高渗通道右边界
    hydrate.show_2d_v2(
        model, dim0=0, dim1=2, shape=[jx, jz], caption=caption, other_items=[c1, c2, c3]
    )


def main():
    """
    主入口函数。

    创建高渗通道模型并执行求解，每步迭代后显示当前状态。
    最大迭代步数为10000步。
    """
    jx, jz = 150, 250
    model = create(jx, jz)
    hydrate.solve(model=model, extra_plot=lambda: show(model, jx, jz), step_max=10000)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
