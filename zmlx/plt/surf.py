from zmlx.fig import *
from zmlx.fig.plt_render import add_surf

_keep = [add_surf]


def test2():
    from zmlx.plt.data.surf import get_data
    from zmlx.plt.cmap import get_cm

    x, y, z, v = get_data(jx=40, jy=20, xr=(-5, 5), yr=(-3, 3))
    v0 = v.min()
    v1 = v.max() + 1

    cmap = get_cm('jet')
    d = axes3(
        surf(x, y, z, v, clim=(v0, v1), cmap=cmap),
        surf(x + 10, y, z + 1, v + 1, clim=(v0, v1), alpha=v + 1, cmap=cmap),
        cbar(clim=(v0, v1), label='Hehe', shrink=0.5, cmap=cmap),
        title='My test'
    )
    show(d, gui_mode=True)


if __name__ == '__main__':
    test2()
