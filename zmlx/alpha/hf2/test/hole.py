# -*- coding: utf-8 -*-

from math import pi, sin, cos

from zml import *
from zmlx.alg.linspace import linspace
from zmlx.plt import plot2


def main():
    sol = DDMSolution2()
    manager = InfManager2()
    network = FractureNetwork2()
    lave = 1

    angles = linspace(0, pi * 2, 30)
    for i in range(1, len(angles)):
        a0 = angles[i - 1]
        a1 = angles[i]
        x0, y0 = 20 * cos(a0), 20 * sin(a0)
        x1, y1 = 20 * cos(a1), 20 * sin(a1)
        network.add_fracture(pos=(x0, y0, x1, y1), lave=lave)

    for fracture in network.get_fractures():
        fracture.p0 = 0
        fracture.k = 0
        fracture.h = 1e4

    stress = Tensor2()
    stress.yy = -1e6

    manager.update_matrix(network, sol, stress, 1e4)
    manager.update_disp()

    for fracture in network.get_fractures():
        x0, y0, x1, y1 = fracture.pos
        print(f'{(x0 + x1) / 2} {(y0 + y1) / 2} {fracture.dn} {fracture.ds}')

    vx, vy, vz = [], [], []
    for x in linspace(-50, 50, 100):
        for y in linspace(-50, 50, 100):
            vx.append(x)
            vy.append(y)
            vz.append(network.get_induced(pos=(x, y), sol2=sol).xx)

    data = [{'name': 'tricontourf',
             'kwargs': {'x': vx, 'y': vy, 'z': vz, 'levels': 30}, 'has_colorbar': True}, ]
    plot2(xlabel='x', ylabel='y', clear=True,
          data=data)


if __name__ == '__main__':
    main()
