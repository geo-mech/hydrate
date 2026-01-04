from zmlx import tfc, Seepage, plt


def show_xz(model: Seepage):
    mask = tfc.get_cell_mask(model, yr=[-1, 1])
    x = tfc.get_x(model, mask=mask)
    z = tfc.get_z(model, mask=mask)
    p = tfc.get_p(model, mask=mask)

    def f(fig):
        ax = plt.add_axes2(fig, aspect='equal', xlabel='x (m)', ylabel='z (m)', title='Pressure Field')
        plt.add_tricontourf(ax, x, z, p / 1e6, cbar=dict(label='Pressure (MPa)'))

    plt.plot_on_figure(f, caption='Pressure')
