def load_xyz(ipath=None, ix=None, iy=None, iz=None):
    if ipath is not None:
        import numpy as np
        data = np.loadtxt(ipath, float)
        if ix is not None:
            x = data[:, ix]
        else:
            x = None
        if iy is not None:
            y = data[:, iy]
        else:
            y = None
        if iz is not None:
            z = data[:, iz]
        else:
            z = None
        return x, y, z
    else:
        return None, None, None
