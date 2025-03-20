from zml import *
from zmlx.alg.get_frac_width import get_frac_width
from zmlx.demo.hf2.alg import update_topology, update_pos


def main():
    # 声明变量
    sol2 = DDMSolution2()
    matrix = InfMatrix()
    network = FractureNetwork()
    model = Seepage()

    # 添加裂缝
    network.add_fracture(pos=[-50, 0, 50, 0], lave=1,
                         data=FractureNetwork.FractureData.create(h=1e3))
    update_topology(model, network)

    update_pos(model, network)

    for c in model.cells:
        c.fluid_number = 1
        c.get_fluid(0).vol = 1.0

    model.get_nearest_cell(pos=[0, 0, 0]).get_fluid(0).vol = 10.0

    for c in model.cells:
        assert isinstance(c, Seepage.Cell)
        c.set_pore(1e6, 1.0, 2.0e6, 1.0)

    for f in model.faces:
        assert isinstance(f, Seepage.Face)
        f.cond = 1.0e-8

    for step in range(5):
        matrix.update(network, sol2)
        model.iterate(dt=1.0)
        for i in range(model.cell_number):
            pre = model.get_cell(i).pre
            f = network.get_fracture(i)
            f.p0 = pre
            f.k = 0  # 内部流体的压力和流体的体积无关
        network.update_disp(matrix)

    for f in network.fractures:
        assert isinstance(f, FractureNetwork.Fracture)
        p = model.get_cell(f.index).pre
        print(p,
              f.dn,
              get_frac_width(f.center[0],
                             half_length=50,
                             shear_modulus=sol2.shear_modulus,
                             poisson_ratio=sol2.poisson_ratio,
                             fluid_net_pressure=p))


if __name__ == '__main__':
    main()
