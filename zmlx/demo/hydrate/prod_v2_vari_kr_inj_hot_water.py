# ** desc = '竖直方向二维的水合物开发过程（变化相对渗透率，尚未实现）（注入热水之后再降压）'

from zmlx import *
from zmlx.seepage_mesh.hydrate import create_xz


def get_water_kr_coeffs(n):
    """获取水相相对渗透率五次多项式系数"""
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
    """获取气相相对渗透率五次多项式系数"""
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
    计算水的相对渗透率曲线
    """
    # assert np is not None
    # a, b, c, d, e, f = get_water_kr_coeffs(n)
    # x = np.linspace(0, 1, 100).tolist()
    # y = [max(0.0, min(1.0, a * sw ** 5 + b * sw ** 4 + c * sw ** 3 + d * sw ** 2 + e * sw + f)) for sw in x]
    # return x, y

    vs, kg, kw = create_kr()
    return vs, kw


def test_1():
    """
    一定是：1、单调递增的；2、y应该是0到1之间（至少是大于0）；3、应该有一个残余饱和度（曲线的左侧一小节，应该等于0）
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
    # a, b, c, d, e, f = get_gas_kr_coeffs(n)
    # x = np.linspace(0, 1, 100).tolist()
    # y = [max(0.0, min(1.0, a * sw ** 5 + b * sw ** 4 + c * sw ** 3 + d * sw ** 2 + e * sw + f)) for sw in x]
    # return x, y
    vs, kg, kw = create_kr()
    return vs, kg


