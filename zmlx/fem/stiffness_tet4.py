import warnings

from zmlx.fem.elements.c3d4 import stiffness as c3d4_stiffness


def stiffness(x0, x1, x2, x3, y0, y1, y2, y3, z0, z1, z2, z3, E, mu):
    warnings.warn("stiffness is deprecated (will be removed after 2026-3-30), "
                  "use c3d4_stiffness instead",
                  DeprecationWarning, stacklevel=2)
    return c3d4_stiffness(
        ((x0, y0, z0),
         (x1, y1, z1),
         (x2, y2, z2),
         (x3, y3, z3)), E, mu)


if __name__ == '__main__':
    m = stiffness(x0=0, x1=0, x2=10, x3=0, y0=0, y1=0, y2=0, y3=15, z0=0, z1=20,
                  z2=0, z3=0, E=200e5, mu=0.32)
    print(m)
    print(m.shape)
