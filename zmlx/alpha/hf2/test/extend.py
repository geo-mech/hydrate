# -*- coding: utf-8 -*-


from zmlx import *
from zmlx.plt.show_fn2 import show_fn2


def main():
    sol2 = DDMSolution2()
    manager = InfManager2()
    network = FractureNetwork2()

    # 多层的渗流模型
    layer_n = 1
    h_sum = 50
    layer_h = h_sum / layer_n
    layers = []
    while len(layers) < layer_n:
        layers.append(Seepage())
    layer_c = layers[int(layer_n / 2)]

    # 用于多层之间的连接
    pip = Seepage()
    for i in range(layer_n):
        pip.add_cell()
        if i > 0:
            pip.add_face(pip.get_cell(i - 1), pip.get_cell(i))

    lave = 1
    ca_p = 0
    ca_ny = 1
    ca_l = 2
    ca_h = 3
    ca_g = 4
    ca_mu = 5
    stress = Tensor2(xx=-1e6, yy=-1.5e6)

    kic = Tensor2(xx=1e6, yy=1e6)
    injs = [(-4, 0), (4, 0)]
    fa_id = 0
    fa_tmp = 1

    for x, y in injs:
        network.add_fracture(pos=(x, y - 1, x, y + 1), lave=lave)
        layer_c.add_injector(pos=(x, y, 0), radi=lave * 3,
                             fluid_id=0,
                             opers=[(0, layer_h * 0.0001)])

    solver = ConjugateGradientSolver(tolerance=1.0e-12)

    dt = 10.0
    for step in range(200):
        gui.break_point()
        print(f'step = {step}. frac_n = {network.frac_n}')

        network.update_h_by_layers(layers, fa_id=fa_id, layer_h=layer_h, w_min=1e-7)

        network.copy_attr(fa_tmp, fa_id)
        for layer_id in range(layer_n):
            lay = layers[layer_id]
            network.copy_attr(fa_id, fa_tmp)
            Hf2Alg.update_seepage_topology(seepage=lay, network=network, fa_id=fa_id)
            Hf2Alg.update_seepage_cell_pos(seepage=lay, network=network, fa_id=fa_id,
                                           coord=Coord3(origin=(0, 0, (layer_id - layer_n / 2) * layer_h)))
            Hf2Alg.update_cond(seepage=lay, network=network, fa_id=fa_id)

        manager.update_matrix(network, sol2, stress, 5)

        for lay in layers:
            Hf2Alg.update_normal_stress(seepage=lay, ca_ny=ca_ny, manager=manager, fa_id=fa_id)
            Hf2Alg.update_length(seepage=lay, ca_l=ca_l, network=network, fa_id=fa_id)
            ca = lay.numpy.cells
            ca.set(ca_h, layer_h)
            ca.set(ca_g, sol2.shear_modulus)
            ca.set(ca_mu, sol2.poisson_ratio)
            Hf2Alg.update_pore(seepage=lay, ca_l=ca_l, ca_h=ca_h, ca_ny=ca_ny, ca_g=ca_g, ca_mu=ca_mu)

        for lay in layers:
            lay.iterate(dt=dt, ca_p=ca_p, solver=solver)

        for lay in layers:
            Hf2Alg.update_cond(seepage=lay, ca_g=ca_g, ca_l=ca_h, ca_h=ca_l)

        Hf2Alg.exchange_fluids(layers=layers, pipe=pip,
                               dt=dt*0.01,
                               ca_g=ca_g, ca_fp=ca_p)

        manager.update_boundary(layer_c, fa_id=fa_id, fh=layer_h)
        manager.update_disp()
        network.extend(kic=kic, sol2=sol2, has_branch=False, lave=lave)

        if step % 20 == 0:
            show_fn2(network=network, seepage=layer_c, ca_c=ca_p, w_max=6, caption='裂缝', fa_id=fa_id)


if __name__ == '__main__':
    gui_exec(main, close_after_done=False)
