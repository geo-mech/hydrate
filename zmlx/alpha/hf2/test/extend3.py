# -*- coding: utf-8 -*-


from zmlx import *
from zmlx.plt.show_fn2 import show_fn2


def main():
    sol2 = DDMSolution2()
    manager = InfManager2()
    network = FractureNetwork2()
    layers = []
    while len(layers) < 30:
        layers.append(Seepage())
    layer_c = layers[15]
    fh_max = 50
    layer_dh = fh_max / len(layers)
    lave = 1
    coord = Coord3()
    ca_p = 0
    ca_ny = 1
    ca_l = 2
    ca_h = 3
    ca_g = 4
    ca_mu = 5
    stress = Tensor2()

    kic = Tensor2(xx=1e6, yy=1e6)
    injs = [(-4, 0), (4, 0)]
    fa_id = 0
    fa_tmp = 1

    for x, y in injs:
        network.add_fracture(pos=(x, y - 1, x, y + 1), lave=lave)
        layer_c.add_injector(pos=(x, y, 0), radi=lave * 3,
                             fluid_id=0,
                             opers=[(0, fh_max * 0.0001)])

    pipe = Seepage()
    while pipe.cell_number < len(layers):
        pipe.add_cell()
    for i in range(1, pipe.cell_number):
        pipe.add_face(pipe.get_cell(i-1), pipe.get_cell(i))

    solver = ConjugateGradientSolver(tolerance=1.0e-12)

    dt = 10.0
    for step in range(200):
        gui.break_point()
        print(f'step = {step}. cell n = {layer_c.cell_number}')

        network.update_h_by_layers(layers, fa_id=fa_id, layer_h=layer_dh, w_min=1e-6)

        network.copy_attr(fa_tmp, fa_id)
        for lay in layers:
            network.copy_attr(fa_id, fa_tmp)
            Hf2Alg.update_seepage_topology(seepage=lay, network=network, fa_id=fa_id)
            Hf2Alg.update_seepage_cell_pos(seepage=lay, network=network, fa_id=fa_id, coord=coord)
            Hf2Alg.update_cond(seepage=lay, network=network, fa_id=fa_id)

        manager.update_matrix(network, sol2, stress, 5)

        for lay in layers:
            Hf2Alg.update_normal_stress(seepage=lay, ca_ny=ca_ny, manager=manager, fa_id=fa_id)
            Hf2Alg.update_length(seepage=lay, ca_l=ca_l, network=network, fa_id=fa_id)
            ca = lay.numpy.cells
            ca.set(ca_h, layer_dh)
            ca.set(ca_g, sol2.shear_modulus)
            ca.set(ca_mu, sol2.poisson_ratio)
            Hf2Alg.update_pore(seepage=lay, ca_l=ca_l, ca_h=ca_h, ca_ny=ca_ny, ca_g=ca_g, ca_mu=ca_mu)
            lay.iterate(dt=dt, ca_p=ca_p, solver=solver)

        Hf2Alg.exchange_fluids(layers=layers, pipe=pipe, dt=dt, ca_g=ca_g, ca_fp=ca_p)
        manager.update_boundary(seepage=layers, fa_id=fa_id)
        manager.update_disp()
        network.extend(kic=kic, sol2=sol2, has_branch=False, lave=lave)

        if step % 20 == 0:
            show_fn2(network=network, seepage=layer_c, ca_c=ca_p, w_max=6, caption='裂缝', fa_id=fa_id)


if __name__ == '__main__':
    gui_exec(main, close_after_done=False)
