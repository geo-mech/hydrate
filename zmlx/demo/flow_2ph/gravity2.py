# ** desc = '重力驱动下的气水分层'


from zmlx import *


def main():
    from zmlx.demo.flow_2ph.gravity import show, create
    def get_s(x, y, z):
        if x > 150:
            return {'ch4': 0.2, 'h2o': 0.8}
        else:
            return {'ch4': 0.8, 'h2o': 0.2}

    jx, jz = 30, 100
    model = create(jx, jz, s=get_s)
    show(model, jx, jz, caption='初始状态')
    seepage.solve(model, close_after_done=False, extra_plot=lambda: show(model, jx, jz, caption='当前状态'),
                  time_forward=3600 * 24 * 365 * 100
                  )


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
