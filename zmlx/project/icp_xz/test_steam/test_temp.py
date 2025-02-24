from icp_xz.steam_injection import steam_injection
from icp_xz.test_steam.opath import opath
from zmlx.alg.apply_async import *


def main():
    tasks = []
    for temp in [500, 600, 700, 800, 900, 1000]:
        folder = opath('temp#', f'{temp}')
        tasks.append(create_async(func=steam_injection,
                                  kwds={'folder': folder,
                                        'steam_temp': temp}))
    apply_async(tasks)


if __name__ == '__main__':
    main()
