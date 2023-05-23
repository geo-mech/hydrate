# -*- coding: utf-8 -*-


from zml import *
from zmlx.alg import get_frac_width, mean


def main():
    sol = DDMSolution2()
    manager = InfManager2()
    network = FractureNetwork2()
    lave = 1

    network.add_fracture(pos=(-50, 0, 50, 0), lave=lave)

    for fracture in network.get_fractures():
        fracture.p0 = 0
        fracture.k = 0
        fracture.h = 1e4

    stress = Tensor2()
    stress.xx, stress.yy, stress.xy = -1e6, -1e6, 0

    manager.update_matrix(network, sol, stress, 1e4)
    manager.update_disp()

    for fracture in network.get_fractures():
        x0, y0, x1, y1 = fracture.pos
        pos = mean(x0, x1)
        width = get_frac_width(pos, half_length=50,
                               shear_modulus=sol.shear_modulus,
                               poisson_ratio=sol.poisson_ratio,
                               fluid_net_pressure=1e6)
        print(f'{pos}\t {width}\t {-fracture.dn}')


if __name__ == '__main__':
    main()
