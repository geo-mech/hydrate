from zmlx.plt.on_axes import add_field2
from zmlx.plt.on_figure import plot_on_figure, AutoLayout


def show_flu_def(flu, pr, tr, **opts):
    """
    显示流体定义： 密度和粘性系数的变化.
    """

    def f(figure):
        layout = AutoLayout(figure, 2, 1.0, xlabel='Pressure (Pa)', ylabel='Temperature (K)')
        layout.add_axes2(add_field2, flu.den, pr, tr,
                         cbar=dict(label='Density'), cmap='viridis', title='Density', )
        layout.add_axes2(add_field2, flu.vis, pr, tr,
                         cbar=dict(label='Viscosity'), cmap='coolwarm', title='Viscosity', )
        figure.suptitle(f'Fluid: name={flu.name}, specific_heat={flu.specific_heat:.1f}')

    opts.setdefault('caption', f'fluid: {flu.name}')
    opts.setdefault('tight_layout', True)
    plot_on_figure(f, **opts)


def test():
    from zmlx.fluid import create_ch4
    show_flu_def(create_ch4(), [4e6, 15e6], [274, 290], gui_mode=True)


if __name__ == '__main__':
    test()
