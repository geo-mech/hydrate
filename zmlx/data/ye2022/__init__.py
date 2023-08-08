"""
Ye, H., et al. (2022). "Numerical simulation of productivity improvement of natural gas hydrate with various well types
: Influence of branch parameters." Journal of Natural Gas Science and Engineering 103.

"""
from zmlx.data.ye2022.load import load, load_120

# 原始数据，徐涛整理的，深度100米
data = load()

# 总共包含120深度的数据
data120 = load_120()

__all__ = ['data', 'data120']


def plot_all(data):
    from zmlx.plt.plotxy import plotxy
    import numpy as np
    plotxy(data.t2rate[:, 0] / (3600 * 24), data.t2rate[:, 1] * (3600 * 24) / 0.7, caption='gas_rate')
    plotxy(data.t2pre[:, 0] / (3600 * 24), data.t2pre[:, 1] / 1e6, caption='prod_pre')
    plotxy(data.t2pre_smooth[:, 0] / (3600 * 24), data.t2pre_smooth[:, 1] / 1e6, caption='t2pre_smooth')
    plotxy(data.z2ki[:, 0], np.log10(data.z2ki[:, 1] * 1.0e15), caption='kini')
    plotxy(data.z2k0[:, 0], np.log10(data.z2k0[:, 1] * 1.0e15), caption='kabs')
    plotxy(data.z2porosity[:, 0], data.z2porosity[:, 1], caption='porosity')
    plotxy(data.z2s[:, 0], data.z2s[:, 1], caption='hyd_sat')


def plot_100():
    from zmlx import gui
    gui.execute(lambda: plot_all(data), close_after_done=False)


def plot_120():
    from zmlx import gui
    gui.execute(lambda: plot_all(data120), close_after_done=False)


if __name__ == '__main__':
    plot_100()
