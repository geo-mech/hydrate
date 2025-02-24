from icp_xz.opath import opath
from icp_xz.well_heating import well_heating
from zmlx.alg.apply_async import *


def main():
    tasks = []
    for perm in [1.0e-15, 3.2e-15, 1.0e-14, 3.2e-14, 1.0e-13]:
        folder = opath('test_perm', f'{perm}')
        tasks.append(create_async(func=well_heating,
                                  kwds={'folder': folder,
                                        'perm': perm}))
    apply_async(tasks)


if __name__ == '__main__':
    main()
