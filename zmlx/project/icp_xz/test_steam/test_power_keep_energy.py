import numpy as np

from icp_xz.steam_injection import steam_injection
from icp_xz.test_steam.opath import opath
from zmlx.alg.apply_async import *


def main():
    """
    变化加热水形成蒸汽的功率(但是，保持总的能量不变)
    """
    tasks = []
    for value in np.linspace(2e3, 10e3, 9):
        folder = opath(folder_name,
                       'power# (energy=5kW_5Y)', f'{value}')
        tasks.append(create_async(func=steam_injection,
                                  kwds={'folder': folder,
                                        'power': value,
                                        'years_heating': 5e3 * 5 / value}))
    apply_async(tasks)


if __name__ == '__main__':
    main()
