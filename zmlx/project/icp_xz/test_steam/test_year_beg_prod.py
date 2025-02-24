import numpy as np

from icp_xz.steam_injection import steam_injection
from icp_xz.test_steam.opath import opath
from zmlx.alg.apply_async import *


def main():
    tasks = []
    for value in np.linspace(1, 15, 15):
        folder = opath('year_beg_prod#', f'{value}')
        tasks.append(create_async(func=steam_injection,
                                  kwds={'folder': folder,
                                        'years_balance': value - 5.0
                                        }
                                  ))
    apply_async(tasks)


if __name__ == '__main__':
    main()
