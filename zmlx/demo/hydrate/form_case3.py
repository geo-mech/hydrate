# ** desc = '纵向二维。浮力作用下气体运移、水合物成藏过程模拟（在模型的顶部设置盖层）'
"""
物理问题描述：本模型模拟甲烷气体在浮力作用下向上运移并被盖层（caprock）阻挡
后在盖层下方形成水合物藏的过程。初始气源区位于底部（x=150m, z=10m），
半径为50m的圆形区域。模型顶部设置了由余弦曲线定义的盖层边界，盖层以上渗透率为0
（完全封闭），模拟天然盖层的封堵作用。
建模方法：采用纵向二维模型（x-z平面），盖层边界由余弦函数定义：
z = cos((x-150)*pi*0.5/150) * 80 + 350。盖层以下渗透率1e-15 m²，
盖层以上渗透率为0（完全不渗透），模拟致密盖层对气体运移的阻挡作用。
气源区孔隙度0.5，围岩孔隙度0.1。
关键参数：最大模拟时间100年，时间步长限制为30天。
"""

from zmlx import *


def create(jx=150, jz=250):
    """
    创建含余弦盖层（caprock）的甲烷水合物成藏模型。

    构建一个纵向二维模型，初始气源区位于底部（z=10m），
    模型顶部设置了由余弦曲线定义的完全封闭盖层，
    研究气体被盖层阻挡后在盖层下方形成水合物藏的动态过程。

    盖层定义：z = cos((x-150)*pi*0.5/150) * 80 + 350
    即盖层高度在x方向呈拱形变化，中央最高、两端最低。

    参数:
        jx (int): x方向网格数，默认150。
        jz (int): z方向网格数，默认250。

    返回:
        Seepage: 创建的含盖层水合物成藏模型对象。
    """
    assert np is not None
    mesh = create_cube(  # 创建矩形网格，模型范围：x=0~300m, z=0~500m
        x=np.linspace(0, 300, jx + 1),
        y=(-0.5, 0.5),
        z=np.linspace(0, 500, jz + 1))

    def get_t(x, y, z):  # 初始温度：按地温梯度计算
        return 278 + 22.15 - 0.0443 * z

    def get_p(x, y, z):  # 初始压力：静水压力分布
        return 11e6 + 5e6 - 1e4 * z

    def is_gas_region(x, y, z):  # 判断是否在初始气源区内
        return get_distance((x, z), (150, 10)) < 50  # 以(150,10)为中心，半径50m

    def get_s(*pos):  # 初始饱和度：气源区为纯CH4，其余为纯水
        return {'ch4': 1} if is_gas_region(*pos) else {'h2o': 1}

    z0, z1 = mesh.get_pos_range(2)  # 获取z方向范围

    def get_denc(x, y, z):  # 体积热容，单位J/(m^3*K)
        if abs(z - z0) < 0.1 or abs(z - z1) < 0.1:
            return 1.0e20  # 边界绝热
        else:
            return 1.0e6

    def get_porosity(*pos):  # 非均匀孔隙度
        return 0.5 if is_gas_region(*pos) else 0.1

    def get_k(x, y, z):  # 渗透率分布：余弦盖层以上为0（不渗透）
        if z < np.cos((x - 150) * np.pi * 0.5 / 150) * 80 + 350:
            return 1.0e-15  # 盖层以下：低渗透率
        else:
            return 0.0  # 盖层以上：完全不渗透（caprock封闭）

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
    显示含盖层水合物成藏模型的可视化结果。

    在模型上叠加显示初始气源区半圆形边界（红色虚线）
    和余弦盖层曲线（黑色虚线），直观展示盖层对气体运移的阻挡效果。

    参数:
        model (Seepage): 水合物模型对象。
        jx (int): x方向网格数。
        jz (int): z方向网格数。
        caption (str, optional): 图表标题。
    """
    assert np is not None
    angles = np.linspace(0, np.pi, 100)
    c1 = item('xy', np.cos(angles) * 50 + 150, np.sin(angles) * 50 + 10, 'r--')  # 初始气源区边界
    vx = np.linspace(10, 290, 100)
    vy = np.cos((vx - 150) * np.pi * 0.5 / 150) * 80 + 350  # 余弦盖层曲线
    c2 = item('xy', vx, vy, 'k--')  # 盖层边界
    hydrate.show_2d_v2(
        model, dim0=0, dim1=2, shape=[jx, jz], caption=caption, other_items=[c1, c2]
    )


def main():
    """
    form_case3.py的主入口函数。

    创建含余弦盖层模型（50x100网格），执行求解并每步显示状态。
    最大模拟时间100年，可通过--no-gui参数禁用GUI。
    """
    jx, jz = 50, 100
    model = create(jx, jz)
    hydrate.solve(model=model, extra_plot=lambda: show(model, jx, jz),
                  time_max=100 * 365 * 24 * 3600)  # 最大模拟时间100年


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
