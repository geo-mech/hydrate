# ** desc = '水平二维EGS换热计算'

from zml import *
from zmlx.config import seepage
from zmlx.filesys import path
from zmlx.utility.GuiIterator import GuiIterator
from zmlx.filesys.opath import opath
from zmlx.fluid import h2o
from zmlx.filesys.make_fname import make_fname
from zmlx.plt.show_dfn2 import show_dfn2
from zmlx.geometry.seg_point_distance import seg_point_distance
import numpy as np


def create_model(dx=100.0, dy=100.0, dz=100.0, temp=500.0, pre=10.0e6, perm=1.0e-14, porosity=0.1, denc=3e6,
                 heat_cond=2.0, vol_day=100.0, p_prod=5e6, t_inj=300.0, fl_min=10.0, fl_max=40.0,
                 angles=None, p21=0.2, f_perm=1.0e-12, has_hf=True, heating_dist=3.0):
    """
    创建模型. 其中：
        dx, dy, dz为模型的大小. (x和y方向的网格大小为1m，在z方向仅用一个网格)
        temp：储层温度
        pre：储层压力
        perm：储层渗透率
        porosity：储层孔隙度
        denc：储层岩体的密度和比热的乘积
        heat_cond：热传导系数
        vol_day：每天注入的冷水的体积
        p_prod：生产井的压力
        t_inj：注入的冷水的温度
        fl_min、fl_max：天然裂缝长度的最小值和最大值
        angles：天然裂缝的方向角度（默认不设置，则方向完全随机）
        p21：天然裂缝的密度
        f_perm：裂缝的渗透率
        has_hf: 是否在入口和出口添加人工裂缝
        heating_dist: 换热的距离（决定了流体和固体换热的效率）
    """
    assert 15.0 <= dx <= 200.0 and 15.0 <= dy <= 200.0 and 15.0 <= dz <= 200.0
    assert 300.0 <= temp <= 700.0
    assert 1e6 <= pre <= 30e6
    assert 1.0e-16 <= perm <= 1.0e-12
    assert 0.1 <= porosity <= 0.6

    jx = round(dx / 1.0)
    jy = round(dy / 1.0)
    x = np.linspace(0, dx, jx)
    y = np.linspace(0, dy, jy)
    z = [-dz / 2, dz / 2]
    mesh = SeepageMesh.create_cube(x, y, z)

    x_min, x_max = mesh.get_pos_range(0)
    y_min, y_max = mesh.get_pos_range(1)

    # 创建模型
    model = seepage.create(mesh=mesh, dt_min=1.0, dt_max=3600 * 24, dv_relative=0.5,
                           fludefs=[h2o.create(name='h2o', density=1000.0, viscosity=1.0e-3)],
                           porosity=porosity, pore_modulus=200e6, p=pre, temperature=temp,
                           denc=denc, s=1.0, perm=perm,
                           heat_cond=heat_cond, gravity=[0, 0, 0], dist=heating_dist
                           )

    # 设置随机数种子，确保生生的DFN一样
    set_srand(0)

    # 生成裂缝
    dfn = Dfn2()
    dfn.range = [x_min, y_min, x_max, y_max]

    # 添加随机裂缝
    dfn.add_frac(angles=np.linspace(0.0, 3.1415*2, 100) if angles is None else angles,
                 lengths=np.linspace(fl_min, fl_max, 100), p21=p21)

    # 添加两条人工裂缝
    if has_hf:
        dfn.add_frac(x0=x_min, y0=y_min, x1=x_max, y1=y_max)

    fractures = dfn.get_fractures()
    show_dfn2(fractures, caption='裂缝')

    # 添加裂缝
    for x0, y0, x1, y1 in dfn.get_fractures():
        print(f'add fracture: {[x0, y0, x1, y1]}. ', end='')
        cell_beg = model.get_nearest_cell(pos=[x0, y0, 0])
        cell_end = model.get_nearest_cell(pos=[x1, y1, 0])

        def get_dist(cell_pos):
            return seg_point_distance([[x0, y0], [x1, y1]], cell_pos[0: 2]) + get_distance(cell_pos, cell_end.pos)

        count = 0
        while cell_beg.index != cell_end.index:
            dist = [get_dist(c.pos) for c in cell_beg.cells]
            idx = 0
            for i in range(1, len(dist)):
                if dist[i] < dist[idx]:
                    idx = i
            cell = cell_beg.get_cell(idx)
            face = model.add_face(cell_beg, cell)
            seepage.set_face(face=face, perm=f_perm)
            count += 1
            cell_beg = cell
        print(f'count of face modified: {count}')

    # 添加注入
    assert 0 <= vol_day
    pos = [x_min, y_min, 0]
    cell = model.get_nearest_cell(pos)
    flu = cell.get_fluid(0).get_copy()
    flu.set_attr(model.reg_flu_key('temperature'), t_inj)
    model.add_injector(cell=cell, fluid_id=0, flu=flu, pos=pos, radi=2, value=vol_day / (3600 * 24))

    # 添加虚拟Cell用于产出
    virtual_cell = seepage.add_cell(model, pos=[x_max, y_max, 1000.0], porosity=1.0, pore_modulus=100e6, vol=1.0e10,
                                    temperature=temp, p=p_prod, s=1.0)
    cell = model.get_nearest_cell([x_max, y_max, 0])
    seepage.add_face(model, virtual_cell, cell, heat_cond=0, perm=perm, area=1.0, length=1.0)

    # 返回模型
    return model


