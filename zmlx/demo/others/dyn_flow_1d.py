# ** desc = '一维的模型，初始一端的压力比较高，计算此压力的传递和震荡过程'

from zmlx import *
from zmlx.plt.on_figure import add_axes2

def set_cell(c: Seepage.Cell, p):
    c.set_pore(p=1, v=1, dp=1, dv=0.5)
    c.fluid_number = 1
    c.get_fluid(0).vol = c.p2v(p)
    print(c.pre)


def main():
    model = Seepage()

    for idx in range(30):
        set_cell(model.add_cell(), 2.0 if idx < 10 else 1.0)

    for idx in range(1, model.cell_number):
        i0 = idx - 1
        i1 = idx
        f = model.add_face(i0, i1)
        f.cond = 1

    ca_p = model.reg_cell_key('p')
    fa_k = model.reg_face_key('k')
    fa_q = model.reg_face_key('q')
    fa_s = model.reg_face_key('s')

    for f in model.faces:
        f.set_attr(fa_k, 1)
        f.set_attr(fa_q, 0)
        f.set_attr(fa_s, 1)

    def on_figure(figure):
        ax = add_axes2(figure, None, nrows=2, ncols=1, index=1, xlabel='x', ylabel='pressure')
        ax.plot(list(range(model.cell_number)), as_numpy(model).cells.pre)
        ax = add_axes2(figure, None, nrows=2, ncols=1, index=2, xlabel='x', ylabel='flow rate')
        ax.plot(list(range(model.face_number)), as_numpy(model).faces.get_attr(fa_q))

    for step in range(2000):
        gui.break_point()
        r = model.iterate(dt=0.1, fa_s=fa_s, fa_q=fa_q, fa_k=fa_k, ca_p=ca_p)
        if step % 10 == 0:
            plot(on_figure)
        print(f'step = {step}, r = {r}')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
