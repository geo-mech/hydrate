"""
赵文智, et al. (2018). "页岩油地下原位转化的内涵与战略地位." 石油勘探与开发 45(04): 537-545.
"""

from zml import Interp1
import os
import numpy as np

data = np.loadtxt(os.path.join(os.path.dirname(__file__), 'data.txt'))

# 将原始数据平移到0附近，同时，将原来深度的值，转化为向上为z的正方向
z = data[:, 0]
z -= ((z[0] + z[-1]) / 2)
z = -z

# 0：z坐标
# 1：孔隙度
# 2：气饱和度
# 3：水饱和度
# 4：轻油饱和度
# 5：重油饱和度
# 6：干酪根饱和度

z2porosity = Interp1(x=z, y=data[:, 1])
z2sg = Interp1(x=z, y=data[:, 2])
z2sw = Interp1(x=z, y=data[:, 3])
z2slo = Interp1(x=z, y=data[:, 4])
z2sho = Interp1(x=z, y=data[:, 5])
z2sk = Interp1(x=z, y=data[:, 6])

__all__ = ['data', 'z2porosity', 'z2sg', 'z2sw', 'z2slo', 'z2sho', 'z2sk']
