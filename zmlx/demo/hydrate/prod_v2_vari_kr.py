# ** desc = '竖直方向二维的水合物开发过程（变化相对渗透率）'
#
# 物理问题描述：
#   与prod_v2.py相同的竖直方向二维水合物降压开采模型（上覆层、水合物层、
#   下伏层三层结构，生产井位于y=10处，井底流压3 MPa）。
#   核心差异：相对渗透率曲线不再是固定的，而是随水合物饱和度动态变化。
#   水合物饱和度越高，水相和气相的流动能力越低，这更加符合物理实际。
#
# 建模方法：
#   1. 根据实验数据拟合出不同水合物饱和度下，水相（krw）和气相（krg）
#      相对渗透率曲线的五次多项式系数（get_water_kr_coeffs, get_gas_kr_coeffs）。
#   2. 水合物饱和度从0到1分成51档（每0.02一档），为每一档预计算一条
#      相对渗透率曲线并存入模型（使用model.set_kr）。
#   3. 在迭代过程中，每隔一定步数调用update_ikr函数，根据当前face两侧
#      的平均水合物饱和度，查询预先存储的相渗曲线ID并设置到face上。
#   4. 通过step_iteration.add_setting注册update_ikr为每步回调函数。
#
# 关键参数说明：
#   相渗曲线存储：KRW_ID_BEG=10, KRG_ID_BEG=120作为ID起点
#   水合物饱和度分档间隔：0.02（共51档）
#   五次多项式系数：来自实验室测试数据的拟合结果
#   step_iteration：每步迭代自动调用update_ikr更新face相渗曲线

from zmlx import *
from zmlx.seepage_mesh.hydrate import create_xz


def get_water_kr_coeffs(n):
    """
    获取水相相对渗透率（krw）的五次多项式系数。

    根据当前水合物饱和度 n，从实验数据分段拟合得到六项系数 a~f，
    用于计算 krw = a*Sw^5 + b*Sw^4 + c*Sw^3 + d*Sw^2 + e*Sw + f。

    参数:
        n (float): 水合物饱和度，范围0~1

    返回:
        tuple: (a, b, c, d, e, f) 五次多项式系数
    """
    if n <= 0.007:
        return -1.701571 * n + 1.757000, 4.493143 * n - 2.083800, -4.070143 * n + 2.171300, 1.488143 * n - 1.009900, -0.192857 * n + 0.155700, 0.004714 * n - 0.004200
    elif n <= 0.076:
        return -1.421519 * n + 1.561319, 2.828152 * n - 0.917276, -2.332789 * n + 0.955357, 0.762278 * n - 0.501992, -0.102358 * n + 0.092150, 0.001893 * n - 0.002176
    elif n <= 0.307:
        return 0.235892 * n - 9.886012, -0.312232 * n + 23.619404, 0.036939 * n - 17.156839, 0.066446 * n + 5.095846, -0.024696 * n - 0.411415, 0.001684 * n - 0.002027
    elif n <= 0.363:
        return 9.486957 * n - 294.054783, -8.922609 * n + 287.196522, 7.244348 * n - 238.075652, -2.604783 * n + 87.963478, 0.363913 * n - 12.334783, -0.016957 * n + 0.574957
    elif n <= 0.421:
        return -4.610000 * n + 184.763000, 11.064483 * n - 434.506966, -9.495690 * n + 368.936966, 3.616552 * n - 138.606621, -0.572414 * n + 21.614655, 0.030569 * n - 1.132503
    else:
        return -4.022642 * n + 159.265887, 9.059007 * n - 349.084926, -7.089755 * n + 272.691489, 2.505358 * n - 96.055358, -0.323577 * n + 12.639277, 0.010934 * n - 0.394234


