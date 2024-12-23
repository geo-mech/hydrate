# ** desc = '模拟流体在单一裂缝内部的流动，并最终达到平衡的状态'

from zml import (DDMSolution2, InfMatrix, FractureNetwork, Seepage, Coord3, Tensor2,
                 FracAlg, ConjugateGradientSolver)
from zmlx.alg.get_frac_width import get_frac_width
from zmlx.alg.mean import mean

# todo:
#     此demo尚未完成.


def main():
    # 声明变量
    sol2 = DDMSolution2()
    matrix = InfMatrix()
    network = FractureNetwork()
    seepage = Seepage()
    lave = 1
    coord = Coord3()
    stress = Tensor2()
    fh = 1e4

    ca_p = 1
    ca_s = 2
    fa_id = 0
    fa_w = 1
    fa_dist = 2

    # 添加裂缝
    FracAlg.add_frac(network, p0=[-50, 0], p1=[50, 0], lave=lave)

    for fracture in network.fractures:
        fracture.h = fh

    FracAlg.update_topology(seepage, network,
                            layer_n=1, z_min=-1, z_max=1,
                            ca_area=ca_s,
                            fa_width=fa_w,
                            fa_dist=fa_dist)

    print(seepage)

    for cell in seepage.cells:
        cell.fluid_number = 1
        cell.get_fluid(0).vol = fh * 0.01 * 2.0

    for face in seepage.faces:
        face.cond = 1.0e-6

    solver = ConjugateGradientSolver(tolerance=1.0e-12)

    # for step in range(20):
    #     matrix.update(network, sol2)
    #
    #     Hf2Alg.update_pore(seepage, manager, fa_id=fa_id)
    #     seepage.iterate(dt=1.0, ca_p=ca_p, solver=solver)
    #     manager.update_boundary(seepage, fa_id=fa_id)
    #     manager.update_disp()

    # for fracture in network.fractures:
    #     fp = seepage.get_cell(round(fracture.get_attr(fa_id))).get_attr(ca_p)
    #     x0, y0, x1, y1 = fracture.pos
    #     pos = mean(x0, x1)
    #     width = get_frac_width(pos, half_length=50,
    #                            shear_modulus=sol2.shear_modulus,
    #                            poisson_ratio=sol2.poisson_ratio,
    #                            fluid_net_pressure=fp)
    #     print(f'{pos}\t {width}\t {-fracture.dn}\t {fp}')


if __name__ == '__main__':
    main()
