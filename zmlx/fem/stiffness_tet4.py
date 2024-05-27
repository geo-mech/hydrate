"""
Created on Sun Feb 19 15:38:08 2023

@author: Maryelin
"""
import numpy as np


def stiffness(x0, x1, x2, x3, y0, y1, y2, y3, z0, z1, z2, z3, E, mu):
    """
    Calculate the stiffness matrix for a tetrahedral stress element.
    
    Parameters:
    
        ex = [x0,x1,x2,x3]         element coordinates
        ey = [y0,y1,y2,y3]
        ez = [z0,z1,z2,z3]

                                    
        E, nu =                for constitutive matrix
    
    Returns:
    
        Ke                      element stiffness matrix (6 x 6)

    """
    ex = [x0, x1, x2, x3]
    ey = [y0, y1, y2, y3]
    ez = [z0, z1, z2, z3]
    te = 1  # (Thickness) in our case is z

    # the matrix C contains the coordinates of the tet4 corner nodes
    C = np.array([
        [1, ex[0], ey[0], ez[0], 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, ex[0], ey[0], ez[0], 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, ex[0], ey[0], ez[0]],
        [1, ex[1], ey[1], ez[1], 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, ex[1], ey[1], ez[1], 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, ex[1], ey[1], ez[1]],
        [1, ex[2], ey[2], ez[2], 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, ex[2], ey[2], ez[2], 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, ex[2], ey[2], ez[2]],
        [1, ex[3], ey[3], ez[3], 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, ex[3], ey[3], ez[3], 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, ex[3], ey[3], ez[3]]
    ])

    V = (1 / 6) * np.linalg.det(np.array([
        [1, ex[0], ey[0], ez[0]],
        [1, ex[1], ey[1], ez[1]],
        [1, ex[2], ey[2], ez[2]],
        [1, ex[3], ey[3], ez[3]]
    ]))
    # constant for the Constant Strain tet4
    B = np.array([
        [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0],
        [0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0],
    ]) @ np.linalg.inv(C)  # reemplantar la distribucion de esto en el papel.

    Dm = E / ((1 - mu) * (1 - 2 * mu)) * np.array([
        [1 - mu, mu, mu, 0, 0, 0],
        [mu, 1 - mu, mu, 0, 0, 0],
        [mu, mu, 1 - mu, 0, 0, 0],
        [0, 0, 0, 1 / 2 - mu, 0, 0],
        [0, 0, 0, 0, 1 / 2 - mu, 0],
        [0, 0, 0, 0, 0, 1 / 2 - mu]
    ])

    ke = np.transpose(B) @ Dm @ B * V
    # k = [np.triu(ke)] #to show the upper part

    return ke


if __name__ == '__main__':
    m = stiffness(x0=0, x1=0, x2=10, x3=0, y0=0, y1=0, y2=0, y3=15, z0=0, z1=20, z2=0, z3=0, E=200e5, mu=0.32)
    np.savetxt('m.txt', m, fmt='%0.2f')
    print(m)
    print(m.shape)
