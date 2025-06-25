# ** desc = '测试仅仅在重力作用下的单相渗流过程'
"""
经过测试，流体从顶部在重力的作用下，渗透到底部用时大约2e6秒，下面，基于达西定律来估算.

Q = dp*k*S/(L*mu) = 1e4 * 1e-14 * 1 / (1 * 1e-3) = 1e-7 m3/s

流体体积为 0.2方米， 因此，时间为 0.2 / 1e-7 = 2e6 s

这与计算出的结果一致。
"""

from zmlx import *

STEP_MAX = 100000000


def create():
    mesh = create_cube(
        x=linspace(-0.5, 0.5, 10), y=[-0.5, 0.5], z=linspace(-0.5, 0.5, 100)
    )
    z_min, z_max = get_pos_range(mesh, 2)

    def porosity(*pos):
        if abs(pos[2] - z_min) < 1.0e-4 or abs(pos[2] - z_max) < 1.0e-4:
            return 1.0e10
        else:
            return 0.2

    model = seepage.create(
        mesh=mesh, dv_relative=0.5,
        fludefs=[Seepage.FluDef(name='h2o')],
        porosity=porosity,
        p=2e6, s=1.0,
        perm=10e-15,
        gravity=[0, 0, -10]
    )
    model.add_tag('disable_update_den', 'disable_update_vis', 'disable_ther')

    key = model.reg_flu_key('time')
    top_ids = []
    btm_ids = []

    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        cell.get_fluid(0).set_attr(key, 0)  # 初始化
        if abs(cell.z - z_max) < 1.0e-4:
            top_ids.append(cell.index)
        if abs(cell.z - z_min) < 1.0e-4:
            btm_ids.append(cell.index)

    step_iteration.add_setting(
        model, start=0, step=1, stop=999999999, name='set_fluid_time',
        args=['@model', top_ids, btm_ids, key]
    )
    return model


def set_fluid_time(model, top_ids, btm_ids, key):
    time = seepage.get_time(model)
    for idx in top_ids:
        model.get_cell(idx).get_fluid(0).set_attr(key, time)
    value = 0
    for idx in btm_ids:
        value += model.get_cell(idx).get_fluid(0).get_attr(key)
    if value > 1.0e-4:
        seepage.set_step(model, STEP_MAX * 2)


def show(model):
    title = f'Time = {seepage.get_time(model, as_str=True)}'
    x = as_numpy(model).cells.x
    z = as_numpy(model).cells.z
    time = as_numpy(model).fluids(0).get_attr(model.get_flu_key('time'))
    tricontourf(
        x, z, time, caption='流体time', title=title)


def main():
    model = create()
    seepage.solve(model, close_after_done=False, step_max=STEP_MAX,
                  extra_plot=lambda: show(model),
                  slots={'set_fluid_time': set_fluid_time}
                  )


if __name__ == '__main__':
    main()
