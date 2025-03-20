from zmlx.data.Ye2022.load_txt import load_txt
from zmlx.plt.plot2 import plot2

if __name__ == '__main__':
    # 产气速率
    rate_gas = load_txt('prod_rate_gas.txt')

    # 产水速率
    rate_wat = load_txt('prod_rate_water.txt')

    x1 = rate_gas[:, 0] / (3600 * 24)
    y1 = rate_gas[:, 1] * 3600 * 24 / 0.716

    x2 = rate_wat[:, 0] / (3600 * 24)
    y2 = rate_wat[:, 1] * 3600 * 24 / 1000.0

    plot2(data=[{'name': 'plot', 'args': [x1, y1]},
                {'name': 'plot', 'args': [x2, y2 * 100]}])
