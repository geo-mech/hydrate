import numpy as np

from zmlx.data.Ye2022.load_txt import load_txt
from zmlx.plt.plot2 import plot2

if __name__ == '__main__':
    # 绝对渗透率
    d = load_txt('perm.txt')

    x1 = d[:, 0]
    y1 = np.log10(d[:, 1])

    # 初始渗透率
    d = load_txt('perm_ini.txt')

    x2 = d[:, 0]
    y2 = np.log10(d[:, 1])

    # 初始渗透率
    d = load_txt('perm_smooth.txt')

    x3 = d[:, 0]
    y3 = np.log10(d[:, 1])

    plot2(data=[{'name': 'plot', 'args': [y1, x1]},
                {'name': 'plot', 'args': [y2, x2]},
                {'name': 'plot', 'args': [y3, x3]}
                ])
