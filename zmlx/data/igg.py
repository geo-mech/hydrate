import os.path

from zmlx.alg.image import get_data


def load_igg(vmin=0.0, vmax=1.0, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0):
    """
    加载igg.png图片
    Args:
        vmin: 图片中最小值对应的数值
        vmax: 图片中最大值对应的数值
        xmin: 图片中x轴的最小值
        xmax: 图片中x轴的最大值
        ymin: 图片中y轴的最小值
        ymax: 图片中y轴的最大值

    Returns:
        一个函数，输入为(x, y)，输出为图片中对应位置的数值
    """
    img = os.path.join(os.path.dirname(__file__), 'igg.png')
    cmap = [[255, 255, 255, 1], [0, 0, 255, 1]]
    f = get_data(img=img, cmap=cmap, vmin=vmin, vmax=vmax, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
    return f


def test():
    from zmlx.ui import plot
    import numpy as np
    f = load_igg()
    x = np.linspace(0, 1, 100)
    y = np.linspace(0, 1, 100)
    x, y = np.meshgrid(x, y)
    z = f(x, y)

    def on_figure(fig):
        ax = fig.add_subplot()
        obj = ax.contourf(x, y, z)
        fig.colorbar(obj)
        ax.set_aspect('equal')

    plot(on_figure, gui_mode=True)


if __name__ == '__main__':
    test()
