"""
此脚本展示Interp1的数据结构
"""

import numpy as np

from zml import Interp1


def test():
    x = np.linspace(0, 3.14, 20)
    y = np.sin(x)

    interp = Interp1(x=x, y=y)

    x, y = interp.get_data()
    print(x.to_list())
    print(y.to_list())

    interp.to_evenly_spaced(30)
    print('to_evenly_spaced')

    x, y = interp.get_data()
    print(x.to_list())
    print(y.to_list())


if __name__ == '__main__':
    test()
