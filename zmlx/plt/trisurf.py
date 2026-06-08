import zmlx.alg.sys as warnings
from zmlx.plt.on_ui import show_trisurf as plot_trisurf

warnings.warn(f'The module {__name__} will be removed after 2027-5-23',
              DeprecationWarning, stacklevel=2)


def test():
    from zmlx.data.surf import get_data
    x, y, z, _ = get_data(jx=40, jy=20, xr=(-5, 5), yr=(-3, 3))
    plot_trisurf(x.flatten(), y.flatten(), z.flatten(), cbar={}, cmap='viridis')


if __name__ == '__main__':
    test()
