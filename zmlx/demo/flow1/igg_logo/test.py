from zmlx import *
from zmlx.alg.image import get_data


def test():
    cmap = [[255, 255, 255, 1], [0, 0, 255, 1]]
    f = get_data(img='image.png', cmap=cmap, vmin=0.0, vmax=1.0,
                 xmin=0, xmax=1, ymin=0, ymax=1)
    x = np.linspace(0, 1, 100)
    y = np.linspace(0, 1, 100)
    X, Y = np.meshgrid(x, y)
    Z = f(X, Y)

    def on_figure(fig):
        ax = fig.add_subplot()
        obj = ax.contourf(X, Y, Z)
        fig.colorbar(obj)
        ax.set_aspect('equal')

    plot(on_figure, gui_mode=True)


if __name__ == '__main__':
    test()
