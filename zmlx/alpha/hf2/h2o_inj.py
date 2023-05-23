from zmlx import *
from zmlx.fluid import *
from zmlx.alpha.hf2.Attrs import *
from zmlx.alpha.hf2.save_c14 import save_c14
from zmlx.alpha.hf2.create_fractures import create_fractures
from random import uniform


def create():
    # 首先，创建一个空的模型.
    model = seepage.create(disable_ther=True, disable_heat_exchange=True,
                           dt_max=3600 * 24, dt_min=1, fluids=[create_ch4(), create_h2o()])

    # 添加裂缝
    model.append(create_fractures())

    # 设置Cell的vol属性
    fw = 1.0e-3
    ca = CellAttrs(model)
    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        ca.set_vol(cell, ca.get_fs(cell) * fw)

    # Face的长度和面积属性
    fa = FaceAttrs(model)
    for face in model.faces:
        assert isinstance(face, Seepage.Face)
        tag = fa.get_tag(face)
        assert tag == 1 or tag == 2
        if tag == 1:
            # 主裂缝
            times = 1.0 - (clamp(abs(face.pos[2]), 0, 25) / 25) ** 0.5
            if abs(face.get_cell(0).pos[2] - face.get_cell(1).pos[2]) > 0.1:
                times = times * 0.1  # 纵向的
            fa.set_s(face, fw * 10 * clamp(times, 0.0, 1))
        else:
            fa.set_s(face, fw * 0.5 * uniform(0, 1.0))
        fa.set_length(face, 1.0)

    # 进行初始的填充
    x = np.linspace(0.0, 100.0, 1000)
    y = x ** 2
    igr = model.add_gr(Interp1(x=x, y=y), need_id=True)
    seepage.set_init(model, porosity=0.2, pore_modulus=100e6, p=1, temperature=280,
                     s=(1, 0), perm=1e-14, igr=igr)

    # 添加一个注入点
    cell = model.get_nearest_cell(pos=(0, 0, 0))
    model.add_injector(fluid_id=1, flu=cell.get_fluid(1), pos=cell.pos,
                       radi=0.1, opers=[(0, 1.0e-6)])

    ca = seepage.CellAttrs(model)
    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        fv0 = cell.p2v(1.0e6)
        ca.set_fv0(cell, fv0)

    # 设置Cell是否处于打开的状态
    ca_open = model.reg_cell_key('is_open')
    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        cell.set_attr(ca_open, 0)

    return model


def solve(model):
    ca = CellAttrs(model)

    def get_c(cell):
        # 返回压力(主裂缝增大压力，让它看上去更加明显. )
        if ca.get_tag(cell) == 1:
            return cell.pre + 30e6
        else:
            return cell.pre

    def get_a(cell):
        if ca.get_tag(cell) == 1:
            return cell.get_fluid(1).vol_fraction
        else:
            return cell.get_fluid(1).vol_fraction * 0.5

    for step in range(20000):
        r = seepage.iterate(model)
        if step % 100 == 0:
            dt, t = time2str(seepage.get_dt(model)), time2str(seepage.get_time(model))
            print(f'step = {step}, dt = {dt}, time = {t}, report={r}')
            save_c14(make_fpath(opath('h2o_inj'), step, '.c14'), model, get_a=get_a, get_c=get_c)


def execute():
    solve(create())


if __name__ == '__main__':
    execute()
