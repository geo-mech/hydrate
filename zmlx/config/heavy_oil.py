from zml import Seepage, create_dict, ConjugateGradientSolver
from zmlx.alg.time2str import time2str
from zmlx.config import seepage
from zmlx.fluid import c11h24
from zmlx.fluid import char
from zmlx.fluid import kerogen
from zmlx.fluid import oil
from zmlx.fluid.ch4 import create as create_ch4
from zmlx.fluid.h2o import create as create_h2o
from zmlx.fluid.h2o_gas import create as create_steam
from zmlx.kr.create_krf import create_krf
from zmlx.plt.plotxy import plotxy
from zmlx.plt.tricontourf import tricontourf
from zmlx.react import decomposition
from zmlx.react import vapor
from zmlx.seepage_mesh import cube
from zmlx.ui import gui
from zmlx.utility.GuiIterator import GuiIterator
from zmlx.utility.SeepageNumpy import as_numpy


def create_fludefs():
    """
    创建流体定义.
        0. gas    1. wat     2. light oil     3. heavy oil     4. solid
    """
    gas = Seepage.FluDef(name='gas')
    gas.add_component(create_ch4(name='ch4'))
    gas.add_component(create_steam(name='steam'))

    wat = create_h2o(name='h2o')
    lo = c11h24.create(name='lo')
    ho = oil.create(name='ho')

    sol = Seepage.FluDef(name='sol')
    sol.add_component(kerogen.create(), name='kerogen')
    sol.add_component(char.create(den=1800), name='char')

    # 返回定义
    return [gas, wat, lo, ho, sol]


def create_reactions():
    """
    创建反应
    """
    result = []

    # h2o and steam
    r = vapor.create(vap='steam', wat='h2o')
    result.append(r)

    # The decomposition of Kerogen.
    r = decomposition.create(left='kerogen',
                             right=[('ho', 0.6), ('lo', 0.1), ('h2o', 0.1), ('ch4', 0.1), ('char', 0.1)],
                             temp=565, heat=161600.0,  # From Maryelin 2023-02-23
                             rate=1.0e-8)
    result.append(r)

    # The decomposition of Heavy oil
    r = decomposition.create(left='ho',
                             right=[('lo', 0.5), ('ch4', 0.2), ('char', 0.3)],
                             temp=603, heat=206034.0,  # From Maryelin 2023-02-23
                             rate=1.0e-8)
    r['inhibitors'].append(create_dict(sol='sol',
                                       liq=None,
                                       c=[0, 0.8, 1.0],
                                       t=[0, 0, 1.0e4]))  # 当固体占据的比重达到80%之后，增加裂解温度，从而限制继续分解
    result.append(r)

    return result


def create_ini():
    """
    创建初始场
    """
    return {'porosity': 0.2, 'pore_modulus': 500e6, 'p': 20e6, 'temperature': 350.0,
            'denc': 4e6, 's': [(0.2, 0.0), 0.1, 0.1, 0.3, (0.3, 0)],
            'perm': 1e-15, 'heat_cond': 2, 'dist': 0.1}


def create_kwargs(gr=None, **kwargs):
    """
    返回用于seepage.create的参数列表
    """
    fludefs = create_fludefs()
    reactions = create_reactions()
    x, y = create_krf(faic=0.02, n=3.0, k_max=20, s_max=3.0, count=300)
    if gui.exists():
        plotxy(x, y, caption='gr')
    kw = create_dict(fludefs=fludefs, reactions=reactions,
                     gr=create_krf(faic=0.02, n=2.0, as_interp=True) if gr is None else gr,
                     has_solid=True, **kwargs)
    kw.update(**create_ini())
    return kw


def create_model():
    """
    建立模型
    """
    # 创建mesh
    mesh = cube.create_xz(x_min=0, dx=1, x_max=100, z_min=-100, dz=1, z_max=0, y_min=0, y_max=1)

    # 创建kw
    kw = create_kwargs()

    # 限定时间步长
    kw.update(create_dict(dt_max=3600 * 24))

    # 创建模型
    model = seepage.create(mesh=mesh, **kw)

    # 添加注热
    ca = seepage.cell_keys(model)
    model.add_injector(pos=[50, 0, -50], radi=3, value=1.0e4, ca_mc=ca.mc, ca_t=ca.temperature)

    # 成功
    return model


def show_2d(model: Seepage, xdim=0, ydim=1):
    """
    二维绘图
    """
    if not gui.exists():
        return
    time = seepage.get_time(model)
    kwargs = {'title': f'plot when model.time={time2str(time)}'}
    x = as_numpy(model).cells.get(-(xdim + 1))
    y = as_numpy(model).cells.get(-(ydim + 1))

    cell_keys = seepage.cell_keys(model)

    def show_key(key):
        tricontourf(x, y, as_numpy(model).cells.get(cell_keys[key]), caption=key,
                    **kwargs)

    show_key('pre')
    show_key('temperature')

    fv_all = as_numpy(model).cells.fluid_vol

    def show_s(flu_name):
        s = as_numpy(model).fluids(*model.find_fludef(flu_name)).vol / fv_all
        tricontourf(x, y, s, caption=flu_name, **kwargs)

    for item in ['ch4', 'lo', 'ho', 'steam', 'char']:
        show_s(item)


def solve(model):
    """
    求解模型
    """
    solver = ConjugateGradientSolver()
    solver.set_tolerance(1e-13)

    def show():
        show_2d(model, xdim=0, ydim=2)

    iterate = GuiIterator(seepage.iterate, show)

    while seepage.get_time(model) < 3600 * 24 * 365 * 10:
        r = iterate(model, solver=solver)
        step = seepage.get_step(model)
        if step % 10 == 0:
            print(
                f'step = {step}, dt = {time2str(seepage.get_dt(model))}, '
                f'time = {time2str(seepage.get_time(model))}, '
                f'report={r}')
    show()


def execute():
    """
    执行建模和求解
    """
    model = create_model()
    solve(model)


if __name__ == '__main__':
    gui.execute(execute, close_after_done=False)
