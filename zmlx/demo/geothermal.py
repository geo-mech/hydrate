# ** desc = '基于井筒换热的地热开发模拟'


import numpy as np

from zml import Seepage
from zmlx.config import seepage
from zmlx.filesys.join_paths import join_paths
from zmlx.plt.plotxy import plotxy
from zmlx.seepage_mesh.create_wellbore import create_wellbore
from zmlx.seepage_mesh.cube import create_cube
from zmlx.ui import gui
from zmlx.utility.Field import Field
from zmlx.utility.GuiIterator import GuiIterator
from zmlx.utility.SeepageNumpy import as_numpy


def create_well(rate_inj=None, temp_inj=None, heat_cond=2.0):
    """
    创建井筒模型.
    """
    mesh = create_wellbore(trajectory=[[0, 50, 0], [100, 50, 0]],
                           length=1, area=0.01)
    # 井筒的总的体积
    mesh_vol = mesh.volume
    mesh.get_cell(-1).vol = 1e6

    if rate_inj is None:
        rate_inj = 1.0e-6

    assert 0 < rate_inj <= 1

    # 将导热系数视为一个三维的场
    heat_cond = Field(heat_cond)

    fludefs = [Seepage.FluDef(name='h2o', den=1000, vis=0.001,
                              specific_heat=4200.0)]

    # 创建水的单相流动计算模型
    model = seepage.create(mesh=mesh,
                           dv_relative=0.8,
                           dt_max=3600 * 24.0,
                           fludefs=fludefs,
                           porosity=1,
                           pore_modulus=200e6,
                           heat_cond=heat_cond,
                           p=1e6,
                           s=1.0,
                           denc=1e20,  # 设置得非常大，从而确保温度不变
                           dist=0.1,  # 换热的距离
                           temperature=400,  # 原始的温度
                           perm=1e-11 * rate_inj / 1e-6,  # 这个应该和流量对应(当rate增大的时候，同步增大)
                           gravity=[0, 0, 0],  # 鉴于我们虚拟单元的设置，最好将重力设置为0
                           tags=['disable_update_den', 'disable_update_vis',
                                 'disable_ther'],
                           warnings_ignored={'gravity'},
                           )

    if temp_inj is None:
        temp_inj = 273.15 + 50  # 默认注入50摄氏度的水

    # 从第一个cell来注入
    cell = model.get_cell(0)
    flu = cell.get_fluid(0).get_copy()
    flu.set_attr(index=model.reg_flu_key('temperature'), value=temp_inj)
    model.add_injector(cell=cell,
                       value=rate_inj,
                       fluid_id='h2o',
                       flu=flu
                       )

    # 用来交换的cell的id
    swap = [True for _ in range(model.cell_number)]
    swap[-1] = False
    model.set_text('swap', swap)

    # 配置求解的选项
    seepage.set_solve(model, time_forward=mesh_vol * 2 / rate_inj)

    return model


def solve_well(model, close_after_done=None, folder=None, gui_iter=None,
               **kwargs):
    swap = eval(model.get_text('swap'))

    def plot():
        if gui.exists():
            title = f'time = {seepage.get_time(model, as_str=True)}'
            x = as_numpy(model).cells.x[swap]
            p = as_numpy(model).cells.pre[swap]
            plotxy(x, p, caption='well_p', title=title)

            t = as_numpy(model).fluids(0).get(
                index=model.reg_flu_key('temperature'))[swap]
            plotxy(x, t, caption='well_T', title=title)

    seepage.solve(model, extra_plot=plot, close_after_done=close_after_done,
                  folder=folder, gui_iter=gui_iter, state_hint='well',
                  **kwargs)


