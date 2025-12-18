"""
Created on Sun Feb 19 15:38:08 2023

@author: Maryelin
https://calfem-for-python.readthedocs.io/en/latest/_modules/calfem/core.html#bar1s
"""
from zml import np
from zmlx.fem.stiffness_triangle import stiffness as tri3


def stiffness(x0, x1, x2, x3, y0, y1, y2, y3, E, mu):
    """
    Calculate the stiffness matrix for a quadrilateral element.
    
    Parameters:
    
        ex = [x0,x1,x2,x3]         element coordinates
        ey = [y0,y1,y2,y3]

                                    
        E, nu =                for constitutive matrix
    
    Returns:
    
        Ke                      element stiffness matrix (8 x 8)

    """
    ex = [x0, x1, x2, x3]
    ey = [y0, y1, y2, y3]

    K = np.zeros((10, 10))

    xm = sum(ex) / 4
    ym = sum(ey) / 4

    ke1 = tri3(ex[0], ex[1], xm, ey[0], ey[1], ym, E, mu)
    tr1 = np.array([1, 2, 3, 4, 9, 10])
    idx = tr1 - 1
    K[np.ix_(idx, idx)] = K[np.ix_(idx, idx)] + ke1

    ke1 = tri3(ex[1], ex[2], xm, ey[1], ey[2], ym, E, mu)
    tr2 = np.array([3, 4, 5, 6, 9, 10])
    idx = tr2 - 1
    K[np.ix_(idx, idx)] = K[np.ix_(idx, idx)] + ke1

    ke1 = tri3(ex[2], ex[3], xm, ey[2], ey[3], ym, E, mu)
    tr3 = np.array([5, 6, 7, 8, 9, 10])
    idx = tr3 - 1
    K[np.ix_(idx, idx)] = K[np.ix_(idx, idx)] + ke1

    ke1 = tri3(ex[3], ex[0], xm, ey[3], ey[0], ym, E, mu)
    tr4 = np.array([7, 8, 1, 2, 9, 10])
    idx = tr4 - 1
    K[np.ix_(idx, idx)] = K[np.ix_(idx, idx)] + ke1

    cd = np.array([[9], [10]])
    nd, nd = np.shape(K)
    cd = (cd - 1).flatten()

    aindx = np.arange(nd)
    aindx = np.delete(aindx, cd, 0)
    bindx = cd

    Kaa = np.asmatrix(K[np.ix_(aindx, aindx)])
    Kab = np.asmatrix(K[np.ix_(aindx, bindx)])
    Kbb = np.asmatrix(K[np.ix_(bindx, bindx)])

    K1 = Kaa - Kab * Kbb.I * Kab.T

    return K1


if __name__ == '__main__':
    m1 = stiffness(x0=0, x1=2, x2=2, x3=0,
                   y0=0, y1=0, y2=2, y3=2, E=200e5, mu=0.32)
    m2 = stiffness(x3=0, x2=2, x1=2, x0=0,
                   y3=0, y2=0, y1=2, y0=2, E=200e5, mu=0.32)
    print(m1)
    print(m2)
