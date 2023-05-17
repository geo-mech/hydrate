# -*- coding: utf-8 -*-
"""
Created on Wed Feb 15 12:00:10 2023

@author: Maryelin
http://mae.uta.edu/~lawrence/me5310/course_materials/me5310_notes/7_Triangular_Elements/7-2_Constant_Strain_Triangle_CST/7-2_Constant_Strain_Triangle_CST.htm
https://calfem-for-python.readthedocs.io/en/latest/_modules/calfem/core.html#plante
"""
import numpy as np


def stiffness(x0, x1, x2, y0, y1, y2, E, nu):
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
    Dm = E / (1 - nu ** 2) * np.mat([[1, nu, 0],
                                     [nu, 1, 0],
                                     [0, 0, (1 - nu) / 2]])

    # constant for the Constant Strain Triangle
    B = np.mat([
        [0, 1, 0, 0, 0, 0, ],
        [0, 0, 0, 0, 0, 1, ],
        [0, 0, 1, 0, 1, 0, ]
    ]) * np.linalg.inv(C)

    ke = np.transpose(B) * Dm * B * A * te
    k = [np.triu(ke)]  # to show the upper part

    return ke


print(stiffness(x0=2.25, x1=2.40, x2=1.5, y0=0.75, y1=1.65, y2=1.0, E=200e5, nu=0.32))
