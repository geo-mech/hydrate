from math import pi, sin, cos

from zml import DDMSolution2, InfMatrix, FractureNetwork
from zmlx.alg.linspace import linspace
from zmlx.plt.tricontourf import tricontourf


def main():
    sol = DDMSolution2()
    matrix = InfMatrix()
    network = FractureNetwork()
    lave = 1

    angles = linspace(0, pi * 2, 30)
    for i in range(1, len(angles)):
        a0 = angles[i - 1]
        a1 = angles[i]
        x0, y0 = 20 * cos(a0), 20 * sin(a0)
        x1, y1 = 20 * cos(a1), 20 * sin(a1)
        network.add_fracture(pos=[x0, y0, x1, y1], lave=lave)

    for f in network.fractures:
        f.p0 = 1e6
        f.k = 0
        f.h = 1e4

    matrix.update(network, sol)
    network.update_disp(matrix)

    for f in network.fractures:
        x0, y0, x1, y1 = f.pos
        print(f'{(x0 + x1) / 2} {(y0 + y1) / 2} {f.dn} {f.ds}')

    vx, vy, vz = [], [], []
    for x in linspace(-50, 50, 100):
        for y in linspace(-50, 50, 100):
            vx.append(x)
            vy.append(y)
            vz.append(network.get_induced(pos=(x, y), sol2=sol).xx)

    tricontourf(vx, vy, vz)


if __name__ == '__main__':
    main()
