from zmlx.data.Ye2022.load_txt import load_txt
from zmlx.plt.fig2 import plot2

if __name__ == '__main__':
    # 产气速率
    d1 = load_txt('porosity.txt')

    # 产水速率
    d2 = load_txt('porosity_smooth.txt')

    d3 = load_txt('sat_hyd.txt')

    x1 = d1[:, 0]
    y1 = d1[:, 1]

    x2 = d2[:, 0]
    y2 = d2[:, 1]

    x3 = d3[:, 0]
    y3 = d3[:, 1]

    plot2(data=[{'name': 'plot', 'args': [y1, x1]},
                {'name': 'plot', 'args': [y2, x2]},
                {'name': 'plot', 'args': [y3, x3]}
                ])
