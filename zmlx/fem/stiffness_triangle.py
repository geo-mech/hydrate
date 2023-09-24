# -*- coding: utf-8 -*-
"""
Created on Wed Feb 15 12:00:10 2023

@author: Maryelin
http://mae.uta.edu/~lawrence/me5310/course_materials/me5310_notes/7_Triangular_Elements/7-2_Constant_Strain_Triangle_CST/7-2_Constant_Strain_Triangle_CST.htm
https://calfem-for-python.readthedocs.io/en/latest/_modules/calfem/core.html#plante
"""
import numpy as np


def stiffness(x0, x1, x2, y0, y1, y2, E, mu):
    """
    Calculate the stiffness matrix for a triangular plane stress element.
    
    Parameters:
    
        ex = [x1,x2,x3]         element coordinates
        ey = [y1,y2,y3]

                                    
        E, nu =                for constitutive matrix
    
    Returns:
    
        Ke                      element stiffness matrix (6 x 6)

    """
    ex = [x0, x1, x2]
    ey = [y0, y1, y2]
    te = 0.3  # (Thickness) in our case is z

    # the matrix C contains the coordinates of the triangle corner nodes
    C = np.mat([
        [1, ex[0], ey[0], 0, 0, 0],
        [0, 0, 0, 1, ex[0], ey[0]],
        [1, ex[1], ey[1], 0, 0, 0],
        [0, 0, 0, 1, ex[1], ey[1]],
        [1, ex[2], ey[2], 0, 0, 0],
        [0, 0, 0, 1, ex[2], ey[2]]
    ])

    A = 0.5 * np.linalg.det(np.mat([
        [1, ex[0], ey[0]],
        [1, ex[1], ey[1]],
        [1, ex[2], ey[2]]
    ]))
    # Stress elastic matrix
    Dm = E / (1 - mu ** 2) * np.mat([[1, mu, 0],
                                     [mu, 1, 0],
                                     [0, 0, (1 - mu) / 2]])

    # constant for the Constant Strain Triangle
    B = np.mat([
        [0, 1, 0, 0, 0, 0, ],
        [0, 0, 0, 0, 0, 1, ],
        [0, 0, 1, 0, 1, 0, ]
    ]) * np.linalg.inv(C)

    ke = np.transpose(B) * Dm * B * A * te
    # k = [np.triu(ke)]  # to show the upper part

    return ke


if __name__ == '__main__':
    m1 = stiffness(x0=0, x1=1, x2=0.5,
                   y0=0, y1=0, y2=1.0, E=200e5, mu=0.32)
    m2 = stiffness(x0=0, x1=0.5, x2=1,
                   y0=0, y1=1.0, y2=0, E=200e5, mu=0.32)
    print(m1)
    print(m2)

