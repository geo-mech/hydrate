# ** desc = '页岩水力压裂 （拟三维）'

from zmlx import *
from zmlx.plt.show_fn2 import show_fn2


class Config(TherFlowConfig):
    def __init__(self):
        super().__init__()
        self.frac_keys = AttrKeys('id')
        self.model_keys.add_keys('stress_xx', 'stress_yy', 'stress_xy',
                                 'kic_xx', 'kic_yy', 'kic_xy',
                                 'thick', 'lave')

    def set_stress(self, model, stress):
        model.set_attr(self.model_keys.stress_xx, stress.xx)
        model.set_attr(self.model_keys.stress_yy, stress.yy)
        model.set_attr(self.model_keys.stress_xy, stress.xy)

    def get_stress(self, model):
        return Tensor2(xx=model.get_attr(self.model_keys.stress_xx),
                       yy=model.get_attr(self.model_keys.stress_yy),
                       xy=model.get_attr(self.model_keys.stress_xy),
                       )

    def set_kic(self, model, kic):
        model.set_attr(self.model_keys.kic_xx, kic.xx)
        model.set_attr(self.model_keys.kic_yy, kic.yy)
        model.set_attr(self.model_keys.kic_xy, kic.xy)

    def get_kic(self, model):
        return Tensor2(xx=model.get_attr(self.model_keys.kic_xx),
                       yy=model.get_attr(self.model_keys.kic_yy),
                       xy=model.get_attr(self.model_keys.kic_xy),
                       )

    def set_thick(self, model, thick):
        model.set_attr(self.model_keys.thick, thick)

    def get_thick(self, model):
        return model.get_attr(self.model_keys.thick)

    def set_lave(self, model, lave):
        model.set_attr(self.model_keys.lave, lave)

    def get_lave(self, model):
        return model.get_attr(self.model_keys.lave)

    def update_seepage_topology(self, seepage, network):
        Hf2Alg.update_seepage_topology(seepage=seepage, network=network,
                                       fa_id=self.frac_keys.id)

    def update_seepage_cell_pos(self, seepage, network, coord):
        Hf2Alg.update_seepage_cell_pos(seepage=seepage, network=network,
                                       fa_id=self.frac_keys.id, coord=coord)

    def update_pore(self, seepage, manager):
        Hf2Alg.update_pore(seepage=seepage, manager=manager,
                           fa_id=self.frac_keys.id)

    def update_cond(self, seepage, network):
        Hf2Alg.update_cond(seepage=seepage, network=network,
                           fa_id=self.frac_keys.id, fw_max=0.0001)

    def create_hf2(self):
        model = Hf2Model()
        self.set_stress(model, Tensor2(xx=-10e6, yy=-11e6))
        self.set_kic(model, Tensor2(xx=1e6, yy=1e6))
        self.set_thick(model, 50)
        self.set_lave(model, 1)
        self.set_dt(model, 10)
        return model

    def add_injector(self, model, x, y, q):
        """
        在给定的位置添加一个注入点，并且同时添加一个南北方向的初始裂缝.
        """
        model.network.add_fracture(pos=(x, y - 1, x, y + 1),
                                   lave=self.get_lave(model))
        model.flow.add_injector(pos=(x, y, 0), radi=self.get_lave(model) * 3,
                                fluid_id=0,
                                flu=Seepage.FluData(den=1000, vis=0.001, vol=1.0),
                                opers=[(0, q)])

    def iterate_ddm(self, model):
        """
        向前迭代一步
        """
        self.update_seepage_topology(seepage=model.flow, network=model.network)
        self.update_seepage_cell_pos(seepage=model.flow, network=model.network,
                                     coord=Coord3())

        # 更新裂缝的高度
        thick = self.get_thick(model)
        for f in model.network.get_fractures():
            f.h = thick

        # 更新矩阵
        model.manager.update_matrix(model.network, model.sol2, self.get_stress(model), 5)

        # 更新流体
        self.update_pore(seepage=model.flow, manager=model.manager)
        self.update_cond(seepage=model.flow, network=model.network)
        model.flow.apply_injectors(dt=self.get_dt(model))
        model.flow.iterate(dt=self.get_dt(model), ca_p=self.cell_keys.pre)

        # 更新固体
        model.network.update_boundary(seepage=model.flow, fa_id=self.frac_keys.id, fh=thick)
        model.manager.update_disp()
        model.network.extend(kic=self.get_kic(model), sol2=model.sol2,
                             has_branch=False, lave=self.get_lave(model))

        self.update_time(model)


config = Config()


def test_hf2():
    model = config.create_hf2()

    q = config.get_thick(model) * 0.00004
    for x, y in [(-4, 0), (4, 0)]:
        config.add_injector(model, x, y, q=q)

    config.set_dt(model, 10)
    for step in range(200):
        gui.break_point()
        config.iterate_ddm(model)
        fn = model.network.frac_n
        time = config.get_time(model)
        print(f'step = {step}. time= {time2str(time)}, frac_n = {fn}')
        if step % 20 == 0:
            show_fn2(network=model.network, seepage=model.flow, ca_c=config.cell_keys.pre, w_max=6,
                     caption='裂缝', fa_id=config.frac_keys.id)


if __name__ == '__main__':
    gui_exec(test_hf2, close_after_done=False)