def get_gas_kr_coeffs(n):
    """
    获取气相相对渗透率（krg）的五次多项式系数。

    根据当前水合物饱和度 n，从实验数据分段拟合得到六项系数 a~f，
    用于计算 krg = a*Sg^5 + b*Sg^4 + c*Sg^3 + d*Sg^2 + e*Sg + f。

    参数:
        n (float): 水合物饱和度，范围0~1

    返回:
        tuple: (a, b, c, d, e, f) 五次多项式系数
    """
    if n <= 0.007:
        return 0.882857 * n + 14.010000, -2.431429 * n - 41.623000, 1.925714 * n + 44.373000, -0.717143 * n - 18.472000, 0.125000 * n + 0.723900, -0.001857 * n + 0.994600
    elif n <= 0.076:
        return -0.046441 * n + 14.050549, -0.047351 * n - 41.590802, 0.063636 * n + 44.326873, -0.028169 * n - 18.456620, 0.065736 * n + 0.761264, -0.002067 * n + 0.994644
    elif n <= 0.307:
        return 0.025103 * n + 14.164215, 0.005049 * n - 42.601373, -0.008961 * n + 46.080784, 0.001275 * n - 19.559746, 0.038370 * n + 0.915354, -0.002870 * n + 1.003237
    elif n <= 0.363:
        return -1.022857 * n + 46.491429, 2.662857 * n - 123.622857, -2.660000 * n + 109.982857, 1.183929 * n - 55.250000, -0.260536 * n + 10.733393, 0.014643 * n + 0.514286
    elif n <= 0.421:
        return 1.017857 * n - 25.821429, -2.321429 * n + 47.785714, 3.142857 * n - 86.392857, -1.803571 * n + 52.535714, 0.349643 * n - 11.822500, 0.015000 * n + 0.460000
    else:
        return 1.350000 * n - 47.630000, -2.800000 * n + 118.292000, 1.766667 * n - 35.386667, -0.666667 * n + 7.400000, -0.185000 * n + 8.698000, 0.013333 * n + 0.353333


def calc_krw(sh):
    """
    计算给定水合物饱和度下的水相相对渗透率曲线。

    通过create_kr生成标准的饱和度-相对渗透率数据对，
    然后从中提取水相(kw)的曲线数据。

    参数:
        sh (float): 水合物饱和度，范围0~1

    返回:
        tuple: (saturation_list, krw_list) 饱和度及其对应的水相相对渗透率
    """
    # 旧版实现（已弃用）：使用五次多项式直接计算
    # assert np is not None
    # a, b, c, d, e, f = get_water_kr_coeffs(n)
    # x = np.linspace(0, 1, 100).tolist()
    # y = [max(0.0, min(1.0, a * sw ** 5 + b * sw ** 4 + c * sw ** 3 + d * sw ** 2 + e * sw + f)) for sw in x]
    # return x, y

    # 使用create_kr生成默认的相渗曲线，从中提取kw
    vs, kg, kw = create_kr()
    return vs, kw


def test_1():
    """
    测试函数：绘制不同水合物饱和度下的水相相对渗透率曲线。

    验证条件：
    1. 曲线单调递增
    2. y值在0到1之间（至少大于0）
    3. 存在残余饱和度（曲线左侧一小段为0）
    """

    def on_figure(f):
        ax = add_axes2(f, xlabel='s', ylabel='kr')
        for n in [0.05, 0.1, 0.2, 0.4, 0.8, 1.0]:
            x, y = calc_krw(n)
            ax.plot(x, y, label=str(n))
        ax.legend()

    plot(on_figure)


#
# if __name__ == '__main__':
#     test_1()


def calc_krg(sh):
    """
    计算给定水合物饱和度下的气相相对渗透率曲线。

    通过create_kr生成标准的饱和度-相对渗透率数据对，
    然后从中提取气相(kg)的曲线数据。

    参数:
        sh (float): 水合物饱和度，范围0~1

    返回:
        tuple: (saturation_list, krg_list) 饱和度及其对应的气相相对渗透率
    """
    # 旧版实现（已弃用）：使用五次多项式直接计算
    # a, b, c, d, e, f = get_gas_kr_coeffs(n)
    # x = np.linspace(0, 1, 100).tolist()
    # y = [max(0.0, min(1.0, a * sw ** 5 + b * sw ** 4 + c * sw ** 3 + d * sw ** 2 + e * sw + f)) for sw in x]
    # return x, y
    vs, kg, kw = create_kr()
    return vs, kg


