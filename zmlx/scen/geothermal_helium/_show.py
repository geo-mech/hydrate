from zmlx import tfc, Seepage, plt

def show_xz(model: Seepage):
    mask = tfc.get_cell_mask(model, yr=[-1, 1])
    x = tfc.get_x(model, mask=mask)
    z = tfc.get_z(model, mask=mask)
    p = tfc.get_p(model, mask=mask)
    t = tfc.get_t(model, mask=mask)

    # 绘制压力的独立函数
    def f_p(fig):
        ax = plt.add_axes2(fig, aspect='equal', xlabel='x (m)', ylabel='z (m)', title='Pressure Field')
        plt.add_tricontourf(ax, x, z, p / 1e6, cbar=dict(label='Pressure (MPa)'))

    # 绘制温度的独立函数
    def f_t(fig):
        ax = plt.add_axes2(fig, aspect='equal', xlabel='x(m)', ylabel='z(m)', title='Temperature Field')
        plt.add_tricontourf(ax, x, z, t, cbar=dict(label='Temperature (K)'))

    # 分别输出两张图
    plt.plot_on_figure(f_p, caption='Pressure')
    plt.plot_on_figure(f_t, caption='Temperature')