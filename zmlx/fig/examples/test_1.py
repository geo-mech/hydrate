from zmlx.fig import *


def test_1():
    from zmlx.data.surf import get_data
    x, y, z, v = get_data(jx=40, jy=20, xr=(-5, 5), yr=(-3, 3))
    v0 = v.min()
    v1 = v.max() + 1
    items = [
        surf(x, y, z, v, clim=(v0, v1), cmap='jet'),
        surf(x + 10, y, z + 1, v + 1,
             clim=(v0, v1), alpha=v + 1, cmap='jet'),
        cbar(clim=(v0, v1), label='Hehe', shrink=0.5, cmap='jet')
    ]
    plot3d(*items)


if __name__ == '__main__':
    test_1()
