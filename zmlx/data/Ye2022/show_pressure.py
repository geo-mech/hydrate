from zmlx.data.Ye2022.load_txt import load_txt
from zmlx.plt.plot2 import plot2

d1 = load_txt('pressure_prod.txt')

x1 = d1[:, 0] / (3600 * 24)
y1 = d1[:, 1]

d2 = load_txt('pressure_prod_smooth.txt')

x2 = d2[:, 0] / (3600 * 24)
y2 = d2[:, 1]

plot2(data=[{'name': 'plot', 'args': [x1, y1]},
            {'name': 'plot', 'args': [x2, y2]}])