def test_2():
    """
    测试函数：绘制不同水合物饱和度下的气相相对渗透率曲线。

    验证条件：
    1. 曲线单调递增
    2. y值在0到1之间（至少大于0）
    3. 存在残余饱和度（曲线左侧一小段为0）
    """

    def on_figure(f):
        ax = add_axes2(f, xlabel='s', ylabel='kr')
        for n in [0.05, 0.1, 0.2, 0.4, 0.8, 1.0]:
            x, y = calc_krg(n)
            ax.plot(x, y, label=str(n))
        ax.legend()

    plot(on_figure)


# if __name__ == '__main__':
#     test_2()


# 相渗曲线在模型中的ID起始值
KRW_ID_BEG = 10   # 水相相对渗透率曲线ID的起始值
KRG_ID_BEG = 120  # 气相相对渗透率曲线ID的起始值


def get_krw_id(sh):
    """
    根据水合物饱和度sh获取对应的水相相对渗透率曲线ID。

    饱和度按0.02的间隔分档，ID = KRW_ID_BEG + round(sh / 0.02)。
    例如：sh=0 -> ID=10, sh=0.5 -> ID=35, sh=1.0 -> ID=60

    参数:
        sh (float): 水合物饱和度，范围[0.0, 1.0]

    返回:
        int: 对应的水相相对渗透率曲线ID
    """
    assert 0.0 <= sh <= 1.0, 'sh must be in [0.0, 1.0]'
    return KRW_ID_BEG + int(round(sh / 0.02))


def get_krg_id(sh):
    """
    根据水合物饱和度sh获取对应的气相相对渗透率曲线ID。

    饱和度按0.02的间隔分档，ID = KRG_ID_BEG + round(sh / 0.02)。
    例如：sh=0 -> ID=120, sh=0.5 -> ID=145, sh=1.0 -> ID=170

    参数:
        sh (float): 水合物饱和度，范围[0.0, 1.0]

    返回:
        int: 对应的气相相对渗透率曲线ID
    """
    assert 0.0 <= sh <= 1.0, 'sh must be in [0.0, 1.0]'
    return KRG_ID_BEG + int(round(sh / 0.02))


def test_3():
    """测试函数：验证get_krw_id和get_krg_id的映射关系"""
    for sh in np.linspace(0, 1, 100):
        print(sh, get_krw_id(sh), get_krg_id(sh))


# if __name__ == '__main__':
#     test_3()


def update_ikr(model: Seepage):
    """
    更新模型所有face的相对渗透率曲线。

    遍历每个face，计算其两侧cell的平均水合物饱和度，
    然后根据该饱和度查询预设的相渗曲线ID并设置到face上。

    该函数会在每步迭代中被step_iteration自动调用。

    参数:
        model (Seepage): 需要更新相渗曲线的渗流模型
    """
    # print("update_ikr")
    for face in model.faces:
        assert isinstance(face, Seepage.Face)

        # 获取当前face的平均水合物饱和度和水相饱和度
        sh = get_sh(face)

        # 根据水合物饱和度查询对应的相渗曲线ID
        i_krw = get_krw_id(sh)  # 水相相对渗透率曲线ID
        i_krg = get_krg_id(sh)  # 气相相对渗透率曲线ID

        # 将相渗曲线ID设置到face上（index 0=气相, index 1=水相）
        face.set_ikr(index=0, value=i_krg)
        face.set_ikr(index=1, value=i_krw)


