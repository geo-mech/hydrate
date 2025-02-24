import numpy as np

from icp_xz.steam_injection import steam_injection
from icp_xz.test_steam.opath import opath
from zmlx.alg.apply_async import *


def main():
    """
    变化加热水形成蒸汽的功率
    """
    tasks = []
    for value in np.linspace(1e3, 10e3, 10):
        folder = opath('power#', f'{value}')
        tasks.append(create_async(func=steam_injection,
                                  kwds={'folder': folder,
                                        'power': value}))
    apply_async(tasks)


if __name__ == '__main__':
    main()
