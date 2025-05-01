import warnings

from zmlx.fem.elements.planar_strain_cst import stiffness as stiffness_cst


def stiffness(x0, x1, x2, y0, y1, y2, E, mu):
    warnings.warn("stiffness is deprecated (will be removed after 2026-3-30), "
                  "please use stiffness_cst instead",
                  DeprecationWarning, stacklevel=2)
    return stiffness_cst(((x0, y0), (x1, y1), (x2, y2)), E, mu, 1.0)


if __name__ == '__main__':
    m1 = stiffness(x0=0, x1=1, x2=0.5,
                   y0=0, y1=0, y2=1.0, E=200e5, mu=0.32)
    m2 = stiffness(x0=0, x1=0.5, x2=1,
                   y0=0, y1=1.0, y2=0, E=200e5, mu=0.32)
    print(m1)
    print(m2)
