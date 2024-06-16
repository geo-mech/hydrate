# ** desc = '基于井筒换热的地热开发模拟'


import numpy as np

from zml import Seepage
from zmlx.config import seepage
from zmlx.plt.plotxy import plotxy
from zmlx.seepage_mesh.create_wellbore import create_wellbore
from zmlx.seepage_mesh.cube import create_cube
from zmlx.ui import gui
from zmlx.utility.SeepageNumpy import as_numpy


def create_well():
    """
    创建井筒模型.
    """
    mesh = create_wellbore(trajectory=[[0, 50, 0], [100, 50, 0]], length=1, area=0.01)
    # 井筒的总的体积
    mesh_vol = mesh.volume
    print(f'The mesh volume = {mesh_vol}')
    mesh.get_cell(-1).vol = 1e6

    # 创建水的单相流动计算模型
    model = seepage.create(mesh=mesh,
                           dv_relative=0.8,
                           dt_max=3600,
                           fludefs=[Seepage.FluDef(name='h2o', den=1000, vis=0.001,
                                                   specific_heat=4200.0)],
                           porosity=1,
                           pore_modulus=200e6,
                           heat_cond=2.0,
                           p=1e6,
                           s=1.0,
                           denc=1e10,  # 设置得非常大，从而确保温度不变
                           dist=0.1,  # 换热的距离
                           temperature=400,  # 原始的温度
                           perm=1e-11,  # 这个应该和流量对应
                           gravity=[0, 0, 0],  # 鉴于我们虚拟单元的设置，最好将重力设置为0
                           warnings_ignored={'gravity'},
                           tags=['disable_update_den', 'disable_update_vis',
                                 'disable_ther']
                           )

    for cell in model.cells:
        print(cell.get_attr(model.reg_cell_key('g_heat')))

    # 从第一个cell来注入
    rate_inj = 1e-6
    cell = model.get_cell(0)
    flu = cell.get_fluid(0).get_copy()
    flu.set_attr(index=model.reg_flu_key('temperature'), value=273.15 + 50)
    model.add_injector(cell=cell,
                       value=rate_inj,
                       fluid_id='h2o',
                       flu=flu
                       )

    # 用来交换的cell的id
    swap_mask = [True for _ in range(model.cell_number)]
    swap_mask[-1] = False
    model.set_text('swap_mask', swap_mask)

    # 配置求解的选项
    seepage.set_solve(model, time_forward=mesh_vol*2 / rate_inj)

    return model


def solve_wellbore(model, close_after_done=None):
    mask = eval(model.get_text('swap_mask'))

    def plot():
        x = as_numpy(model).cells.x[mask]
        p = as_numpy(model).cells.pre[mask]
        plotxy(x, p, caption='well_p',
               title=f'time = {seepage.get_time(model, as_str=True)}')

        t = as_numpy(model).fluids(0).get(
            index=model.reg_flu_key('temperature'))[mask]
        plotxy(x, t, caption='well_T',
               title=f'time = {seepage.get_time(model, as_str=True)}')

    seepage.solve(model, extra_plot=plot, close_after_done=close_after_done)


def test_1():
    solve_wellbore(create_well(), close_after_done=False)


def create_reservoir(wellbore_model: Seepage):
    mesh = create_cube(np.linspace(0, 100, 100),
                       np.linspace(0, 100, 100),
                       (-0.5, 0.5))

    # 井筒的轨迹
    swap_mask = eval(wellbore_model.get_text('swap_mask'))
    vx = as_numpy(wellbore_model).cells.x[swap_mask]
    vy = as_numpy(wellbore_model).cells.y[swap_mask]
    vz = as_numpy(wellbore_model).cells.z[swap_mask]

    swap_mask = [False for _ in range(mesh.cell_number)]

    for idx in range(len(vx)):
        x, y, z = vx[idx], vy[idx], vz[idx]

        c = mesh.add_cell()
        c.pos = [1e6, 0, 0]  # 设置一个虚拟的位置，非常远，从而在绘图的时候，根据距离将其排除
        c.vol = 1e6  # 设置得非常大，从而确保温度不变

        # 建立连接
        f = mesh.add_face(c, mesh.get_nearest_cell(pos=[x, y, z]))
        f.area = 1
        f.length = 1

        swap_mask.append(True)  # 这些cell用来交换

    model = seepage.create(mesh=mesh,
                           temperature=400,
                           denc=1.0e6,
                           heat_cond=2.0,
                           dt_max=24.0 * 3600.0 * 10.0,
                           )

    model.set_text('swap_mask', swap_mask)  # 交换区

    # 用于求解的选项
    mask = seepage.get_cell_mask(model, xr=[-1000, 1000])
    seepage.set_solve(model,
                      show_cells={'dim0': 0, 'dim1': 1, 'show_p': False, 'mask': mask},
                      time_forward=60 * 24 * 3600
                      )
    return model


def get_cell_t(model: Seepage):
    mask = eval(model.get_text('swap_mask'))
    buf = as_numpy(model).cells.get(index=model.reg_cell_key('temperature'))
    return buf[mask]


def set_cell_t(model: Seepage, vt):
    mask = eval(model.get_text('swap_mask'))
    buf = as_numpy(model).cells.get(index=model.reg_cell_key('temperature'))
    buf[mask] = vt
    as_numpy(model).cells.set(index=model.reg_cell_key('temperature'), buf=buf)


def get_flu_t(model: Seepage):
    mask = eval(model.get_text('swap_mask'))
    buf = as_numpy(model).fluids(0).get(index=model.reg_flu_key('temperature'))
    return buf[mask]


def test_2():
    model = create_reservoir(wellbore_model=create_well())
    mask = eval(model.get_text('swap_mask'))
    vt = [300 for x in mask if x]
    set_cell_t(model, vt)
    seepage.solve(model, close_after_done=False)


def test_3():
    wellbore = create_well()
    res = create_reservoir(wellbore_model=wellbore)

    def solve():
        while seepage.get_time(res) < 10 * 365 * 24 * 3600:
            # 读取储层温度并设置给井筒
            set_cell_t(wellbore, get_cell_t(res))
            # 井筒迭代
            seepage.set_time(wellbore, seepage.get_time(res))   # 同步时间
            solve_wellbore(wellbore)
            # 读取井筒的温度，并设置给储层
            set_cell_t(res, get_flu_t(wellbore))
            # 储层迭代
            seepage.solve(res)

    gui.execute(func=solve, close_after_done=False)


if __name__ == '__main__':
    test_3()
