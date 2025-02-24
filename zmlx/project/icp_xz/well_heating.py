from icp_xz.create import create
from icp_xz.mesh import create_mesh
from icp_xz.opath import opath
from icp_xz.solve import solve
from zml import Seepage, is_windows, Tensor3
from zmlx.ui import gui


def well_heating(folder=None, perm=None, power=None,
                 gui_mode=None, dx=None, dz=None,
                 heat_cond=None,
                 years_heating=None, years_balance=None,
                 years_prod=None, years_flooding=None,
                 close_after_done=True,
                 s=None,
                 q_flooding=None,
                 **space):
    """
    执行建模和求解 (井筒电加热).
        竖直模型;
        power为加热的功率，temp为加热的温度，两者只能指定一个（并且必须指定一个）;
    """
    if years_heating is None:
        years_heating = 10.0

    if years_balance is None:
        years_balance = 5.0

    if years_prod is None:
        years_prod = 5.0

    if years_flooding is None:
        years_flooding = 5.0

    if power is None:
        power = 1e3  # 每米的储层加热的功率

    if heat_cond is None:
        heat_cond = 2.0

    if perm is None:
        perm = 1.0e-15

    if dx is None:
        dx = 0.3

    if dz is None:
        dz = 0.3

    if q_flooding is None:
        q_flooding = 0.1 / (24 * 3600)

    # 创建mesh(注意，这里的y代表了竖直方向)
    mesh = create_mesh(dx=dx, dz=dz)

    # 注入的流体的属性
    flu = Seepage.FluData(den=1000, vis=0.001, mass=1e6)
    flu.set_attr(0, 300)
    flu.set_attr(1, 4200)

    t1 = years_heating * 24 * 3600 * 365  # 加热结束，开始焖井
    t2 = t1 + years_balance * 24 * 3600 * 365  # 焖井结束开始降压
    t3 = t2 + years_prod * 24 * 3600 * 365  # 降压生产结束，开始驱替
    t4 = t3 + 3600.0 * 24.0 * 365.0 * years_flooding
    assert t3 >= t1

    def make_inj(pos):
        return dict(value=power, pos=pos,
                           opers=[[t1, f'val {0.0}'],
                                  [t3, f'fid 1'],
                                  [t3, f'val {q_flooding}'],
                                  ],
                           flu=flu,  # 注入的流体属性
                           )

    def run():
        create(space, mesh=mesh,
               perm=Tensor3(xx=perm * 3, yy=perm * 3, zz=perm),
               injectors=[make_inj([15.0, 0, -7.5]),
                          make_inj([15.0, 0, +7.5])],
               heat_cond=Tensor3(xx=heat_cond,
                                 yy=heat_cond,
                                 zz=heat_cond / 3),
               s=s,
               z_max=15, z_min=-15,
               operations=[[t2, 'outlet', True]]  # 在t2的时候，打开出口，开始生产;
               )
        solve(space, folder=folder, time_max=t4)

    if gui_mode is None:
        gui_mode = is_windows

    gui.execute(run, close_after_done=close_after_done,
                disable_gui=not gui_mode)


if __name__ == '__main__':
    well_heating(folder=opath('well_heating_base'))