def plot_cells(model, folder=None):
    """
    绘图（给定folder的时候保存图片）
    """
    if not gui.exists():
        return
    from zmlx.plt.tricontourf import tricontourf
    assert isinstance(model, Seepage)

    time = time2str(seepage.get_time(model))
    year = seepage.get_time(model) / (3600 * 24 * 365)

    x = model.numpy.cells.x
    y = model.numpy.cells.y
    x = x[: -1]
    y = y[: -1]

    def show_ca(idx, name):
        p = model.numpy.cells.get(idx)
        p = p[: -1]
        tricontourf(x, y, p, caption=name, title=f'time = {time}',
                    fname=make_fname(year, path.join(folder, name), '.jpg', 'y'))

    # 流体压力和岩石温度
    show_ca(-12, 'pressure')
    show_ca(model.get_cell_key('temperature'), 'rock_temp')

    # 显示流体温度
    t = model.numpy.fluids(0).get(index=model.reg_flu_key('temperature'))
    t = t[: -1]
    tricontourf(x, y, t, caption='流体温度', title=f'time = {time}',
                fname=make_fname(year, path.join(folder, 'flu_temp'), '.jpg', 'y'))


def solve(model: Seepage, time_max=3600 * 24 * 365 * 30, folder=None):
    if folder is not None:
        print_tag(folder)
        print(f'Solve. folder = {folder}')
        if gui.exists():
            gui.title(f'Data folder = {folder}')

    solver = ConjugateGradientSolver(tolerance=1.0e-14)
    iterate = GuiIterator(seepage.iterate, lambda: plot_cells(model, folder=path.join(folder, 'figures')))

    while seepage.get_time(model) < time_max:
        iterate(model, solver=solver)
        step = seepage.get_step(model)
        if step % 10 == 0:
            time = time2str(seepage.get_time(model))
            dt = time2str(seepage.get_dt(model))
            print(f'step = {step}, dt = {dt}, time = {time}')


def execute(folder=None, time_max=3600 * 24 * 365 * 10, **kwargs):
    """
    执行建模和计算的全过程
    """
    model = create_model(**kwargs)
    print(model)
    solve(model, folder=folder, time_max=time_max)


def _test3():
    execute(folder=opath('egs2'))


if __name__ == '__main__':
    from zmlx.ui.GuiBuffer import gui
    gui.execute(_test3, close_after_done=False, disable_gui=False)

