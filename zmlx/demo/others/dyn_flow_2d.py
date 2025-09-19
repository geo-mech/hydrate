# ** desc = '二维的模型，初始左下角位置的压力比较高，模拟这个压力波扩散-震荡的过程'

from zmlx import *
from zmlx.plt.on_axes import *
from zmlx.plt.on_figure import add_axes2


def set_cell(c: Seepage.Cell, p):
    c.set_pore(p=1, v=1, dp=1, dv=0.5)
    c.fluid_number = 1
    c.get_fluid(0).vol = c.p2v(p)
    return c


def main():
    model = Seepage()
    mesh = create_cube(x=linspace(0, 1, 50),
                       y=linspace(0, 1, 50),
                       z=(-0.5, 0.5)
                       )
    for c in mesh.cells:
        x, y, z = c.pos
        if point_distance([x, y], [0.4, 0.4]) < 0.2:
            p = 2
        else:
            p = 1
        set_cell(model.add_cell(), p).pos = [x, y, z]

    for f in mesh.faces:
        model.add_face(f.cell_i0, f.cell_i1).cond = 1

    ca_p = model.reg_cell_key('p')
    fa_k = model.reg_face_key('k')
    fa_q = model.reg_face_key('q')
    fa_s = model.reg_face_key('s')

    for f in model.faces:
        f.set_attr(fa_k, 1)
        f.set_attr(fa_q, 0)
        f.set_attr(fa_s, 1)

    x = as_numpy(model).cells.x
    y = as_numpy(model).cells.y

    for step in range(300):
        gui.break_point()
        r = model.iterate(dt=0.1, fa_s=fa_s, fa_q=fa_q, fa_k=fa_k, ca_p=ca_p)
        if step % 5 == 0:
            plot(add_axes2, tricontourf, x, y, as_numpy(model).cells.pre, xlabel='x', ylabel='y',
                 cbar=dict(label='Pressure', shrink=0.8), aspect='equal', tight_layout=True)
        print(f'step = {step}, r = {r}')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
