# ** desc = '一维的模型，初始一端的压力比较高，计算此压力的传递和震荡过程'

from zmlx import *


def set_cell(c: Seepage.Cell, p):
    c.set_pore(p=1, v=1, dp=1, dv=0.5)
    c.fluid_number = 1
    c.get_fluid(0).vol = c.p2v(p)


def main():
    model = Seepage()

    for idx in range(30):
        set_cell(model.add_cell(), 2.0 if idx < 10 else 1.0)

    for idx in range(1, model.cell_number):
        f = model.add_face(idx - 1, idx)
        f.cond = 0.1

    ca_p = model.reg_cell_key('p')
    fa_k = model.reg_face_key('k')
    fa_q = model.reg_face_key('q')
    fa_s = model.reg_face_key('s')

    for f in model.faces:
        f.set_attr(fa_k, 1)
        f.set_attr(fa_q, 0)
        f.set_attr(fa_s, 1)

    def add_curves(fig):
        add_axes2(fig, add_curve2, list(range(model.cell_number)), as_numpy(model).cells.pre, nrows=2, ncols=1,
                  index=1, xlabel='x', ylabel='pressure', title='pressure')
        add_axes2(fig, add_curve2, list(range(model.face_number)), as_numpy(model).faces.get_attr(fa_q), nrows=2,
                  ncols=1, index=2, xlabel='x', ylabel='flow rate', title='flow rate')

    for step in range(2000):
        gui.break_point()
        r = model.iterate(dt=0.1, fa_s=fa_s, fa_q=fa_q, fa_k=fa_k, ca_p=ca_p)
        if step % 10 == 0:
            plot(add_curves, caption='当前状态', tight_layout=True)
        print(f'step = {step}, r = {r}')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
