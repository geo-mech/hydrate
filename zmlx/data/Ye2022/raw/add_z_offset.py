from zml import np
from zmlx.alg.fsys import first_only


def add_z_offset(fname, dz):
    data = np.loadtxt(fname)
    data[:, 0] += dz
    np.savetxt(fname, data, fmt='%.4e')


if __name__ == '__main__':
    first_only()
    for fname in ['perm.txt', 'perm_ini.txt', 'perm_smooth.txt', 'porosity.txt',
                  'porosity_smooth.txt', 'sat_hyd.txt',
                  'sat_hyd_smooth.txt']:
        add_z_offset(fname, -10)
        print(f'{fname}: succeed')