def test_2():
    """
    一定是：1、单调递增的；2、y应该是0到1之间（至少是大于0）；3、应该有一个残余饱和度（曲线的左侧一小节，应该等于0）
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


KRW_ID_BEG = 10
KRG_ID_BEG = 120


def get_krw_id(sh):
    assert 0.0 <= sh <= 1.0, 'sh must be in [0.0, 1.0]'
    return KRW_ID_BEG + int(round(sh / 0.02))


def get_krg_id(sh):
    assert 0.0 <= sh <= 1.0, 'sh must be in [0.0, 1.0]'
    return KRG_ID_BEG + int(round(sh / 0.02))


def test_3():
    for sh in np.linspace(0, 1, 100):
        print(sh, get_krw_id(sh), get_krg_id(sh))


# if __name__ == '__main__':
#     test_3()


def update_ikr(model: Seepage):
    """
    更新所有face的相对渗透率曲线
    """
    # print("update_ikr")
    for face in model.faces:
        assert isinstance(face, Seepage.Face)

        # 获取当前face的平均水合物饱和度和水相饱和度
        sh = get_sh(face)

        i_krw = get_krw_id(sh)
        i_krg = get_krg_id(sh)

        face.set_ikr(index=0, value=i_krg)
        face.set_ikr(index=1, value=i_krw)


def create():
    """
    创建模型
    """
    mesh = create_xz(x_max=50, z_min=-100, z_max=0, dx=1, dz=1, upper=30,
                     lower=30)

    # 添加虚拟的cell和face用于生产
    add_cell_face(mesh, pos=[0, 0, -50], offset=[0, 10, 0], vol=1000,
                  area=5, length=1)

    # 找到上下范围，从而去找到顶底的边界
    z_min, z_max = mesh.get_pos_range(2)

    def is_upper(x, y, z):
        return abs(z - z_max) < 0.01

    def is_lower(x, y, z):
        return abs(z - z_min) < 0.01

    def is_prod(x, y, z):
        return abs(y - 10) < 0.1

    def get_s(x, y, z):
        if is_prod(x, y, z) or z > -30 or z < -70:
            return {'h2o': 1}
        else:
            return {'h2o': 0.6, 'ch4_hydrate': 0.4}

    def get_k(x, y, z):
        if z > -30 or z < -70:
            return Tensor3(xx=1.0e-15, yy=1.0e-15, zz=0.3e-15)   #
        else:
            return Tensor3(xx=1.0e-14, yy=1.0e-14, zz=1.0e-15)

    def get_p(x, y, z):
        return 12e6 - z * 1e4

    def get_t(x, y, z):
        return 285 - z * 0.04

    def denc(*pos):
        return 1e20 if is_upper(*pos) or is_lower(*pos) else 5e6

    def get_fai(x, y, z):
        if is_upper(x, y, z):  # 顶部固定压力
            return 1.0e10
        else:
            return 0.3

    def heat_cond(x, y, z):  # 确保不会有热量通过用于生产的虚拟的cell传递过来.
        return 1.0 if abs(y) < 2 else 0.0

    # 关键词
    model = hydrate.create(
        gravity=[0, 0, -10],
        dt_min=1,
        dt_max=24 * 3600,
        dv_relative=0.1,
        mesh=mesh,
        porosity=get_fai,
        pore_modulus=100e6,
        denc=denc,
        temperature=get_t,
        p=get_p,
        s=get_s,
        perm=get_k,
        # dist=1.0, # 单元内部，假设流体和固体没有充分接触的，导热的距离
        heat_cond=heat_cond,
        prods=[{'index': mesh.cell_number - 1,
                't': [0, 1e20], 'p': [3e6, 3e6]}]
    )

    model.add_tag("check_dt")  # 确保时间步长符合CFL的约束

    # 将相对渗透曲线放入模型
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

    # 初始更新
    update_ikr(model)

    # 用于solve的选项
    model.set_text(
        key='solve',
        text={'monitor': {'cell_ids': [model.cell_number - 1]},
              'time_max': 3 * 365 * 24 * 3600,
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
    """获取face两侧cell的平均水合物饱和度"""
    c0, c1 = face.get_cell(0), face.get_cell(1)
    assert isinstance(c0, Seepage.Cell)
    assert isinstance(c1, Seepage.Cell)
    s0 = c0.get_fluid_vol_fraction(2)
    s1 = c1.get_fluid_vol_fraction(2)
    assert s0 is not None
    assert s1 is not None
    return (s0 + s1) / 2


def test_4():
    model: Seepage = create()

    for face in model.faces:
        sh = get_sh(face)
        print(sh, face.get_ikr(0), face.get_ikr(1), " = ", get_krg_id(sh), get_krw_id(sh))


# if __name__ == '__main__':
#     test_4()


def inj_hot_water(model: Seepage, time_forward=30.0 * 24 * 3600, folder=None):
    """
    模拟30天的热水注入的过程
    """
    virtual_face = model.get_face(-1)
    assert virtual_face is not None
    perm_backup = virtual_face.get_attr('perm')
    tfc.set_face(virtual_face, perm=0.0, heat_cond=0.0)

    # 加上注入热水的条件
    target_id = min(virtual_face.get_cell(0).index, virtual_face.get_cell(1).index)
    target_cell = model.get_cell(target_id)

    fa_t = model.get_flu_key('temperature')

    flu = target_cell.get_fluid(1).get_copy()  # water
    flu.set_attr(fa_t, 273.15 + 50)

    inj_n_backup = model.injector_number
    model.add_injector(
        cell=target_id, fluid_id=1, flu=flu, value=0.3 / (24 * 3600)
    )

    t0 = tfc.get_time(model)
    time_max = t0 + time_forward
    hydrate.solve(model,
                  extra_plot=lambda: hydrate.show_2d_v2(model, yr=[-1, 1], dim0=0, dim1=2),
                  slots={'update_ikr': update_ikr},
                  time_max=time_max, folder=folder,
                  )

    # 恢复注入条件
    tfc.set_face(virtual_face, perm=perm_backup, heat_cond=0.0)
    model.injector_number = inj_n_backup
    tfc.set_dt(model, 1.0e-3)  # 重置时间步长为100ms


def gas_production(model: Seepage, folder=None):
    hydrate.solve(model,
                  extra_plot=lambda: hydrate.show_2d_v2(model, yr=[-1, 1], dim0=0, dim1=2),
                  slots={'update_ikr': update_ikr},
                  folder=folder
                  )


def main(folder=None):
    model = create()
    inj_hot_water(model, folder=folder, time_forward=100.0 * 24 * 3600)
    gas_production(model, folder=folder)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