def create_res(well: Seepage, heat_cond=2.0):
    mesh = create_cube(np.linspace(0, 100, 100),
                       np.linspace(0, 100, 100),
                       (-0.5, 0.5))

    # 井筒的轨迹
    swap = eval(well.get_text('swap'))
    vx = as_numpy(well).cells.x[swap]
    vy = as_numpy(well).cells.y[swap]
    vz = as_numpy(well).cells.z[swap]
    vg = as_numpy(well).cells.get(index=well.reg_cell_key('g_heat'))[swap]  # 导热的能力

    i_swap = [False for _ in range(mesh.cell_number)]
    o_index = []
    # 将导热系数视为一个三维的场
    heat_cond = Field(heat_cond)

    for idx in range(len(vx)):
        x, y, z = vx[idx], vy[idx], vz[idx]

        c = mesh.add_cell()
        c.pos = [1e6, 0, 0]  # 设置一个虚拟的位置，非常远，从而在绘图的时候，根据距离将其排除
        c.vol = 1e6  # 设置得非常大，从而确保温度不变

        # 建立连接
        c2 = mesh.get_nearest_cell(pos=[x, y, z])
        f = mesh.add_face(c, c2)
        f.area = 0  # 后续设置g_heat
        f.length = 1

        # 交换区
        i_swap.append(True)  # 这些cell用来交换
        o_index.append(c2.index)

    model = seepage.create(mesh=mesh,
                           temperature=273.15 + 200.0,  # 200摄氏度
                           denc=5.0e6,
                           heat_cond=heat_cond,
                           dv_relative=0.5,
                           dt_max=3600 * 24 * 10,
                           )

    # 设置导热能力
    face_n0 = model.face_number - len(vx)
    for idx in range(len(vx)):
        model.get_face(face_n0 + idx).set_attr(model.reg_face_key('g_heat'), vg[idx])

    model.set_text('i_swap', i_swap)
    model.set_text('o_index', o_index)

    # 用于求解的选项
    mask = seepage.get_cell_mask(model,
                                 xr=[-1000, 1000])
    seepage.set_solve(model,
                      show_cells={'dim0': 0, 'dim1': 1,
                                  'show_p': False,
                                  'mask': mask},
                      time_forward=60 * 24 * 3600
                      )
    return model


def get_cell_t(model: Seepage):
    buf = as_numpy(model).cells.get(index=model.reg_cell_key('temperature'))
    text = model.get_text('o_index')
    if len(text) > 0:
        o_index = eval(text)
        temp = [buf[i] for i in o_index]
        return np.array(temp)
    else:
        swap = eval(model.get_text('swap'))
        return buf[swap]


def set_cell_t(model: Seepage, vt):
    text = model.get_text('i_swap')
    if len(text) > 0:
        swap = eval(text)
    else:
        swap = eval(model.get_text('swap'))
    buf = as_numpy(model).cells.get(index=model.reg_cell_key('temperature'))
    buf[swap] = vt
    as_numpy(model).cells.set(index=model.reg_cell_key('temperature'),
                              buf=buf)


def get_flu_t(model: Seepage):
    swap = eval(model.get_text('swap'))
    buf = as_numpy(model).fluids(0).get(index=model.reg_flu_key('temperature'))
    return buf[swap]


def test_1():
    solve_well(create_well(), close_after_done=False, time_max=1e10)


def test_2():
    heat_cond = 2
    well = create_well(heat_cond=heat_cond, rate_inj=1.0e-6)
    res = create_res(well=well, heat_cond=heat_cond)
    swap = eval(res.get_text('swap'))
    vt = [300 for x in swap if x]
    set_cell_t(res, vt)
    seepage.set_solve(res,
                      time_forward=6000 * 24 * 3600
                      )
    seepage.solve(res, close_after_done=False)


def main(folder=None):
    def solve():
        heat_cond = 2
        well = create_well(heat_cond=heat_cond, rate_inj=1.0e-5)
        res = create_res(well=well, heat_cond=heat_cond)

        gui_iter = GuiIterator()

        while seepage.get_time(res) < 10 * 365 * 24 * 3600:
            seepage.set_time(well, seepage.get_time(res))  # 同步时间
            # 读取储层温度并设置给井筒
            set_cell_t(well, get_cell_t(res))
            # 井筒迭代
            solve_well(well, folder=join_paths(folder, 'well'),
                       gui_iter=gui_iter)
            # 读取井筒的温度，并设置给储层
            set_cell_t(res, get_flu_t(well))
            # 储层迭代
            seepage.solve(res, folder=join_paths(folder, 'res'),
                          gui_iter=gui_iter, state_hint='res')

    gui.execute(func=solve, close_after_done=False, disable_gui=False)


if __name__ == '__main__':
    main()