def create():
    """
    创建竖直方向二维的水合物开发模型（变相渗版本）。

    与基本版本相比，本函数额外执行以下操作：
    1. 为水合物饱和度0~1范围内每0.02间隔预计算并存储相渗曲线
    2. 初始调用update_ikr设置初始相渗曲线
    3. 注册step_iteration回调，使每步迭代自动更新相渗曲线

    参数:
        无

    返回:
        Seepage: 创建完成的渗流模型，包含变相渗配置
    """
    mesh = create_xz(x_max=50, z_min=-100, z_max=0, dx=1, dz=1, upper=30,
                     lower=30)

    # 添加虚拟的cell和face用于生产（位于y=10处，模拟水平井筒）
    add_cell_face(mesh, pos=[0, 0, -50], offset=[0, 10, 0], vol=1000,
                  area=5, length=1)

    # 找到上下范围，从而去找到顶底的边界
    z_min, z_max = mesh.get_pos_range(2)

    def is_upper(x, y, z):
        """判断是否为顶部边界cell"""
        return abs(z - z_max) < 0.01

    def is_lower(x, y, z):
        """判断是否为底部边界cell"""
        return abs(z - z_min) < 0.01

    def is_prod(x, y, z):
        """判断是否为生产井cell"""
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
        """设置初始压力：10 MPa + z * (-0.01 MPa/m)"""
        return 10e6 - z * 1e4

    def get_t(x, y, z):
        """设置初始温度：285 K + z * (-0.04 K/m)"""
        return 285 - z * 0.04

    def denc(*pos):
        """设置密度乘比热容：边界为大值以固定温度边界条件"""
        return 1e20 if is_upper(*pos) or is_lower(*pos) else 5e6

    def get_fai(x, y, z):
        """
        设置孔隙度。
        顶部边界（z=z_max）设为大值1e10以固定压力边界条件。
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
        gravity=[0, 0, -10],
        dt_min=1,
        dt_max=24 * 3600,
        cfl=0.1,
        mesh=mesh,
        porosity=get_fai,
        pore_modulus=100e6,
        denc=denc,
        temperature=get_t,
        p=get_p,
        s=get_s,
        perm=get_k,
        heat_cond=heat_cond,
        prods=[{'index': mesh.cell_number - 1,
                't': [0, 1e20], 'p': [3e6, 3e6]}]
    )

    # 将相对渗透曲线放入模型：预计算所有水合物饱和度下的相渗曲线
    # 遍历0~1范围内2000个点，按0.02间隔分档存储
    id_has_been_add = set()
    for sh in np.linspace(0, 1, 2000):
        id = get_krw_id(sh)
        if id not in id_has_been_add:
            id_has_been_add.add(id)
            x, y = calc_krw(sh)
            model.set_kr(index=id, saturation=x, kr=y)

    id_has_been_add = set()
    for sh in np.linspace(0, 1, 2000):
        id = get_krg_id(sh)
        if id not in id_has_been_add:
            id_has_been_add.add(id)
            x, y = calc_krg(sh)
            model.set_kr(index=id, saturation=x, kr=y)

    # 初始更新：根据当前水合物饱和度设置face的相渗曲线
    update_ikr(model)

    # 用于solve的选项
    model.set_text(
        key='solve',
        text={'monitor': {'cell_ids': [model.cell_number - 1]},
              'time_max': 3 * 365 * 24 * 3600,  # 模拟3年
              }
    )

    # 告诉模型，在后续solve的过程中，需要每隔5步来调用一次update_ikr函数
    step_iteration.add_setting(
        model,
        step=1,
        name='update_ikr',
        args=['@model'])

    # 返回模型
    return model


def get_sh(face):
    """
    获取face两侧cell的平均水合物饱和度。

    水合物在流体组分中的索引为2（第3种流体组分），
    通过get_fluid_vol_fraction(2)获取水合物体积分数。

    参数:
        face (Seepage.Face): 需要计算平均水合物饱和度的face

    返回:
        float: face两侧cell的平均水合物饱和度
    """
    c0, c1 = face.get_cell(0), face.get_cell(1)
    assert isinstance(c0, Seepage.Cell)
    assert isinstance(c1, Seepage.Cell)
    # 水合物索引为2，获取体积分数（饱和度）
    s0 = c0.get_fluid_vol_fraction(2)
    s1 = c1.get_fluid_vol_fraction(2)
    assert s0 is not None
    assert s1 is not None
    return (s0 + s1) / 2


def test_4():
    """测试函数：输出模型所有face的相渗曲线ID和水合物饱和度"""
    model: Seepage = create()

    for face in model.faces:
        sh = get_sh(face)
        print(sh, face.get_ikr(0), face.get_ikr(1), " = ", get_krg_id(sh), get_krw_id(sh))


# if __name__ == '__main__':
#     test_4()


def main():
    """
    主函数：创建变相渗模型并启动求解。
    在求解过程中，每步迭代都会自动调用update_ikr更新相渗曲线。
    slots参数传入update_ikr函数，供求解器在需要时调用。
    """
    model = create()
    hydrate.solve(model, extra_plot=lambda: hydrate.show_2d_v2(model, yr=[-1, 1], dim0=0, dim1=2),
                  slots={'update_ikr': update_ikr}
                  )


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
