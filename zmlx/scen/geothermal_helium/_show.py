from zmlx import tfc, Seepage, plt


def show_xz(model: Seepage):
    mask = tfc.get_cell_mask(model, yr=[-1, 1])
    ca = tfc.cell_keys(model)

    # 提取坐标
    x = tfc.get_x(model, mask=mask)
    z = tfc.get_z(model, mask=mask)

    # 提取物理场数据
    p = tfc.get_p(model, mask=mask)
    t = tfc.get_t(model, mask=mask)


    # 获取氦气的质量
    he_mass = tfc.get_m(model, fid='he',mask=mask)

    # ================= 绘图函数区 =================
    def f_p(fig):
        ax = plt.add_axes2(fig, aspect='equal', xlabel='x (m)', ylabel='z (m)', title='Pressure Field')
        plt.add_tricontourf(ax, x, z, p / 1e6, cbar=dict(label='Pressure (MPa)'))

    def f_t(fig):
        ax = plt.add_axes2(fig, aspect='equal', xlabel='x(m)', ylabel='z(m)', title='Temperature Field')
        plt.add_tricontourf(ax, x, z, t, cbar=dict(label='Temperature (K)'))

    def f_he_mass(fig):
        ax = plt.add_axes2(fig, aspect='equal', xlabel='x(m)', ylabel='z(m)', title='he_mass Field ')
        plt.add_tricontourf(ax, x, z, he_mass, cbar=dict(label='he_mass (kg)'))



    # ================= 输出面板区 =================
    plt.plot_on_figure(f_p, caption='Pressure')
    plt.plot_on_figure(f_t, caption='Temperature')
    plt.plot_on_figure(f_he_mass, caption='he_mass Field ')
