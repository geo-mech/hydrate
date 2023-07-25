import pyqtgraph.colormap as pgc


def from_matplotlib(name='coolwarm'):
    """
    关于matplotlib内置的colormap，参考：
        https://matplotlib.org/stable/tutorials/colors/colormaps.html
    """
    return pgc.get(name, source='matplotlib')


def coolwarm():
    return from_matplotlib('coolwarm')


def jet():
    return from_matplotlib('jet')


if __name__ == '__main__':
    print(jet())
