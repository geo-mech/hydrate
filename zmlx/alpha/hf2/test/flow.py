# -*- coding: utf-8 -*-


from zml import *
from zmlx.alg import get_frac_width, mean


def main():
    sol2 = DDMSolution2()
    manager = InfManager2()
    network = FractureNetwork2()
    seepage = Seepage()
    lave = 1
    coord = Coord3()
    ca_p = 1
    stress = Tensor2()
    fh = 1e4
    fa_id = 0

    network.add_fracture(pos=(-50, 0, 50, 0), lave=lave)

    for fracture in network.get_fractures():
        fracture.h = fh

    Hf2Alg.update_seepage_topology(seepage=seepage, network=network, fa_id=fa_id)
    Hf2Alg.update_seepage_cell_pos(seepage=seepage, network=network, fa_id=fa_id, coord=coord)
    print(f'seepage = {seepage}')

    for cell in seepage.cells:
        cell.fluid_number = 1
        cell.get_fluid(0).vol = fh * 0.01 * 2.0

    for face in seepage.faces:
        face.cond = 1.0e-6

    solver = ConjugateGradientSolver(tolerance=1.0e-12)

    for step in range(20):
        manager.update_matrix(network, sol2, stress, 5)
        manager.update_pore(seepage, fa_id=fa_id)
        seepage.iterate(dt=1.0, ca_p=ca_p, solver=solver)
        manager.update_boundary(seepage, fa_id=fa_id)
        manager.update_disp()

    for fracture in network.get_fractures():

        fp = seepage.get_cell(round(fracture.get_attr(fa_id))).get_attr(ca_p)
        x0, y0, x1, y1 = fracture.pos
        pos = mean(x0, x1)
        width = get_frac_width(pos, half_length=50,
                               shear_modulus=sol2.shear_modulus,
                               poisson_ratio=sol2.poisson_ratio,
                               fluid_net_pressure=fp)
        print(f'{pos}\t {width}\t {-fracture.dn}\t {fp}')


if __name__ == '__main__':
    main()
