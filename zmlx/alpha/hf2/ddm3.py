# -*- coding: utf-8 -*-
"""
基本思路：
    将天然裂缝等，都事先放到Seepage中存储，并完全利用Seepage来表示(利用krf来更新导流的能力). 将主裂缝，利用另外一套多层的网络来存储。考虑到在
    裂缝体系内，流体流动的速度比较高，因此，将主裂缝和天然裂缝放到统一的一个Seepage下进行流动计算（后续如果有基质渗流，则可以放在另外一个独立的
    Seepage下运行）。

应力更新的步骤：
    1. 利用二维的ddm，计算得到各个竖直的单元的诱导应力，并且再叠加上原位应力，得到各个各单元的应力;
    2. 再利用二维的ddm，考虑裂缝在纵向上的应力影响，再计算在数值方向上的应力分布，从而根据中心的应力，计算得到各个单位的应力. (这一步暂时不要)

"""

from zmlx import *
from zmlx.alg.opath import opath
from zmlx.alg.get_frac_cond import g_1cm
from zmlx.alpha.hf2 import CellKeys, FaceKeys, FracKeys
from zmlx.alpha.hf2.layers import pop_layers, push_layers, update_layers_topology, get_middle_layer, \
    create_layers, get_middle_layer_id, get_cell_ibeg
from zmlx.alpha.hf2.save_c14 import save_c14
from zmlx.alpha.hf2.create_krf import create_krf
from zmlx.alpha.hf2.reset_injectors import reset_injectors
from zmlx.alpha.hf2.show_layer import show_layer
from zmlx.alg.clamp import clamp


class Ddm3:

    def __init__(self, wk_dir=None, layer_n=15, h_sum=30, lave=1.0, seepage=None):
        self.wk_dir = wk_dir if wk_dir is not None else opath('hf2_extend_v3')

        self.seepage, self.krf = Seepage() if seepage is None else seepage, create_krf()
        self.sol2, self.manager, self.network = DDMSolution2(), InfManager2(), FractureNetwork2()

        self.layers = create_layers(layer_n)
        self.layer_h = h_sum / layer_n
        self.lave = lave
        self.stress = Tensor2(xx=-1e6, yy=-1e6)
        self.kic = Tensor2(xx=1e6, yy=1e6)

        for x, y in [(-4, 0), (4, 0)]:
            self.add_inj(x, y)

        self.dt, self.step, self.time = 1.0e-3, 0, 0
        self.history = ExHistory()

    def add_inj(self, x, y, q=None):
        """
        添加注入点，以及初始的裂缝
        """
        self.network.add_fracture(pos=(x, y - 1, x, y + 1), lave=self.lave)
        if q is None:
            q = self.layer_h * len(self.layers) * 0.0001
        self.seepage.add_injector(pos=(x, y, 0), radi=self.lave * 3, fluid_id=0,
                                  opers=[(0, q)])

    def opath(self, *args):
        """
        生成输出路径
        """
        return opath(self.wk_dir, *args)

    def iterate(self):
        """
        向前迭代一步
        """
        self.time += self.dt
        self.step += 1

        # todo: 强制将裂缝的高度设置为我们的层的总高度，以此来计算诱导应力。这样并不准确，后续需要修改
        for f in self.network.get_fractures():
            f.h = self.layer_h * len(self.layers)

        if True:  # self.step % 2 == 0 or self.seepage.cell_number == 0:
            # 这里主要处理裂缝的扩展操作.
            pop_layers(self.layers, self.seepage)
            update_layers_topology(layers=self.layers, network=self.network,
                                   layer_h=self.layer_h, z_average=0)
            push_layers(self.seepage, self.layers)

            self.manager.update_matrix(self.network, self.sol2, self.stress, 5)
            self.manager.update_boundary(get_middle_layer(self.layers),
                                         fa_id=FracKeys.id, fh=self.layer_h)
            self.manager.update_disp()
            count = self.network.extend(kic=self.kic, sol2=self.sol2, has_branch=False,
                                        lave=self.lave)
            print(f'Count of Extend: {count}')

            self.history.record(self.dt, count)

            reset_injectors(self.seepage)

        ilayer_c = get_middle_layer_id(self.layers)
        layer_c = self.layers[ilayer_c]
        layer_c.clone_cells(0, self.seepage,
                            get_cell_ibeg(self.layers, self.seepage, ilayer_c),
                            layer_c.cell_number)

        self.manager.update_boundary(seepage=layer_c, fa_id=FracKeys.id,
                                     fh=self.layer_h)  # todo: 当多层或者有dfn的时候，千万不可直接用seepage
        self.manager.update_disp()

        Hf2Alg.update_normal_stress(seepage=layer_c, ca_ny=CellKeys.ny,
                                    manager=self.manager, fa_id=FracKeys.id, except_self=False,
                                    relax_factor=0.1)
        ibeg = get_cell_ibeg(self.layers, self.seepage, 0)
        nys = [cell.get_attr(CellKeys.ny) for cell in layer_c.cells]
        for lay in self.layers:
            for ny in nys:
                self.seepage.get_cell(ibeg).set_attr(CellKeys.ny, ny)
                ibeg += 1

        Hf2Alg.update_pore(seepage=self.seepage, ca_ny=CellKeys.ny, ca_s=CellKeys.s, k1=1.0e-10, k2=1.0e-9)

        cells = self.seepage.numpy.cells
        cells.set(CellKeys.v0, cells.get(CellKeys.s) * 0.01)  # 用于更新导流能力

        # self.seepage.numpy.faces.set(FaceKeys.g0, g_1cm)
        #
        # 设置Face的导流能力，在水平方向和竖直方向上，让裂缝的导流能力不一样.
        for face in self.seepage.faces:
            assert isinstance(face, Seepage.FaceData)
            tag = round(face.get_attr(FaceKeys.tag))
            assert tag == 1 or tag == 2
            if tag == 1:
                face.set_attr(FaceKeys.g0, g_1cm)
            else:
                face.set_attr(FaceKeys.g0, g_1cm*0.1)

        self.seepage.update_cond(v0=CellKeys.v0, g0=FaceKeys.g0, krf=self.krf)
        self.seepage.iterate(dt=self.dt, ca_p=CellKeys.fp)

        dt = self.history.get_best_dt(0.05)
        if dt > 0:
            self.dt = clamp(dt, self.dt * 0.1, self.dt * 1.5)

    @staticmethod
    def test():
        space = Ddm3()
        for step in range(50000):
            gui.status(f'step = {space.step}. frac_n = {space.network.frac_n}. dt = {space.dt}')
            gui.break_point()
            space.iterate()
            if step % 100 == 0:
                Hf2Alg.update_normal_stress(seepage=get_middle_layer(space.layers), ca_ny=CellKeys.ny,
                                            manager=space.manager, fa_id=FracKeys.id, except_self=False)
                show_layer(space.layers, space.network)

            if step % 500 == 0:
                save_c14(make_fpath(folder=space.opath('c14'), step=step, ext='.txt'), space.seepage)

        space.seepage.save(space.opath('seepage.xml'))
        space.network.save(space.opath('network.xml'))


if __name__ == '__main__':
    gui.execute(Ddm3.test, close_after_done=False)
