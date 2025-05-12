import warnings

try:
    import numpy as np
except ImportError:
    np = None
import pyqtgraph as pg
import pyqtgraph.colormap as pgc


def from_matplotlib(name='coolwarm'):
    """
    关于matplotlib内置的colormap，参考：
        https://matplotlib.org/stable/tutorials/colors/colormaps.html
    """
    try:
        return pgc.get(name, source='matplotlib')
    except Exception as e:
        warnings.warn(f'{e}, please update the pyqtgraph! ', UserWarning)
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # 红色、绿色、蓝色
        return pg.ColorMap(np.linspace(0, 1, len(colors)), colors)


def coolwarm():
    return from_matplotlib('coolwarm')


def jet():
    return from_matplotlib('jet')


if __name__ == '__main__':
    print(jet())
