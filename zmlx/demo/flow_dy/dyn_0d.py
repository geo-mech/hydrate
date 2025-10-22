# ** desc = '模拟两个Cell，在压力和惯性的作用下，反复震荡的过程'

from zmlx import *


def set_cell(c: Seepage.Cell, p):
    c.set_pore(p=1, v=1, dp=1, dv=0.5)
    c.fluid_number = 1
    c.get_fluid(0).vol = c.p2v(p)
    print(c.pre)


def main():
    model = Seepage()

    set_cell(model.add_cell(), 1)
    set_cell(model.add_cell(), 2)
    f = model.add_face(0, 1)
    f.cond = 1

    ca_p = model.reg_cell_key('p')
    fa_k = model.reg_face_key('k')
    fa_q = model.reg_face_key('q')
    fa_s = model.reg_face_key('s')

    f.set_attr(fa_k, 1)
    f.set_attr(fa_q, 0)
    f.set_attr(fa_s, 1)

    c0 = model.get_cell(0)
    c1 = model.get_cell(1)
    f = model.get_face(0)

    vt = []
    vq = []
    p0 = []
    p1 = []

    def show(fig):
        xy1 = item('xy', vt, vq)
        xy2 = item('xy', vt, p0, label='p0')
        xy3 = item('xy', vt, p1, label='p1')
        add_axes2(fig, add_items, xy1, nrows=2, ncols=1, index=1, xlabel='x', ylabel='q')
        add_axes2(fig, add_items, xy2, xy3, item('legend'), nrows=2, ncols=1, index=2, xlabel='x', ylabel='p')

    for step in range(200):
        gui.break_point()
        r = model.iterate(dt=0.1, fa_s=fa_s, fa_q=fa_q, fa_k=fa_k, ca_p=ca_p)
        vt.append(step)
        vq.append(f.get_attr(fa_q))
        p0.append(c0.pre)
        p1.append(c1.pre)
        if step % 10 == 0:
            plot(show, caption='当前状态', tight_layout=True)
            print(f'step = {step}, r = {r}')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
