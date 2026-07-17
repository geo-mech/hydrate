# ** desc = '纵向二维。浮力作用下气体运移、水合物成藏过程模拟（采用均匀的模型）'
"""
物理问题描述：本模型模拟甲烷气体在浮力作用下向上运移并形成水合物的成藏过程。
与form.py不同，本模型采用均匀渗透率场（无高渗通道），
初始气源区位于模型底部（x=150m, z=10m），半径为50m的圆形区域。
建模方法：采用纵向二维模型（x-z平面），均匀渗透率1e-15 m²模拟低渗透地层。
初始气源区孔隙度设为0.5（高于围岩的0.1），模拟气源层的高孔隙特性。
边界条件：上下边界设为绝热封闭，其余为封闭边界。
关键参数：渗透率均匀1e-15 m²，孔隙度在气源区为0.5/围岩为0.1。
最大模拟时间100年（time_max=100*365*24*3600s）。
"""

from zmlx import *


def create(jx=150, jz=250):
    """
    创建均匀渗透率的甲烷水合物成藏模型。

    构建一个纵向二维模型，初始气源区位于底部（z=10m），
    渗透率全场均匀（1e-15 m²），气源区孔隙度高于围岩。

    参数:
        jx (int): x方向网格数，默认150。
        jz (int): z方向网格数，默认250。

    返回:
        Seepage: 创建的均匀模型水合物成藏模型对象。
    """
    assert np is not None
    mesh = create_cube(  # 创建矩形网格，模型范围：x=0~300m, z=0~500m
        x=np.linspace(0, 300, jx + 1),
        y=(-0.5, 0.5),
        z=np.linspace(0, 500, jz + 1))

    def get_t(x, y, z):  # 初始温度：按地温梯度计算
        return 278 + 22.15 - 0.0443 * z

    def get_p(x, y, z):  # 初始压力：静水压力，参考压力16MPa
        return 11e6 + 5e6 - 1e4 * z

    def is_gas_region(x, y, z):  # 判断是否在初始气源区内
        return get_distance((x, z), (150, 10)) < 50  # 以(150,10)为中心，半径50m圆形区域

    def get_s(*pos):  # 初始饱和度：气源区为纯CH4，其余为纯水
        return {'ch4': 1} if is_gas_region(*pos) else {'h2o': 1}

    z0, z1 = mesh.get_pos_range(2)  # 获取z方向范围

    def get_denc(x, y, z):  # 体积热容，单位J/(m^3*K)
        if abs(z - z0) < 0.1 or abs(z - z1) < 0.1:
            return 1.0e20  # 边界绝热
        else:
            return 1.0e6

    def get_k(x, y, z):  # 全场均匀渗透率
        return 1.0e-15  # 低渗透率，单位m²

    def get_porosity(*pos):  # 非均匀孔隙度：气源区0.5，围岩0.1
        return 0.5 if is_gas_region(*pos) else 0.1

    model = hydrate.create(
        has_inh=True,  # 存在抑制剂（盐分）
        has_ch4_in_liq=True,  # CH4可溶于液相
        gravity=[0, 0, -10],  # 重力加速度，单位m/s²
        mesh=mesh,
        porosity=get_porosity,
        pore_modulus=100e6,  # 孔隙体积模量，单位Pa
        denc=get_denc,
        dist=0.1,
        temperature=get_t, p=get_p, s=get_s,
        perm=get_k, heat_cond=2.0, dt_max=3600 * 24 * 30  # 最大时间步长30天
    )
    return model


def show(model: Seepage, jx, jz, caption=None):
    """
    显示均匀渗透率水合物成藏模型的可视化结果。

    在模型上叠加显示初始气源区半圆形边界（红色虚线），
    帮助对比气体运移范围与初始气源位置的关系。

    参数:
        model (Seepage): 水合物模型对象。
        jx (int): x方向网格数。
        jz (int): z方向网格数。
        caption (str, optional): 图表标题。
    """
    assert np is not None
    angles = np.linspace(0, np.pi, 100)
    c1 = item('xy', np.cos(angles) * 50 + 150, np.sin(angles) * 50 + 10, 'r--')  # 初始气源区边界
    hydrate.show_2d_v2(
        model, dim0=0, dim1=2, shape=[jx, jz], caption=caption, other_items=[c1]
    )


def main():
    """
    主入口函数。

    创建均匀渗透率模型（50x100网格），执行求解，最大模拟时间100年。
    使用GUI界面交互执行，可通过--no-gui参数禁用GUI。
    """
    jx, jz = 50, 100
    model = create(jx, jz)
    hydrate.solve(model=model, extra_plot=lambda: show(model, jx, jz),
                  time_max=100 * 365 * 24 * 3600)  # 最大模拟时间100年


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
