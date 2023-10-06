# ** desc = '页岩水力压裂 （拟三维）'

from zmlx.plt.show_fn2 import show_fn2
from zmlx.utility.AttrKeys import *

stress = Tensor2(xx=-10e6, yy=-11e6)
kic = Tensor2(xx=1e6, yy=1e6)
thick = 50
lave = 1
dt = 10
time = 0
seepage = Seepage()
network = FractureNetwork2()
manager = InfManager2()
sol2 = DDMSolution2()

for x, y in [(-4, 0), (4, 0)]:
    q = thick * 0.00004
    network.add_fracture(pos=(x, y - 1, x, y + 1),
                         lave=lave)
    seepage.add_injector(pos=(x, y, 0), radi=lave * 3,
                         fluid_id=0,
                         flu=Seepage.FluData(den=1000, vis=0.001, vol=1.0),
                         opers=[(0, q)])


def iterate():
    Hf2Alg.update_seepage_topology(seepage=seepage, network=network, fa_id=frac_keys(seepage).id)
    Hf2Alg.update_seepage_cell_pos(seepage=seepage, network=network, fa_id=frac_keys(seepage).id, coord=Coord3())

    # 更新裂缝的高度
    for f in network.get_fractures():
        f.h = thick

    # 更新矩阵
    manager.update_matrix(network, sol2, stress, 5)

    # 更新流体
    Hf2Alg.update_pore(seepage=seepage, manager=manager, fa_id=frac_keys(seepage).id)
    Hf2Alg.update_cond(seepage=seepage, network=network, fa_id=frac_keys(seepage).id, fw_max=0.0001)
    seepage.apply_injectors(dt=dt)
    seepage.iterate(dt=dt, ca_p=cell_keys(seepage).pre)

    # 更新固体
    network.update_boundary(seepage=seepage, fa_id=frac_keys(seepage).id, fh=thick)
    manager.update_disp()
    network.extend(kic=kic, sol2=sol2,
                   has_branch=False, lave=lave)


def main():
    for step in range(200):
        gui.break_point()
        iterate()
        fn = network.frac_n
        print(f'step = {step}. frac_n = {fn}')
        if step % 20 == 0:
            show_fn2(network=network, seepage=seepage, ca_c=cell_keys(seepage).pre, w_max=6,
                     caption='裂缝', fa_id=frac_keys(seepage).id)


if __name__ == '__main__':
    gui_exec(main, close_after_done=False)
