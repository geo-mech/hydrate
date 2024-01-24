import numpy as np

from zmlx.data.Ye2022.load import load_
from zmlx.plt.plot2 import plot2

# 产气速率
d1 = load_('perm.txt')

# 产水速率
d2 = load_('perm_ini.txt')

x1 = d1[:, 0]
y1 = np.log10(d1[:, 1])

x2 = d2[:, 0]
y2 = np.log10(d2[:, 1])

plot2(data=[{'name': 'plot', 'args': [y1, x1]},
            {'name': 'plot', 'args': [y2, x2]}],
      caption='生产速率')
